"""Analysis engine integration."""

from __future__ import annotations


def run_analysis(job):
    return {"analysis_id": job.analysis_id, "status": "completed"}
