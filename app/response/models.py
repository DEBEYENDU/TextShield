"""Response data models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    MONITOR = "MONITOR"
    WARN = "WARN"
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    NOTIFY = "NOTIFY"
    TAG = "TAG"
    ADD_LOCAL_IOC = "ADD_LOCAL_IOC"
    INCREASE_MONITORING = "INCREASE_MONITORING"
    CREATE_CASE = "CREATE_CASE"


class ActionSafety(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionReversibility(str, Enum):
    REVERSIBLE = "reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"


class ActionState(str, Enum):
    PENDING = "PENDING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AutomationLevel(str, Enum):
    DISABLED = "DISABLED"
    RECOMMEND_ONLY = "RECOMMEND_ONLY"
    AUTO_LOW_RISK = "AUTO_LOW_RISK"
    AUTO_MEDIUM_RISK = "AUTO_MEDIUM_RISK"
    AUTO_HIGH_CONFIDENCE = "AUTO_HIGH_CONFIDENCE"


class PolicyType(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"
    ENTERPRISE = "ENTERPRISE"
    RESEARCH = "RESEARCH"
    CUSTOM = "CUSTOM"


class ResponseScope(str, Enum):
    MESSAGE = "MESSAGE"
    MESSAGE_SET = "MESSAGE_SET"
    CAMPAIGN = "CAMPAIGN"
    IOC = "IOC"
    DOMAIN = "DOMAIN"
    URL = "URL"
    SENDER = "SENDER"
    PHONE = "PHONE"
    ACTOR_HYPOTHESIS = "ACTOR_HYPOTHESIS"
    USER = "USER"
    ORGANIZATION = "ORGANIZATION"


class ResponseDecision(BaseModel):
    response_id: str
    analysis_id: str
    decision_id: str
    action: ActionType
    confidence: float
    risk: str
    policy: PolicyType
    reason: str
    supporting_evidence: List[Dict] = []
    contradicting_evidence: List[Dict] = []
    requires_approval: bool = False
    reversible: ActionReversibility = ActionReversibility.REVERSIBLE
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None


class ActionPlan(BaseModel):
    plan_id: str
    response_id: str
    steps: List[Dict] = []
    created_at: datetime = datetime.utcnow()


class ActionStep(BaseModel):
    action_id: str
    sequence: int
    action_type: ActionType
    target: str
    scope: ResponseScope
    status: ActionState = ActionState.PENDING
    approval_required: bool = False
    rollback_supported: bool = True
    created_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None


class Approval(BaseModel):
    approval_id: str
    action_id: str
    approver: str
    decision: str
    reason: str = ""
    timestamp: datetime = datetime.utcnow()
    policy_version: str = ""


class ResponseAction(BaseModel):
    action_id: str
    response_id: str
    analysis_id: str
    action_type: ActionType
    safety: ActionSafety
    reversibility: ActionReversibility
    state: ActionState
    scope: ResponseScope
    target: str
    confidence: float
    policy: PolicyType
    requires_approval: bool = False
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
