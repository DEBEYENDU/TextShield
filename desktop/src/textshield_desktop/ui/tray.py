"""System tray integration and explicit clipboard actions."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .icons import app_icon


class TrayIcon(QSystemTrayIcon):
    show_overlay_requested = Signal()
    analyze_clipboard_requested = Signal()
    copy_selection_requested = Signal()
    clear_clipboard_requested = Signal()
    launcher_toggled = Signal(bool)
    always_on_top_toggled = Signal(bool)
    open_dashboard_requested = Signal()
    settings_requested = Signal()
    reconnect_requested = Signal()
    startup_toggled = Signal(bool)
    quit_requested = Signal()

    def __init__(self, available: bool, parent=None) -> None:
        super().__init__(app_icon(), parent)
        self._available = available
        self.setToolTip("TextShield")

        self._menu = QMenu()
        self._status_action = QAction("Backend: checking...", self._menu)
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)
        self._menu.addSeparator()

        self._open_action = QAction("Open TextShield", self._menu)
        self._open_action.triggered.connect(self.show_overlay_requested.emit)
        self._menu.addAction(self._open_action)

        self._analyze_clipboard_action = QAction("Analyze Clipboard", self._menu)
        self._analyze_clipboard_action.triggered.connect(
            self.analyze_clipboard_requested.emit
        )
        self._menu.addAction(self._analyze_clipboard_action)

        self._copy_selection_action = QAction("Copy Selected Text", self._menu)
        self._copy_selection_action.triggered.connect(
            self.copy_selection_requested.emit
        )
        self._menu.addAction(self._copy_selection_action)

        self._clear_clipboard_action = QAction("Clear Clipboard", self._menu)
        self._clear_clipboard_action.triggered.connect(
            self.clear_clipboard_requested.emit
        )
        self._menu.addAction(self._clear_clipboard_action)

        self._launcher_action = QAction("Show launcher", self._menu)
        self._launcher_action.setCheckable(True)
        self._launcher_action.setChecked(True)
        self._launcher_action.triggered.connect(
            lambda checked: self.launcher_toggled.emit(checked)
        )
        self._menu.addAction(self._launcher_action)

        self._top_action = QAction("Always on top", self._menu)
        self._top_action.setCheckable(True)
        self._top_action.setChecked(True)
        self._top_action.triggered.connect(
            lambda checked: self.always_on_top_toggled.emit(checked)
        )
        self._menu.addAction(self._top_action)

        self._menu.addSeparator()
        dashboard = QAction("Open Dashboard", self._menu)
        dashboard.triggered.connect(self.open_dashboard_requested.emit)
        self._menu.addAction(dashboard)
        settings = QAction("Settings", self._menu)
        settings.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings)
        self._reconnect_action = QAction("Reconnect Backend", self._menu)
        self._reconnect_action.triggered.connect(self.reconnect_requested.emit)
        self._menu.addAction(self._reconnect_action)

        self._startup_action = QAction("Start with Windows", self._menu)
        self._startup_action.setCheckable(True)
        self._startup_action.triggered.connect(
            lambda checked: self.startup_toggled.emit(checked)
        )
        self._menu.addAction(self._startup_action)

        self._menu.addSeparator()
        quit_action = QAction("Exit", self._menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)

        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_overlay_requested.emit()

    def set_always_on_top(self, enabled: bool) -> None:
        self._top_action.setChecked(enabled)

    def set_launcher_visible(self, visible: bool) -> None:
        self._launcher_action.setChecked(visible)

    def set_start_with_windows(self, enabled: bool) -> None:
        self._startup_action.setChecked(enabled)

    def set_startup_available(self, available: bool) -> None:
        self._startup_action.setEnabled(available)
        self._startup_action.setToolTip(
            ""
            if available
            else "Start with Windows is only available on Windows."
        )

    def set_backend_status(
        self, connected: bool, base_url: str, data: dict | None = None
    ) -> None:
        payload = data or {}
        state = "online" if connected else "offline"
        self._status_action.setText(f"Backend: {state}")
        detail = payload.get("error") if not connected else ""
        if detail:
            self._status_action.setToolTip(str(detail))
        else:
            self._status_action.setToolTip(base_url)
        self.setToolTip(f"TextShield \u00b7 backend {state}\n{base_url}")

    def action_labels(self) -> list[str]:
        return [
            action.text()
            for action in self._menu.actions()
            if not action.isSeparator()
        ]

    def show(self) -> None:
        if self._available:
            super().show()

    def is_available(self) -> bool:
        return self._available
