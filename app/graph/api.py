"""Graph API endpoints."""
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/graph")
@router.get("/")
def graph_overview(): return {"status":"ok"}
