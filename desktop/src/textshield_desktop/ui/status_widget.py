"""Shared backend status indicator."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class BackendStatusWidget(QWidget):
    def __init__(self, compact: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._compact = compact
        self._dot = QLabel("\u25cf")
        self._dot.setObjectName("StatusDot")
        self._text = QLabel("Backend: checking...")
        self._text.setObjectName("StatusText")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self._dot)
        layout.addWidget(self._text)
        layout.addStretch(1)

    def set_status(
        self, connected: bool, data: dict[str, Any] | None = None, base_url: str = ""
    ) -> None:
        payload = data or {}
        self._dot.setProperty("online", "true" if connected else "false")
        self._dot.style().unpolish(self._dot)
        self._dot.style().polish(self._dot)
        if not connected:
            text = "Backend offline"
            tooltip = payload.get("error") or "Cannot reach the backend"
        else:
            status = str(payload.get("status", "ok")).lower()
            model = payload.get("model_ready", payload.get("model_loaded"))
            if status not in {"ok", "healthy"}:
                text = f"Backend {status}"
            elif model is False:
                text = "Backend online \u00b7 model unavailable"
            else:
                text = "Backend online"
            if not self._compact and base_url:
                text = f"{text} \u00b7 {base_url}"
            tooltip = (
                f"{base_url}\nstatus={payload.get('status', 'unknown')}\n"
                f"model_ready={payload.get('model_ready', 'unknown')}"
            )
        self._text.setText(text)
        self.setToolTip(tooltip)
