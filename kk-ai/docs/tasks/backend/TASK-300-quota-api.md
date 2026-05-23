# TASK-300：配额查询 API

## 元信息

| 字段     | 值                              |
| -------- | ------------------------------- |
| TASK ID  | TASK-300                        |
| 标题     | 实现配额查询 API                |
| 负责人   | @backend-lead                   |
| 优先级   | P0                              |
| 预估工时 | 2h                              |
| 关联需求 | TASK-100 前端配额页面需要数据源 |

---

## 2. 目标

实现 `GET /quota` 接口，返回所有项目的配额汇总和明细。

---

## 3. 验收标准

- [ ] AC-1：接口返回配额汇总（今日总调用、本月总调用、平均使用率、超限项目数）
- [ ] AC-2：接口返回各项目配额明细（projectId, name, todayUsed/Limit, monthUsed/Limit, usageRate, status）
- [ ] AC-3：数据从 Redis 配额键读取（`quota:daily:YYYYMMDD:{project_id}` 等）
- [ ] AC-4：如果 Redis 无数据，返回默认值（used=0）
- [ ] AC-5：接口需要 X-API-Key 鉴权（通过 AuthMiddleware）
- [ ] AC-6：`pytest` 通过，覆盖率 > 50%

---

## 4. 技术方案

### 文件变更

```
新增：
- app/router/quota.py          # 配额路由
- tests/test_quota.py          # 单元测试

修改：
- app/main.py                  # 注册 quota 路由
- app/router/proxy.py          # 如需调整路由冲突
```

### 接口定义

```python
# GET /quota
# Headers: X-API-Key: xxx

# Response 200
{
  "data": {
    "summary": {
      "todayTotal": 8432,
      "monthTotal": 156789,
      "avgUsageRate": 42.5,
      "exceededCount": 0
    },
    "projects": [
      {
        "projectId": "proj_001",
        "projectName": "康康 AI 中台",
        "todayUsed": 5234,
        "todayLimit": 10000,
        "monthUsed": 89321,
        "monthLimit": 300000,
        "usageRate": 52.3,
        "status": "normal"
      }
    ]
  }
}
```

### 核心算法

```python
async def get_quota_summary():
    now = datetime.now()
    day_key = now.strftime("quota:daily:%Y%m%d")
    month_key = now.strftime("quota:monthly:%Y%m")

    # 从 Redis 批量读取所有项目的配额
    # 计算汇总指标
    # 返回响应
```

### 约束条件

- [ ] 使用 Redis pipeline 批量读取
- [ ] 使用 Pydantic 模型验证响应
- [ ] 异常必须记录 trace_id
- [ ] 数据不存在时返回 0 而非报错

---

## 5. 依赖与阻塞

| 依赖项                 | 状态      | 说明                                         |
| ---------------------- | --------- | -------------------------------------------- |
| RedisClient quota 方法 | ✅ 已完成 | redis_client.py 已有 check_and_consume_quota |
| AuthMiddleware         | ✅ 已完成 | 已设置 request.state.project_id              |

---

## 7. Prompt

```markdown
【Situation】
FastAPI Gateway 项目，已有 RedisClient 封装和 AuthMiddleware。
需要为前端配额页面提供数据接口。

【Task】
实现 GET /quota 接口，返回配额汇总和明细。

【Action】

1. 在 app/router/quota.py 创建路由
2. 从 Redis 读取 quota:daily:YYYYMMDD:_ 和 quota:monthly:YYYYMM:_
3. 计算 summary 指标和 projects 明细
4. 状态计算：usageRate < 80% normal, < 100% warning, >= 100% exceeded
5. 注册到 app/main.py
6. 编写 tests/test_quota.py

【Constraint】

- 使用 Redis pipeline 批量读取
- 使用 Pydantic 模型
- 异常记录 trace_id
- 数据缺失返回 0

【Verification】

- pytest tests/test_quota.py
- mypy app/router/quota.py
- curl -H "X-API-Key: xxx" http://localhost:8000/quota
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
