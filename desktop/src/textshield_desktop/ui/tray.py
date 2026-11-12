"""System tray integration."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .icons import app_icon


class TrayIcon(QSystemTrayIcon):
    show_overlay_requested = Signal()
    launcher_toggled = Signal(bool)
    always_on_top_toggled = Signal(bool)
    open_dashboard_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, available: bool, parent=None) -> None:
        super().__init__(app_icon(), parent)
        self._available = available
        self.setToolTip("TextShield")

        self._menu = QMenu()
        show_overlay = QAction("Show TextShield", self._menu)
        show_overlay.triggered.connect(self.show_overlay_requested.emit)
        self._menu.addAction(show_overlay)

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
        dashboard = QAction("Open dashboard", self._menu)
        dashboard.triggered.connect(self.open_dashboard_requested.emit)
        self._menu.addAction(dashboard)
        settings = QAction("Settings", self._menu)
        settings.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings)

        self._menu.addSeparator()
        quit_action = QAction("Quit", self._menu)
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

    def set_backend_status(self, connected: bool, base_url: str) -> None:
        state = "online" if connected else "offline"
        self.setToolTip(f"TextShield \u00b7 backend {state}\n{base_url}")

    def show(self) -> None:
        if self._available:
            super().show()

    def is_available(self) -> bool:
        return self._available
