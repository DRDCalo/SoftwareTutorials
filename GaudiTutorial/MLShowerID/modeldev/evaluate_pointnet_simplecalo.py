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
"""Evaluate SimpleCalo PointNet: load artifacts, infer, plot, and save results.

The model is shared with training in pointnet_model.py. Evaluation helpers live
in pointnet_util.py alongside data processing and export tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pointnet_util import (
    collect_scores,
    compute_metrics,
    load_validation_artifacts,
    plot_loss,
    plot_roc,
    save_evaluation_results,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot loss and ROC curves for the SimpleCalo PointNet model.")
    parser.add_argument(
        "--artifact-dir",
        default="GaudiTutorial/modeldev/pointnet_outputs",
        help="Directory containing training_summary.json, model state, and converted NPZ.",
    )
    parser.add_argument("--batch-size", type=int, default=256)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_dir = Path(args.artifact_dir)
    with (artifact_dir / "training_summary.json").open(encoding="utf-8") as handle:
        summary = json.load(handle)

    model, dataset = load_validation_artifacts(artifact_dir, summary)
    y_true, y_score = collect_scores(model, dataset, args.batch_size)
    metrics = compute_metrics(y_true, y_score, artifact_dir)

    plot_loss(summary["history"], artifact_dir / "loss_curve.png")
    plot_roc(y_true, y_score, metrics["auc"], artifact_dir / "roc_curve.png")
    save_evaluation_results(artifact_dir, metrics)

    print(f"saved loss curve: {artifact_dir / 'loss_curve.png'}")
    print(f"saved ROC curve: {artifact_dir / 'roc_curve.png'}")
    print(f"saved summary: {artifact_dir / 'evaluation_summary.json'}")
    print(f"AUC: {metrics['auc']:.6f}")
    print(f"accuracy@0.5: {metrics['accuracy_at_0p5']:.6f}")


if __name__ == "__main__":
    main()
