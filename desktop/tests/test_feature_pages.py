from __future__ import annotations

import json

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMessageBox

from textshield_desktop.backend.client import BackendClient
from textshield_desktop.config import DesktopConfig
from textshield_desktop.ui.main_window import MainWindow
from textshield_desktop.ui.overlay import OverlayWindow
from textshield_desktop.ui.pages.history_page import HistoryPage
from textshield_desktop.ui.pages.knowledge_page import KnowledgeBasePage
from textshield_desktop.ui.pages.threat_intel_page import ThreatIntelPage


def test_history_page_loads_and_filters(qtbot, api_factory) -> None:
    api = api_factory(
        {
            ("GET", "/api/history"): (
                200,
                {
                    "items": [
                        {
                            "id": 7,
                            "timestamp": "2026-11-14T10:11:12+00:00",
                            "input_type": "sms",
                            "message_hash": "abcdef123456",
                            "classification": "SPAM",
                            "confidence": 0.91,
                            "risk_level": "HIGH",
                            "intent": "prize_claim",
                            "preview": "You won a prize",
                        }
                    ],
                    "total": 1,
                    "limit": 25,
                    "offset": 0,
                },
            )
        }
    )
    client = BackendClient(api.url)
    page = HistoryPage(client)
    qtbot.addWidget(page)
    page.show()
    page.activate()
    qtbot.waitUntil(lambda: page.table.rowCount() == 1, timeout=3000)
    assert page.total == 1
    assert page.table.item(0, 3).text() == "SPAM"
    assert "91.0%" == page.table.item(0, 4).text()
    assert "input_type" not in api.requests[0][1]

    page._input_type.setCurrentIndex(2)
    qtbot.waitUntil(lambda: len(api.requests) >= 2, timeout=3000)
    assert "input_type=sms" in api.requests[-1][1]
    client.close()
    qtbot.wait(50)


def test_knowledge_page_loads_and_rebuilds(qtbot, api_factory, monkeypatch) -> None:
    status = {
        "ready": True,
        "backend": "chromadb",
        "embedding_provider": "sentence_transformers",
        "chunk_count": 105,
        "document_count": 28,
        "categories": ["phishing"],
        "built_at": "2026-08-10T15:30:40+00:00",
    }
    rebuilt = dict(status, backend="rebuilt", chunk_count=106)
    api = api_factory(
        {
            ("GET", "/api/knowledge-base"): (200, status),
            ("POST", "/api/knowledge-base/rebuild"): (200, rebuilt),
        }
    )
    client = BackendClient(api.url)
    page = KnowledgeBasePage(client)
    qtbot.addWidget(page)
    page.show()
    page.activate()
    qtbot.waitUntil(lambda: bool(page.status), timeout=3000)
    assert page._values["chunk_count"].text() == "105"

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    page._rebuild_requested()
    qtbot.waitUntil(
        lambda: page.status.get("backend") == "rebuilt", timeout=3000
    )
    assert page._values["chunk_count"].text() == "106"
    assert api.requests[-1][0] == "POST"
    assert api.requests[-1][1] == "/api/knowledge-base/rebuild"
    client.close()
    qtbot.wait(50)


def test_threat_page_loads_and_checks_ioc(qtbot, api_factory) -> None:
    providers = {
        "providers": [
            {
                "name": "mock",
                "version": "1.0.0",
                "enabled": True,
                "configured": True,
                "capabilities": ["url", "domain"],
            },
            {
                "name": "static",
                "version": "1.0.0",
                "enabled": True,
                "configured": True,
                "capabilities": ["url", "domain"],
            },
        ],
        "config": {"allow_external_lookups": False},
    }
    status = {
        "cache": {"entries": 2},
        "rate_limits": {"limited_events": 0},
        "reputation": {"tracked_iocs": 4},
        "offline_ready": True,
        "external_lookups_allowed": False,
    }
    check = {
        "ioc": "http://example.invalid/claim",
        "ioc_type": "url",
        "results": [
            {
                "provider": "static",
                "verdict": "suspicious",
                "confidence": 0.3,
                "raw_summary": "Non-HTTPS link",
            }
        ],
        "aggregated_verdict": "suspicious",
        "confidence": 0.6,
        "cached": False,
    }
    api = api_factory(
        {
            ("GET", "/api/threat-intel/providers"): (200, providers),
            ("GET", "/api/threat-intel/status"): (200, status),
            ("POST", "/api/threat-intel/check"): (200, check),
        }
    )
    client = BackendClient(api.url)
    page = ThreatIntelPage(client)
    qtbot.addWidget(page)
    page.show()
    page.activate()
    qtbot.waitUntil(
        lambda: page.providers_count == 2 and bool(page.status), timeout=3000
    )
    assert "Offline ready: Yes" in page._summary.text()

    page._ioc.setText("http://example.invalid/claim")
    page._check()
    qtbot.waitUntil(
        lambda: "IOC check completed." in page._state.text(), timeout=3000
    )
    assert "Verdict: suspicious" in page._results.toPlainText()
    body = json.loads(api.requests[-1][2].decode("utf-8"))
    assert body["ioc"] == "http://example.invalid/claim"
    client.close()
    qtbot.wait(50)


def test_overlay_navigation_signals(qtbot) -> None:
    client = BackendClient("http://127.0.0.1:1")
    overlay = OverlayWindow(DesktopConfig(), client, QPoint(20, 20))
    qtbot.addWidget(overlay)
    overlay.show_overlay()
    qtbot.wait(50)
    assert overlay.menu_button_count() == 8
    assert not overlay.menu_open()
    overlay.show_menu()
    assert overlay.menu_open()

    with qtbot.waitSignal(overlay.navigate_requested, timeout=1000) as blocker:
        overlay._menu_buttons[1].click()
    assert blocker.args == ["history"]

    with qtbot.waitSignal(overlay.settings_requested, timeout=1000):
        overlay._menu_buttons[6].click()

    overlay._menu_buttons[0].click()
    assert not overlay.menu_open()
    overlay.hide_overlay()
    client.close()
    qtbot.wait(50)


def test_main_window_has_sections_and_unavailable_pages(qtbot) -> None:
    client = BackendClient("http://127.0.0.1:1")
    window = MainWindow(DesktopConfig(), client, tray_available=True)
    qtbot.addWidget(window)
    assert window.section_keys() == [
        "analyze",
        "history",
        "knowledge",
        "threat",
        "intelligence",
        "research",
    ]
    window.set_section("intelligence")
    assert window.current_section() == "intelligence"
    assert window._nav_buttons["intelligence"].property("unavailable") is True
    window.set_section("research")
    assert window.current_section() == "research"
    client.close()
    qtbot.wait(50)
