from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

T = TypeVar("T")


class Event:
    """Base event class."""

    def __init__(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
    ):
        self.event_type = event_type
        self.source = source
        self.data = data
        self.event_id = event_id or str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "source": self.source,
            "data": self.data,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        from datetime import datetime
        event = cls(
            event_type=data["event_type"],
            source=data["source"],
            data=data["data"],
            event_id=data["event_id"],
        )
        event.timestamp = datetime.fromisoformat(data["timestamp"])
        return event


class EventBus:
    """Internal event bus for loose coupling between components."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def emit(self, event: Event) -> None:
        """Event an event to all subscribers."""
        self._history.append(event)

        # Enforce history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"Error in event handler for {event.event_type}: {e}")

    def get_history(
        self,
        event_type: Optional[str] = None,
        start_from: Optional[datetime] = None,
    ) -> List[Event]:
        """Get event history, optionally filtered by type."""
        events = self._history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_from:
            events = [e for e in events if e.timestamp >= start_from]

        return events

    def get_subscribers(self, event_type: str) -> List[str]:
        """Get list of subscriber names/callables for an event type."""
        return list(self._subscribers.get(event_type, []))


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Predefined event types
class EventTypes:
    """Predefined event type constants."""

    MESSAGE_RECEIVED = "message_received"
    SEMANTIC_COMPLETED = "semantic_completed"
    INTENT_COMPLETED = "intent_completed"
    RETRIEVAL_COMPLETED = "retrieval_completed"
    DECISION_COMPLETED = "decision_completed"
    ANALYSIS_STORED = "analysis_stored"
    WEBHOOK_TRIGGERED = "webhook_triggered"
    ANALYTICS_UPDATED = "analytics_updated"
    PLUGIN_INSTALLED = "plugin_installed"
    PLUGIN_UNINSTALLED = "plugin_uninstalled"
    MODEL_UPDATED = "model_updated"
    KNOWLEDGE_UPDATED = "knowledge_updated"


# Convenience functions for common events


def message_received_event(
    message_id: str,
    text: str,
    source: str = "unknown",
) -> Event:
    """Create a message_received event."""
    return Event(
        event_type=EventTypes.MESSAGE_RECEIVED,
        source=source,
        data={
            "message_id": message_id,
            "text": text,
        },
    )


def semantic_completed_event(
    message_id: str,
    classification: str,
    confidence: float,
    source: str = "unknown",
) -> Event:
    """Create a semantic_completed event."""
    return Event(
        event_type=EventTypes.SEMANTIC_COMPLETED,
        source=source,
        data={
            "message_id": message_id,
            "classification": classification,
            "confidence": confidence,
        },
    )


def intent_completed_event(
    message_id: str,
    primary_intent: str,
    confidence: float,
    source: str = "unknown",
) -> Event:
    """Create an intent_completed event."""
    return Event(
        event_type=EventTypes.INTENT_COMPLETED,
        source=source,
        data={
            "message_id": message_id,
            "primary_intent": primary_intent,
            "confidence": confidence,
        },
    )


def retrieval_completed_event(
    message_id: str,
    retrieved_docs: int,
    source: str = "unknown",
) -> Event:
    """Create a retrieval_completed event."""
    return Event(
        event_type=EventTypes.RETRIEVAL_COMPLETED,
        source=source,
        data={
            "message_id": message_id,
            "retrieved_docs": retrieved_docs,
        },
    )


def decision_completed_event(
    message_id: str,
    classification: str,
    risk_level: str,
    confidence: float,
    source: str = "unknown",
) -> Event:
    """Create a decision_completed event."""
    return Event(
        event_type=EventTypes.DECISION_COMPLETED,
        source=source,
        data={
            "message_id": message_id,
            "classification": classification,
            "risk_level": risk_level,
            "confidence": confidence,
        },
    )


def analysis_stored_event(
    record_id: int,
    classification: str,
    risk_level: str,
    confidence: float,
    source: str = "unknown",
) -> Event:
    """Create an analysis_stored event."""
    return Event(
        event_type=EventTypes.ANALYSIS_STORED,
        source=source,
        data={
            "record_id": record_id,
            "classification": classification,
            "risk_level": risk_level,
            "confidence": confidence,
        },
    )


def webhook_triggered_event(
    webhook_id: str,
    event_name: str,
    result: Dict[str, Any],
    source: str = "unknown",
) -> Event:
    """Create a webhook_triggered event."""
    return Event(
        event_type=EventTypes.WEBHOOK_TRIGGERED,
        source=source,
        data={
            "webhook_id": webhook_id,
            "event_name": event_name,
            "result": result,
        },
    )


def analytics_updated_event(
    metric_name: str,
    value: Any,
    source: str = "unknown",
) -> Event:
    """Create an analytics_updated event."""
    return Event(
        event_type=EventTypes.ANALYTICS_UPDATED,
        source=source,
        data={
            "metric_name": metric_name,
            "value": value,
        },
    )


def plugin_installed_event(
    plugin_name: str,
    plugin_version: str,
    source: str = "unknown",
) -> Event:
    """Create a plugin_installed event."""
    return Event(
        event_type=EventTypes.PLUGIN_INSTALLED,
        source=source,
        data={
            "plugin_name": plugin_name,
            "plugin_version": plugin_version,
        },
    )


def plugin_uninstalled_event(
    plugin_name: str,
    source: str = "unknown",
) -> Event:
    """Create a plugin_uninstalled event."""
    return Event(
        event_type=EventTypes.PLUGIN_UNINSTALLED,
        source=source,
        data={
            "plugin_name": plugin_name,
        },
    )


def model_updated_event(
    model_name: str,
    version: str,
    source: str = "unknown",
) -> Event:
    """Create a model_updated event."""
    return Event(
        event_type=EventTypes.MODEL_UPDATED,
        source=source,
        data={
            "model_name": model_name,
            "version": version,
        },
    )


def knowledge_updated_event(
    knowledge_base: str,
    items_added: int,
    source: str = "unknown",
) -> Event:
    """Create a knowledge_updated event."""
    return Event(
        event_type=EventTypes.KNOWLEDGE_UPDATED,
        source=source,
        data={
            "knowledge_base": knowledge_base,
            "items_added": items_added,
        },
    )