from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.evidence.engine import EvidenceEngine
from app.evidence.explanation import EvidenceExplanation

router = APIRouter(prefix="/evidence", tags=["evidence"])

engine = EvidenceEngine()


class CollectRequest(BaseModel):
    analysis_id: str
    force: bool = False


@router.post("/collect")
def collect_evidence(req: CollectRequest):
    """Collect evidence from all registered subsystems for the given analysis_id."""
    try:
        merged = engine.collect(req.analysis_id, force=req.force)
        return merged.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EvidenceGet(BaseModel):
    analysis_id: str


@router.get("/{analysis_id}")
def get_evidence(analysis_id: str):
    """Return the unified evidence item for the given analysis_id."""
    merged = engine.get_evidence(analysis_id)
    if merged is None:
        raise HTTPException(status_code=404, detail="Evidence not found for this analysis_id")
    return merged.to_dict()


@router.get("/graph/{analysis_id}")
def get_evidence_graph(analysis_id: str):
    """Return the evidence graph for the given analysis_id."""
    g = engine.get_graph(analysis_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Graph not found for this analysis_id")
    # return node info + links (serialisable)
    nodes = {nid: {"type": nd["type"], "source": nd["source"].value, "timestamp": nd["timestamp"].isoformat()}
             for nid, nd in g.all_nodes().items()}
    links = {nid: g.get_neighbors(nid) for nid in g.all_nodes()}
    return {"nodes": nodes, "links": links}


class ExplanationRequest(BaseModel):
    analysis_id: str


@router.post("/explain")
def explain_evidence(req: ExplanationRequest):
    """Return a human-readable explanation of the evidence."""
    try:
        expl = EvidenceExplanation.collection_summary(engine)
        # try per‑analysis explanation
        merged = engine.get_evidence(req.analysis_id)
        if merged:
            parts = []
            parts.append(f"Evidence collected from multiple sources.")
            parts.append(f"Overall confidence: {merged.confidence:.1%}.")
            parts.append(f"Sources: {', '.join(set(e.source.value for e in [merged] ))}.")
            return {"analysis_id": req.analysis_id, "explanation": " ".join(parts)}
        return {"analysis_id": req.analysis_id, "explanation": expl}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))