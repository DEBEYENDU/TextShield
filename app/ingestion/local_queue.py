"""Local development queue."""

from __future__ import annotations
import threading
from queue import Queue
from app.ingestion.queue import QueueBackend


class LocalQueue(QueueBackend):
    def __init__(self):
        self._q = Queue()
        self._lock = threading.Lock()
        self._processed = set()

    def enqueue(self, job):
        self._q.put(job)

    def dequeue(self):
        try:
            return self._q.get_nowait()
        except:
            return None

    def acknowledge(self, job_id):
        with self._lock:
            self._processed.add(job_id)

    def reject(self, job_id):
        pass

    def size(self) -> int:
        return self._q.qsize()
