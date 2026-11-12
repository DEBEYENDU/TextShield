"""Window placement helpers that respect Windows display scaling."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def clamp_point(point: QPoint, size) -> QPoint:
    screen = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
    if screen is None:
        return point
    area = screen.availableGeometry()
    x = max(area.left(), min(point.x(), area.right() - size.width() + 1))
    y = max(area.top(), min(point.y(), area.bottom() - size.height() + 1))
    return QPoint(x, y)


def restore_position(window: QWidget, saved: str, default_point: QPoint) -> None:
    if saved:
        try:
            x_text, y_text = saved.split(",", 1)
            point = QPoint(int(x_text), int(y_text))
            rect = QRect(point, window.size())
            if any(
                screen.availableGeometry().intersects(rect)
                for screen in QGuiApplication.screens()
            ):
                window.move(point)
                return
        except (TypeError, ValueError):
            pass
    window.move(clamp_point(default_point, window.size()))


def position_string(window: QWidget) -> str:
    return f"{window.x()},{window.y()}"
