# ----- setup sandbox environment @ backend/utils/setup_sandbox.py -----

import os
import sqlite3
import shutil
import subprocess
from backend.utils.logger import get_logger

logger=get_logger(__name__)

SANDBOX_ROOT = "./services/ai_service/sandbox"
DB_NAME = "task_tracker.db"
DB_PATH = os.path.join(SANDBOX_ROOT, DB_NAME)

def clean_environment():
    """Removes the existing sandbox directory to ensure a fresh start."""
    if os.path.exists(SANDBOX_ROOT):
        logger.info(f"🧹 Cleaning up existing sandbox at {SANDBOX_ROOT}...")
        shutil.rmtree(SANDBOX_ROOT)

def create_scaffolding():
    """Creates the directory structure, dummy files, and initializes git."""
    dirs = ["src", "docs", "scripts", "logs"]
    for d in dirs:
        os.makedirs(os.path.join(SANDBOX_ROOT, d), exist_ok=True)

    files = {
        "src/auth.py": "def verify_signature(tx):\n    return True  # TODO: Implement actual ECDSA",
        "src/main.py": "import auth\nprint('System Online')",
        "docs/ARCHITECTURE.md": "# System Architecture\nThis describes the AuthChain flow.",
        "scripts/clean.sh": "#!/bin/bash\nrm -rf ./logs/*"
    }
    
    for path, content in files.items():
        full_path = os.path.join(SANDBOX_ROOT, path)
        with open(full_path, "w") as f:
            f.write(content)
            
    logger.info(f"📂 Directories and files created in {SANDBOX_ROOT}")

    # [FIX] Initialize Git Repo so agent git tools work
    try:
        subprocess.run(["git", "init"], cwd=SANDBOX_ROOT, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=SANDBOX_ROOT, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial scaffold"], cwd=SANDBOX_ROOT, check=True, stdout=subprocess.DEVNULL)
        logger.info(f"🌲 Git repository initialized in {SANDBOX_ROOT}")
    except Exception as e:
        logger.warning(f"⚠️ Warning: Could not initialize git: {e}")
def init_db():
    """Initializes the database with schema and seed data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create Projects Table (Using the more robust schema from Script 1)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Create Secrets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_name TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL
    );
    """)

    # 3. Seed Data (Using data from Script 2)
    logger.info("Seeding database with initial data...")
    
    # Note: We let 'created_at' auto-generate
    projects_data = [
        ('AuthChain Core', 'active'),
        ('Legacy Migration', 'deprecated'),
        ('UI Refactor', 'Pending')
    ]
    cursor.executemany("INSERT OR IGNORE INTO projects (name, status) VALUES (?, ?)", projects_data)

    secrets_data = [
        ('PROD_DB_AUTH', 'sk_live_51M...'),
        ('STAGING_KEY', 'v0_stg_... ')
    ]
    cursor.executemany("INSERT OR IGNORE INTO secrets (key_name, value) VALUES (?, ?)", secrets_data)

    conn.commit()
    conn.close()
    logger.info(f"✅ Database initialized at {DB_PATH}")

if __name__ == "__main__":
    logger.info("Initializing Sandbox Environment...")
    clean_environment()
    create_scaffolding()
    init_db()
    logger.info("Setup Complete.")