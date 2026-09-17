"""REST API for semantic intelligence."""

from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel

from app.semantic.semantic_service import semantic_service
from app.semantic.multilingual import MultilingualPipeline

router = APIRouter(prefix="/semantic", tags=["semantic"])


class SemanticRequest(BaseModel):
    text: str
    message_type: str = "text"


class MultilingualRequest(BaseModel):
    text: str


@router.post("/analyze")
def analyze(req: SemanticRequest):
    result = semantic_service.analyze_message(req.text, message_type=req.message_type)
    return result.dict()


@router.post("/multilingual")
def multilingual(req: MultilingualRequest):
    pipeline = MultilingualPipeline()
    return pipeline.process(req.text)
