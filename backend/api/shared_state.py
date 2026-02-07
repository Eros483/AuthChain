# ----- Shared state for API and Agent @ backend/api/shared_state.py -----

from typing import Dict
from backend.api.models import CriticalActionProposal, UserApprovalRequest

# Shared state dictionaries
pending_approvals: Dict[str, CriticalActionProposal] = {}
approval_decisions: Dict[str, UserApprovalRequest] = {}
execution_status: Dict[str, str] = {}
agent_responses: Dict[str, dict] = {}