"""Backend URL and window preference dialog."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..backend.client import BackendClient
from ..config import DesktopConfig, normalize_backend_url


class SettingsDialog(QDialog):
    def __init__(
        self, config: DesktopConfig, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.result_config: DesktopConfig | None = None
        self._probe: BackendClient | None = None
        self.setWindowTitle("TextShield Settings")
        self.setModal(True)
        self.resize(500, 330)

        title = QLabel("Connection")
        title.setObjectName("SectionTitle")
        description = QLabel(
            "Point the desktop shell at the TextShield FastAPI server. "
            "The default is a local backend started with python run.py."
        )
        description.setObjectName("Muted")
        description.setWordWrap(True)

        self._url = QLineEdit(config.backend_url)
        self._url.setPlaceholderText("http://127.0.0.1:8000")
        test = QPushButton("Test")
        test.setObjectName("SecondaryButton")
        test.clicked.connect(self._test)
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        url_row.addWidget(self._url, 1)
        url_row.addWidget(test)

        self._probe_status = QLabel("")
        self._probe_status.setObjectName("Muted")
        self._probe_status.setWordWrap(True)
        self._probe_status.hide()

        self._always_on_top = QCheckBox("Keep overlay above other windows")
        self._always_on_top.setChecked(config.always_on_top)
        self._hide_on_focus = QCheckBox("Hide overlay when it loses focus")
        self._hide_on_focus.setChecked(config.hide_on_focus_out)
        self._launcher = QCheckBox("Show floating launcher")
        self._launcher.setChecked(config.launcher_visible)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(url_row)
        layout.addWidget(self._probe_status)
        layout.addSpacing(6)
        layout.addWidget(self._always_on_top)
        layout.addWidget(self._hide_on_focus)
        layout.addWidget(self._launcher)
        layout.addStretch(1)
        layout.addWidget(buttons)

    def _test(self) -> None:
        try:
            url = normalize_backend_url(self._url.text())
        except ValueError as exc:
            self._set_probe_status(str(exc), error=True)
            return
        self._probe_status.setText("Testing connection...")
        self._probe_status.setObjectName("Muted")
        self._probe_status.show()
        if self._probe is not None:
            self._probe.close()
            self._probe.deleteLater()
        self._probe = BackendClient(url, self)
        self._probe.healthChanged.connect(self._on_probe_result)
        self._probe.check_health()

    def _on_probe_result(self, connected: bool, data: dict) -> None:
        if connected:
            status = data.get("status", "ok")
            self._set_probe_status(f"Connected. Backend status: {status}.")
        else:
            self._set_probe_status(
                f"Offline: {data.get('error', 'cannot reach backend')}",
                error=True,
            )

    def _set_probe_status(self, text: str, error: bool = False) -> None:
        self._probe_status.setText(text)
        self._probe_status.setObjectName("ErrorText" if error else "Muted")
        self._probe_status.style().unpolish(self._probe_status)
        self._probe_status.style().polish(self._probe_status)
        self._probe_status.show()

    def _accept(self) -> None:
        try:
            url = normalize_backend_url(self._url.text())
        except ValueError as exc:
            self._set_probe_status(str(exc), error=True)
            return
        self.result_config = replace(
            self.config,
            backend_url=url,
            always_on_top=self._always_on_top.isChecked(),
            hide_on_focus_out=self._hide_on_focus.isChecked(),
            launcher_visible=self._launcher.isChecked(),
        )
        self.accept()

    def done(self, result: int) -> None:
        if self._probe is not None:
            self._probe.close()
        super().done(result)
