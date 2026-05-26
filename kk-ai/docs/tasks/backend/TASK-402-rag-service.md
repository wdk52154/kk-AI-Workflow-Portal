# TASK-402：RAG Service（service-rag）

## 元信息

| 字段     | 值                                         |
| -------- | ------------------------------------------ |
| TASK ID  | TASK-402                                   |
| 标题     | RAG Service - 向量检索与知识库服务         |
| 负责人   | @backend-lead                              |
| 优先级   | P0                                         |
| 预估工时 | 8h                                         |
| 关联需求 | TASK-401 LLM Gateway（Embedding + Rerank） |

---

## 1. 背景

AI 中台需要 RAG（Retrieval-Augmented Generation）能力，支撑知识库问答场景。用户上传文档后，系统自动分块、向量化存储到 ChromaDB，检索时根据 query 向量匹配最相关的文档片段，供 LLM 生成回答。

---

## 2. 目标

实现 `service-rag` 服务（端口 9002），提供完整的文档摄入 → 向量存储 → 语义检索 → 重排序链路：

- **文档摄入**：支持 txt/pdf/md，自动分块 + Embedding
- **知识检索**：向量相似度检索，返回 Top-K 结果
- **多租户隔离**：按 `project_id` 隔离，每个项目独立 Chroma Collection
- **元数据过滤**：按 source_type、date_range、tags 过滤
- **重排序**：接入 LLM Gateway 做 Rerank，提升检索质量

---

## 3. 验收标准

### AC-1：文档摄入接口

- [ ] `POST /v1/ingest_document` 支持上传文件（multipart/form-data）
- [ ] 支持格式：`.txt`、`.pdf`、`.md`
- [ ] 自动分块策略：
  - 按 token 数分块（默认 chunk_size=512, overlap=50）
  - 使用 `tiktoken` 计算 token 数
  - 支持按段落/标题智能切分（Markdown 按 `#` 标题切分）
- [ ] 每个 chunk 自动调用 LLM Gateway（`POST /v1/embeddings`）获取向量
- [ ] 存储到 ChromaDB，携带元数据：`project_id`、`source_type`、`filename`、`chunk_index`、`tags`、`created_at`
- [ ] 摄入完成后返回：`document_id`、`chunk_count`、`status`

### AC-2：知识检索接口

- [ ] `POST /v1/search_knowledge` 接收 `query` + `top_k`（默认 5）
- [ ] 先对 query 做 Embedding（调用 LLM Gateway）
- [ ] ChromaDB 向量相似度检索，返回 Top-K chunks
- [ ] 支持元数据过滤：`source_type`、`date_range`（start/end ISO 格式）、`tags`
- [ ] 检索结果格式：
  ```json
  {
    "results": [
      {
        "content": "...",
        "score": 0.92,
        "metadata": {
          "source_type": "pdf",
          "filename": "product_manual.pdf",
          "chunk_index": 3,
          "tags": ["产品", "说明书"]
        }
      }
    ]
  }
  ```

### AC-3：多租户隔离

- [ ] 每个 `project_id` 对应独立的 Chroma Collection：`rag_{project_id}`
- [ ] Collection 不存在时自动创建
- [ ] 检索时严格限定在请求对应的 project collection
- [ ] 错误场景：缺少 `X-Project-Id` Header 时返回 400

### AC-4：重排序（Rerank）

- [ ] 检索后可选启用 Rerank（`rerank=true` 参数）
- [ ] 调用 LLM Gateway 的 chat completion 接口做重排序
- [ ] Prompt 模板：给定 query 和候选文档列表，让 LLM 按相关性打分并排序
- [ ] Rerank 后返回重新排序的结果（保留原始向量分数作为参考）

### AC-5：文档管理

- [ ] `GET /v1/documents` 列出项目下的所有文档
- [ ] `DELETE /v1/documents/{document_id}` 删除文档及其所有 chunks
- [ ] `GET /v1/documents/{document_id}/chunks` 查看文档的分块详情

### AC-6：健康检查与监控

- [ ] `GET /health` 返回服务状态、ChromaDB 连接状态、已加载 Collection 数量
- [ ] 暴露 Prometheus metrics（可选）：摄入文档数、检索次数、平均延迟

### AC-7：测试与质量

- [ ] `pytest` 全部通过，覆盖率 ≥ 50%
- [ ] 至少 2 个摄入测试（txt + pdf）
- [ ] 至少 2 个检索测试（纯向量 + 带元数据过滤）
- [ ] 至少 1 个多租户隔离测试（project A 的数据 project B 查不到）
- [ ] 至少 1 个删除文档测试

---

## 4. 技术方案

### 项目结构

```
services/service-rag/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ingest.py        # 文档摄入请求/响应模型
│   │   ├── search.py        # 检索请求/响应模型
│   │   └── document.py      # 文档管理模型
│   ├── router/
│   │   ├── __init__.py
│   │   ├── ingest.py        # /v1/ingest_document
│   │   ├── search.py        # /v1/search_knowledge
│   │   └── documents.py     # /v1/documents CRUD
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chroma_store.py  # ChromaDB 封装
│   │   ├── document_parser.py # 文档解析器（txt/pdf/md）
│   │   ├── text_splitter.py   # 文本分块
│   │   ├── embedding_client.py # LLM Gateway Embedding 客户端
│   │   └── reranker.py      # 重排序服务
│   └── middleware/
│       └── project_auth.py  # X-Project-Id 校验
├── chroma_data/             # ChromaDB 持久化数据
├── tests/
│   ├── fixtures/            # 测试文档样本
│   │   ├── sample.txt
│   │   └── sample.md
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_ingest.py
│   ├── test_search.py
│   ├── test_documents.py
│   └── test_tenant.py
├── pyproject.toml
├── run.py
└── .env.example
```

### ChromaDB 封装

```python
# app/services/chroma_store.py
import chromadb
from chromadb.config import Settings as ChromaSettings

class ChromaStore:
    """Multi-tenant ChromaDB vector store."""

    def __init__(self, persist_dir: str = "./chroma_data"):
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=persist_dir,
                anonymized_telemetry=False,
            )
        )

    def _collection_name(self, project_id: str) -> str:
        return f"rag_{project_id}"

    def get_or_create_collection(self, project_id: str):
        """Get or create a project-specific collection."""
        name = self._collection_name(project_id)
        return self.client.get_or_create_collection(name)

    def add_chunks(self, project_id: str, chunks: list[Chunk]) -> list[str]:
        """Add document chunks to the project's collection."""
        collection = self.get_or_create_collection(project_id)
        ids = [c.id for c in chunks]
        texts = [c.text for c in chunks]
        embeddings = [c.embedding for c in chunks]
        metadatas = [c.metadata for c in chunks]
        collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        return ids

    def search(self, project_id: str, query_embedding: list[float], top_k: int = 5, filters: dict | None = None):
        """Search chunks in the project's collection."""
        collection = self.get_or_create_collection(project_id)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,
        )
        return results
```

### 文档解析器

```python
# app/services/document_parser.py
import io
from pathlib import Path

class DocumentParser:
    """Parse txt/pdf/md documents into raw text."""

    def parse(self, file: UploadFile) -> str:
        suffix = Path(file.filename).suffix.lower()
        content = file.file.read()

        if suffix == ".txt":
            return content.decode("utf-8")
        elif suffix == ".md":
            return content.decode("utf-8")
        elif suffix == ".pdf":
            return self._parse_pdf(content)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _parse_pdf(self, content: bytes) -> str:
        """Parse PDF using PyPDF2 or pdfplumber."""
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
```

### 文本分块

```python
# app/services/text_splitter.py
import tiktoken

class TokenTextSplitter:
    """Split text into chunks by token count."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50, model: str = "cl100k_base"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoder = tiktoken.get_encoding(model)

    def split(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        tokens = self.encoder.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def split_markdown(self, text: str) -> list[str]:
        """Split markdown by headers (# ## ###)."""
        import re
        sections = re.split(r'\n(?=#+\s)', text)
        return [s.strip() for s in sections if s.strip()]
```

### Embedding 客户端

```python
# app/services/embedding_client.py
import httpx

class EmbeddingClient:
    """Client for LLM Gateway Embedding API."""

    def __init__(self, base_url: str = "http://localhost:9001"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Get embeddings for a list of texts."""
        payload = {"input": texts}
        if model:
            payload["model"] = model

        response = await self.client.post(
            f"{self.base_url}/v1/embeddings",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
```

### 重排序服务

```python
# app/services/reranker.py
import json
import httpx

class Reranker:
    """Rerank search results using LLM Gateway."""

    RERANK_PROMPT = """Given the following query and candidate passages, rank them by relevance.
Query: {query}

Candidates:
{candidates}

Return a JSON array with the indices of candidates sorted by relevance (most relevant first):
[{{"index": 0, "score": 0.95}}, ...]"""

    def __init__(self, base_url: str = "http://localhost:9001"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def rerank(self, query: str, results: list[dict]) -> list[dict]:
        """Rerank results using LLM."""
        candidates = "\n\n".join(
            f"[{i}] {r['content'][:500]}" for i, r in enumerate(results)
        )
        prompt = self.RERANK_PROMPT.format(query=query, candidates=candidates)

        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": None,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
        )
        response.raise_for_status()
        # Parse LLM output and reorder results
        # ...
```

### 摄入接口设计

```python
# app/router/ingest.py
@router.post("/v1/ingest_document")
async def ingest_document(
    request: Request,
    file: UploadFile,
    source_type: str = Form("document"),
    tags: str = Form(""),  # comma-separated
):
    project_id = request.headers.get("X-Project-Id")
    if not project_id:
        raise HTTPException(status_code=400, detail="Missing X-Project-Id header")

    # 1. Parse document
    parser = DocumentParser()
    text = parser.parse(file)

    # 2. Split into chunks
    splitter = TokenTextSplitter()
    if file.filename.endswith(".md"):
        chunks = splitter.split_markdown(text)
    else:
        chunks = splitter.split(text)

    # 3. Get embeddings from LLM Gateway
    embedding_client = EmbeddingClient()
    embeddings = await embedding_client.embed(chunks)

    # 4. Store in ChromaDB
    chroma = ChromaStore()
    chunk_objects = [
        Chunk(
            id=f"{doc_id}_{i}",
            text=chunk,
            embedding=emb,
            metadata={
                "project_id": project_id,
                "source_type": source_type,
                "filename": file.filename,
                "chunk_index": i,
                "tags": tags.split(",") if tags else [],
                "created_at": datetime.now().isoformat(),
            },
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    chroma.add_chunks(project_id, chunk_objects)

    return {
        "document_id": doc_id,
        "filename": file.filename,
        "chunk_count": len(chunks),
        "status": "success",
    }
```

### 约束条件

- [ ] ChromaDB 数据持久化到 `./chroma_data`，不丢数据
- [ ] 每个 chunk 的 embedding 通过 LLM Gateway 获取，禁止本地加载 embedding 模型
- [ ] PDF 解析失败时回退到纯文本提取（保留原始字节供人工检查）
- [ ] 单文件最大 10MB，超过返回 413
- [ ] 单次摄入最多 1000 个 chunks，超过返回 413
- [ ] 检索时 `top_k` 最大 50，超过返回 400
- [ ] 元数据过滤使用 ChromaDB 的 `where` 语法

---

## 5. 依赖与阻塞

| 依赖项                 | 状态      | 说明                    |
| ---------------------- | --------- | ----------------------- |
| FastAPI + Uvicorn      | ✅ 已完成 | 框架就绪                |
| ChromaDB               | ⚠️ 需安装 | `chromadb>=0.5.0`       |
| tiktoken               | ⚠️ 需安装 | Token 计数              |
| PyPDF2 / pdfplumber    | ⚠️ 需安装 | PDF 解析                |
| LLM Gateway (TASK-401) | ✅ 已完成 | Embedding + Rerank 接口 |
| MCP HUB Gateway        | ✅ 已完成 | 统一入口路由转发        |
| httpx                  | ✅ 已完成 | 异步 HTTP 客户端        |

---

## 6. 风险与应对

| 风险                   | 影响 | 应对策略                                     |
| ---------------------- | ---- | -------------------------------------------- |
| ChromaDB 并发写入冲突  | 中   | Collection 级别加锁或单线程摄入队列          |
| 大 PDF 解析内存爆炸    | 中   | 限制文件大小 10MB，分页解析                  |
| Embedding 批量调用超时 | 中   | 分批调用（每批 100 个 chunks），超时重试     |
| project_id 碰撞        | 低   | Collection 命名 `rag_{project_id}`，严格校验 |
| 向量维度不匹配         | 低   | 初始化时固定维度（如 1024），不一致时报错    |

---

## 7. Prompt

```markdown
【Situation】
AI 中台需要 RAG 能力，已有 LLM Gateway（端口 9001）提供 Embedding 和 Chat。
需要构建 service-rag（端口 9002），实现文档摄入 → 分块 → 向量化 → 检索 → 重排序。

【Task】
实现 RAG Service，支持 txt/pdf/md 摄入、ChromaDB 向量检索、多租户隔离。

【Action】

1. 创建项目结构 `services/service-rag/`
2. 实现 `ChromaStore`（多租户 Collection 管理）
3. 实现 `DocumentParser`（txt/pdf/md）
4. 实现 `TokenTextSplitter`（按 token 分块 + Markdown 标题切分）
5. 实现 `EmbeddingClient`（调用 LLM Gateway:9001 /v1/embeddings）
6. 实现 `Reranker`（调用 LLM Gateway:9001 /v1/chat/completions）
7. 实现路由：
   - POST /v1/ingest_document
   - POST /v1/search_knowledge
   - GET /v1/documents
   - DELETE /v1/documents/{id}
   - GET /v1/documents/{id}/chunks
8. 实现 `X-Project-Id` 中间件校验
9. 编写测试（mock Embedding 和 ChromaDB）

【Constraint】

- 向量存储用 ChromaDB，持久化到本地
- Embedding 必须通过 LLM Gateway（禁止本地模型）
- 严格 project_id 隔离
- pytest 覆盖率 ≥50%

【Verification】

- pytest tests/ -v --cov=app --cov-fail-under=50
- curl -F "file=@sample.txt" -H "X-Project-Id: proj_001" http://localhost:9002/v1/ingest_document
- curl -H "X-Project-Id: proj_001" -H "Content-Type: application/json" -d '{"query":"hello","top_k":3}' http://localhost:9002/v1/search_knowledge
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
