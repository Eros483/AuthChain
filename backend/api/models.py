# ----- Pydantic Base models for API responses @ backend/api/models.py -----

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UserQueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class CriticalActionProposal(BaseModel):
    thread_id: str
    tool_name: str
    tool_arguments: Dict[str, Any]
    reasoning_summary: str
    timestamp: str

class BlockchainApprovalRequest(BaseModel):
    thread_id: str
    tool_name: str
    tool_arguments: Dict[str, Any]
    reasoning_summary: str

class UserApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    reasoning: Optional[str] = None

class AgentStatusResponse(BaseModel):
    thread_id: str
    status: str  # "RUNNING", "AWAITING_APPROVAL", "COMPLETED", "ERROR"
    message: Optional[str] = None