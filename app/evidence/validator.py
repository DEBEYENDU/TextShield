from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone
from .models import EvidenceItem, EvidenceSource


class EvidenceValidator:
    """Validate evidence items against a common schema.

    Ensures that every piece of evidence produced by any subsystem
    contains the required fields and that values are in acceptable ranges.
    """

    @staticmethod
    def validate(evidence: EvidenceItem) -> List[str]:
        """Return a list of error messages; empty list means valid."""
        errors: List[str] = []

        # source must be a valid EvidenceSource enum value
        try:
            EvidenceSource(evidence.source)
        except ValueError:
            errors.append(f"Invalid source: {evidence.source}")

        # confidence must be 0.0 - 1.0
        if not (0.0 <= evidence.confidence <= 1.0):
            errors.append(f"Confidence out of range: {evidence.confidence}")

        # weight should be positive
        if evidence.weight <= 0:
            errors.append(f"Weight must be positive: {evidence.weight}")

        # timestamp should be a datetime (already ensured by constructor, but check)
        if not isinstance(evidence.timestamp, datetime):
            errors.append(f"Timestamp not a datetime: {type(evidence.timestamp)}")

        # raw_evidence must not be None
        if evidence.raw_evidence is None:
            errors.append("raw_evidence is None")

        # structured_evidence should be a dict if present
        if evidence.structured_evidence is not None and not isinstance(evidence.structured_evidence, dict):
            errors.append(f"structured_evidence not a dict: {type(evidence.structured_evidence)}")

        return errors

    @staticmethod
    def bulk_validate(items: List[EvidenceItem]) -> Dict[str, List[str]]:
        """Validate a batch of evidence items.

        Returns a dict mapping evidence_id -> list of errors.
        """
        result: Dict[str, List[str]] = {}
        for item in items:
            result[item.evidence_id] = EvidenceValidator.validate(item)
        return result