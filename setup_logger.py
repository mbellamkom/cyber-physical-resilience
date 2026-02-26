import sqlite3
import os
from pathlib import Path

DB_DIR = r"D:\Cyber_Physical_DBs"
DB_PATH = os.path.join(DB_DIR, "agent_logs.db")

def create_database():
    Path(DB_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        model_version TEXT NOT NULL,
        source_document_name TEXT,
        system_prompt TEXT NOT NULL,
        extracted_text TEXT NOT NULL,
        raw_model_response TEXT,
        parsed_output_json TEXT,
        processing_time_ms INTEGER,
        error_flag BOOLEAN DEFAULT 0,
        error_message TEXT
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
