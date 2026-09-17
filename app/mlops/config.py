"""MLOps configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

def _get(k, d):
    return os.getenv(k, d)

@dataclass
class MLOpsConfig:
    dataset_path: str = field(default_factory=lambda: _get("MLOPS_DATASET_PATH", "data/datasets"))
    model_dir: str = field(default_factory=lambda: _get("MLOPS_MODEL_DIR", "models"))
    artifact_dir: str = field(default_factory=lambda: _get("MLOPS_ARTIFACT_DIR", "artifacts"))
    registry_path: str = field(default_factory=lambda: _get("MLOPS_REGISTRY_PATH", "data/mlops_registry.json"))
    random_seed: int = 42
    eval_threshold_f1: float = 0.85
    regression_fpr_increase: float = 0.02
    deployment_mode: str = field(default_factory=lambda: _get("MLOPS_DEPLOY_MODE", "manual"))
