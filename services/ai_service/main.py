# -----  Main Agent Runner @ services/ai_service/main.py -----

import uuid
from langchain_core.messages import HumanMessage

from services.ai_service.agent.graph import graph
from services.ai_service.ipc.messenger import send_to_blockchain, check_for_approval
from services.ai_service.agent.prompts import format_rejection_message


def run_agent_interactive(user_query: str):
    """
    Runs the agent with interactive approval flow and enhanced observability.
    
    Flow:
    1. Agent processes query
    2. If critical tool -> interrupt and ask for approval
    3. Human approves/rejects via blockchain IPC
    4. Resume or inject rejection and continue
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("=" * 80)
    print("AGENT SESSION STARTING")
    print(f"Session ID: {thread_id}")
    print(f"User Query: {user_query}")
    print("=" * 80)
    
    # Track execution metrics
    tool_calls_made = 0
    nodes_visited = []
    
    # Initial invocation
    events = graph.stream(
        {"messages": [HumanMessage(content=user_query)]},
        config,
        stream_mode="values"
    )
    
    # Process events until we hit an interrupt or finish
    for event in events:
        last_msg = event["messages"][-1]
        msg_type = type(last_msg).__name__
        
        # Determine which node produced this message
        current_node = "agent"  # default
        if hasattr(last_msg, 'name') and last_msg.name:
            current_node = last_msg.name
        elif msg_type == "ToolMessage":
            current_node = "tool_execution"
        
        nodes_visited.append(str(current_node))
        
        print(f"\n[NODE: {current_node}] ({msg_type})")
        print("-" * 80)
        
        # Display AI reasoning/thoughts
        if hasattr(last_msg, 'content') and last_msg.content:
            content_preview = last_msg.content[:500]
            if len(last_msg.content) > 500:
                content_preview += "... (truncated)"
            print(f"Content: {content_preview}")
        
        # Display tool calls with detailed arguments
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            for i, tc in enumerate(last_msg.tool_calls, 1):
                tool_calls_made += 1
                print(f"\nTool Call #{tool_calls_made}: {tc['name']}")
                print(f"  Arguments:")
                for arg_name, arg_value in tc['args'].items():
                    arg_preview = str(arg_value)[:200]
                    if len(str(arg_value)) > 200:
                        arg_preview += "... (truncated)"
                    print(f"    {arg_name}: {arg_preview}")
        
        # Display tool results
        if msg_type == "ToolMessage":
            result_preview = last_msg.content[:300]
            if len(last_msg.content) > 300:
                result_preview += "... (truncated)"
            print(f"Tool Result: {result_preview}")
            
            # Highlight errors
            if "ERROR" in last_msg.content:
                print("\n>>> ERROR DETECTED IN TOOL OUTPUT <<<")
    
    print("\n" + "=" * 80)
    print("AGENT EXECUTION PAUSED OR COMPLETED")
    print(f"Total Tool Calls: {tool_calls_made}")
    print(f"Nodes Visited: {' -> '.join(nodes_visited)}")
    print("=" * 80)
    
    # Check if we interrupted (critical tool detected)
    state = graph.get_state(config)
    
    if state.next and "execute_critical" in state.next:
        print("\n" + "=" * 80)
        print("CRITICAL ACTION DETECTED - APPROVAL REQUIRED")
        print("=" * 80)
        
        # Send to blockchain for approval
        payload = send_to_blockchain(state.values, thread_id)
        
        print(f"\nPending Critical Action:")
        print(f"  Tool: {payload['tool_name']}")
        print(f"  Arguments: {payload.get('tool_args', {})}")
        print(f"\nReasoning:")
        print(f"  {payload['reasoning_summary']}")
        
        print(f"\nWaiting for approval via IPC...")
        print(f"  Mailbox: ./services/ipc_mailbox/blockchain/res_{thread_id}.json")
        print(f"\nTo approve: Create response file with {{'approved': true}}")
        print(f"To reject: Create response file with {{'approved': false, 'reason': '...'}}")
        
        return thread_id, "AWAITING_APPROVAL"
    
    print("\n" + "=" * 80)
    print("AGENT SESSION COMPLETE")
    print("=" * 80)
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
    
    print("\n" + "=" * 80)
    print(f"RESUMING SESSION: {thread_id}")
    print("=" * 80)
    
    if approved:
        print("Action APPROVED - Executing critical tool...")
        print("-" * 80)
        
        # Resume from interrupt - this executes the critical tool
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            last_msg = event["messages"][-1]
            msg_type = type(last_msg).__name__
            
            print(f"\n[{msg_type}]")
            
            if hasattr(last_msg, 'content') and last_msg.content:
                content_preview = last_msg.content[:500]
                if len(last_msg.content) > 500:
                    content_preview += "... (truncated)"
                print(f"{content_preview}")
            
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    print(f"\nSubsequent Tool Call: {tc['name']}")
    
    else:
        print(f"Action REJECTED - Reason: {rejection_reason}")
        print("-" * 80)
        
        # Inject rejection message and continue
        state = graph.get_state(config)
        tool_name = state.values.get("pending_critical_tool", {}).get("name", "unknown")
        
        rejection_msg = format_rejection_message(tool_name, rejection_reason)
        
        print(f"\nInjecting rejection feedback into agent context...")
        
        # Update state with rejection
        graph.update_state(
            config,
            {"messages": [HumanMessage(content=rejection_msg)]},
        )
        
        # Resume agent to handle rejection
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            last_msg = event["messages"][-1]
            msg_type = type(last_msg).__name__
            
            print(f"\n[{msg_type}]")
            
            if hasattr(last_msg, 'content') and last_msg.content:
                print(f"{last_msg.content}")
    
    print("\n" + "=" * 80)
    print("SESSION COMPLETE")
    print("=" * 80)


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
        query = input("Enter your request: ") if len(sys.argv) == 1 else " ".join(sys.argv[1:])
        thread_id, status = run_agent_interactive(query)
        
        if status == "AWAITING_APPROVAL":
            print(f"\nSession saved. To resume:")
            print(f"  Approve: python -m services.ai_service.main --resume {thread_id} true")
            print(f"  Reject: python -m services.ai_service.main --resume {thread_id} false 'your reason here'")