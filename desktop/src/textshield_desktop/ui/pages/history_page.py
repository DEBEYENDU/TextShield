"""Analysis history page backed by GET /api/history."""

from __future__ import annotations

from urllib.parse import urlencode

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...backend.client import BackendClient
from .common import page_hint, percent, set_state, value_text


def _format_time(value: object) -> str:
    text = value_text(value)
    if text == "-":
        return text
    return text.replace("T", " ").replace("+00:00", "").replace("Z", "")


class HistoryPage(QWidget):
    def __init__(self, client: BackendClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._limit = 25
        self._offset = 0
        self._total = 0
        self._loading = False

        self._input_type = QComboBox()
        self._input_type.addItem("All types", None)
        self._input_type.addItem("Text", "text")
        self._input_type.addItem("SMS", "sms")
        self._input_type.addItem("Email", "email")

        self._classification = QComboBox()
        self._classification.addItem("All classes", None)
        self._classification.addItem("SPAM", "SPAM")
        self._classification.addItem("HAM", "HAM")

        self._risk = QComboBox()
        self._risk.addItem("All risk levels", None)
        self._risk.addItem("CRITICAL", "CRITICAL")
        self._risk.addItem("HIGH", "HIGH")
        self._risk.addItem("MEDIUM", "MEDIUM")
        self._risk.addItem("LOW", "LOW")

        self._refresh = QPushButton("Refresh")
        self._refresh.setObjectName("SecondaryButton")
        self._refresh.clicked.connect(self.refresh)

        filters = QHBoxLayout()
        filters.setSpacing(7)
        filters.addWidget(self._input_type)
        filters.addWidget(self._classification)
        filters.addWidget(self._risk)
        filters.addStretch(1)
        filters.addWidget(self._refresh)

        self._state = QLabel("")
        self._state.setObjectName("Muted")
        self._state.setWordWrap(True)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            [
                "ID",
                "Time",
                "Type",
                "Class",
                "Confidence",
                "Risk",
                "Intent",
                "Preview",
            ]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setMinimumHeight(320)
        widths = [48, 140, 65, 70, 85, 70, 80]
        for column, width in enumerate(widths):
            self._table.setColumnWidth(column, width)

        self._page = QLabel("")
        self._page.setObjectName("HintText")
        self._previous = QPushButton("Previous")
        self._previous.setObjectName("SecondaryButton")
        self._previous.clicked.connect(self._previous_page)
        self._next = QPushButton("Next")
        self._next.setObjectName("SecondaryButton")
        self._next.clicked.connect(self._next_page)

        pager = QHBoxLayout()
        pager.setSpacing(8)
        pager.addWidget(self._page)
        pager.addStretch(1)
        pager.addWidget(self._previous)
        pager.addWidget(self._next)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        layout.addWidget(
            page_hint(
                "Read-only view of the existing /api/history endpoint. "
                "Filters and pagination are handled by the backend."
            )
        )
        layout.addLayout(filters)
        layout.addWidget(self._state)
        layout.addWidget(self._table, 1)
        layout.addLayout(pager)

        self._client.requestFinished.connect(self._on_request_finished)
        self._client.requestFailed.connect(self._on_request_failed)
        self._input_type.currentIndexChanged.connect(self._apply_filters)
        self._classification.currentIndexChanged.connect(self._apply_filters)
        self._risk.currentIndexChanged.connect(self._apply_filters)
        self._update_pager()

    def activate(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        if self._loading:
            return
        self._loading = True
        self._refresh.setEnabled(False)
        self._update_pager()
        set_state(self._state, "Loading history...")
        params: list[tuple[str, object]] = [
            ("limit", self._limit),
            ("offset", self._offset),
            ("order_by", "timestamp"),
            ("direction", "desc"),
        ]
        for key, combo in (
            ("input_type", self._input_type),
            ("classification", self._classification),
            ("risk_level", self._risk),
        ):
            value = combo.currentData()
            if value:
                params.append((key, value))
        path = "/api/history?" + urlencode(params)
        if not self._client.get("history", path):
            self._loading = False
            self._refresh.setEnabled(True)
            set_state(self._state, "A history request is already running.", True)

    def _apply_filters(self) -> None:
        self._offset = 0
        self.refresh()

    def _previous_page(self) -> None:
        if self._offset <= 0:
            return
        self._offset = max(0, self._offset - self._limit)
        self.refresh()

    def _next_page(self) -> None:
        if self._offset + self._limit >= self._total:
            return
        self._offset += self._limit
        self.refresh()

    def _on_request_finished(self, operation: str, data: object) -> None:
        if operation != "history":
            return
        self._loading = False
        self._refresh.setEnabled(True)
        if not isinstance(data, dict):
            set_state(self._state, "History response was not an object.", True)
            return
        items = data.get("items")
        if not isinstance(items, list):
            items = []
        self._total = int(data.get("total") or 0)
        self._limit = int(data.get("limit") or self._limit)
        self._offset = int(data.get("offset") or self._offset)
        self._fill(items)
        if items:
            set_state(
                self._state,
                f"Loaded {len(items)} history entries from the backend.",
            )
        else:
            set_state(self._state, "No history entries match the current filters.")
        self._update_pager()

    def _on_request_failed(self, operation: str, message: str) -> None:
        if operation != "history":
            return
        self._loading = False
        self._refresh.setEnabled(True)
        self._update_pager()
        set_state(self._state, message, True)

    def _fill(self, items: list[object]) -> None:
        self._table.setRowCount(len(items))
        for row, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            preview = item.get("preview")
            if not preview:
                digest = value_text(item.get("message_hash"), "")
                preview = f"hash {digest[:12]}" if digest else ""
            values = [
                value_text(item.get("id")),
                _format_time(item.get("timestamp")),
                value_text(item.get("input_type")).upper(),
                value_text(item.get("classification")).upper(),
                percent(item.get("confidence")),
                value_text(item.get("risk_level")).upper(),
                value_text(item.get("intent")),
                value_text(preview, ""),
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 7:
                    cell.setToolTip(value)
                self._table.setItem(row, column, cell)

    def _update_pager(self) -> None:
        if self._total <= 0:
            self._page.setText("No entries")
        else:
            start = self._offset + 1
            end = min(self._offset + self._limit, self._total)
            self._page.setText(f"Showing {start}-{end} of {self._total}")
        self._previous.setEnabled(self._offset > 0 and not self._loading)
        self._next.setEnabled(
            self._offset + self._limit < self._total and not self._loading
        )

    @property
    def total(self) -> int:
        return self._total

    @property
    def table(self) -> QTableWidget:
        return self._table
