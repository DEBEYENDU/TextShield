from __future__ import annotations

from PySide6.QtCore import QPoint, Qt

from textshield_desktop.backend.client import BackendClient
from textshield_desktop.config import DesktopConfig
from textshield_desktop.ui.launcher import LauncherWindow
from textshield_desktop.ui.main_window import MainWindow
from textshield_desktop.ui.overlay import OverlayWindow
from textshield_desktop.ui.result_view import ResultView
from textshield_desktop.ui.settings_dialog import SettingsDialog


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
    dialog = SettingsDialog(DesktopConfig())
    qtbot.addWidget(dialog)
    dialog._url.setText("127.0.0.1:9100")
    dialog._accept()
    assert dialog.result_config is not None
    assert dialog.result_config.backend_url == "http://127.0.0.1:9100"
    assert dialog.result() == 1

    invalid = SettingsDialog(DesktopConfig())
    qtbot.addWidget(invalid)
    invalid._url.setText("ftp://bad")
    invalid._accept()
    assert invalid.result_config is None
    assert invalid.result() == 0
