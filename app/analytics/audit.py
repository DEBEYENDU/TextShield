from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class AuditLogger:
    """Logger for audit events."""

    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self._events: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        sensitivity_level: str = "medium",
    ):
        """Log an audit event."""
        safe_data = self._sanitize_data(event_data)
        event_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "sensitivity_level": sensitivity_level,
            "data": safe_data,
        }
        self._events.append(event_record)

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = data.copy()
        sensitive_keys = ["message_content", "raw_text", "personal_data", "ssn"]
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"
        return safe_data

    def get_events(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        events = self._events

        if event_type:
            events = [e for e in events if e["event_type"] == event_type]

        if start_date or end_date:
            start = datetime.fromisoformat(start_date) if start_date else datetime.min
            end = datetime.fromisoformat(end_date) if end_date else datetime.max
            events = [
                e
                for e in events
                if start <= datetime.fromisoformat(e["timestamp"]) <= end
            ]

        events.sort(key=lambda e: e["timestamp"], reverse=True)

        if limit:
            events = events[:limit]

        return events

    def get_event_count(self, event_type: Optional[str] = None) -> int:
        events = self._events
        if event_type:
            return sum(1 for e in events if e["event_type"] == event_type)
        return len(events)


class AuditService:
    @staticmethod
    def log_analysis_execution(
        analysis_id: str,
        classification: str,
        confidence: float,
        risk_level: str,
        processing_time: float,
        user_id: Optional[str] = None,
    ):
        AuditLogger().log_event(
            event_type="analysis_execution",
            event_data={
                "analysis_id": analysis_id,
                "classification": classification,
                "confidence": confidence,
                "risk_level": risk_level,
                "processing_time": processing_time,
                "user_id": user_id,
            },
        )

    @staticmethod
    def log_model_change(
        model_name: str,
        version: str,
        change_type: str,
        changed_by: Optional[str] = None,
    ):
        AuditLogger().log_event(
            event_type="model_change",
            event_data={
                "model_name": model_name,
                "version": version,
                "change_type": change_type,
                "changed_by": changed_by,
            },
        )

    @staticmethod
    def log_knowledge_update(
        knowledge_base: str,
        update_type: str,
        changed_by: Optional[str] = None,
    ):
        AuditLogger().log_event(
            event_type="knowledge_update",
            event_data={
                "knowledge_base": knowledge_base,
                "update_type": update_type,
                "changed_by": changed_by,
            },
        )

    @staticmethod
    def log_system_startup():
        AuditLogger().log_event(event_type="system_startup", event_data={})

    @staticmethod
    def log_system_shutdown():
        AuditLogger().log_event(event_type="system_shutdown", event_data={})
