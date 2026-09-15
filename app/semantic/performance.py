"""Performance optimization utilities."""

from __future__ import annotations
import time
from functools import wraps


def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


def batch_process(pipeline, texts: list[str], batch_size: int = 32):
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        for t in batch:
            results.append(pipeline.analyze(message=t, message_type="text", include_embeddings=False))
    return results
