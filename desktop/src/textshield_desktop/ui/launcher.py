"""Small always-on-top floating launcher."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..config import DesktopConfig
from .geometry import clamp_point, position_string, restore_position
from .icons import app_icon


class LauncherWindow(QWidget):
    clicked = Signal()
    position_changed = Signal(str)

    def __init__(self, config: DesktopConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._menu: QMenu | None = None
        self._drag_offset: QPoint | None = None
        self._drag_moved = False
        self._always_on_top = config.always_on_top

        self.setWindowTitle("TextShield Launcher")
        self.setWindowIcon(app_icon())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(72, 72)

        self._button = QToolButton()
        self._button.setObjectName("LauncherButton")
        self._button.setIcon(app_icon())
        self._button.setIconSize(QSize(42, 42))
        self._button.setFixedSize(56, 56)
        self._button.setToolTip("Open TextShield")
        self._button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._button.clicked.connect(self.clicked.emit)
        self._button.installEventFilter(self)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 170))
        self._button.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self._button)

        area = self.screen().availableGeometry() if self.screen() else None
        if area is None:
            default = QPoint(100, 100)
        else:
            default = QPoint(
                area.right() - self.width() - 24,
                area.bottom() - self.height() - 24,
            )
        restore_position(self, config.launcher_position, default)
        self.set_always_on_top(config.always_on_top)

    def set_menu(self, menu: QMenu) -> None:
        self._menu = menu

    def show_launcher(self) -> None:
        self.move(clamp_point(self.pos(), self.size()))
        self.show()
        self.raise_()

    def hide_launcher(self) -> None:
        self.hide()

    def set_always_on_top(self, enabled: bool) -> None:
        self._always_on_top = enabled
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        if self.isVisible():
            self.show_launcher()

    def eventFilter(self, watched, event) -> bool:
        if watched is not self._button:
            return super().eventFilter(watched, event)
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_offset = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                self._drag_moved = False
                return True
        elif event.type() == QEvent.Type.MouseMove:
            if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
                target = event.globalPosition().toPoint() - self._drag_offset
                if (target - self.pos()).manhattanLength() > 4:
                    self._drag_moved = True
                self.move(target)
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if self._drag_offset is not None:
                self._drag_offset = None
                self.move(clamp_point(self.pos(), self.size()))
                self.position_changed.emit(position_string(self))
                if not self._drag_moved:
                    self.clicked.emit()
                return True
        elif event.type() == QEvent.Type.ContextMenu:
            if self._menu is not None:
                self._menu.exec(event.globalPos())
                return True
        return super().eventFilter(watched, event)

    def contextMenuEvent(self, event) -> None:
        if self._menu is not None:
            self._menu.exec(event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)

    def closeEvent(self, event) -> None:
        self.hide()
        event.ignore()
