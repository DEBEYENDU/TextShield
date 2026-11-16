"""Windows per-user startup registration."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - only on non-Windows
    winreg = None

STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_VALUE = "TextShieldDesktop"


def startup_supported() -> bool:
    return sys.platform == "win32" and winreg is not None


def startup_command() -> str:
    """Return the command Windows should launch at sign-in."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'
    executable = Path(sys.executable)
    pythonw = executable.with_name("pythonw.exe")
    if pythonw.exists():
        executable = pythonw
    script = Path(__file__).resolve().parents[3] / "run_desktop.py"
    return f'"{executable}" "{script}" --startup'


class StartupManager:
    def __init__(
        self,
        key_path: str = STARTUP_KEY,
        value_name: str = STARTUP_VALUE,
        command: str | None = None,
    ) -> None:
        self.key_path = key_path
        self.value_name = value_name
        self._command = command

    @property
    def available(self) -> bool:
        return startup_supported()

    @property
    def command(self) -> str:
        return self._command or startup_command()

    def enabled(self) -> bool:
        if not self.available:
            return False
        assert winreg is not None
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.key_path,
                0,
                winreg.KEY_READ,
            ) as key:
                value, _ = winreg.QueryValueEx(key, self.value_name)
                return bool(value)
        except FileNotFoundError:
            return False

    def set_enabled(self, enabled: bool) -> None:
        if not self.available:
            raise OSError("Start with Windows is only supported on Windows")
        assert winreg is not None
        if enabled:
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                self.key_path,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(
                    key,
                    self.value_name,
                    0,
                    winreg.REG_SZ,
                    self.command,
                )
            return
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.key_path,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, self.value_name)
        except FileNotFoundError:
            return

    def delete_key(self) -> None:
        """Remove the registration key (used by tests)."""
        if not self.available:
            return
        assert winreg is not None
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.key_path)
        except FileNotFoundError:
            return
