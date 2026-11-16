from __future__ import annotations

import ctypes
import sys
import uuid

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QSignalSpy

from textshield_desktop.native import clipboard as clipboard_module
from textshield_desktop.native.clipboard import ClipboardService
from textshield_desktop.native.hotkey import (
    DEFAULT_HOTKEY,
    GlobalHotkey,
    hotkey_parts,
    validate_hotkey,
)
from textshield_desktop.native.startup import StartupManager, startup_command


def test_hotkey_parts_and_validation() -> None:
    modifiers, virtual_key = hotkey_parts(DEFAULT_HOTKEY)
    assert modifiers & 0x0007 == 0x0007
    assert virtual_key == ord("T")
    modifiers, virtual_key = hotkey_parts("Ctrl+Shift+F12")
    assert modifiers & 0x0006 == 0x0006
    assert virtual_key == 0x7B
    assert validate_hotkey(DEFAULT_HOTKEY) is None
    assert validate_hotkey("F12") is not None
    assert validate_hotkey("Ctrl+Alt+Shift") is not None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows hotkey test")
def test_global_hotkey_registers_and_receives_message(qtbot) -> None:
    if QGuiApplication.platformName() == "offscreen":
        pytest.skip("global hotkeys need a native Windows window")
    hotkey = GlobalHotkey()
    try:
        if not hotkey.set_shortcut("Ctrl+Alt+Shift+F12"):
            pytest.skip(f"hotkey unavailable: {hotkey.last_error}")
        user32 = ctypes.windll.user32
        user32.PostMessageW.argtypes = (
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_size_t,
        )
        user32.PostMessageW.restype = ctypes.c_bool
        spy = QSignalSpy(hotkey.activated)
        assert user32.PostMessageW(
            hotkey.native_window_id,
            0x0312,
            hotkey.hotkey_id,
            0,
        )
        qtbot.waitUntil(lambda: spy.count() >= 1, timeout=2000)
        qtbot.wait(100)
        assert spy.count() == 1
    finally:
        hotkey.close()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows clipboard test")
def test_clipboard_read_clear(qtbot) -> None:
    clipboard = QGuiApplication.clipboard()
    assert clipboard is not None
    previous = clipboard.text()
    try:
        service = ClipboardService()
        clipboard.setText("TextShield clipboard test")
        assert service.text() == "TextShield clipboard test"
        assert service.has_content()
        service.clear()
        assert not service.has_content()
    finally:
        if previous:
            clipboard.setText(previous)
        else:
            clipboard.clear()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows selection test")
def test_capture_selected_text(qtbot, monkeypatch) -> None:
    clipboard = QGuiApplication.clipboard()
    assert clipboard is not None
    clipboard.clear()
    service = ClipboardService()
    monkeypatch.setattr(clipboard_module.windows, "is_own_window", lambda hwnd: False)
    monkeypatch.setattr(
        clipboard_module.windows,
        "restore_foreground_window",
        lambda hwnd: True,
    )
    monkeypatch.setattr(
        clipboard_module.windows,
        "send_ctrl_c",
        lambda: clipboard.setText("selected text") or True,
    )
    sequence = iter((1, 2))
    monkeypatch.setattr(
        clipboard_module.windows,
        "clipboard_sequence_number",
        lambda: next(sequence),
    )
    text, error = service.capture_selected_text(12345)
    assert error is None
    assert text == "selected text"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows selection test")
def test_capture_selected_text_rejects_own_window(monkeypatch) -> None:
    monkeypatch.setattr(clipboard_module.windows, "is_own_window", lambda hwnd: True)
    text, error = ClipboardService().capture_selected_text(12345)
    assert text is None
    assert "Switch to the application" in error


@pytest.mark.skipif(sys.platform != "win32", reason="Windows startup test")
def test_startup_manager_toggle() -> None:
    key_path = rf"Software\TextShield\Tests\{uuid.uuid4().hex}"
    manager = StartupManager(
        key_path=key_path,
        value_name="TextShieldDesktopTest",
        command=r'"C:\fake\TextShield.exe" --startup',
    )
    try:
        assert manager.available
        assert not manager.enabled()
        manager.set_enabled(True)
        assert manager.enabled()
        manager.set_enabled(False)
        assert not manager.enabled()
    finally:
        manager.delete_key()


def test_startup_command(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        sys,
        "executable",
        r"C:\Program Files\TextShield\TextShieldDesktop.exe",
    )
    assert startup_command() == (
        r'"C:\Program Files\TextShield\TextShieldDesktop.exe" --startup'
    )
