import os
import json
from datetime import datetime

AI_MAILBOX = os.path.abspath("./services/ipc_mailbox/ai")
BC_MAILBOX = os.path.abspath("./services/ipc_mailbox/blockchain")

def send_to_blockchain(state: dict, thread_id: str):
    """
    Writes a proposal to the AI mailbox for the Blockchain to pick up.
    """
    os.makedirs(AI_MAILBOX, exist_ok=True)
    tool_call = state.get("pending_critical_tool", {})
    
    payload = {
        "tool_name": tool_call.get("name"),
        "tool_arguments": tool_call.get("args"),
        "reasoning_summary": state.get("reasoning_summary"),
        "timestamp": datetime.now().isoformat(),
        "checkpoint_id": thread_id,
    }

    file_path = os.path.join(AI_MAILBOX, f"req_{thread_id}.json")
    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2)
    return payload

def check_for_approval(thread_id: str):
    """
    Checks the blockchain mailbox for a corresponding response file.
    This would be used for the automated polling logic later.
    """
    response_path = os.path.join(BC_MAILBOX, f"res_{thread_id}.json")
    if os.path.exists(response_path):
        with open(response_path, "r") as f:
            return json.load(f)
    return None