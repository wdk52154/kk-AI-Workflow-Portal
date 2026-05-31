import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import os

class VoiceStore:
    def __init__(self, db_path: str = "./data/voice.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS voice_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                platform TEXT DEFAULT 'web',
                status TEXT DEFAULT 'active',
                messages TEXT DEFAULT '[]',
                intent_stats TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS voice_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                media_urls TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def create_session(self, user_id: str, platform: str = "web") -> str:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO voice_sessions (session_id, user_id, platform, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sid, user_id, platform, "active", now, now))
        conn.commit()
        conn.close()
        return sid

    def get_session(self, session_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM voice_sessions WHERE session_id = ?', (session_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {
            "session_id": r[0], "user_id": r[1], "platform": r[2],
            "status": r[3], "messages": json.loads(r[4]),
            "intent_stats": json.loads(r[5]),
            "created_at": r[6], "updated_at": r[7]
        }

    def add_message(self, session_id: str, role: str, content: str,
                    intent: str = None, media_urls: List[str] = None):
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO voice_messages (session_id, role, content, intent, media_urls, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, role, content, intent, json.dumps(media_urls or []), now))

        # Update session messages
        c.execute('SELECT messages FROM voice_sessions WHERE session_id = ?', (session_id,))
        msgs = json.loads(c.fetchone()[0])
        msgs.append({"role": role, "content": content, "intent": intent, "created_at": now})
        c.execute('UPDATE voice_sessions SET messages = ?, updated_at = ? WHERE session_id = ?',
                  (json.dumps(msgs), now, session_id))
        conn.commit()
        conn.close()

    def get_messages(self, session_id: str) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT role, content, intent, media_urls, created_at
            FROM voice_messages WHERE session_id = ? ORDER BY created_at
        ''', (session_id,))
        rows = c.fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1], "intent": r[2],
                 "media_urls": json.loads(r[3]), "created_at": r[4]} for r in rows]

    def transfer_session(self, session_id: str, reason: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE voice_sessions SET status = ?, updated_at = ? WHERE session_id = ?',
                  ("transferred", now, session_id))
        conn.commit()
        conn.close()
        return {
            "session_id": session_id,
            "status": "transferred",
            "reason": reason,
            "messages": self.get_messages(session_id)
        }

_voice_store: Optional[VoiceStore] = None

def get_voice_store() -> VoiceStore:
    global _voice_store
    if _voice_store is None:
        _voice_store = VoiceStore()
    return _voice_store
