from __future__ import annotations

from PySide6.QtCore import QPoint, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from textshield_desktop.ui.geometry import (
    clamp_point,
    position_string,
    restore_position,
)


def test_clamp_point_stays_on_screen() -> None:
    screen = QGuiApplication.primaryScreen()
    assert screen is not None
    area = screen.availableGeometry()
    for point in (QPoint(-100000, -100000), QPoint(100000, 100000)):
        clamped = clamp_point(point, QSize(424, 520))
        assert area.contains(clamped)


def test_restore_position_falls_back_when_offscreen(qtbot) -> None:
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(424, 520)
    restore_position(window, "999999,999999", QPoint(40, 40))
    assert window.pos() == QPoint(40, 40)
    assert position_string(window) == "40,40"


def test_restore_position_uses_saved_position(qtbot) -> None:
    window = QWidget()
    qtbot.addWidget(window)
    window.resize(424, 520)
    restore_position(window, "120,130", QPoint(40, 40))
    assert window.pos() == QPoint(120, 130)
