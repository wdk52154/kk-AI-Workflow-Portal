# TASK-001：滑动窗口限流中间件

## 元信息

| 字段 | 值 |
|------|---|
| TASK ID | TASK-001 |
| 标题 | Redis 滑动窗口限流中间件 |
| 负责人 | @backend-lead |
| 优先级 | P0 |
| 预估工时 | 3h |
| 关联 ARCH | docs/backend/mcp-hub/architecture.md |

---

## 1. 背景

Gateway 需要保护下游服务不被过载请求打垮，按 project_id + endpoint 维度进行限流。

---

## 2. 目标

实现基于 Redis Sorted Set 的滑动窗口限流中间件，超限返回 HTTP 429。

---

## 3. 验收标准

- [ ] AC-1：每个请求按 `project_id:endpoint` 维度计数
- [ ] AC-2：使用 Redis 滑动窗口（ZADD + ZREMRANGEBYSCORE + ZCARD）
- [ ] AC-3：窗口大小 60 秒，可配置
- [ ] AC-4：超限返回 HTTP 429，body 包含当前计数和上限
- [ ] AC-5：Redis 不可用时降级放行（不阻塞业务）
- [ ] AC-6：`pytest` 测试通过

---

## 4. 技术方案

### 4.1 文件变更

```
新增：
- app/middleware/rate_limit.py
- app/utils/redis_client.py（RateLimit 相关方法）
- tests/test_rate_limit.py

修改：
- app/main.py（注册中间件）
- app/config.py（限流配置项）
```

### 4.2 接口定义

```python
# RedisClient 方法
async def check_rate_limit(
    self,
    project_id: str,
    endpoint: str,
    limit: int,
    window_seconds: int = 60,
) -> tuple[bool, int, int]:
    """Returns (allowed, current_count, limit)"""
```

### 4.3 关键算法

```python
now = time.time()
key = f"ratelimit:{project_id}:{endpoint}"
window_start = now - window_seconds

# 清理过期窗口
pipe.zremrangebyscore(key, 0, window_start)
# 获取当前计数（清理后）
pipe.zcard(key)
# 添加当前请求
pipe.zadd(key, {str(now): now})
pipe.expire(key, window_seconds + 1)

results = await pipe.execute()
current = results[1] + 1
```

### 4.4 约束条件

- [ ] 使用 `redis.asyncio` 异步客户端
- [ ] 使用 pipeline 减少网络往返
- [ ] 超限后 rollback 已添加的计数（避免超限请求仍被计入）
- [ ] 跳过 `/health`、`/docs` 等豁免路径

---

## 5. 依赖与阻塞

| 依赖项 | 状态 | 说明 |
|--------|------|------|
| AuthMiddleware | ✅ 已完成 | 需要先设置 request.state.project_id |
| RedisClient | ✅ 已完成 | 基础封装已就绪 |

---

## 6. 测试策略

### 6.1 单元测试

```python
@pytest.mark.asyncio
async def test_rate_limit_under_limit():
    # 发送 limit-1 次请求，全部通过
    
@pytest.mark.asyncio
async def test_rate_limit_exceed():
    # 发送 limit+1 次请求，最后一次返回 429
    
@pytest.mark.asyncio
async def test_rate_limit_window_slide():
    # 模拟时间流逝，窗口滑动后重置计数
```

### 6.2 集成测试

```bash
curl -H "X-API-Key: test-key" http://localhost:8000/mcp-a/api/test
# 连续发送 61 次，第 61 次应返回 429
```

---

## 7. 给 AI 的 Prompt

```markdown
【Situation】
FastAPI Gateway 项目，已有 RedisClient 封装在 app/utils/redis_client.py。
AuthMiddleware 已设置 request.state.project_id。

【Task】
实现 RateLimitMiddleware，基于 Redis 滑动窗口限流。

【Action】
1. 在 app/middleware/rate_limit.py 中创建 RateLimitMiddleware
2. 继承 BaseHTTPMiddleware
3. 限流键格式：ratelimit:{project_id}:{endpoint}
4. 使用 Redis sorted set 实现滑动窗口
5. 配置项在 app/config.py：RATE_LIMIT_WINDOW_SECONDS、RATE_LIMIT_DEFAULT_PER_MINUTE
6. 跳过 /health、/docs、/openapi.json
7. 超限返回 HTTP 429，body：{ error, message, trace_id, quota: {current, limit, window} }

【Result】
- pytest 通过
- curl 连续请求测试通过
- Redis 不可用时降级放行
```

---

## 8. 迭代记录

| 轮次 | AI 输出 | 人验收结果 | 修复点 |
|------|---------|-----------|--------|
| R1 | 初始实现 | ⚠️ 部分通过 | 超限后未 rollback 计数 |
| R2 | 修复 rollback | ✅ 通过 | - |

---

## 9. 复盘

- Redis pipeline 是性能关键，必须使用
- 超限 rollback 是易遗漏点，应在规范中显式注明
- 降级策略（Redis 不可用时放行）需要在规范中明确，否则 AI 可能默认阻塞
