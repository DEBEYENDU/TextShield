"""Research report generation."""

from __future__ import annotations
import uuid
from .models import ResearchReport
from .enums import KnowledgeState

class ResearchReportGenerator:
    def generate(self, research_id: str, findings: list, confidence: float, recommendations: list) -> ResearchReport:
        summary = f"Research {research_id} completed with {len(findings)} findings"
        report = ResearchReport(
            report_id=f"rep-{uuid.uuid4().hex[:8]}",
            research_id=research_id,
            summary=summary,
            evidence_summary=[],
            findings=findings,
            confidence=confidence,
            recommendations=recommendations
        )
        return report
