"""Queue abstraction."""

from __future__ import annotations
from abc import ABC, abstractmethod


class QueueBackend(ABC):
    @abstractmethod
    def enqueue(self, job): ...
    @abstractmethod
    def dequeue(self): ...
    @abstractmethod
    def acknowledge(self, job_id): ...
    @abstractmethod
    def reject(self, job_id): ...
    @abstractmethod
    def size(self) -> int: ...
