from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class IOCType(str, Enum):
    URL = "url"
    DOMAIN = "domain"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    IP = "ip"
    EMAIL = "email"
    PHONE = "phone"
    URL_SHORTENER = "url_shortener"
    QR_CODE_URL = "qr_code_url"
    CRYPTO_WALLET = "crypto_wallet"


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass
class ExtractedIOC:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: IOCType = IOCType.URL
    original_value: str = ""
    normalized_value: str = ""
    confidence: float = 0.5
    validation_status: ValidationStatus = ValidationStatus.UNKNOWN
    start_pos: int = -1
    end_pos: int = -1
    extractor_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    occurrence_count: int = 1
    context_snippet: str = ""
    source_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "confidence": self.confidence,
            "validation_status": self.validation_status.value,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "extractor_name": self.extractor_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "occurrence_count": self.occurrence_count,
            "context_snippet": self.context_snippet,
            "source_message": self.source_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedIOC":
        obj = cls()
        obj.id = data.get("id", str(uuid.uuid4()))
        obj.type = IOCType(data["type"])
        obj.original_value = data.get("original_value", "")
        obj.normalized_value = data.get("normalized_value", "")
        obj.confidence = data.get("confidence", 0.5)
        obj.validation_status = ValidationStatus(data.get("validation_status", "unknown"))
        obj.start_pos = data.get("start_pos", -1)
        obj.end_pos = data.get("end_pos", -1)
        obj.extractor_name = data.get("extractor_name", "")
        ts = data.get("timestamp")
        if ts:
            obj.timestamp = datetime.fromisoformat(ts)
        else:
            obj.timestamp = datetime.now(timezone.utc)
        obj.metadata = data.get("metadata", {})
        obj.occurrence_count = data.get("occurrence_count", 1)
        obj.context_snippet = data.get("context_snippet", "")
        obj.source_message = data.get("source_message", "")
        return obj
