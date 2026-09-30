"""Tests for evaluation integration."""

from app.intelligence.evaluation import generate_evaluation_cases, run_evaluation, feedback_loop, EvalResultStatus
from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate


def make_candidate(cid="can-1", confidence=0.5):
    return ResearchCandidate(
        candidate_id=cid,
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        confidence=confidence,
        status=CandidateState.NEW,
        reason="Test"
    )


def test_generate_cases():
    candidates = [make_candidate("c1"), make_candidate("c2")]
    cases = generate_evaluation_cases(candidates)
    assert len(cases) == 2
    assert cases[0].candidate_id == "c1"
    assert cases[0].status == EvalResultStatus.SKIPPED


def test_run_evaluation():
    cases = [
        # mock cases
    ]
    from app.intelligence.evaluation import EvaluationCase
    c1 = EvaluationCase(case_id="e1", candidate_id="c1", expected_outcome="ok", actual_outcome="ok", status=EvalResultStatus.PASS, score=1.0)
    c2 = EvaluationCase(case_id="e2", candidate_id="c2", expected_outcome="ok", actual_outcome="bad", status=EvalResultStatus.FAIL, score=0.0)
    res = run_evaluation([c1, c2])
    assert res["total"] == 2
    assert res["passed"] == 1
    assert res["failed"] == 1
    assert res["avg_score"] == 0.5


def test_feedback_loop():
    candidates = [make_candidate("c1", confidence=0.9), make_candidate("c2", confidence=0.5)]
    eval_res = {"total": 2}
    fb = feedback_loop(candidates, eval_res)
    assert fb[0]["action"] == "promote"
    assert fb[1]["action"] == "review"
