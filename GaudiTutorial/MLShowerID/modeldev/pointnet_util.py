#
# Copyright (c) 2020-2024 Key4hep-Project.
#
# This file is part of Key4hep.
# See https://key4hep.github.io/key4hep-doc/ for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Shared SimpleCalo tools for data processing, model export, and evaluation.

Plotting and metric dependencies are imported when the evaluation tools run.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import onnx
import torch
from torch.utils.data import Dataset
import uproot

from pointnet_model import (
    BACKGROUND_LABEL, CLASS_NAMES, FEATURE_NAMES, SIGNAL_LABEL,
    PointNetWithPreprocessing, TinyPointNet,
)


@dataclass
class Normalizer:
    mean: list[float]
    std: list[float]

    def apply(self, points: np.ndarray, mask: np.ndarray) -> np.ndarray:
        output = points.copy()
        valid = mask.astype(bool)
        if valid.any():
            mean = np.asarray(self.mean, dtype=np.float32)
            std = np.asarray(self.std, dtype=np.float32)
            output[valid] = (output[valid] - mean) / std
        return output


class SimpleCaloDataset(Dataset):
    def __init__(self, points: np.ndarray, mask: np.ndarray, labels: np.ndarray) -> None:
        self.points = torch.from_numpy(points).float()
        self.mask = torch.from_numpy(mask).bool()
        self.labels = torch.from_numpy(labels).long()

    def __len__(self) -> int:
        return int(self.labels.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.points[index], self.mask[index], self.labels[index]


def read_simplecalo(
    input_path: Path,
    tree_name: str,
    collection: str,
    max_events: int,
    max_points: int,
    label: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int | str]]:
    tree = uproot.open(input_path)[tree_name]
    stop = min(max_events, tree.num_entries)
    branches = [
        f"{collection}/{collection}.energy",
        f"{collection}/{collection}.position.x",
        f"{collection}/{collection}.position.y",
        f"{collection}/{collection}.position.z",
    ]
    arrays = tree.arrays(branches, entry_stop=stop, library="np")

    energy = arrays[branches[0]]
    xpos = arrays[branches[1]]
    ypos = arrays[branches[2]]
    zpos = arrays[branches[3]]

    n_events = len(energy)
    points = np.zeros((n_events, max_points, len(FEATURE_NAMES)), dtype=np.float32)
    mask = np.zeros((n_events, max_points), dtype=np.bool_)
    labels = np.full((n_events,), label, dtype=np.int64)
    total_hits = 0
    kept_hits = 0

    for event_idx in range(n_events):
        e = np.asarray(energy[event_idx], dtype=np.float32)
        x = np.asarray(xpos[event_idx], dtype=np.float32)
        y = np.asarray(ypos[event_idx], dtype=np.float32)
        z = np.asarray(zpos[event_idx], dtype=np.float32)

        n_hits = len(e)
        total_hits += n_hits
        if n_hits == 0:
            continue

        order = np.argsort(e)[::-1][:max_points]
        selected = np.stack([x[order], y[order], z[order], e[order]], axis=1)
        n_keep = selected.shape[0]
        points[event_idx, :n_keep] = selected
        mask[event_idx, :n_keep] = True
        kept_hits += n_keep

    metadata = {
        "input": str(input_path),
        "label": int(label),
        "events": int(n_events),
        "max_points": int(max_points),
        "total_hits": int(total_hits),
        "kept_hits": int(kept_hits),
    }
    return points, mask, labels, metadata


def load_signal_background(args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    signal = read_simplecalo(
        Path(args.signal_input),
        args.tree,
        args.collection,
        args.max_events,
        args.max_points,
        SIGNAL_LABEL,
    )
    background = read_simplecalo(
        Path(args.background_input),
        args.tree,
        args.collection,
        args.max_events,
        args.max_points,
        BACKGROUND_LABEL,
    )

    points = np.concatenate([signal[0], background[0]], axis=0)
    mask = np.concatenate([signal[1], background[1]], axis=0)
    labels = np.concatenate([signal[2], background[2]], axis=0)
    metadata = {
        "signal": signal[3],
        "background": background[3],
        "total_events": int(len(labels)),
        "max_points": int(args.max_points),
    }
    return points, mask, labels, metadata


def fit_normalizer(points: np.ndarray, mask: np.ndarray, train_indices: np.ndarray) -> Normalizer:
    valid_points = points[train_indices][mask[train_indices]]
    mean = valid_points.mean(axis=0)
    std = valid_points.std(axis=0)
    std = np.where(std < 1.0e-6, 1.0, std)
    return Normalizer(mean=mean.astype(float).tolist(), std=std.astype(float).tolist())


def annotate_and_validate_onnx(
    onnx_path: Path, normalizer: Normalizer, max_points: int
) -> None:
    """Record the deployment contract and verify preprocessing/output nodes."""
    model = onnx.load(onnx_path)
    operator_types = {node.op_type for node in model.graph.node}
    required_operators = {"Sub", "Div", "Softmax"}
    missing = required_operators - operator_types
    if missing:
        raise RuntimeError(
            f"Exported ONNX model is missing required operators: {sorted(missing)}"
        )

    input_names = [value.name for value in model.graph.input]
    output_names = [value.name for value in model.graph.output]
    if input_names != ["points", "mask"] or output_names != ["scores"]:
        raise RuntimeError(
            f"Unexpected ONNX interface: inputs={input_names}, outputs={output_names}"
        )

    onnx.helper.set_model_props(
        model,
        {
            "feature_names": json.dumps(FEATURE_NAMES),
            "feature_mean": json.dumps(normalizer.mean),
            "feature_std": json.dumps(normalizer.std),
            "class_names": json.dumps(CLASS_NAMES),
            "points_layout": f"[batch, {max_points}, {len(FEATURE_NAMES)}]",
            "preprocessing": "(points - feature_mean) / feature_std for valid hits",
            "output": "softmax probabilities ordered as [electron, hadron]",
        },
    )
    onnx.checker.check_model(model)
    onnx.save(model, onnx_path)


def export_artifacts(
    model: TinyPointNet,
    normalizer: Normalizer,
    metadata: dict,
    args: argparse.Namespace,
    history: list[dict],
    labels: np.ndarray,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    """Save the checkpoint, deployment models, and training summary."""
    max_points = args.max_points
    model_cpu = model.cpu().eval()
    state_path = output_dir / "pointnet_simplecalo_state.pt"
    torch.save(
        {
            "model_state_dict": model_cpu.state_dict(),
            "model_class": "TinyPointNet",
            "feature_names": FEATURE_NAMES,
            "class_names": CLASS_NAMES,
            "normalizer": asdict(normalizer),
            "metadata": metadata,
            "args": vars(args),
        },
        state_path,
    )

    example_points = torch.zeros(1, max_points, len(FEATURE_NAMES), dtype=torch.float32)
    example_mask = torch.ones(1, max_points, dtype=torch.bool)
    deployment_model = PointNetWithPreprocessing(
        model_cpu, normalizer.mean, normalizer.std
    ).eval()
    traced = torch.jit.trace(deployment_model, (example_points, example_mask))
    traced_path = output_dir / "pointnet_simplecalo_torchscript.pt"
    traced.save(traced_path)

    onnx_path = output_dir / "pointnet_simplecalo.onnx"
    torch.onnx.export(
        deployment_model,
        (example_points, example_mask),
        onnx_path,
        input_names=["points", "mask"],
        output_names=["scores"],
        dynamic_axes={
            "points": {0: "batch"},
            "mask": {0: "batch"},
            "scores": {0: "batch"},
        },
        opset_version=17,
        dynamo=False,
    )
    annotate_and_validate_onnx(onnx_path, normalizer, max_points)

    with (output_dir / "training_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "history": history,
                "feature_names": FEATURE_NAMES,
                "class_names": CLASS_NAMES,
                "normalizer": asdict(normalizer),
                "metadata": metadata,
                "class_counts": np.bincount(labels, minlength=2).astype(int).tolist(),
                "state_dict": str(state_path),
                "torchscript": str(traced_path),
                "onnx": str(onnx_path),
                "onnx_input": "raw (x, y, z, energy); mean/std normalization embedded",
                "onnx_output": "softmax scores [electron, hadron]",
            },
            handle,
            indent=2,
        )

    return state_path, traced_path, onnx_path


# Evaluation tools

MAX_PLOTTED_LOSS = 10.0


def json_float_list(values: np.ndarray) -> list[float | None]:
    output: list[float | None] = []
    for value in values.astype(float):
        output.append(float(value) if np.isfinite(value) else None)
    return output


def plot_loss(history: list[dict], output_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    train_points = [
        (row["epoch"], row["train_loss"])
        for row in history
        if np.isfinite(row["train_loss"]) and row["train_loss"] <= MAX_PLOTTED_LOSS
    ]
    val_points = [
        (row["epoch"], row["val_loss"])
        for row in history
        if np.isfinite(row["val_loss"]) and row["val_loss"] <= MAX_PLOTTED_LOSS
    ]
    train_epochs, train_loss = zip(*train_points) if train_points else ([], [])
    val_epochs, val_loss = zip(*val_points) if val_points else ([], [])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(train_epochs, train_loss, label="training loss", linewidth=2)
    ax.plot(val_epochs, val_loss, label="validation loss", linewidth=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Cross entropy loss")
    ax.set_title("Tiny PointNet training curve")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def validation_indices(num_events: int, seed: int) -> np.ndarray:
    indices = np.arange(num_events)
    rng = np.random.RandomState(seed)
    rng.shuffle(indices)
    split = int(0.8 * len(indices))
    return indices[split:]


def collect_scores(model: TinyPointNet, dataset: SimpleCaloDataset, batch_size: int) -> tuple[np.ndarray, np.ndarray]:
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    labels = []
    scores = []
    model.eval()
    with torch.no_grad():
        for points, mask, batch_labels in loader:
            logits = model(points, mask)
            probabilities = torch.softmax(logits, dim=1)
            scores.append(probabilities[:, 1].cpu().numpy())
            labels.append(batch_labels.cpu().numpy())
    return np.concatenate(labels), np.concatenate(scores)


def plot_roc(labels: np.ndarray, scores: np.ndarray, roc_auc: float, output_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    fpr, tpr, _ = roc_curve(labels, scores)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, linewidth=2, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="0.5", label="random")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Tiny PointNet ROC curve")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def load_validation_artifacts(
    artifact_dir: Path, summary: dict
) -> tuple[TinyPointNet, SimpleCaloDataset]:
    """Restore the trained model and reproduce the training validation split."""
    with np.load(artifact_dir / "simplecalo_pointcloud.npz") as arrays:
        points = arrays["points"]
        mask = arrays["mask"]
        labels = arrays["labels"]

    seed = int(summary["metadata"].get("seed", summary.get("args", {}).get("seed", 12345)))
    # Older summaries store the seed only under args.
    seed = int(summary.get("args", {}).get("seed", seed))
    val_indices = validation_indices(len(labels), seed)

    checkpoint = torch.load(summary["state_dict"], map_location="cpu")
    model = TinyPointNet()
    model.load_state_dict(checkpoint["model_state_dict"])

    val_dataset = SimpleCaloDataset(points[val_indices], mask[val_indices], labels[val_indices])
    return model, val_dataset


def compute_metrics(
    y_true: np.ndarray, y_score: np.ndarray, artifact_dir: Path
) -> dict:
    """Compute ROC/AUC and accuracy with the original background score convention."""
    from sklearn.metrics import auc, roc_curve

    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    predictions = (y_score >= 0.5).astype(np.int64)
    accuracy = float((predictions == y_true).mean())

    validation_class_counts = np.bincount(y_true, minlength=2).astype(int).tolist()
    outputs = {
        "loss_curve": str(artifact_dir / "loss_curve.png"),
        "roc_curve": str(artifact_dir / "roc_curve.png"),
    }
    metrics = {
        "num_validation_events": int(len(y_true)),
        "validation_class_counts": validation_class_counts,
        "auc": float(roc_auc),
        "accuracy_at_0p5": accuracy,
        "positive_label": 1,
        "score_definition": "softmax(logits)[:, 1], label 1 = background",
        "roc_points": {
            "fpr": json_float_list(fpr),
            "tpr": json_float_list(tpr),
            "thresholds": json_float_list(thresholds),
        },
        "outputs": outputs,
    }
    return metrics


def save_evaluation_results(artifact_dir: Path, metrics: dict) -> None:
    """Write detailed metrics and the compact evaluation summary."""
    summary_output = {
        "summary": str(artifact_dir / "training_summary.json"),
        "onnx": str(artifact_dir / "pointnet_simplecalo.onnx"),
        "auc": metrics["auc"],
        "accuracy_at_0p5": metrics["accuracy_at_0p5"],
        "validation_events": metrics["num_validation_events"],
        "validation_class_counts": metrics["validation_class_counts"],
        "score_definition": metrics["score_definition"],
        "outputs": metrics["outputs"],
    }
    with (artifact_dir / "evaluation_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, allow_nan=False)
    with (artifact_dir / "evaluation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_output, handle, indent=2, allow_nan=False)

