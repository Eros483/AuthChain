# ----- endpoint management for API @ backend/api/endpoints.py -----

from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.api.models import (
    UserQueryRequest,
    CriticalActionProposal,
    BlockchainApprovalRequest,
    UserApprovalRequest,
    AgentStatusResponse
)
from services.ai_service.main import run_agent_interactive, resume_after_approval
from typing import Dict, Optional, List
import asyncio
from datetime import datetime

from backend.utils.logger import get_logger

logger=get_logger(__name__)

router = APIRouter()

pending_approvals: Dict[str, CriticalActionProposal] = {}
approval_decisions: Dict[str, UserApprovalRequest] = {}
execution_status: Dict[str, str] = {}  # Track execution status
agent_responses: Dict[str, dict] = {}  # Store agent outputs

def run_agent_background(query: str, thread_id: str):
    """
    Background task to run agent without blocking API response.
    Captures the agent's final output.
    """
    try:
        execution_status[thread_id] = "RUNNING"
        actual_thread_id, status, output = run_agent_interactive(query)
        execution_status[thread_id] = status
        
        # Store the final response from the agent
        # This will be accessible via the /agent/response endpoint
        agent_responses[thread_id] = {
            "status": status,
            "completed_at": datetime.now().isoformat(),
            "thread_id": actual_thread_id,
            "output": output  # Contains messages, tool_calls, nodes_visited, summary
        }
        
    except Exception as e:
        execution_status[thread_id] = f"ERROR: {str(e)}"
        agent_responses[thread_id] = {
            "status": "ERROR",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        logger.info(f"[BACKGROUND ERROR] {e}")

@router.post("/agent/execute", response_model=AgentStatusResponse)
async def execute_agent(request: UserQueryRequest, background_tasks: BackgroundTasks):
    """
    Frontend sends user query to execute agent.
    Returns thread_id immediately and runs agent in background.
    """
    import uuid
    thread_id = str(uuid.uuid4())
    
    # Start agent in background
    background_tasks.add_task(run_agent_background, request.query, thread_id)
    
    execution_status[thread_id] = "RUNNING"
    
    return AgentStatusResponse(
        thread_id=thread_id,
        status="RUNNING",
        message="Agent execution started in background"
    )

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
    elif thread_id in execution_status:
        status = execution_status[thread_id]
        return AgentStatusResponse(
            thread_id=thread_id,
            status=status,
            message=f"Current status: {status}"
        )
    else:
        return AgentStatusResponse(
            thread_id=thread_id,
            status="UNKNOWN",
            message="Thread ID not found"
        )

@router.get("/agent/response/{thread_id}")
async def get_agent_response(thread_id: str):
    """
    Get the agent's final output/response after execution completes.
    
    This endpoint returns:
    - The final status (COMPLETED, ERROR, AWAITING_APPROVAL)
    - Any output messages from the agent
    - Timestamp of completion
    
    Use this to retrieve results after polling /agent/status shows COMPLETED.
    """
    if thread_id not in agent_responses and thread_id not in execution_status:
        raise HTTPException(status_code=404, detail="Thread ID not found")
    
    if thread_id in agent_responses:
        return agent_responses[thread_id]
    
    # Still running
    return {
        "thread_id": thread_id,
        "status": execution_status.get(thread_id, "UNKNOWN"),
        "message": "Execution still in progress"
    }

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
    execution_status[proposal.thread_id] = "AWAITING_APPROVAL"
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

@router.post("/user/approve", response_model=dict)
async def user_approval(request: UserApprovalRequest, background_tasks: BackgroundTasks):
    """
    Frontend posts user's approval/rejection decision here.
    Both blockchain and AI service read from this.
    """
    if request.thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Store decision
    approval_decisions[request.thread_id] = request
    
    # Resume agent execution in background
    def resume_background():
        try:
            output = resume_after_approval(
                request.thread_id,
                request.approved,
                request.reasoning
            )
            execution_status[request.thread_id] = "COMPLETED"
            
            # Store final response
            agent_responses[request.thread_id] = {
                "status": "COMPLETED",
                "approved": request.approved,
                "completed_at": datetime.now().isoformat(),
                "output": output
            }
            
            # Cleanup
            if request.thread_id in pending_approvals:
                del pending_approvals[request.thread_id]
                
        except Exception as e:
            execution_status[request.thread_id] = f"ERROR: {str(e)}"
            agent_responses[request.thread_id] = {
                "status": "ERROR",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }
            logger.info(f"[RESUME ERROR] {e}")
    
    background_tasks.add_task(resume_background)
    
    return {
        "status": "resuming",
        "thread_id": request.thread_id,
        "approved": request.approved,
        "message": "Agent resuming in background"
    }

@router.get("/user/decision/{thread_id}")
async def get_user_decision(thread_id: str):
    """
    Blockchain and AI service poll this to check for user decision.
    """
    if thread_id not in approval_decisions:
        raise HTTPException(status_code=404, detail="No decision yet")
    
    return approval_decisions[thread_id]