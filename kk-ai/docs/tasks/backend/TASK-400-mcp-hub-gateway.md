# TASK-400：MCP HUB Gateway 核心网关

## 元信息

| 字段     | 值                                      |
| -------- | --------------------------------------- |
| TASK ID  | TASK-400                                |
| 标题     | MCP HUB Gateway 核心网关                |
| 负责人   | @backend-lead                           |
| 优先级   | P0                                      |
| 预估工时 | 8h                                      |
| 关联需求 | 项目 7 核心入口，所有下游服务的统一网关 |

---

## 1. 背景

AI 中台需要统一的 HTTP Gateway 作为所有外部请求的唯一入口。Gateway 负责鉴权、限流、配额校验、请求路由和全链路日志，下游服务（9001-9004 及后续）无需关心认证和流控逻辑。

---

## 2. 目标

实现完整的 `mcp-hub` Gateway 服务，包含以下 5 层中间件链：

```
Request → Auth(①) → RateLimit(②) → Quota(③) → Router(④) → Logger(⑤) → Response
```

- **Auth(①)**：X-API-Key 鉴权，支持多项目 Key 管理，按 `project_id` 隔离
- **RateLimit(②)**：基于 Redis 的滑动窗口限流，按 `project_id + endpoint` 维度
- **Quota(③)**：按项目配额管理，每日/每月调用上限（TASK-102 已有基础，需增强）
- **Router(④)**：动态路由表，将请求转发到下游服务（9001-9004 及后续服务）
- **Logger(⑤)**：结构化 JSON 日志，记录 `trace_id`、`project_id`、`latency`、`status`

---

## 3. 验收标准

### AC-1：Auth 中间件

- [ ] 从 Header `X-API-Key` 读取 API Key
- [ ] 支持多项目 Key 管理（`app/services/api_key_service.py`，内存 Dict 存储）
- [ ] 无效 Key 返回 401，响应体包含 `{"error": "Unauthorized", "message": "Invalid API Key"}`
- [ ] 有效 Key 将 `project_id` 写入 `request.state.project_id`
- [ ] `EXEMPT_PATHS` 支持免鉴权路径（如 `/health`、`/docs`、`/api/v1/quota/**`）

### AC-2：RateLimit 中间件

- [ ] 基于 Redis 的滑动窗口限流（窗口大小 60s，按 `project_id:endpoint` 维度）
- [ ] 默认阈值：普通项目 100 req/min，内部项目 1000 req/min
- [ ] 超限返回 429，响应体包含 `Retry-After` Header
- [ ] Redis 不可用时降级为内存计数（`asyncio.Lock` 保护）

### AC-3：Quota 中间件（增强）

- [ ] 复用 TASK-102 的 `QuotaService`，每日/每月调用上限校验
- [ ] 请求到达时消费配额（`check_and_consume`）
- [ ] 配额超限返回 429，响应体包含 `{"error": "QuotaExceeded", "quota_info": {...}}`
- [ ] 配额接近阈值（≥80%）时在响应 Header 添加 `X-Quota-Warning: true`

### AC-4：Router 中间件

- [ ] 动态路由表（`app/services/router_service.py`），支持 CRUD 路由规则
- [ ] 路由匹配规则：`path_prefix` → `target_url`
- [ ] 支持转发到下游服务（如 `/v1/chat` → `http://localhost:9001`）
- [ ] 使用 `httpx.AsyncClient` 转发请求，保留原 Header + Body
- [ ] 下游服务不可用时返回 503，`{"error": "ServiceUnavailable", "target": "..."}`

### AC-5：Logger 中间件

- [ ] 结构化 JSON 日志（`structlog` 或自定义 Formatter）
- [ ] 每条日志包含：`timestamp`、`level`、`trace_id`、`project_id`、`method`、`path`、`latency_ms`、`status_code`、`user_agent`
- [ ] `trace_id` 从 Header `X-Trace-ID` 读取，不存在时生成 UUID
- [ ] 日志输出到 stdout，格式为单行 JSON

### AC-6：中间件顺序

- [ ] 正确的中间件注册顺序：`LoggerMiddleware` → `AuthMiddleware` → `RateLimitMiddleware` → `QuotaMiddleware` → `RouterMiddleware`
- [ ] 注意：`LoggerMiddleware` 需要最早注册以捕获完整请求生命周期（或使用 `BaseHTTPMiddleware` 包裹）

### AC-7：管理与监控 API

- [ ] `GET /health` → 返回网关状态、各下游服务健康检查
- [ ] `GET /api/v1/admin/routes` → 返回当前路由表
- [ ] `POST /api/v1/admin/routes` → 新增路由规则
- [ ] `DELETE /api/v1/admin/routes/{id}` → 删除路由规则
- [ ] 管理 API 需要 `X-Admin-Key` 鉴权（与业务 API Key 分离）

### AC-8：测试与质量

- [ ] `pytest` 全部通过，覆盖率 ≥ 50%
- [ ] 每个中间件至少 2 个测试用例
- [ ] Router 转发测试使用 `respx` 或 `httpx.MockTransport` mock 下游服务

---

## 4. 技术方案

### 文件变更

```
新增：
- app/middleware/auth.py           # AuthMiddleware（增强多 Key 支持）
- app/middleware/rate_limit.py     # RateLimitMiddleware（滑动窗口）
- app/middleware/quota.py          # QuotaMiddleware（复用+增强）
- app/middleware/router.py         # RouterMiddleware（动态转发）
- app/middleware/logger.py         # LoggerMiddleware（结构化日志）
- app/services/api_key_service.py  # 多项目 API Key 管理
- app/services/rate_limit_service.py # 限流计数服务
- app/services/router_service.py   # 动态路由表管理
- app/models/api_key.py            # APIKey Pydantic 模型
- app/models/route.py              # RouteRule Pydantic 模型
- tests/test_middleware_*.py       # 各中间件测试

修改：
- app/main.py                      # 重新注册中间件链顺序
- app/config.py                    # 添加网关配置项
```

### API Key 服务设计

```python
class APIKeyService:
    """多项目 API Key 管理服务（内存存储，后续迁移 Redis）"""

    def __init__(self):
        self._keys: dict[str, APIKey] = {}
        # 预置默认 Key
        self._keys["kk-admin-key"] = APIKey(
            key="kk-admin-key",
            project_id="admin",
            name="Admin",
            rate_limit=1000,
            status="active",
        )

    def validate(self, key: str) -> APIKey | None:
        """验证 Key，返回 APIKey 或 None"""

    def create_key(self, project_id: str, name: str, rate_limit: int = 100) -> APIKey:
        """创建新 Key"""
```

### 滑动窗口限流算法

```python
async def is_allowed(self, project_id: str, endpoint: str) -> tuple[bool, int]:
    """
    滑动窗口限流检查

    返回: (是否允许, 剩余配额)

    Redis Key: rate_limit:{project_id}:{endpoint}:{window_start}
    Window: 60s
    """
    now = time.time()
    window = int(now // 60) * 60
    key = f"rate_limit:{project_id}:{endpoint}:{window}"

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 120)  # 保留 2 个窗口
    results = await pipe.execute()

    count = results[0]
    limit = await self.get_limit(project_id)
    return count <= limit, max(0, limit - count)
```

### 动态路由转发

```python
async def forward(self, request: Request) -> Response:
    """
    根据请求路径匹配路由规则，转发到下游服务

    匹配规则：最长前缀匹配
    """
    path = request.url.path
    rule = self.router_service.match(path)

    if not rule:
        raise HTTPException(status_code=404, detail="Service not found")

    target = f"{rule.target_url}{path}"

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target,
            headers=dict(request.headers),
            content=await request.body(),
            timeout=30.0,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
```

### 结构化日志格式

```json
{
  "timestamp": "2026-05-26T12:34:56.789Z",
  "level": "INFO",
  "logger": "mcp-hub.gateway",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "proj_001",
  "method": "POST",
  "path": "/v1/chat/completions",
  "status_code": 200,
  "latency_ms": 234.5,
  "user_agent": "Mozilla/5.0...",
  "client_ip": "192.168.1.100"
}
```

### 约束条件

- [ ] 中间件顺序必须严格：`Logger` → `Auth` → `RateLimit` → `Quota` → `Router`
- [ ] 所有外部调用使用 `httpx.AsyncClient`，禁止同步 `requests`
- [ ] Redis 不可用时所有服务降级到内存模式，不影响功能
- [ ] API Key 服务支持热加载（后续从配置文件或数据库读取）
- [ ] 路由表支持热更新（无需重启服务）
- [ ] 错误响应统一格式：`{"error": "ErrorCode", "message": "...", "trace_id": "..."}`
- [ ] 管理 API 与业务 API 鉴权分离（`X-Admin-Key` vs `X-API-Key`）

---

## 5. 依赖与阻塞

| 依赖项                  | 状态      | 说明                              |
| ----------------------- | --------- | --------------------------------- |
| FastAPI + Uvicorn       | ✅ 已完成 | 基础框架已就绪                    |
| RedisClient             | ✅ 已完成 | `app/core/redis_client.py` 已封装 |
| QuotaService (TASK-102) | ✅ 已完成 | 配额规则与用量统计已实现          |
| AuthMiddleware          | ⚠️ 需增强 | 当前单 Key，需改为多项目 Key 管理 |
| CORSMiddleware          | ✅ 已完成 | 跨域已配置                        |
| Pydantic v2             | ✅ 已完成 | 模型验证框架                      |

---

## 6. 风险与应对

| 风险                       | 影响 | 应对策略                                |
| -------------------------- | ---- | --------------------------------------- |
| Router 转发丢失 Header     | 高   | 显式转发所有 Header，排除 `host`        |
| 中间件顺序错误导致逻辑异常 | 高   | 在 `main.py` 中注释说明顺序，测试覆盖   |
| Redis 不可用导致全链路崩溃 | 中   | 所有 Redis 依赖加降级逻辑，内存模式兜底 |
| 下游服务超时拖垮 Gateway   | 中   | 设置 `httpx` timeout，超时报 503        |
| trace_id 传递不一致        | 低   | 统一在 LoggerMiddleware 生成/读取       |

---

## 7. Prompt

```markdown
【Situation】
FastAPI Gateway 项目，已有基础中间件框架（Auth、Quota）和 RedisClient。
需要实现完整的 5 层中间件链：Auth → RateLimit → Quota → Router → Logger。

【Task】
实现 MCP HUB Gateway 核心网关，作为所有外部请求的统一入口。

【Action】

1. 实现 `APIKeyService`（多项目 Key 管理）
   - 内存 Dict 存储，预置 admin Key
   - 支持 validate / create / revoke 操作

2. 增强 `AuthMiddleware`
   - 从 `X-API-Key` 读取
   - 无效返回 401
   - 有效写入 `request.state.project_id`

3. 实现 `RateLimitMiddleware`
   - Redis 滑动窗口（60s）
   - 按 project_id + endpoint 维度
   - 超限返回 429 + Retry-After

4. 增强 `QuotaMiddleware`
   - 复用 `QuotaService.check_and_consume()`
   - 超限返回 429 + quota_info
   - ≥80% 添加 X-Quota-Warning Header

5. 实现 `RouterMiddleware`
   - 动态路由表（最长前缀匹配）
   - 使用 httpx 转发请求
   - 下游不可用返回 503

6. 实现 `LoggerMiddleware`
   - 结构化 JSON 日志
   - trace_id / project_id / latency / status

7. 实现管理 API
   - /health、/api/v1/admin/routes（CRUD）
   - X-Admin-Key 鉴权

8. 注册中间件链（正确顺序）

9. 编写测试（每个中间件 ≥2 个用例）

【Constraint】

- 中间件顺序：Logger → Auth → RateLimit → Quota → Router
- Redis 降级内存模式
- 错误响应统一格式
- httpx 异步转发
- pytest 覆盖率 ≥50%

【Verification】

- pytest tests/ -v --cov=app --cov-fail-under=50
- curl -H "X-API-Key: kk-admin-key" http://localhost:8000/health
- curl -H "X-API-Key: kk-admin-key" http://localhost:8000/v1/chat（测试转发）
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
