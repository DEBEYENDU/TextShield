"""Development entry point for the TextShield desktop shell."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from textshield_desktop.app import main

if __name__ == "__main__":
    raise SystemExit(main())
