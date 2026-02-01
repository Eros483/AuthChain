# -----  Agent Prompts @ services/ai_service/agent/prompts.py -----

SYSTEM_PROMPT = """You are an autonomous AI Software Engineer.

**YOUR WORKSPACE:**
- Sandbox Root: `./services/ai_service/sandbox/`
- Database: `task_tracker.db` (SQLite)

**YOUR MANDATE:**
1. **TRUST YOUR EYES:** Only read files that appear in `list_directory`. Do not hallucinate filenames like `README.md` or `requirements.txt` if you didn't see them.
2. **NO RETRIES ON 404:** If `read_file` returns "does not exist", STOP. Do not try to read that file again. Choose a different file from the list.
3. **EXPLORE FIRST:** Always run `list_directory(".")` before doing anything else.

**CRITICAL RULES:**
- Do not stop until the user's request is fully completed.
- If a tool fails, analyze WHY and try a DIFFERENT approach.
"""

def format_rejection_message(tool_name: str, reasoning: str) -> str:
    """
    Format a rejection message to inject back into agent context
    """
    return f"""
    The human has REJECTED your proposed action.

    Tool attempted: {tool_name}
    Rejection reason: {reasoning}

    You should:
    1. Acknowledge the rejection
    2. Propose an alternative approach if possible
    3. Or explain why you cannot complete the task without this action
    """

def create_approval_summary(state: dict) -> str:
    """
    Create a human-readable summary for the approval UI
    """
    tool_call = state.get("pending_critical_tool", {})
    reasoning = state.get("reasoning_summary", "No reasoning provided")
    
    return f"""
    CRITICAL ACTION REQUESTED

    Tool: {tool_call.get('name')}
    Arguments: {tool_call.get('args')}

    Why: {reasoning}

    Approve this action?
    """