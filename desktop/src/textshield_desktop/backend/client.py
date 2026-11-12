"""HTTP client for the existing TextShield FastAPI backend.

The desktop shell never imports backend business logic. It talks to the
existing API over loopback HTTP and renders the returned JSON as-is.
"""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import QByteArray, QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class BackendClient(QObject):
    healthChanged = Signal(bool, dict)
    analysisStarted = Signal()
    analysisFinished = Signal(dict)
    analysisFailed = Signal(str)

    def __init__(self, base_url: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._base_url = ""
        self._health_reply: QNetworkReply | None = None
        self._analysis_reply: QNetworkReply | None = None
        self.set_base_url(base_url)

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def is_busy(self) -> bool:
        return self._analysis_reply is not None

    def set_base_url(self, base_url: str) -> None:
        self._base_url = (base_url or "").rstrip("/")

    def _url(self, path: str) -> QUrl:
        return QUrl(self._base_url + path)

    def check_health(self) -> None:
        if self._health_reply is not None:
            return
        request = QNetworkRequest(self._url("/api/health"))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        request.setTransferTimeout(4000)
        reply = self._manager.get(request)
        self._health_reply = reply
        reply.finished.connect(lambda: self._on_health_finished(reply))

    def analyze(self, text: str) -> bool:
        if self._analysis_reply is not None:
            return False
        payload = json.dumps({"input_type": "text", "message": text}).encode("utf-8")
        request = QNetworkRequest(self._url("/api/analyze"))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        request.setTransferTimeout(90000)
        self._analysis_reply = self._manager.post(request, QByteArray(payload))
        self._analysis_reply.finished.connect(
            lambda: self._on_analysis_finished(self._analysis_reply)
        )
        self.analysisStarted.emit()
        return True

    def close(self) -> None:
        for reply in (self._health_reply, self._analysis_reply):
            if reply is not None:
                reply.abort()
        self._health_reply = None
        self._analysis_reply = None

    def _on_health_finished(self, reply: QNetworkReply) -> None:
        self._health_reply = None
        try:
            status = reply.attribute(
                QNetworkRequest.Attribute.HttpStatusCodeAttribute
            )
            data = self._read_json(reply)
            if status is not None and int(status) >= 400:
                self.healthChanged.emit(
                    False,
                    {
                        "error": self._format_detail(
                            data, f"Backend returned HTTP {status}"
                        )
                    },
                )
            elif reply.error() == QNetworkReply.NetworkError.NoError:
                if status is not None and 200 <= int(status) < 300:
                    self.healthChanged.emit(True, data)
                else:
                    self.healthChanged.emit(
                        False,
                        {"error": f"Backend returned HTTP {status}"},
                    )
            else:
                self.healthChanged.emit(False, {"error": reply.errorString()})
        finally:
            reply.deleteLater()

    def _on_analysis_finished(self, reply: QNetworkReply) -> None:
        self._analysis_reply = None
        try:
            status = reply.attribute(
                QNetworkRequest.Attribute.HttpStatusCodeAttribute
            )
            data = self._read_json(reply)
            if status is not None and int(status) >= 400:
                self.analysisFailed.emit(
                    self._format_detail(data, f"Backend returned HTTP {status}")
                )
            elif reply.error() == QNetworkReply.NetworkError.NoError:
                if status is not None and 200 <= int(status) < 300:
                    self.analysisFinished.emit(data)
                else:
                    self.analysisFailed.emit(
                        self._format_detail(
                            data, f"Backend returned HTTP {status}"
                        )
                    )
            else:
                self.analysisFailed.emit(
                    self._connection_error(reply.errorString())
                )
        except Exception as exc:
            self.analysisFailed.emit(f"Could not parse backend response: {exc}")
        finally:
            reply.deleteLater()

    def _connection_error(self, detail: str) -> str:
        return (
            f"Cannot reach the TextShield backend at {self._base_url}.\n"
            f"{detail}\n"
            "Start the backend with: python run.py"
        )

    @staticmethod
    def _read_json(reply: QNetworkReply) -> dict[str, Any]:
        raw = bytes(reply.readAll())
        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {"data": value}

    @staticmethod
    def _format_detail(data: dict[str, Any], fallback: str) -> str:
        detail = data.get("detail") or data.get("error")
        if isinstance(detail, list):
            parts: list[str] = []
            for item in detail:
                if isinstance(item, dict):
                    location = ".".join(str(part) for part in item.get("loc", []))
                    message = str(item.get("msg", "invalid value"))
                    parts.append(f"{location}: {message}" if location else message)
                else:
                    parts.append(str(item))
            return "; ".join(parts) or fallback
        if detail:
            return str(detail)
        return fallback
