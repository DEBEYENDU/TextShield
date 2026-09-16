"""Research tasks."""

from __future__ import annotations
from .models import ResearchTask

class TaskExecutor:
    def execute(self, task: ResearchTask) -> ResearchTask:
        task.status = "COMPLETED"
        return task
