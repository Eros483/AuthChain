# -----  AI Agent Graph Definition @ services/ai_service/agent/graph.py -----

import json
import sqlite3 # <--- ADD THIS
from datetime import datetime
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

from services.ai_service.agent.state import AgentState
from services.ai_service.agent.prompts import SYSTEM_PROMPT
from services.ai_service.ai_tools.manager import get_tools, is_critical
from backend.core.llm_factory import get_llm

llm = get_llm() 
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    messages = state["messages"]
    
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # FORCE REASONING with ERROR HANDLING:
    if isinstance(messages[-1], ToolMessage):
        # Check if the last tool result was an error
        last_content = messages[-1].content
        if "ERROR" in last_content or "does not exist" in last_content:
             messages.append(
                HumanMessage(content="⚠️ The previous tool failed. Do NOT try the exact same action again. Check the available files list and try a different file.")
            )
        else:
            messages.append(
                HumanMessage(content="Analyze the tool output above. Does it fully answer the request? If not, what is the next step?")
            )

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def route_tools(state: AgentState) -> Literal["safe_tools", "critical_gate", "end"]:
    """
    Robust routing with Debugging
    """
    last_msg = state["messages"][-1]
    
    # DEBUG PRINT
    print(f"\n[ROUTER DEBUG] Msg Type: {type(last_msg)}")
    print(f"[ROUTER DEBUG] Tool Calls: {getattr(last_msg, 'tool_calls', 'None')}")

    # 1. If it's the User, stop (or send to agent if you want loop)
    # Use .type string check to be safe against import mismatches
    if getattr(last_msg, "type", "") == "human":
        return "end"

    # 2. Check for Tool Calls (Duck Typing)
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        # Check if critical
        if any(is_critical(tc["name"]) for tc in last_msg.tool_calls):
            print("[ROUTER DEBUG] Decision: critical_gate")
            return "critical_gate"
        
        print("[ROUTER DEBUG] Decision: safe_tools")
        return "safe_tools"

    # 3. If AI message with NO tools -> End
    print("[ROUTER DEBUG] Decision: end (No tools found)")
    return "end"


def critical_gate(state: AgentState):
    """
    Extracts reasoning for critical tool calls.
    """
    last_msg = state["messages"][-1]
    
    if not last_msg.tool_calls:
        return state
    
    tool_call = last_msg.tool_calls[0]
    
    # Extract recent context for reasoning
    recent_history = state["messages"][-5:]  # Last 5 messages for context
    history_text = "\n".join([
        f"{msg.__class__.__name__}: {msg.content if hasattr(msg, 'content') else str(msg)}"
        for msg in recent_history
    ])
    
    # Ask LLM to summarize reasoning
    summary_prompt = f"""
    Based on this conversation history:

    {history_text}

    The AI agent wants to call the tool '{tool_call['name']}' with these arguments:
    {json.dumps(tool_call['args'], indent=2)}

    In 2-3 sentences, explain WHY the agent wants to perform this action. Be specific about what problem it's solving or what goal it's achieving.
    """
    
    summary_response = llm.invoke(summary_prompt)
    summary = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)
    
    return {
        "reasoning_summary": summary,
        "pending_critical_tool": tool_call
    }


workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("safe_tools", ToolNode(tools))
workflow.add_node("critical_gate", critical_gate)
workflow.add_node("execute_critical", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent", 
    route_tools, 
    {
        "safe_tools": "safe_tools", 
        "critical_gate": "critical_gate", 
        "end": END
    }
)

# CRITICAL: This edge MUST exist for the loop to continue
workflow.add_edge("safe_tools", "agent") 
workflow.add_edge("critical_gate", "execute_critical")
workflow.add_edge("execute_critical", "agent")

graph = workflow.compile(
    checkpointer=MemorySaver(), 
    interrupt_before=["execute_critical"]
)