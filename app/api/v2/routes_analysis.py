from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import asyncio

router = APIRouter(prefix="/v2", tags=["v2-analysis"])


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_message(
    text: str,
    include_explanation: bool = True,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze a single message for spam/phishing/fraud."""
    from app.main import app_state
    
    # Use the existing analysis pipeline
    result = await app_state["pipeline"].analyze(
        text=text,
        include_explanation=include_explanation,
    )
    
    return {
        "classification": result.classification,
        "risk_level": result.risk_level,
        "confidence": result.confidence,
        "intent": result.intent,
        "timestamp": result.timestamp,
    }


@router.post("/batch", response_model=Dict[str, Any])
async def batch_analyze(
    texts: list[str],
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze multiple messages asynchronously."""
    job_id = f"batch_{len(texts)}_{__import__('uuid').uuid4().hex[:8]}"
    
    from app.main import app_state
    
    background_tasks.add_task(
        app_state["pipeline"].batch_analyze,
        texts=texts,
        job_id=job_id,
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "total_messages": len(texts),
        "message": "Batch analysis started - use polling to check status",
    }


@router.get("/history", response_model=Dict[str, Any])
async def get_history(
    skip: int = 0,
    limit: int = 50,
    classification: Optional[str] = None,
) -> Dict[str, Any]:
    """Get analysis history."""
    from app.main import app_state
    
    history = app_state["history_service"].get(
        classification=classification,
        skip=skip,
        limit=limit,
    )
    
    return {
        "items": history,
        "total": len(history),
        "skip": skip,
        "limit": limit,
    }


@router.get("/history/{record_id}", response_model=Dict[str, Any])
async def get_history_record(
    record_id: int,
) -> Dict[str, Any]:
    """Get a specific analysis record by ID."""
    from app.main import app_state
    
    record = app_state["history_service"].get(
        record_id=record_id,
    )
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {"record": record[0] if record else None}


@router.delete("/history/{record_id}")
async def delete_history_record(
    record_id: int,
) -> Dict[str, Any]:
    """Delete an analysis record."""
    from app.main import app_state
    
    success = app_state["history_service"].delete_record(record_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return {"deleted": True, "record_id": record_id}


@router.get("/system/health", response_model=Dict[str, Any])
async def system_health() -> Dict[str, Any]:
    """System health check."""
    from app.main import app_state
    
    return app_state["monitoring_service"].get_health_summary()


@router.get("/system/metrics", response_model=Dict[str, Any])
async def system_metrics() -> Dict[str, Any]:
    """System metrics."""
    from app.main import app_state
    
    return app_state["monitoring_service"].get_metrics_snapshot()


@router.get("/system/version", response_model=Dict[str, Any])
async def system_version() -> Dict[str, Any]:
    """TextShield version."""
    return {
        "version": "2.1.0",
        "name": "TextShield V2.1 - Enterprise Integration Layer",
    }