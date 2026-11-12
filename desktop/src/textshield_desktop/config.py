"""Desktop configuration backed by QSettings."""

from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtCore import QSettings, QUrl

ORGANIZATION = "TextShield"
APPLICATION = "TextShieldDesktop"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"


def normalize_backend_url(value: str) -> str:
    """Return a usable http(s) base URL or raise ValueError."""
    raw = (value or "").strip() or DEFAULT_BACKEND_URL
    if "://" not in raw:
        raw = "http://" + raw
    url = QUrl(raw)
    if (
        not url.isValid()
        or url.scheme().lower() not in {"http", "https"}
        or not url.host()
    ):
        raise ValueError("Backend URL must be a valid http:// or https:// URL")
    return url.toString().rstrip("/")


@dataclass
class DesktopConfig:
    backend_url: str = DEFAULT_BACKEND_URL
    always_on_top: bool = True
    hide_on_focus_out: bool = True
    launcher_visible: bool = True
    overlay_geometry: str = ""
    launcher_position: str = ""

    @classmethod
    def load(cls, settings: QSettings | None = None) -> "DesktopConfig":
        store = settings or QSettings(ORGANIZATION, APPLICATION)
        env_url = os.getenv("TEXTSHIELD_BACKEND_URL", "")
        backend_url = env_url or store.value(
            "backend/url", DEFAULT_BACKEND_URL, type=str
        )
        try:
            backend_url = normalize_backend_url(backend_url)
        except ValueError:
            backend_url = DEFAULT_BACKEND_URL
        return cls(
            backend_url=backend_url,
            always_on_top=store.value("ui/always_on_top", True, type=bool),
            hide_on_focus_out=store.value("ui/hide_on_focus_out", True, type=bool),
            launcher_visible=store.value("ui/launcher_visible", True, type=bool),
            overlay_geometry=store.value("ui/overlay_geometry", "", type=str),
            launcher_position=store.value("ui/launcher_position", "", type=str),
        )

    def save(self, settings: QSettings | None = None) -> None:
        store = settings or QSettings(ORGANIZATION, APPLICATION)
        store.setValue("backend/url", self.backend_url)
        store.setValue("ui/always_on_top", self.always_on_top)
        store.setValue("ui/hide_on_focus_out", self.hide_on_focus_out)
        store.setValue("ui/launcher_visible", self.launcher_visible)
        store.setValue("ui/overlay_geometry", self.overlay_geometry)
        store.setValue("ui/launcher_position", self.launcher_position)
        store.sync()
