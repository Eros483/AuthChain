# -----  AI Agent State Definition @ services/ai_service/agent/state.py -----

from typing import Annotated, TypedDict, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    '''
    AgentState definition
    '''
    messages: Annotated[List[BaseMessage], add_messages]
    reasoning_summary: Optional[str]
    pending_critical_tool: Optional[dict]