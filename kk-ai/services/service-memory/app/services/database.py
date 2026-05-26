"""SQLite database initialization and connection management."""

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager

from app.config import get_settings

logger = logging.getLogger("service-memory.database")

_DB_LOCK = threading.Lock()


def init_db(db_path: str | None = None) -> None:
    """Initialize SQLite database with required tables."""
    settings = get_settings()
    path = db_path or settings.DB_PATH

    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with _DB_LOCK:
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA journal_mode=WAL")

        # Memories table (conversation history)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mem_session ON memories(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mem_timestamp ON memories(timestamp)
        """)

        # User facts table (cross-project user profile)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                fact_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                fact_type TEXT NOT NULL,
                fact_content TEXT NOT NULL,
                embedding TEXT,
                confidence REAL NOT NULL,
                source_project_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_fact_unique
            ON user_facts(user_id, fact_type, fact_content)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_fact_user ON user_facts(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_fact_type ON user_facts(fact_type)
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized: %s", path)


@contextmanager
def get_db_connection(db_path: str | None = None):
    """Get a database connection context manager."""
    settings = get_settings()
    path = db_path or settings.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
