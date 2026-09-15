"""Retry engine."""

from __future__ import annotations
import time


def retry_with_backoff(fn, retries=3, delay=5):
    for i in range(retries):
        try:
            return fn()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(delay * (2 ** i))
