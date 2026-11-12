from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from textshield_desktop.backend.client import BackendClient


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._respond()

    def do_POST(self) -> None:
        self._respond()

    def log_message(self, format: str, *args) -> None:
        return

    def _respond(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        self.server.requests.append((self.command, self.path, body))
        payload = json.dumps(self.server.response).encode("utf-8")
        self.send_response(self.server.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class FakeBackend:
    def __init__(self, response: dict, status: int = 200) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.response = response
        self._server.status = status
        self._server.requests = []
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}"

    @property
    def requests(self) -> list[tuple[str, str, bytes]]:
        return self._server.requests

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


@pytest.fixture
def backend_factory():
    servers: list[FakeBackend] = []

    def make(response: dict, status: int = 200) -> FakeBackend:
        server = FakeBackend(response, status)
        servers.append(server)
        return server

    yield make
    for server in servers:
        server.close()


def test_health_ok(qtbot, backend_factory) -> None:
    server = backend_factory({"status": "ok", "model_loaded": True})
    client = BackendClient(server.url)
    with qtbot.waitSignal(client.healthChanged, timeout=3000) as blocker:
        client.check_health()
    assert blocker.args[0] is True
    assert blocker.args[1]["status"] == "ok"
    client.close()
    qtbot.wait(100)


def test_analyze_returns_real_payload(qtbot, backend_factory) -> None:
    payload = {
        "classification": "PHISHING",
        "confidence": 0.94,
        "risk_level": "HIGH",
        "risk_score": 91,
        "explanation": "The message contains a credential lure.",
        "recommended_action": "Do not click the link.",
        "message_type": "sms",
        "model_used": "test-model",
    }
    server = backend_factory(payload)
    client = BackendClient(server.url)
    with qtbot.waitSignal(client.analysisFinished, timeout=3000) as blocker:
        assert client.analyze("click http://example.invalid") is True
    assert blocker.args[0] == payload
    request = server.requests[0]
    assert request[0] == "POST"
    assert request[1] == "/api/analyze"
    assert b'"input_type": "text"' in request[2]
    client.close()
    qtbot.wait(100)


def test_analyze_error_detail(qtbot, backend_factory) -> None:
    server = backend_factory(
        {"detail": [{"loc": ["body", "message"], "msg": "field required"}]},
        status=422,
    )
    client = BackendClient(server.url)
    with qtbot.waitSignal(client.analysisFailed, timeout=3000) as blocker:
        assert client.analyze("hello") is True
    assert "body.message: field required" in blocker.args[0]
    client.close()
    qtbot.wait(100)


def test_connection_refused(qtbot) -> None:
    server = FakeBackend({"status": "ok"})
    port = server._server.server_port
    server.close()
    client = BackendClient(f"http://127.0.0.1:{port}")
    with qtbot.waitSignal(client.analysisFailed, timeout=5000) as blocker:
        assert client.analyze("hello") is True
    assert "Cannot reach the TextShield backend" in blocker.args[0]
    client.close()
    qtbot.wait(100)
