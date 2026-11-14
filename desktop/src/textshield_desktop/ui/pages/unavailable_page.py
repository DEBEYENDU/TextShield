"""Transparent placeholder for functionality not mounted by the backend."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .common import page_hint


class UnavailablePage(QWidget):
    def __init__(
        self,
        title: str,
        summary: str,
        details: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        badge = QLabel("NOT AVAILABLE IN THIS BACKEND")
        badge.setObjectName("UnavailableBadge")
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        body = QLabel(summary)
        body.setWordWrap(True)
        body.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        detail = QLabel(details)
        detail.setObjectName("Muted")
        detail.setWordWrap(True)
        detail.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(badge)
        card_layout.addWidget(heading)
        card_layout.addWidget(body)
        card_layout.addWidget(detail)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(
            page_hint(
                "The desktop client only connects to routes that are registered "
                "in the running FastAPI app. No mock data is shown here."
            )
        )
        layout.addWidget(card)
        layout.addStretch(1)
