"""Research request lifecycle management."""

from __future__ import annotations
import uuid
from .models import ResearchRequest
from .enums import ResearchState
from .repository import ResearchRepository
from .config import config


class ResearchRequestManager:
    def __init__(self, repo: ResearchRepository | None = None):
        self.repo = repo or ResearchRepository()

    def create_request(self, request_type: str, target: str, scope: str, priority: int = 5) -> str:
        from .enums import ResearchType
        research_id = f"res-{uuid.uuid4().hex[:8]}"
        req = ResearchRequest(
            research_id=research_id,
            request_type=ResearchType(request_type),
            target=target,
            scope=scope,
            priority=priority,
            max_sources=config.max_sources,
            max_depth=config.max_depth,
            max_runtime=config.max_runtime_seconds,
            confidence_threshold=config.confidence_threshold
        )
        self.repo.create_request(req)
        return research_id

    def get_request(self, research_id: str) -> ResearchRequest | None:
        return self.repo.get_request(research_id)

    def update_state(self, research_id: str, state: str) -> None:
        from .enums import ResearchState
        self.repo.update_state(research_id, ResearchState(state))
