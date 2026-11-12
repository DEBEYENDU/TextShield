"""Rendering for the real /api/analyze response."""

from __future__ import annotations

import html
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _confidence(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if 0.0 <= number <= 1.0:
        number *= 100.0
    return f"{number:.1f}%"


def _score(value: Any) -> str:
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return ""


def _short(value: Any, limit: int = 360) -> str:
    text = _text(value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "\u2026"


class ResultView(QWidget):
    def __init__(self, compact: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._compact = compact
        self._classification = QLabel("Awaiting analysis")
        self._classification.setObjectName("ClassificationBadge")
        self._classification.setProperty("classification", "NONE")
        self._confidence = QLabel("Confidence: -")
        self._confidence.setObjectName("Muted")
        self._risk = QLabel("RISK: -")
        self._risk.setObjectName("RiskBadge")
        self._risk.setProperty("risk", "NONE")
        self._explanation = QLabel(
            "Paste a message and run an analysis against the local backend."
        )
        self._explanation.setWordWrap(True)
        self._explanation.setObjectName("Muted")
        self._explanation.setMaximumHeight(108 if compact else 300)
        self._explanation.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._recommendation = QLabel("")
        self._recommendation.setWordWrap(True)
        self._recommendation.setMaximumHeight(78 if compact else 240)
        self._recommendation.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._details = QTextBrowser()
        self._details.setOpenExternalLinks(True)
        self._details.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._details.setMinimumHeight(120)
        self._details.hide()
        self._details_hint = QLabel("")
        self._details_hint.setObjectName("HintText")
        self._details_hint.hide()

        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(self._classification)
        top.addStretch(1)
        top.addWidget(self._confidence)
        top.addWidget(self._risk)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addLayout(top)
        layout.addWidget(self._explanation)
        layout.addWidget(self._recommendation)
        layout.addWidget(self._details_hint)
        layout.addWidget(self._details, 1)

    def clear(self) -> None:
        self._set_badge("Awaiting analysis", "NONE")
        self._confidence.setText("Confidence: -")
        self._set_risk("RISK: -", "NONE")
        self._explanation.setText(
            "Paste a message and run an analysis against the local backend."
        )
        self._explanation.setObjectName("Muted")
        self._refresh(self._explanation)
        self._recommendation.setText("")
        self._details.clear()
        self._details.hide()
        self._details_hint.hide()

    def show_error(self, message: str) -> None:
        self._set_badge("ERROR", "ERROR")
        self._confidence.setText("Confidence: -")
        self._set_risk("RISK: -", "NONE")
        self._explanation.setText(message)
        self._explanation.setObjectName("ErrorText")
        self._refresh(self._explanation)
        self._recommendation.setText("")
        self._details.clear()
        self._details.hide()
        self._details_hint.hide()

    def set_result(self, data: dict[str, Any]) -> None:
        classification = _text(data.get("classification") or "UNKNOWN").upper()
        confidence = _confidence(data.get("confidence"))
        risk_level = _text(data.get("risk_level") or "UNKNOWN").upper()
        risk_score = _score(data.get("risk_score"))

        self._set_badge(classification, classification)
        self._confidence.setText(f"Confidence: {confidence}")
        risk_text = f"RISK: {risk_level}"
        if risk_score:
            risk_text += f" \u00b7 {risk_score}/100"
        self._set_risk(risk_text, risk_level)

        explanation = _text(data.get("explanation")).strip()
        if not explanation:
            explanation = "The backend returned a result without an explanation."
        self._explanation.setText(explanation)
        self._explanation.setObjectName("Muted")
        self._refresh(self._explanation)

        action = _text(data.get("recommended_action")).strip()
        if action:
            self._recommendation.setText(f"Recommended action: {action}")
        else:
            self._recommendation.setText("")
        self._recommendation.setToolTip(action)

        self._details.setHtml(self._build_details(data))
        if self._compact:
            self._details_hint.setText("Open the dashboard for full evidence.")
            self._details_hint.show()
        else:
            self._details.show()

    def classification_text(self) -> str:
        return self._classification.text()

    def confidence_text(self) -> str:
        return self._confidence.text()

    def risk_text(self) -> str:
        return self._risk.text()

    def _set_badge(self, text: str, classification: str) -> None:
        self._classification.setText(text)
        self._classification.setProperty("classification", classification)
        self._refresh(self._classification)

    def _set_risk(self, text: str, risk: str) -> None:
        self._risk.setText(text)
        self._risk.setProperty("risk", risk)
        self._refresh(self._risk)

    @staticmethod
    def _refresh(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _build_details(self, data: dict[str, Any]) -> str:
        rows: list[str] = []

        def add(label: str, value: Any) -> None:
            text = _text(value).strip()
            if text:
                rows.append(
                    f"<p style='margin:3px 0'><b>{html.escape(label)}:</b> "
                    f"{html.escape(_short(text))}</p>"
                )

        add("Message type", data.get("message_type"))
        add("Model", data.get("model_used"))
        intent = data.get("intent")
        if isinstance(intent, dict):
            add("Intent", intent.get("label") or intent.get("intent"))
            add("Intent description", intent.get("description"))
        elif intent:
            add("Intent", intent)

        indicators = data.get("indicators")
        if isinstance(indicators, list) and indicators:
            values = ", ".join(
                _text(item.get("name") if isinstance(item, dict) else item)
                for item in indicators
            )
            add("Indicators", values)

        urls = data.get("urls_found")
        if isinstance(urls, list) and urls:
            add("URLs", ", ".join(_text(url) for url in urls))

        evidence = data.get("evidence")
        if isinstance(evidence, list) and evidence:
            for index, item in enumerate(evidence[:3], start=1):
                if isinstance(item, dict):
                    source = item.get("source") or item.get("document_id") or "RAG"
                    content = item.get("content") or item.get("text") or item
                    add(f"Evidence {index} ({source})", content)
                else:
                    add(f"Evidence {index}", item)

        disclaimer = data.get("disclaimer")
        if disclaimer:
            rows.append(
                f"<p style='margin-top:8px;color:#8ca2c4'>"
                f"{html.escape(_text(disclaimer))}</p>"
            )

        if not rows:
            rows.append(
                "<p style='color:#8ca2c4'>No additional evidence fields were "
                "returned for this message.</p>"
            )
        return (
            "<div style='color:#c9d6f2;font-family:Segoe UI;font-size:9pt;'>"
            + "".join(rows)
            + "</div>"
        )
