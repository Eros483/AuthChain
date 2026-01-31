# services/ai_service/agent/graph.py -- Agent workflow graph definition

from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from ai_tools.manager import get_tools, is_critical
from agent.state import AgentState

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def route_tools(state: AgentState) -> Literal["safe_tools", "critical_gate", "end"]:
    last_msg = state["messages"][-1]
    if not last_msg.tool_calls:
        return "end"
    
    for tool_call in last_msg.tool_calls:
        if is_critical(tool_call["name"]):
            return "critical_gate"
    return "safe_tools"

def critical_gate(state: AgentState):
    """
    Prepares data for the user/blockchain before the interrupt hits.
    """
    last_msg = state["messages"][-1]
    tool_call = last_msg.tool_calls[0]

    summary = f"Agent wants to use {tool_call['name']} to modify the environment."
    
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

workflow.add_conditional_edges("agent", route_tools)
workflow.add_edge("safe_tools", "agent")

workflow.add_edge("critical_gate", "execute_critical")
workflow.add_edge("execute_critical", "agent")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory, interrupt_before=["execute_critical"])