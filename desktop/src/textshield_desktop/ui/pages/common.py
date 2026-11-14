"""Small helpers shared by API-backed pages."""

from __future__ import annotations

import html
import json
from typing import Any

from PySide6.QtWidgets import QLabel, QWidget


def set_state(label: QLabel, text: str, error: bool = False) -> None:
    label.setText(text)
    label.setObjectName("ErrorText" if error else "Muted")
    label.style().unpolish(label)
    label.style().polish(label)


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def percent(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if 0.0 <= number <= 1.0:
        number *= 100.0
    return f"{number:.1f}%"


def value_text(value: Any, fallback: str = "-") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def short(value: Any, limit: int = 120) -> str:
    text = value_text(value, "")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "\u2026"


def html_block(text: str) -> str:
    return (
        "<div style='color:#c9d6f2;font-family:Consolas,Segoe UI;"
        "font-size:9pt;white-space:pre-wrap;'>"
        + html.escape(text)
        + "</div>"
    )


def page_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageTitle")
    return label


def page_hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("HintText")
    label.setWordWrap(True)
    return label


def page_shell(parent: QWidget) -> tuple:
    """Return (layout, state_label) for a standard page body."""
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    state = QLabel("")
    state.setObjectName("Muted")
    state.setWordWrap(True)
    return layout, state
