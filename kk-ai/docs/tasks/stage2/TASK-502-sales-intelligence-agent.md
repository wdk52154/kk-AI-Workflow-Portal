# TASK-502：销售智能 Agent

## 元信息

| 字段       | 值                                                                            |
| ---------- | ----------------------------------------------------------------------------- |
| TASK ID    | TASK-502                                                                      |
| 标题       | 销售智能 Agent（service-sales + web-sales）                                   |
| 优先级     | P1                                                                            |
| 类型       | fullstack                                                                     |
| 关联       | service-rag:9002, service-memory:9003, service-data:9005, service-prompt:9004 |
| Depends On | TASK-501（素材平台骨架已完成）                                                |

## 目标

建设销售智能 Agent，实现话术 RAG 推荐、AI 陪练对话、数据回流数据中心，提升销售团队转化率。

## 验收标准

### 后端（service-sales, Port 9007）

- [x] `POST /v1/sales/query` - 输入客户问题，返回推荐话术 + 异议处理方案
- [x] `POST /v1/sales/roleplay/start` - 开始陪练，返回角色设定
- [x] `POST /v1/sales/roleplay/chat` - 陪练对话（流式 SSE 返回）
- [x] `POST /v1/sales/roleplay/evaluate` - 结束陪练，综合评分与改进建议
- [x] `GET /v1/sales/scripts` - 话术库 CRUD
- [x] `POST /v1/sales/scripts` - 录入新话术，**自动回流到 service-data:9005**
- [x] `GET /v1/sales/conversations` - 查询陪练对话记录，支持标记优质对话
- [x] 数据回流机制：优质对话（评分≥80）→ service-data /data/ingest → 沉淀为话术/异议库
- [x] 调用 service-prompt:9004 获取陪练客户角色 Prompt 模板（客户端就绪，YAML 已注册）
- [x] pytest 覆盖率 ≥50%（实际 88%）

### 前端（apps/web-sales, Port 5175）

- [x] 销售话术助手：对话式查询界面
- [x] AI 陪练室：分屏界面（学员输入 + AI 客户回复 + 实时评分）
- [x] 话术库管理：增删改查 + 回流标记
- [x] 销售看板：陪练记录、评分趋势、常用话术统计
- [x] 前端单元测试（Vitest）：覆盖 services/sales.ts（8 tests passed）
- [x] TypeScript 严格模式零报错

## 技术约束

- 所有 LLM 调用走 mcp-hub:8000 → service-llm:9001
- 知识库检索走 service-rag:9002
- 用户画像调用 service-memory:9003
- 数据回流调用 service-data:9005 /data/ingest
- 话术 Prompt 模板从 service-prompt:9004 获取（禁止硬编码）
- pytest 覆盖率 ≥50%
