# ----- Langchain decorated tool for building new tools @ services/tool_creation_service/request_tool_creation.py ----- 

from langchain_core.tools import tool
from backend.utils.logger import get_logger

logger = get_logger(__name__)

@tool
def request_tool_creation(capability_needed: str) -> str:
    """
    Requests creation of a new tool when existing tools are insufficient.
    
    WHEN TO USE:
    - You need a capability that doesn't exist in your current toolkit
    - Existing tools cannot accomplish the task
    - The task requires a reusable operation
    
    CRITICAL ACTION - Requires human approval for tool code review.
    
    Args:
        capability_needed: Clear description of what the new tool should do
    
    Example:
        request_tool_creation("I need to parse CSV files and extract specific columns")
    
    Returns:
        Status message about tool creation request
    """
    logger.info(f"Tool creation requested: {capability_needed}")
    
    # This will trigger the approval flow
    # The actual generation happens in the graph node
    return f"Tool creation request submitted: {capability_needed}"