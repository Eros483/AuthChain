# -----  Main Agent Runner @ services/ai_service/main.py -----

import uuid
import requests
from datetime import datetime
from langchain_core.messages import HumanMessage

from services.ai_service.agent.graph import graph
from services.ai_service.agent.prompts import format_rejection_message

API_BASE_URL = "http://localhost:8000/api/v1"

def run_agent_interactive(user_query: str, thread_id: str = None):
    """
    Runs the agent with interactive approval flow and enhanced observability.
    """
    thread_id = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("=" * 80)
    print("AGENT SESSION STARTING")
    print(f"Session ID: {thread_id}")
    print(f"User Query: {user_query}")
    print("=" * 80)
    
    tool_calls_made = 0
    nodes_visited = []
    agent_messages = []
    
    events = graph.stream(
        {"messages": [HumanMessage(content=user_query)]},
        config,
        stream_mode="values"
    )
    
    for event in events:
        last_msg = event["messages"][-1]
        msg_type = type(last_msg).__name__
        
        current_node = "agent"
        if hasattr(last_msg, 'name') and last_msg.name:
            current_node = last_msg.name
        elif msg_type == "ToolMessage":
            current_node = "tool_execution"
        
        nodes_visited.append(str(current_node))
        
        print(f"\n[NODE: {current_node}] ({msg_type})")
        print("-" * 80)
        
        # FIX: Handle content being a list or string
        if hasattr(last_msg, 'content') and last_msg.content and msg_type == "AIMessage":
            # Content can be string or list
            if isinstance(last_msg.content, str):
                content_preview = last_msg.content[:500]
                if len(last_msg.content) > 500:
                    content_preview += "... (truncated)"
                print(f"Content: {content_preview}")
                
                agent_messages.append({
                    "type": "ai_message",
                    "content": last_msg.content,
                    "timestamp": datetime.now().isoformat()
                })
            elif isinstance(last_msg.content, list):
                print(f"Content: [List with {len(last_msg.content)} items]")
                agent_messages.append({
                    "type": "ai_message",
                    "content": str(last_msg.content),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Display tool calls
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
                
                agent_messages.append({
                    "type": "tool_call",
                    "tool_name": tc['name'],
                    "arguments": tc['args'],
                    "timestamp": datetime.now().isoformat()
                })
        
        # Display tool results
        if msg_type == "ToolMessage":
            # FIX: Handle content being a list or string
            if isinstance(last_msg.content, str):
                result_preview = last_msg.content[:300]
                if len(last_msg.content) > 300:
                    result_preview += "... (truncated)"
                print(f"Tool Result: {result_preview}")
                
                agent_messages.append({
                    "type": "tool_result",
                    "content": last_msg.content,
                    "timestamp": datetime.now().isoformat()
                })
                
                if "ERROR" in last_msg.content:
                    print("\n>>> ERROR DETECTED IN TOOL OUTPUT <<<")
            else:
                print(f"Tool Result: [Non-string content]")
    
    print("\n" + "=" * 80)
    print("AGENT EXECUTION PAUSED OR COMPLETED")
    print(f"Total Tool Calls: {tool_calls_made}")
    print(f"Nodes Visited: {' -> '.join(nodes_visited)}")
    print("=" * 80)
    
    state = graph.get_state(config)
    
    if state.next and "execute_critical" in state.next:
        print("\n" + "=" * 80)
        print("CRITICAL ACTION DETECTED - SUBMITTING TO API")
        print("=" * 80)
        
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
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n" + "=" * 80)
    print(f"RESUMING SESSION: {thread_id}")
    print("=" * 80)
    
    agent_messages = []
    
    if approved:
        print("Action APPROVED - Executing critical tool...")
        print("-" * 80)
        
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            last_msg = event["messages"][-1]
            msg_type = type(last_msg).__name__
            
            print(f"\n[{msg_type}]")
            
            # FIX: Handle content being a list or string
            if hasattr(last_msg, 'content') and last_msg.content:
                if isinstance(last_msg.content, str):
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
                else:
                    print(f"[Non-string content: {type(last_msg.content)}]")
            
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
        
        state = graph.get_state(config)
        tool_name = state.values.get("pending_critical_tool", {}).get("name", "unknown")
        
        rejection_msg = format_rejection_message(tool_name, rejection_reason)
        
        print(f"\nInjecting rejection feedback into agent context...")
        
        graph.update_state(
            config,
            {"messages": [HumanMessage(content=rejection_msg)]},
        )
        
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            last_msg = event["messages"][-1]
            msg_type = type(last_msg).__name__
            
            print(f"\n[{msg_type}]")
            
            # FIX: Handle content being a list or string
            if hasattr(last_msg, 'content') and last_msg.content:
                if isinstance(last_msg.content, str):
                    print(f"{last_msg.content}")
                    
                    if msg_type == "AIMessage":
                        agent_messages.append({
                            "type": "ai_message",
                            "content": last_msg.content,
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    print(f"[Non-string content]")
    
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
