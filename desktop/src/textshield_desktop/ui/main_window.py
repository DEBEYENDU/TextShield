"""Full desktop window with API-backed feature navigation."""

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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..backend.client import BackendClient
from ..config import DesktopConfig
from .analysis_widget import AnalysisWidget
from .icons import app_icon
from .pages.history_page import HistoryPage
from .pages.knowledge_page import KnowledgeBasePage
from .pages.threat_intel_page import ThreatIntelPage
from .pages.unavailable_page import UnavailablePage
from .status_widget import BackendStatusWidget


class MainWindow(QMainWindow):
    open_dashboard_requested = Signal()
    settings_requested = Signal()
    hide_requested = Signal()

    SECTION_LABELS = {
        "analyze": "Analyze",
        "history": "History",
        "knowledge": "Knowledge Base",
        "threat": "Threat Intelligence",
        "intelligence": "Intelligence",
        "research": "Research",
    }

    def __init__(
        self,
        config: DesktopConfig,
        client: BackendClient,
        tray_available: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tray_available = tray_available
        self._current_section = "analyze"
        self.setWindowTitle("TextShield")
        self.setWindowIcon(app_icon())
        self.resize(1020, 760)
        self.setMinimumSize(820, 600)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(208)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 18, 14, 16)
        side.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(9)
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(36, 36))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("TextShield")
        title.setObjectName("SidebarTitle")
        subtitle = QLabel("Desktop")
        subtitle.setObjectName("HintText")
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        brand.addWidget(logo)
        brand.addLayout(brand_text)
        brand.addStretch(1)
        side.addLayout(brand)
        side.addSpacing(10)

        workspace = QLabel("WORKSPACE")
        workspace.setObjectName("NavSection")
        side.addWidget(workspace)

        self._nav_buttons: dict[str, QPushButton] = {}
        for key, label in self.SECTION_LABELS.items():
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if key in {"intelligence", "research"}:
                button.setProperty("unavailable", True)
                button.setToolTip(
                    "The running backend does not mount this API. "
                    "Open the section for details."
                )
            button.clicked.connect(
                lambda checked=False, section=key: self.set_section(section)
            )
            side.addWidget(button)
            self._nav_buttons[key] = button

        side.addStretch(1)
        self._status = BackendStatusWidget(compact=True)
        side.addWidget(self._status)
        self._url = QLabel(config.backend_url)
        self._url.setObjectName("HintText")
        self._url.setWordWrap(True)
        self._url.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._url.setToolTip(config.backend_url)
        side.addWidget(self._url)
        side.addSpacing(8)

        settings = QPushButton("Settings")
        settings.setObjectName("SecondaryButton")
        settings.clicked.connect(self.settings_requested.emit)
        dashboard = QPushButton("Open Full Dashboard")
        dashboard.setObjectName("SecondaryButton")
        dashboard.clicked.connect(self.open_dashboard_requested.emit)
        hide = QPushButton("Hide to tray" if tray_available else "Close")
        hide.setObjectName("SecondaryButton")
        hide.clicked.connect(self._hide_or_close)
        side.addWidget(settings)
        side.addWidget(dashboard)
        side.addWidget(hide)

        root.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 18, 22, 16)
        content_layout.setSpacing(12)
        header = QHBoxLayout()
        header.setSpacing(8)
        self._section_title = QLabel("Analyze")
        self._section_title.setObjectName("PageTitle")
        header.addWidget(self._section_title)
        header.addStretch(1)
        content_layout.addLayout(header)

        self._stack = QStackedWidget()
        self._pages: dict[str, QWidget] = {
            "analyze": AnalysisWidget(client, compact=False),
            "history": HistoryPage(client),
            "knowledge": KnowledgeBasePage(client),
            "threat": ThreatIntelPage(client),
            "intelligence": UnavailablePage(
                "Intelligence",
                "The running backend does not mount an intelligence API, so "
                "this section cannot load candidate data.",
                "Existing module: app/intelligence/api.py "
                "(GET /api/v1/intelligence/candidates, /gaps, /coverage). "
                "It is not registered in app/main.py, and no candidate "
                "generator is wired into the running app. The desktop client "
                "does not call it or fabricate candidates.",
            ),
            "research": UnavailablePage(
                "Research",
                "The running backend does not mount a research API, and the "
                "existing module is an in-memory request stub.",
                "Existing module: app/research/api.py "
                "(POST /api/v1/research/request, GET /api/v1/research/{id}). "
                "It is not registered in app/main.py and has no execution "
                "worker. The desktop client does not expose a create-request "
                "form or simulate research results.",
            ),
        }
        for page in self._pages.values():
            self._stack.addWidget(page)
        content_layout.addWidget(self._stack, 1)
        root.addWidget(content, 1)

        self.setCentralWidget(central)
        self.set_section("analyze")

    def show_main(self, section: str | None = None) -> None:
        if section:
            self.set_section(section)
        self.show()
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def set_section(self, section: str) -> None:
        if section not in self._pages:
            section = "analyze"
        self._current_section = section
        for key, button in self._nav_buttons.items():
            button.setChecked(key == section)
        self._stack.setCurrentWidget(self._pages[section])
        self._section_title.setText(self.SECTION_LABELS.get(section, "Analyze"))
        page = self._pages[section]
        activate = getattr(page, "activate", None)
        if callable(activate):
            activate()

    def current_section(self) -> str:
        return self._current_section

    def section_keys(self) -> list[str]:
        return list(self._pages.keys())

    def page(self, section: str) -> QWidget | None:
        return self._pages.get(section)

    def set_backend_status(self, connected: bool, data: dict) -> None:
        self._status.set_status(connected, data, self._url.text())

    def set_backend_url(self, base_url: str) -> None:
        self._url.setText(base_url)
        self._url.setToolTip(base_url)

    def analysis_widget(self) -> AnalysisWidget:
        return self._pages["analyze"]  # type: ignore[return-value]

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
