# -----  Main Agent Runner @ services/ai_service/main.py -----

import uuid
from langchain_core.messages import HumanMessage

from services.ai_service.agent.graph import graph
from services.ai_service.ipc.messenger import send_to_blockchain, check_for_approval
from services.ai_service.agent.prompts import format_rejection_message


def run_agent_interactive(user_query: str):
    """
    Runs the agent with interactive approval flow.
    
    Flow:
    1. Agent processes query
    2. If critical tool → interrupt and ask for approval
    3. Human approves/rejects via blockchain IPC
    4. Resume or inject rejection and continue
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("=" * 60)
    print("🚀 AGENT SESSION STARTING")
    print(f"ID: {thread_id}")
    print("=" * 60)
    
    # Initial invocation
    events = graph.stream(
        {"messages": [HumanMessage(content=user_query)]},
        config,
        stream_mode="values"
    )
    
    # Process events until we hit an interrupt or finish
    for event in events:
        last_msg = event["messages"][-1]

        print(f"DEBUG RAW CONTENT: {last_msg.content[:100]}...") 
        print(f"DEBUG TOOL CALLS: {len(last_msg.tool_calls) if hasattr(last_msg, 'tool_calls') else 'None'}")
        
        node_name = getattr(last_msg, 'name', 'agent')
        
        print(f"\n[NODE: {node_name}]")
        
        if hasattr(last_msg, 'content') and last_msg.content:
            print(f"🤖 AI THOUGHT: {last_msg.content}")
        
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                print(f"🔧 TOOL CALL: {tc['name']}")
                print(f"   Args: {tc['args']}")
    
    # Check if we interrupted (critical tool detected)
    state = graph.get_state(config)
    
    if state.next and "execute_critical" in state.next:
        print("\n" + "=" * 60)
        print("⚠️  CRITICAL ACTION DETECTED - APPROVAL REQUIRED")
        print("=" * 60)
        
        # Send to blockchain for approval
        payload = send_to_blockchain(state.values, thread_id)
        print(f"\n📤 Sent to blockchain:")
        print(f"   Tool: {payload['tool_name']}")
        print(f"   Reasoning: {payload['reasoning_summary']}")
        print(f"\n⏳ Waiting for approval via IPC...")
        print(f"   Mailbox: ./services/ipc_mailbox/blockchain/res_{thread_id}.json")
        print("\n💡 To approve: Create the response file with {'approved': true}")
        print("💡 To reject: Create the response file with {'approved': false, 'reason': '...'}")
        
        return thread_id, "AWAITING_APPROVAL"
    
    print("\n" + "=" * 60)
    print("✅ AGENT SESSION COMPLETE")
    print("=" * 60)
    return thread_id, "COMPLETED"


def resume_after_approval(thread_id: str, approved: bool, rejection_reason: str = None):
    """
    Resumes agent execution after human decision.
    
    Args:
        thread_id: The session ID
        approved: Whether the action was approved
        rejection_reason: If rejected, why?
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "=" * 60)
    print(f"🔄 RESUMING SESSION: {thread_id}")
    print("=" * 60)
    
    if approved:
        print("✅ Action APPROVED - Executing critical tool...")
        
        # Resume from interrupt - this executes the critical tool
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            last_msg = event["messages"][-1]
            if hasattr(last_msg, 'content') and last_msg.content:
                print(f"🤖 {last_msg.content}")
    
    else:
        print(f"❌ Action REJECTED - Reason: {rejection_reason}")
        
        # Inject rejection message and continue
        state = graph.get_state(config)
        tool_name = state.values.get("pending_critical_tool", {}).get("name", "unknown")
        
        rejection_msg = format_rejection_message(tool_name, rejection_reason)
        
        # Update state with rejection
        graph.update_state(
            config,
            {"messages": [HumanMessage(content=rejection_msg)]},
        )
        
        # Resume agent to handle rejection
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            last_msg = event["messages"][-1]
            if hasattr(last_msg, 'content') and last_msg.content:
                print(f"🤖 {last_msg.content}")
    
    print("\n" + "=" * 60)
    print("✅ SESSION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Check if we're resuming or starting fresh
    if len(sys.argv) > 1 and sys.argv[1] == "--resume":
        # Resume mode: python -m services.ai_service.main --resume <thread_id> <approved> [reason]
        thread_id = sys.argv[2]
        approved = sys.argv[3].lower() == "true"
        rejection_reason = sys.argv[4] if len(sys.argv) > 4 else "No reason provided"
        
        resume_after_approval(thread_id, approved, rejection_reason)
    
    else:
        # Fresh start
        query = input("🧑 Enter your request: ") if len(sys.argv) == 1 else " ".join(sys.argv[1:])
        thread_id, status = run_agent_interactive(query)
        
        if status == "AWAITING_APPROVAL":
            print(f"\n💾 Session saved. To resume:")
            print(f"   Approve: python -m services.ai_service.main --resume {thread_id} true")
            print(f"   Reject: python -m services.ai_service.main --resume {thread_id} false 'your reason here'")