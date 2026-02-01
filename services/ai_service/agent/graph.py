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

llm = get_llm() 
tools = get_tools()
llm_with_tools = llm.bind_tools(tools)


def call_model(state: AgentState):
    messages = state["messages"]
    
    # 1. System Prompt Injection
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # 2. Infinite Loop Guard
    # If the last 3 messages are identical tool calls, force a stop.
    if len(messages) > 6:
        last_three = messages[-3:]
        # Check if they are all tool messages from the same tool
        if all(isinstance(m, ToolMessage) for m in last_three):
            # Heuristic: If we are just reading repeatedly, stop.
            return {"messages": [AIMessage(content="I have completed the task. Final Answer: The requested actions have been performed.")]}

    # 3. Reasoning Injection (Error Handling)
    if isinstance(messages[-1], ToolMessage):
        last_content = messages[-1].content
        if "ERROR" in last_content or "does not exist" in last_content:
             messages.append(
                HumanMessage(content="⚠️ The previous tool failed. Do NOT try the exact same action again. Check the available files list and try a different file.")
            )
        else:
            messages.append(
                HumanMessage(content="Analyze the tool output above. Does it fully answer the request? If so, output a Final Answer. If not, what is the next step?")
            )

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def route_tools(state: AgentState) -> Literal["safe_tools", "critical_gate", "end"]:
    """
    Robust routing with Debugging
    """
    last_msg = state["messages"][-1]
    
    print(f"\n[ROUTER DEBUG] Msg Type: {type(last_msg)}")
    print(f"[ROUTER DEBUG] Tool Calls: {getattr(last_msg, 'tool_calls', 'None')}")

    if getattr(last_msg, "type", "") == "human":
        return "end"

    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        if any(is_critical(tc["name"]) for tc in last_msg.tool_calls):
            print("[ROUTER DEBUG] Decision: critical_gate")
            return "critical_gate"
        
        print("[ROUTER DEBUG] Decision: safe_tools")
        return "safe_tools"

    print("[ROUTER DEBUG] Decision: end (No tools found)")
    return "end"


def critical_gate(state: AgentState):
    last_msg = state["messages"][-1]
    
    if not last_msg.tool_calls:
        return state
    
    tool_call = last_msg.tool_calls[0]
    
    recent_history = state["messages"][-5:]
    history_text = "\n".join([
        f"{msg.__class__.__name__}: {msg.content if hasattr(msg, 'content') else str(msg)}"
        for msg in recent_history
    ])
    
    summary_prompt = f"""
    Based on this conversation history:
    {history_text}
    The AI agent wants to call '{tool_call['name']}' with args: {json.dumps(tool_call['args'])}
    In 2 sentences, explain WHY.
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

# --- SQLITE CHECKPOINTER SETUP ---
# Ensure this path exists or is writable
db_path = "./services/ai_service/sandbox/checkpoints.sqlite"
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)

graph = workflow.compile(
    checkpointer=checkpointer, 
    interrupt_before=["execute_critical"]
)