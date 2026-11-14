from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._respond()

    def do_POST(self) -> None:
        self._respond()

    def do_DELETE(self) -> None:
        self._respond()

    def log_message(self, format: str, *args) -> None:
        return

    def _respond(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        self.server.requests.append((self.command, self.path, body))
        path = self.path.split("?", 1)[0]
        status, payload = self.server.routes.get(
            (self.command, path), (404, {"detail": "not found"})
        )
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class FakeApi:
    def __init__(self, routes: dict[tuple[str, str], tuple[int, Any]]) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.routes = routes
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
