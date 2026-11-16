"""Windows global hotkey support using RegisterHotKey."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QWidget

DEFAULT_HOTKEY = "Ctrl+Alt+Shift+T"

_WM_HOTKEY = 0x0312
_MOD_ALT = 0x0001
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_MOD_WIN = 0x0008
_MOD_NOREPEAT = 0x4000
_HOTKEY_ID = 0x5A17

if sys.platform == "win32":
    _user32 = ctypes.windll.user32
    _user32.RegisterHotKey.argtypes = (
        wintypes.HWND,
        ctypes.c_int,
        wintypes.UINT,
        wintypes.UINT,
    )
    _user32.RegisterHotKey.restype = wintypes.BOOL
    _user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
    _user32.UnregisterHotKey.restype = wintypes.BOOL
else:
    _user32 = None

_SPECIAL_KEYS = {
    Qt.Key.Key_Space: 0x20,
    Qt.Key.Key_Tab: 0x09,
    Qt.Key.Key_Escape: 0x1B,
    Qt.Key.Key_Return: 0x0D,
    Qt.Key.Key_Enter: 0x0D,
    Qt.Key.Key_Backspace: 0x08,
    Qt.Key.Key_Delete: 0x2E,
    Qt.Key.Key_Insert: 0x2D,
    Qt.Key.Key_Home: 0x24,
    Qt.Key.Key_End: 0x23,
    Qt.Key.Key_PageUp: 0x21,
    Qt.Key.Key_PageDown: 0x22,
    Qt.Key.Key_Left: 0x25,
    Qt.Key.Key_Up: 0x26,
    Qt.Key.Key_Right: 0x27,
    Qt.Key.Key_Down: 0x28,
    Qt.Key.Key_Pause: 0x13,
    Qt.Key.Key_Print: 0x2C,
    Qt.Key.Key_ScrollLock: 0x91,
    Qt.Key.Key_CapsLock: 0x14,
    Qt.Key.Key_NumLock: 0x90,
}


def hotkey_parts(sequence: str) -> tuple[int, int]:
    """Return Win32 modifier flags and virtual-key code for a shortcut."""
    key_sequence = QKeySequence(sequence)
    if key_sequence.isEmpty() or key_sequence.count() != 1:
        raise ValueError("Hotkey must contain exactly one key combination")
    combination = key_sequence[0]
    key = int(combination.key())
    modifiers = combination.keyboardModifiers()

    win_modifiers = 0
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        win_modifiers |= _MOD_CONTROL
    if modifiers & Qt.KeyboardModifier.AltModifier:
        win_modifiers |= _MOD_ALT
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        win_modifiers |= _MOD_SHIFT
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        win_modifiers |= _MOD_WIN
    if not win_modifiers:
        raise ValueError("Hotkey must include Ctrl, Alt, Shift, or Win")

    if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
        virtual_key = key
    elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
        virtual_key = key
    elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
        virtual_key = 0x70 + (key - Qt.Key.Key_F1)
    else:
        virtual_key = _SPECIAL_KEYS.get(Qt.Key(key), 0)
    if not virtual_key:
        raise ValueError("Use a letter, number, function key, or common key")
    return win_modifiers, virtual_key


def validate_hotkey(sequence: str) -> str | None:
    """Return a human-readable error, or None when the shortcut is usable."""
    try:
        hotkey_parts(sequence)
    except ValueError as exc:
        return str(exc)
    return None


class _HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, owner: "GlobalHotkey") -> None:
        super().__init__()
        self._owner = owner

    def nativeEventFilter(self, event_type, message):  # noqa: N802
        return self._owner._handle_native_event(event_type, message)


class GlobalHotkey(QObject):
    """Register one process-wide hotkey and emit ``activated`` on WM_HOTKEY."""

    activated = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._shortcut = ""
        self._registered = False
        self._last_error = ""
        self._window: QWidget | None = None
        self._filter: _HotkeyEventFilter | None = None
        self._last_hotkey_time = -1

    @property
    def available(self) -> bool:
        return sys.platform == "win32"

    @property
    def shortcut(self) -> str:
        return self._shortcut

    @property
    def is_registered(self) -> bool:
        return self._registered

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def native_window_id(self) -> int:
        return int(self._window.winId()) if self._window is not None else 0

    @property
    def hotkey_id(self) -> int:
        return _HOTKEY_ID

    def set_shortcut(self, sequence: str) -> bool:
        """Register ``sequence``, restoring the previous shortcut on failure."""
        previous = self._shortcut
        self._unregister()
        if not self.available:
            self._last_error = "Global hotkeys are only supported on Windows"
            return False
        if QApplication.platformName() == "offscreen":
            self._last_error = (
                "Global hotkeys need the native Windows window platform"
            )
            return False
        try:
            hotkey_parts(sequence)
        except ValueError as exc:
            self._last_error = str(exc)
            if previous:
                self._register(previous)
            return False
        if not self._ensure_window():
            self._last_error = "Could not create the hotkey window"
            return False
        if not self._register(sequence):
            self._last_error = (
                f"Could not register {sequence}. Another application may be "
                "using that shortcut."
            )
            if previous:
                self._register(previous)
            return False
        self._shortcut = sequence
        self._last_error = ""
        return True

    def unregister(self) -> None:
        self._unregister()

    def close(self) -> None:
        self._unregister()
        app = QApplication.instance()
        if app is not None and self._filter is not None:
            app.removeNativeEventFilter(self._filter)
            self._filter = None
        if self._window is not None:
            self._window.close()
            self._window.deleteLater()
            self._window = None

    def _handle_native_event(self, event_type, message) -> bool:
        if not self._registered or message is None:
            return False
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == _WM_HOTKEY and int(msg.wParam) == _HOTKEY_ID:
                message_time = int(msg.time)
                if message_time and message_time == self._last_hotkey_time:
                    return True
                self._last_hotkey_time = message_time
                self.activated.emit()
                return True
        except (TypeError, ValueError, OSError):
            return False
        return False

    def _ensure_window(self) -> bool:
        if self._window is not None:
            return True
        app = QApplication.instance()
        if app is None:
            return False
        self._window = QWidget()
        self._window.setWindowTitle("TextShield Hotkey")
        self._window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self._window.winId()
        self._filter = _HotkeyEventFilter(self)
        app.installNativeEventFilter(self._filter)
        return True

    def _register(self, sequence: str) -> bool:
        try:
            modifiers, virtual_key = hotkey_parts(sequence)
        except ValueError:
            return False
        if not self._ensure_window():
            return False
        hwnd = self.native_window_id
        registered = bool(
            _user32.RegisterHotKey(
                hwnd,
                _HOTKEY_ID,
                modifiers | _MOD_NOREPEAT,
                virtual_key,
            )
        )
        if registered:
            self._registered = True
            self._shortcut = sequence
        return registered

    def _unregister(self) -> None:
        if not self._registered:
            self._shortcut = ""
            self._last_hotkey_time = -1
            return
        try:
            _user32.UnregisterHotKey(
                self.native_window_id, _HOTKEY_ID
            )
        finally:
            self._registered = False
            self._shortcut = ""
            self._last_hotkey_time = -1
