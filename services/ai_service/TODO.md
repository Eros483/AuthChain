- **Pipeline**
    - User queries agent.
    - Agent uses tools.
    - Tier 1 tools go through check node.
    - Tier 2 or Tier 3 tools are stopped at node.
        - Use `interrupt_before`.
    - Save checkpoint, extract relevant information including tool call, arguments, and reasoning.
    - Send reasoning to be summarized by LLM.
    - Use IPC to send reasoning, tool call, and arguments to blockchain pipeline.
        - If accepted, restore state, continue execution.
        - If rejected, do NOT restore state—agent remains at interrupt point.
            - Return rejection message to agent context.
            - Agent acknowledges rejection and explains to user why action was blocked.
            - Frontend displays warning with rejection reason.

- **Use-Case Scenario**
    - Agent interacts with a sandboxed repository directory.
    - Agent has access to a small SQLite database (task tracking, feature flags, user data).
    - Autonomous coding agent that can read, write, commit code, and interact with database.
    - **Demo highlight**: Show agent attempting to delete database (common AI agent failure mode) and governance system blocking it.

- **Tools to be implemented**
```yaml
  tool_tiers:
    tier1_safe: [read_file, list_directory, search_codebase, git_log, git_diff, read_database]
    tier2_write: [write_file, git_commit, edit_database]
    tier3_critical: [deploy_to_production, delete_database, git_push]
```

- **State Restoration Logic**
    - **On Approval**: Load checkpoint, execute tool call, continue agent loop.
    - **On Rejection**: Keep checkpoint frozen, inject rejection message into agent's next input, agent reformulates approach or informs user it cannot proceed.
    - LangGraph's interrupt mechanism naturally preserves state—no manual rollback needed.

- **Notes**
    - Blockchain integration handled via IPC (send structured JSON, receive approval/rejection).
    - `deploy_to_production` triggers alert on blockchain UI—no actual deployment needed.
    - Database included specifically to demonstrate governance blocking dangerous `delete_database` operations.
