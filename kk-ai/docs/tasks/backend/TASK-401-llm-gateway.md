# TASK-401：LLM Gateway（service-llm）

## 元信息

| 字段     | 值                                |
| -------- | --------------------------------- |
| TASK ID  | TASK-401                          |
| 标题     | LLM Gateway - 豆包 ARK 接入服务   |
| 负责人   | @backend-lead                     |
| 优先级   | P0                                |
| 预估工时 | 6h                                |
| 关联需求 | TASK-400 Gateway 路由转发下游服务 |

---

## 1. 背景

AI 中台需要接入大语言模型能力，豆包 ARK（Doubao ARK）是字节跳动提供的 LLM 推理平台。需要构建一个独立的 LLM Gateway 服务（端口 9001），向上通过 MCP HUB Gateway（端口 8000）暴露，向下对接豆包 ARK OpenAI-compatible API。

---

## 2. 目标

实现 `service-llm` 服务，作为 AI 中台的统一 LLM 能力层：

- **对话能力**：支持流式/非流式 chat completion，多模型切换
- **向量能力**：支持文本 embedding
- **模型管理**：动态模型列表，配置外置 YAML
- **流式输出**：SSE（Server-Sent Events）实时返回
- **稳定性**：接口级熔断 + 重试，保障下游不可用时不雪崩

---

## 3. 验收标准

### AC-1：Chat Completion 接口

- [ ] `POST /v1/chat/completions` 支持非流式对话（`stream=false`）
- [ ] 同上接口支持 SSE 流式对话（`stream=true`，返回 `text/event-stream`）
- [ ] `model` 参数选择对应豆包模型（如 `doubao-lite-4k`、`doubao-pro-128k`）
- [ ] 请求体兼容 OpenAI 格式：`messages`、`model`、`temperature`、`max_tokens`、`stream`
- [ ] 响应体兼容 OpenAI 格式：`id`、`object`、`created`、`model`、`choices`

### AC-2：Embedding 接口

- [ ] `POST /v1/embeddings` 支持文本向量化
- [ ] 请求体：`input`、`model`
- [ ] 响应体：`object`、`data`、`model`、`usage`

### AC-3：模型列表接口

- [ ] `GET /v1/models` 返回可用模型列表
- [ ] 包含豆包 ARK 官方模型 + Custom Doubao 1.5 Endpoint
- [ ] 响应格式兼容 OpenAI：`object: "list"`、`data: [{id, object, created}]`

### AC-4：SSE 流式输出

- [ ] 流式响应用 `StreamingResponse` + `text/event-stream`
- [ ] 每行格式：`data: {JSON}\n\n`
- [ ] 结束标记：`data: [DONE]\n\n`
- [ ] 支持客户端中断（`Request.is_disconnected` 检测）

### AC-5：模型配置外置 YAML + 热加载

- [ ] 配置文件：`config/models.yaml`
- [ ] 包含：模型 ID、豆包 endpoint ID、上下文长度、温度范围、定价等
- [ ] 支持热加载（文件修改后自动生效，不重启服务）
- [ ] 加载失败时保持上一次有效配置，打印 warning

### AC-6：熔断与重试机制

- [ ] 对豆包 ARK 请求实现 3 次指数退避重试（1s → 2s → 4s）
- [ ] 连续失败 5 次触发熔断，30s 后半开探测
- [ ] 熔断期间返回 503，`{"error": "CIRCUIT_OPEN", "message": "LLM service temporarily unavailable"}`
- [ ] 使用 `httpx.AsyncClient` + 自定义重试/熔断装饰器

### AC-7：错误处理

- [ ] 豆包返回 429 → 透传 429，加 `Retry-After` Header
- [ ] 豆包返回 500 → 重试 3 次后返回 502
- [ ] 豆包返回 401/403 → 透传，记录 error 日志
- [ ] 网络超时（10s）→ 重试后返回 504

### AC-8：健康检查与监控

- [ ] `GET /health` 返回服务状态、各模型可用性、熔断器状态
- [ ] 暴露 Prometheus metrics（可选）：请求数、延迟、错误率、熔断状态

### AC-9：测试与质量

- [ ] `pytest` 全部通过，覆盖率 ≥ 50%
- [ ] 至少 2 个流式输出测试（mock SSE 事件流）
- [ ] 至少 2 个熔断/重试测试（mock 失败场景）
- [ ] 至少 1 个配置热加载测试

---

## 4. 技术方案

### 项目结构

```
services/service-llm/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic Settings + YAML 加载
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py          # ChatCompletion 请求/响应 Pydantic 模型
│   │   ├── embedding.py     # Embedding 请求/响应 Pydantic 模型
│   │   └── models.py        # Model 列表响应模型
│   ├── router/
│   │   ├── __init__.py
│   │   ├── chat.py          # /v1/chat/completions
│   │   ├── embedding.py     # /v1/embeddings
│   │   └── models.py        # /v1/models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ark_client.py    # 豆包 ARK HTTP 客户端
│   │   ├── circuit_breaker.py # 熔断器实现
│   │   └── model_manager.py # 模型配置管理（YAML 热加载）
│   └── middleware/
│       └── logger.py        # 结构化日志
├── config/
│   └── models.yaml          # 模型配置文件
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_chat.py
│   ├── test_embedding.py
│   ├── test_models.py
│   └── test_circuit_breaker.py
├── pyproject.toml
├── run.py
└── .env.example
```

### 模型配置 YAML 示例

```yaml
# config/models.yaml
models:
  - id: "doubao-lite-4k"
    name: "Doubao Lite 4K"
    provider: "doubao"
    endpoint_id: "ep-xxxxxxxxxxxxxxx" # 豆包 ARK Endpoint ID
    context_length: 4096
    temperature_range: [0.0, 1.0]
    max_tokens: 4096
    pricing:
      input_per_1k: 0.0008
      output_per_1k: 0.002
    supports_streaming: true
    supports_embedding: false

  - id: "doubao-pro-128k"
    name: "Doubao Pro 128K"
    provider: "doubao"
    endpoint_id: "ep-yyyyyyyyyyyyyyy"
    context_length: 128000
    temperature_range: [0.0, 1.0]
    max_tokens: 128000
    pricing:
      input_per_1k: 0.005
      output_per_1k: 0.015
    supports_streaming: true
    supports_embedding: false

  - id: "doubao-embedding"
    name: "Doubao Embedding"
    provider: "doubao"
    endpoint_id: "ep-zzzzzzzzzzzzzzz"
    context_length: 8192
    pricing:
      input_per_1k: 0.0001
    supports_streaming: false
    supports_embedding: true

default_chat_model: "doubao-lite-4k"
default_embedding_model: "doubao-embedding"
```

### 豆包 ARK API 调用

```python
# app/services/ark_client.py
import httpx

class ArkClient:
    """豆包 ARK API 客户端。"""

    def __init__(self, api_key: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat_completion(self, model: str, messages: list, stream: bool = False, **kwargs):
        """调用豆包 chat completion API。"""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs,
        }
        if stream:
            return await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Accept": "text/event-stream"},
            )
        return await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
        )

    async def embeddings(self, model: str, input_text: str | list[str]):
        """调用豆包 embedding API。"""
        payload = {"model": model, "input": input_text}
        return await self.client.post(
            f"{self.base_url}/embeddings",
            json=payload,
        )
```

### 熔断器实现

```python
# app/services/circuit_breaker.py
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开探测

class CircuitBreaker:
    """简单熔断器实现。"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    def call(self, func):
        """装饰器：包装异步函数，实现熔断逻辑。"""
        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError("LLM service temporarily unavailable")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as exc:
                self._on_failure()
                raise

        return wrapper

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### SSE 流式输出

```python
# app/router/chat.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completion(request: Request, body: ChatCompletionRequest):
    model_manager = get_model_manager()
    model_config = model_manager.get_model(body.model)

    if not model_config:
        raise HTTPException(status_code=404, detail=f"Model '{body.model}' not found")

    ark_client = get_ark_client()

    if body.stream:
        async def event_stream():
            response = await ark_client.chat_completion(
                model=model_config.endpoint_id,
                messages=[m.model_dump() for m in body.messages],
                stream=True,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield f"{line}\n\n"
                if await request.is_disconnected():
                    break
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
        )

    # Non-streaming
    response = await ark_client.chat_completion(
        model=model_config.endpoint_id,
        messages=[m.model_dump() for m in body.messages],
        stream=False,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )
    return response.json()
```

### 约束条件

- [ ] 使用 `httpx.AsyncClient` 进行所有外部 HTTP 调用，禁止同步 `requests`
- [ ] 所有模型配置变更必须通过 YAML 文件，禁止硬编码模型信息
- [ ] 热加载使用 `watchdog` 或定时轮询（间隔 5s）
- [ ] 流式输出必须处理客户端断开连接，避免资源泄漏
- [ ] 错误响应统一格式：`{"error": "ErrorCode", "message": "..."}`
- [ ] 熔断器状态持久化到内存（当前进程），后续可扩展 Redis

---

## 5. 依赖与阻塞

| 依赖项            | 状态      | 说明                              |
| ----------------- | --------- | --------------------------------- |
| MCP HUB Gateway   | ✅ 已完成 | TASK-400，提供统一入口路由转发    |
| FastAPI + Uvicorn | ✅ 已完成 | 框架就绪                          |
| httpx             | ✅ 已完成 | 异步 HTTP 客户端                  |
| PyYAML            | ⚠️ 需安装 | 模型配置解析                      |
| watchdog（可选）  | ⚠️ 需安装 | YAML 热加载文件监控               |
| 豆包 ARK API Key  | ⬜ 需申请 | 实际对接需要字节跳动 ARK 平台账号 |

---

## 6. 风险与应对

| 风险                          | 影响 | 应对策略                                                       |
| ----------------------------- | ---- | -------------------------------------------------------------- |
| 豆包 API 变更导致不兼容       | 高   | 响应模型用 Pydantic 校验，变更时快速适配                       |
| SSE 连接过多导致内存泄漏      | 中   | 客户端断开检测 + 连接超时自动清理                              |
| YAML 配置语法错误导致服务崩溃 | 中   | 加载失败时保持旧配置，打印错误日志                             |
| 豆包 429 限流影响用户体验     | 中   | 指数退避重试 + 透传 Retry-After                                |
| 模型 endpoint_id 泄露         | 低   | 对外暴露 model ID（如 doubao-lite-4k），内部映射到 endpoint_id |

---

## 7. Prompt

```markdown
【Situation】
AI 中台需要接入豆包 ARK LLM 能力，作为下游服务（端口 9001）。
上游通过 MCP HUB Gateway（端口 8000）转发请求。

【Task】
实现 service-llm，提供 Chat Completion、Embedding、模型列表接口。

【Action】

1. 创建项目结构 `services/service-llm/`
2. 实现 `config/models.yaml` 模型配置
3. 实现 `ModelManager`（YAML 加载 + 热加载）
4. 实现 `ArkClient`（httpx 异步调用豆包 API）
5. 实现 `CircuitBreaker`（熔断 + 重试）
6. 实现路由：
   - POST /v1/chat/completions（流式 + 非流式）
   - POST /v1/embeddings
   - GET /v1/models
7. 实现 SSE 流式输出（StreamingResponse）
8. 实现健康检查 GET /health
9. 编写测试（mock 豆包响应）

【Constraint】

- 兼容 OpenAI API 格式
- 模型配置外置 YAML，支持热加载
- 熔断 + 指数退避重试
- httpx 异步调用
- pytest 覆盖率 ≥50%

【Verification】

- pytest tests/ -v --cov=app --cov-fail-under=50
- curl -H "Content-Type: application/json" -d '{"model":"doubao-lite-4k","messages":[{"role":"user","content":"hello"}]}' http://localhost:9001/v1/chat/completions
- curl http://localhost:9001/v1/models
- curl http://localhost:9001/health
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
