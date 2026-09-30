"""Intelligence scheduler integration."""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Callable, List, Dict
from pydantic import BaseModel
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IntelligenceJob(BaseModel):
    job_id: str
    name: str
    schedule: str
    status: JobStatus = JobStatus.PENDING
    last_run: datetime | None = None
    next_run: datetime | None = None
    handler: str = ""


class IntelligenceScheduler:
    def __init__(self):
        self.jobs: Dict[str, IntelligenceJob] = {}

    def register_job(self, job: IntelligenceJob) -> None:
        self.jobs[job.job_id] = job

    def list_jobs(self) -> List[IntelligenceJob]:
        return list(self.jobs.values())

    def schedule_freshness_check(self, interval_days: int = 1) -> IntelligenceJob:
        now = datetime.utcnow()
        job = IntelligenceJob(
            job_id=f"job-fresh-{now.timestamp()}",
            name="freshness_check",
            schedule=f"every {interval_days} days",
            next_run=now + timedelta(days=interval_days),
            handler="app.intelligence.freshness.detect_stale_candidates"
        )
        self.register_job(job)
        return job

    def schedule_coverage_audit(self, interval_days: int = 7) -> IntelligenceJob:
        now = datetime.utcnow()
        job = IntelligenceJob(
            job_id=f"job-cov-{now.timestamp()}",
            name="coverage_audit",
            schedule=f"every {interval_days} days",
            next_run=now + timedelta(days=interval_days),
            handler="app.intelligence.coverage.calculate_coverage"
        )
        self.register_job(job)
        return job

    def run_due_jobs(self, now: datetime | None = None) -> List[str]:
        now = now or datetime.utcnow()
        run_ids = []
        for job in self.jobs.values():
            if job.next_run and job.next_run <= now and job.status != JobStatus.RUNNING:
                job.status = JobStatus.RUNNING
                # Simulate run
                job.last_run = now
                job.next_run = now + timedelta(days=1)
                job.status = JobStatus.COMPLETED
                run_ids.append(job.job_id)
        return run_ids


scheduler = IntelligenceScheduler()
