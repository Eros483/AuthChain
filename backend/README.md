# AuthChain API Documentation

### 1. Execute Agent

**POST** `/api/v1/agent/execute`

Starts the AI agent with a user query. The agent runs in the background and returns immediately.
The `thread_id` returned here is the canonical ID used across all follow-up endpoints, including critical-action approval flow.

#### Request Body

```json
{
  "query": "string",          // Required: The task for the agent to perform
  "user_id": "string"         // Optional: User identifier
}
```

#### Response

```json
{
  "thread_id": "string",      // Unique session identifier
  "status": "RUNNING",        // Current status
  "message": "string"         // Status description
}
```

#### Status Values
- `RUNNING` - Agent is actively executing
- `AWAITING_APPROVAL` - Critical action requires approval
- `COMPLETED` - Task finished successfully
- `ERROR` - Execution failed

---

### 2. Get Agent Status

**GET** `/api/v1/agent/status/{thread_id}`

Check the current status of an agent execution.

#### Path Parameters

- `thread_id` (string, required) - The session identifier returned from `/agent/execute`

#### Response

```json
{
  "thread_id": "string",
  "status": "string",         // RUNNING | AWAITING_APPROVAL | COMPLETED | ERROR | UNKNOWN
  "message": "string"
}
```

---

### 3. Get Agent Response

**GET** `/api/v1/agent/response/{thread_id}`

Get the agent's final output after execution completes. This includes all messages, tool calls, and results.

#### Path Parameters

- `thread_id` (string, required) - The session identifier returned from `/agent/execute`

#### Response

```json
{
  "status": "COMPLETED",           // COMPLETED | ERROR | RUNNING
  "completed_at": "string",        // ISO 8601 timestamp
  "thread_id": "string",
  "output": {
    "messages": [                  // Array of all agent interactions
      {
        "type": "ai_message",
        "content": "string",
        "timestamp": "string"
      },
      {
        "type": "tool_call",
        "tool_name": "string",
        "arguments": {},
        "timestamp": "string"
      },
      {
        "type": "tool_result",
        "content": "string",
        "timestamp": "string"
      }
    ],
    "tool_calls": 1,               // Total number of tool calls made
    "nodes_visited": ["array"],    // Execution flow through the graph
    "summary": "string"            // Brief summary of what was accomplished
  }
}
```

#### Message Types

- `ai_message` - AI's reasoning or response to user
- `tool_call` - A tool the agent executed
- `tool_result` - The output from a tool execution


#### Error Responses

- `404 Not Found` - Thread ID not found
- `200 OK` with `"status": "RUNNING"` - Execution still in progress, check back later
---

### 4. Get Critical Action Details

**GET** `/api/v1/critical-action/{thread_id}`

Retrieve details about a pending critical action that requires approval.

#### Path Parameters

- `thread_id` (string, required) - The session identifier returned from `/agent/execute`

#### Response

```json
{
  "thread_id": "string",
  "tool_name": "string",              // Name of the critical tool (e.g., "delete_file")
  "tool_arguments": {                 // Tool-specific arguments
    "path": "string"
  },
  "reasoning_summary": "string",      // AI-generated explanation of why this action is needed
  "timestamp": "string"               // ISO 8601 timestamp
}
```
#### Error Responses

- `404 Not Found` - No pending action for the specified thread_id

---

### 5. Blockchain Approval

**POST** `/api/v1/blockchain/approve`

**Blockchain Service Endpoint** - Called by the blockchain service after validating a critical action.

#### Request Body

```json
{
  "thread_id": "string",
  "tool_name": "string",
  "tool_arguments": {},
  "reasoning_summary": "string"
}
```

#### Response

```json
{
  "status": "forwarded_to_user",
  "thread_id": "string"
}
```
---

### 6. User Approval

**POST** `/api/v1/user/approve`

**Frontend Endpoint** - Submit user's approval or rejection decision for a critical action.

#### Request Body

```json
{
  "thread_id": "string",      // Required
  "approved": boolean,        // Required: true = approve, false = reject
  "reasoning": "string"       // Optional: Required if approved=false, explains why rejected
}
```

#### Response

```json
{
  "status": "resuming",
  "thread_id": "string",
  "approved": boolean,
  "message": "Agent resuming in background"
}
```

#### Error Responses

- `404 Not Found` - Thread not found or no pending action

---

### 7. Get User Decision

**GET** `/api/v1/user/decision/{thread_id}`

**Polling Endpoint** - Used by blockchain service and AI service to check if user has made a decision.

#### Path Parameters

- `thread_id` (string, required)

#### Response

```json
{
  "thread_id": "string",
  "approved": boolean,
  "reasoning": "string"       // Only present if rejected
}
```

#### Error Responses

- `404 Not Found` - No decision has been made yet

---

### 8. Health Check

**GET** `/health`

Check if the API server is running.

#### Response

```json
{
  "status": "healthy",
  "service": "ai-agent-backend"
}
```

---

## Request Flow Diagram

```
1. Frontend → POST /api/v1/agent/execute
   ↓ Returns immediately
   {"thread_id", "status": "RUNNING"}

2a. Safe Tool Path:
   Agent → Executes tool
   ↓
   Frontend → GET /api/v1/agent/status/{thread_id}
   ↓ Returns {"status": "COMPLETED"}
   Frontend → GET /api/v1/agent/response/{thread_id}
   ↓ Returns full output

2b. Critical Tool Path:
   Agent → Detects critical tool
   ↓
   Agent → POST /api/v1/critical-action/submit
   ↓
   Frontend → GET /api/v1/agent/status/{thread_id}
   ↓ Returns {"status": "AWAITING_APPROVAL"}
   Frontend → GET /api/v1/critical-action/{thread_id}
   ↓ Returns action details
   [Optional] Blockchain → POST /api/v1/blockchain/approve
   ↓
   Frontend → POST /api/v1/user/approve
   ↓
   Agent → Resumes execution
   ↓
   Frontend → GET /api/v1/agent/response/{thread_id}
   ↓ Returns full output
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 404  | Resource not found (thread_id or pending action) |
| 500  | Internal server error (agent execution failure) |

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.
