"""Minimal Win32 helpers for explicit, user-triggered desktop actions.

Nothing in this module watches input or reads other application content.
The helpers only:
- inspect the current foreground window,
- restore a previously active window,
- send an explicit Ctrl+C key chord,
- read the clipboard sequence number.
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    _ULONG_PTR = ctypes.c_size_t

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", _ULONG_PTR),
        ]

    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", _ULONG_PTR),
        ]

    class _HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class _INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("ki", _KEYBDINPUT),
            ("mi", _MOUSEINPUT),
            ("hi", _HARDWAREINPUT),
        ]

    class _INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

    _user32.SendInput.argtypes = (
        wintypes.UINT,
        ctypes.POINTER(_INPUT),
        ctypes.c_int,
    )
    _user32.SendInput.restype = wintypes.UINT
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = (
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    )
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
    _user32.SetForegroundWindow.restype = wintypes.BOOL
    _user32.BringWindowToTop.argtypes = (wintypes.HWND,)
    _user32.BringWindowToTop.restype = wintypes.BOOL
    _user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
    _user32.ShowWindow.restype = wintypes.BOOL
    _user32.IsIconic.argtypes = (wintypes.HWND,)
    _user32.IsIconic.restype = wintypes.BOOL
    _user32.AttachThreadInput.argtypes = (
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.BOOL,
    )
    _user32.AttachThreadInput.restype = wintypes.BOOL
    _user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
    _kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    _INPUT_KEYBOARD = 1
    _KEYEVENTF_KEYUP = 0x0002
    _VK_CONTROL = 0x11
    _VK_C = 0x43
    _SW_RESTORE = 9


def foreground_window() -> int:
    """Return the current foreground HWND, or 0 when unavailable."""
    if not IS_WINDOWS:
        return 0
    return int(_user32.GetForegroundWindow() or 0)


def window_process_id(hwnd: int) -> int:
    """Return the process ID that owns ``hwnd``."""
    if not IS_WINDOWS or not hwnd:
        return 0
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def is_own_window(hwnd: int) -> bool:
    """Return True when ``hwnd`` belongs to this TextShield process."""
    return bool(hwnd) and window_process_id(hwnd) == os.getpid()


def restore_foreground_window(hwnd: int) -> bool:
    """Restore and activate ``hwnd`` after an explicit user action."""
    if not IS_WINDOWS or not hwnd:
        return False
    try:
        if _user32.IsIconic(hwnd):
            _user32.ShowWindow(hwnd, _SW_RESTORE)
        _user32.BringWindowToTop(hwnd)
        if _user32.SetForegroundWindow(hwnd):
            return True

        foreground = _user32.GetForegroundWindow()
        current_thread = _kernel32.GetCurrentThreadId()
        target_thread = _user32.GetWindowThreadProcessId(hwnd, None)
        foreground_thread = (
            _user32.GetWindowThreadProcessId(foreground, None)
            if foreground
            else 0
        )
        attached = False
        if target_thread and current_thread != target_thread:
            attached = bool(
                _user32.AttachThreadInput(
                    current_thread, target_thread, True
                )
            )
        if foreground_thread and current_thread != foreground_thread:
            _user32.AttachThreadInput(
                current_thread, foreground_thread, True
            )
        try:
            return bool(_user32.SetForegroundWindow(hwnd))
        finally:
            if foreground_thread and current_thread != foreground_thread:
                _user32.AttachThreadInput(
                    current_thread, foreground_thread, False
                )
            if attached:
                _user32.AttachThreadInput(
                    current_thread, target_thread, False
                )
    except OSError:
        return False


def send_ctrl_c() -> bool:
    """Send an explicit Ctrl+C chord to the foreground window."""
    if not IS_WINDOWS:
        return False
    inputs = (_INPUT * 4)()
    for index, (virtual_key, flags) in enumerate(
        (
            (_VK_CONTROL, 0),
            (_VK_C, 0),
            (_VK_C, _KEYEVENTF_KEYUP),
            (_VK_CONTROL, _KEYEVENTF_KEYUP),
        )
    ):
        inputs[index].type = _INPUT_KEYBOARD
        inputs[index].ki.wVk = virtual_key
        inputs[index].ki.dwFlags = flags
    sent = _user32.SendInput(4, inputs, ctypes.sizeof(_INPUT))
    return int(sent) == 4


def clipboard_sequence_number() -> int:
    """Return the Windows clipboard sequence number, or 0 if unavailable."""
    if not IS_WINDOWS:
        return 0
    return int(_user32.GetClipboardSequenceNumber())
