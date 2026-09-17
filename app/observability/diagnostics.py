"""Analysis diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class AnalysisDiagnostics:
    request_id: str = ""
    analysis_id: str = ""
    total_duration_ms: float = 0.0
    ml_duration_ms: float = 0.0
    rag_duration_ms: float = 0.0
    llm_duration_ms: float = 0.0
    threat_intel_duration_ms: float = 0.0
    provider_status: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
