import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import os

class LiveStore:
    def __init__(self, db_path: str = "./data/live.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS records (
                record_id TEXT PRIMARY KEY,
                stream_url TEXT NOT NULL,
                title TEXT,
                platform TEXT,
                status TEXT DEFAULT 'recording',
                duration_seconds INTEGER DEFAULT 0,
                video_url TEXT,
                highlights TEXT DEFAULT '[]',
                transcript TEXT DEFAULT '[]',
                started_at TEXT NOT NULL,
                stopped_at TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS clips (
                clip_id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                title TEXT,
                start_time REAL,
                end_time REAL,
                duration REAL,
                video_url TEXT,
                enhancements TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def start_record(self, stream_url: str, title: str, platform: str) -> str:
        rid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO records (record_id, stream_url, title, platform, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (rid, stream_url, title, platform, "recording", now))
        conn.commit()
        conn.close()
        return rid

    def stop_record(self, record_id: str, duration: int, video_url: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE records SET status = ?, duration_seconds = ?, video_url = ?, stopped_at = ?
            WHERE record_id = ?
        ''', ("stopped", duration, video_url, now, record_id))
        conn.commit()
        conn.close()
        return self.get_record(record_id)

    def get_record(self, record_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM records WHERE record_id = ?', (record_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {
            "record_id": r[0], "stream_url": r[1], "title": r[2], "platform": r[3],
            "status": r[4], "duration_seconds": r[5], "video_url": r[6],
            "highlights": json.loads(r[7]), "transcript": json.loads(r[8]),
            "started_at": r[9], "stopped_at": r[10]
        }

    def save_analysis(self, record_id: str, highlights: list, transcript: list):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE records SET highlights = ?, transcript = ? WHERE record_id = ?
        ''', (json.dumps(highlights), json.dumps(transcript), record_id))
        conn.commit()
        conn.close()

    def create_clip(self, record_id: str, title: str, start_time: float,
                    end_time: float, duration: float, video_url: str) -> str:
        cid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO clips (clip_id, record_id, title, start_time, end_time, duration, video_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cid, record_id, title, start_time, end_time, duration, video_url, now))
        conn.commit()
        conn.close()
        return cid

    def get_clip(self, clip_id: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM clips WHERE clip_id = ?', (clip_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {
            "clip_id": r[0], "record_id": r[1], "title": r[2],
            "start_time": r[3], "end_time": r[4], "duration": r[5],
            "video_url": r[6], "enhancements": json.loads(r[7]), "status": r[8]
        }

    def list_clips(self, record_id: Optional[str] = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if record_id:
            c.execute('SELECT * FROM clips WHERE record_id = ? ORDER BY created_at DESC', (record_id,))
        else:
            c.execute('SELECT * FROM clips ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()
        return [{"clip_id": r[0], "record_id": r[1], "title": r[2],
                 "start_time": r[3], "end_time": r[4], "duration": r[5],
                 "video_url": r[6], "enhancements": json.loads(r[7]),
                 "status": r[8]} for r in rows]

    def update_clip(self, clip_id: str, data: dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        fields = []
        params = []
        for k, v in data.items():
            if k == "enhancements":
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            params.append(v)
        params.append(clip_id)
        c.execute(f"UPDATE clips SET {', '.join(fields)} WHERE clip_id = ?", params)
        conn.commit()
        conn.close()

_live_store: Optional[LiveStore] = None

def get_live_store() -> LiveStore:
    global _live_store
    if _live_store is None:
        _live_store = LiveStore()
    return _live_store
