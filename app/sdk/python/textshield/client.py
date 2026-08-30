from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import httpx


class TextShieldClient:
    """Official Python SDK for TextShield v2.1."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self._default_headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            self._default_headers["X-API-Key"] = api_key

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an HTTP request to the TextShield API."""
        url = f"{self.base_url}/api/v2{endpoint}"

        headers = self._default_headers.copy()

        response = self._client.request(
            method=method,
            url=url,
            json=json,
            params=params,
            headers=headers,
        )

        response.raise_for_status()
        return response.json() if response.content else {}

    def analyze(
        self,
        text: str,
        include_explanation: bool = True,
    ) -> Dict[str, Any]:
        """Analyze a single message for spam/phishing/fraud."""
        return self._request(
            "POST",
            "/analyze",
            json={
                "text": text,
                "include_explanation": include_explanation,
            },
        )

    def batch_analyze(
        self,
        texts: List[str],
    ) -> Dict[str, Any]:
        """Analyze multiple messages asynchronously."""
        return self._request(
            "POST",
            "/batch",
            json={"texts": texts},
        )

    def get_history(
        self,
        skip: int = 0,
        limit: int = 50,
        classification: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get analysis history."""
        return self._request(
            "GET",
            "/history",
            params={
                "skip": skip,
                "limit": limit,
                "classification": classification,
            },
        )

    def get_record(self, record_id: int) -> Dict[str, Any]:
        """Get a specific analysis record by ID."""
        return self._request(
            "GET",
            f"/history/{record_id}",
        )

    def delete_record(self, record_id: int) -> Dict[str, Any]:
        """Delete an analysis record."""
        return self._request(
            "DELETE",
            f"/history/{record_id}",
        )

    def health_check(self) -> Dict[str, Any]:
        """Check system health."""
        return self._request("GET", "/system/health")

    def get_version(self) -> Dict[str, Any]:
        """Get TextShield version."""
        return self._request("GET", "/system/version")

    def close(self):
        """Close the HTTP client."""
        self._client.close()


# Convenience functions for quick usage
def quick_analyze(
    text: str,
    api_key: str,
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """Quick analyze a message."""
    client = TextShieldClient(base_url=base_url, api_key=api_key)
    try:
        return client.analyze(text=text)
    finally:
        client.close()