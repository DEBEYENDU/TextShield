"""Intelligence coverage metrics."""

from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class CoverageDomain(str, Enum):
    IOC = "IOC"
    ACTOR = "ACTOR"
    CAMPAIGN = "CAMPAIGN"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    THREAT_INTEL = "THREAT_INTEL"
    GENERAL = "GENERAL"


class CoverageMetric(BaseModel):
    domain: CoverageDomain
    coverage_score: float = Field(ge=0.0, le=1.0)
    total_candidates: int = 0
    covered_candidates: int = 0
    gap_count: int = 0
    details: Dict = Field(default_factory=dict)


def calculate_coverage(candidates: List, gaps: List) -> Dict[CoverageDomain, CoverageMetric]:
    domain_counts: Dict[CoverageDomain, int] = {d: 0 for d in CoverageDomain}
    domain_covered: Dict[CoverageDomain, int] = {d: 0 for d in CoverageDomain}
    domain_gaps: Dict[CoverageDomain, int] = {d: 0 for d in CoverageDomain}

    for c in candidates:
        domain = _map_candidate_to_domain(c)
        domain_counts[domain] += 1
        if c.evidence_count > 0 or c.confidence >= 0.7:
            domain_covered[domain] += 1

    for g in gaps:
        domain = _map_gap_to_domain(g)
        domain_gaps[domain] += 1

    metrics: Dict[CoverageDomain, CoverageMetric] = {}
    for domain in CoverageDomain:
        total = domain_counts[domain]
        covered = domain_covered[domain]
        gap_count = domain_gaps[domain]
        score = covered / total if total > 0 else 1.0
        score = max(0.0, min(1.0, score))
        metrics[domain] = CoverageMetric(
            domain=domain,
            coverage_score=round(score, 3),
            total_candidates=total,
            covered_candidates=covered,
            gap_count=gap_count,
            details={"uncovered": total - covered}
        )
    return metrics


def _map_candidate_to_domain(candidate) -> CoverageDomain:
    ct = candidate.candidate_type.value if hasattr(candidate.candidate_type, "value") else str(candidate.candidate_type)
    if ct == "UNKNOWN_IOC":
        return CoverageDomain.IOC
    if ct == "ATTRIBUTION_HYPOTHESIS":
        return CoverageDomain.ACTOR
    if ct == "NEW_INFRASTRUCTURE":
        return CoverageDomain.INFRASTRUCTURE
    if ct == "CAMPAIGN_CORRELATION":
        return CoverageDomain.CAMPAIGN
    if ct == "THREAT_INTEL_GAP":
        return CoverageDomain.THREAT_INTEL
    return CoverageDomain.GENERAL


def _map_gap_to_domain(gap) -> CoverageDomain:
    gt = gap.gap_type.value if hasattr(gap.gap_type, "value") else str(gap.gap_type)
    if gt == "MISSING_IOC":
        return CoverageDomain.IOC
    if gt == "MISSING_ATTRIBUTION":
        return CoverageDomain.ACTOR
    if gt == "MISSING_CAMPAIGN_LINK":
        return CoverageDomain.CAMPAIGN
    if gt == "UNKNOWN_ENTITY":
        return CoverageDomain.INFRASTRUCTURE
    return CoverageDomain.GENERAL


def overall_coverage(metrics: Dict[CoverageDomain, CoverageMetric]) -> float:
    if not metrics:
        return 1.0
    scores = [m.coverage_score for m in metrics.values()]
    return round(sum(scores) / len(scores), 3)
