import json
from datetime import datetime

def create_ipc_payload(state: dict, thread_id: str):
    tool_call = state.get("pending_critical_tool", {})
    return {
        "tool_name": tool_call.get("name"),
        "tool_arguments": tool_call.get("args"),
        "reasoning_summary": state.get("reasoning_summary"),
        "timestamp": datetime.now().isoformat(),
        "checkpoint_id": thread_id,
    }