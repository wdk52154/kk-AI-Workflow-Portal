# 康康 AI 公司 · AI 系统技术总监规划书
## Technical Director's Implementation Roadmap

> **核心战略**：中台底座先行（项目6+7）→ B端赋能与资产沉淀（项目4+5）→ C端获客产品（项目1+2+3）→ 模型增强与飞轮闭环（项目8）
> 
> **技术统一约束**：前端 `pnpm + monorepo + React18` | 后端 `Python + FastAPI + PostgreSQL + Redis` | AI `Python原生 / LangChain生态`

---

## 阶段一：中台底座建设（Foundation Layer）
**工期建议**：6-8 周 | **核心目标**：搭建 MCP 集群中枢 + AI 数据中心 + 统一基础设施

### 1.1 本阶段涵盖项目
- **项目7**：Agent 与 MCP 集群架构（MCP HUB + 4大核心服务）
- **项目6**：AI 数据中心（数据清洗、标注、存储、版本管理）
- **基础设施**：ChromaDB、SQLite、Redis、YAML Prompt 模板引擎

### 1.2 架构要点
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| MCP HUB Gateway | FastAPI (Port 8000) | Auth → RateLimit → Quota → Router → Logger |
| LLM 网关 | FastAPI (Port 9001) | chat_completion / embedding / list_models，对接豆包 ARK |
| RAG 服务 | FastAPI (Port 9002) | ingest_document / search_knowledge，多租户 project_id 隔离 |
| 记忆服务 | FastAPI (Port 9003) | Conversation Memory + Cross-Project User Facts (SQLite/Redis) |
| Prompt 中心 | FastAPI (Port 9004) | MCP 原生 @server.prompt() + YAML 模板热更新 |
| 向量数据库 | ChromaDB | 知识库向量存储 |
| 元数据/关系库 | PostgreSQL + SQLite | PostgreSQL 主库，SQLite 用于轻量级元数据 |
| 缓存与会话 | Redis | Cache + Session + RateLimit |
| 前端管理台 | React18 + monorepo | 中台管理后台、服务监控、数据标注界面 |

### 1.3 交付物
- [ ] MCP HUB 可运行，支持 `X-API-Key` 鉴权与路由分发
- [ ] 4大微服务（9001-9004）容器化（Docker Compose）
- [ ] 数据中心完成 ETL Pipeline：微信咨询 + 客服对话 + 销售话术 → 清洗 → 标注 → 沉淀
- [ ] 前端 monorepo 初始化完成，共享 UI 组件库搭建

---

## 阶段二：B端赋能与资产中台（Internal Empowerment）
**工期建议**：5-6 周 | **核心目标**：销售智能提效 + 多模态素材资产管理

### 2.1 本阶段涵盖项目
- **项目5**：素材管理与运营平台（Asset & Ops Platform）
- **项目4**：销售智能 Agent（Sales Agent）

### 2.2 架构要点
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 素材平台后端 | FastAPI | 图片/视频/海报模板的 CRUD + 分类标签 + 多模态素材 API |
| 素材平台前端 | React18 | 素材库管理、海报编辑器集成、模板市场 |
| 销售 Agent 后端 | FastAPI + LangChain | 销售话术 RAG、异议库检索、AI 陪练对话 |
| 销售 Agent 前端 | React18 | 销售话术助手、陪练界面、话术评分看板 |
| 数据回流 | 项目6 API | Top Sales 话术自动沉淀、对话数据回写数据中心 |

### 2.3 交付物
- [ ] 素材平台上线：素材复用率提升 5x 的基础设施就绪
- [ ] 销售 Agent 上线：新人 1 周上岗，RAG 检索销售话术 + 异议库
- [ ] 与项目7 MCP HUB 完全打通，通过 `recall_user_facts` 获取跨项目用户画像

---

## 阶段三：C端获客产品矩阵（Customer-Facing）
**工期建议**：8-10 周 | **核心目标**：3大 C 端 Agent 产品化上线

### 3.1 本阶段涵盖项目
- **项目1**：AI 实时语音对话客服（AI Voice Agent）
- **项目2**：自媒体运营 Agent（Content Agent）
- **项目3**：智能直播切片 Agent（Live Clipping Agent）

### 3.2 架构要点
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| AI 客服后端 | FastAPI + LangChain | RAG 检索 + 7阶段 Pipeline + 多模态回复 + 长期记忆 + TTS/STT |
| AI 客服前端 | React18 | 语音交互 UI、对话界面、客服管理后台 |
| 自媒体 Agent 后端 | FastAPI + LangChain | 选题策划、文案生成、多平台适配、自动发布 API 对接 |
| 自媒体 Agent 前端 | React18 | 内容编辑器、发布日历、数据看板 |
| 直播切片后端 | FastAPI + CV/ASR | 直播流录制、ASR 转写、智能高光检测、自动切片 |
| 直播切片前端 | React18 | 直播管理、切片审核、视频编辑器 |
| 统一依赖 | 项目5 素材API | C端产品调用素材平台获取图片/视频/海报 |
| 统一依赖 | 项目7 MCP | chat_completion + search_knowledge + recall_memory |

### 3.3 交付物
- [ ] AI 客服：24h 智能客服上线，支持语音对话，转化漏斗起点就绪
- [ ] 自媒体 Agent：内容产能提升 10x，支持多平台运营
- [ ] 直播切片 Agent：6h 直播 → 10 个爆款切片，自动化 Pipeline 跑通
- [ ] 所有 C 端产品通过 MCP HUB 统一调用底层能力

---

## 阶段四：模型增强与飞轮闭环（Model Enhancement & Flywheel）
**工期建议**：持续迭代（首期 4-6 周） | **核心目标**：数据飞轮转起来，模型越用越聪明

### 4.1 本阶段涵盖项目
- **项目8**：模型增强与强化学习（Model Enhancement & RL）
- **飞轮闭环**：Real Conversations → Better Data → Smarter Model → Better Service → More Conversations

### 4.2 架构要点
| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 数据飞轮引擎 | Python + PostgreSQL | 从项目6抽取 SFT指令对 + DPO偏好对 + 拒答样本 |
| 本地验证 | Python + LoRA | 本地 LoRA 验证流程 |
| 云端训练 | 火山方舟 API | SFT/DPO 全量训练 → 评估 → 模型仓库 |
| 模型仓库 | FastAPI + OSS | 模型版本管理、灰度发布、A/B Test |
| 模型部署 | Custom Doubao 1.5 Endpoint | 训练好的新模型注册回 MCP LLM 网关的 endpoint 池 |
| GPO/RL | Python | 强化学习优化策略（如 GPO） |

### 4.3 数据飞轮 Pipeline
```
项目1/4 真实对话 
    → 项目6 AI数据中心（清洗+标注）
    → 生成 SFT指令对 + DPO偏好对 + 拒答样本
    → 项目8 模型增强（LoRA验证 → 火山方舟训练 → 评估）
    → Custom Doubao 1.5 Endpoint 灰度发布
    → 项目1 AI客服 / 项目4 销售Agent 调用新模型
    → 更好的服务 → 更多用户对话 → 更多数据
```

### 4.4 交付物
- [ ] 模型增强 Pipeline 自动化：从数据抽取到模型部署全链路
- [ ] Custom Doubao 1.5 Endpoint 上线，支持灰度发布
- [ ] 数据飞轮指标看板：对话量、数据质量、模型评分、业务转化

---

## 统一技术规范

### 代码仓库组织（Monorepo）
```
dongwang-ai/
├── apps/
│   ├── web-admin/          # 中台管理后台 (React18)
│   ├── web-sales/          # 销售 Agent 前端 (React18)
│   ├── web-voice/          # AI 客服前端 (React18)
│   ├── web-content/        # 自媒体 Agent 前端 (React18)
│   ├── web-live/           # 直播切片前端 (React18)
│   └── web-asset/          # 素材平台前端 (React18)
├── packages/
│   ├── ui/                 # 共享 UI 组件库 (shadcn/ui 或自研)
│   ├── utils/              # 共享工具库
│   └── types/              # 共享 TypeScript 类型
├── services/               # 后端微服务 (Python + FastAPI)
│   ├── mcp-hub/            # 项目7: MCP HUB Gateway (Port 8000)
│   ├── service-llm/        # LLM 网关 (Port 9001)
│   ├── service-rag/        # RAG 服务 (Port 9002)
│   ├── service-memory/     # 记忆服务 (Port 9003)
│   ├── service-prompt/     # Prompt 中心 (Port 9004)
│   ├── service-data/       # 项目6: AI 数据中心
│   ├── service-sales/      # 项目4: 销售智能 Agent
│   ├── service-asset/      # 项目5: 素材管理与运营平台
│   ├── service-voice/      # 项目1: AI 实时语音客服
│   ├── service-content/    # 项目2: 自媒体运营 Agent
│   ├── service-live/       # 项目3: 智能直播切片 Agent
│   └── service-model/      # 项目8: 模型增强与 RL
├── infra/
│   ├── docker-compose.yml  # 本地开发环境
│   └── k8s/                # K8s 部署清单 (后期)
└── pnpm-workspace.yaml
```

### 后端规范
- **框架**：FastAPI + Pydantic v2
- **数据库**：PostgreSQL（主库）+ Redis（缓存）+ ChromaDB（向量）
- **ORM**：SQLAlchemy 2.0 + Alembic 迁移
- **异步**：全链路 async/await
- **API 文档**：自动 OpenAPI/Swagger
- **鉴权**：JWT + X-API-Key 双模式
- **通信**：项目间内部调用优先使用 HTTP + 共享 Redis 消息队列

### AI 规范
- **LLM 接入**：统一通过项目7 LLM 网关，禁止各服务直接调用豆包 ARK
- **RAG 标准**：所有知识库检索必须经过项目7 RAG 服务
- **记忆标准**：用户画像、对话记忆统一走项目7 记忆服务
- **Prompt 管理**：所有 Prompt 必须注册到项目7 Prompt 中心，支持 YAML 热更新
- **Agent 框架**：推荐使用 LangChain / LangGraph 编排复杂 Agent 工作流

### 部署规范
- **容器化**：所有服务 Docker 化，阶段一完成 Docker Compose 编排
- **环境**：本地 → 测试 → 预发布 → 生产
- **监控**：Prometheus + Grafana（后期）
- **日志**：结构化 JSON 日志，统一收集

---

## 风险与应对
| 风险 | 应对策略 |
|------|---------|
| MCP 架构复杂度高，初期过度设计 | 阶段一先实现核心网关+4服务，后期扩展 |
| 多项目并行，接口不兼容 | 严格定义 OpenAPI 契约，阶段一输出接口规范文档 |
| 数据质量差，模型增强效果不明显 | 项目6优先建设数据清洗和人工审核流程 |
| C端产品需求变更快 | 阶段三采用敏捷迭代，MVP 先上线再优化 |
| 语音实时性要求高 | 项目1采用流式传输（WebSocket/SSE），TTS/STT 异步处理 |

---

*规划人：AI 技术总监*  
*版本：v1.0*  
*日期：2026-05-23*
