# MCP HUB Gateway

统一 HTTP Gateway，为 AI 工作流下游服务提供统一入口，支持鉴权、限流、配额、路由转发、结构化日志。

## 服务信息

| 项 | 值 |
|---|---|
| 服务名 | `mcp-hub` |
| 端口 | `8000` |
| 框架 | FastAPI + Uvicorn |
| 中间件链 | Auth → RateLimit → Quota → Router → Logger |

## 中间件链说明

```
┌─────────────┐
│   Logger    │  ← 外层：生成 trace_id，记录 latency / status / project_id
├─────────────┤
│   Quota     │  ← 检查并消耗项目每日/每月配额
├─────────────┤
│ RateLimit   │  ← Redis 滑动窗口限流 (project_id + endpoint)
├─────────────┤
│    Auth     │  ← 内层：X-API-Key 鉴权，绑定 project_id
├─────────────┤
│   Router    │  ← 动态路由转发到下游服务 (9001-9004+)
└─────────────┘
```

## 快速启动

```bash
cd kk-ai/services/mcp-hub

# 安装依赖（如果未安装）
pip install -r requirements.txt

# 方式一：直接运行
python run.py

# 方式二：使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MCPHUB_PORT` | `8000` | 服务端口 |
| `MCPHUB_DEBUG` | `False` | 调试模式（开启 reload + docs） |
| `MCPHUB_REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `MCPHUB_REDIS_PASSWORD` | `None` | Redis 密码 |
| `MCPHUB_LOG_LEVEL` | `INFO` | 日志级别 |
| `MCPHUB_LOG_FORMAT` | `json` | `json` 或 `text` |
| `MCPHUB_API_KEYS_JSON` | `None` | 内存级 API Key 配置 JSON |
| `MCPHUB_ROUTES_JSON` | `None` | 内存级路由表配置 JSON |
| `MCPHUB_REQUEST_TIMEOUT_SECONDS` | `30.0` | 下游请求超时 |

## API Key 管理

### 方式一：Redis（推荐，生产环境）

```python
import redis, json
r = redis.Redis()
r.hset("mcp-hub:api-keys", "kk_live_demo_key", json.dumps({
    "project_id": "proj_001",
    "name": "康康 AI 中台",
    "api_key": "kk_live_demo_key",
    "daily_quota": 10000,
    "monthly_quota": 300000,
    "rate_limit_per_minute": 60,
    "enabled": True,
}))
```

### 方式二：环境变量（开发/测试）

```bash
export MCPHUB_API_KEYS_JSON='[{
    "project_id": "proj_001",
    "name": "康康 AI 中台",
    "api_key": "kk_live_demo_key",
    "daily_quota": 10000,
    "monthly_quota": 300000,
    "rate_limit_per_minute": 60,
    "enabled": true
}]'
```

## 路由表管理

### 方式一：Redis（推荐）

```python
import redis
r = redis.Redis()
r.hset("mcp-hub:routes", "mcp-a", "http://localhost:9001")
r.hset("mcp-hub:routes", "mcp-b", "http://localhost:9002")
```

### 方式二：环境变量

```bash
export MCPHUB_ROUTES_JSON='[{
    "service_name": "mcp-a",
    "target_url": "http://localhost:9001"
}, {
    "service_name": "mcp-b",
    "target_url": "http://localhost:9002"
}]'
```

## 请求示例

```bash
# 1. Health check（无需鉴权）
curl http://localhost:8000/health

# 2. 转发到下游服务（需要 X-API-Key）
curl -H "X-API-Key: kk_live_demo_key" \
     -H "Content-Type: application/json" \
     http://localhost:8000/mcp-a/api/v1/chat \
     -d '{"message": "hello"}'
```

## 响应头说明

| Header | 说明 |
|--------|------|
| `X-Trace-Id` | 请求链路追踪 ID |
| `X-Quota-Daily-Used` | 当日已调用次数 |
| `X-Quota-Daily-Limit` | 当日配额上限 |
| `X-Quota-Monthly-Used` | 当月已调用次数 |
| `X-Quota-Monthly-Limit` | 当月配额上限 |

## 错误码

| HTTP | Error Code | 说明 |
|------|-----------|------|
| 401 | `UNAUTHORIZED` | 缺少或无效的 X-API-Key |
| 403 | `FORBIDDEN` | 项目被禁用 |
| 404 | `SERVICE_NOT_FOUND` | 下游服务未注册 |
| 429 | `RATE_LIMIT_EXCEEDED` | 滑动窗口限流触发 |
| 429 | `QUOTA_EXCEEDED` | 每日/每月配额耗尽 |
| 502 | `BAD_GATEWAY` | 下游服务不可达 |
| 504 | `GATEWAY_TIMEOUT` | 下游服务超时 |

## 项目结构

```
mcp-hub/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 + 中间件注册
│   ├── config.py            # Pydantic Settings 配置
│   ├── middleware/
│   │   ├── auth.py          # X-API-Key 鉴权
│   │   ├── rate_limit.py    # Redis 滑动窗口限流
│   │   ├── quota.py         # 每日/每月配额
│   │   └── logger.py        # 结构化 JSON 日志
│   ├── router/
│   │   └── proxy.py         # 动态路由转发 + health
│   ├── models/
│   │   └── schemas.py       # Pydantic 模型
│   └── utils/
│       └── redis_client.py  # Redis 客户端封装
├── run.py                   # 开发启动脚本
├── requirements.txt
└── README.md
```
