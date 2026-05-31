import sqlite3
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
import os

class ScriptStore:
    def __init__(self, db_path: str = "./data/sales.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                tags TEXT DEFAULT '[]',
                scenario TEXT DEFAULT '',
                conversion_rate REAL DEFAULT 0,
                objection_target TEXT,
                usage_count INTEGER DEFAULT 0,
                source TEXT DEFAULT 'manual',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS roleplay_sessions (
                session_id TEXT PRIMARY KEY,
                customer_type TEXT NOT NULL,
                scenario TEXT,
                product TEXT,
                transcript TEXT DEFAULT '[]',
                scores TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                ended_at TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def create_script(self, data: dict) -> str:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO scripts (id, title, content, category, tags, scenario,
                conversion_rate, objection_target, usage_count, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sid, data["title"], data["content"], data.get("category", "general"),
            json.dumps(data.get("tags", [])), data.get("scenario", ""),
            data.get("conversion_rate", 0.0), data.get("objection_target"),
            0, data.get("source", "manual"), now, now
        ))
        conn.commit()
        conn.close()
        return sid

    def list_scripts(self, category: Optional[str] = None, q: Optional[str] = None,
                     page: int = 1, page_size: int = 20):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        where = "1=1"
        params = []
        if category:
            where += " AND category = ?"
            params.append(category)
        if q:
            where += " AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        c.execute(f"SELECT COUNT(*) FROM scripts WHERE {where}", params)
        total = c.fetchone()[0]
        c.execute(f'''
            SELECT id, title, content, category, tags, scenario,
                   conversion_rate, objection_target, usage_count, source,
                   created_at, updated_at
            FROM scripts WHERE {where}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        ''', params + [page_size, (page - 1) * page_size])
        rows = c.fetchall()
        conn.close()
        data = []
        for r in rows:
            data.append({
                "id": r[0], "title": r[1], "content": r[2], "category": r[3],
                "tags": json.loads(r[4]), "scenario": r[5],
                "conversion_rate": r[6], "objection_target": r[7],
                "usage_count": r[8], "source": r[9],
                "created_at": r[10], "updated_at": r[11]
            })
        return {"data": data, "total": total, "page": page, "page_size": page_size}

    def get_script(self, script_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT id, title, content, category, tags, scenario,
                   conversion_rate, objection_target, usage_count, source,
                   created_at, updated_at
            FROM scripts WHERE id = ?
        ''', (script_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {
            "id": r[0], "title": r[1], "content": r[2], "category": r[3],
            "tags": json.loads(r[4]), "scenario": r[5],
            "conversion_rate": r[6], "objection_target": r[7],
            "usage_count": r[8], "source": r[9],
            "created_at": r[10], "updated_at": r[11]
        }

    def delete_script(self, script_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
        ok = c.rowcount > 0
        conn.commit()
        conn.close()
        return ok

    def increment_usage(self, script_id: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE scripts SET usage_count = usage_count + 1 WHERE id = ?", (script_id,))
        conn.commit()
        conn.close()

    # --- Roleplay session ---
    def create_session(self, session_id: str, customer_type: str, scenario: Optional[str],
                       product: Optional[str]):
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO roleplay_sessions (session_id, customer_type, scenario, product, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, customer_type, scenario, product, now))
        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT session_id, customer_type, scenario, product, transcript, scores, created_at, ended_at
            FROM roleplay_sessions WHERE session_id = ?
        ''', (session_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {
            "session_id": r[0], "customer_type": r[1], "scenario": r[2],
            "product": r[3], "transcript": json.loads(r[4]),
            "scores": json.loads(r[5]), "created_at": r[6], "ended_at": r[7]
        }

    def append_message(self, session_id: str, role: str, content: str):
        session = self.get_session(session_id)
        if not session:
            return False
        transcript = session["transcript"]
        transcript.append({"role": role, "content": content, "time": datetime.now(timezone.utc).isoformat()})
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE roleplay_sessions SET transcript = ? WHERE session_id = ?",
                  (json.dumps(transcript), session_id))
        conn.commit()
        conn.close()
        return True

    def list_sessions(self, page: int = 1, page_size: int = 20):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM roleplay_sessions WHERE ended_at IS NOT NULL")
        total = c.fetchone()[0]
        c.execute('''
            SELECT session_id, customer_type, scenario, product, transcript,
                   scores, created_at, ended_at
            FROM roleplay_sessions
            WHERE ended_at IS NOT NULL
            ORDER BY ended_at DESC
            LIMIT ? OFFSET ?
        ''', (page_size, (page - 1) * page_size))
        rows = c.fetchall()
        conn.close()
        data = []
        for r in rows:
            scores = json.loads(r[5]) if r[5] else {}
            data.append({
                "id": r[0], "session_id": r[0], "conversation_type": "roleplay",
                "transcript": json.loads(r[4]), "total_score": scores.get("total_score"),
                "quality_marked": scores.get("total_score", 0) >= 80,
                "metadata": {"customer_type": r[1], "scenario": r[2], "product": r[3]},
                "created_at": r[6], "ended_at": r[7]
            })
        return {"data": data, "total": total, "page": page, "page_size": page_size}

    def end_session(self, session_id: str, scores: dict):
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE roleplay_sessions SET scores = ?, ended_at = ? WHERE session_id = ?",
                  (json.dumps(scores), now, session_id))
        conn.commit()
        conn.close()

_script_store: Optional[ScriptStore] = None

def get_script_store() -> ScriptStore:
    global _script_store
    if _script_store is None:
        _script_store = ScriptStore()
    return _script_store
