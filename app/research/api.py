"""FastAPI routes for research."""

from fastapi import APIRouter
from pydantic import BaseModel
from .request_manager import ResearchRequestManager
from .repository import ResearchRepository
from .enums import ResearchType

router = APIRouter(prefix="/api/v1/research", tags=["research"])
manager = ResearchRequestManager(ResearchRepository())

class CreateRequest(BaseModel):
    request_type: str
    target: str
    scope: str
    priority: int = 5

@router.post("/request")
def create_research(req: CreateRequest):
    research_id = manager.create_request(req.request_type, req.target, req.scope, req.priority)
    return {"research_id": research_id}

@router.get("/{research_id}")
def get_research(research_id: str):
    req = manager.get_request(research_id)
    if not req:
        return {"error": "not found"}
    return req.model_dump()
