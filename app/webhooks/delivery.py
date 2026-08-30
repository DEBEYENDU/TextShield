from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Callable, Awaitable

from app.events import Event, EventTypes, get_event_bus


class WebhookDelivery:
    """Manages webhook delivery with retries, signing, and timeouts."""

    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 10,
        backoff_factor: float = 2.0,
    ):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.backoff_factor = backoff_factor
        self._subscriptions: Dict[str, Dict[str, Any]] = {}
        self._delivery_history: List[Dict[str, Any]] = []

    def subscribe(
        self,
        webhook_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Subscribe to events via webhook."""
        self._subscriptions[webhook_id] = {
            "url": url,
            "events": events,
            "secret": secret,
            "headers": headers or {},
            "created_at": datetime.utcnow(),
            "last_triggered": None,
            "success_count": 0,
            "failure_count": 0,
            "retry_count": 0,
        }

    def unsubscribe(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Unsubscribe a webhook."""
        return self._subscriptions.pop(webhook_id, None)

    async def trigger(
        self,
        webhook_id: str,
        event: Event,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Trigger a webhook delivery."""
        subscription = self._subscriptions.get(webhook_id)
        if not subscription:
            return {
                "webhook_id": webhook_id,
                "status": "not_found",
                "message": "Webhook not found",
            }

        # Check if this event type is subscribed
        if event.event_type not in subscription["events"]:
            return {
                "webhook_id": webhook_id,
                "status": "event_not_subscribed",
                "message": f"Event type {event.event_type} not subscribed",
            }

        url = subscription["url"]
        secret = subscription["secret"]
        webhook_headers = dict(subscription["headers"])

        # Add event data to payload
        delivery_payload = {
            "event": event.to_dict(),
            "payload": payload or {},
        }

        # Sign the webhook if secret is provided
        if secret:
            delivery_payload["signature"] = self._sign_payload(
                json.dumps(delivery_payload), secret
            )

        attempt = 0
        while attempt <= self.max_retries:
            try:
                response = await asyncio.wait_for(
                    self._perform_delivery(url, delivery_payload, webhook_headers),
                    timeout=self.timeout_seconds,
                )

                # Record successful delivery
                subscription["last_triggered"] = datetime.utcnow()
                subscription["success_count"] += 1

                self._delivery_history.append({
                    "webhook_id": webhook_id,
                    "event_type": event.event_type,
                    "status": "success",
                    "response_status": response.status,
                    "attempt": attempt + 1,
                })

                return {
                    "webhook_id": webhook_id,
                    "status": "success",
                    "response_status": response.status,
                }

            except asyncio.TimeoutError:
                attempt += 1
                if attempt <= self.max_retries:
                    # Exponential backoff
                    wait_time = self.timeout_seconds * (self.backoff_factor ** (attempt - 1))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self._delivery_history.append({
                        "webhook_id": webhook_id,
                        "event_type": event.event_type,
                        "status": "timeout",
                        "attempt": attempt,
                    })
                    return {
                        "webhook_id": webhook_id,
                        "status": "timeout",
                        "message": "Delivery timed out after max retries",
                    }

            except Exception as e:
                attempt += 1
                if attempt <= self.max_retries:
                    # Exponential backoff
                    wait_time = self.timeout_seconds * (self.backoff_factor ** (attempt - 1))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self._delivery_history.append({
                        "webhook_id": webhook_id,
                        "event_type": event.event_type,
                        "status": "failed",
                        "error": str(e),
                        "attempt": attempt,
                    })
                    return {
                        "webhook_id": webhook_id,
                        "status": "failed",
                        "message": str(e),
                    }

        # Should not reach here, but just in case
        return {
            "webhook_id": webhook_id,
            "status": "max_retries_exceeded",
            "message": "Max retries exceeded",
        }

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Sign a payload using HMAC."""
        import hmac
        import hashlib

        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def get_subscription(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook subscription details."""
        return self._subscriptions.get(webhook_id)

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """List all webhook subscriptions."""
        return list(self._subscriptions.values())

    def get_delivery_history(
        self,
        webhook_id: Optional[str] = None,
        start_from: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get delivery history, optionally filtered by webhook."""
        history = self._delivery_history

        if webhook_id:
            history = [h for h in history if h["webhook_id"] == webhook_id]

        if start_from:
            history = [h for h in history if h.get("triggered_at", datetime.min) >= start_from]

        return history


# Global webhook delivery instance
_webhook_delivery: Optional[WebhookDelivery] = None


def get_webhook_delivery() -> WebhookDelivery:
    """Get the global webhook delivery instance."""
    global _webhook_delivery
    if _webhook_delivery is None:
        _webhook_delivery = WebhookDelivery()
    return _webhook_delivery


def trigger_webhook_event(
    event: Event,
    webhook_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Trigger webhook for an event."""
    delivery = get_webhook_delivery()

    # If webhook_id is specified, only trigger that webhook
    # Otherwise, trigger all webhooks subscribed to this event type
    if webhook_id:
        return asyncio.get_event_loop().run_until_complete(
            delivery.trigger(webhook_id, event)
        )

    # Trigger all matching webhooks
    results = []
    for webhook_id in delivery.list_subscriptions():
        if event.event_type in webhook_id["events"]:
            result = asyncio.get_event_loop().run_until_complete(
                delivery.trigger(webhook_id["webhook_id"], event)
            )
            results.append(result)

    return {"triggered": len(results), "results": results}