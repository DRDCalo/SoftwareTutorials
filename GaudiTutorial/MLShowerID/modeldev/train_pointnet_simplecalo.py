#!/usr/bin/env python3
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
"""Train SimpleCalo PointNet: configure, prepare data, train, and export.

Network definitions live in pointnet_model.py; data processing and artifact
export live in pointnet_util.py. Run this file as the command-line entry point.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from pointnet_model import FEATURE_NAMES, TinyPointNet
from pointnet_util import (
    SimpleCaloDataset,
    export_artifacts,
    fit_normalizer,
    load_signal_background,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a tiny PointNet on simplecaloRO PODIO calorimeter hits."
    )
    parser.add_argument(
        "--signal-input",
        default="simplecalo_e-_1-20GeV.root",
        help="Signal PODIO ROOT file. Label is 0.",
    )
    parser.add_argument(
        "--background-input",
        default="simplecalo_pi-_1-20GeV.root",
        help="Background PODIO ROOT file. Label is 1.",
    )
    parser.add_argument("--tree", default="events", help="PODIO event tree name.")
    parser.add_argument("--collection", default="simplecaloRO", help="Hit collection name.")
    parser.add_argument(
        "--output-dir",
        default="pointnet_outputs",
        help="Directory for model and optional NPZ outputs.",
    )
    parser.add_argument("--max-events", type=int, default=10000)
    parser.add_argument("--max-points", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--seed", type=int, default=12345)

    return parser.parse_args()


def accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    predictions = logits.argmax(dim=1)
    return float((predictions == labels).float().mean().item())


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None = None,
) -> tuple[float, float]:
    is_train = optimizer is not None
    model.train(is_train)
    loss_fn = nn.CrossEntropyLoss()
    total_loss = 0.0
    total_acc = 0.0
    total_events = 0

    for points, mask, labels in loader:
        points = points.to(device)
        mask = mask.to(device)
        labels = labels.to(device)

        with torch.set_grad_enabled(is_train):
            logits = model(points, mask)
            loss = loss_fn(logits, labels)
            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        batch_size = int(labels.shape[0])
        total_events += batch_size
        total_loss += float(loss.item()) * batch_size
        total_acc += accuracy(logits.detach(), labels) * batch_size

    return total_loss / total_events, total_acc / total_events


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    points, mask, labels, metadata = load_signal_background(args)

    indices = np.arange(len(labels))
    np.random.shuffle(indices)
    split = int(0.8 * len(indices))
    train_indices = indices[:split]
    val_indices = indices[split:]
    if len(train_indices) == 0 or len(val_indices) == 0:
        raise RuntimeError("Need at least two events to make a 4:1 train/validation split.")

    normalizer = fit_normalizer(points, mask, train_indices)
    points = normalizer.apply(points, mask)

    # Normalized point clouds for evaluate_pointnet_simplecalo.py, which
    # reproduces the validation split from these arrays and the seed.
    npz_path = output_dir / "simplecalo_pointcloud.npz"
    np.savez_compressed(npz_path, points=points, mask=mask, labels=labels)

    train_loader = DataLoader(
        SimpleCaloDataset(points[train_indices], mask[train_indices], labels[train_indices]),
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        SimpleCaloDataset(points[val_indices], mask[val_indices], labels[val_indices]),
        batch_size=args.batch_size,
        shuffle=False,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TinyPointNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)

    print(f"events={len(labels)} train={len(train_indices)} val={len(val_indices)} device={device}")
    print(f"signal_input={args.signal_input}")
    print(f"background_input={args.background_input}")
    print(f"features={FEATURE_NAMES}")
    print(f"class_counts={np.bincount(labels, minlength=2).tolist()}")

    history = []
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, train_loader, device, optimizer)
        val_loss, val_acc = run_epoch(model, val_loader, device)
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
        }
        history.append(row)
        print(
            f"epoch {epoch:03d} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.3f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.3f}"
        )

    state_path, traced_path, onnx_path = export_artifacts(
        model, normalizer, metadata, args, history, labels, output_dir
    )

    print(f"saved state_dict: {state_path}")
    print(f"saved torchscript: {traced_path}")
    print(f"saved onnx: {onnx_path}")
    print(f"saved point clouds: {npz_path}")


if __name__ == "__main__":
    main()
