"""Evaluation integration for intelligence."""

from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel
from enum import Enum


class EvalResultStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class EvaluationCase(BaseModel):
    case_id: str
    candidate_id: str
    expected_outcome: str
    actual_outcome: str
    status: EvalResultStatus
    score: float


def generate_evaluation_cases(candidates: List) -> List[EvaluationCase]:
    cases = []
    for c in candidates:
        # Stub generation
        cases.append(EvaluationCase(
            case_id=f"eval-{c.candidate_id}",
            candidate_id=c.candidate_id,
            expected_outcome="validated",
            actual_outcome="unknown",
            status=EvalResultStatus.SKIPPED,
            score=0.0
        ))
    return cases


def run_evaluation(cases: List[EvaluationCase]) -> Dict:
    passed = sum(1 for c in cases if c.status == EvalResultStatus.PASS)
    failed = sum(1 for c in cases if c.status == EvalResultStatus.FAIL)
    total = len(cases)
    avg_score = sum(c.score for c in cases) / total if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": total - passed - failed,
        "avg_score": round(avg_score, 3)
    }


def feedback_loop(candidates: List, evaluation_results: Dict) -> List[Dict]:
    feedback = []
    for c in candidates:
        feedback.append({
            "candidate_id": c.candidate_id,
            "action": "promote" if getattr(c, "confidence", 0) >= 0.8 else "review",
            "evaluation": evaluation_results
        })
    return feedback
