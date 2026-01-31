from langchain_core.tools import tool

@tool
def read_file(path: str):
    """
    Reads a file from the repository sandbox.
    """
    return f"Contents of {path}: [Mock file content for {path}]"

@tool
def list_directory(path: str = "."):
    """
    Lists files in the current directory.
    """
    return "README.md, main.py, data.db, src/"

@tool
def delete_database(database_name: str):
    """
    Deletes a database file. 
    CRITICAL: Permanent action.
    """
    return f"SUCCESS: {database_name} has been deleted from disk."

@tool
def write_file(path: str, content: str):
    """Writes or overwrites a file. 
    CRITICAL: Changes codebase.
    """
    return f"SUCCESS: Content written to {path}."

TIER_SAFE = ["read_file", "list_directory"]
TIER_CRITICAL = ["delete_database", "write_file"]

def get_tools():
    return [read_file, list_directory, delete_database, write_file]

def is_critical(tool_name: str) -> bool:
    return tool_name in TIER_CRITICAL