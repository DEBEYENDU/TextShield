"""Threat-intelligence page backed by the existing threat-intel API."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ...backend.client import BackendClient
from .common import html_block, page_hint, percent, pretty_json, set_state, value_text


def _yes_no(value: Any) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "-"


class ThreatIntelPage(QWidget):
    def __init__(self, client: BackendClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._pending: set[str] = set()
        self._providers: list[dict[str, Any]] = []
        self._status: dict[str, Any] = {}

        self._refresh = QPushButton("Refresh")
        self._refresh.setObjectName("SecondaryButton")
        self._refresh.clicked.connect(self.refresh)
        actions = QHBoxLayout()
        actions.addWidget(self._refresh)
        actions.addStretch(1)

        self._state = QLabel("")
        self._state.setObjectName("Muted")
        self._state.setWordWrap(True)

        self._summary = QLabel("")
        self._summary.setObjectName("Muted")
        self._summary.setWordWrap(True)

        self._providers_table = QTableWidget(0, 5)
        self._providers_table.setHorizontalHeaderLabels(
            ["Provider", "Version", "Enabled", "Configured", "Capabilities"]
        )
        self._providers_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._providers_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self._providers_table.verticalHeader().setVisible(False)
        self._providers_table.horizontalHeader().setStretchLastSection(True)
        self._providers_table.setMinimumHeight(112)
        self._providers_table.setMaximumHeight(170)
        for column in range(4):
            self._providers_table.setColumnWidth(column, 110)

        self._status_details = QTextBrowser()
        self._status_details.setOpenExternalLinks(False)
        self._status_details.setMinimumHeight(80)
        self._status_details.setMaximumHeight(130)

        self._ioc = QLineEdit()
        self._ioc.setPlaceholderText("URL, domain, IP address, or file hash")
        self._ioc.returnPressed.connect(self._check)
        self._check_button = QPushButton("Check IOC")
        self._check_button.setObjectName("AnalyzeButton")
        self._check_button.clicked.connect(self._check)
        ioc_row = QHBoxLayout()
        ioc_row.setSpacing(8)
        ioc_row.addWidget(self._ioc, 1)
        ioc_row.addWidget(self._check_button)

        self._results = QTextBrowser()
        self._results.setOpenExternalLinks(False)
        self._results.setMinimumHeight(150)
        self._results.setHtml(
            html_block(
                "Enter an IOC to query the existing /api/threat-intel/check "
                "endpoint. Provider results are shown exactly as returned."
            )
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(
            page_hint(
                "Uses the existing provider registry, status, and IOC-check "
                "endpoints. No URL is visited by the desktop app."
            )
        )
        layout.addLayout(actions)
        layout.addWidget(self._state)
        layout.addWidget(self._summary)
        layout.addWidget(QLabel("Providers"))
        layout.addWidget(self._providers_table)
        layout.addWidget(QLabel("Cache, rate limits, and reputation"))
        layout.addWidget(self._status_details)
        layout.addWidget(QLabel("Check an IOC"))
        layout.addLayout(ioc_row)
        layout.addWidget(self._results, 1)

        self._client.requestFinished.connect(self._on_request_finished)
        self._client.requestFailed.connect(self._on_request_failed)

    def activate(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        if self._pending:
            return
        self._pending = {"threat_providers", "threat_status"}
        self._refresh.setEnabled(False)
        set_state(self._state, "Loading threat-intelligence status...")
        if not self._client.get("threat_providers", "/api/threat-intel/providers"):
            self._pending.clear()
            self._refresh.setEnabled(True)
            set_state(self._state, "A threat-intel request is already running.", True)
            return
        if not self._client.get("threat_status", "/api/threat-intel/status"):
            self._pending.discard("threat_providers")
            self._pending.clear()
            self._refresh.setEnabled(True)
            set_state(self._state, "A threat-intel request is already running.", True)

    def _check(self) -> None:
        if "threat_check" in self._pending:
            return
        ioc = self._ioc.text().strip()
        if not ioc:
            set_state(self._state, "Enter an IOC before checking.", True)
            return
        self._pending.add("threat_check")
        self._check_button.setEnabled(False)
        self._ioc.setEnabled(False)
        set_state(self._state, "Checking IOC against the existing API...")
        self._results.setHtml(html_block("Waiting for the backend..."))
        if not self._client.post(
            "threat_check",
            "/api/threat-intel/check",
            {"ioc": ioc},
            timeout_ms=30000,
        ):
            self._pending.discard("threat_check")
            self._check_button.setEnabled(True)
            self._ioc.setEnabled(True)
            set_state(self._state, "An IOC check is already running.", True)

    def _on_request_finished(self, operation: str, data: object) -> None:
        if operation == "threat_providers":
            self._pending.discard(operation)
            if isinstance(data, dict):
                providers = data.get("providers")
                self._providers = (
                    [item for item in providers if isinstance(item, dict)]
                    if isinstance(providers, list)
                    else []
                )
                self._fill_providers(self._providers)
                set_state(
                    self._state,
                    f"Loaded {len(self._providers)} threat-intelligence providers.",
                )
            else:
                set_state(self._state, "Provider response was not an object.", True)
            self._finish_pending()
            return
        if operation == "threat_status":
            self._pending.discard(operation)
            if isinstance(data, dict):
                self._status = data
                self._fill_status(data)
                set_state(self._state, "Threat-intelligence status loaded.")
            else:
                set_state(self._state, "Status response was not an object.", True)
            self._finish_pending()
            return
        if operation == "threat_check":
            self._pending.discard(operation)
            self._check_button.setEnabled(True)
            self._ioc.setEnabled(True)
            if isinstance(data, dict):
                self._render_check(data)
                set_state(self._state, "IOC check completed.")
            else:
                self._results.setHtml(
                    html_block("The IOC check response was not an object.")
                )
                set_state(self._state, "Invalid IOC response.", True)
            self._finish_pending()

    def _on_request_failed(self, operation: str, message: str) -> None:
        if operation == "threat_check":
            self._pending.discard(operation)
            self._check_button.setEnabled(True)
            self._ioc.setEnabled(True)
            self._results.setHtml(html_block(message))
        elif operation in {"threat_providers", "threat_status"}:
            self._pending.discard(operation)
        else:
            return
        set_state(self._state, message, True)
        self._finish_pending()

    def _finish_pending(self) -> None:
        if not self._pending:
            self._refresh.setEnabled(True)

    def _fill_providers(self, providers: list[dict[str, Any]]) -> None:
        self._providers_table.setRowCount(len(providers))
        for row, provider in enumerate(providers):
            capabilities = provider.get("capabilities")
            if isinstance(capabilities, list):
                capability_text = ", ".join(str(item) for item in capabilities)
            else:
                capability_text = value_text(capabilities)
            values = [
                value_text(provider.get("name")),
                value_text(provider.get("version")),
                _yes_no(provider.get("enabled")),
                _yes_no(provider.get("configured")),
                capability_text,
            ]
            for column, value in enumerate(values):
                self._providers_table.setItem(
                    row, column, QTableWidgetItem(value)
                )

    def _fill_status(self, data: dict[str, Any]) -> None:
        cache = data.get("cache") if isinstance(data.get("cache"), dict) else {}
        reputation = (
            data.get("reputation")
            if isinstance(data.get("reputation"), dict)
            else {}
        )
        self._summary.setText(
            f"Offline ready: {_yes_no(data.get('offline_ready'))} \u00b7 "
            f"External lookups: {_yes_no(data.get('external_lookups_allowed'))} \u00b7 "
            f"Cache entries: {value_text(cache.get('entries'), '0')} \u00b7 "
            f"Tracked IOCs: {value_text(reputation.get('tracked_iocs'), '0')}"
        )
        self._status_details.setHtml(html_block(pretty_json(data)))

    def _render_check(self, data: dict[str, Any]) -> None:
        lines = [
            f"IOC: {value_text(data.get('ioc'))}",
            f"Type: {value_text(data.get('ioc_type'))}",
            f"Verdict: {value_text(data.get('aggregated_verdict'))}",
            f"Confidence: {percent(data.get('confidence'))}",
            f"Cached: {_yes_no(data.get('cached'))}",
            "",
            "Provider results:",
        ]
        results = data.get("results")
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    "- "
                    f"{value_text(item.get('provider'))}: "
                    f"{value_text(item.get('verdict'))} "
                    f"({percent(item.get('confidence'))})"
                    + (
                        f" \u2014 {item.get('raw_summary')}"
                        if item.get("raw_summary")
                        else ""
                    )
                )
        if len(lines) == 7:
            lines.append("- No provider results returned.")
        self._results.setHtml(html_block("\n".join(lines)))

    @property
    def providers_count(self) -> int:
        return len(self._providers)

    @property
    def status(self) -> dict[str, Any]:
        return dict(self._status)
