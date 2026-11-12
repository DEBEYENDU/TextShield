"""Message input and analysis flow."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..backend.client import BackendClient
from .result_view import ResultView


class AnalysisWidget(QWidget):
    def __init__(
        self, client: BackendClient, compact: bool = False, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._client = client
        self._busy = False
        self._input = QPlainTextEdit()
        self._input.setPlaceholderText(
            "Paste an email, SMS, chat message, or URL to analyze..."
        )
        self._input.setFixedHeight(92 if compact else 120)
        self._input.setTabChangesFocus(True)

        self._analyze = QPushButton("ANALYZE")
        self._analyze.setObjectName("AnalyzeButton")
        self._analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear = QPushButton("Clear")
        self._clear.setObjectName("SecondaryButton")
        self._clear.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self._analyze)
        buttons.addStretch(1)
        buttons.addWidget(self._clear)

        self._error = QLabel("")
        self._error.setObjectName("ErrorText")
        self._error.setWordWrap(True)
        self._error.hide()

        self._result = ResultView(compact=compact)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self._input)
        layout.addLayout(buttons)
        layout.addWidget(self._error)
        layout.addWidget(self._result)

        self._analyze.clicked.connect(self._submit)
        self._clear.clicked.connect(self._clear_all)
        self._input.textChanged.connect(self._update_button)
        self._client.analysisStarted.connect(self._on_started)
        self._client.analysisFinished.connect(self._on_finished)
        self._client.analysisFailed.connect(self._on_failed)

        for sequence in ("Ctrl+Return", "Ctrl+Enter"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(self._submit)

        self._update_button()

    def _update_button(self) -> None:
        self._analyze.setEnabled(bool(self._input.toPlainText().strip()) and not self._busy)

    def _submit(self) -> None:
        if self._busy:
            return
        text = self._input.toPlainText().strip()
        if not text:
            self._show_error("Enter a message before running an analysis.")
            return
        self._error.hide()
        self._result.clear()
        if not self._client.analyze(text):
            self._show_error("An analysis is already running.")

    def _clear_all(self) -> None:
        self._input.clear()
        self._error.hide()
        self._result.clear()
        self._input.setFocus()

    def _on_started(self) -> None:
        self._busy = True
        self._analyze.setText("ANALYZING...")
        self._input.setReadOnly(True)
        self._update_button()

    def _on_finished(self, data: dict) -> None:
        self._busy = False
        self._analyze.setText("ANALYZE")
        self._input.setReadOnly(False)
        self._error.hide()
        self._result.set_result(data)
        self._update_button()

    def _on_failed(self, message: str) -> None:
        self._busy = False
        self._analyze.setText("ANALYZE")
        self._input.setReadOnly(False)
        self._result.show_error(message)
        self._show_error(message)
        self._update_button()

    def _show_error(self, message: str) -> None:
        self._error.setText(message)
        self._error.show()

    def input_text(self) -> str:
        return self._input.toPlainText()

    def set_input_text(self, text: str) -> None:
        self._input.setPlainText(text)

    def result_view(self) -> ResultView:
        return self._result
