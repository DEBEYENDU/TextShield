"""Icon resource helpers."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon

RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"
ICON_DIR = RESOURCE_DIR / "icons"
ICON_ICO = ICON_DIR / "textshield.ico"
ICON_PNG = ICON_DIR / "textshield.png"
ICON_SVG = ICON_DIR / "textshield.svg"


def app_icon() -> QIcon:
    for path in (ICON_ICO, ICON_PNG, ICON_SVG):
        if path.exists():
            return QIcon(str(path))
    return QIcon()
