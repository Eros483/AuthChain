# -----  AI Agent Workflow Graph Definition @ services/ai_service/agent/graph.py ----

import json
import sqlite3
import os
import shutil
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

logger = get_logger(__name__)

logger.info("Initializing LLM and tools...")
llm = get_llm() 
tools = get_tools(llm)

llm_with_tools = llm.bind_tools(tools)
logger.info(f"Tools bound to LLM: {len(tools)} tools available")

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

    logger.info("Calling LLM with tools...")
    response = llm_with_tools.invoke(messages)
    logger.info(f"LLM response received: {type(response).__name__}")

    if hasattr(response, 'tool_calls') and response.tool_calls and len(response.tool_calls) > 1:
        seen = {}
        unique_tool_calls = []
        
        for i, tc in enumerate(response.tool_calls):
            tc_signature = (tc['name'], json.dumps(tc['args'], sort_keys=True))
            
            if tc_signature not in seen:
                seen[tc_signature] = i
                unique_tool_calls.append(tc)
            else:
                logger.warning(f"🔁 Removed exact duplicate tool call #{i+1}: {tc['name']}")

        if len(unique_tool_calls) < len(response.tool_calls):
            response.tool_calls = unique_tool_calls
            logger.info(f"✂️ Deduplicated: {len(response.tool_calls)} → {len(unique_tool_calls)} tool calls")
    
    return {"messages": [response]}

def route_tools(state: AgentState) -> Literal["safe_tools", "critical_gate", "end"]:
    """
    Intelligent routing with debugging capabilities
    """
    last_msg = state["messages"][-1]
    
    logger.info(f"[ROUTER] Message Type: {type(last_msg).__name__}")
    
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        logger.info(f"[ROUTER] Tool Calls Detected: {len(last_msg.tool_calls)}")
        for tc in last_msg.tool_calls:
            logger.info(f"  - {tc['name']}: {list(tc['args'].keys())}")
        
        # Check for critical tools
        if any(is_critical(tc["name"]) for tc in last_msg.tool_calls):
            logger.info("[ROUTER] Routing to: critical_gate")
            return "critical_gate"
        
        logger.info("[ROUTER] Routing to: safe_tools")
        return "safe_tools"

    # Check if agent is signaling completion
    if hasattr(last_msg, 'content') and last_msg.content:
        content_lower = str(last_msg.content).lower()
        if "task completed" in content_lower or "task complete" in content_lower:
            logger.info("[ROUTER] Routing to: end (task completion detected)")
            return "end"

    logger.info("[ROUTER] Routing to: end (no tools, no completion signal)")
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

logger.info("Building workflow graph...")
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

# ============================================================================
# FIXED: Complete SQLite checkpoint database setup
# ============================================================================

# Use absolute path to ensure we can write to it
checkpoint_dir = os.path.abspath("./services/ai_service/sandbox")
db_path = os.path.join(checkpoint_dir, "checkpoints.sqlite")

logger.info(f"Checkpoint directory: {checkpoint_dir}")
logger.info(f"Checkpoint database: {db_path}")

# Ensure directory exists with proper permissions
os.makedirs(checkpoint_dir, exist_ok=True)
logger.info(f"Directory exists: {os.path.exists(checkpoint_dir)}")
logger.info(f"Directory writable: {os.access(checkpoint_dir, os.W_OK)}")

# Remove corrupted database if it exists
if os.path.exists(db_path):
    try:
        logger.info("Removing existing checkpoint database...")
        os.remove(db_path)
        
        # Also remove WAL and SHM files if they exist
        for ext in ['-wal', '-shm', '-journal']:
            wal_file = f"{db_path}{ext}"
            if os.path.exists(wal_file):
                os.remove(wal_file)
                logger.info(f"Removed {wal_file}")
        
        logger.info("Old checkpoint files removed")
    except Exception as e:
        logger.warning(f"Could not remove old checkpoint: {e}")

# Create fresh database with proper configuration
try:
    logger.info("Creating fresh SQLite connection...")
    
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False,
        timeout=30.0,
        isolation_level=None  # Autocommit
    )
    
    # Configure for reliability and concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')  # Faster, still safe
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('PRAGMA temp_store=MEMORY')
    
    # Verify database is working
    conn.execute('SELECT 1').fetchone()
    logger.info("✓ SQLite connection verified")
    
    # Create checkpointer
    checkpointer = SqliteSaver(conn)
    logger.info("✓ Checkpointer created")
    
    # Test checkpointer setup
    try:
        checkpointer.setup()
        logger.info("✓ Checkpointer setup completed")
    except Exception as e:
        logger.error(f"Checkpointer setup failed: {e}")
        raise
    
except Exception as e:
    logger.error(f"Failed to create checkpoint database: {e}")
    logger.error(f"Working directory: {os.getcwd()}")
    logger.error(f"Checkpoint path: {db_path}")
    logger.error(f"Path exists: {os.path.exists(os.path.dirname(db_path))}")
    logger.error(f"Path writable: {os.access(os.path.dirname(db_path), os.W_OK)}")
    raise

logger.info("Compiling graph with checkpointer...")
graph = workflow.compile(
    checkpointer=checkpointer, 
    interrupt_before=["execute_critical"]
)
logger.info("✓ Graph compiled successfully")