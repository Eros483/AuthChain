# DevOps Guardrail Agent - Implementation Roadmap

## Project Overview
Building an Autonomous DevOps Agent with blockchain-based authorization for critical operations. The agent can autonomously fix bugs and run tests, but requires immutable blockchain approval for production deployments and destructive actions.

---

## Architecture Summary

### Core Components
- **Agent Framework**: LangGraph (Python) - State machine with checkpointing
- **Authorization Layer**: Go Blockchain Service - Immutable approval system
- **Communication**: File-based IPC with cryptographic verification
- **Security**: Multi-tier risk classification with ML-based scoring

### Key Principles
1. **Separation of Concerns**: Agent logic ↔ Authorization logic completely decoupled
2. **State Persistence**: Full checkpoint/resume capability across process boundaries
3. **Cryptographic Verification**: Hash-based action integrity verification
4. **Audit Trail**: Immutable blockchain logging of all critical actions

---

## Phase 1: Project Setup & Core Infrastructure

### 1.1 Directory Structure Setup
- [ ] Create main project structure:
```
  services/ai_service/
  ├── agent/
  ├── ai_tools/
  ├── ipc/
  ├── config/
  └── main.py
```

### 1.2 Dependencies & Environment
- [ ] Create `requirements.txt`:
  - `langgraph>=0.1.0`
  - `langchain>=0.1.0`
  - `pydantic>=2.0.0`
  - `watchdog>=3.0.0` (file system monitoring)
  - `cryptography>=41.0.0`
  - `pytest>=7.4.0`
  - `python-dotenv>=1.0.0`
- [ ] Set up virtual environment
- [ ] Create `.env.example` with required variables
- [ ] Set up logging configuration

### 1.3 Configuration Files
- [ ] Create `config/tool_config.yaml`:
```yaml
  tool_tiers:
    tier1_safe: [read_file, list_directory, search_codebase, git_log, git_diff, check_service_status]
    tier2_write: [write_file, create_git_branch, git_commit, run_unit_tests, install_dependency]
    tier3_critical: [deploy_to_production, delete_database, git_force_push, modify_secrets]
  
  risk_thresholds:
    auto_execute: 0.3
    require_review: 0.7
    require_blockchain: 0.7
  
  timeouts:
    authorization_timeout: 300  # 5 minutes
    tool_execution_timeout: 600  # 10 minutes
```

- [ ] Create `config/agent_config.yaml`:
```yaml
  agent:
    max_iterations: 20
    checkpoint_interval: 1  # Checkpoint after every step
    
  llm:
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 2000
    
  ipc:
    request_path: "./ipc_channel/auth_request.json"
    response_path: "./ipc_channel/auth_response.json"
    lock_timeout: 30
```

---

## Phase 2: IPC Layer Implementation

### 2.1 IPC Schemas (`ipc/schemas.py`)
- [ ] Define `AuthRequest` Pydantic model:
```python
  class AuthRequest(BaseModel):
      request_id: str
      timestamp: datetime
      tool_name: str
      parameters: Dict[str, Any]
      agent_state_checkpoint: str
      action_hash: str
      risk_score: float
      estimated_impact: Dict[str, Any]
      reasoning: str
```

- [ ] Define `AuthResponse` Pydantic model:
```python
  class AuthResponse(BaseModel):
      request_id: str
      decision: Literal["approved", "denied"]
      blockchain_tx_hash: str
      timestamp: datetime
      approver: str
      signature: str
      denial_reason: Optional[str] = None
      conditions: List[str] = []
```

### 2.2 Cryptography Module (`ipc/crypto.py`)
- [ ] Implement `generate_action_hash(tool_name, parameters)`:
  - Use SHA-256
  - Include timestamp to prevent replays
  - Return hex digest

- [ ] Implement `verify_response_signature(response, public_key)`:
  - Verify blockchain signature
  - Check timestamp freshness
  - Validate request_id matches

### 2.3 IPC Channel (`ipc/channel.py`)
- [ ] Implement file locking mechanism using `fcntl`
- [ ] Create `write_auth_request(request: AuthRequest)`:
  - Acquire file lock
  - Write JSON atomically
  - Release lock
  - Return success status

- [ ] Create `read_auth_response(request_id: str) -> Optional[AuthResponse]`:
  - Poll for response file
  - Acquire read lock
  - Parse and validate JSON
  - Delete response file after reading
  - Return parsed response or None

- [ ] Add error handling for:
  - File permission issues
  - Corrupted JSON
  - Lock timeout

### 2.4 File System Watcher (`ipc/watcher.py`)
- [ ] Implement `ResponseWatcher` class:
```python
  class ResponseWatcher:
      def __init__(self, response_path: str):
          self.observer = Observer()
          self.handler = ResponseFileHandler()
          
      def wait_for_response(self, request_id: str, timeout: int) -> Optional[AuthResponse]:
          # Monitor file system for response
          # Return response or timeout
```

- [ ] Add timeout mechanism
- [ ] Add logging for all file system events

---

## Phase 3: Tool Implementation

### 3.1 Tool Registry (`ai_tools/registry.py`)
- [ ] Create `ToolRegistry` class:
```python
  class ToolMetadata(BaseModel):
      name: str
      tier: Literal["safe", "write", "critical"]
      description: str
      parameters: Dict[str, Any]
      risk_base_score: float
      requires_reasoning: bool
```

- [ ] Implement tool registration decorator:
```python
  @register_tool(tier="safe", risk_score=0.1)
  def read_file(file_path: str) -> str:
      ...
```

- [ ] Create tool lookup methods
- [ ] Add parameter validation

### 3.2 Input Validators (`ai_tools/validators.py`)
- [ ] Implement `validate_file_path(path: str)`:
  - Check for path traversal attacks
  - Ensure path is within project directory
  - Validate file exists (for reads)

- [ ] Implement `validate_git_branch_name(branch: str)`:
  - Check for valid characters
  - Prevent shell injection

- [ ] Implement `validate_environment_name(env: str)`:
  - Whitelist allowed environments
  - Prevent typos (prod vs production)

- [ ] Create generic `sanitize_input(value: Any)` helper

### 3.3 Tier 1: Safe Tools (`ai_tools/safe_tools.py`)
- [ ] **`read_file(file_path: str) -> Dict`**:
  - Validate path
  - Read file contents
  - Detect language/syntax
  - Return: `{content, language, line_count, size}`

- [ ] **`list_directory(path: str, recursive: bool = False) -> List[Dict]`**:
  - Validate path
  - Use `os.walk()` or `pathlib`
  - Get file metadata
  - Return: `[{name, type, size, last_modified, permissions}]`

- [ ] **`search_codebase(query: str, file_pattern: str = "*") -> List[Dict]`**:
  - Use `subprocess` to call `ripgrep` or `grep`
  - Parse output
  - Return: `[{file, line_number, match, context}]`

- [ ] **`git_log(branch: str, limit: int = 10) -> List[Dict]`**:
  - Execute `git log --format=json`
  - Parse output
  - Return: `[{hash, author, date, message}]`

- [ ] **`git_diff(file_path: str = None) -> str`**:
  - Execute `git diff`
  - Return unified diff format

- [ ] **`check_service_status(service_name: str) -> Dict`**:
  - Query Docker API or systemd
  - Parse status
  - Return: `{status, uptime, memory_usage, cpu_usage}`

### 3.4 Tier 2: Write Tools (`ai_tools/write_tools.py`)
- [ ] **`write_file(file_path: str, content: str, reasoning: str) -> Dict`**:
  - Validate path (prevent writes outside repo)
  - Create backup of existing file
  - Write atomically (temp file + rename)
  - Calculate checksum
  - Return: `{success, checksum, backup_path}`

- [ ] **`create_git_branch(branch_name: str) -> Dict`**:
  - Validate branch name
  - Execute `git checkout -b`
  - Return: `{branch_name, base_commit}`

- [ ] **`git_commit(message: str, files: List[str]) -> Dict`**:
  - Validate files exist
  - Stage files
  - Commit with message
  - Return: `{commit_hash, files_changed, insertions, deletions}`

- [ ] **`run_unit_tests(module: str = None, verbose: bool = True) -> Dict`**:
  - Execute `pytest` with coverage
  - Parse output (pass/fail counts)
  - Return: `{passed, failed, coverage_percent, duration, failure_details}`

- [ ] **`install_dependency(package: str, version: str = None) -> Dict`**:
  - Add to requirements.txt
  - Execute `pip install`
  - Return: `{installed_version, dependencies_added}`

### 3.5 Tier 3: Critical Tools - Stubs Only (`ai_tools/critical_tools.py`)
- [ ] **`deploy_to_production(branch: str, environment: str, reasoning: str) -> Dict`**:
  - **DO NOT IMPLEMENT ACTUAL LOGIC**
  - Return stub: `{deployment_id, status: "pending_authorization"}`

- [ ] **`delete_database(db_name: str, reasoning: str) -> Dict`**:
  - **DO NOT IMPLEMENT ACTUAL LOGIC**
  - Return stub: `{deleted: False, status: "pending_authorization"}`

- [ ] **`git_force_push(branch: str, remote: str, reasoning: str) -> Dict`**:
  - **DO NOT IMPLEMENT ACTUAL LOGIC**
  - Return stub: `{force_pushed: False, status: "pending_authorization"}`

- [ ] **`modify_secrets(action: str, key: str, value: str = None, reasoning: str) -> Dict`**:
  - **DO NOT IMPLEMENT ACTUAL LOGIC**
  - Return stub: `{action: None, status: "pending_authorization"}`

---

## Phase 4: Risk Classification System

### 4.1 Risk Classifier (`agent/risk_classifier.py`)
- [ ] Create `RiskClassifier` class:
```python
  class RiskClassifier:
      def __init__(self, config: Dict):
          self.base_scores = config['tool_tiers']
          self.modifiers = config['risk_modifiers']
          
      def score_action(self, tool_name: str, parameters: Dict) -> float:
          # Calculate risk score 0.0-1.0
          pass
```

- [ ] Implement base scoring:
  - Tier 1 tools: 0.1-0.2
  - Tier 2 tools: 0.3-0.5
  - Tier 3 tools: 0.7-1.0

- [ ] Implement parameter-based modifiers:
  - Environment = "production": +0.2
  - Time of day (off-hours): +0.1
  - File path contains "secrets": +0.3
  - Operation is destructive (delete): +0.2

- [ ] Implement reasoning quality scorer:
  - Check if reasoning is provided
  - Check length (min 50 chars)
  - Check for key phrases ("tested", "rollback plan")
  - Adjust score based on quality

- [ ] Create `estimate_impact(tool_name, parameters)`:
  - Return: `{users_affected, downtime_risk, data_risk}`

---

## Phase 5: LangGraph Agent Implementation

### 5.1 State Management (`agent/checkpointer.py`)
- [ ] Create `AgentState` TypedDict:
```python
  class AgentState(TypedDict):
      messages: List[Dict]
      current_tool: Optional[str]
      tool_parameters: Optional[Dict]
      pending_authorization: bool
      auth_request_id: Optional[str]
      execution_results: List[Dict]
      error_state: Optional[str]
      iteration_count: int
      risk_score: float
```

- [ ] Implement custom checkpointer that serializes to disk
- [ ] Add checkpoint versioning
- [ ] Add checkpoint cleanup (delete old checkpoints)

### 5.2 Graph Nodes (`agent/nodes.py`)
- [ ] **`reasoning_node(state: AgentState) -> AgentState`**:
  - Call LLM with current state
  - Parse tool call from response
  - Update state with selected tool
  - Increment iteration count

- [ ] **`risk_assessment_node(state: AgentState) -> AgentState`**:
  - Use RiskClassifier to score action
  - Add risk_score to state
  - Determine if authorization needed

- [ ] **`safe_execution_node(state: AgentState) -> AgentState`**:
  - Execute tool directly (Tier 1 & 2)
  - Capture result
  - Add to execution_results
  - Handle errors gracefully

- [ ] **`blockchain_request_node(state: AgentState) -> AgentState`**:
  - Generate AuthRequest
  - Calculate action_hash
  - Write to IPC channel
  - Set pending_authorization = True
  - **PAUSE GRAPH EXECUTION HERE**

- [ ] **`authorization_handler_node(state: AgentState) -> AgentState`**:
  - Read AuthResponse from IPC
  - Verify signature
  - Update state with decision
  - If approved: proceed to execution
  - If denied: log and continue agent loop

- [ ] **`critical_execution_node(state: AgentState) -> AgentState`**:
  - Execute critical tool (Tier 3)
  - **Only called after authorization**
  - Log extensively
  - Return result

- [ ] **`error_handler_node(state: AgentState) -> AgentState`**:
  - Log error details
  - Update error_state
  - Attempt recovery if possible

### 5.3 Router Logic (`agent/router.py`)
- [ ] **`should_continue(state: AgentState) -> str`**:
  - Check iteration count (max 20)
  - Check if task complete
  - Check for errors
  - Return: "continue" | "end" | "error"

- [ ] **`route_by_risk(state: AgentState) -> str`**:
  - If risk_score < 0.7: "safe_execute"
  - If risk_score >= 0.7: "blockchain_request"

- [ ] **`route_by_authorization(state: AgentState) -> str`**:
  - If pending_authorization: "wait_for_auth"
  - Else: "critical_execute"

### 5.4 Graph Assembly (`agent/graph.py`)
- [ ] Define graph structure:
```python
  from langgraph.graph import StateGraph
  from langgraph.checkpoint.memory import MemorySaver
  
  graph = StateGraph(AgentState)
  
  # Add nodes
  graph.add_node("reasoning", reasoning_node)
  graph.add_node("risk_assessment", risk_assessment_node)
  graph.add_node("safe_execution", safe_execution_node)
  graph.add_node("blockchain_request", blockchain_request_node)
  graph.add_node("authorization_handler", authorization_handler_node)
  graph.add_node("critical_execution", critical_execution_node)
  graph.add_node("error_handler", error_handler_node)
```

- [ ] Define edges:
```python
  graph.set_entry_point("reasoning")
  graph.add_edge("reasoning", "risk_assessment")
  graph.add_conditional_edges(
      "risk_assessment",
      route_by_risk,
      {
          "safe_execute": "safe_execution",
          "blockchain_request": "blockchain_request"
      }
  )
  graph.add_edge("safe_execution", "reasoning")
  graph.add_edge("blockchain_request", "authorization_handler")
  graph.add_conditional_edges(
      "authorization_handler",
      route_by_authorization,
      {
          "critical_execute": "critical_execution",
          "denied": "reasoning"
      }
  )
  graph.add_edge("critical_execution", "reasoning")
```

- [ ] Add interrupts:
```python
  graph.add_conditional_edges(
      "blockchain_request",
      lambda state: "wait" if state["pending_authorization"] else "continue"
  )
```

- [ ] Compile graph with checkpointing:
```python
  checkpointer = MemorySaver()
  app = graph.compile(
      checkpointer=checkpointer,
      interrupt_before=["authorization_handler"]
  )
```

---

## Phase 6: Main Orchestration

### 6.1 Entry Point (`main.py`)
- [ ] Create `DevOpsAgent` class:
```python
  class DevOpsAgent:
      def __init__(self, config_path: str):
          self.config = load_config(config_path)
          self.graph = load_graph()
          self.ipc_channel = IPCChannel()
          self.response_watcher = ResponseWatcher()
          
      def run(self, initial_prompt: str):
          # Main execution loop
          pass
```

- [ ] Implement `run()` method:
  - Initialize state with user prompt
  - Start graph execution
  - Handle interrupts for authorization
  - Wait for blockchain approval
  - Resume graph after approval
  - Return final result

- [ ] Implement `handle_authorization_interrupt()`:
  - Detect when graph pauses
  - Wait for response file
  - Verify response
  - Resume graph with authorization result

- [ ] Add graceful shutdown handling
- [ ] Add logging to file and console

### 6.2 CLI Interface (`main.py`)
- [ ] Add argument parsing:
```python
  parser = argparse.ArgumentParser()
  parser.add_argument("--prompt", required=True)
  parser.add_argument("--config", default="config/agent_config.yaml")
  parser.add_argument("--resume", help="Resume from checkpoint ID")
  parser.add_argument("--debug", action="store_true")
```

- [ ] Add interactive mode for multi-turn conversations
- [ ] Add checkpoint listing command
- [ ] Add tool testing command

---

## Phase 7: Testing & Validation

### 7.1 Unit Tests
- [ ] **IPC Layer Tests** (`tests/test_ipc.py`):
  - Test request serialization/deserialization
  - Test file locking mechanism
  - Test signature verification
  - Test timeout handling

- [ ] **Tool Tests** (`tests/test_tools.py`):
  - Test each safe tool with valid inputs
  - Test path traversal prevention
  - Test error handling for invalid inputs
  - Test tool output format compliance

- [ ] **Risk Classifier Tests** (`tests/test_risk_classifier.py`):
  - Test base scoring for each tier
  - Test parameter modifiers
  - Test edge cases (missing reasoning, etc.)

- [ ] **Graph Tests** (`tests/test_graph.py`):
  - Test state transitions
  - Test interrupt mechanism
  - Test checkpoint save/restore
  - Test error recovery

### 7.2 Integration Tests
- [ ] **End-to-End Safe Flow** (`tests/integration/test_safe_flow.py`):
  - Prompt: "Read the auth.py file and list all functions"
  - Verify: Agent uses read_file, search_codebase
  - Verify: No blockchain calls made

- [ ] **End-to-End Critical Flow** (`tests/integration/test_critical_flow.py`):
  - Prompt: "Deploy the fix to production"
  - Verify: Agent pauses at blockchain_request
  - Mock: Approved response
  - Verify: Agent resumes and completes

- [ ] **Denial Flow** (`tests/integration/test_denial_flow.py`):
  - Prompt: "Delete the users database"
  - Verify: Agent pauses at blockchain_request
  - Mock: Denied response
  - Verify: Agent logs denial and continues

### 7.3 Security Tests
- [ ] **Path Traversal Test**:
  - Attempt: `read_file("../../../../etc/passwd")`
  - Verify: Blocked by validator

- [ ] **Command Injection Test**:
  - Attempt: `create_git_branch("main; rm -rf /")`
  - Verify: Blocked by validator

- [ ] **Replay Attack Test**:
  - Capture auth_request.json
  - Replay same request
  - Verify: Rejected (timestamp check)

- [ ] **Signature Tampering Test**:
  - Modify auth_response.json
  - Verify: Signature verification fails

---

## Phase 8: Demo Preparation

### 8.1 Demo Scenario Script
- [ ] Create `demo_scenario.md` with step-by-step walkthrough
- [ ] Prepare sample codebase with intentional bug:
```python
  # backend/auth.py (buggy version)
  def authenticate(username, password):
      if username == "admin":  # Bug: hardcoded admin bypass
          return True
      return check_password(username, password)
```

- [ ] Write demo prompts:
  1. "Analyze backend/auth.py and identify security issues"
  2. "Fix the authentication bypass vulnerability"
  3. "Run all unit tests to verify the fix"
  4. "Deploy the fix to production"

### 8.2 Mock Blockchain Service (For Demo)
- [ ] Create `mock_blockchain_service.py`:
  - Watch for auth_request.json
  - Simulate 5-second blockchain confirmation delay
  - Auto-approve all requests (for demo)
  - Write auth_response.json
  - Log all transactions to console with colors

- [ ] Add demo mode flag to skip real blockchain
- [ ] Add visual indicators for authorization flow

### 8.3 Demo UI (Optional)
- [ ] Create simple web UI with:
  - Agent thought process display (real-time)
  - Tool execution log
  - Authorization status indicator
  - Blockchain transaction history
  - File diff viewer

---

## Phase 9: Go Blockchain Service Integration

### 9.1 Go Service Watcher
- [ ] Create file system watcher in Go
- [ ] Parse auth_request.json
- [ ] Validate action_hash
- [ ] Format for blockchain submission

### 9.2 Smart Contract Interaction
- [ ] Define smart contract interface for authorization
- [ ] Implement transaction submission
- [ ] Implement event listening for approvals
- [ ] Handle gas estimation and nonce management

### 9.3 Response Generation
- [ ] Sign responses with private key
- [ ] Write auth_response.json atomically
- [ ] Include blockchain transaction receipt
- [ ] Add retry logic for failed transactions

---

## Phase 10: Documentation & Polish

### 10.1 Documentation
- [ ] Write `README.md` with:
  - Project overview
  - Architecture diagram
  - Installation instructions
  - Configuration guide
  - Usage examples

- [ ] Write `ARCHITECTURE.md` (this file, expanded)
- [ ] Write `API.md` documenting all tools
- [ ] Write `SECURITY.md` explaining threat model
- [ ] Write `DEMO_GUIDE.md` for presentations

### 10.2 Code Quality
- [ ] Add type hints to all functions
- [ ] Add docstrings to all public functions
- [ ] Run linters (black, flake8, mypy)
- [ ] Achieve >80% test coverage
- [ ] Add pre-commit hooks

### 10.3 Deployment Preparation
- [ ] Create Docker Compose setup
- [ ] Add health check endpoints
- [ ] Add metrics/monitoring (Prometheus?)
- [ ] Create deployment checklist
- [ ] Write incident response playbook

---

## Success Criteria

### Functional Requirements ✓
- [ ] Agent can autonomously execute 11+ safe/write tools
- [ ] Agent correctly pauses on critical operations
- [ ] Blockchain approval flow works end-to-end
- [ ] Agent resumes after approval without state loss
- [ ] Denials are handled gracefully

### Security Requirements ✓
- [ ] Path traversal attacks blocked
- [ ] Command injection prevented
- [ ] Signature verification enforced
- [ ] Replay attacks detected
- [ ] All critical actions logged immutably

### Demo Requirements ✓
- [ ] Complete demo runs in <5 minutes
- [ ] Authorization flow clearly visible
- [ ] Agent reasoning is understandable
- [ ] Blockchain transaction is observable
- [ ] Failure modes are handled gracefully

---

## Priority Order

### P0 - Critical Path (Week 1)
1. IPC layer implementation
2. Basic tool registry (6 tools)
3. Simple LangGraph with 1 critical tool
4. Mock blockchain service

### P1 - Core Features (Week 2)
1. Risk classifier
2. All 15 tools implemented
3. Full graph with interrupts
4. Real blockchain integration

### P2 - Polish (Week 3)
1. Comprehensive testing
2. Documentation
3. Demo UI
4. Performance optimization

---

## Notes & Decisions

### Technology Choices
- **Why LangGraph?** Built-in checkpointing and state management
- **Why file-based IPC?** Simple, language-agnostic, easy to debug
- **Why not REST API?** Harder to implement true pause/resume
- **Why not message queue?** Adds complexity without clear benefit

### Open Questions
- [ ] Should we add tool usage analytics?
- [ ] Should we implement a "dry run" mode?
- [ ] Should we add multi-agent support later?
- [ ] Should we implement rollback mechanisms?

### Risk Mitigation
- **Risk**: LangGraph doesn't support our use case
  - **Mitigation**: Prototype interrupt mechanism in Week 1
  
- **Risk**: File-based IPC has race conditions
  - **Mitigation**: Use proper file locking from day 1
  
- **Risk**: Blockchain transactions are too slow
  - **Mitigation**: Add timeout handling and user notifications

---

## Maintenance & Future Enhancements

### Post-Launch TODO
- [ ] Add tool usage metrics and analytics
- [ ] Implement tool result caching
- [ ] Add multi-agent collaboration
- [ ] Support for custom tool plugins
- [ ] Web-based configuration UI
- [ ] Integration with CI/CD platforms
- [ ] Support for multiple blockchain networks

---

**Last Updated**: 2024-01-26  
**Status**: Ready for Implementation  
**Owner**: DevOps Team  
**Reviewers**: Security Team, Blockchain Team