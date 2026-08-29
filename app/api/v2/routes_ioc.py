from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.threat.ioc.engine import IOCEngine
from app.threat.ioc.models import IOCType

router = APIRouter(prefix="/ioc", tags=["ioc"])
engine = IOCEngine()


class ExtractRequest(BaseModel):
    text: str
    source_message: Optional[str] = ""


class ValidateRequest(BaseModel):
    value: str
    type: str


@router.post("/extract")
def extract_iocs(req: ExtractRequest):
    try:
        iocs = engine.extract(req.text, req.source_message or "")
        return {
            "count": len(iocs),
            "iocs": [ioc.to_dict() for ioc in iocs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
def validate_ioc(req: ValidateRequest):
    try:
        ioc_type = IOCType(req.type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IOC type")
    result = engine.validate_ioc(req.value, ioc_type)
    return result
