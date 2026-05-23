# AI Harness 使用指南

## 快速开始

### 1. 准备 TASK 规范

```bash
# 复制模板并填写
cp docs/tasks/TASK-template.md docs/tasks/frontend/TASK-100-xxx.md
# 用编辑器填写所有章节
```

### 2. 生成 Prompt

```bash
# 读取 System Prompt + Task-specific Prompt
cat .ai-harness/prompts/system-prompt.md
# 根据 TASK 内容填充 frontend-task.md 或 backend-task.md 模板
```

### 3. AI 执行

将生成的 Prompt 发给 AI Agent（Kimi Code / Claude Code / Cursor）。

### 4. 应用变更

AI 输出通常是完整的文件代码，需要手动或脚本应用到项目中。

```bash
# 方式一：手动复制
# 打开 AI 输出的文件，复制到对应目录

# 方式二：使用 patch
# 让 AI 输出 diff 格式，应用 patch
```

### 5. 运行验收

```bash
# 验收脚本会自动运行类型检查、测试、构建、lint
cd kk-ai
./.ai-harness/scripts/verify.sh TASK-100
```

### 6. 迭代修复

如果验收失败，将错误日志反馈给 AI：

```markdown
【验收失败反馈】

TASK：TASK-100
轮次：Round 2

Harness 检查结果：
```

[粘贴 verify.sh 输出]

```

请分析失败原因，修复问题后重新输出完整代码。
修复原则：
1. 只修改与错误相关的代码
2. 保持其他逻辑不变
3. 如果错误是因为规范不明确，请指出需要升级的约束
```

### 7. 填写迭代复盘

验收通过后，填写复盘文档，更新规范库。

```bash
cp docs/tasks/TASK-iteration-template.md docs/tasks/frontend/TASK-100-iteration.md
```

---

## 目录说明

| 目录/文件                  | 作用                                 |
| -------------------------- | ------------------------------------ |
| `prompts/system-prompt.md` | 系统级上下文，每次给 AI 的第一条消息 |
| `prompts/frontend-task.md` | 前端任务 Prompt 模板                 |
| `prompts/backend-task.md`  | 后端任务 Prompt 模板                 |
| `scripts/verify.sh`        | 验收脚本，6 阶段检查                 |
| `reports/`                 | 验收报告存放目录                     |

## 最佳实践

1. **TASK 粒度**：一个 TASK 对应 2-4 小时的开发量，超过则拆分
2. **AC 必须可验证**：每个验收标准都能通过脚本或人工检查确认
3. **Prompt 不要太长**：提供必要上下文即可，避免一次性给 AI 整个代码库
4. **失败即进化**：每次验收失败都更新 TASK.md 约束，下次同类任务自动避免
