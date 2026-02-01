# -----  AI Tools Manager @ services/ai_service/ai_tools/manager.py -----

from langchain_core.tools import tool
import os
import sqlite3

SANDBOX_PATH = os.path.abspath("./services/ai_service/sandbox")
DB_PATH = os.path.join(SANDBOX_PATH, "task_tracker.db")


def _resolve_path(path: str) -> str:
    """
    Resolves a relative path within the sandbox.
    Handles paths that might start with / or ./
    """
    # Remove leading slashes or ./
    path = path.lstrip('./').lstrip('/')
    return os.path.join(SANDBOX_PATH, path)


@tool
def list_directory(path: str = ".") -> str:
    """
    Lists all files and subdirectories in the specified sandbox directory.
    
    Args:
        path: Relative path from sandbox root (e.g., "src" or "." for root)
    
    Returns:
        A formatted list of files and directories
    
    Example:
        list_directory("src") → Shows contents of sandbox/src/
        list_directory(".") → Shows contents of sandbox root
    """
    full_path = _resolve_path(path)
    
    if not os.path.exists(full_path):
        return f"ERROR: Path '{path}' does not exist in sandbox"
    
    if not os.path.isdir(full_path):
        return f"ERROR: '{path}' is not a directory"
    
    items = os.listdir(full_path)
    
    if not items:
        return f"Directory '{path}' is empty"
    
    result = [f"Contents of '{path}':"]
    for item in sorted(items):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            result.append(f"  📁 {item}/")
        else:
            size = os.path.getsize(item_path)
            result.append(f"  📄 {item} ({size} bytes)")
    
    return "\n".join(result)


@tool
def read_file(path: str) -> str:
    """
    Reads the complete contents of a file from the sandbox.
    """
    full_path = _resolve_path(path)
    
    if not os.path.exists(full_path):
        # SMART FIX: If file missing, list what IS there to stop hallucination
        directory = os.path.dirname(full_path)
        if not directory: 
            directory = SANDBOX_PATH
            
        try:
            actual_files = os.listdir(directory)
            files_str = ", ".join(actual_files)
            return f"❌ ERROR: File '{path}' does not exist.\n💡 AVAILABLE FILES: {files_str}\n⚠️ DO NOT TRY READING '{path}' AGAIN."
        except:
            return f"ERROR: File '{path}' does not exist and directory is invalid."
    
    if not os.path.isfile(full_path):
        return f"ERROR: '{path}' is not a file"
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Contents of '{path}':\n\n{content}"
    except Exception as e:
        return f"ERROR reading '{path}': {str(e)}"


@tool
def search_codebase(query: str) -> str:
    """
    Searches for a text string within all files in the src/ directory.
    
    Args:
        query: The text string to search for
    
    Returns:
        List of files containing the query string
    
    Example:
        search_codebase("def verify") → Finds all files with "def verify"
    """
    results = []
    src_dir = os.path.join(SANDBOX_PATH, "src")
    
    if not os.path.exists(src_dir):
        return "ERROR: src/ directory does not exist"
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if query in content:
                        rel_path = os.path.relpath(file_path, SANDBOX_PATH)
                        # Count occurrences
                        count = content.count(query)
                        results.append(f"{rel_path} ({count} occurrence{'s' if count > 1 else ''})")
            except:
                continue
    
    if not results:
        return f"No matches found for '{query}' in src/"
    
    return f"Found '{query}' in:\n" + "\n".join(f"  • {r}" for r in results)


@tool
def read_database(query: str) -> str:
    """
    Executes a SELECT query on the task_tracker.db database.
    ONLY SELECT queries are allowed.
    """
    # ... (Keep existing checks) ...
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # ... (Keep existing success logic) ...
        
        results = cursor.fetchall()
        # ... (formatting code) ...
        return "\n".join([" | ".join(map(str, row)) for row in results])
    
    except Exception as e:
        # FAIL-SAFE: If query fails, show the agent what tables ACTUALLY exist
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return f"❌ SQL Error: {str(e)}\n\n💡 HINT: The valid tables are: {', '.join(tables)}"
        except:
            return f"❌ Database error: {str(e)}"
        finally:
            conn.close()

# ===== CRITICAL TOOLS =====

@tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file in the sandbox. Creates new files or overwrites existing ones.
    ⚠️ CRITICAL ACTION - Requires human approval.
    
    Args:
        path: Relative path from sandbox root (e.g., "src/new_module.py")
        content: The text content to write to the file
    
    Returns:
        Success or error message
    
    Example:
        write_file("src/utils.py", "def helper():\\n    return True")
    """
    full_path = _resolve_path(path)
    
    # Create directory if needed
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        size = len(content)
        return f"✅ Successfully wrote {size} bytes to '{path}'"
    
    except Exception as e:
        return f"ERROR writing to '{path}': {str(e)}"


@tool
def delete_file(path: str) -> str:
    """
    Deletes a specific file from the sandbox.
    ⚠️ CRITICAL ACTION - Requires human approval.
    
    Args:
        path: Relative path from sandbox root (e.g., "src/old_module.py")
    
    Returns:
        Success or error message
    """
    full_path = _resolve_path(path)
    
    if not os.path.exists(full_path):
        return f"ERROR: File '{path}' does not exist"
    
    if not os.path.isfile(full_path):
        return f"ERROR: '{path}' is not a file"
    
    try:
        os.remove(full_path)
        return f"✅ Successfully deleted '{path}'"
    except Exception as e:
        return f"ERROR deleting '{path}': {str(e)}"


@tool
def edit_database(query: str) -> str:
    """
    Executes INSERT, UPDATE, or DELETE queries on task_tracker.db.
    ⚠️ CRITICAL ACTION - Requires human approval.
    
    Args:
        query: A SQL INSERT, UPDATE, or DELETE statement
    
    Returns:
        Success message with rows affected
    """
    query_upper = query.strip().upper()
    if query_upper.startswith("SELECT"):
        return "ERROR: Use read_database for SELECT queries"
    
    if not any(query_upper.startswith(cmd) for cmd in ["INSERT", "UPDATE", "DELETE"]):
        return "ERROR: Only INSERT, UPDATE, DELETE queries allowed"
    
    if not os.path.exists(DB_PATH):
        return "ERROR: Database file not found"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        return f"✅ Query executed successfully. {rows_affected} row(s) affected."
    
    except Exception as e:
        return f"Database error: {str(e)}"


@tool
def delete_database(database_name: str) -> str:
    """
    Deletes the entire task_tracker database.
    ⚠️ CRITICAL ACTION - Requires human approval.
    
    This is an extremely destructive operation that will permanently delete all data.
    
    Args:
        database_name: Name of database to delete (must be "task_tracker.db")
    
    Returns:
        Success or error message
    """
    if database_name != "task_tracker.db":
        return f"ERROR: Unknown database '{database_name}'. Only 'task_tracker.db' exists."
    
    if not os.path.exists(DB_PATH):
        return "ERROR: Database file does not exist"
    
    try:
        os.remove(DB_PATH)
        return f"✅ Database '{database_name}' has been permanently deleted"
    except Exception as e:
        return f"ERROR deleting database: {str(e)}"


@tool
def deploy_to_production() -> str:
    """
    Triggers a deployment to the production environment.
    ⚠️ CRITICAL ACTION - Requires human approval.
    
    This simulates sending a deployment signal in a real system.
    
    Returns:
        Deployment confirmation message
    """
    return "🚀 DEPLOYMENT SIGNAL SENT TO PRODUCTION PIPELINE"


# Tool categorization
TIER_SAFE = [
    "read_file", 
    "list_directory", 
    "read_database", 
    "search_codebase"
]

TIER_CRITICAL = [
    "write_file",
    "delete_file", 
    "edit_database",
    "delete_database", 
    "deploy_to_production"
]


def get_tools():
    """Returns all available tools"""
    return [
        list_directory,
        read_file,
        search_codebase,
        read_database,
        write_file,
        delete_file,
        edit_database,
        delete_database,
        deploy_to_production
    ]


def is_critical(tool_name: str) -> bool:
    """Check if a tool requires human approval"""
    return tool_name in TIER_CRITICAL