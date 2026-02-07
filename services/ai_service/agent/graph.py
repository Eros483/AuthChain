# -----  AI Agent Workflow Graph Definition @ services/ai_service/agent/graph.py ----

import json
import sqlite3
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver 

from services.ai_service.agent.state import AgentState
from services.ai_service.agent.prompts import SYSTEM_PROMPT
from services.ai_service.ai_tools.manager import get_tools, is_critical
from backend.core.llm_factory import get_llm

from backend.utils.logger import get_logger

logger=get_logger(__name__)

llm = get_llm() 
tools = get_tools(llm)

llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    """
    Core agent reasoning node with enhanced error handling and loop prevention
    """
    messages = state["messages"]
    
    # Ensure system prompt is always present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Enhanced loop detection
    if len(messages) > 10:
        recent = messages[-6:]
        
        # Check for repeated tool call patterns
        tool_call_history = []
        for msg in recent:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_call_history.append((tc['name'], json.dumps(tc['args'], sort_keys=True)))
        
        # If same tool+args called 3+ times, stop
        if len(tool_call_history) >= 3:
            for i in range(len(tool_call_history) - 2):
                if tool_call_history[i] == tool_call_history[i+1] == tool_call_history[i+2]:
                    return {
                        "messages": [AIMessage(
                            content=f"Task halted: Detected repeated tool call pattern ({tool_call_history[i][0]}). This suggests an unsolvable constraint or logic error. Please review the task requirements."
                        )]
                    }

    # Enhanced error recovery guidance
    if isinstance(messages[-1], ToolMessage):
        last_content = messages[-1].content
        
        # Detect common error patterns and provide specific guidance
        if "ERROR" in last_content or "does not exist" in last_content:
            error_guidance = None
            
            if "does not exist" in last_content and ".db" not in last_content:
                error_guidance = "The previous file operation failed. Use list_directory to see available files, then choose a valid path."
            
            elif ".db" in last_content or ".sqlite" in last_content:
                error_guidance = "You attempted to read a binary database file. Use sql_db_list_tables and sql_db_query instead."
            
            elif "sql_db_query" in str(messages[-2]) if len(messages) > 1 else False:
                error_guidance = "SQL query failed. Use sql_db_schema to verify table structure, then try sql_db_query_checker to validate your query."
            
            if error_guidance:
                messages.append(HumanMessage(content=error_guidance))

    response = llm_with_tools.invoke(messages)
    
    # LOG duplicate tool calls for debugging (but don't block them)
    if hasattr(response, 'tool_calls') and response.tool_calls and len(response.tool_calls) > 1:
        seen = {}
        for i, tc in enumerate(response.tool_calls):
            tc_signature = (tc['name'], json.dumps(tc['args'], sort_keys=True))
            if tc_signature in seen:
                logger.info(f"\n[DEBUG] Duplicate tool call detected: {tc['name']} (call #{i+1} matches call #{seen[tc_signature]+1})")
            else:
                seen[tc_signature] = i
    
    return {"messages": [response]}

def route_tools(state: AgentState) -> Literal["safe_tools", "critical_gate", "end"]:
    """
    Intelligent routing with debugging capabilities
    """
    last_msg = state["messages"][-1]
    
    print(f"\n[ROUTER] Message Type: {type(last_msg).__name__}")
    
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        print(f"[ROUTER] Tool Calls Detected: {len(last_msg.tool_calls)}")
        for tc in last_msg.tool_calls:
            print(f"  - {tc['name']}: {list(tc['args'].keys())}")
        
        # Check for critical tools
        if any(is_critical(tc["name"]) for tc in last_msg.tool_calls):
            logger.info("[ROUTER] Routing to: critical_gate")
            return "critical_gate"
        
        print("[ROUTER] Routing to: safe_tools")
        return "safe_tools"

    # Check if agent is signaling completion
    if hasattr(last_msg, 'content') and last_msg.content:
        content_lower = last_msg.content.lower()
        if "task completed" in content_lower or "task complete" in content_lower:
            logger.info("[ROUTER] Routing to: end (task completion detected)")
            return "end"

    print("[ROUTER] Routing to: end (no tools, no completion signal)")
    return "end"


def critical_gate(state: AgentState):
    """
    Critical action gating method
    """
    last_msg = state["messages"][-1]
    
    if not hasattr(last_msg, 'tool_calls') or not last_msg.tool_calls:
        return state
    
    tool_call = last_msg.tool_calls[0]

    recent_history = state["messages"][-8:]
    history_text = "\n".join([
        f"{msg.__class__.__name__}: {msg.content[:200] if hasattr(msg, 'content') else str(msg)[:200]}"
        for msg in recent_history
    ])

    summary_prompt = f"""
    Conversation Context:
    {history_text}
    
    The AI agent is requesting permission to execute: {tool_call['name']}
    With arguments: {json.dumps(tool_call['args'], indent=2)}
    
    Provide a clear, 1-2 sentence explanation of:
    1. What this action will do
    2. Why the agent needs to do this to complete the task
    3. What the expected outcome is
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

workflow.add_edge("safe_tools", "agent") 
workflow.add_edge("critical_gate", "execute_critical")
workflow.add_edge("execute_critical", "agent")

db_path = "./services/ai_service/sandbox/checkpoints.sqlite"
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)

graph = workflow.compile(
    checkpointer=checkpointer, 
    interrupt_before=["execute_critical"]
)