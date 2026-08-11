"""Shared pytest fixtures for TextShield.

* Auto-trains the ML model once if model files are missing
  (so `pytest` works on a fresh clone without prior setup).
* Provides a TestClient bound to the FastAPI app.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def trained_model() -> None:
    """Ensure the classifier exists before any test that needs it."""
    if settings.MODEL_PATH.exists() and settings.VECTORIZER_PATH.exists():
        return
    script = PROJECT_ROOT / "scripts" / "train_model.py"
    result = subprocess.run(
        [sys.executable, str(script), "--out", str(settings.MODEL_PATH.parent)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"auto-train failed:\n{result.stdout}\n{result.stderr}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client