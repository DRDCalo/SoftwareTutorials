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


