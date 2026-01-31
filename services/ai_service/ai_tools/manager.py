# services/ai_service/ai_tools/manager.py -- Tool definitions and management

from langchain_core.tools import tool
import os
import sqlite3

SANDBOX_PATH = os.path.abspath("./services/ai_service/sandbox")
DB_PATH = os.path.join(SANDBOX_PATH, "task_tracker.db")

@tool
def search_codebase(query: str):
    """Searches for a string within the src/ directory."""
    results = []
    src_dir = os.path.join(SANDBOX_PATH, "src")
    for root, _, files in os.walk(src_dir):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                if query in f.read():
                    results.append(f"{file} matches '{query}'")
    return results if results else "No matches found."

@tool
def read_file(path: str):
    """Reads a file from the sandbox."""
    full_path = os.path.join(SANDBOX_PATH, path)
    with open(full_path, 'r') as f: return f.read()

@tool
def list_directory(path: str = "."):
    """Lists files in the sandbox."""
    return os.listdir(os.path.join(SANDBOX_PATH, path))

@tool
def read_database(query: str):
    """Executes a SELECT query on the task database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    res = cursor.fetchall()
    conn.close()
    return res

@tool
def delete_file(path: str):
    """
    Deletes a specific file from the sandbox. 
    CRITICAL ACTION.
    """
    full_path = os.path.join(SANDBOX_PATH, path)
    if os.path.exists(full_path):
        os.remove(full_path)
        return f"SUCCESS: {path} has been deleted."
    else:
        return f"ERROR: File {path} not found."

@tool
def delete_database(database_name: str):
    """Deletes the database. CRITICAL ACTION."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        return f"DELETED {database_name} successfully."
    return "ERROR: Database file not found."

@tool
def write_file(path: str, content: str):
    """Writes content to a file. CRITICAL ACTION."""
    full_path = os.path.join(SANDBOX_PATH, path)
    with open(full_path, 'w') as f: f.write(content)
    return f"Successfully wrote to {path}"

@tool
def edit_database(query: str):
    """Executes UPDATE/INSERT/DELETE queries. CRITICAL ACTION."""
    db_path = os.path.join(SANDBOX_PATH, "task_tracker.db")
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        return f"Successfully executed change. Rows affected: {cursor.rowcount}"
    except Exception as e:
        return f"Database Error: {str(e)}"
    finally:
        conn.close()

@tool
def deploy_to_production():
    """Triggers production deployment. CRITICAL ACTION."""
    return "DEPLOYMENT SIGNAL SENT TO PROD"

# Updated Tiers
TIER_SAFE = ["read_file", "list_directory", "read_database", "search_codebase", "git_log", "git_diff"]
TIER_CRITICAL = [
    "deploy_to_production", 
    "delete_database", 
    "delete_file", 
    "git_push_commit", 
    "edit_database", 
    "write_file"
]

def get_tools():
    return [
        read_file, 
        list_directory, 
        read_database, 
        delete_file, 
        delete_database, 
        write_file, 
        edit_database,
        deploy_to_production
    ]

def is_critical(tool_name: str) -> bool:
    return tool_name in TIER_CRITICAL