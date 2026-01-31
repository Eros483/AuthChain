import json
from datetime import datetime
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from services.ai_service.agent.state import AgentState
from services.ai_service.ai_tools.manager import get_tools, is_critical

from backend.core.config import settings
from backend.core.llm_factory import get_llm

llm = get_llm() 
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = SystemMessage(
    content="""
    You are an autonomous AI Engineer. 
    You have access to the following tools:
    - list_directory
    - read_file
    - write_file
    - delete_file

    To use a tool, you MUST generate a tool call. 
    DO NOT describe what you want to do. JUST DO IT.
    Start by running `list_directory` on the current folder.
    """
    )

def call_model(state: AgentState):
    # Prepend the System Message to the history
    messages = [SYSTEM_PROMPT] + [m for m in state["messages"] if m.content or hasattr(m, "tool_calls")]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def call_model(state: AgentState):
    messages = [m for m in state["messages"] if m.content or hasattr(m, "tool_calls")]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def route_tools(state: AgentState) -> Literal["safe_tools", "critical_gate", "end"]:
    last_msg = state["messages"][-1]

    if isinstance(last_msg, HumanMessage):
        return "end"

    if isinstance(last_msg, AIMessage):
        if not last_msg.tool_calls:
            return "end"
        
        if any(is_critical(tc["name"]) for tc in last_msg.tool_calls):
            return "critical_gate"
            
    return "safe_tools"

def critical_gate(state: AgentState):
    """
    Summarizes reasoning and prepares IPC payload.
    """
    last_msg = state["messages"][-1]
    tool_call = last_msg.tool_calls[0]

    summary_prompt = f"Summarize why the agent wants to call {tool_call['name']} with {tool_call['args']} based on this history: {state['messages'][-3:]} in 2 sentences."
    summary = llm.invoke(summary_prompt).content
    
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
workflow.add_conditional_edges("agent", route_tools, {"safe_tools": "safe_tools", "critical_gate": "critical_gate", "end": END})
workflow.add_edge("safe_tools", "agent")
workflow.add_edge("critical_gate", "execute_critical")
workflow.add_edge("execute_critical", "agent")

from langgraph.checkpoint.memory import MemorySaver
graph = workflow.compile(checkpointer=MemorySaver(), interrupt_before=["execute_critical"])