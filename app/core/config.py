"""Backward-compatibility shim (V2.0 foundation).

The configuration layer now lives in ``app/core/settings.py`` (typed
settings), ``app/core/constants.py`` (application constants) and
``app/core/features.py`` (feature flags). This module re-exports the old
symbols so existing imports keep working during the migration; new code
should import from the new modules directly.

.. deprecated:: 2.0
    Import from ``app.core.settings`` instead.
"""

from __future__ import annotations

from app.core.features import FeatureFlags, features
from app.core.settings import (
    BASE_DIR,
    Settings,
    load_settings,
    settings,
)

__all__ = [
    "BASE_DIR",
    "Settings",
    "load_settings",
    "settings",
    "FeatureFlags",
    "features",
]
