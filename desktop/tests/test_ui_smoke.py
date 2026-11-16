from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence

from textshield_desktop.backend.client import BackendClient
from textshield_desktop.config import DesktopConfig
from textshield_desktop.ui.analysis_widget import AnalysisWidget
from textshield_desktop.ui.clipboard_dialog import ClipboardReviewDialog
from textshield_desktop.ui.launcher import LauncherWindow
from textshield_desktop.ui.main_window import MainWindow
from textshield_desktop.ui.overlay import OverlayWindow
from textshield_desktop.ui.result_view import ResultView
from textshield_desktop.ui.settings_dialog import SettingsDialog
from textshield_desktop.ui.tray import TrayIcon


def test_result_view_renders_payload(qtbot) -> None:
    view = ResultView(compact=True)
    qtbot.addWidget(view)
    view.set_result(
        {
            "classification": "PHISHING",
            "confidence": 0.93,
            "risk_level": "HIGH",
            "risk_score": 88,
            "explanation": "Credential lure.",
            "recommended_action": "Do not click.",
            "indicators": [
                {
                    "indicator": "Urgency language",
                    "severity": "high",
                    "evidence": "within 24 hours",
                }
            ],
            "urls": [
                {
                    "url": "http://example.invalid/login",
                    "host": "example.invalid",
                    "warnings": ["Non-HTTPS link detected"],
                }
            ],
            "rag_evidence": [
                {
                    "document": "Phishing messages often use urgency.",
                    "source": "phishing.md",
                    "category": "phishing",
                    "score": 0.62,
                }
            ],
            "risk_factors": ["ML classified the message as PHISHING"],
        }
    )
    assert view._classification.text() == "PHISHING"
    assert "93.0%" in view._confidence.text()
    assert "HIGH" in view._risk.text()
    details = view._details.toPlainText()
    assert "Urgency language" in details
    assert "example.invalid" in details
    assert "Risk factors" in details
    view.show_error("Backend offline")
    assert view._classification.text() == "ERROR"


def test_overlay_show_hide_reopen(qtbot) -> None:
    client = BackendClient("http://127.0.0.1:1")
    overlay = OverlayWindow(DesktopConfig(), client, QPoint(40, 40))
    qtbot.addWidget(overlay)
    overlay.show_overlay()
    qtbot.wait(50)
    assert overlay.isVisible()
    assert overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    overlay.set_always_on_top(False)
    assert not overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    overlay.set_always_on_top(True)
    assert overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    overlay.hide_overlay()
    qtbot.wait(30)
    assert not overlay.isVisible()
    overlay.show_overlay()
    qtbot.wait(50)
    assert overlay.isVisible()
    overlay.close()
    assert not overlay.isVisible()
    client.close()


def test_launcher_click_signal(qtbot) -> None:
    launcher = LauncherWindow(DesktopConfig(launcher_position="40,40"))
    qtbot.addWidget(launcher)
    with qtbot.waitSignal(launcher.clicked, timeout=1000):
        launcher._button.click()
    launcher.show_launcher()
    assert launcher.isVisible()
    launcher.hide_launcher()
    assert not launcher.isVisible()


def test_main_window_closes_to_tray(qtbot) -> None:
    client = BackendClient("http://127.0.0.1:1")
    window = MainWindow(DesktopConfig(), client, tray_available=True)
    qtbot.addWidget(window)
    window.show_main()
    assert window.isVisible()
    window.close()
    assert not window.isVisible()
    client.close()


def test_settings_dialog_validates_and_saves(qtbot) -> None:
    dialog = SettingsDialog(DesktopConfig(), startup_available=True)
    qtbot.addWidget(dialog)
    dialog._url.setText("127.0.0.1:9100")
    dialog._hotkey.setKeySequence(QKeySequence("Ctrl+Alt+Shift+F12"))
    dialog._startup.setChecked(True)
    dialog._accept()
    assert dialog.result_config is not None
    assert dialog.result_config.backend_url == "http://127.0.0.1:9100"
    assert dialog.result_config.hotkey == "Ctrl+Alt+Shift+F12"
    assert dialog.result_config.start_with_windows is True
    assert dialog.result() == 1

    invalid = SettingsDialog(DesktopConfig(), startup_available=True)
    qtbot.addWidget(invalid)
    invalid._url.setText("ftp://bad")
    invalid._accept()
    assert invalid.result_config is None
    assert invalid.result() == 0

    bad_hotkey = SettingsDialog(DesktopConfig(), startup_available=True)
    qtbot.addWidget(bad_hotkey)
    bad_hotkey._hotkey.setKeySequence(QKeySequence("F12"))
    bad_hotkey._accept()
    assert bad_hotkey.result_config is None
    assert "Ctrl" in bad_hotkey._hotkey_status.text()


def test_clipboard_review_dialog(qtbot) -> None:
    dialog = ClipboardReviewDialog(
        "Hello from the clipboard",
        source="clipboard",
        backend_online=False,
    )
    qtbot.addWidget(dialog)
    assert dialog.analysis_text == "Hello from the clipboard"
    assert not dialog._offline.isHidden()
    dialog._input_type.setCurrentIndex(1)
    dialog._accept()
    assert dialog.result() == 1
    assert dialog.input_type() == "sms"


def test_analysis_widget_clipboard_actions(qtbot) -> None:
    client = BackendClient("http://127.0.0.1:1")
    widget = AnalysisWidget(client)
    qtbot.addWidget(widget)
    with qtbot.waitSignal(widget.clipboard_analyze_requested, timeout=1000):
        widget._clipboard_analyze.click()
    with qtbot.waitSignal(widget.copy_selection_requested, timeout=1000):
        widget._copy_selection.click()
    with qtbot.waitSignal(widget.clear_clipboard_requested, timeout=1000):
        widget._clear_clipboard.click()
    widget.set_clipboard_text("Hello", "sms", "clipboard")
    assert widget.input_text() == "Hello"
    assert widget.input_type() == "sms"
    assert "Clipboard" in widget.source_text()
    widget.set_input_text("Typed text")
    assert widget.source_text() == ""
    client.close()


def test_tray_actions_and_status(qtbot) -> None:
    tray = TrayIcon(available=False)
    labels = tray.action_labels()
    for label in (
        "Open TextShield",
        "Analyze Clipboard",
        "Copy Selected Text",
        "Clear Clipboard",
        "Open Dashboard",
        "Settings",
        "Reconnect Backend",
        "Start with Windows",
        "Exit",
    ):
        assert label in labels
    with qtbot.waitSignal(tray.analyze_clipboard_requested, timeout=1000):
        tray._analyze_clipboard_action.trigger()
    with qtbot.waitSignal(tray.reconnect_requested, timeout=1000):
        tray._reconnect_action.trigger()
    tray.set_backend_status(False, "http://127.0.0.1:1", {"error": "offline"})
    assert "offline" in tray._status_action.text()
    tray.set_start_with_windows(True)
    assert tray._startup_action.isChecked()
    tray.deleteLater()
