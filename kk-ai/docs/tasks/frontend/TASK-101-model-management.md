# TASK-101：模型管理页面

## 元信息

| 字段     | 值                   |
| -------- | -------------------- |
| TASK ID  | TASK-101             |
| 标题     | 实现 AI 模型管理页面 |
| 优先级   | P1                   |
| 预估工时 | 4h                   |

---

## 2. 目标

新增 `/models` 路由页面，展示接入的 AI 模型列表，支持启用/停用操作。

---

## 3. 验收标准

- [ ] AC-1：ProTable 展示模型列表（模型名、提供商、状态、QPS、延迟、操作）
- [ ] AC-2：状态列用 Switch 组件切换启用/停用
- [ ] AC-3：操作列包含"编辑"和"测试"按钮
- [ ] AC-4：点击"测试"弹出 Modal，输入 prompt 后调用测试接口
- [ ] AC-5：表格支持按提供商筛选
- [ ] AC-6：`typecheck + test:unit + build` 通过

---

## 4. 技术方案

### API 接口

```typescript
// GET /models
interface ModelInfo {
  modelId: string;
  name: string;
  provider: "openai" | "anthropic" | "local";
  status: "active" | "inactive";
  qps: number;
  avgLatency: number;
}

// POST /models/{id}/toggle
// POST /models/{id}/test  body: { prompt: string }
```

### 约束条件

- [ ] Switch 切换时显示 loading，完成后显示 message.success
- [ ] Modal 表单使用 ProForm
- [ ] 测试接口返回流式响应，需要 SSE 处理

---

## 7. Prompt

```markdown
【Situation】
项目使用 Ant Design Pro，已有 ProTable + ProForm + Modal 组件可用。

【Task】
实现模型管理页面 /models。

【Action】

1. ProTable 展示模型列表，列：name, provider(Tag), status(Switch), qps, avgLatency, actions
2. Switch 切换模型状态，调用 POST /models/{id}/toggle
3. "测试"按钮打开 Modal，ProForm 输入 prompt
4. 提交后调用 POST /models/{id}/test，流式展示响应
5. 支持按 provider 筛选

【Constraint】

- 流式响使用 EventSource 或 fetch + ReadableStream
- Switch loading 状态必须处理
- 不使用 any
```
