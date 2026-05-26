# TASK-405：AI 数据中心（service-data）

## 元信息

| 字段     | 值                                           |
| -------- | -------------------------------------------- |
| TASK ID  | TASK-405                                     |
| 标题     | AI 数据中心 - ETL Pipeline + 数据产品        |
| 负责人   | @backend-lead                                |
| 优先级   | P1                                           |
| 预估工时 | 10h                                          |
| 关联需求 | TASK-402 RAG Service、TASK-404 Prompt Center |

---

## 1. 背景

AI 中台的核心价值之一是数据飞轮：业务产生数据 → 数据训练模型 → 模型提升业务 → 产生更多数据。当前各业务线的数据散落在不同系统中（微信、客服、销售、学员），缺乏统一的数据中心来：

1. **标准化摄入**：统一接收多源异构数据
2. **智能清洗**：去重、脱敏、质量评分
3. **人工标注**：运营团队打标签，持续优化模型
4. **产品化沉淀**：将清洗后的数据转化为可直接使用的产品（话术库、异议库、画像库）

---

## 2. 目标

实现 `service-data` 服务，作为 AI 中台的统一数据中心：

- **ETL Pipeline**：多源数据摄入 → 清洗 → 标注 → 沉淀
- **数据产品**：话术库、异议库、用户画像库
- **数据看板**：统计指标、质量监控
- **开放查询**：支持业务方查询和导出清洗后的数据

---

## 3. 验收标准

### AC-1：数据摄入

- [ ] `POST /v1/data/ingest` 支持多种数据源类型：`wechat`、`customer_service`、`sales_call`、`student_survey`
- [ ] 请求体：
  ```json
  {
    "source_type": "wechat",
    "project_id": "proj_001",
    "records": [
      {
        "raw_id": "wx_msg_001",
        "content": "用户咨询内容...",
        "metadata": {
          "user_id": "u001",
          "timestamp": "2026-05-26T10:00:00Z",
          "channel": "wechat"
        }
      }
    ]
  }
  ```
- [ ] 单批次最多 1000 条记录，超过返回 413
- [ ] 摄入后返回：`batch_id`、`record_count`、`status`

### AC-2：数据清洗

- [ ] 自动清洗流程（摄入后异步执行）：
  - **去重**：基于 `raw_id + content_hash`，重复数据标记 `status=duplicated`
  - **脱敏**：正则匹配手机号、身份证号、邮箱，替换为 `[PHONE]`、`[ID]`、`[EMAIL]`
  - **格式标准化**：统一编码 UTF-8，去除不可见字符，统一换行符
  - **质量评分**：调用 LLM Gateway 评估数据质量（完整性、相关性、可读性），分数 0-100
- [ ] 清洗结果写入 `cleaned_data` 表，保留原始数据在 `raw_data` 表
- [ ] 清洗失败的记录标记 `status=failed`，记录失败原因

### AC-3：人工标注

- [ ] `POST /v1/data/{record_id}/annotate` 支持人工标注
- [ ] 标注字段：
  - `intent`：意图标签（如 `咨询`、`投诉`、`购买意向`）
  - `emotion`：情绪标签（如 ` positive`、`neutral`、`negative`）
  - `quality_score`：人工质量评分（1-5）
  - `tags`：自定义标签数组（如 `高意向`、`价格敏感`）
  - `notes`：标注备注
- [ ] `GET /v1/data/pending_annotation` 返回待标注数据列表（按质量评分低优先）
- [ ] `GET /v1/data/annotation_stats` 返回标注统计（已标注/待标注/各标签分布）

### AC-4：数据产品 - Top Sales 话术库

- [ ] `GET /v1/products/sales_scripts` 返回高转化话术列表
- [ ] 筛选条件：`project_id`、`min_conversion_rate`、`tags`
- [ ] 话术来源：标注为 `高转化` 的销售对话记录
- [ ] 返回格式：
  ```json
  {
    "scripts": [
      {
        "script_id": "...",
        "content": "...",
        "conversion_rate": 0.85,
        "usage_count": 120,
        "tags": ["开场", "高转化"],
        "source_project_id": "proj_001"
      }
    ]
  }
  ```

### AC-5：数据产品 - 异议库

- [ ] `GET /v1/products/objections` 返回客户异议与标准应答
- [ ] 筛选条件：`project_id`、`objection_type`、`tags`
- [ ] 异议来源：标注为 `客户异议` 的对话记录
- [ ] 返回格式：
  ```json
  {
    "objections": [
      {
        "objection_id": "...",
        "objection_text": "价格太贵了",
        "response_text": "理解您的顾虑，我们现在有优惠活动...",
        "objection_type": "price",
        "frequency": 350,
        "tags": ["价格", "常见异议"]
      }
    ]
  }
  ```

### AC-6：数据产品 - 用户画像库

- [ ] `GET /v1/products/user_profiles` 返回结构化用户标签
- [ ] 支持按 `user_id` 查询单个用户画像
- [ ] 画像字段：
  - `basic`：年龄、性别、地域（脱敏后）
  - `preferences`：偏好标签（从对话中提取）
  - `constraints`：约束标签（如预算、过敏史）
  - `value_score`：用户价值评分（0-100）
  - `interaction_count`：交互次数
  - `last_interaction`：最近交互时间
- [ ] 画像数据来源于 service-memory 的 user_facts（跨项目共享）

### AC-7：数据查询与导出

- [ ] `POST /v1/data/query` 支持复杂查询
- [ ] 查询条件：`source_type`、`project_id`、`date_range`、`intent`、`emotion`、`tags`、`min_quality_score`
- [ ] 返回分页结果，支持 `page` 和 `page_size`
- [ ] `POST /v1/data/export` 导出查询结果为 CSV/JSON
- [ ] 导出限制：单次最多 10000 条

### AC-8：数据看板

- [ ] `GET /v1/data/stats` 返回数据看板统计
- [ ] 统计指标：
  - `total_records`：总记录数
  - `records_by_source`：各数据源记录数
  - `records_by_project`：各项目记录数
  - `avg_quality_score`：平均质量分
  - `annotation_progress`：标注进度（已标注/总数）
  - `top_intents`：Top 10 意图分布
  - `top_emotions`：情绪分布
  - `data_growth`：最近 7 天数据增长趋势

### AC-9：数据向量化（RAG 集成）

- [ ] 清洗后的高质量数据（quality_score ≥ 70）自动调用 service-rag:9002 `/v1/ingest_document` 向量化
- [ ] 数据内容作为文档摄入，metadata 包含：`source_type`、`project_id`、`intent`、`tags`
- [ ] 支持通过 RAG 语义检索召回历史数据

### AC-10：测试与质量

- [ ] `pytest` 全部通过，覆盖率 ≥ 50%
- [ ] 至少 2 个数据摄入 + 清洗测试
- [ ] 至少 2 个数据查询测试（带过滤条件）
- [ ] 至少 1 个数据产品测试（话术库/异议库/画像库）
- [ ] 至少 1 个数据看板统计测试

---

## 4. 技术方案

### 项目结构

```
services/service-data/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── data_record.py   # 数据记录模型
│   │   ├── annotation.py    # 标注模型
│   │   └── data_products.py # 数据产品模型
│   ├── router/
│   │   ├── __init__.py
│   │   ├── ingest.py        # /v1/data/ingest
│   │   ├── query.py         # /v1/data/query, /v1/data/export
│   │   ├── annotate.py      # /v1/data/annotate
│   │   ├── products.py      # /v1/products/*
│   │   └── stats.py         # /v1/data/stats
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_store.py    # 数据存储服务（SQLite）
│   │   ├── etl_pipeline.py  # ETL 清洗管道
│   │   ├── annotator.py     # 标注服务
│   │   ├── data_products.py # 数据产品生成
│   │   └── rag_client.py    # service-rag 客户端
│   └── middleware/
│       └── logger.py
├── data/                    # SQLite 数据目录
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_ingest.py
│   ├── test_query.py
│   ├── test_products.py
│   └── test_stats.py
├── pyproject.toml
├── run.py
└── .env.example
```

### 数据库设计

```sql
-- raw_data: 原始摄入数据
CREATE TABLE raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_id TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- wechat, customer_service, sales_call, student_survey
    project_id TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    metadata TEXT,  -- JSON
    status TEXT DEFAULT 'pending',  -- pending, cleaned, duplicated, failed
    created_at TEXT NOT NULL,
    UNIQUE(raw_id, source_type)
);

-- cleaned_data: 清洗后的数据
CREATE TABLE cleaned_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_data_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    project_id TEXT NOT NULL,
    original_content TEXT NOT NULL,
    cleaned_content TEXT NOT NULL,
    quality_score INTEGER,  -- 0-100
    intent TEXT,
    emotion TEXT,
    tags TEXT,  -- JSON array
    is_annotated INTEGER DEFAULT 0,
    annotation_data TEXT,  -- JSON
    status TEXT DEFAULT 'available',  -- available, archived, vectorized
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (raw_data_id) REFERENCES raw_data(id)
);

-- data_batches: 摄入批次记录
CREATE TABLE data_batches (
    batch_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    project_id TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'processing',
    created_at TEXT NOT NULL
);
```

### ETL Pipeline

```python
# app/services/etl_pipeline.py
import hashlib
import json
import logging
import re
from datetime import datetime, timezone

from app.services.data_store import get_data_store

logger = logging.getLogger("service-data.etl")

# 脱敏规则
SENSITIVE_PATTERNS = [
    (r'\b1[3-9]\d{9}\b', '[PHONE]'),      # 手机号
    (r'\b\d{17}[\dXx]\b', '[ID]'),        # 身份证号
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),  # 邮箱
]

class ETLPipeline:
    """ETL pipeline: deduplicate, desensitize, normalize, quality score."""

    async def process_batch(self, batch_id: str) -> dict:
        """Process a batch of raw data."""
        store = get_data_store()
        raw_records = store.get_raw_by_batch(batch_id, status='pending')

        results = {'cleaned': 0, 'duplicated': 0, 'failed': 0}

        for record in raw_records:
            try:
                # Step 1: Deduplication
                content_hash = self._hash_content(record['content'])
                if store.is_duplicate(record['project_id'], content_hash):
                    store.update_raw_status(record['id'], 'duplicated')
                    results['duplicated'] += 1
                    continue

                # Step 2: Desensitization
                cleaned = self._desensitize(record['content'])

                # Step 3: Normalization
                cleaned = self._normalize(cleaned)

                # Step 4: Quality scoring (mock for now, call LLM Gateway in production)
                quality_score = self._mock_quality_score(cleaned)

                # Save cleaned data
                store.save_cleaned({
                    'raw_data_id': record['id'],
                    'source_type': record['source_type'],
                    'project_id': record['project_id'],
                    'original_content': record['content'],
                    'cleaned_content': cleaned,
                    'quality_score': quality_score,
                    'content_hash': content_hash,
                })
                store.update_raw_status(record['id'], 'cleaned')
                results['cleaned'] += 1

            except Exception as exc:
                logger.error("ETL failed for record %s: %s", record['id'], exc)
                store.update_raw_status(record['id'], 'failed', str(exc))
                results['failed'] += 1

        # Update batch status
        store.update_batch_status(batch_id, 'completed', results)

        # Auto-vectorize high-quality data
        await self._auto_vectorize(batch_id)

        return results

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

    def _desensitize(self, content: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            content = re.sub(pattern, replacement, content)
        return content

    def _normalize(self, content: str) -> str:
        # Remove invisible characters
        content = ''.join(c for c in content if c.isprintable() or c in '\n\t')
        # Normalize newlines
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # Strip extra whitespace
        lines = [line.strip() for line in content.split('\n')]
        return '\n'.join(line for line in lines if line)

    def _mock_quality_score(self, content: str) -> int:
        """Mock quality scoring. In production, call LLM Gateway."""
        score = 50
        if len(content) > 20:
            score += 20
        if len(content) > 50:
            score += 15
        if any(c in content for c in '。？！'):
            score += 10
        return min(100, score)

    async def _auto_vectorize(self, batch_id: str) -> None:
        """Auto-vectorize high-quality cleaned data."""
        # Implementation: call service-rag:9002 /v1/ingest_document
        pass
```

### 数据产品生成

```python
# app/services/data_products.py
class DataProductService:
    """Generate data products from cleaned and annotated data."""

    def get_sales_scripts(self, project_id: str | None = None,
                          min_conversion_rate: float = 0.0,
                          tags: list[str] | None = None) -> list[dict]:
        """Get Top Sales scripts."""
        store = get_data_store()
        filters = {'intent': '高转化', 'min_quality_score': 70}
        if project_id:
            filters['project_id'] = project_id
        if tags:
            filters['tags'] = tags
        return store.query_cleaned(**filters)

    def get_objections(self, project_id: str | None = None,
                       objection_type: str | None = None,
                       tags: list[str] | None = None) -> list[dict]:
        """Get objection-response pairs."""
        store = get_data_store()
        filters = {'intent': '客户异议'}
        if project_id:
            filters['project_id'] = project_id
        if objection_type:
            filters['objection_type'] = objection_type
        return store.query_cleaned(**filters)

    def get_user_profile(self, user_id: str) -> dict | None:
        """Get user profile from service-memory."""
        # Call service-memory:9003 /v1/recall_user_facts
        pass
```

### 约束条件

- [ ] 单批次摄入最多 1000 条，单条内容最大 10KB
- [ ] 脱敏必须覆盖手机号、身份证号、邮箱（正则匹配）
- [ ] 清洗后的数据保留原始数据，不可物理删除
- [ ] 数据产品只返回 `quality_score >= 70` 的数据
- [ ] 用户画像数据来源于 service-memory 的 `user_facts`，保持跨项目共享
- [ ] 数据导出限制单次 10000 条，防止内存溢出
- [ ] 所有时间戳使用 ISO 8601 格式，UTC 时区

---

## 5. 依赖与阻塞

| 依赖项                    | 状态      | 说明                 |
| ------------------------- | --------- | -------------------- |
| FastAPI + Uvicorn         | ✅ 已完成 | 框架就绪             |
| SQLite                    | ✅ 已完成 | Python 内置          |
| RAG Service (TASK-402)    | ✅ 已完成 | 数据向量化摄入       |
| Memory Service (TASK-403) | ✅ 已完成 | 用户画像数据源       |
| Prompt Center (TASK-404)  | ✅ 已完成 | 数据清洗 Prompt 模板 |
| LLM Gateway (TASK-401)    | ✅ 已完成 | 质量评分             |

---

## 6. 风险与应对

| 风险                           | 影响 | 应对策略                                    |
| ------------------------------ | ---- | ------------------------------------------- |
| 数据量过大导致 SQLite 性能瓶颈 | 高   | 分表存储（按月分表），或后续迁移 PostgreSQL |
| 脱敏规则遗漏敏感信息           | 高   | 正则 + 关键词库双层检测，人工抽检           |
| 数据质量评分不准确             | 中   | 人工标注反馈校准评分模型                    |
| 向量化调用频繁导致限流         | 中   | 批量向量化，夜间低峰期执行                  |
| 跨项目数据隐私争议             | 中   | 用户画像只共享脱敏后的标签，不共享原始内容  |

---

## 7. Prompt

```markdown
【Situation】
AI 中台需要统一的数据中心（service-data），接收多源数据、清洗、标注、沉淀为数据产品。
已有 RAG Service（9002）、Memory Service（9003）、Prompt Center（9004）。

【Task】
实现 service-data，提供 ETL Pipeline + 数据产品 + 数据看板。

【Action】

1. 创建项目结构 `services/service-data/`
2. 实现 SQLite 数据库（raw_data、cleaned_data、data_batches 表）
3. 实现 ETLPipeline（去重、脱敏、标准化、质量评分）
4. 实现数据摄入路由 `POST /v1/data/ingest`
5. 实现标注路由 `POST /v1/data/{id}/annotate`、`GET /v1/data/pending_annotation`
6. 实现数据产品路由：
   - `GET /v1/products/sales_scripts`
   - `GET /v1/products/objections`
   - `GET /v1/products/user_profiles`
7. 实现查询路由 `POST /v1/data/query`、`POST /v1/data/export`
8. 实现看板路由 `GET /v1/data/stats`
9. 实现 RAG 客户端（自动向量化高质量数据）
10. 编写测试

【Constraint】

- 单批次最多 1000 条
- 数据脱敏（手机号、身份证、邮箱）
- 数据产品只返回 quality_score >= 70
- pytest 覆盖率 ≥50%

【Verification】

- pytest tests/ -v --cov=app --cov-fail-under=50
- curl -H "Content-Type: application/json" -d '{"source_type":"wechat","project_id":"proj_001","records":[...]}' http://localhost:9005/v1/data/ingest
- curl http://localhost:9005/v1/data/stats
- curl http://localhost:9005/v1/products/sales_scripts
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
