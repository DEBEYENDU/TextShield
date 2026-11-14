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
    requestStarted = Signal(str)
    requestFinished = Signal(str, object)
    requestFailed = Signal(str, str)

    def __init__(self, base_url: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._base_url = ""
        self._health_reply: QNetworkReply | None = None
        self._analysis_reply: QNetworkReply | None = None
        self._requests: dict[str, QNetworkReply] = {}
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

    def analyze(self, text: str, input_type: str = "text") -> bool:
        if self._analysis_reply is not None:
            return False
        kind = (input_type or "text").lower()
        if kind not in {"text", "sms", "email"}:
            kind = "text"
        if kind == "email":
            payload = {"input_type": "email", "email_raw": text}
        else:
            payload = {"input_type": kind, "message": text}
        body = json.dumps(payload).encode("utf-8")
        request = QNetworkRequest(self._url("/api/analyze"))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        request.setTransferTimeout(90000)
        self._analysis_reply = self._manager.post(request, QByteArray(body))
        self._analysis_reply.finished.connect(
            lambda: self._on_analysis_finished(self._analysis_reply)
        )
        self.analysisStarted.emit()
        return True

    def get(self, operation: str, path: str, timeout_ms: int = 15000) -> bool:
        return self._request(operation, "GET", path, None, timeout_ms)

    def post(
        self,
        operation: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout_ms: int = 15000,
    ) -> bool:
        return self._request(operation, "POST", path, payload, timeout_ms)

    def delete(self, operation: str, path: str, timeout_ms: int = 15000) -> bool:
        return self._request(operation, "DELETE", path, None, timeout_ms)

    def _request(
        self,
        operation: str,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        timeout_ms: int,
    ) -> bool:
        if operation in self._requests:
            return False
        request = QNetworkRequest(self._url(path))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
        )
        request.setRawHeader(b"Accept", b"application/json")
        request.setTransferTimeout(timeout_ms)
        body = QByteArray(json.dumps(payload).encode("utf-8")) if payload else QByteArray()
        if method == "GET":
            reply = self._manager.get(request)
        elif method == "POST":
            reply = self._manager.post(request, body)
        else:
            reply = self._manager.deleteResource(request)
        self._requests[operation] = reply
        reply.finished.connect(
            lambda: self._on_request_finished(operation, reply)
        )
        self.requestStarted.emit(operation)
        return True

    def close(self) -> None:
        replies = [self._health_reply, self._analysis_reply, *self._requests.values()]
        for reply in replies:
            if reply is not None:
                reply.abort()
        self._health_reply = None
        self._analysis_reply = None
        self._requests.clear()

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
                        "error": self._format_http_error(
                            int(status),
                            data,
                            f"Backend returned HTTP {status}",
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
                    self._format_http_error(
                        int(status),
                        data,
                        f"Backend returned HTTP {status}",
                    )
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

    def _on_request_finished(
        self, operation: str, reply: QNetworkReply
    ) -> None:
        self._requests.pop(operation, None)
        try:
            status = reply.attribute(
                QNetworkRequest.Attribute.HttpStatusCodeAttribute
            )
            data = self._read_json_value(reply)
            if status is not None and int(status) >= 400:
                self.requestFailed.emit(
                    operation,
                    self._format_http_error(
                        int(status),
                        data if isinstance(data, dict) else {},
                        f"Backend returned HTTP {status}",
                    ),
                )
            elif reply.error() == QNetworkReply.NetworkError.NoError:
                if status is not None and 200 <= int(status) < 300:
                    self.requestFinished.emit(operation, data)
                else:
                    self.requestFailed.emit(
                        operation, f"Backend returned HTTP {status}"
                    )
            else:
                self.requestFailed.emit(
                    operation, self._connection_error(reply.errorString())
                )
        except Exception as exc:
            self.requestFailed.emit(
                operation, f"Could not parse backend response: {exc}"
            )
        finally:
            reply.deleteLater()

    def _connection_error(self, detail: str) -> str:
        return (
            f"Cannot reach the TextShield backend at {self._base_url}.\n"
            f"{detail}\n"
            "Start the backend with: python run.py"
        )

    @staticmethod
    def _read_json_value(reply: QNetworkReply) -> Any:
        raw = bytes(reply.readAll())
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _read_json(reply: QNetworkReply) -> dict[str, Any]:
        value = BackendClient._read_json_value(reply)
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

    @classmethod
    def _format_http_error(
        cls, status: int, data: dict[str, Any], fallback: str
    ) -> str:
        if status == 401:
            return (
                "Authentication required (HTTP 401). The current backend has no "
                "desktop credentials configured."
            )
        if status == 403:
            return "The backend denied this request (HTTP 403)."
        return cls._format_detail(data, fallback)
