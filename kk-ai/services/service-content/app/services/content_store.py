import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import os

class ContentStore:
    def __init__(self, db_path: str = "./data/content.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS contents (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                tone TEXT DEFAULT 'lively',
                brand TEXT DEFAULT '',
                keywords TEXT DEFAULT '[]',
                suggested_images TEXT DEFAULT '[]',
                status TEXT DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                scheduled_at TEXT,
                status TEXT DEFAULT 'scheduled',
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def create_content(self, data: dict) -> str:
        cid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO contents (id, platform, title, content, tags, tone, brand, keywords, suggested_images, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cid, data["platform"], data["title"], data["content"],
              json.dumps(data.get("tags", [])), data.get("tone", "lively"),
              data.get("brand", ""), json.dumps(data.get("keywords", [])),
              json.dumps(data.get("suggested_images", [])), "draft", now, now))
        conn.commit()
        conn.close()
        return cid

    def get_content(self, content_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM contents WHERE id = ?', (content_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {
            "id": r[0], "platform": r[1], "title": r[2], "content": r[3],
            "tags": json.loads(r[4]), "tone": r[5], "brand": r[6],
            "keywords": json.loads(r[7]), "suggested_images": json.loads(r[8]),
            "status": r[9], "created_at": r[10], "updated_at": r[11]
        }

    def list_contents(self, platform: Optional[str] = None, page: int = 1, page_size: int = 20):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        where = "1=1"
        params = []
        if platform:
            where += " AND platform = ?"
            params.append(platform)
        c.execute(f"SELECT COUNT(*) FROM contents WHERE {where}", params)
        total = c.fetchone()[0]
        c.execute(f'''
            SELECT * FROM contents WHERE {where}
            ORDER BY updated_at DESC LIMIT ? OFFSET ?
        ''', params + [page_size, (page - 1) * page_size])
        rows = c.fetchall()
        conn.close()
        data = []
        for r in rows:
            data.append({
                "id": r[0], "platform": r[1], "title": r[2], "content": r[3],
                "tags": json.loads(r[4]), "tone": r[5], "brand": r[6],
                "keywords": json.loads(r[7]), "suggested_images": json.loads(r[8]),
                "status": r[9], "created_at": r[10], "updated_at": r[11]
            })
        return {"data": data, "total": total, "page": page, "page_size": page_size}

    def update_content(self, content_id: str, data: dict) -> Optional[dict]:
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        fields = []
        params = []
        for k, v in data.items():
            if k in ["tags", "keywords", "suggested_images"]:
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            params.append(v)
        params.append(now)
        params.append(content_id)
        c.execute(f"UPDATE contents SET {', '.join(fields)}, updated_at = ? WHERE id = ?", params)
        conn.commit()
        conn.close()
        return self.get_content(content_id)

    def create_schedule(self, data: dict) -> str:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO schedules (id, content_id, platform, scheduled_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sid, data["content_id"], data["platform"], data.get("scheduled_at"), data.get("status", "scheduled"), now))
        conn.commit()
        conn.close()
        return sid

    def list_schedules(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT s.id, s.content_id, s.platform, s.scheduled_at, s.status, s.created_at,
                   c.title, c.content
            FROM schedules s LEFT JOIN contents c ON s.content_id = c.id
            ORDER BY s.scheduled_at
        ''')
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "content_id": r[1], "platform": r[2],
                 "scheduled_at": r[3], "status": r[4], "created_at": r[5],
                 "title": r[6], "content": r[7]} for r in rows]

_content_store: Optional[ContentStore] = None

def get_content_store() -> ContentStore:
    global _content_store
    if _content_store is None:
        _content_store = ContentStore()
    return _content_store
