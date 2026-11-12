"""Full desktop window."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..backend.client import BackendClient
from ..config import DesktopConfig
from .analysis_widget import AnalysisWidget
from .icons import app_icon
from .status_widget import BackendStatusWidget


class MainWindow(QMainWindow):
    open_dashboard_requested = Signal()
    settings_requested = Signal()
    hide_requested = Signal()

    def __init__(
        self,
        config: DesktopConfig,
        client: BackendClient,
        tray_available: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tray_available = tray_available
        self.setWindowTitle("TextShield")
        self.setWindowIcon(app_icon())
        self.resize(780, 780)
        self.setMinimumSize(560, 560)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(12)
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(48, 48))
        titles = QVBoxLayout()
        titles.setSpacing(1)
        title = QLabel("TextShield")
        title.setObjectName("Title")
        subtitle = QLabel("Explainable message risk analysis")
        subtitle.setObjectName("Subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addWidget(logo)
        header.addLayout(titles)
        header.addStretch(1)
        self._status = BackendStatusWidget(compact=False)
        header.addWidget(self._status)
        root.addLayout(header)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 18)
        card_layout.setSpacing(10)
        section = QLabel("Analyze a message")
        section.setObjectName("SectionTitle")
        hint = QLabel(
            "Runs against the existing TextShield API. No clipboard, OCR, or "
            "screen capture is used."
        )
        hint.setObjectName("HintText")
        hint.setWordWrap(True)
        self._analysis = AnalysisWidget(client, compact=False)
        card_layout.addWidget(section)
        card_layout.addWidget(hint)
        card_layout.addWidget(self._analysis)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(card)
        root.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self._url = QLabel(config.backend_url)
        self._url.setObjectName("HintText")
        self._url.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        footer.addWidget(self._url)
        footer.addStretch(1)

        dashboard = QPushButton("Open dashboard")
        dashboard.setObjectName("SecondaryButton")
        dashboard.clicked.connect(self.open_dashboard_requested.emit)
        settings = QPushButton("Settings")
        settings.setObjectName("SecondaryButton")
        settings.clicked.connect(self.settings_requested.emit)
        hide = QPushButton("Hide to tray" if tray_available else "Close")
        hide.setObjectName("SecondaryButton")
        hide.clicked.connect(self._hide_or_close)
        footer.addWidget(dashboard)
        footer.addWidget(settings)
        footer.addWidget(hide)
        root.addLayout(footer)

        self.setCentralWidget(central)

    def show_main(self) -> None:
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def set_backend_status(self, connected: bool, data: dict) -> None:
        self._status.set_status(connected, data, self._url.text())

    def set_backend_url(self, base_url: str) -> None:
        self._url.setText(base_url)

    def _hide_or_close(self) -> None:
        if self._tray_available:
            self.hide()
            self.hide_requested.emit()
        else:
            QApplication.instance().quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._tray_available:
            self.hide()
            event.ignore()
            return
        QApplication.instance().quit()
        event.accept()
