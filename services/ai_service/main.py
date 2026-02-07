# -----  Main Agent Runner @ services/ai_service/main.py -----

import uuid
import requests
from datetime import datetime
from langchain_core.messages import HumanMessage

from services.ai_service.agent.graph import graph
from services.ai_service.agent.prompts import format_rejection_message

API_BASE_URL = "http://localhost:8000/api/v1"

def run_agent_interactive(user_query: str):
    """
    Runs the agent with interactive approval flow and enhanced observability.
    
    Flow:
    1. Agent processes query
    2. If critical tool -> interrupt and ask for approval
    3. Human approves/rejects via API
    4. Resume or inject rejection and continue
    
    Returns:
        tuple: (thread_id, status, agent_output)
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
    agent_messages = []  # Store agent's text responses
    
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
        
        # Capture AI reasoning/thoughts
        if hasattr(last_msg, 'content') and last_msg.content and msg_type == "AIMessage":
            content_preview = last_msg.content[:500]
            if len(last_msg.content) > 500:
                content_preview += "... (truncated)"
            print(f"Content: {content_preview}")
            
            # Store full message for API response
            agent_messages.append({
                "type": "ai_message",
                "content": last_msg.content,
                "timestamp": datetime.now().isoformat()
            })
        
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
                
                # Store tool call info
                agent_messages.append({
                    "type": "tool_call",
                    "tool_name": tc['name'],
                    "arguments": tc['args'],
                    "timestamp": datetime.now().isoformat()
                })
        
        # Display and capture tool results
        if msg_type == "ToolMessage":
            result_preview = last_msg.content[:300]
            if len(last_msg.content) > 300:
                result_preview += "... (truncated)"
            print(f"Tool Result: {result_preview}")
            
            # Store tool result
            agent_messages.append({
                "type": "tool_result",
                "content": last_msg.content,
                "timestamp": datetime.now().isoformat()
            })
            
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
        print("CRITICAL ACTION DETECTED - SUBMITTING TO API")
        print("=" * 80)
        
        # Prepare payload
        payload = {
            "thread_id": thread_id,
            "tool_name": state.values["pending_critical_tool"]["name"],
            "tool_arguments": state.values["pending_critical_tool"]["args"],
            "reasoning_summary": state.values.get("reasoning_summary", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\nPending Critical Action:")
        print(f"  Tool: {payload['tool_name']}")
        print(f"  Arguments: {payload['tool_arguments']}")
        print(f"\nReasoning:")
        print(f"  {payload['reasoning_summary']}")
        
        # Submit to API
        try:
            response = requests.post(
                f"{API_BASE_URL}/critical-action/submit",
                json=payload
            )
            response.raise_for_status()
            print(f"\n✅ Critical action submitted to API")
            print(f"   Blockchain can retrieve at: GET /api/v1/critical-action/{thread_id}")
            print(f"   Frontend can retrieve at: GET /api/v1/critical-action/{thread_id}")
        except Exception as e:
            print(f"\n❌ Failed to submit to API: {e}")
        
        return thread_id, "AWAITING_APPROVAL", {
            "messages": agent_messages,
            "tool_calls": tool_calls_made,
            "nodes_visited": nodes_visited
        }
    
    print("\n" + "=" * 80)
    print("AGENT SESSION COMPLETE")
    print("=" * 80)
    
    return thread_id, "COMPLETED", {
        "messages": agent_messages,
        "tool_calls": tool_calls_made,
        "nodes_visited": nodes_visited,
        "summary": "Task completed successfully"
    }


def resume_after_approval(thread_id: str, approved: bool, rejection_reason: str = None):
    """
    Resumes agent execution after human decision.
    
    Args:
        thread_id: The session ID
        approved: Whether the action was approved
        rejection_reason: If rejected, why?
        
    Returns:
        dict: Final agent output
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "=" * 80)
    print(f"RESUMING SESSION: {thread_id}")
    print("=" * 80)
    
    agent_messages = []
    
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
                
                if msg_type == "AIMessage":
                    agent_messages.append({
                        "type": "ai_message",
                        "content": last_msg.content,
                        "timestamp": datetime.now().isoformat()
                    })
            
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    print(f"\nSubsequent Tool Call: {tc['name']}")
                    agent_messages.append({
                        "type": "tool_call",
                        "tool_name": tc['name'],
                        "arguments": tc['args'],
                        "timestamp": datetime.now().isoformat()
                    })
    
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
                
                if msg_type == "AIMessage":
                    agent_messages.append({
                        "type": "ai_message",
                        "content": last_msg.content,
                        "timestamp": datetime.now().isoformat()
                    })
    
    print("\n" + "=" * 80)
    print("SESSION COMPLETE")
    print("=" * 80)
    
    return {
        "messages": agent_messages,
        "summary": "Execution completed after approval decision"
    }


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
        thread_id, status, output = run_agent_interactive(query)
        
        print(f"\n=== AGENT OUTPUT ===")
        print(f"Thread ID: {thread_id}")
        print(f"Status: {status}")
        print(f"Messages: {len(output['messages'])}")
        
        if status == "AWAITING_APPROVAL":
            print(f"\nSession saved. To resume:")
            print(f"  Approve: python -m services.ai_service.main --resume {thread_id} true")
            print(f"  Reject: python -m services.ai_service.main --resume {thread_id} false 'your reason here'")