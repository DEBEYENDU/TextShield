from .models import IOCType, ExtractedIOC, ValidationStatus
from .engine import IOCEngine
from .base import BaseExtractor

class IOCExtractor:
    def __init__(self):
        self.engine = IOCEngine()
    
    def extract(self, text: str) -> dict:
        iocs = self.engine.extract(text)
        result = {}
        for ioc in iocs:
            t = ioc.type.value
            result.setdefault(t, []).append(ioc.normalized_value)
        return result
    
    def get_counts(self):
        # compatibility
        return {}

__all__ = ["IOCType", "ExtractedIOC", "ValidationStatus", "IOCExtractor", "IOCEngine", "BaseExtractor"]
