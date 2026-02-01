# ----- Database tools @ services/ai_service/ai_tools.db_setup.py -----

import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_PATH = os.path.join(BASE_DIR, "sandbox")
DB_PATH = os.path.join(SANDBOX_PATH, "task_tracker.db")

print(f"🔌 AGENT CONNECTING TO DB AT: {DB_PATH}")

db = SQLDatabase.from_uri(
    f"sqlite:///{DB_PATH}",
    sample_rows_in_table_info=3
)

def get_sql_tools(llm):
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    return toolkit.get_tools()