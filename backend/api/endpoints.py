# ----- endpoint management for API @ backend/api/endpoints.py -----

from fastapi import APIRouter, HTTPException, BackgroundTasks
import requests
from backend.api.models import (
    UserQueryRequest,
    CriticalActionProposal,
    BlockchainApprovalRequest,
    UserApprovalRequest,
    AgentStatusResponse
)
from services.ai_service.main import run_agent_interactive, resume_after_approval
from backend.api.shared_state import (
    pending_approvals,
    approval_decisions,
    execution_status,
    agent_responses
)
from typing import Dict, Optional, List
import asyncio
from datetime import datetime
import traceback

from backend.utils.logger import get_logger

logger = get_logger(__name__)

BLOCKCHAIN_URL = "https://authchaingo.onrender.com/api"

router = APIRouter()

def run_agent_background(query: str, thread_id: str):
    """
    Background task to run agent without blocking API response.
    """
    try:
        logger.info(f"[BACKGROUND START] Thread {thread_id}")
        logger.info(f"[BACKGROUND] Query: {query}")
        execution_status[thread_id] = "RUNNING"
        
        logger.info(f"[BACKGROUND] Calling run_agent_interactive...")
        actual_thread_id, status, output = run_agent_interactive(query, thread_id)
        
        logger.info(f"[BACKGROUND] Agent returned with status: {status}")
        execution_status[thread_id] = status
        
        agent_responses[thread_id] = {
            "status": status,
            "completed_at": datetime.now().isoformat(),
            "thread_id": actual_thread_id,
            "output": output
        }
        
        logger.info(f"[BACKGROUND COMPLETE] Thread {thread_id} - Status: {status}")
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[BACKGROUND ERROR] Thread {thread_id}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback:\n{error_trace}")
        
        execution_status[thread_id] = f"ERROR: {str(e)}"
        agent_responses[thread_id] = {
            "status": "ERROR",
            "error": str(e),
            "traceback": error_trace,
            "completed_at": datetime.now().isoformat()
        }

@router.post("/agent/execute", response_model=AgentStatusResponse)
async def execute_agent(request: UserQueryRequest, background_tasks: BackgroundTasks):
    """
    Frontend sends user query to execute agent.
    """
    import uuid
    thread_id = str(uuid.uuid4())
    
    logger.info(f"[API] Received execution request for thread {thread_id}")
    logger.info(f"[API] Query: {request.query}")
    
    background_tasks.add_task(run_agent_background, request.query, thread_id)
    
    execution_status[thread_id] = "RUNNING"
    
    logger.info(f"[API] Background task added for thread {thread_id}")
    
    return AgentStatusResponse(
        thread_id=thread_id,
        status="RUNNING",
        message="Agent execution started in background"
    )

# @router.get("/agent/status/{thread_id}", response_model=AgentStatusResponse)
# async def get_agent_status(thread_id: str):
#     """
#     Check if agent is waiting for approval or has completed.
#     """
#     if thread_id in pending_approvals:
#         return AgentStatusResponse(
#             thread_id=thread_id,
#             status="AWAITING_APPROVAL",
#             message="Critical action requires approval"
#         )
#     elif thread_id in approval_decisions:
#         return AgentStatusResponse(
#             thread_id=thread_id,
#             status="COMPLETED",
#             message="Execution resumed after approval decision"
#         )
#     elif thread_id in execution_status:
#         status = execution_status[thread_id]
#         return AgentStatusResponse(
#             thread_id=thread_id,
#             status=status,
#             message=f"Current status: {status}"
#         )
#     else:
#         return AgentStatusResponse(
#             thread_id=thread_id,
#             status="UNKNOWN",
#             message="Thread ID not found"
#         )
@router.get("/agent/status/{thread_id}", response_model=AgentStatusResponse)
async def get_agent_status(thread_id: str):
    if thread_id in pending_approvals:
        return AgentStatusResponse(
            thread_id=thread_id,
            status="AWAITING_APPROVAL",
            message="Critical action requires approval"
        )

    if thread_id in agent_responses:
        return AgentStatusResponse(
            thread_id=thread_id,
            status="COMPLETED",
            message="Execution completed"
        )

    if thread_id in execution_status:
        return AgentStatusResponse(
            thread_id=thread_id,
            status=execution_status[thread_id],
            message=f"Current status: {execution_status[thread_id]}"
        )

    return AgentStatusResponse(
        thread_id=thread_id,
        status="UNKNOWN",
        message="Thread ID not found"
    )

@router.get("/agent/response/{thread_id}")
async def get_agent_response(thread_id: str):
    """
    Get the agent's final output/response after execution completes.
    """
    if thread_id not in agent_responses and thread_id not in execution_status:
        raise HTTPException(status_code=404, detail="Thread ID not found")
    
    if thread_id in agent_responses:
        return agent_responses[thread_id]
    
    return {
        "thread_id": thread_id,
        "status": execution_status.get(thread_id, "UNKNOWN"),
        "message": "Execution still in progress"
    }

@router.get("/critical-action/{thread_id}", response_model=CriticalActionProposal)
async def get_critical_action(thread_id: str):
    """
    Blockchain calls this to retrieve critical action details.
    """
    if thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="No pending action for this thread")
    
    return pending_approvals[thread_id]

# @router.post("/critical-action/submit")
# async def submit_critical_action(proposal: CriticalActionProposal):
#     """
#     AI service calls this when critical tool is triggered.
#     """
#     try:
#         resp = requests.post(
#             BLOCKCHAIN_URL + "/actions",
#             json={
#                 "proposal_id": proposal.thread_id,
#                 "checkpoint_id": proposal.thread_id,
#                 "tool_name": proposal.tool_name,
#                 "tool_arguments": proposal.tool_arguments,
#                 "reasoning_summary": proposal.reasoning_summary,
#             },
#             timeout=3,
#         )
#         if resp.status_code != 200:
#             logger.warning(f"Blockchain rejected proposal: {resp.status_code}")
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Failed to connect to blockchain: {e}")
#         # Continue anyway
    
#     # Store in shared state
#     pending_approvals[proposal.thread_id] = proposal
#     execution_status[proposal.thread_id] = "AWAITING_APPROVAL"
    
#     return {"status": "stored", "thread_id": proposal.thread_id}
@router.post("/critical-action/submit")
async def submit_critical_action(proposal: CriticalActionProposal):
    """
    AI service calls this when critical tool is triggered.
    Blockchain is authoritative. Failure blocks execution.
    """
    try:
        logger.info(f"[GOVERNANCE] Submitting proposal {proposal.thread_id} to blockchain")

        resp = requests.post(
            f"{BLOCKCHAIN_URL}/actions",
            json={
                "proposal_id": proposal.thread_id,
                "checkpoint_id": proposal.thread_id,
                "tool_name": proposal.tool_name,
                "tool_arguments": proposal.tool_arguments,
                "reasoning_summary": proposal.reasoning_summary,
            },
            timeout=5,
        )

        if resp.status_code != 200:
            logger.error(f"[GOVERNANCE] Blockchain rejected proposal {proposal.thread_id}")
            execution_status[proposal.thread_id] = "BLOCKED"
            raise HTTPException(
                status_code=503,
                detail="Blockchain rejected governance request. Execution blocked."
            )

        result = resp.json()

        if not result.get("critical"):
            logger.info(f"[GOVERNANCE] Action non-critical. Continuing execution.")
            execution_status[proposal.thread_id] = "RUNNING"
            return {"status": "non_critical"}

        pending_approvals[proposal.thread_id] = proposal
        execution_status[proposal.thread_id] = "AWAITING_APPROVAL"

        logger.info(f"[GOVERNANCE] Proposal {proposal.thread_id} awaiting approval")
        return {"status": "awaiting_approval", "thread_id": proposal.thread_id}

    except requests.exceptions.RequestException as e:
        logger.critical(f"[GOVERNANCE DOWN] Cannot reach blockchain: {e}")

        execution_status[proposal.thread_id] = "BLOCKED"
        raise HTTPException(
            status_code=503,
            detail="Blockchain unavailable. Critical execution blocked."
        )

@router.post("/blockchain/approve")
async def blockchain_approval(request: BlockchainApprovalRequest):
    """
    Blockchain posts here after processing critical action.
    """
    if request.thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Thread not found")
    
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
    """
    if request.thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    proposal = pending_approvals[request.thread_id]
    
    try:
        resp = requests.post(
            BLOCKCHAIN_URL + "/blocks",
            json={
                "proposal_id": request.thread_id,
                "checkpoint_id": request.thread_id,
                "tool_name": proposal.tool_name,
                "tool_arguments": proposal.tool_arguments,
                "reasoning_summary": proposal.reasoning_summary,
                "decision": {
                    "approved": request.approved,
                    "decision_by": "user",
                    "rejection_reason": request.reasoning,
                    "timestamp": int(datetime.now().timestamp()),
                },
                "timestamp": int(datetime.now().timestamp()),
            },
            timeout=5,
        )
        if resp.status_code not in (200, 201, 202):
            logger.warning(f"Blockchain failed to record decision: {resp.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to blockchain: {e}")
    
    approval_decisions[request.thread_id] = request
    
    def resume_background():
        try:
            logger.info(f"[RESUME] Starting for thread {request.thread_id}")
            output = resume_after_approval(
                request.thread_id,
                request.approved,
                request.reasoning
            )
            execution_status[request.thread_id] = "COMPLETED"
            
            agent_responses[request.thread_id] = {
                "status": "COMPLETED",
                "approved": request.approved,
                "completed_at": datetime.now().isoformat(),
                "output": output
            }
            
            if request.thread_id in pending_approvals:
                del pending_approvals[request.thread_id]
            
            logger.info(f"[RESUME COMPLETE] Thread {request.thread_id}")
                
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"[RESUME ERROR] Thread {request.thread_id}: {e}")
            logger.error(f"Traceback:\n{error_trace}")
            
            execution_status[request.thread_id] = f"ERROR: {str(e)}"
            agent_responses[request.thread_id] = {
                "status": "ERROR",
                "error": str(e),
                "traceback": error_trace,
                "completed_at": datetime.now().isoformat()
            }
    
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