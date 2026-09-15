"""Actor profiling and fingerprinting."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime
from .models import ActorProfile
from app.core.logging import get_logger

logger = get_logger(__name__)


class ActorProfiler:
    def __init__(self):
        self._profiles: Dict[str, ActorProfile] = {}

    def create_profile(self, actor_id: str, name: str, types: List[str]) -> ActorProfile:
        profile = ActorProfile(
            id=actor_id,
            name=name,
            types=types,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            confidence=0.5,
            status="HYPOTHESIZED"
        )
        self._profiles[actor_id] = profile
        logger.info("Actor profile created: %s", actor_id)
        return profile

    def update_profile(self, actor_id: str, ttp_fp: Dict[str, float] | None = None,
                       infra_fp: Dict[str, float] | None = None,
                       ling_fp: Dict[str, float] | None = None) -> ActorProfile | None:
        profile = self._profiles.get(actor_id)
        if not profile:
            return None
        if ttp_fp:
            profile.ttp_fingerprints.update(ttp_fp)
        if infra_fp:
            profile.infrastructure_fingerprints.update(infra_fp)
        if ling_fp:
            profile.linguistic_fingerprints.update(ling_fp)
        profile.last_seen = datetime.utcnow()
        profile.evidence_count += 1
        return profile

    def get_profile(self, actor_id: str) -> ActorProfile | None:
        return self._profiles.get(actor_id)

    def list_profiles(self) -> List[ActorProfile]:
        return list(self._profiles.values())
