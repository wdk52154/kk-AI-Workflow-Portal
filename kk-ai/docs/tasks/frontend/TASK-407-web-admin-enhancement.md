# TASK-407：前端中台管理后台增强

## 元信息

| 字段     | 值                                                           |
| -------- | ------------------------------------------------------------ |
| TASK ID  | TASK-407                                                     |
| 标题     | web-admin 增强 - 监控看板 / 数据标注 / Prompt 管理 / API Key |
| 负责人   | @frontend-lead                                               |
| 优先级   | P1                                                           |
| 预估工时 | 12h                                                          |
| 类型     | frontend                                                     |
| 关联需求 | TASK-400~405（全部后端服务）                                 |

---

## 1. 背景

当前 web-admin 只有总览 Dashboard 和配额管理两个功能模块。随着后端 6 个服务（mcp-hub / service-llm / service-rag / service-memory / service-prompt / service-data）全部就绪，运营团队需要在前端统一管理：

1. **服务健康监控**：实时查看各服务的 QPS、延迟、错误率、健康状态
2. **数据标注**：人工审核清洗后的数据，打标签（意图、情绪、质量）
3. **Prompt 模板管理**：YAML 编辑器 + 变量校验 + 实时渲染预览
4. **API Key 管理**：项目级 Key 的增删改查与配额设置

---

## 2. 目标

在 web-admin 中新增 4 个功能模块，全部对接真实后端 API。

---

## 3. 验收标准

### AC-1：服务监控看板（`/monitor`）

- [ ] 页面展示 6 个服务的健康状态卡片：
  - mcp-hub (8000)、service-llm (9001)、service-rag (9002)、service-memory (9003)、service-prompt (9004)、service-data (9005)
- [ ] 每个卡片显示：`status`（ok/degraded/down）、`version`、服务专属指标
  - mcp-hub：Redis 连接状态
  - service-llm：模型加载数量
  - service-rag：集合数量
  - service-memory：热记忆数量
  - service-prompt：Prompt 模板数量
  - service-data：总记录数 / 清洗数
- [ ] 整体统计行：在线服务数 / 总服务数、平均延迟（mock 数据）、今日错误数（mock 数据）
- [ ] 每 30 秒自动刷新，支持手动刷新按钮
- [ ] 状态色：ok=绿色、degraded=黄色、down=红色
- [ ] 任一服务不可用时显示错误提示但不阻塞页面

### AC-2：数据标注界面（`/data/annotation`）

- [ ] 页面展示待标注数据列表（调用 `GET /v1/data/pending_annotation`）
- [ ] 列表字段：ID、清洗后内容、质量评分、创建时间
- [ ] 支持分页（page / page_size）
- [ ] 点击「标注」弹出 Drawer，包含表单：
  - `intent`：Select 选择器（预设选项：咨询、投诉、购买意向、高转化、客户异议、其他）
  - `emotion`：Select 选择器（positive、neutral、negative）
  - `quality_score`：Rate 评分 1-5 星
  - `tags`：Tag 输入框，支持多标签
  - `notes`：TextArea 备注
- [ ] 提交后调用 `POST /v1/data/{record_id}/annotate`
- [ ] 标注成功后刷新列表，Toast 提示成功
- [ ] 顶部展示标注统计卡片（调用 `GET /v1/data/annotation_stats`）：
  - 总记录数、已标注数、待标注数、标注完成率
  - 意图分布 Top 5（横向柱状图或标签列表）
  - 情绪分布（饼图或标签色块）

### AC-3：Prompt 管理界面（`/prompts`）

- [ ] 页面展示 Prompt 模板列表（调用 `GET /v1/prompts`）
- [ ] 列表字段：ID、名称、分类、版本、描述
- [ ] 支持按分类筛选（system / user / assistant / tool / rag / sales / voice）
- [ ] 支持新增 Prompt：Modal 表单
  - `id`：Input（必填，唯一标识）
  - `name`：Input（必填）
  - `category`：Select（7 大分类）
  - `template`：TextArea YAML 模板内容
  - `variables`：动态表单（key + default_value + description）
  - `description`：TextArea
- [ ] 提交后调用 `POST /v1/prompts`
- [ ] 支持删除：Popconfirm 确认后调用 `DELETE /v1/prompts/{prompt_id}`
- [ ] 点击「预览」展开行内区域：
  - 左侧：YAML 模板只读展示（monaco-editor 或预格式化文本）
  - 右侧：变量输入表单 +「渲染」按钮
  - 渲染结果展示：调用 `POST /v1/prompts/{prompt_id}/render`
- [ ] 支持按名称搜索

### AC-4：API Key 管理（`/auth/keys`）

- [ ] 页面展示 API Key 列表（调用 MCP HUB Admin API：`GET /api/v1/admin/api-keys`）
- [ ] 列表字段：Key ID、项目名称、状态（active/disabled）、创建时间、日配额、月配额
- [ ] 支持新增 Key：Modal 表单
  - `project_name`：Input（必填）
  - `daily_limit`：InputNumber
  - `monthly_limit`：InputNumber
  - `alert_threshold`：Slider 0-100%
- [ ] 提交后调用 `POST /api/v1/admin/api-keys`
- [ ] 支持编辑配额：Inline 编辑或 Modal，调用 `PUT /api/v1/admin/api-keys/{key_id}`
- [ ] 支持禁用/启用：Switch 切换状态（soft delete，status='deleted' / 'active'）
- [ ] 支持复制 Key 到剪贴板（只展示部分，如 `kk_live_xxxx...xxxx`）
- [ ] 支持按项目名称搜索

### AC-5：路由与菜单

- [ ] App.tsx ProLayout route 配置新增：
  ```ts
  { path: "/monitor", name: "服务监控", icon: <MonitorOutlined /> },
  { path: "/data/annotation", name: "数据标注", icon: <EditOutlined /> },
  { path: "/prompts", name: "Prompt 管理", icon: <FileTextOutlined /> },
  { path: "/auth/keys", name: "API Key", icon: <KeyOutlined /> },
  ```
- [ ] Routes 注册对应的页面组件
- [ ] 菜单点击正常导航

### AC-6：API 封装

- [ ] `src/services/monitor.ts`：封装 6 个服务的 health 接口
- [ ] `src/services/annotation.ts`：封装 pending_annotation / annotate / annotation_stats
- [ ] `src/services/prompt.ts`：封装 prompts list / get / render / register / delete
- [ ] `src/services/apiKey.ts`：封装 api-keys CRUD（对接 mcp-hub Admin API）
- [ ] 所有 API 文件统一使用 `request<T>` 工具函数（参考 `services/quota.ts`）
- [ ] 所有接口定义完整的 TypeScript 类型

### AC-7：测试

- [ ] `src/test/pages/monitor.test.tsx`：监控卡片渲染测试
- [ ] `src/test/pages/annotation.test.tsx`：标注表单提交测试（mock API）
- [ ] `src/test/pages/prompts.test.tsx`：Prompt 列表渲染测试
- [ ] `src/test/pages/apiKeys.test.tsx`：API Key 表格渲染测试
- [ ] `src/test/services/*.test.tsx`：各 API 封装测试（mock fetch）
- [ ] `pnpm test:unit` 全部通过
- [ ] `pnpm typecheck` 无类型错误

### AC-8：类型检查与代码质量

- [ ] 所有新增文件使用 TypeScript Strict
- [ ] 无 `any` 类型（除非第三方库无类型定义）
- [ ] ESLint 无错误，`pnpm lint` 通过
- [ ] 暗色模式兼容（使用 Ant Design token 或 CSS Variables）

---

## 4. 技术方案

### 文件变更清单

```
apps/web-admin/src/
├── services/
│   ├── monitor.ts              # 新增：6 个服务 health API
│   ├── annotation.ts           # 新增：数据标注 API
│   ├── prompt.ts               # 新增：Prompt 管理 API
│   └── apiKey.ts               # 新增：API Key 管理 API
├── pages/
│   ├── monitor/
│   │   └── index.tsx           # 新增：服务监控看板
│   ├── annotation/
│   │   └── index.tsx           # 新增：数据标注界面
│   ├── prompts/
│   │   └── index.tsx           # 新增：Prompt 管理界面
│   └── apiKeys/
│       └── index.tsx           # 新增：API Key 管理界面
├── test/
│   ├── pages/
│   │   ├── monitor.test.tsx    # 新增
│   │   ├── annotation.test.tsx # 新增
│   │   ├── prompts.test.tsx    # 新增
│   │   └── apiKeys.test.tsx    # 新增
│   └── services/               # 新增目录
│       ├── monitor.test.ts
│       ├── annotation.test.ts
│       ├── prompt.test.ts
│       └── apiKey.test.ts
└── App.tsx                     # 修改：新增路由和菜单
```

### API 对接清单

| 前端模块    | 调用 API                        | 服务端点            |
| ----------- | ------------------------------- | ------------------- |
| 监控看板    | GET /health                     | 6 个服务各自端口    |
| 数据标注    | GET /v1/data/pending_annotation | service-data:9005   |
| 数据标注    | POST /v1/data/{id}/annotate     | service-data:9005   |
| 数据标注    | GET /v1/data/annotation_stats   | service-data:9005   |
| Prompt 管理 | GET /v1/prompts                 | service-prompt:9004 |
| Prompt 管理 | POST /v1/prompts                | service-prompt:9004 |
| Prompt 管理 | DELETE /v1/prompts/{id}         | service-prompt:9004 |
| Prompt 管理 | POST /v1/prompts/{id}/render    | service-prompt:9004 |
| API Key     | GET /api/v1/admin/api-keys      | mcp-hub:8000        |
| API Key     | POST /api/v1/admin/api-keys     | mcp-hub:8000        |
| API Key     | PUT /api/v1/admin/api-keys/{id} | mcp-hub:8000        |

**注意**：监控看板需要直接调用 6 个不同端口的 `/health`，其他模块统一走 mcp-hub:8000 代理。

### monitor.ts 核心设计

```typescript
// src/services/monitor.ts
export interface ServiceHealth {
  name: string;
  port: number;
  url: string;
  status: "ok" | "degraded" | "down";
  version: string;
  metrics: Record<string, unknown>;
  latencyMs: number;
  checkedAt: string;
}

const SERVICES = [
  { name: "MCP HUB", port: 8000, path: "/health" },
  { name: "LLM Gateway", port: 9001, path: "/health" },
  { name: "RAG Service", port: 9002, path: "/health" },
  { name: "Memory Service", port: 9003, path: "/health" },
  { name: "Prompt Center", port: 9004, path: "/health" },
  { name: "Data Center", port: 9005, path: "/health" },
];

export async function checkAllServices(): Promise<ServiceHealth[]> {
  const base = API_BASE.replace(/:\d+$/, ""); // strip port
  return Promise.all(
    SERVICES.map(async (svc) => {
      const start = performance.now();
      try {
        const res = await fetch(`${base}:${svc.port}${svc.path}`, {
          signal: AbortSignal.timeout(5000),
        });
        const latency = Math.round(performance.now() - start);
        if (res.ok) {
          const data = await res.json();
          return {
            name: svc.name,
            port: svc.port,
            url: `${base}:${svc.port}`,
            status: "ok" as const,
            version: data.version || "unknown",
            metrics: data,
            latencyMs: latency,
            checkedAt: new Date().toISOString(),
          };
        }
        return {
          name: svc.name,
          port: svc.port,
          url: `${base}:${svc.port}`,
          status: "degraded" as const,
          version: "unknown",
          metrics: {},
          latencyMs: latency,
          checkedAt: new Date().toISOString(),
        };
      } catch {
        return {
          name: svc.name,
          port: svc.port,
          url: `${base}:${svc.port}`,
          status: "down" as const,
          version: "unknown",
          metrics: {},
          latencyMs: -1,
          checkedAt: new Date().toISOString(),
        };
      }
    }),
  );
}
```

### 约束条件

- [ ] 监控看板直接访问各服务端点（非代理），因为 mcp-hub 可能本身故障需要被监控
- [ ] 所有 API 调用统一使用 `request<T>` 封装（monitor.ts 除外，因需直接访问不同端口）
- [ ] 页面加载状态使用 ProTable / ProCard 的 loading 属性或 Spin
- [ ] 错误处理统一：try/catch + message.error() + 控制台日志
- [ ] 表单提交按钮需防重复点击（Button loading 状态）
- [ ] 暗色模式使用 Ant Design 的 `useToken()` 或 CSS Variables，禁止硬编码颜色
- [ ] 响应式布局：ProLayout 自动处理侧边栏，内容区使用 ProCard 的 responsive gutter

---

## 5. 依赖与阻塞

| 依赖项                    | 状态      | 说明                     |
| ------------------------- | --------- | ------------------------ |
| mcp-hub (TASK-400)        | ✅ 已完成 | Admin API /health        |
| service-llm (TASK-401)    | ✅ 已完成 | /health 返回模型数       |
| service-rag (TASK-402)    | ✅ 已完成 | /health 返回集合数       |
| service-memory (TASK-403) | ✅ 已完成 | /health 返回热记忆数     |
| service-prompt (TASK-404) | ✅ 已完成 | /v1/prompts 全 CRUD      |
| service-data (TASK-405)   | ✅ 已完成 | /v1/data/annotate 等     |
| web-admin 基础框架        | ✅ 已完成 | React + AntD + ProLayout |

---

## 6. 风险与应对

| 风险                         | 影响 | 应对策略                                                     |
| ---------------------------- | ---- | ------------------------------------------------------------ |
| 后端服务未启动导致 API 失败  | 高   | 监控看板独立调用，失败时显示 down 状态；其他页面错误边界处理 |
| 跨端口请求 CORS 问题         | 中   | 各后端服务已配置 CORS allow_origins=["*"]                    |
| Prompt YAML 编辑器实现复杂   | 中   | 第一阶段用 TextArea，第二阶段可集成 @monaco-editor/react     |
| 大量测试文件导致执行时间变长 | 低   | 并行执行，vitest 默认并行                                    |

---

## 7. Prompt

```markdown
【Situation】
AI 中台 web-admin 前端需要新增 4 个功能模块：服务监控看板、数据标注、Prompt 管理、API Key 管理。
后端 6 个服务（TASK-400~405）已全部就绪并提供 API。

【Task】
实现 TASK-407：web-admin 前端增强。

【Action】

1. 创建 API 封装文件：
   - src/services/monitor.ts（6 个服务 health 检查）
   - src/services/annotation.ts（数据标注）
   - src/services/prompt.ts（Prompt CRUD + 渲染）
   - src/services/apiKey.ts（API Key CRUD）

2. 创建页面组件：
   - src/pages/monitor/index.tsx（服务监控卡片 + 自动刷新）
   - src/pages/annotation/index.tsx（待标注列表 + 标注 Drawer + 统计卡片）
   - src/pages/prompts/index.tsx（Prompt 列表 + 新增 Modal + 预览区）
   - src/pages/apiKeys/index.tsx（API Key 表格 + 新增/编辑/禁用）

3. 更新 App.tsx：
   - route 配置新增 4 个菜单项
   - Routes 注册 4 个页面组件

4. 编写测试：
   - pages/ 下 4 个页面测试
   - services/ 下 4 个 API 测试

5. 运行验证：
   - pnpm typecheck
   - pnpm test:unit

【Constraint】

- React 18 + TypeScript Strict + Ant Design 6 + ProComponents 2
- react-router-dom v7
- 监控看板直接访问各服务端点（非代理）
- 暗色模式兼容
- 禁止修改与 TASK 无关的文件

【Verification】

- pnpm typecheck（无类型错误）
- pnpm test:unit（全部通过）
- pnpm lint（无 ESLint 错误）
- 浏览器验证：菜单点击正常导航，各页面数据加载正常
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
