# ----- boilerplate for integrating langchain generated code into agent graph @ services/tool_creation_service/graph_integration.py -----

from typing import Literal
from services.ai_service.agent.state import AgentState
from services.tool_creation_service.generator import generate_tool_proposal, validate_tool_code
from backend.core.llm_factory import get_llm
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def tool_creation_gate(state: AgentState):
    """
    Handles tool creation requests - similar to critical_gate
    
    This node:
    1. Extracts the capability description from tool call
    2. Generates tool code using LLM
    3. Validates the generated code
    4. Prepares approval summary for human review
    """
    last_msg = state["messages"][-1]
    
    if not hasattr(last_msg, 'tool_calls') or not last_msg.tool_calls:
        return state
    
    tool_call = last_msg.tool_calls[0]
    
    # Extract the capability description
    capability_needed = tool_call['args'].get('capability_needed', '')
    
    logger.info(f"[TOOL CREATION GATE] Generating proposal for: {capability_needed}")
    
    # Generate tool proposal using LLM
    try:
        # Get recent context for better tool generation
        recent_history = state["messages"][-8:]
        context = "\n".join([
            f"{msg.__class__.__name__}: {getattr(msg, 'content', '')[:200]}"
            for msg in recent_history
        ])
        
        proposal = generate_tool_proposal(capability_needed, context)
        
        # Validate the generated code
        validation = validate_tool_code(proposal.implementation, proposal.risk_tier)
        
        if not validation["safe"]:
            # If validation fails, return error to agent
            error_msg = "Tool generation failed validation:\n" + "\n".join(validation["issues"])
            return {
                "reasoning_summary": error_msg,
                "pending_critical_tool": None
            }
        
        # Create approval summary
        param_list = "\n".join([
            f"  - {p['name']} ({p['type']}): {p['description']}"
            for p in proposal.parameters
        ])
        
        summary = f"""
NEW TOOL PROPOSAL: {proposal.tool_name}

Purpose: {proposal.description}

Reasoning: {proposal.reasoning}

Risk Level: {proposal.risk_tier}

Parameters:
{param_list}

Example Usage:
{proposal.example_usage}

Generated Code Preview:
{proposal.implementation[:500]}...

Validation:
✓ No security issues detected
{f"⚠ Warnings: {', '.join(validation['warnings'])}" if validation['warnings'] else "✓ No warnings"}
"""

        return {
            "reasoning_summary": summary,
            "pending_critical_tool": {
                "name": "create_tool",
                "args": {
                    "proposal": proposal.dict(),
                    "validation": validation
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Tool generation failed: {e}")
        return {
            "reasoning_summary": f"Failed to generate tool: {str(e)}",
            "pending_critical_tool": None
        }


def execute_tool_creation(state: AgentState):
    """
    After approval, registers the tool and makes it available to the agent
    
    This node:
    1. Extracts the approved proposal from state
    2. Registers the tool in the registry (saves to disk)
    3. Loads the tool into memory
    4. Returns success message to agent
    """
    from services.tool_creation_service.registry import tool_registry
    from services.tool_creation_service.generator import ToolCreationProposal
    from langchain_core.messages import AIMessage
    
    pending = state.get("pending_critical_tool", {})
    proposal_dict = pending.get("args", {}).get("proposal", {})
    
    if not proposal_dict:
        logger.warning("No proposal found in pending_critical_tool")
        return {
            "messages": [AIMessage(content="Tool creation failed: No proposal data found")]
        }
    
    proposal = ToolCreationProposal(**proposal_dict)

    tool_hash = tool_registry.register_tool(
        proposal,
        approved_by="human_approver"
    )
    
    logger.info(f"✓ Tool created and registered: {proposal.tool_name} (hash: {tool_hash})")

    new_tool = tool_registry.load_tool(proposal.tool_name)
    logger.info(f"✓ Tool loaded and ready: {new_tool.name}")

    success_msg = f"""
✅ New tool created successfully!

Tool: {proposal.tool_name}
Description: {proposal.description}
Hash: {tool_hash}

The tool is now available in your toolkit. You can use it like this:
{proposal.example_usage}

You can now proceed with using this tool to complete your task.
"""
    
    return {
        "messages": [AIMessage(content=success_msg)],
        "tool_creation_result": {
            "tool_name": proposal.tool_name,
            "tool_hash": tool_hash,
            "status": "CREATED_AND_LOADED"
        }
    }