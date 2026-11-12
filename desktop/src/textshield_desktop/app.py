"""Desktop application bootstrap and smoke test."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QSystemTrayIcon

from .backend.client import BackendClient
from .config import (
    APPLICATION,
    ORGANIZATION,
    DesktopConfig,
    normalize_backend_url,
)
from .ui.geometry import position_string
from .ui.icons import app_icon
from .ui.launcher import LauncherWindow
from .ui.main_window import MainWindow
from .ui.overlay import OverlayWindow
from .ui.settings_dialog import SettingsDialog
from .ui.theme import STYLESHEET
from .ui.tray import TrayIcon


class DesktopApplication(QObject):
    def __init__(self, app: QApplication, args: argparse.Namespace | None = None) -> None:
        super().__init__()
        self.qapp = app
        self.config = DesktopConfig.load()
        if args is not None and args.backend_url:
            try:
                self.config.backend_url = normalize_backend_url(args.backend_url)
            except ValueError:
                pass
        self._shutdown_done = False
        self._last_health_ok = False
        self._last_health: dict = {}

        self.client = BackendClient(self.config.backend_url, self)
        self.launcher = LauncherWindow(self.config)
        self.overlay = OverlayWindow(
            self.config, self.client, self._default_overlay_position()
        )
        self.tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        self.main_window = MainWindow(
            self.config, self.client, self.tray_available
        )
        self.tray = TrayIcon(self.tray_available, self)
        self._launcher_menu: QMenu | None = None
        self._build_launcher_menu()
        self._connect_signals()

        self.health_timer = QTimer(self)
        self.health_timer.setInterval(5000)
        self.health_timer.timeout.connect(self.client.check_health)

    def _default_overlay_position(self) -> QPoint:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return QPoint(80, 80)
        area = screen.availableGeometry()
        return QPoint(
            area.right() - 424 - 24,
            area.bottom() - 480 - 96,
        )

    def _build_launcher_menu(self) -> None:
        menu = QMenu(self.launcher)
        open_action = menu.addAction("Open TextShield")
        open_action.triggered.connect(self._show_overlay)
        menu.addSeparator()
        dashboard = menu.addAction("Open dashboard")
        dashboard.triggered.connect(self.open_dashboard)
        settings = menu.addAction("Settings")
        settings.triggered.connect(self.show_settings)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)
        self._launcher_menu = menu
        self.launcher.set_menu(menu)

    def _connect_signals(self) -> None:
        self.client.healthChanged.connect(self._on_health)
        self.launcher.clicked.connect(self._show_overlay)
        self.launcher.position_changed.connect(self._save_launcher_position)
        self.overlay.position_changed.connect(self._save_overlay_position)
        self.overlay.expand_requested.connect(self._show_main)
        self.overlay.open_dashboard_requested.connect(self.open_dashboard)
        self.main_window.open_dashboard_requested.connect(self.open_dashboard)
        self.main_window.settings_requested.connect(self.show_settings)
        self.tray.show_overlay_requested.connect(self._show_overlay)
        self.tray.launcher_toggled.connect(self._set_launcher_visible)
        self.tray.always_on_top_toggled.connect(self._set_always_on_top)
        self.tray.open_dashboard_requested.connect(self.open_dashboard)
        self.tray.settings_requested.connect(self.show_settings)
        self.tray.quit_requested.connect(self.quit)

    def start(self) -> None:
        self._set_launcher_visible(self.config.launcher_visible)
        self.tray.show()
        if not self.tray_available and not self.config.launcher_visible:
            self._show_main()
        self.health_timer.start()
        self.client.check_health()

    def _on_health(self, connected: bool, data: dict) -> None:
        self._last_health_ok = connected
        self._last_health = data
        self.overlay.set_status(connected, data)
        self.main_window.set_backend_status(connected, data)
        self.tray.set_backend_status(connected, self.client.base_url)

    def _show_overlay(self) -> None:
        self.overlay.show_overlay()

    def _show_main(self) -> None:
        self.overlay.hide_overlay()
        self.main_window.show_main()

    def _save_overlay_position(self, value: str) -> None:
        self.config.overlay_geometry = value
        self.config.save()

    def _save_launcher_position(self, value: str) -> None:
        self.config.launcher_position = value
        self.config.save()

    def _set_launcher_visible(self, visible: bool) -> None:
        self.config.launcher_visible = visible
        self.config.save()
        if visible:
            self.launcher.show_launcher()
        else:
            self.launcher.hide_launcher()
        self.tray.set_launcher_visible(visible)

    def _set_always_on_top(self, enabled: bool) -> None:
        self.config.always_on_top = enabled
        self.config.save()
        self.overlay.set_always_on_top(enabled)
        self.launcher.set_always_on_top(enabled)
        self.tray.set_always_on_top(enabled)

    def open_dashboard(self) -> None:
        QDesktopServices.openUrl(QUrl(self.client.base_url + "/"))

    def show_settings(self) -> None:
        dialog = SettingsDialog(self.config, None)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_config:
            self.apply_config(dialog.result_config)

    def apply_config(self, config: DesktopConfig) -> None:
        self.config = config
        self.config.save()
        self.client.set_base_url(config.backend_url)
        self.client.check_health()
        self.overlay.set_hide_on_focus_out(config.hide_on_focus_out)
        self.overlay.set_always_on_top(config.always_on_top)
        self.launcher.set_always_on_top(config.always_on_top)
        self.main_window.set_backend_url(config.backend_url)
        self.tray.set_always_on_top(config.always_on_top)
        self._set_launcher_visible(config.launcher_visible)

    def quit(self) -> None:
        self.qapp.quit()

    def shutdown(self) -> None:
        if self._shutdown_done:
            return
        self._shutdown_done = True
        self.config.overlay_geometry = position_string(self.overlay)
        self.config.launcher_position = position_string(self.launcher)
        self.config.save()
        self.health_timer.stop()
        self.tray.hide()
        self.client.close()

    def run_smoke_test(self, report_path: str | None = None) -> int:
        self.start()
        self.launcher.show_launcher()
        self.overlay.set_hide_on_focus_out(False)
        QTest.qWait(250)

        checks: dict = {}
        checks["backend_url"] = self.client.base_url
        checks["icon_loaded"] = not app_icon().isNull()
        checks["icon_sizes"] = [
            f"{size.width()}x{size.height()}"
            for size in app_icon().availableSizes()
        ]
        checks["tray_icon_set"] = not self.tray.icon().isNull()
        checks["launcher_visible"] = self.launcher.isVisible()
        checks["tray_available"] = self.tray_available
        checks["tray_visible"] = (
            self.tray.isVisible() if self.tray_available else False
        )
        checks["always_on_top"] = bool(
            self.overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        )

        self._show_overlay()
        QTest.qWait(200)
        checks["overlay_visible"] = self.overlay.isVisible()
        self.overlay.hide_overlay()
        QTest.qWait(100)
        checks["overlay_hidden"] = not self.overlay.isVisible()
        self._show_overlay()
        QTest.qWait(150)
        checks["overlay_reopened"] = self.overlay.isVisible()

        self._show_main()
        QTest.qWait(200)
        checks["main_window_visible"] = self.main_window.isVisible()
        self.main_window.hide()
        self._show_overlay()
        QTest.qWait(100)

        self.client.check_health()
        QTest.qWait(1200)
        checks["backend_health_ok"] = self._last_health_ok
        checks["backend_health"] = self._last_health

        result: dict = {}
        failure: dict = {}

        def on_result(data: dict) -> None:
            result.update(data)

        def on_failure(message: str) -> None:
            failure["error"] = message

        self.client.analysisFinished.connect(on_result)
        self.client.analysisFailed.connect(on_failure)
        sample = (
            "Congratulations! You won a $1000 gift card. "
            "Claim now at http://example.invalid/claim"
        )
        self.overlay._analysis.set_input_text(sample)
        checks["analysis_request_sent"] = self.client.analyze(sample)
        deadline = time.monotonic() + 90
        while not result and not failure and time.monotonic() < deadline:
            QTest.qWait(100)
        QTest.qWait(150)
        checks["analysis_completed"] = bool(result)
        checks["analysis_error"] = failure.get("error")
        rendered = self.overlay._analysis.result_view().classification_text()
        checks["analysis_displayed"] = bool(
            result.get("classification")
            and rendered == str(result.get("classification")).upper()
        )
        checks["classification"] = result.get("classification")
        checks["confidence"] = result.get("confidence")
        checks["risk_level"] = result.get("risk_level")
        checks["has_explanation"] = bool(result.get("explanation"))
        checks["analysis_response"] = {
            key: result.get(key)
            for key in (
                "classification",
                "confidence",
                "risk_level",
                "risk_score",
                "model_used",
                "explanation",
                "recommended_action",
            )
        }

        required = [
            "icon_loaded",
            "tray_icon_set",
            "launcher_visible",
            "overlay_visible",
            "overlay_hidden",
            "overlay_reopened",
            "main_window_visible",
            "always_on_top",
            "backend_health_ok",
            "analysis_completed",
            "analysis_displayed",
            "has_explanation",
        ]
        checks["ok"] = all(bool(checks.get(name)) for name in required)
        checks["frozen"] = bool(getattr(sys, "frozen", False))

        report = json.dumps(checks, indent=2)
        if report_path:
            path = Path(report_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")
        else:
            print(report)
        self.shutdown()
        return 0 if checks["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TextShield desktop shell")
    parser.add_argument("--backend-url", default=None)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--smoke-report", default=None)
    args, qt_args = parser.parse_known_args(argv)

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication([sys.argv[0]] + qt_args)
    app.setOrganizationName(ORGANIZATION)
    app.setApplicationName(APPLICATION)
    app.setApplicationDisplayName("TextShield")
    app.setWindowIcon(app_icon())
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    app.setQuitOnLastWindowClosed(False)

    desktop = DesktopApplication(app, args)
    app.aboutToQuit.connect(desktop.shutdown)
    if args.smoke_test:
        return desktop.run_smoke_test(args.smoke_report)
    desktop.start()
    return app.exec()
