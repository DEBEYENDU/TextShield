from __future__ import annotations

import abc
from typing import List

from .models import ExtractedIOC, IOCType


class BaseExtractor(abc.ABC):
    """Common interface for all IOC extractors."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def ioc_type(self) -> IOCType:
        ...

    @abc.abstractmethod
    def supports(self, text: str) -> bool:
        ...

    @abc.abstractmethod
    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        ...

    def normalize(self, value: str) -> str:
        return value

    def validate(self, value: str) -> bool:
        return True
