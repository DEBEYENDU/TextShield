"""Hunting repository abstraction."""

from __future__ import annotations
from typing import List
from .observations import ObservationStore
from .models import Finding, Pattern, Hypothesis
from app.core.logging import get_logger

logger = get_logger(__name__)


class HuntingRepository:
    def __init__(self):
        self.observations = ObservationStore()
        self._findings: List[Finding] = []
        self._patterns: List[Pattern] = []
        self._hypotheses: List[Hypothesis] = []

    def add_finding(self, finding: Finding) -> Finding:
        self._findings.append(finding)
        logger.info("Finding stored: %s", finding.finding_id)
        return finding

    def get_findings(self) -> List[Finding]:
        return list(self._findings)

    def add_pattern(self, pattern: Pattern) -> Pattern:
        self._patterns.append(pattern)
        logger.info("Pattern stored: %s", pattern.pattern_id)
        return pattern

    def add_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        self._hypotheses.append(hypothesis)
        logger.info("Hypothesis stored: %s", hypothesis.hypothesis_id)
        return hypothesis
