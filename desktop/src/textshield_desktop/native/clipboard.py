"""Explicit clipboard actions. No continuous clipboard monitoring."""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, QObject, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from . import windows


class ClipboardService(QObject):
    def text(self) -> str:
        clipboard = QGuiApplication.clipboard()
        return clipboard.text() if clipboard is not None else ""

    def has_content(self) -> bool:
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return False
        mime = clipboard.mimeData()
        return bool(mime and mime.formats())

    def clear(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.clear()

    def capture_selected_text(
        self, target_hwnd: int, timeout_ms: int = 900
    ) -> tuple[str | None, str | None]:
        """Send an explicit Ctrl+C to ``target_hwnd`` and return selected text.

        The caller must have obtained ``target_hwnd`` from an explicit user
        action. This method never runs in the background.
        """
        if not windows.IS_WINDOWS:
            return None, "Copying selected text is only supported on Windows."
        if not target_hwnd or windows.is_own_window(target_hwnd):
            return (
                None,
                "Switch to the application containing the selected text, then "
                "try Copy Selected Text again.",
            )
        if not windows.restore_foreground_window(target_hwnd):
            return (
                None,
                "Windows did not allow TextShield to reactivate the previous "
                "window. Select the text and copy it manually instead.",
            )
        QTest.qWait(120)
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return None, "The Windows clipboard is not available."

        before = windows.clipboard_sequence_number()
        if not windows.send_ctrl_c():
            return None, "TextShield could not send the copy shortcut."

        changed = windows.clipboard_sequence_number() != before
        if not changed:
            loop = QEventLoop()

            def on_changed() -> None:
                loop.quit()

            clipboard.dataChanged.connect(on_changed)
            QTimer.singleShot(timeout_ms, loop.quit)
            loop.exec()
            clipboard.dataChanged.disconnect(on_changed)
            changed = windows.clipboard_sequence_number() != before
        if not changed:
            return (
                None,
                "No selected text was copied. The active application may not "
                "support Ctrl+C, or nothing was selected.",
            )

        text = clipboard.text().strip()
        if not text:
            return (
                None,
                "The selection did not produce text on the clipboard.",
            )
        return text, None
