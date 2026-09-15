"""Observation store and ingestion."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from .models import Observation
from app.core.logging import get_logger

logger = get_logger(__name__)


class ObservationStore:
    def __init__(self):
        self._observations: Dict[str, Observation] = {}

    def add(self, obs: Observation) -> Observation:
        if obs.observation_id in self._observations:
            logger.debug("Observation %s already exists", obs.observation_id)
        self._observations[obs.observation_id] = obs
        logger.info("Observation stored: %s", obs.observation_id)
        return obs

    def get(self, observation_id: str) -> Observation | None:
        return self._observations.get(observation_id)

    def list_by_analysis(self, analysis_id: str) -> List[Observation]:
        return [o for o in self._observations.values() if o.analysis_id == analysis_id]

    def list_by_message(self, message_id: str) -> List[Observation]:
        return [o for o in self._observations.values() if o.message_id == message_id]

    def list_recent(self, hours: int = 24) -> List[Observation]:
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(hours=hours)
        return [o for o in self._observations.values() if o.timestamp >= cutoff]

    def count(self) -> int:
        return len(self._observations)

    def clear(self):
        self._observations.clear()
