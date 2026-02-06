import os
import subprocess
from langchain_core.tools import tool
from services.ai_service.ai_tools.db_setup import get_sql_tools

SANDBOX_PATH = os.path.abspath("./services/ai_service/sandbox")

def _resolve_path(path: str) -> str:
    """
    Resolves a relative path within the sandbox.
    Handles paths that might start with / or ./ or be relative
    """
    # Remove leading ./ if present
    if path.startswith('./'):
        path = path[2:]
    
    # Remove leading / if present
    path = path.lstrip('/')
    
    # If path already starts with the sandbox path (full path given), use as-is
    if path.startswith(SANDBOX_PATH):
        return path
    
    # Otherwise, join with sandbox path
    return os.path.join(SANDBOX_PATH, path)

# --- GIT TOOLS ---

def _run_git_command(args: list) -> str:
    """Helper to run git commands in the sandbox root"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=SANDBOX_PATH,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"GIT ERROR: {e.stderr}"
    except FileNotFoundError:
        return "ERROR: Git is not installed in the environment."

@tool
def git_status() -> str:
    """
    Shows the working tree status (changed files, untracked files).
    Use this to see what has changed before committing.
    """
    return _run_git_command(["status"])

@tool
def git_log(limit: int = 5) -> str:
    """
    Shows the commit logs.
    Args:
        limit: Number of commits to show (default 5)
    """
    return _run_git_command(["log", f"-n{limit}", "--oneline"])

@tool
def git_diff() -> str:
    """
    Shows changes between commits, commit and working tree, etc.
    Use this to review modifications before committing.
    """
    return _run_git_command(["diff"])

# --- FILE SYSTEM TOOLS ---

@tool
def list_directory(path: str = ".") -> str:
    """
    Lists all files and subdirectories in the specified sandbox directory.
    
    USAGE: Always start with list_directory(".") to understand the workspace structure.
    
    Args:
        path: Relative path from sandbox root (e.g., "src" or "." for root)
    
    Returns: Detailed directory listing with file sizes and types
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
    
    # Separate directories and files for better readability
    dirs = []
    files = []
    
    for item in sorted(items):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            dirs.append(f"  [DIR]  {item}/")
        else:
            size = os.path.getsize(item_path)
            extension = os.path.splitext(item)[1]
            files.append(f"  [FILE] {item} ({size} bytes){extension}")
    
    if dirs:
        result.append("\nDirectories:")
        result.extend(dirs)
    
    if files:
        result.append("\nFiles:")
        result.extend(files)
    
    return "\n".join(result)

@tool
def read_file(path: str) -> str:
    """
    Reads the complete contents of a text file from the sandbox.
    
    WARNING: Cannot read binary files (.db, .sqlite, .pyc, images)
    For database files, use sql_db_* tools instead.
    
    Args:
        path: Relative path to file (e.g., "src/main.py")
    
    Returns: Full file contents with line numbers for reference
    """
    # Binary file protection
    BINARY_EXTENSIONS = {'.db', '.sqlite', '.sqlite-wal', '.sqlite-shm', '.pyc', '.png', '.jpg', '.jpeg', '.bin'}
    _, ext = os.path.splitext(path)
    
    if ext.lower() in BINARY_EXTENSIONS:
        if ext.lower() in {'.db', '.sqlite'}:
            return f"ERROR: '{path}' is a database file. Use sql_db_list_tables and sql_db_query to inspect it."
        return f"ERROR: '{path}' is a binary file and cannot be read as text."

    full_path = _resolve_path(path)
    
    if not os.path.exists(full_path):
        available_files = os.listdir(os.path.dirname(full_path)) if os.path.dirname(full_path) else []
        return f"ERROR: File '{path}' does not exist. Available files in directory: {', '.join(available_files)}"
    
    if not os.path.isfile(full_path):
        return f"ERROR: '{path}' is not a file"
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Add line numbers for better reference
        lines = content.split('\n')
        numbered_lines = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
        
        return f"Contents of '{path}' ({len(lines)} lines):\n\n" + "\n".join(numbered_lines)
    except Exception as e:
        return f"ERROR reading '{path}': {str(e)}"

@tool
def search_codebase(query: str) -> str:
    """
    Searches for a text string within all files in the sandbox.
    
    USAGE: Use this to find where functions, classes, or variables are defined.
    Example: search_codebase("def authenticate") to find authentication functions
    
    Args:
        query: Text string to search for (case-sensitive)
    
    Returns: List of files containing the query with match counts
    """
    results = []
    search_root = SANDBOX_PATH
    
    for root, _, files in os.walk(search_root):
        # Skip git metadata and cache directories
        if ".git" in root or "__pycache__" in root:
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip binary files
            if file.endswith(('.db', '.sqlite', '.pyc', '.png', '.jpg', '.jpeg')):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if query in content:
                        rel_path = os.path.relpath(file_path, SANDBOX_PATH)
                        count = content.count(query)
                        
                        # Find line numbers where query appears
                        lines = content.split('\n')
                        line_numbers = [i+1 for i, line in enumerate(lines) if query in line]
                        line_info = f"lines {', '.join(map(str, line_numbers[:5]))}"
                        if len(line_numbers) > 5:
                            line_info += f"... (+ {len(line_numbers) - 5} more)"
                        
                        results.append(f"{rel_path} ({count} matches, {line_info})")
            except:
                continue
    
    if not results:
        return f"No matches found for '{query}' in codebase"
    
    return f"Found '{query}' in {len(results)} file(s):\n" + "\n".join(f"  - {r}" for r in results)

@tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file in the sandbox. Creates new files or overwrites existing ones.
    
    CRITICAL ACTION - Requires human approval.
    
    USAGE: Use this after reading existing code and planning modifications.
    Always write complete, valid code - partial updates will break functionality.
    
    Args:
        path: Relative path to file (e.g., "src/auth.py")
        content: Complete file content to write
    
    Returns: Confirmation with file size
    """
    full_path = _resolve_path(path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        size = len(content)
        line_count = content.count('\n') + 1
        return f"Successfully wrote {size} bytes ({line_count} lines) to '{path}'"
    except Exception as e:
        return f"ERROR writing to '{path}': {str(e)}"

@tool
def delete_file(path: str) -> str:
    """
    Deletes a specific file from the sandbox.
    
    CRITICAL ACTION - Requires human approval.
    
    Args:
        path: Relative path to file to delete (e.g., "task_tracker.db" or "src/old_file.py")
    
    Returns: Confirmation of deletion
    """
    full_path = _resolve_path(path)
    
    if not os.path.exists(full_path):
        # Provide helpful debug info
        parent_dir = os.path.dirname(full_path) if os.path.dirname(full_path) else SANDBOX_PATH
        if os.path.exists(parent_dir):
            available = os.listdir(parent_dir)
            return f"ERROR: File '{path}' does not exist at {full_path}. Available files: {', '.join(available)}"
        else:
            return f"ERROR: File '{path}' does not exist. Parent directory also not found: {parent_dir}"
    
    if os.path.isdir(full_path):
        return f"ERROR: '{path}' is a directory, not a file. Use a different method to remove directories."
    
    try:
        os.remove(full_path)
        return f"Successfully deleted '{path}' from sandbox"
    except Exception as e:
        return f"ERROR deleting '{path}': {str(e)}"

@tool
def deploy_to_production() -> str:
    """
    Triggers a deployment signal to the production pipeline.
    
    CRITICAL ACTION - Requires human approval.
    
    Returns: Deployment confirmation
    """
    return "DEPLOYMENT SIGNAL SENT TO PRODUCTION PIPELINE"

# --- TOOL CONFIGURATION ---

TIER_CRITICAL = [
    "write_file",
    "delete_file", 
    "deploy_to_production",
    "sql_db_query",  # Raw SQL execution requires approval
]

TIER_SAFE = [
    "read_file", 
    "list_directory", 
    "search_codebase",
    "sql_db_list_tables",
    "sql_db_schema",
    "sql_db_query_checker",
    "git_status",
    "git_log",
    "git_diff"
]

def is_critical(tool_name: str) -> bool:
    """Check if a tool requires human approval"""
    return tool_name in TIER_CRITICAL

def get_tools(llm):
    """
    Returns combined list of File tools + SQL tools + Git tools.
    
    Tool organization:
    - File System: list_directory, read_file, search_codebase, write_file, delete_file
    - Database: sql_db_list_tables, sql_db_schema, sql_db_query, sql_db_query_checker
    - Version Control: git_status, git_log, git_diff
    - Deployment: deploy_to_production
    """
    file_tools = [
        list_directory, 
        read_file, 
        search_codebase, 
        write_file, 
        delete_file, 
        deploy_to_production,
        git_status,
        git_log,
        git_diff
    ]

    sql_tools = get_sql_tools(llm)
    
    return file_tools + sql_tools