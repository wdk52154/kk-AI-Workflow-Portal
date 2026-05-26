# TASK-406：Docker Compose 编排

## 元信息

| 字段     | 值                                 |
| -------- | ---------------------------------- |
| TASK ID  | TASK-406                           |
| 标题     | Docker Compose 编排 - 全栈一键启动 |
| 负责人   | @devops-lead                       |
| 优先级   | P1                                 |
| 预估工时 | 6h                                 |
| 关联需求 | TASK-400~405（全部后端服务）       |

---

## 1. 背景

当前项目已有部分 Docker 化（mcp-hub + web-admin + redis），但下游服务（service-llm / service-rag / service-memory / service-prompt / service-data）缺乏 Dockerfile，docker-compose.yml 也未覆盖全栈。开发团队需要：

1. **一键启动**：`docker compose up -d` 拉起全部 6 个服务 + 3 个基础设施
2. **服务依赖**：LLM Gateway 先启动，RAG/Memory/Data 依赖 LLM；Data 依赖 RAG + Memory
3. **健康检查**：每个服务暴露 `/health`，Compose 中配置 `healthcheck` + `depends_on condition`
4. **环境变量统一**：根目录 `.env` 文件管理所有配置，各服务通过 `env_file` 或 `environment` 注入

---

## 2. 目标

实现完整的 Docker Compose 编排，支持：

- **6 个业务服务**：mcp-hub(8000)、service-llm(9001)、service-rag(9002)、service-memory(9003)、service-prompt(9004)、service-data(9005)
- **3 个基础设施**：PostgreSQL(5432)、Redis(6379)、ChromaDB(8001)
- **1 个前端**：web-admin(5173)
- **统一配置**：根目录 `.env` 文件
- **健康检查**：每个服务就绪后才启动下游依赖

---

## 3. 验收标准

### AC-1：所有服务 Dockerfile

- [ ] `services/service-llm/Dockerfile` - Python 3.13 slim，pip 安装依赖，非 root 运行
- [ ] `services/service-rag/Dockerfile` - 同上，需包含 `chroma_data` 数据目录
- [ ] `services/service-memory/Dockerfile` - 同上，需包含 `data/` 数据目录
- [ ] `services/service-prompt/Dockerfile` - 同上，需包含 `prompts/` 目录
- [ ] `services/service-data/Dockerfile` - 同上，需包含 `data/` 数据目录
- [ ] 所有 Dockerfile 遵循统一模式：多阶段构建（如需要）→ 依赖安装 → 代码复制 → 非 root 用户

### AC-2：Docker Compose 全栈编排

- [ ] `docker-compose.yml` 包含以下服务：
      | 服务 | 镜像/构建 | 端口 | 说明 |
      |------|-----------|------|------|
      | postgres | postgres:16-alpine | 5432 | AI 数据中心持久化存储 |
      | redis | redis:7-alpine | 6379 | 缓存 / RateLimit |
      | chromadb | chromadb/chroma:0.6.0 | 8001 | 向量数据库（备选，目前内存降级） |
      | mcp-hub | build: services/mcp-hub | 8000 | API 网关 |
      | service-llm | build: services/service-llm | 9001 | LLM Gateway |
      | service-rag | build: services/service-rag | 9002 | RAG Service |
      | service-memory | build: services/service-memory | 9003 | Memory Service |
      | service-prompt | build: services/service-prompt | 9004 | Prompt Center |
      | service-data | build: services/service-data | 9005 | AI 数据中心 |
      | web-admin | build: apps/web-admin | 5173 | 管理后台 |

### AC-3：服务依赖与健康检查

- [ ] `service-llm` 启动后，`service-rag` / `service-memory` / `service-data` 才启动
- [ ] `redis` 健康后，`mcp-hub` 才启动
- [ ] 每个服务配置 `healthcheck`：
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:${PORT}/health"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
  ```
- [ ] Python 服务需安装 `curl`（在 Dockerfile 中 `apt-get install curl`）

### AC-4：统一环境变量

- [ ] 根目录 `.env` 文件管理全部配置：

  ```bash
  # 基础设施
  POSTGRES_USER=ai_platform
  POSTGRES_PASSWORD=ai_platform_secret
  POSTGRES_DB=ai_platform
  REDIS_URL=redis://redis:6379/0
  CHROMADB_URL=http://chromadb:8001

  # API Keys
  ARK_API_KEY=your-ark-api-key-here
  ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

  # 服务间调用（使用 Docker 网络内域名）
  LLM_GATEWAY_URL=http://service-llm:9001
  RAG_SERVICE_URL=http://service-rag:9002
  MEMORY_SERVICE_URL=http://service-memory:9003
  PROMPT_CENTER_URL=http://service-prompt:9004
  DATA_SERVICE_URL=http://service-data:9005
  MCP_HUB_URL=http://mcp-hub:8000
  ```

- [ ] 各服务 `docker-compose.yml` 中通过 `env_file: .env` 注入环境变量
- [ ] 前端 `VITE_API_BASE_URL` 指向 `http://localhost:8000`

### AC-5：数据卷持久化

- [ ] `postgres-data`：PostgreSQL 数据持久化
- [ ] `redis-data`：Redis 数据持久化
- [ ] `chroma-data`：ChromaDB 数据持久化
- [ ] `service-rag-data`：RAG 文档和向量存储
- [ ] `service-memory-data`：Memory SQLite 数据库
- [ ] `service-data-data`：Data Center SQLite 数据库
- [ ] `service-prompt-data`：Prompt YAML 模板

### AC-6：网络配置

- [ ] 所有服务共享 `ai-platform` bridge 网络
- [ ] 服务间通过服务名（如 `service-llm`）通信

### AC-7：Makefile / 脚本封装

- [ ] `Makefile` 提供常用命令：
  - `make up` → `docker compose up -d`
  - `make down` → `docker compose down`
  - `make logs` → `docker compose logs -f`
  - `make build` → `docker compose build`
  - `make test` → 在各服务容器中运行 pytest
  - `make clean` → 删除卷和网络

### AC-8：冒烟测试

- [ ] `docker compose up -d` 后，所有服务 `docker compose ps` 状态为 `healthy`
- [ ] `curl http://localhost:8000/health` 返回 MCP HUB 健康
- [ ] `curl http://localhost:9001/health` 返回 LLM Gateway 健康
- [ ] `curl http://localhost:9002/health` 返回 RAG Service 健康
- [ ] `curl http://localhost:9003/health` 返回 Memory Service 健康
- [ ] `curl http://localhost:9004/health` 返回 Prompt Center 健康
- [ ] `curl http://localhost:9005/health` 返回 Data Center 健康

---

## 4. 技术方案

### 统一 Dockerfile 模板（Python 服务）

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安装系统依赖（curl for healthcheck）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY run.py .

# 数据目录权限
RUN mkdir -p data && chmod 755 data

# 非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=10s \
  CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["python", "run.py"]
```

### docker-compose.yml 核心结构

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  chromadb:
    image: chromadb/chroma:0.6.0
    volumes:
      - chroma-data:/chroma/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5

  service-llm:
    build: ./services/service-llm
    ports:
      - "9001:9001"
    env_file: .env
    environment:
      - LLM_PORT=9001
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s

  service-rag:
    build: ./services/service-rag
    ports:
      - "9002:9002"
    env_file: .env
    environment:
      - RAG_PORT=9002
      - LLM_GATEWAY_URL=http://service-llm:9001
    depends_on:
      service-llm:
        condition: service_healthy
    volumes:
      - service-rag-data:/app/chroma_data

  service-memory:
    build: ./services/service-memory
    ports:
      - "9003:9003"
    env_file: .env
    environment:
      - MEMORY_PORT=9003
      - LLM_GATEWAY_URL=http://service-llm:9001
    depends_on:
      service-llm:
        condition: service_healthy
    volumes:
      - service-memory-data:/app/data

  service-prompt:
    build: ./services/service-prompt
    ports:
      - "9004:9004"
    env_file: .env
    environment:
      - PROMPT_PORT=9004
    volumes:
      - service-prompt-data:/app/prompts

  service-data:
    build: ./services/service-data
    ports:
      - "9005:9005"
    env_file: .env
    environment:
      - DATA_PORT=9005
      - DATA_RAG_SERVICE_URL=http://service-rag:9002
      - DATA_MEMORY_SERVICE_URL=http://service-memory:9003
      - DATA_LLM_GATEWAY_URL=http://service-llm:9001
    depends_on:
      service-llm:
        condition: service_healthy
      service-rag:
        condition: service_healthy
      service-memory:
        condition: service_healthy
    volumes:
      - service-data-data:/app/data

  mcp-hub:
    build: ./services/mcp-hub
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - MCPHUB_PORT=8000
      - MCPHUB_REDIS_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  web-admin:
    build: ./apps/web-admin
    ports:
      - "5173:80"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - mcp-hub

volumes:
  postgres-data:
  redis-data:
  chroma-data:
  service-rag-data:
  service-memory-data:
  service-data-data:
  service-prompt-data:

networks:
  ai-platform:
    driver: bridge
```

### 约束条件

- [ ] Python 服务 Dockerfile 必须安装 `curl` 用于健康检查
- [ ] 所有服务非 root 运行（`USER appuser`）
- [ ] 环境变量优先使用 `.env` 文件，敏感信息（如 API Key）不硬编码在 compose 中
- [ ] 开发模式使用 `docker compose up -d`，生产模式建议 `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- [ ] 数据卷必须使用命名卷（named volumes），禁止 bind mount 到主机目录（开发环境除外）
- [ ] 服务间调用必须使用 Docker 网络内域名（如 `http://service-llm:9001`），不能使用 `localhost`

---

## 5. 依赖与阻塞

| 依赖项               | 状态      | 说明               |
| -------------------- | --------- | ------------------ |
| mcp-hub Dockerfile   | ✅ 已完成 | 已存在             |
| web-admin Dockerfile | ✅ 已完成 | 已存在             |
| service-llm          | ✅ 已完成 | TASK-401           |
| service-rag          | ✅ 已完成 | TASK-402           |
| service-memory       | ✅ 已完成 | TASK-403           |
| service-prompt       | ✅ 已完成 | TASK-404           |
| service-data         | ✅ 已完成 | TASK-405（刚交付） |

---

## 6. 风险与应对

| 风险                          | 影响 | 应对策略                                     |
| ----------------------------- | ---- | -------------------------------------------- |
| Python 3.13 slim 镜像缺少依赖 | 中   | Dockerfile 中安装 gcc + build-essential      |
| 服务启动顺序错误导致依赖失败  | 高   | `depends_on` + `condition: service_healthy`  |
| 环境变量未注入导致配置错误    | 中   | 统一 `.env` + 启动时打印配置验证             |
| 前端 Vite 代理指向错误        | 低   | 开发时用 `http://localhost:8000`，生产用域名 |
| 数据卷未持久化导致数据丢失    | 高   | 全部使用命名卷，定期备份脚本                 |

---

## 7. Prompt

```markdown
【Situation】
AI 中台已有 6 个后端服务（TASK-400~405）和 1 个前端，需要完整的 Docker Compose 编排实现一键启动。

【Task】
实现 TASK-406：Docker Compose 全栈编排。

【Action】

1. 为 service-llm / service-rag / service-memory / service-prompt / service-data 创建 Dockerfile（参考 mcp-hub 模式）
2. 更新根目录 docker-compose.yml，覆盖全部服务 + PostgreSQL + Redis + ChromaDB
3. 创建根目录 .env 文件统一管理环境变量
4. 为每个服务配置 healthcheck
5. 配置服务依赖（service-llm → service-rag/memory/data）
6. 配置命名卷持久化
7. 创建 Makefile 封装常用命令
8. 冒烟测试：docker compose up -d 后所有服务 healthy

【Constraint】

- Python 服务 Dockerfile 必须安装 curl
- 所有服务非 root 运行
- 服务间调用使用 Docker 网络域名
- 敏感信息不硬编码

【Verification】

- docker compose up -d
- docker compose ps（全部 healthy）
- for port in 8000 9001 9002 9003 9004 9005; do curl -s http://localhost:$port/health; done
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
