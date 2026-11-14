"""Knowledge-base status and rebuild page backed by existing endpoints."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...backend.client import BackendClient
from .common import page_hint, set_state, value_text


class KnowledgeBasePage(QWidget):
    def __init__(self, client: BackendClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._loading = False
        self._status: dict[str, Any] = {}

        self._refresh = QPushButton("Refresh")
        self._refresh.setObjectName("SecondaryButton")
        self._refresh.clicked.connect(self.refresh)
        self._rebuild = QPushButton("Rebuild")
        self._rebuild.setObjectName("SecondaryButton")
        self._rebuild.clicked.connect(self._rebuild_requested)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self._refresh)
        actions.addWidget(self._rebuild)
        actions.addStretch(1)

        self._state = QLabel("")
        self._state.setObjectName("Muted")
        self._state.setWordWrap(True)

        card = QFrame()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)
        self._values: dict[str, QLabel] = {}
        fields = [
            ("Ready", "ready"),
            ("Backend", "backend"),
            ("Embedding provider", "embedding_provider"),
            ("Chunks", "chunk_count"),
            ("Documents", "document_count"),
            ("Built at", "built_at"),
            ("Categories", "categories"),
        ]
        for row, (label, key) in enumerate(fields):
            name = QLabel(label)
            name.setObjectName("Muted")
            value = QLabel("-")
            value.setWordWrap(True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._values[key] = value
            grid.addWidget(name, row, 0)
            grid.addWidget(value, row, 1)
        grid.setColumnStretch(1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(
            page_hint(
                "Reads the existing /api/knowledge-base status and can call the "
                "existing rebuild endpoint. The desktop app never opens or "
                "creates its own vector database."
            )
        )
        layout.addLayout(actions)
        layout.addWidget(self._state)
        layout.addWidget(card)
        layout.addStretch(1)

        self._client.requestFinished.connect(self._on_request_finished)
        self._client.requestFailed.connect(self._on_request_failed)

    def activate(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self._set_buttons(False)
        set_state(self._state, "Loading knowledge-base status...")
        if not self._client.get("kb_status", "/api/knowledge-base"):
            self._loading = False
            self._set_buttons(True)
            set_state(
                self._state,
                "A knowledge-base request is already running.",
                True,
            )

    def _rebuild_requested(self) -> None:
        if self._loading:
            return
        answer = QMessageBox.question(
            self,
            "Rebuild knowledge base",
            "Rebuild the existing vector database from the knowledge_base "
            "directory? This can take several minutes and replaces the current "
            "index.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._loading = True
        self._set_buttons(False)
        set_state(
            self._state,
            "Rebuilding knowledge base... This can take several minutes.",
        )
        if not self._client.post(
            "kb_rebuild",
            "/api/knowledge-base/rebuild",
            timeout_ms=600000,
        ):
            self._loading = False
            self._set_buttons(True)
            set_state(
                self._state,
                "A knowledge-base request is already running.",
                True,
            )

    def _set_buttons(self, enabled: bool) -> None:
        self._refresh.setEnabled(enabled)
        self._rebuild.setEnabled(enabled)

    def _on_request_finished(self, operation: str, data: object) -> None:
        if operation not in {"kb_status", "kb_rebuild"}:
            return
        self._loading = False
        self._set_buttons(True)
        if not isinstance(data, dict):
            set_state(self._state, "Knowledge-base response was not an object.", True)
            return
        self._status = data
        self._populate(data)
        if operation == "kb_rebuild":
            set_state(self._state, "Knowledge base rebuilt successfully.")
        else:
            set_state(self._state, "Knowledge-base status loaded.")

    def _on_request_failed(self, operation: str, message: str) -> None:
        if operation not in {"kb_status", "kb_rebuild"}:
            return
        self._loading = False
        self._set_buttons(True)
        set_state(self._state, message, True)

    def _populate(self, data: dict[str, Any]) -> None:
        ready = data.get("ready")
        self._values["ready"].setText(
            "Yes" if ready is True else "No" if ready is False else "-"
        )
        self._values["backend"].setText(value_text(data.get("backend")))
        self._values["embedding_provider"].setText(
            value_text(data.get("embedding_provider"))
        )
        self._values["chunk_count"].setText(value_text(data.get("chunk_count")))
        self._values["document_count"].setText(
            value_text(data.get("document_count"))
        )
        self._values["built_at"].setText(value_text(data.get("built_at")))
        categories = data.get("categories")
        if isinstance(categories, list) and categories:
            self._values["categories"].setText(", ".join(str(c) for c in categories))
        else:
            self._values["categories"].setText("-")

    @property
    def status(self) -> dict[str, Any]:
        return dict(self._status)
