"""Research planner."""

from __future__ import annotations
import uuid
from .models import ResearchTask
from .enums import ResearchType

class ResearchPlanner:
    def plan(self, request_type: ResearchType, target: str) -> list[ResearchTask]:
        tasks = []
        steps = [
            ("source_identification", "Identify sources"),
            ("collection", "Collect evidence"),
            ("normalization", "Normalize evidence"),
            ("extraction", "Extract entities/IoCs"),
            ("validation", "Validate evidence"),
            ("fusion", "Fuse knowledge"),
            ("graph_update", "Update graph"),
            ("report_generation", "Generate report"),
        ]
        for task_type, desc in steps:
            tasks.append(ResearchTask(
                task_id=f"task-{uuid.uuid4().hex[:8]}",
                research_id="pending",
                task_type=task_type
            ))
        return tasks
