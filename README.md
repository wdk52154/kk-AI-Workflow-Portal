# 康康 AI 公司 · 全栈 AI 系统技术规划

> **核心战略**：中台底座先行 → B端赋能与资产沉淀 → C端获客产品 → 模型增强与飞轮闭环
> 
> **AI 之争 = 思维之争 · 体系之争 · 生态之争**

---

## 📋 文档导航

| 文档 | 说明 |
|------|------|
| [`AI_SYSTEM_ROADMAP.md`](./AI_SYSTEM_ROADMAP.md) | 完整技术规划书，含 4 阶段路线图、统一技术规范、风险应对 |
| [`prompt_stage_1_foundation.md`](./prompt_stage_1_foundation.md) | **阶段一提示词**：中台底座建设（MCP HUB + 4大服务 + AI数据中心 + Monorepo） |
| [`prompt_stage_2_internal.md`](./prompt_stage_2_internal.md) | **阶段二提示词**：B端赋能（销售智能 Agent + 素材管理与运营平台） |
| [`prompt_stage_3_customer.md`](./prompt_stage_3_customer.md) | **阶段三提示词**：C端获客（AI语音客服 + 自媒体Agent + 直播切片Agent） |
| [`prompt_stage_4_flywheel.md`](./prompt_stage_4_flywheel.md) | **阶段四提示词**：模型增强与飞轮闭环（LoRA/SFT/DPO + 灰度发布 + Custom Doubao） |

---

## 🏗️ 8大项目生态架构

```
┌─────────────────────────────────────────────────────────────┐
│  C 端获客（Customer-Facing）                                  │
│  项目1 AI实时语音客服  项目2 自媒体运营Agent  项目3 直播切片Agent  │
│  24h在岗·转化漏斗起点   内容产能↑10x           6h直播→10个爆款切片  │
└──────────────────────┬──────────────────────────────────────┘
                       │ 调用多模态素材 API + MCP HUB
┌──────────────────────▼──────────────────────────────────────┐
│  B 端赋能（Internal Empowerment）                             │
│  项目4 销售智能Agent          项目5 素材管理与运营平台            │
│  新人1周上岗·转化↑40%          素材复用率↑5x                     │
│  真实话术RAG + 异议库          图片/视频/海报模板 + 多模态API      │
└──────────────────────┬──────────────────────────────────────┘
                       │ 数据回流 + 销售话术沉淀
┌──────────────────────▼──────────────────────────────────────┐
│  中台底座（Foundation Layer）【最重要】                        │
│  项目6 AI数据中心              项目7 Agent与MCP集群架构          │
│  AI之争=数据之争                一次开发所有项目复用              │
│  微信咨询+客服对话+销售话术      MCP HUB(8000) + LLM(9001)       │
│  →清洗→标注→沉淀               RAG(9002) + Memory(9003)        │
│                                Prompt中心(9004)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ 微调训练数据
┌──────────────────────▼──────────────────────────────────────┐
│  项目8 模型增强与强化学习                                       │
│  豆包1.5 → 懂业务的专属模型 · 灰度迭代                         │
│  SFT/DPO全量训练 → 评估 → 模型仓库 → Custom Endpoint           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 数据飞轮（The AI Flywheel）

```
项目1/4 真实对话 
    → 项目6 AI数据中心（清洗 + 标注）
    → 生成 SFT指令对 + DPO偏好对 + 拒答样本
    → 项目8 模型增强（LoRA验证 → 火山方舟训练 → 评估）
    → Custom Doubao 1.5 Endpoint 灰度发布
    → 项目1/4 调用新模型 → 更好的服务 → 更多对话 → ...
```

---

## 🛠️ 统一技术栈

| 层级 | 技术选型 |
|------|---------|
| **前端** | pnpm + monorepo + React 18 + TypeScript + Vite |
| **后端** | Python 3.11+ + FastAPI + Pydantic v2 |
| **数据库** | PostgreSQL 15+ + SQLAlchemy 2.0 + Alembic |
| **缓存** | Redis 7+ |
| **向量库** | ChromaDB |
| **AI 编排** | LangChain / LangGraph |
| **基座模型** | 豆包 ARK（Doubao 1.5） |
| **云端训练** | 火山方舟 |
| **部署** | Docker + Docker Compose |

---

## 📅 实施阶段

| 阶段 | 周期 | 核心交付 | 提示词文件 |
|------|------|---------|-----------|
| **阶段一** | 6-8 周 | MCP HUB + 4大服务 + AI数据中心 + Monorepo | [`prompt_stage_1_foundation.md`](./prompt_stage_1_foundation.md) |
| **阶段二** | 5-6 周 | 销售Agent + 素材平台 | [`prompt_stage_2_internal.md`](./prompt_stage_2_internal.md) |
| **阶段三** | 8-10 周 | AI客服 + 自媒体Agent + 直播切片 | [`prompt_stage_3_customer.md`](./prompt_stage_3_customer.md) |
| **阶段四** | 持续迭代 | 数据飞轮 + 模型增强 + 灰度发布 | [`prompt_stage_4_flywheel.md`](./prompt_stage_4_flywheel.md) |

---

## 🚀 如何使用这些提示词

1. **阶段启动时**：将对应阶段的 `.md` 文件内容作为 **System Prompt** 输入给 AI 编程助手（如 Cursor、Kimi、Claude Code）
2. **分阶段开发**：严格按照阶段顺序执行，**严禁跳阶段**
3. **接口契约**：阶段一完成后输出的《接口规范文档》是后续阶段的法律
4. **代码仓库**：按 `AI_SYSTEM_ROADMAP.md` 中的 Monorepo 目录结构初始化

---

*康康 AI 公司 · 技术总监规划*  
*2026-05-23*
