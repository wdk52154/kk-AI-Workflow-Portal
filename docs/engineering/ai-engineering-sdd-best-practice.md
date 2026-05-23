# AI 工程化落地指南：驾驭编程 + SDD 最佳实践

> 项目：康康 AI 全栈系统（kk-ai）  
> 版本：v1.0  
> 适用范围：AI 时代软件工程团队的方法论落地

---

## 一、核心理念：AI 工程化的三层飞轮

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 工程化飞轮模型                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│   │  SDD 规范层  │ →  │  AI 驾驭编程 │ →  │  反馈飞轮   │   │
│   │  定义问题   │    │  解决问题   │    │  优化问题   │   │
│   └─────────────┘    └─────────────┘    └─────────────┘   │
│          ↑                                    │             │
│          └────────────────────────────────────┘             │
│                                                             │
│   第一层：人定义高质量规范（What & Why）                      │
│   第二层：AI 按规范执行（How）                                │
│   第三层：结果反哺规范迭代（Better）                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**：

> 人负责**决策**和**验收**，AI 负责**实现**和**优化**。通过 SDD 规范将人的意图精确传达给 AI，通过反馈飞轮持续进化规范。

---

## 二、SDD：Specification-Driven Development 规范驱动开发

### 2.1 什么是 SDD？

SDD 是一种以**结构化规范（Specification）**为核心驱动力的开发方法论。它不是传统意义上的"先写文档再写代码"，而是：

- **可执行的规范**：规范即 prompt，AI 能直接理解并转化为代码
- **分层递进的规范**：从业务需求 → 技术方案 → 代码实现，逐层细化
- **持续演化的规范**：每次迭代后更新规范，形成活文档

### 2.2 SDD 规范分层模型

```
L0 业务层（Business Spec）
    └── "用户需要一个 AI 管理后台，支持主题切换和配额监控"
    
L1 产品层（Product Spec）  
    └── PRD.md：页面结构、交互流程、数据需求
    
L2 架构层（Architecture Spec）
    └── ARCH.md：技术选型、目录结构、接口契约
    
L3 实现层（Implementation Spec）
    └── TASK.md：模块拆分、API 签名、测试策略
    
L4 代码层（Code Spec）
    └── Prompt："按以下规范实现 Button 组件..."
```

### 2.3 规范文件模板

#### ARCH.md（架构规范）

```markdown
# 架构规范：康康 AI 全栈系统

## 1. 技术栈决策

| 层级 | 技术 | 约束 |
|------|------|------|
| 前端 | React 18 + TypeScript | strict 模式 |
| 前端 UI | Ant Design Pro | 优先使用 Pro 组件 |
| 前端状态 | URL + Context | 避免过度引入 Redux |
| 后端 | FastAPI + Python 3.11+ | async/await 全链路 |
| 数据库 | PostgreSQL | 结构化数据 |
| 缓存 | Redis | 限流 + 配额 + Session |
| 部署 | Docker + K8s | 声明式配置 |

## 2. 目录结构规范

```
kk-ai/
├── apps/           # 可独立部署的应用
├── packages/       # 共享库（类型、UI、工具）
├── services/       # 后端服务
│   └── mcp-hub/    # Gateway 入口
├── docs/           # 规范文档（SDD）
│   ├── engineering/  # 工程化规范
│   ├── frontend/     # 前端技术文档
│   └── backend/      # 后端技术文档
└── infra/          # 基础设施（Dockerfile、K8s YAML）
```

## 3. 接口契约

所有前后端交互通过 mcp-hub Gateway：
- 认证：`X-API-Key` Header
- 追踪：`X-Trace-Id` Header（Gateway 自动生成）
- 响应格式：`{ data: T, error?: { code, message } }`

## 4. 编码规范

- TypeScript：`strict: true`，禁用 `any`
- Python：PEP 8，类型注解覆盖率 > 90%
-  commit message：Conventional Commits
```

#### TASK.md（任务规范）

```markdown
# 任务规范：实现用户配额管理页面

## 背景
[链接到 L1 Product Spec]

## 目标
在管理后台新增"配额管理"页面，展示项目配额使用情况。

## 验收标准（AC）
- [ ] 页面路径：`/quota`
- [ ] 展示今日/本月调用量、配额上限、剩余量
- [ ] 调用后端 API：`GET /mcp-hub/quota/{project_id}`
- [ ] 支持按项目筛选（下拉选择）
- [ ] 表格支持排序和分页

## 技术方案
- 使用 `ProTable` 实现表格
- 使用 `StatisticCard` 展示 KPI
- 数据获取：`useSWR` 或 React Query
- 错误处理：统一显示 `message.error()`

## 依赖
- 需要后端先实现 `GET /quota/{project_id}` 接口
- 需要 `@kk-ai/types` 中定义 `QuotaResponse` 类型

## 预估
- 前端：2h
- 后端：2h  
- 联调：1h
```

### 2.4 规范 → Prompt 的转换原则

将 SDD 规范转换为给 AI 的 prompt 时，遵循 **STAR 原则**：

| 字母 | 含义 | 示例 |
|------|------|------|
| **S**ituation | 上下文背景 | "这是一个基于 FastAPI 的 Gateway 服务" |
| **T**ask | 具体任务 | "实现基于 Redis 的滑动窗口限流中间件" |
| **A**ction | 执行约束 | "使用 `redis.asyncio`，限流键格式为 `ratelimit:{project_id}:{endpoint}`" |
| **R**esult | 验收标准 | "返回 `(allowed, current, limit)` 三元组，超限返回 HTTP 429" |

**Prompt 示例**：

```
【Situation】
项目使用 FastAPI + Python 3.13，Monorepo 结构。
已有 RedisClient 封装在 app/utils/redis_client.py。

【Task】
实现 RateLimitMiddleware（滑动窗口限流）。

【Action】
1. 继承 BaseHTTPMiddleware
2. 跳过 /health、/docs 路径
3. 从 request.state 读取 project_id
4. 使用 Redis sorted set（ZADD/ZREMRANGEBYSCORE/ZCARD）实现滑动窗口
5. 限流键：ratelimit:{project_id}:{endpoint}

【Result】
- 超限返回 HTTP 429，body：{ error, message, trace_id, quota }
- 未超限继续执行 call_next
- 添加 DEBUG 日志记录当前计数
```

---

## 三、AI 驾驭编程：从 Copilot 到 Agent

### 3.1 AI 编程的四个阶段

```
Level 1: AI Copilot（副驾驶）
    └── 补全代码、解释代码、简单重构
    └── 工具：GitHub Copilot、Codeium

Level 2: AI Pair（结对编程）
    └── 对话式开发、生成测试、Debug 辅助
    └── 工具：Cursor、Windsurf、ChatGPT

Level 3: AI Driver（驾驭编程）⭐ 当前目标
    └── AI 按规范独立实现模块，人负责验收
    └── 工具：Claude Code、Kimi Code CLI、Devin

Level 4: AI Architect（架构师）
    └── AI 参与技术决策、自动生成 SDD、全栈交付
    └── 未来目标
```

### 3.2 驾驭编程的工作流

```
人                          AI
│                           │
│── 写 TASK.md ─────────────>│
│   (L3 Implementation Spec) │
│                           │
│<── AI 生成代码 + 测试 ───────│
│                           │
│── 代码审查 + 测试运行 ─────>│
│   (人验收，AI 修复)         │
│                           │
│<── AI 修复问题 ────────────│
│                           │
│── 验收通过 ───────────────>│
│   (合并 PR，更新规范)       │
```

### 3.3 驾驭编程的 Best Practice

#### 3.3.1 任务粒度：1 个 AI Session = 1 个 TASK

**不要**：给 AI 一个大而模糊的任务
> ❌ "帮我做一个管理后台"

**要**：拆分为可执行的 TASK，每个 TASK 对应一个 AI Session
> ✅ "实现配额管理页面，详见 docs/tasks/TASK-004-quota-page.md"

#### 3.3.2 上下文管理：给 AI 足够但不过多的上下文

**有效上下文**：
- 当前任务的 TASK.md
- 相关的 API 接口定义
- 已有的组件使用示例（1-2 个即可）
- 目录结构和命名约定

**避免**：
- 一次性丢给 AI 整个代码库
- 包含无关业务的代码
- 过时的文档

#### 3.3.3 迭代策略：小步快跑 + 频繁验收

```
Round 1: 生成骨架代码
    └── 人：确认目录结构、接口签名

Round 2: 填充业务逻辑
    └── 人：确认核心算法、数据流

Round 3: 补充测试和边界处理
    └── 人：运行测试，确认覆盖率

Round 4: 优化和重构
    └── 人：确认代码质量、性能指标
```

#### 3.3.4 代码审查清单（人必须验收）

| 检查项 | 工具辅助 | 人必须确认 |
|--------|---------|-----------|
| 类型安全 | `tsc --noEmit` | ✅ 接口契约 |
| 单元测试 | `pytest` / `vitest` | ✅ 边界条件 |
| 安全漏洞 | `bandit` / `eslint-security` | ✅ 鉴权逻辑 |
| 性能基线 | `pytest-benchmark` | ✅ 复杂度 |
| 代码风格 | `black` / `prettier` | ✅ 可读性 |

---

## 四、在本项目中的具体落地路径

### 4.1 文档目录规范

```
docs/
├── engineering/                    # 工程化方法论（本文档）
│   └── ai-engineering-sdd-best-practice.md
│
├── frontend/
│   ├── monorepo-initialization.md   # 前端架构文档
│   ├── components/                  # 组件规范
│   │   ├── button-spec.md
│   │   └── table-spec.md
│   └── tasks/                       # 前端任务规范（SDD L3）
│       ├── TASK-001-theme-switch.md
│       └── TASK-002-quota-page.md
│
└── backend/
    ├── mcp-hub/                     # Gateway 服务文档
    │   ├── architecture.md
    │   └── middleware-spec.md
    └── tasks/                       # 后端任务规范（SDD L3）
        ├── TASK-001-auth-middleware.md
        └── TASK-002-rate-limit.md
```

### 4.2 AI 驾驭编程的标准 prompt 模板

#### 前端开发 Prompt 模板

```markdown
# 任务：[TASK 标题]

## 背景
项目使用 React 18 + TypeScript + Ant Design Pro，Monorepo 结构。
前端应用在 `kk-ai/apps/web-admin/`。

## 目标
[一句话描述要做什么]

## 参考规范
- 前端架构：docs/frontend/monorepo-initialization.md
- 组件规范：优先使用 Ant Design Pro 组件，其次用 antd，最后自定义
- 样式方案：antd ConfigProvider 主题，不直接使用 Tailwind/CSS Modules

## 具体要求
1. [功能点 1]
2. [功能点 2]
3. [功能点 3]

## 验收标准
- [ ] `pnpm run typecheck` 通过
- [ ] `pnpm run build` 通过
- [ ] 页面在 http://localhost:5173 可正常访问

## 现有代码参考
[提供 1-2 个相关文件的代码片段]
```

#### 后端开发 Prompt 模板

```markdown
# 任务：[TASK 标题]

## 背景
项目使用 FastAPI + Python 3.13，服务位于 `kk-ai/services/{service-name}/`。

## 目标
[一句话描述要做什么]

## 参考规范
- 中间件链：Auth → RateLimit → Quota → Router → Logger
- Redis 封装：app/utils/redis_client.py
- 配置管理：Pydantic Settings（MCPHUB_ 前缀）

## 接口契约
```python
# Request
POST /api/v1/xxx
Headers: X-API-Key: {key}
Body: {...}

# Response 200
{ "data": {...} }

# Response 4xx/5xx
{ "error": "CODE", "message": "...", "trace_id": "..." }
```

## 具体要求
1. [功能点 1]
2. [功能点 2]

## 验收标准
- [ ] `pytest` 通过
- [ ] `python run.py` 可正常启动
- [ ] curl 测试通过
```

### 4.3 反馈飞轮：从 Code Review 到 Spec 升级

```
每次迭代后必须回答三个问题：

1. AI 是否理解了规范？
   └── 如果反复出现相同错误 → 规范不够清晰 → 升级 TASK.md

2. 代码质量是否达标？
   └── 如果频繁需要重构 → 缺乏质量约束 → 在规范中增加"约束条件"

3. 交付速度是否可接受？
   └── 如果 Round > 4 → 任务粒度过大 → 拆分为子 TASK
```

**规范升级示例**：

```diff
# TASK-002-quota-page.md

## 技术方案
  - 使用 ProTable 实现表格
+ - 表格列定义使用 `columns` 变量提取到组件外（便于测试）
+ - 数据加载使用 `useRequest` hook（统一错误处理）
+ - 空状态使用 ProTable 内置 `toolBarRender` 配置
```

---

## 五、工具链建议

| 场景 | 推荐工具 | 说明 |
|------|---------|------|
| AI Coding Agent | Kimi Code CLI / Claude Code | 本地执行，上下文持久化 |
| 代码审查 | GitHub Copilot Chat | 解释代码、找 Bug |
| 文档生成 | Mintlify / Docusaurus | SDD 规范站点化 |
| 测试生成 | Codium / Codeium | 自动生成单元测试 |
| 规范检查 | ESLint + Pydantic | 强制规范落地 |
| CI/CD | GitHub Actions + Turbo Remote Cache | 加速构建 |

---

## 六、总结：AI 工程化的关键转变

| 维度 | 传统开发 | AI 工程化 |
|------|---------|----------|
| **核心产出** | 代码 | **规范 + 代码** |
| **人的角色** | 写代码 | **写规范、验收、决策** |
| **AI 的角色** | 辅助补全 | **按规范执行、迭代优化** |
| **文档** | 事后补 | **事前驱动（SDD）** |
| **迭代方式** | 周级迭代 | **小时级迭代** |
| **质量保障** | 人工 Review | **规范约束 + 自动化 + 人验收** |

> **最终目标**：建立一套"人定义规范 → AI 执行实现 → 自动化验收 → 规范持续进化"的工程化飞轮，让团队从重复编码中解放出来，专注于业务创新和架构决策。

---

## 附录：Prompt 工程速查表

### 上下文注入技巧

```
【文件引用】
请阅读以下文件后实现：
- docs/backend/middleware-spec.md
- app/utils/redis_client.py (第 40-80 行)

【代码片段】
参考以下已有实现风格：
```python
[代码片段]
```

【约束列表】
必须遵守：
1. 不使用 any 类型
2. 所有函数必须有 docstring
3. 异常必须记录 trace_id
```

### 迭代修复技巧

```
【Round N 反馈】
上版本有以下问题：
1. [具体问题 1] → 期望：[正确行为]
2. [具体问题 2] → 期望：[正确行为]

请修复以上问题，保持其他逻辑不变。
```

### 验收确认技巧

```
【验收通过】
代码已确认满足：
- ✅ typecheck 通过
- ✅ 功能符合 TASK.md AC-1, AC-3
- ⚠️ AC-2 的边界条件需要补充测试

下一步：请补充 AC-2 的单元测试。
```
