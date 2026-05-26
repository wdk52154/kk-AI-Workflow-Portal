# TASK-403：Memory Service（service-memory）

## 元信息

| 字段     | 值                                         |
| -------- | ------------------------------------------ |
| TASK ID  | TASK-403                                   |
| 标题     | Memory Service - 对话记忆与用户画像服务    |
| 负责人   | @backend-lead                              |
| 优先级   | P0                                         |
| 预估工时 | 6h                                         |
| 关联需求 | TASK-401 LLM Gateway（Embedding 语义检索） |

---

## 1. 背景

AI 中台需要统一的记忆服务，解决两个核心问题：

1. **对话记忆**：多轮对话中 LLM 需要上下文，但受限于 token 上限，不能把所有历史都塞进去。需要智能地存储和召回最相关的对话片段。
2. **跨项目用户画像**：用户在项目 A（医疗助手）告诉系统"我对芒果过敏"，当他在项目 B（餐饮推荐）提问时，系统应该自动规避芒果相关推荐，无需重复说明。

---

## 2. 目标

实现 `service-memory` 服务（端口 9003），提供对话记忆管理和跨项目用户画像：

- **对话记忆**：按 `session_id` 存储多轮对话，支持语义检索召回
- **用户画像**：`user_facts` 表记录关键事实，跨项目共享
- **热冷分离**：热数据（最近 7 天）Redis，冷数据（历史）PostgreSQL
- **语义检索**：记忆召回支持向量相似度搜索

---

## 3. 验收标准

### AC-1：存储对话记忆

- [ ] `POST /v1/store_memory` 存储单条对话片段
- [ ] 请求体：`session_id`、`user_id`、`role`（user/assistant）、`content`、`timestamp`
- [ ] 自动对 `content` 做 Embedding（调用 LLM Gateway），存入向量索引
- [ ] 同时写入 Redis（热数据）和 PostgreSQL（冷数据持久化）
- [ ] 返回：`memory_id`、`status`

### AC-2：召回对话记忆

- [ ] `POST /v1/recall_memory` 按语义检索召回相关记忆
- [ ] 请求体：`session_id`、`query`（当前用户输入）、`top_k`（默认 5）
- [ ] 先对 `query` 做 Embedding，然后向量相似度搜索该 session 的历史
- [ ] 返回 Top-K 最相关的历史对话片段，按相关性排序
- [ ] 响应格式：
  ```json
  {
    "query": "...",
    "session_id": "...",
    "results": [
      {
        "memory_id": "...",
        "role": "user",
        "content": "...",
        "score": 0.95,
        "timestamp": "2026-05-26T10:00:00Z"
      }
    ]
  }
  ```

### AC-3：存储用户事实

- [ ] `POST /v1/store_user_fact` 存储/更新用户关键事实
- [ ] 请求体：`user_id`、`fact_type`、`fact_content`、`confidence`（0.0-1.0）、`source_project_id`
- [ ] `fact_type` 枚举：`preference`、`constraint`、`profile`、`behavior`
- [ ] 对 `fact_content` 做 Embedding，存入向量索引（支持语义召回）
- [ ] 如果同一 `user_id + fact_type + fact_content` 已存在，更新 `confidence` 和 `updated_at`
- [ ] 返回：`fact_id`、`status`

### AC-4：召回用户事实

- [ ] `POST /v1/recall_user_facts` 按 `user_id` 召回所有事实
- [ ] 请求体：`user_id`、`fact_type`（可选过滤）、`query`（可选语义过滤）
- [ ] 如果提供 `query`，先对 query 做 Embedding，然后与用户 facts 做向量相似度匹配
- [ ] 返回匹配的事实列表，按 `confidence` 降序排列
- [ ] 响应格式：
  ```json
  {
    "user_id": "...",
    "total": 3,
    "facts": [
      {
        "fact_id": "...",
        "fact_type": "constraint",
        "fact_content": "对芒果过敏",
        "confidence": 0.98,
        "source_project_id": "proj_001",
        "created_at": "2026-05-26T10:00:00Z"
      }
    ]
  }
  ```

### AC-5：热冷数据分离

- [ ] **热数据（Redis）**：最近 7 天的记忆，快速读取
- [ ] **冷数据（PostgreSQL）**：全部历史，持久化存储
- [ ] `recall_memory` 优先查 Redis，缺失时查 PostgreSQL
- [ ] 后台定时任务（每天凌晨）将 Redis 中超期数据归档到 PostgreSQL
- [ ] **当前阶段降级**：Redis 用内存 Dict，PostgreSQL 用 SQLite

### AC-6：跨项目用户画像

- [ ] `user_facts` 不按 `project_id` 隔离，全局共享
- [ ] 任何项目写入的事实，其他项目都可以读取
- [ ] 事实来源追溯：记录 `source_project_id`，方便审计

### AC-7：健康检查与监控

- [ ] `GET /health` 返回服务状态、Redis 连接、PostgreSQL 连接、索引数量

### AC-8：测试与质量

- [ ] `pytest` 全部通过，覆盖率 ≥ 50%
- [ ] 至少 2 个 store_memory + recall_memory 测试
- [ ] 至少 2 个 store_user_fact + recall_user_facts 测试
- [ ] 至少 1 个跨项目事实共享测试（项目 A 写入，项目 B 读取）
- [ ] 至少 1 个语义检索测试（用 query 召回相关记忆）

---

## 4. 技术方案

### 项目结构

```
services/service-memory/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── memory.py        # 对话记忆模型
│   │   └── user_fact.py     # 用户事实模型
│   ├── router/
│   │   ├── __init__.py
│   │   ├── memory.py        # /v1/store_memory, /v1/recall_memory
│   │   └── user_fact.py     # /v1/store_user_fact, /v1/recall_user_facts
│   ├── services/
│   │   ├── __init__.py
│   │   ├── memory_store.py  # 记忆存储服务（Redis + PG）
│   │   ├── user_fact_store.py # 用户事实存储服务
│   │   ├── embedding_client.py # LLM Gateway Embedding 客户端
│   │   └── vector_index.py  # 内存向量索引（语义检索）
│   └── middleware/
│       └── logger.py        # 结构化日志
├── data/                    # SQLite 数据目录
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_memory.py
│   └── test_user_fact.py
├── pyproject.toml
├── run.py
└── .env.example
```

### 数据模型

```python
# app/models/memory.py
from datetime import datetime
from pydantic import BaseModel, Field

class MemoryEntry(BaseModel):
    """A single conversation memory entry."""
    memory_id: str
    session_id: str
    user_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    embedding: list[float] | None = None
    timestamp: datetime

class StoreMemoryRequest(BaseModel):
    session_id: str
    user_id: str
    role: str = "user"
    content: str = Field(..., min_length=1)

class StoreMemoryResponse(BaseModel):
    memory_id: str
    status: str = "stored"

class RecallMemoryRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

class RecallMemoryResult(BaseModel):
    memory_id: str
    role: str
    content: str
    score: float
    timestamp: str

class RecallMemoryResponse(BaseModel):
    query: str
    session_id: str
    results: list[RecallMemoryResult]
    total: int
```

```python
# app/models/user_fact.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class UserFact(BaseModel):
    """A user fact/profile entry."""
    fact_id: str
    user_id: str
    fact_type: Literal["preference", "constraint", "profile", "behavior"]
    fact_content: str
    embedding: list[float] | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_project_id: str
    created_at: datetime
    updated_at: datetime

class StoreUserFactRequest(BaseModel):
    user_id: str
    fact_type: Literal["preference", "constraint", "profile", "behavior"]
    fact_content: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_project_id: str

class RecallUserFactsRequest(BaseModel):
    user_id: str
    fact_type: str | None = None
    query: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)
```

### 存储策略

```python
# app/services/memory_store.py
"""
Memory storage with hot/cold separation.

Hot (Redis/memory): Recent 7 days, fast read.
Cold (PostgreSQL/SQLite): Full history, persistent.

Current stage downgrade:
- Redis → Memory Dict with TTL
- PostgreSQL → SQLite
"""

import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone

class MemoryStore:
    """Dual-layer memory store: hot (memory) + cold (SQLite)."""

    def __init__(self, db_path: str = "./data/memory.db"):
        self._hot: dict[str, dict] = {}  # memory_id -> entry
        self._hot_ttl_days = 7
        self._lock = threading.Lock()
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite tables."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_session ON memories(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user ON memories(user_id)
        """)
        conn.commit()
        conn.close()

    def store(self, entry: MemoryEntry) -> str:
        """Store to both hot and cold."""
        with self._lock:
            self._hot[entry.memory_id] = entry.model_dump()

        # Cold storage
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry.memory_id, entry.session_id, entry.user_id,
             entry.role, entry.content,
             json.dumps(entry.embedding) if entry.embedding else None,
             entry.timestamp.isoformat())
        )
        conn.commit()
        conn.close()
        return entry.memory_id

    def recall_by_session(self, session_id: str, query_embedding: list[float], top_k: int = 5):
        """Recall from hot first, then cold."""
        # Get all memories for session
        hot_memories = [
            m for m in self._hot.values()
            if m["session_id"] == session_id
        ]

        # If hot has enough, use hot; else fallback to cold
        if len(hot_memories) < top_k:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute(
                "SELECT * FROM memories WHERE session_id = ?",
                (session_id,)
            )
            cold_memories = [
                dict(zip([d[0] for d in cursor.description], row))
                for row in cursor.fetchall()
            ]
            conn.close()
            all_memories = hot_memories + cold_memories
        else:
            all_memories = hot_memories

        # Vector similarity search
        return self._vector_search(all_memories, query_embedding, top_k)
```

### 用户事实存储

```python
# app/services/user_fact_store.py
class UserFactStore:
    """Global user fact store (shared across all projects)."""

    def __init__(self, db_path: str = "./data/memory.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                fact_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                fact_type TEXT NOT NULL,
                fact_content TEXT NOT NULL,
                embedding BLOB,
                confidence REAL NOT NULL,
                source_project_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_fact
            ON user_facts(user_id, fact_type, fact_content)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON user_facts(user_id)
        """)
        conn.commit()
        conn.close()

    def store(self, fact: UserFact) -> str:
        """Store or update a user fact."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            INSERT INTO user_facts (fact_id, user_id, fact_type, fact_content,
                embedding, confidence, source_project_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, fact_type, fact_content) DO UPDATE SET
                confidence = excluded.confidence,
                embedding = excluded.embedding,
                updated_at = excluded.updated_at,
                source_project_id = excluded.source_project_id
        """, (...))
        conn.commit()
        conn.close()
        return fact.fact_id

    def recall(self, user_id: str, fact_type: str | None = None,
               query_embedding: list[float] | None = None, top_k: int = 10):
        """Recall user facts. If query_embedding provided, do semantic search."""
        conn = sqlite3.connect(self._db_path)
        sql = "SELECT * FROM user_facts WHERE user_id = ?"
        params = [user_id]
        if fact_type:
            sql += " AND fact_type = ?"
            params.append(fact_type)

        cursor = conn.execute(sql, params)
        facts = [dict(zip([d[0] for d in cursor.description], row))
                 for row in cursor.fetchall()]
        conn.close()

        if query_embedding and facts:
            return self._vector_search(facts, query_embedding, top_k)

        # Sort by confidence desc
        facts.sort(key=lambda f: f["confidence"], reverse=True)
        return facts[:top_k]
```

### 向量索引

```python
# app/services/vector_index.py
import numpy as np

class VectorIndex:
    """In-memory vector index for semantic search."""

    def search(self, entries: list[dict], query_embedding: list[float], top_k: int = 5):
        if not entries:
            return []

        query = np.array(query_embedding)
        embeddings = []
        valid_entries = []

        for entry in entries:
            emb = entry.get("embedding")
            if emb:
                embeddings.append(emb)
                valid_entries.append(entry)

        if not embeddings:
            return []

        embeddings = np.array(embeddings)
        similarities = np.dot(embeddings, query) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query)
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [
            {**valid_entries[i], "score": float(similarities[i])}
            for i in top_indices
        ]
```

### 约束条件

- [ ] 记忆按 `session_id` 隔离，用户事实全局共享
- [ ] 热数据 TTL 7 天，超期自动归档到冷存储
- [ ] Embedding 必须通过 LLM Gateway（禁止本地加载 embedding 模型）
- [ ] SQLite 数据库文件持久化到 `./data/` 目录
- [ ] 错误响应统一格式：`{"error": "ErrorCode", "message": "..."}`
- [ ] `recall_memory` 优先热存储，热数据不足时自动查冷存储

---

## 5. 依赖与阻塞

| 依赖项                 | 状态      | 说明                               |
| ---------------------- | --------- | ---------------------------------- |
| FastAPI + Uvicorn      | ✅ 已完成 | 框架就绪                           |
| LLM Gateway (TASK-401) | ✅ 已完成 | Embedding 接口                     |
| SQLite                 | ✅ 已完成 | Python 内置                        |
| Redis                  | ⚠️ 降级   | 当前用内存 Dict，后续迁移 Redis    |
| PostgreSQL             | ⚠️ 降级   | 当前用 SQLite，后续迁移 PostgreSQL |
| numpy                  | ✅ 已完成 | 向量计算                           |
| httpx                  | ✅ 已完成 | 异步 HTTP 客户端                   |

---

## 6. 风险与应对

| 风险                           | 影响 | 应对策略                                     |
| ------------------------------ | ---- | -------------------------------------------- |
| SQLite 并发写入锁              | 中   | 使用连接池 + WAL 模式，或加线程锁            |
| 向量索引内存膨胀               | 中   | 限制单个 session 最大记忆数（1000 条）       |
| Embedding 调用超时             | 中   | 异步调用 + 超时回退（返回最近 N 条）         |
| 用户事实冲突（同一事实不同值） | 低   | 取 confidence 最高的事实，记录来源项目       |
| 跨项目隐私泄露                 | 低   | 事实按 confidence 分级，敏感事实可选项目隔离 |

---

## 7. Prompt

```markdown
【Situation】
AI 中台需要统一的记忆服务（端口 9003），支持对话记忆和用户画像。
已有 LLM Gateway（端口 9001）提供 Embedding 能力。

【Task】
实现 service-memory，提供记忆存储/召回、用户事实存储/召回。

【Action】

1. 创建项目结构 `services/service-memory/`
2. 实现 SQLite 数据库初始化（memories + user_facts 表）
3. 实现 MemoryStore（热内存 + 冷 SQLite，session 隔离）
4. 实现 UserFactStore（SQLite，全局共享）
5. 实现 VectorIndex（内存 cosine similarity）
6. 实现 EmbeddingClient（调用 LLM Gateway:9001）
7. 实现路由：
   - POST /v1/store_memory
   - POST /v1/recall_memory
   - POST /v1/store_user_fact
   - POST /v1/recall_user_facts
8. 实现健康检查 GET /health
9. 编写测试（含跨项目共享测试）

【Constraint】

- 热数据内存存储（7 天 TTL），冷数据 SQLite
- Embedding 必须通过 LLM Gateway
- 用户事实跨项目共享
- pytest 覆盖率 ≥50%

【Verification】

- pytest tests/ -v --cov=app --cov-fail-under=50
- curl -H "Content-Type: application/json" -d '{"session_id":"s1","user_id":"u1","content":"hello"}' http://localhost:9003/v1/store_memory
- curl -H "Content-Type: application/json" -d '{"session_id":"s1","query":"hello","top_k":3}' http://localhost:9003/v1/recall_memory
- curl -H "Content-Type: application/json" -d '{"user_id":"u1","fact_type":"constraint","fact_content":"芒果过敏","source_project_id":"proj_001"}' http://localhost:9003/v1/store_user_fact
- curl -H "Content-Type: application/json" -d '{"user_id":"u1","query":"水果推荐"}' http://localhost:9003/v1/recall_user_facts
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
