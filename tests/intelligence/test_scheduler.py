"""Tests for intelligence scheduler."""

from datetime import datetime, timedelta
from app.intelligence.scheduler import IntelligenceScheduler, IntelligenceJob, JobStatus


def test_register_and_list():
    sched = IntelligenceScheduler()
    job = IntelligenceJob(job_id="j1", name="test", schedule="daily")
    sched.register_job(job)
    assert len(sched.list_jobs()) == 1


def test_schedule_freshness_check():
    sched = IntelligenceScheduler()
    job = sched.schedule_freshness_check(interval_days=1)
    assert job.name == "freshness_check"
    assert "freshness" in job.handler


def test_schedule_coverage_audit():
    sched = IntelligenceScheduler()
    job = sched.schedule_coverage_audit(interval_days=7)
    assert job.name == "coverage_audit"


def test_run_due_jobs():
    sched = IntelligenceScheduler()
    now = datetime.utcnow()
    job = IntelligenceJob(job_id="j1", name="test", schedule="daily", next_run=now - timedelta(seconds=1))
    sched.register_job(job)
    run_ids = sched.run_due_jobs(now=now)
    assert "j1" in run_ids
    assert sched.jobs["j1"].status == JobStatus.COMPLETED
    assert sched.jobs["j1"].last_run is not None
