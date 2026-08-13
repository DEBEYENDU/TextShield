"""File system utilities: safe path handling, JSON I/O, atomic writes."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def ensure_dir(path: Path | str) -> Path:
    """Create a directory (and parents) if missing; return the Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_json(path: Path | str, default: Any = None) -> Any:
    """Read a JSON file; return ``default`` on missing/corrupt files."""
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path | str, payload: Any, indent: int = 2) -> bool:
    """Write a JSON file atomically (temp file + rename)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=indent)
        os.replace(tmp, p)
        return True
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def is_within(base: Path | str, candidate: Path | str) -> bool:
    """True when ``candidate`` resolves inside ``base``."""
    base_resolved = Path(base).resolve()
    candidate_resolved = Path(candidate).resolve()
    return candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents