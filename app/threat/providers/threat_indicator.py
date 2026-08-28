from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.threat.ioc.models import IOCType


@dataclass
class ThreatIndicator:
    indicator: str
    indicator_type: IOCType
    provider: str
    detection_status: str
    confidence: float
    severity: str
    timestamp: datetime
    ttl: Optional[timedelta]
    source: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "indicator_type": self.indicator_type.value,
            "provider": self.provider,
            "detection_status": self.detection_status,
            "confidence": self.confidence,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl.total_seconds() if self.ttl else None,
            "source": self.source,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreatIndicator":
        return cls(
            indicator=data["indicator"],
            indicator_type=IOCType(data["indicator_type"]),
            provider=data["provider"],
            detection_status=data["detection_status"],
            confidence=data["confidence"],
            severity=data["severity"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=timedelta(seconds=data["ttl_seconds"]) if data.get("ttl_seconds") else None,
            source=data.get("source", ""),
            explanation=data.get("explanation", ""),
        )
