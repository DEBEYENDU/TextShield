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
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from .backend.client import BackendClient
from .config import (
    APPLICATION,
    ORGANIZATION,
    DesktopConfig,
    normalize_backend_url,
)
from .native.clipboard import ClipboardService
from .native.hotkey import GlobalHotkey
from .native.startup import StartupManager
from .native.windows import IS_WINDOWS, foreground_window, is_own_window
from .ui.clipboard_dialog import ClipboardReviewDialog
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
        self._last_external_window = 0
        self._hotkey_error = ""
        self._startup_error = ""
        self._startup_launch = bool(args and getattr(args, "startup", False))

        self.clipboard = ClipboardService(self)
        self.startup = StartupManager()
        self.startup_available = self.startup.available
        if self.startup_available:
            try:
                self.config.start_with_windows = self.startup.enabled()
            except OSError as exc:
                self.config.start_with_windows = False
                self._startup_error = str(exc)
        else:
            self.config.start_with_windows = False

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
        self.hotkey = GlobalHotkey(self)
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
            area.bottom() - 520 - 96,
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
        self.overlay.navigate_requested.connect(self._show_main_section)
        self.overlay.settings_requested.connect(self.show_settings)
        self.overlay.open_dashboard_requested.connect(self.open_dashboard)
        self.overlay.analyze_clipboard_requested.connect(
            self.analyze_clipboard
        )
        self.overlay.copy_selection_requested.connect(
            self.copy_selected_text
        )
        self.overlay.clear_clipboard_requested.connect(self.clear_clipboard)
        self.main_window.open_dashboard_requested.connect(self.open_dashboard)
        self.main_window.settings_requested.connect(self.show_settings)
        self.main_window.analyze_clipboard_requested.connect(
            self.analyze_clipboard
        )
        self.main_window.copy_selection_requested.connect(
            self.copy_selected_text
        )
        self.main_window.clear_clipboard_requested.connect(
            self.clear_clipboard
        )
        self.tray.show_overlay_requested.connect(self._show_overlay)
        self.tray.analyze_clipboard_requested.connect(self.analyze_clipboard)
        self.tray.copy_selection_requested.connect(self.copy_selected_text)
        self.tray.clear_clipboard_requested.connect(self.clear_clipboard)
        self.tray.launcher_toggled.connect(self._set_launcher_visible)
        self.tray.always_on_top_toggled.connect(self._set_always_on_top)
        self.tray.open_dashboard_requested.connect(self.open_dashboard)
        self.tray.settings_requested.connect(self.show_settings)
        self.tray.reconnect_requested.connect(self.reconnect_backend)
        self.tray.startup_toggled.connect(self._set_start_with_windows)
        self.tray.quit_requested.connect(self.quit)
        self.hotkey.activated.connect(self._toggle_overlay)

    def start(self) -> None:
        self.tray.set_startup_available(self.startup_available)
        self.tray.set_start_with_windows(self.config.start_with_windows)
        if self.startup_available and self.config.start_with_windows:
            try:
                self.startup.set_enabled(True)
            except OSError as exc:
                self._startup_error = str(exc)
                try:
                    enabled = self.startup.enabled()
                except OSError:
                    enabled = False
                self.config.start_with_windows = enabled
                self.tray.set_start_with_windows(enabled)
        if self._startup_launch and self.tray_available:
            self.launcher.hide_launcher()
            self.tray.set_launcher_visible(False)
        else:
            self._set_launcher_visible(self.config.launcher_visible)
        self.tray.show()
        if not self.tray_available and not self.launcher.isVisible():
            self._show_main()
        if not self.hotkey.set_shortcut(self.config.hotkey):
            self._hotkey_error = self.hotkey.last_error
            if self.tray_available:
                self.tray.showMessage(
                    "TextShield hotkey",
                    self._hotkey_error,
                    QSystemTrayIcon.MessageIcon.Warning,
                    6000,
                )
        else:
            self._hotkey_error = ""
        self.health_timer.start()
        self.client.check_health()

    def _on_health(self, connected: bool, data: dict) -> None:
        self._last_health_ok = connected
        self._last_health = data
        self.overlay.set_status(connected, data)
        self.main_window.set_backend_status(connected, data)
        self.tray.set_backend_status(connected, self.client.base_url, data)

    def _show_overlay(self, focus_input: bool = True) -> None:
        if not self.overlay.isVisible():
            self._remember_external_window()
        self.overlay.show_overlay(focus_input=focus_input)

    def _toggle_overlay(self) -> None:
        if self.overlay.isVisible() and self.overlay.isActiveWindow():
            self.overlay.hide_overlay()
            return
        self._remember_external_window()
        self.overlay.show_overlay(focus_input=True)

    def _remember_external_window(self) -> None:
        hwnd = foreground_window()
        if hwnd and not is_own_window(hwnd):
            self._last_external_window = hwnd

    def _show_main(self, section: str | None = None) -> None:
        self.overlay.hide_overlay()
        self.main_window.show_main(section)

    def _show_main_section(self, section: str) -> None:
        self._show_main(section)

    def _dialog_parent(self):
        if self.main_window.isVisible():
            return self.main_window
        return self.overlay

    def _show_message(
        self,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
    ) -> None:
        parent = self._dialog_parent()
        lock_overlay = parent is self.overlay
        if lock_overlay:
            self.overlay.set_hide_on_focus_out(False)
        try:
            QMessageBox(
                icon,
                title,
                text,
                QMessageBox.StandardButton.Ok,
                parent,
            ).exec()
        finally:
            if lock_overlay:
                self.overlay.set_hide_on_focus_out(
                    self.config.hide_on_focus_out
                )

    def _ask(self, title: str, text: str) -> bool:
        parent = self._dialog_parent()
        lock_overlay = parent is self.overlay
        if lock_overlay:
            self.overlay.set_hide_on_focus_out(False)
        try:
            answer = QMessageBox.question(
                parent,
                title,
                text,
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            return answer == QMessageBox.StandardButton.Yes
        finally:
            if lock_overlay:
                self.overlay.set_hide_on_focus_out(
                    self.config.hide_on_focus_out
                )

    def _review_text(self, text: str, source: str) -> None:
        if self.main_window.isVisible():
            parent = self.main_window
            target = self.main_window.analysis_widget()
        else:
            self._show_overlay(focus_input=False)
            parent = self.overlay
            target = self.overlay.analysis_widget()
        lock_overlay = parent is self.overlay
        if lock_overlay:
            self.overlay.set_hide_on_focus_out(False)
        try:
            dialog = ClipboardReviewDialog(
                text,
                source=source,
                backend_online=self._last_health_ok,
                parent=parent,
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            target.set_clipboard_text(
                dialog.analysis_text,
                dialog.input_type(),
                source,
            )
            target.submit()
        finally:
            if lock_overlay:
                self.overlay.set_hide_on_focus_out(
                    self.config.hide_on_focus_out
                )

    def analyze_clipboard(self) -> None:
        text = self.clipboard.text()
        if not text.strip():
            self._show_overlay()
            self._show_message(
                QMessageBox.Icon.Information,
                "Analyze Clipboard",
                "The clipboard does not contain text. Copy a message in "
                "another application, then try again.",
            )
            return
        self._review_text(text, "clipboard")

    def copy_selected_text(self) -> None:
        if not IS_WINDOWS:
            self._show_message(
                QMessageBox.Icon.Information,
                "Copy Selected Text",
                "Copying selected text is only supported on Windows.",
            )
            return
        target = self._last_external_window
        if not target or is_own_window(target):
            target = foreground_window()
        if not target or is_own_window(target):
            self._show_overlay()
            self._show_message(
                QMessageBox.Icon.Information,
                "Copy Selected Text",
                "Select text in another application, then press the TextShield "
                "hotkey and choose Copy Selected Text. TextShield does not "
                "inspect other windows in the background.",
            )
            return
        self.overlay.hide_overlay()
        text, error = self.clipboard.capture_selected_text(target)
        if error:
            self._show_overlay()
            self._show_message(
                QMessageBox.Icon.Warning,
                "Copy Selected Text",
                error,
            )
            return
        self._review_text(text, "selection")

    def clear_clipboard(self) -> None:
        if not self.clipboard.has_content():
            self._show_overlay()
            self._show_message(
                QMessageBox.Icon.Information,
                "Clear Clipboard",
                "The clipboard is already empty.",
            )
            return
        if not self._ask(
            "Clear Clipboard",
            "Remove all current clipboard content? This cannot be undone.",
        ):
            return
        self.clipboard.clear()
        if self.tray_available:
            self.tray.showMessage(
                "TextShield",
                "Clipboard cleared.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )

    def reconnect_backend(self) -> None:
        self.client.check_health()

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
        dialog = SettingsDialog(
            self.config,
            None,
            startup_available=self.startup_available,
            hotkey_error=self._hotkey_error,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_config:
            error = self.apply_config(dialog.result_config)
            if error:
                self._show_message(
                    QMessageBox.Icon.Warning,
                    "Settings",
                    error,
                )

    def apply_config(self, config: DesktopConfig) -> str | None:
        errors: list[str] = []
        previous_hotkey = self.config.hotkey
        if config.hotkey != previous_hotkey:
            if not self.hotkey.set_shortcut(config.hotkey):
                error = self.hotkey.last_error
                errors.append(error)
                config.hotkey = previous_hotkey
                self.hotkey.set_shortcut(previous_hotkey)
                self._hotkey_error = error
            else:
                self._hotkey_error = ""
        if self.startup_available:
            try:
                startup_enabled = self.startup.enabled()
            except OSError as exc:
                startup_enabled = False
                errors.append(str(exc))
            if config.start_with_windows != startup_enabled:
                try:
                    self.startup.set_enabled(config.start_with_windows)
                except OSError as exc:
                    errors.append(str(exc))
                    try:
                        config.start_with_windows = self.startup.enabled()
                    except OSError:
                        config.start_with_windows = False
        self.config = config
        self.config.save()
        self.client.set_base_url(config.backend_url)
        self.client.check_health()
        self.overlay.set_hide_on_focus_out(config.hide_on_focus_out)
        self.overlay.set_always_on_top(config.always_on_top)
        self.launcher.set_always_on_top(config.always_on_top)
        self.main_window.set_backend_url(config.backend_url)
        self.tray.set_always_on_top(config.always_on_top)
        self.tray.set_start_with_windows(config.start_with_windows)
        self._set_launcher_visible(config.launcher_visible)
        return "\n".join(errors) or None

    def _set_start_with_windows(self, enabled: bool) -> None:
        if not self.startup_available:
            self.tray.set_start_with_windows(False)
            return
        try:
            self.startup.set_enabled(enabled)
        except OSError as exc:
            try:
                current = self.startup.enabled()
            except OSError:
                current = False
            self.tray.set_start_with_windows(current)
            self._show_message(
                QMessageBox.Icon.Warning,
                "Start with Windows",
                str(exc),
            )
            return
        self.config.start_with_windows = enabled
        self.config.save()
        self.tray.set_start_with_windows(enabled)

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
        self.hotkey.close()
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
        checks["tray_actions"] = self.tray.action_labels()
        checks["tray_analyze_clipboard"] = (
            "Analyze Clipboard" in checks["tray_actions"]
        )
        checks["tray_reconnect"] = (
            "Reconnect Backend" in checks["tray_actions"]
        )
        checks["hotkey_checked"] = QGuiApplication.platformName() != "offscreen"
        checks["hotkey_registered"] = self.hotkey.is_registered
        checks["hotkey"] = self.hotkey.shortcut
        checks["hotkey_error"] = self.hotkey.last_error
        checks["startup_supported"] = self.startup_available
        checks["startup_enabled"] = self.config.start_with_windows
        checks["clipboard_available"] = QGuiApplication.clipboard() is not None
        checks["screen_count"] = len(QGuiApplication.screens())
        checks["screens"] = [
            {
                "name": screen.name(),
                "geometry": screen.geometry().getRect(),
                "available": screen.availableGeometry().getRect(),
                "device_pixel_ratio": screen.devicePixelRatio(),
                "logical_dpi": screen.logicalDotsPerInch(),
            }
            for screen in QGuiApplication.screens()
        ]
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
        self.overlay.hide_overlay()
        QTest.qWait(80)
        self.hotkey.activated.emit()
        QTest.qWait(120)
        checks["hotkey_toggle_show"] = self.overlay.isVisible()

        self._show_main()
        QTest.qWait(200)
        checks["main_window_visible"] = self.main_window.isVisible()
        checks["main_sections"] = self.main_window.section_keys()
        checks["unavailable_sections"] = all(
            self.main_window.page(section) is not None
            for section in ("intelligence", "research")
        )

        def wait_until(predicate, timeout: float = 20.0) -> bool:
            deadline = time.monotonic() + timeout
            while not predicate() and time.monotonic() < deadline:
                QTest.qWait(100)
            return bool(predicate())

        self.main_window.show_main("history")
        history = self.main_window.page("history")
        checks["history_loaded"] = wait_until(
            lambda: history is not None
            and not getattr(history, "_loading", True)
            and bool(getattr(history, "_state").text()),
            20,
        )
        checks["history_total"] = getattr(history, "total", None)
        checks["history_rows"] = (
            getattr(history, "table").rowCount() if history is not None else 0
        )

        self.main_window.show_main("knowledge")
        knowledge = self.main_window.page("knowledge")
        checks["knowledge_loaded"] = wait_until(
            lambda: knowledge is not None and bool(knowledge.status), 20
        )
        checks["knowledge_status"] = (
            knowledge.status if knowledge is not None else {}
        )

        self.main_window.show_main("threat")
        threat = self.main_window.page("threat")
        checks["threat_loaded"] = wait_until(
            lambda: threat is not None
            and bool(threat.status)
            and not getattr(threat, "_pending", set()),
            20,
        )
        checks["threat_providers"] = (
            threat.providers_count if threat is not None else 0
        )
        if threat is not None:
            threat._ioc.setText("http://example.invalid/claim")
            threat._check()
            checks["threat_check_completed"] = wait_until(
                lambda: "completed" in threat._state.text()
                or "failed" in threat._state.text(),
                30,
            )
            checks["threat_check_result"] = threat._results.toPlainText()

        self.main_window.hide()
        self._show_overlay()
        QTest.qWait(100)
        self.overlay.show_menu()
        checks["overlay_menu_open"] = self.overlay.menu_open()
        checks["overlay_menu_items"] = self.overlay.menu_button_count()
        self.overlay._show_analysis()
        checks["overlay_menu_closed"] = not self.overlay.menu_open()

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
        checks["analysis_response"]["risk_factors"] = result.get("risk_factors")
        checks["analysis_response"]["url_count"] = len(result.get("urls") or [])
        checks["analysis_response"]["rag_evidence_count"] = len(
            result.get("rag_evidence") or []
        )

        required = [
            "icon_loaded",
            "tray_icon_set",
            "launcher_visible",
            "overlay_visible",
            "overlay_hidden",
            "overlay_reopened",
            "main_window_visible",
            "main_sections",
            "unavailable_sections",
            "history_loaded",
            "knowledge_loaded",
            "threat_loaded",
            "threat_check_completed",
            "overlay_menu_open",
            "overlay_menu_closed",
            "overlay_menu_items",
            "tray_actions",
            "tray_analyze_clipboard",
            "tray_reconnect",
            "hotkey_toggle_show",
            "startup_supported",
            "clipboard_available",
            "always_on_top",
            "backend_health_ok",
            "analysis_completed",
            "analysis_displayed",
            "has_explanation",
        ]
        if checks.get("hotkey_checked"):
            required.append("hotkey_registered")
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
    parser.add_argument(
        "--startup",
        action="store_true",
        help="Start minimized for the Windows startup entry",
    )
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
