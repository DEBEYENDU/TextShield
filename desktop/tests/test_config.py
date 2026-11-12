from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from textshield_desktop.config import DesktopConfig, normalize_backend_url


def test_normalize_backend_url() -> None:
    assert normalize_backend_url("127.0.0.1:8000") == "http://127.0.0.1:8000"
    assert normalize_backend_url("http://localhost:9000/") == "http://localhost:9000"
    assert normalize_backend_url("https://example.test/api/") == "https://example.test/api"
    with pytest.raises(ValueError):
        normalize_backend_url("ftp://example.test")
    with pytest.raises(ValueError):
        normalize_backend_url("http://")


def test_config_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TEXTSHIELD_BACKEND_URL", raising=False)
    path = tmp_path / "settings.ini"
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    config = DesktopConfig.load(settings)
    assert config.backend_url == "http://127.0.0.1:8000"
    assert config.always_on_top is True
    assert config.hide_on_focus_out is True
    assert config.launcher_visible is True

    config.backend_url = "http://127.0.0.1:9100"
    config.always_on_top = False
    config.hide_on_focus_out = False
    config.launcher_visible = False
    config.overlay_geometry = "100,200"
    config.launcher_position = "300,400"
    config.save(settings)

    loaded = DesktopConfig.load(settings)
    assert loaded.backend_url == "http://127.0.0.1:9100"
    assert loaded.always_on_top is False
    assert loaded.hide_on_focus_out is False
    assert loaded.launcher_visible is False
    assert loaded.overlay_geometry == "100,200"
    assert loaded.launcher_position == "300,400"


def test_config_env_override(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TEXTSHIELD_BACKEND_URL", "http://127.0.0.1:9200")
    settings = QSettings(
        str(tmp_path / "env.ini"), QSettings.Format.IniFormat
    )
    settings.setValue("backend/url", "http://127.0.0.1:8000")
    assert DesktopConfig.load(settings).backend_url == "http://127.0.0.1:9200"
