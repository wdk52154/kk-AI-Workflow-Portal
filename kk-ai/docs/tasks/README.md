# TASK 规范库

本目录存放所有 AI 工程化的 TASK 规范，作为 AI 驾驭编程的输入契约。

## 目录结构

```
docs/tasks/
├── README.md                        # 本文件
├── TASK-template.md                 # 空白 TASK 模板（复制使用）
├── TASK-iteration-template.md       # 迭代复盘模板
├── frontend/                        # 前端 TASK
│   ├── TASK-100-quota-page.md       # 配额管理页面
│   ├── TASK-101-model-management.md # 模型管理页面
│   └── ...
└── backend/                         # 后端 TASK
    ├── TASK-300-quota-api.md        # 配额查询 API
    ├── TASK-301-model-test-api.md   # 模型测试 API（SSE）
    └── ...
```

## TASK 编号规则

| 前缀                | 范围     | 说明                 |
| ------------------- | -------- | -------------------- |
| TASK-001 ~ TASK-099 | 基础设施 | Husky、CI/CD、工具链 |
| TASK-100 ~ TASK-199 | 前端页面 | web-admin 页面开发   |
| TASK-200 ~ TASK-299 | 前端组件 | @kk-ai/ui 组件开发   |
| TASK-300 ~ TASK-399 | 后端服务 | Gateway、API 开发    |
| TASK-400 ~ TASK-499 | 数据模型 | 类型定义、数据库     |
| TASK-500 ~ TASK-599 | 文档规范 | 工程化文档、最佳实践 |

## 创建新 TASK 的标准流程

```bash
# 1. 复制模板
cp docs/tasks/TASK-template.md docs/tasks/frontend/TASK-XXX-title.md

# 2. 按模板填写所有章节
# 重点：AC（验收标准）必须可验证

# 3. 将 TASK 转换为 Prompt
# 参考 .ai-harness/prompts/frontend-task.md 或 backend-task.md

# 4. 发给 AI 执行

# 5. 运行验收脚本
kk-ai/.ai-harness/scripts/verify.sh TASK-XXX

# 6. 填写迭代复盘
# cp docs/tasks/TASK-iteration-template.md docs/tasks/frontend/TASK-XXX-iteration.md
```

## 当前 TASK 列表

### 前端（Frontend）

| ID       | 标题         | 状态      | 预估 | 实际 | 迭代 |
| -------- | ------------ | --------- | ---- | ---- | ---- |
| TASK-100 | 配额管理页面 | ⬜ 待开发 | 3h   | -    | -    |
| TASK-101 | 模型管理页面 | ⬜ 待开发 | 4h   | -    | -    |

### 后端（Backend）

| ID       | 标题                | 状态      | 预估 | 实际 | 迭代 |
| -------- | ------------------- | --------- | ---- | ---- | ---- |
| TASK-300 | 配额查询 API        | ⬜ 待开发 | 2h   | -    | -    |
| TASK-301 | 模型测试 API（SSE） | ⬜ 待开发 | 3h   | -    | -    |

## 规范进化飞轮

```
创建 TASK → AI 执行 → Harness 验收 → 发现问题
     ↑                                      ↓
  升级规范 ←────── 填写迭代复盘 ←───────┘
```

**核心原则**：每次失败都是规范升级的机会，让下一个同类 TASK 更容易成功。

## 统计数据

- 前端 TASK 总数：2
- 后端 TASK 总数：2
- 已完成 TASK：0
- 平均迭代轮次：N/A
- 一次性通过率：N/A

> 每周更新统计数据。
