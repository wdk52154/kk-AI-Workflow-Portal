"""SQLite database initialization and connection management."""

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager

from app.config import get_settings

logger = logging.getLogger("service-data.database")

_DB_LOCK = threading.Lock()


def init_db(db_path: str | None = None) -> None:
    """Initialize SQLite database with required tables."""
    settings = get_settings()
    path = db_path or settings.DB_PATH

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with _DB_LOCK:
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA journal_mode=WAL")

        # Raw data table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                project_id TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                metadata TEXT,
                status TEXT DEFAULT 'pending',
                batch_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_unique
            ON raw_data(raw_id, source_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_raw_batch ON raw_data(batch_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_raw_project ON raw_data(project_id)
        """)

        # Cleaned data table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cleaned_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_data_id INTEGER NOT NULL,
                source_type TEXT NOT NULL,
                project_id TEXT NOT NULL,
                original_content TEXT NOT NULL,
                cleaned_content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                quality_score INTEGER,
                intent TEXT,
                emotion TEXT,
                tags TEXT,
                is_annotated INTEGER DEFAULT 0,
                annotation_data TEXT,
                status TEXT DEFAULT 'available',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (raw_data_id) REFERENCES raw_data(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cleaned_project ON cleaned_data(project_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cleaned_intent ON cleaned_data(intent)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cleaned_quality ON cleaned_data(quality_score)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cleaned_status ON cleaned_data(status)
        """)

        # Data batches table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_batches (
                batch_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                project_id TEXT NOT NULL,
                record_count INTEGER NOT NULL,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processing',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_batch_project ON data_batches(project_id)
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
