# TASK-102: 配额管理后端 API 与中间件增强

## 元信息

| 字段 | 值 |
|------|-----|
| **ID** | TASK-102 |
| **Type** | backend |
| **Est** | 3h |
| **Priority** | P1 |
| **Depends On** | TASK-100（配额展示页面已有基础中间件） |
| **Author** | @dekang |
| **Created** | 2026-05-23 |

---

## 背景与目标

当前 MCP HUB Gateway 已有一个基础的 `QuotaMiddleware`，但缺少**配额规则的管理能力**。本 TASK 在后端实现完整的配额规则 CRUD API，并增强中间件使其能够根据规则动态拦截超限请求。

**目标**：
1. 提供 RESTful API 管理配额规则（创建/查询/更新/软删除）
2. 增强 QuotaMiddleware：根据规则动态检查配额，支持阈值告警
3. 实时用量统计 API，供前端展示

---

## 验收标准（AC）

### AC-1: 数据模型定义

- [ ] 创建 `app/models/quota.py`，定义以下 Pydantic v2 模型：
  ```python
  class QuotaRule(BaseModel):
      id: str  # uuid4
      project_name: str
      daily_limit: int = Field(gt=0)
      monthly_limit: int = Field(gt=0)
      alert_threshold: int = Field(ge=1, le=100)  # 百分比
      status: Literal["active", "deleted"] = "active"
      created_at: datetime
      updated_at: datetime
  
  class QuotaRuleCreate(BaseModel):
      project_name: str = Field(min_length=1, max_length=64)
      daily_limit: int = Field(gt=0)
      monthly_limit: int = Field(gt=0)
      alert_threshold: int = Field(ge=1, le=100)
  
  class QuotaRuleUpdate(BaseModel):
      daily_limit: int | None = Field(default=None, gt=0)
      monthly_limit: int | None = Field(default=None, gt=0)
      alert_threshold: int | None = Field(default=None, ge=1, le=100)
      status: Literal["active", "deleted"] | None = None
  
  class QuotaUsage(BaseModel):
      project_name: str
      daily_used: int
      daily_limit: int
      monthly_used: int
      monthly_limit: int
      usage_rate: float  # 0.0 - 100.0
      status: Literal["normal", "warning", "exceeded"]
  ```

### AC-2: 配额规则 CRUD API

- [ ] `GET /api/v1/quota/rules` — 分页查询配额规则
  - 查询参数：`project_name`(模糊匹配), `status`, `page`(默认1), `page_size`(默认20, max100)
  - 响应：
    ```json
    {
      "items": [...],
      "total": 100,
      "page": 1,
      "page_size": 20
    }
    ```
  - `status=deleted` 的规则默认不返回，除非显式指定

- [ ] `POST /api/v1/quota/rules` — 创建配额规则
  - 校验：`monthly_limit >= daily_limit`，否则返回 `422`
  - 同一 `project_name` 只能有一条 `active` 规则，重复创建返回 `409 Conflict`
  - 成功返回 `201`，响应体为创建的规则

- [ ] `GET /api/v1/quota/rules/{id}` — 查询单条规则
  - 不存在返回 `404`

- [ ] `PUT /api/v1/quota/rules/{id}` — 更新配额规则
  - 只允许更新 `daily_limit`, `monthly_limit`, `alert_threshold`, `status`
  - 校验 `monthly_limit >= daily_limit`
  - 更新后 `updated_at` 自动刷新
  - 成功返回 `200`

- [ ] `DELETE /api/v1/quota/rules/{id}` — 软删除
  - 将 `status` 设为 `"deleted"`
  - 返回 `204 No Content`
  - 已删除的规则再次删除返回 `204`（幂等）

### AC-3: 用量统计 API

- [ ] `GET /api/v1/quota/usage` — 查询所有项目的实时用量
  - 返回所有**有配额规则**的项目用量列表
  - 每个项目的计算逻辑：
    - `daily_used`: Redis `GET quota:daily:{project}` 或 0
    - `monthly_used`: Redis `GET quota:monthly:{project}` 或 0
    - `daily_limit/monthly_limit`: 从规则表读取
    - `usage_rate`: `max(daily_used/daily_limit, monthly_used/monthly_limit) * 100`
    - `status`: 
      - `usage_rate >= 100` → `"exceeded"`
      - `usage_rate >= alert_threshold` → `"warning"`
      - 其他 → `"normal"`

- [ ] `GET /api/v1/quota/usage/{project_name}` — 查询单个项目用量
  - 项目无配额规则：返回 `daily_limit=0, monthly_limit=0, status="normal"`
  - 项目名包含 `/` 等特殊字符时正确解码（URL 编码处理）

### AC-4: QuotaMiddleware 增强

- [ ] 请求到达时，从请求头或路径参数中提取 `project_name`
  - 优先从 Header `X-Project-Name` 读取
  - 其次从 URL path 第二段提取（如 `/api/project-a/xxx` → `project-a`）
  - 无项目名则跳过配额检查（放行）

- [ ] 查找该项目的 `active` 配额规则
  - 无规则 → 放行，不记录用量
  - 有规则 → 继续检查

- [ ] 用量检查逻辑：
  - 读取 Redis 中的 `daily_used` 和 `monthly_used`
  - `daily_used >= daily_limit` → 返回 `429`，`error="QUOTA_EXCEEDED"`，`type="daily"`
  - `monthly_used >= monthly_limit` → 返回 `429`，`error="QUOTA_EXCEEDED"`，`type="monthly"`
  - 否则 → 放行，并 `INCR` 计数器

- [ ] 阈值告警：
  - 放行前计算当前使用率
  - 如果使用率 ≥ `alert_threshold`，记录 warning 日志：
    ```
    {"level":"WARNING","event":"QUOTA_ALERT","project":"xxx","daily_usage":"850/1000","monthly_usage":"25000/30000","usage_rate":85,"threshold":80}
    ```

- [ ] Redis 键管理：
  - `quota:daily:{project_name}` — 日计数器，TTL 设为当天剩余秒数
  - `quota:monthly:{project_name}` — 月计数器，TTL 设为当月剩余秒数
  - 键名中的特殊字符用 `:` 替换（安全处理）

### AC-5: 项目列表 API

- [ ] `GET /api/v1/projects` — 返回所有已知项目名列表
  - 用于前端 Select 下拉选择
  - 先从配额规则表中提取，不足则补充预定义列表
  - 返回：`{"items": ["project-a", "project-b", ...]}`

### AC-6: 错误响应规范

所有错误响应统一格式：
```json
{
  "error": "ERROR_CODE",
  "message": "人类可读的错误描述",
  "detail": {} // 可选的额外信息
}
```

| 场景 | HTTP 状态 | error code |
|------|----------|------------|
| 参数校验失败 | 422 | `VALIDATION_ERROR` |
| 项目规则已存在 | 409 | `RULE_EXISTS` |
| 规则不存在 | 404 | `RULE_NOT_FOUND` |
| 日限额超限 | 429 | `QUOTA_EXCEEDED` |
| 月限额超限 | 429 | `QUOTA_EXCEEDED` |

### AC-7: 测试覆盖

- [ ] `test_quota.py` 覆盖以下场景：
  - 创建规则成功（201）
  - 重复创建返回 409
  - 参数校验失败返回 422（月限额 < 日限额）
  - 查询单条规则成功 / 不存在返回 404
  - 更新规则成功，updated_at 刷新
  - 软删除后查询不到
  - 用量统计计算正确（normal/warning/exceeded 三种状态）
  - 中间件：无规则放行、超限拦截 429、阈值告警记录日志

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/mcp-hub/app/models/quota.py` | 新增 | Pydantic 模型定义 |
| `services/mcp-hub/app/router/quota.py` | 新增 | FastAPI 路由：CRUD + usage + projects |
| `services/mcp-hub/app/services/quota_service.py` | 新增 | 业务逻辑：规则存储、用量计算、Redis 操作 |
| `services/mcp-hub/app/middleware/quota.py` | 修改 | 增强：动态规则检查、阈值告警 |
| `services/mcp-hub/app/main.py` | 修改 | 注册 quota_router |
| `services/mcp-hub/tests/test_quota.py` | 新增 | pytest 测试 |

---

## 技术约束

1. **Python 版本**：3.13，使用现代语法（`str | None` 等）
2. **Web 框架**：FastAPI 0.115.x，Pydantic v2
3. **数据存储**：配额规则用内存 `dict[str, QuotaRule]`（键为 `id`），用量用 Redis
4. **Redis 降级**：Redis 不可用时，用量计数回退到内存 `dict`（TTL 不精确，可接受）
5. **并发安全**：用量更新使用 Redis `INCR`，内存模式使用 `threading.Lock`
6. **日志**：使用标准 `logging`，告警日志级别为 `WARNING`

---

## 关键算法

### TTL 计算

```python
from datetime import datetime, timedelta

def get_daily_ttl() -> int:
    """获取当天剩余秒数"""
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - now).total_seconds())

def get_monthly_ttl() -> int:
    """获取当月剩余秒数"""
    now = datetime.now()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    return int((next_month - now).total_seconds())
```

### 使用率计算

```python
def calculate_usage(
    daily_used: int, daily_limit: int,
    monthly_used: int, monthly_limit: int,
    alert_threshold: int
) -> QuotaUsage:
    daily_rate = (daily_used / daily_limit * 100) if daily_limit > 0 else 0
    monthly_rate = (monthly_used / monthly_limit * 100) if monthly_limit > 0 else 0
    usage_rate = max(daily_rate, monthly_rate)
    
    if daily_used >= daily_limit or monthly_used >= monthly_limit:
        status = "exceeded"
    elif usage_rate >= alert_threshold:
        status = "warning"
    else:
        status = "normal"
    
    return QuotaUsage(...)
```

---

## 边界条件

| 场景 | 预期行为 |
|------|---------|
| 项目无配额规则 | 中间件放行，usage API 返回 limit=0 |
| 日限额用完但月限额未用完 | 拦截（429），type="daily" |
| 月限额用完但日限额未用完 | 拦截（429），type="monthly" |
| 修改月限额小于当前已用量 | 允许修改，后续请求会被拦截 |
| 删除规则后新请求到达 | 中间件找不到规则，放行 |
| Redis 故障 | 回退内存模式，用量统计继续可用 |
| 并发请求同时到达 | Redis INCR 保证原子性，不会超卖 |
| 项目名含特殊字符 | 键名做安全替换（`/` → `_`），防止 Redis 键注入 |

---

## 依赖注入设计

```python
# app/services/quota_service.py

class QuotaService:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.rules: dict[str, QuotaRule] = {}  # id -> rule
        self._lock = threading.Lock()
    
    def create_rule(self, data: QuotaRuleCreate) -> QuotaRule:
        """创建规则，检查唯一约束"""
    
    def get_rule(self, rule_id: str) -> QuotaRule | None:
        """查询单条规则"""
    
    def list_rules(
        self, 
        project_name: str | None = None,
        status: str = "active",
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[QuotaRule], int]:
        """分页查询规则，返回 (items, total)"""
    
    def update_rule(self, rule_id: str, data: QuotaRuleUpdate) -> QuotaRule:
        """更新规则"""
    
    def delete_rule(self, rule_id: str) -> None:
        """软删除"""
    
    def get_usage(self, project_name: str) -> QuotaUsage:
        """查询项目实时用量"""
    
    def check_and_increment(self, project_name: str) -> dict:
        """中间件调用：检查配额并增加计数，返回 {"allowed": bool, "reason": str|None}"""

# FastAPI Dependency
def get_quota_service() -> QuotaService:
    from app.main import app
    return app.state.quota_service
```

---

## 实现 Prompt（给 AI 的指令）

```markdown
你是 Python 后端工程师，精通 FastAPI + Pydantic v2 + Redis。

请实现 TASK-102：配额管理后端 API 与中间件增强。

**约束**：
1. 严格按 AC 逐条实现，完成后逐项自检
2. 使用现有项目结构（services/mcp-hub/），遵循已有代码风格
3. 所有模型使用 Pydantic v2，API 使用 FastAPI 0.115.x
4. Redis 操作封装在 `app.utils.redis_client` 中，不要直接引入 redis 库
5. 配额规则存储在内存 dict 中（不需要数据库），用量计数用 Redis
6. 中间件增强要保持向后兼容：无规则的项目继续放行
7. 所有错误响应必须符合统一的错误格式（见 AC-6）
8. 日志使用 Python 标准 logging，告警使用 WARNING 级别

**特别注意**：
- `QuotaRuleCreate` 和 `QuotaRuleUpdate` 不要混淆，更新时 project_name 不可修改
- 软删除只改 status 字段，数据保留在内存中
- Redis 键名要做安全处理（替换特殊字符），防止注入
- TTL 计算要准确：日计数器当天过期，月计数器当月过期
- 内存模式下并发安全使用 threading.Lock

**验证**：
完成后执行：
```bash
cd kk-ai/services/mcp-hub && pytest tests/test_quota.py -v --cov=app --cov-report=term-missing
```
确保所有测试通过，覆盖率 ≥ 50%。
```

---

## 迭代记录

### Round 1

- **时间**：2026-05-23
- **结果**：待执行
- **问题记录**：
  - 
- **规范升级**：
  - 

---

## 参考

- [TASK-100 配额展示页面](../frontend/TASK-100-quota-page.md)
- [TASK-101 配额规则管理页面](../frontend/TASK-101-quota-rule-management.md)
- [后端 API 设计规范](../../engineering/backend-api-design.md)
- [MCP HUB 中间件说明](../../engineering/mcp-hub-middleware.md)
