"""Review dialog shown before clipboard text is analyzed."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class ClipboardReviewDialog(QDialog):
    def __init__(
        self,
        text: str,
        source: str = "clipboard",
        backend_online: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.analysis_text = text
        self._source = source
        self.setWindowTitle(
            "Analyze selected text" if source == "selection" else "Analyze clipboard"
        )
        self.setModal(True)
        self.resize(560, 420)

        heading = QLabel(
            "Review selected text"
            if source == "selection"
            else "Review clipboard text"
        )
        heading.setObjectName("SectionTitle")
        description = QLabel(
            "This text was read once for this action. It will be sent to the "
            "TextShield backend only after you choose Analyze. TextShield does "
            "not monitor the clipboard, and this text is not written to logs or "
            "settings."
        )
        description.setObjectName("Muted")
        description.setWordWrap(True)

        self._preview = QPlainTextEdit()
        self._preview.setPlainText(text)
        self._preview.setReadOnly(True)
        self._preview.setTabChangesFocus(True)

        count = QLabel(f"{len(text):,} characters")
        count.setObjectName("HintText")

        self._input_type = QComboBox()
        self._input_type.setObjectName("InputType")
        self._input_type.addItem("Text", "text")
        self._input_type.addItem("SMS", "sms")
        self._input_type.addItem("Email", "email")
        self._input_type.setFixedWidth(100)
        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        type_label = QLabel("Treat as")
        type_label.setObjectName("Muted")
        type_row.addWidget(type_label)
        type_row.addWidget(self._input_type)
        type_row.addStretch(1)
        type_row.addWidget(count)

        self._offline = QLabel(
            "The backend is currently offline. Analysis will fail until it "
            "reconnects."
        )
        self._offline.setObjectName("ErrorText")
        self._offline.setWordWrap(True)
        self._offline.setVisible(not backend_online)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        analyze = buttons.addButton(
            "Analyze", QDialogButtonBox.ButtonRole.AcceptRole
        )
        analyze.setObjectName("AnalyzeButton")
        analyze.setDefault(True)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(self._preview, 1)
        layout.addLayout(type_row)
        layout.addWidget(self._offline)
        layout.addWidget(buttons)

        self._preview.setFocus()
        self._preview.selectAll()

    def input_type(self) -> str:
        return str(self._input_type.currentData())

    def _accept(self) -> None:
        text = self._preview.toPlainText()
        if not text.strip():
            return
        self.analysis_text = text
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
