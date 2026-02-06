### AI Service Overview
The typical sequence of steps that happen upon receiving a user prompt are:
1. Receive user query via API.
2. Process query into langgraph service.
3. Should be able to execute multiple read tools safely consequtively.
4. Any write/delete tool, i.e labelled as `Critical Tools` are to be interrupted.
    - The agent state is written into a sandboxes SQL database.
5. Forward a JSON (currently via IPC, future, API communication) to the blockchain pipeline.
    - Example JSON output transfer
```
{
  "tool_name": "list_directory",
  "tool_arguments": {
    "path": "./services/ai_service/sandbox/"
  },
  "reasoning_summary": "The AI agent wants to call 'list_directory' because it needs to retrieve the list of files in the specified directory, likely to check if a user's sandbox is present and can be deleted. This is necessary for the AI to fulfill the human's request to delete a user DB by first verifying that the relevant sandbox exists.",
  "timestamp": "2026-02-04T17:42:14.583978",
  "checkpoint_id": "37a1c383-7d92-4e56-aacd-a4cd351d5577"
}
```
6. Receive output from the blockchain pipeline, and should consist of
    -  TRUE
        - Permits continuation of execution of the agent state, restored from the SQL db.
    - FALSE
        - Typically comes with a field for User explaination for rejection.
        - Does not permit usage of the tool.