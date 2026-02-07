const API_BASE = "https://authchain-ejkf.onrender.com/api/v1";
// const API_BASE = "http://localhost:8000/api/v1";

export interface ExecuteResponse {
  thread_id: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  thread_id: string;
  status: "RUNNING" | "AWAITING_APPROVAL" | "COMPLETED" | "ERROR" | "UNKNOWN";
  message?: string;
}

export interface Message {
  type: "ai_message" | "tool_call" | "tool_result";
  content?: string;
  tool_name?: string;
  arguments?: Record<string, unknown>;
  timestamp: string;
}

export interface AgentResponse {
  status: string;
  completed_at?: string;
  thread_id: string;
  output?: {
    messages: Message[];
    tool_calls: number;
    nodes_visited: string[];
    summary?: string;
  };
  message?: string;
}

export interface CriticalAction {
  thread_id: string;
  tool_name: string;
  tool_arguments: Record<string, unknown>;
  reasoning_summary: string;
  timestamp: string;
}

export async function executeAgent(query: string): Promise<ExecuteResponse> {
  const response = await fetch(`${API_BASE}/agent/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return response.json();
}

export async function getAgentStatus(threadId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/agent/status/${threadId}`);
  return response.json();
}

export async function getAgentResponse(threadId: string): Promise<AgentResponse> {
  const response = await fetch(`${API_BASE}/agent/response/${threadId}`);
  return response.json();
}

export async function getCriticalAction(threadId: string): Promise<CriticalAction> {
  const response = await fetch(`${API_BASE}/critical-action/${threadId}`);
  return response.json();
}

export async function submitApproval(
  threadId: string,
  approved: boolean,
  reasoning?: string
): Promise<{ status: string; thread_id: string; approved: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/user/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, approved, reasoning }),
  });
  return response.json();
}
