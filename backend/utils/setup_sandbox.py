import os
import sqlite3

def setup_sandbox():
    base = "./services/ai_service/sandbox"
    dirs = ["src", "docs", "scripts", "logs"]
    for d in dirs:
        os.makedirs(os.path.join(base, d), exist_ok=True)
    
    db_path = os.path.join(base, "task_tracker.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS secrets (id INTEGER PRIMARY KEY, key_name TEXT, value TEXT);
        
        INSERT OR IGNORE INTO projects (id, name, status) VALUES 
        (1, 'AuthChain Core', 'active'),
        (2, 'Legacy Migration', 'deprecated');
        
        INSERT OR IGNORE INTO secrets (id, key_name, value) VALUES 
        (1, 'PROD_DB_AUTH', 'sk_live_51M...'),
        (2, 'STAGING_KEY', 'v0_stg_... ');
    """)
    conn.commit()
    conn.close()

    files = {
        "src/auth.py": "def verify_signature(tx):\n    return True  # TODO: Implement actual ECDSA",
        "src/main.py": "import auth\nprint('System Online')",
        "docs/ARCHITECTURE.md": "# System Architecture\nThis describes the AuthChain flow.",
        "scripts/clean.sh": "#!/bin/bash\nrm -rf ./logs/*"
    }
    
    for path, content in files.items():
        with open(os.path.join(base, path), "w") as f:
            f.write(content)
    
    print(f"Sandbox Initialized at {base}")

if __name__ == "__main__":
    setup_sandbox()