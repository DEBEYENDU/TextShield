"""Dashboard API: evaluation metrics, history, confusion, drift, feedback."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class FeedbackIn(BaseModel):
    message: str = ""
    verdict: str = "needs_review"
    analyst: str = "dashboard"
    comment: str = ""
    expected: str = ""
    predicted: str = ""
    run_id: str = ""


def _latest_run_id() -> str | None:
    from app.evaluation.evaluator import EvaluationEngine

    runs = EvaluationEngine().list_runs()
    return runs[-1]["run_id"] if runs else None


@router.get("/metrics")
def evaluation_metrics(run_id: str | None = None) -> dict:
    """Current metrics summary (latest run by default)."""
    from app.evaluation.evaluator import EvaluationEngine
    from app.evaluation.reports import summarize_run

    rid = run_id or _latest_run_id()
    if rid is None:
        return {"detail": "no evaluation runs yet; run the benchmark CLI first"}
    return summarize_run(EvaluationEngine().load_run(rid))


@router.get("/history")
def evaluation_history() -> dict:
    """List recorded evaluation runs."""
    from app.evaluation.evaluator import EvaluationEngine

    runs = EvaluationEngine().list_runs()
    return {"runs": runs, "total": len(runs)}


@router.get("/confusion")
def evaluation_confusion(run_id: str | None = None) -> dict:
    """Confusion matrix plus FP/FN groupings."""
    from app.evaluation import confusion as confusion_mod
    from app.evaluation.evaluator import EvaluationEngine

    rid = run_id or _latest_run_id()
    if rid is None:
        return {"detail": "no evaluation runs yet"}
    records = EvaluationEngine().load_run(rid).get("records", [])
    return {"run_id": rid,
            "confusion": confusion_mod.confusion_matrix(records),
            "false_positives": confusion_mod.false_positives(records),
            "false_negatives": confusion_mod.false_negatives(records)}


@router.get("/drift")
def evaluation_drift(baseline: str | None = None,
                     current: str | None = None) -> dict:
    """Distribution drift between two runs (latest two by default)."""
    from app.evaluation import drift as drift_mod
    from app.evaluation.evaluator import EvaluationEngine

    engine = EvaluationEngine()
    runs = engine.list_runs()
    if len(runs) < 1:
        return {"detail": "need at least one run for a drift snapshot"}
    cur_id = current or runs[-1]["run_id"]
    base_id = baseline or (runs[-2]["run_id"] if len(runs) > 1 else cur_id)
    base = drift_mod.snapshot(engine.load_run(base_id).get("records", []))
    cur = drift_mod.snapshot(engine.load_run(cur_id).get("records", []))
    return {"baseline": base_id, "current": cur_id,
            **drift_mod.detect_drift(base, cur)}


@router.get("/feedback")
def evaluation_feedback() -> dict:
    """Analyst feedback stats plus the current review queue."""
    from app.evaluation.feedback import FeedbackStore

    store = FeedbackStore()
    return {"stats": store.stats(), "queue": store.review_queue()[:20]}


@router.post("/feedback")
def evaluation_feedback_record(payload: FeedbackIn) -> dict:
    """Record analyst feedback (correct/incorrect/FP/FN/needs_review)."""
    from app.evaluation.feedback import FeedbackStore

    try:
        item = FeedbackStore().record(
            payload.message, payload.verdict, payload.analyst,
            payload.comment, payload.expected, payload.predicted,
            payload.run_id)
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"recorded": True, "feedback": item}
