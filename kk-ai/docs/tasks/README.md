# TASK 规范库

本目录存放所有 AI 工程化的 TASK 规范，作为 AI 驾驭编程的输入契约。

## 目录结构

```
docs/tasks/
├── README.md              # 本文件
├── frontend/              # 前端 TASK
│   └── TASK-XXX-xxx.md
└── backend/               # 后端 TASK
    └── TASK-XXX-xxx.md
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

## 创建新 TASK

1. 复制模板：`cp docs/engineering/TASK-template.md docs/tasks/{frontend,backend}/TASK-XXX-title.md`
2. 按模板填写所有章节
3. 运行验收：`kk-ai/.ai-harness/scripts/verify.sh TASK-XXX`

## 规范升级流程

```
AI 执行 TASK → Harness 验收 → 发现问题 → 更新 TASK.md 约束 → 下次自动避免
```

## 统计数据

- 前端 TASK 总数：0
- 后端 TASK 总数：0
- 一次性通过率：N/A
- 平均迭代轮次：N/A

> 每周更新统计数据。
