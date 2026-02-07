# AuthChain API Documentation

### 1. Execute Agent

**POST** `/api/v1/agent/execute`

Starts the AI agent with a user query. The agent runs in the background and returns immediately.

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

#### Example

```bash
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a Python script that prints hello world"
  }'
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RUNNING",
  "message": "Agent execution started in background"
}
```

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

#### Example

```bash
curl http://localhost:8000/api/v1/agent/status/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "AWAITING_APPROVAL",
  "message": "Critical action requires approval"
}
```

---

### 3. Get Critical Action Details

**GET** `/api/v1/critical-action/{thread_id}`

Retrieve details about a pending critical action that requires approval.

#### Path Parameters

- `thread_id` (string, required) - The session identifier

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

#### Example

```bash
curl http://localhost:8000/api/v1/critical-action/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "tool_name": "delete_file",
  "tool_arguments": {
    "path": "task_tracker.db"
  },
  "reasoning_summary": "The agent needs to delete task_tracker.db to free up space in the sandbox and ensure a clean environment for future tasks.",
  "timestamp": "2026-02-07T12:15:30.123456"
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

#### Example

```bash
curl -X POST http://localhost:8000/api/v1/blockchain/approve \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "tool_name": "delete_file",
    "tool_arguments": {"path": "task_tracker.db"},
    "reasoning_summary": "Blockchain verified: Safe to delete test database"
  }'
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

#### Example - Approve

```bash
curl -X POST http://localhost:8000/api/v1/user/approve \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "approved": true
  }'
```

#### Example - Reject

```bash
curl -X POST http://localhost:8000/api/v1/user/approve \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "approved": false,
    "reasoning": "This database is still needed for testing"
  }'
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

#### Example

```bash
curl http://localhost:8000/api/v1/user/decision/550e8400-e29b-41d4-a716-446655440000
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

#### Example

```bash
curl http://localhost:8000/health
```

---

## Workflow

### Complete Request Flow

```
1. Frontend → POST /api/v1/agent/execute
   ↓
   Returns: {thread_id, status: "RUNNING"}

2. Agent executes in background
   ↓
   If critical tool needed → Agent calls POST /api/v1/critical-action/submit
   ↓
   Status changes to "AWAITING_APPROVAL"

3. Frontend polls GET /api/v1/agent/status/{thread_id}
   ↓
   Response: {status: "AWAITING_APPROVAL"}

4. Frontend → GET /api/v1/critical-action/{thread_id}
   ↓
   Returns: {tool_name, tool_arguments, reasoning_summary}

5. [Optional] Blockchain → POST /api/v1/blockchain/approve
   ↓
   Validates and forwards to user

6. Frontend → POST /api/v1/user/approve
   ↓
   {thread_id, approved: true/false, reasoning?}
   ↓
   Agent resumes execution

7. Frontend → GET /api/v1/agent/status/{thread_id}
   ↓
   Response: {status: "COMPLETED"}
```


---

## Error Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 404  | Resource not found (thread_id or pending action) |
| 500  | Internal server error (agent execution failure) |

---

## Critical Tools

The following tools require human approval:

- `write_file` - Create or modify files in sandbox
- `delete_file` - Delete files from sandbox
- `sql_db_query` - Execute raw SQL queries
- `deploy_to_production` - Trigger production deployment

---

## Safe Tools (No Approval Required)

These tools execute immediately:

- `read_file` - Read file contents
- `list_directory` - List directory contents
- `search_codebase` - Search for text in files
- `sql_db_list_tables` - List database tables
- `sql_db_schema` - View table schemas
- `sql_db_query_checker` - Validate SQL queries
- `git_status` - Show git status
- `git_log` - View git history
- `git_diff` - Show file differences

---


---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for Swagger UI documentation.