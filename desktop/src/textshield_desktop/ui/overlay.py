"""Frameless floating overlay with compact feature navigation."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..backend.client import BackendClient
from ..config import DesktopConfig
from .analysis_widget import AnalysisWidget
from .geometry import clamp_point, position_string, restore_position
from .icons import app_icon
from .status_widget import BackendStatusWidget


class TitleBar(QWidget):
    drag_finished = Signal()
    expand_requested = Signal()
    menu_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(38)
        self._drag_offset: QPoint | None = None

        icon = QLabel()
        icon.setPixmap(app_icon().pixmap(22, 22))
        title = QLabel("TextShield")
        title.setObjectName("OverlayTitle")

        self._menu = QToolButton()
        self._menu.setObjectName("IconButton")
        self._menu.setText("\u2630")
        self._menu.setToolTip("Navigate")
        self._menu.clicked.connect(self.menu_requested.emit)

        self._expand = QToolButton()
        self._expand.setObjectName("IconButton")
        self._expand.setText("\u2922")
        self._expand.setToolTip("Open full window")
        self._expand.clicked.connect(self.expand_requested.emit)

        minimize = QToolButton()
        minimize.setObjectName("IconButton")
        minimize.setText("\u2014")
        minimize.setToolTip("Hide overlay")
        minimize.clicked.connect(lambda: self.window().hide())

        close = QToolButton()
        close.setObjectName("IconButton")
        close.setText("\u00d7")
        close.setToolTip("Hide overlay")
        close.clicked.connect(lambda: self.window().hide())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 5, 5)
        layout.setSpacing(7)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(self._menu)
        layout.addWidget(self._expand)
        layout.addWidget(minimize)
        layout.addWidget(close)

    def set_menu_open(self, opened: bool) -> None:
        self._menu.setText("\u2190" if opened else "\u2630")
        self._menu.setToolTip("Back to analysis" if opened else "Navigate")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_offset is not None:
            self._drag_offset = None
            self.drag_finished.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.expand_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class OverlayWindow(QWidget):
    position_changed = Signal(str)
    expand_requested = Signal()
    open_dashboard_requested = Signal()
    navigate_requested = Signal(str)
    settings_requested = Signal()

    def __init__(
        self,
        config: DesktopConfig,
        client: BackendClient,
        default_position: QPoint | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self._client = client
        self._hide_on_focus_out = config.hide_on_focus_out
        self._always_on_top = config.always_on_top
        self._menu_buttons: list[QPushButton] = []
        self.setWindowTitle("TextShield")
        self.setWindowIcon(app_icon())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(424, 520)
        self._build()
        restore_position(
            self,
            config.overlay_geometry,
            default_position or QPoint(80, 80),
        )
        self.set_always_on_top(config.always_on_top)

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(0)

        self._root = QFrame()
        self._root.setObjectName("OverlayRoot")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 170))
        self._root.setGraphicsEffect(shadow)
        outer.addWidget(self._root)

        layout = QVBoxLayout(self._root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._title_bar = TitleBar()
        self._title_bar.drag_finished.connect(self._on_drag_finished)
        self._title_bar.expand_requested.connect(self.expand_requested.emit)
        self._title_bar.menu_requested.connect(self._toggle_menu)
        layout.addWidget(self._title_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 8, 16, 14)
        content_layout.setSpacing(9)

        self._stack = QStackedWidget()
        self._analysis_page = QWidget()
        analysis_layout = QVBoxLayout(self._analysis_page)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(0)
        self._analysis = AnalysisWidget(self._client, compact=True)
        analysis_layout.addWidget(self._analysis)
        self._stack.addWidget(self._analysis_page)

        self._menu_page = QWidget()
        menu_layout = QVBoxLayout(self._menu_page)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(5)
        menu_title = QLabel("Navigate")
        menu_title.setObjectName("SectionTitle")
        menu_layout.addWidget(menu_title)
        for label, key, unavailable in (
            ("Analyze", "analyze", False),
            ("History", "history", False),
            ("Knowledge Base", "knowledge", False),
            ("Threat Intelligence", "threat", False),
            ("Intelligence \u00b7 unavailable", "intelligence", True),
            ("Research \u00b7 unavailable", "research", True),
            ("Settings", "settings", False),
            ("Open Full Dashboard", "dashboard", False),
        ):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if unavailable:
                button.setProperty("unavailable", True)
                button.setToolTip(
                    "The running backend does not mount this API. "
                    "Open the full window for details."
                )
            button.clicked.connect(
                lambda checked=False, action=key: self._menu_action(action)
            )
            menu_layout.addWidget(button)
            self._menu_buttons.append(button)
        menu_layout.addStretch(1)
        self._stack.addWidget(self._menu_page)
        content_layout.addWidget(self._stack, 1)

        status_row = QHBoxLayout()
        status_row.setSpacing(5)
        self._status = BackendStatusWidget(compact=True)
        dashboard = QPushButton("Dashboard")
        dashboard.setObjectName("LinkButton")
        dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        dashboard.clicked.connect(self.open_dashboard_requested.emit)
        status_row.addWidget(self._status, 1)
        status_row.addWidget(dashboard)
        content_layout.addLayout(status_row)
        layout.addWidget(content)
        self._show_analysis()

    def _menu_action(self, action: str) -> None:
        if action == "analyze":
            self._show_analysis()
        elif action == "settings":
            self.settings_requested.emit()
        elif action == "dashboard":
            self.open_dashboard_requested.emit()
        else:
            self.navigate_requested.emit(action)

    def _toggle_menu(self) -> None:
        if self._stack.currentWidget() is self._analysis_page:
            self.show_menu()
        else:
            self._show_analysis()

    def _show_analysis(self) -> None:
        self._stack.setCurrentWidget(self._analysis_page)
        self._title_bar.set_menu_open(False)

    def show_menu(self) -> None:
        self._stack.setCurrentWidget(self._menu_page)
        self._title_bar.set_menu_open(True)

    def show_overlay(self) -> None:
        self._show_analysis()
        self.move(clamp_point(self.pos(), self.size()))
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_overlay(self) -> None:
        self.hide()
        self._save_position()

    def set_always_on_top(self, enabled: bool) -> None:
        self._always_on_top = enabled
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if self.isVisible():
            self.show_overlay()

    def set_hide_on_focus_out(self, enabled: bool) -> None:
        self._hide_on_focus_out = enabled

    def set_status(self, connected: bool, data: dict) -> None:
        self._status.set_status(connected, data, self._client.base_url)

    def menu_open(self) -> bool:
        return self._stack.currentWidget() is self._menu_page

    def menu_button_count(self) -> int:
        return len(self._menu_buttons)

    def _on_drag_finished(self) -> None:
        self.move(clamp_point(self.pos(), self.size()))
        self._save_position()

    def _save_position(self) -> None:
        self.position_changed.emit(position_string(self))

    def event(self, event) -> bool:
        if (
            event.type() == QEvent.Type.WindowDeactivate
            and self._hide_on_focus_out
            and self.isVisible()
        ):
            QTimer.singleShot(140, self._hide_if_inactive)
        return super().event(event)

    def _hide_if_inactive(self) -> None:
        if self.isVisible() and not self.isActiveWindow():
            self.hide_overlay()

    def showEvent(self, event) -> None:
        self.move(clamp_point(self.pos(), self.size()))
        super().showEvent(event)

    def closeEvent(self, event) -> None:
        self.hide()
        self._save_position()
        event.ignore()
