from fastapi import APIRouter, HTTPException
from backend.api.models import (
    UserQueryRequest,
    CriticalActionProposal,
    BlockchainApprovalRequest,
    UserApprovalRequest,
    AgentStatusResponse
)
from services.ai_service.main import run_agent_interactive, resume_after_approval
from typing import Dict
import asyncio

router = APIRouter()

pending_approvals: Dict[str, CriticalActionProposal] = {}
approval_decisions: Dict[str, UserApprovalRequest] = {}

@router.post("/agent/execute", response_model=AgentStatusResponse)
async def execute_agent(request: UserQueryRequest):
    """
    Frontend sends user query to execute agent.
    Returns thread_id and initial status.
    """
    try:
        thread_id, status = run_agent_interactive(request.query)
        
        return AgentStatusResponse(
            thread_id=thread_id,
            status=status,
            message="Agent execution started" if status == "COMPLETED" else "Awaiting approval"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/status/{thread_id}", response_model=AgentStatusResponse)
async def get_agent_status(thread_id: str):
    """
    Check if agent is waiting for approval or has completed.
    """
    if thread_id in pending_approvals:
        return AgentStatusResponse(
            thread_id=thread_id,
            status="AWAITING_APPROVAL",
            message="Critical action requires approval"
        )
    elif thread_id in approval_decisions:
        return AgentStatusResponse(
            thread_id=thread_id,
            status="COMPLETED",
            message="Execution resumed after approval decision"
        )
    else:
        return AgentStatusResponse(
            thread_id=thread_id,
            status="UNKNOWN",
            message="Thread ID not found"
        )

@router.get("/critical-action/{thread_id}", response_model=CriticalActionProposal)
async def get_critical_action(thread_id: str):
    """
    Blockchain calls this to retrieve critical action details.
    Frontend also calls this to display to user.
    """
    if thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="No pending action for this thread")
    
    return pending_approvals[thread_id]

@router.post("/critical-action/submit")
async def submit_critical_action(proposal: CriticalActionProposal):
    """
    AI service calls this when critical tool is triggered.
    Stores the proposal for blockchain/frontend to retrieve.
    """
    pending_approvals[proposal.thread_id] = proposal
    return {"status": "stored", "thread_id": proposal.thread_id}

@router.post("/blockchain/approve")
async def blockchain_approval(request: BlockchainApprovalRequest):
    """
    Blockchain posts here after processing critical action.
    This sends it to frontend for final user decision.
    """
    if request.thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Update pending approval with blockchain verification
    pending_approvals[request.thread_id] = CriticalActionProposal(
        thread_id=request.thread_id,
        tool_name=request.tool_name,
        tool_arguments=request.tool_arguments,
        reasoning_summary=request.reasoning_summary,
        timestamp=pending_approvals[request.thread_id].timestamp
    )
    
    return {"status": "forwarded_to_user", "thread_id": request.thread_id}

@router.post("/user/approve")
async def user_approval(request: UserApprovalRequest):
    """
    Frontend posts user's approval/rejection decision here.
    Both blockchain and AI service read from this.
    """
    if request.thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Store decision
    approval_decisions[request.thread_id] = request
    
    # Resume agent execution
    try:
        resume_after_approval(
            request.thread_id,
            request.approved,
            request.reasoning
        )
        
        # Cleanup
        del pending_approvals[request.thread_id]
        
        return {
            "status": "executed",
            "thread_id": request.thread_id,
            "approved": request.approved
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/decision/{thread_id}")
async def get_user_decision(thread_id: str):
    """
    Blockchain and AI service poll this to check for user decision.
    """
    if thread_id not in approval_decisions:
        raise HTTPException(status_code=404, detail="No decision yet")
    
    return approval_decisions[thread_id]