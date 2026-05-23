# TASK-301：模型测试 API（SSE 流式响应）

## 元信息

| 字段     | 值                                    |
| -------- | ------------------------------------- |
| TASK ID  | TASK-301                              |
| 标题     | 实现模型测试 API（SSE 流式）          |
| 优先级   | P1                                    |
| 预估工时 | 3h                                    |
| 关联需求 | TASK-101 前端模型管理页面的"测试"功能 |

---

## 2. 目标

实现 `POST /models/{model_id}/test` 接口，接收 prompt，转发到下游模型服务，以 SSE 流式返回响应。

---

## 3. 验收标准

- [ ] AC-1：接收 JSON body `{ "prompt": "xxx" }`
- [ ] AC-2：根据 model_id 路由到对应的下游服务
- [ ] AC-3：使用 SSE（text/event-stream）流式返回模型响应
- [ ] AC-4：下游服务断开时优雅结束 SSE
- [ ] AC-5：支持超时（30s）
- [ ] AC-6：`pytest` 通过

---

## 4. 技术方案

### 接口定义

```python
# POST /models/{model_id}/test
# Content-Type: application/json
# X-API-Key: xxx

# Request Body
{ "prompt": "你好，请介绍自己" }

# Response: text/event-stream
# data: {"chunk": "你"}
# data: {"chunk": "好"}
# data: {"chunk": "！"}
# data: {"done": true}
```

### 核心实现

```python
from fastapi.responses import StreamingResponse
import httpx

async def test_model(model_id: str, prompt: str):
    target = resolve_model_target(model_id)

    async def stream_response():
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", target, json={"prompt": prompt}) as resp:
                async for chunk in resp.aiter_text():
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
    )
```

### 约束条件

- [ ] 使用 `httpx.AsyncClient` 的 `stream` 方法
- [ ] 超时 30 秒
- [ ] 错误时返回非 SSE 的标准错误响应
- [ ] 记录 trace_id 和 latency

---

## 7. Prompt

```markdown
【Situation】
FastAPI Gateway 已有动态路由转发能力（app/router/proxy.py）。
需要新增 SSE 流式接口用于模型测试。

【Task】
实现 POST /models/{model_id}/test SSE 流式接口。

【Action】

1. 在 app/router/proxy.py 或新建 app/router/models.py 中添加路由
2. 接收 prompt，通过 resolve_target 找到下游模型服务
3. 使用 httpx stream 转发请求
4. 以 SSE 格式流式返回响应
5. 处理超时和断开

【Constraint】

- 使用 StreamingResponse
- httpx stream + aiter_text
- 超时 30s
- 错误返回标准 JSON 错误（非 SSE）

【Verification】

- pytest
- curl -N -H "Accept: text/event-stream" -X POST http://localhost:8000/models/mcp-a/test
```
