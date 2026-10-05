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
"""PointNet architecture and its deployment preprocessing wrapper."""

from __future__ import annotations

import torch
from torch import nn


FEATURE_NAMES = ("x", "y", "z", "energy")
CLASS_NAMES = ("electron", "hadron")
SIGNAL_LABEL = 0
BACKGROUND_LABEL = 1


class TinyPointNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.point_mlp = nn.Sequential(
            nn.Linear(len(FEATURE_NAMES), 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
        )

    def forward(self, points: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        point_features = self.point_mlp(points)
        point_features = point_features.masked_fill(~mask.unsqueeze(-1), -1.0e9)
        global_features = point_features.max(dim=1).values
        return self.classifier(global_features)


class PointNetWithPreprocessing(nn.Module):
    """Raw features -> embedded standardization -> PointNet -> softmax scores."""

    def __init__(self, model: TinyPointNet, mean: list[float], std: list[float]) -> None:
        super().__init__()
        self.model = model
        self.register_buffer(
            "feature_mean",
            torch.tensor(mean, dtype=torch.float32).view(1, 1, len(FEATURE_NAMES)),
        )
        self.register_buffer(
            "feature_std",
            torch.tensor(std, dtype=torch.float32).view(1, 1, len(FEATURE_NAMES)),
        )

    def forward(self, points: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        normalized = (points - self.feature_mean) / self.feature_std
        normalized = torch.where(mask.unsqueeze(-1), normalized, torch.zeros_like(normalized))
        return torch.softmax(self.model(normalized, mask), dim=1)


