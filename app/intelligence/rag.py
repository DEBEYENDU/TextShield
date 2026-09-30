"""RAG governance integration."""

from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel


class RagDocument(BaseModel):
    doc_id: str
    content: str
    source: str
    confidence: float
    provenance: str


class RagGovernancePolicy(BaseModel):
    allow_promotion: bool = True
    min_confidence: float = 0.7
    require_provenance: bool = True
    max_age_days: int = 365


def filter_documents_for_rag(documents: List[RagDocument], policy: RagGovernancePolicy) -> List[RagDocument]:
    filtered = []
    for doc in documents:
        if doc.confidence < policy.min_confidence:
            continue
        if policy.require_provenance and not doc.provenance:
            continue
        filtered.append(doc)
    return filtered


def promote_to_rag(candidate, documents: List[RagDocument], policy: RagGovernancePolicy) -> List[RagDocument]:
    if not policy.allow_promotion:
        return []
    filtered = filter_documents_for_rag(documents, policy)
    # Stub: would write to RAG store
    return filtered


def audit_rag_integration(candidates: List, rag_store: Optional[Dict] = None) -> Dict:
    rag_store = rag_store or {}
    audit = {
        "total_candidates": len(candidates),
        "promoted": 0,
        "rejected": 0,
        "details": []
    }
    for c in candidates:
        if getattr(c, "confidence", 0) >= 0.7:
            audit["promoted"] += 1
        else:
            audit["rejected"] += 1
        audit["details"].append({
            "candidate_id": c.candidate_id,
            "confidence": getattr(c, "confidence", 0)
        })
    return audit
