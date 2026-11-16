from __future__ import annotations

import argparse
import json
from dataclasses import replace

from PySide6.QtWidgets import QApplication, QDialog

from textshield_desktop import app as app_module
from textshield_desktop.app import DesktopApplication
from textshield_desktop.config import DesktopConfig


class _AcceptingReviewDialog:
    def __init__(
        self,
        text: str,
        source: str = "clipboard",
        backend_online: bool = True,
        parent=None,
    ) -> None:
        self.analysis_text = text
        self._source = source
        self._type = "text"

    def exec(self) -> int:
        return int(QDialog.DialogCode.Accepted)

    def input_type(self) -> str:
        return self._type


def _make_app(monkeypatch, qtbot, url: str) -> DesktopApplication:
    config = DesktopConfig(backend_url=url)
    monkeypatch.setattr(
        app_module.DesktopConfig,
        "load",
        classmethod(lambda cls, settings=None: config),
    )
    monkeypatch.setattr(
        app_module.DesktopConfig,
        "save",
        lambda self, settings=None: None,
    )
    app = DesktopApplication(
        QApplication.instance(),
        argparse.Namespace(backend_url=None, startup=False),
    )
    qtbot.addWidget(app.overlay)
    qtbot.addWidget(app.main_window)
    qtbot.addWidget(app.launcher)
    return app


def test_clipboard_and_selection_review_paths(qtbot, api_factory, monkeypatch) -> None:
    payload = {
        "classification": "PHISHING",
        "confidence": 0.95,
        "risk_level": "HIGH",
        "risk_score": 92,
        "explanation": "Credential lure.",
        "recommended_action": "Do not click.",
    }
    api = api_factory({("POST", "/api/analyze"): (200, payload)})
    app = _make_app(monkeypatch, qtbot, api.url)
    monkeypatch.setattr(app_module, "ClipboardReviewDialog", _AcceptingReviewDialog)
    monkeypatch.setattr(app_module, "is_own_window", lambda hwnd: False)
    messages: list[tuple] = []
    monkeypatch.setattr(app, "_show_message", lambda *args: messages.append(args))
    clipboard_text = ["Click http://example.invalid now"]
    monkeypatch.setattr(app.clipboard, "text", lambda: clipboard_text[0])
    try:
        app.analyze_clipboard()
        widget = app.overlay.analysis_widget()
        qtbot.waitUntil(
            lambda: widget.result_view().classification_text() == "PHISHING",
            timeout=4000,
        )
        assert "Clipboard" in widget.source_text()
        first_request = json.loads(api.requests[0][2])
        assert first_request["message"] == "Click http://example.invalid now"

        app._last_external_window = 12345
        monkeypatch.setattr(
            app.clipboard,
            "capture_selected_text",
            lambda target: ("Selected text for review", None),
        )
        app.copy_selected_text()
        qtbot.waitUntil(
            lambda: widget.result_view().classification_text() == "PHISHING"
            and "Selected text" in widget.source_text(),
            timeout=4000,
        )
        assert "Selected text" in widget.source_text()
        second_request = json.loads(api.requests[1][2])
        assert second_request["message"] == "Selected text for review"

        app.main_window.show_main()
        clipboard_text[0] = "Main window clipboard"
        app.analyze_clipboard()
        main_widget = app.main_window.analysis_widget()
        qtbot.waitUntil(
            lambda: main_widget.result_view().classification_text()
            == "PHISHING",
            timeout=4000,
        )
        assert "Clipboard" in main_widget.source_text()
        third_request = json.loads(api.requests[2][2])
        assert third_request["message"] == "Main window clipboard"
        assert not messages
    finally:
        app.shutdown()


def test_apply_config_reports_hotkey_conflict(
    qtbot, api_factory, monkeypatch
) -> None:
    app = _make_app(monkeypatch, qtbot, api_factory({}).url)

    class _ConflictingHotkey:
        last_error = "Could not register the shortcut."

        def set_shortcut(self, sequence: str) -> bool:
            return False

        def close(self) -> None:
            return

    app.hotkey.close()
    app.hotkey = _ConflictingHotkey()
    config = replace(app.config, hotkey="Ctrl+Alt+Shift+K")
    error = app.apply_config(config)
    assert error is not None
    assert "Could not register" in error
    assert app.config.hotkey == "Ctrl+Alt+Shift+T"

    class _FailingStartup:
        def enabled(self) -> bool:
            return False

        def set_enabled(self, enabled: bool) -> None:
            raise OSError("startup permission denied")

    app.startup_available = True
    app.startup = _FailingStartup()
    config = replace(app.config, start_with_windows=True)
    error = app.apply_config(config)
    assert error is not None
    assert "permission denied" in error
    assert app.config.start_with_windows is False
    app.shutdown()


def test_clear_clipboard_requires_confirmation(
    qtbot, api_factory, monkeypatch
) -> None:
    app = _make_app(monkeypatch, qtbot, api_factory({}).url)
    cleared: list[bool] = []
    monkeypatch.setattr(app.clipboard, "has_content", lambda: True)
    monkeypatch.setattr(app.clipboard, "clear", lambda: cleared.append(True))
    try:
        monkeypatch.setattr(app, "_ask", lambda title, text: False)
        app.clear_clipboard()
        assert cleared == []
        monkeypatch.setattr(app, "_ask", lambda title, text: True)
        app.clear_clipboard()
        assert cleared == [True]
    finally:
        app.shutdown()
