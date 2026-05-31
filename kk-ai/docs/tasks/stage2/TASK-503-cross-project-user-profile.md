# TASK-503：跨项目用户画像验证

## 元信息

| 字段       | 值                                                               |
| ---------- | ---------------------------------------------------------------- |
| TASK ID    | TASK-503                                                         |
| 标题       | 跨项目用户画像验证（service-memory + service-sales + web-admin） |
| 优先级     | P1                                                               |
| 类型       | fullstack                                                        |
| 关联       | service-memory:9003, service-sales:9007, web-admin               |
| Depends On | TASK-502（销售 Agent 已完成）                                    |

## 目标

验证阶段一建设的 Cross-Project User Memory 机制，确保用户画像事实可在不同项目间共享和召回，实现"客服记录 → 销售规避"的跨项目数据流转。

## 验收标准

### 后端

- [x] `service-memory:9003` 支持存储用户事实（store_user_fact）
- [x] `service-memory:9003` 支持跨项目召回用户事实（recall_user_facts）
- [x] `service-sales:9007` 的 query 接口自动召回用户画像并规避禁忌产品
- [x] 端到端冒烟测试：存储 "用户A对芒果过敏" → 销售查询自动规避芒果产品

### 前端（web-admin）

- [x] 「用户画像查询」调试页面：输入 user_id 查看跨项目事实
- [x] 支持按 fact_type 筛选：preference / constraint / profile / behavior
- [x] 支持语义查询（基于向量相似度召回）
- [x] 显示事实来源项目（source_project_id）

### 端到端验证

- [x] 项目1（AI客服）记录 "用户A对芒果过敏"
- [x] 项目4（销售Agent）召回该事实
- [x] 自动规避含芒果成分的产品推荐
- [x] 验证记录可查询、可追踪

## 技术约束

- 用户画像存储在 service-memory:9003（SQLite + Embedding）
- 召回使用向量相似度搜索（cosine similarity）
- 所有项目共享同一 user_id 命名空间
- pytest 覆盖率 ≥50%
