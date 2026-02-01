# ----- File systems and DB tools @ services/ai_service/ai_tools/manager.py -----

from langchain_core.tools import tool
import os
from services.ai_service.ai_tools.db_setup import get_sql_tools

SANDBOX_PATH = os.path.abspath("./services/ai_service/sandbox")

def _resolve_path(path: str) -> str:
    """
    Resolves a relative path within the sandbox.
    Handles paths that might start with / or ./
    """
    path = path.lstrip('./').lstrip('/')
    return os.path.join(SANDBOX_PATH, path)

@tool
def list_directory(path: str = ".") -> str:
    """
    Lists all files and subdirectories in the specified sandbox directory.
    
    Args:
        path: Relative path from sandbox root (e.g., "src" or "." for root)
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
        return f"ERROR: File '{path}' does not exist"
    
    if not os.path.isfile(full_path):
        return f"ERROR: '{path}' is not a file"
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f"Contents of '{path}':\n\n{f.read()}"
    except Exception as e:
        return f"ERROR reading '{path}': {str(e)}"

@tool
def search_codebase(query: str) -> str:
    """
    Searches for a text string within all files in the src/ directory.
    Useful for finding where functions or variables are defined.
    """
    results = []
    search_root = SANDBOX_PATH
    
    for root, _, files in os.walk(search_root):
        if ".git" in root or "__pycache__" in root:
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if query in content:
                        rel_path = os.path.relpath(file_path, SANDBOX_PATH)
                        count = content.count(query)
                        results.append(f"{rel_path} ({count} matches)")
            except:
                continue
    
    if not results:
        return f"No matches found for '{query}'"
    
    return f"Found '{query}' in:\n" + "\n".join(f"  • {r}" for r in results)

@tool
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file in the sandbox. Creates new files or overwrites existing ones.
    CRITICAL ACTION - Requires human approval.
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
    CRITICAL ACTION - Requires human approval.
    """
    full_path = _resolve_path(path)
    
    if not os.path.exists(full_path):
        return f"ERROR: File '{path}' does not exist"
    
    try:
        os.remove(full_path)
        return f"✅ Successfully deleted '{path}'"
    except Exception as e:
        return f"ERROR deleting '{path}': {str(e)}"

@tool
def deploy_to_production() -> str:
    """
    Triggers a deployment signal to the production pipeline.
    CRITICAL ACTION - Requires human approval.
    """
    return "🚀 DEPLOYMENT SIGNAL SENT TO PRODUCTION PIPELINE"

TIER_CRITICAL = [
    "write_file",
    "delete_file", 
    "deploy_to_production",
    "sql_db_query"
]

TIER_SAFE = [
    "read_file", 
    "list_directory", 
    "search_codebase",
    "sql_db_list_tables",
    "sql_db_schema",
    "sql_db_query_checker"
]

def is_critical(tool_name: str) -> bool:
    """
    Check if a tool requires human approval
    """
    return tool_name in TIER_CRITICAL

def get_tools(llm):
    """
    Returns combined list of File tools + SQL tools.
    Requires 'llm' to initialize SQL toolkit.
    """
    file_tools = [
        list_directory, 
        read_file, 
        search_codebase, 
        write_file, 
        delete_file, 
        deploy_to_production
    ]

    sql_tools = get_sql_tools(llm)
    
    return file_tools + sql_tools