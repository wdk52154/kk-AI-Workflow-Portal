# TASK-100：配额管理页面

## 元信息

| 字段     | 值                               |
| -------- | -------------------------------- |
| TASK ID  | TASK-100                         |
| 标题     | 实现配额管理页面                 |
| 负责人   | @frontend-lead                   |
| 优先级   | P1                               |
| 预估工时 | 3h                               |
| 关联需求 | 管理后台需要展示项目配额使用情况 |

---

## 1. 背景（Situation）

康康 AI 为多个项目提供 API 服务，每个项目有每日/每月调用配额。管理后台需要一张页面展示所有项目的配额使用情况，方便运营人员监控和预警。

---

## 2. 目标（Task）

在管理后台新增 `/quota` 路由页面，展示配额 KPI 卡片 + 项目配额明细表格。

---

## 3. 验收标准（Acceptance Criteria）

- [ ] AC-1：页面顶部展示 4 张 StatisticCard（今日总调用、本月总调用、配额使用率、超限项目数）
- [ ] AC-2：ProTable 展示各项目配额明细（项目名称、今日调用/上限、本月调用/上限、使用率、状态）
- [ ] AC-3：使用率 >= 80% 用黄色 Tag 标记，>= 100% 用红色 Tag 标记
- [ ] AC-4：支持按项目名称搜索（ProTable 内置 search）
- [ ] AC-5：表格支持按使用率排序
- [ ] AC-6：数据从后端 `GET /quota` 接口获取（接口已就绪）
- [ ] AC-7：响应式：桌面端完整表格，移动端卡片列表
- [ ] AC-8：`pnpm run typecheck && pnpm run test:unit` 通过

---

## 4. 技术方案（Action）

### 4.1 文件变更

```
新增：
- apps/web-admin/src/pages/quota/index.tsx      # 页面组件
- apps/web-admin/src/pages/quota/hooks.ts        # useQuotaData hook
- apps/web-admin/src/test/pages/quota.test.tsx   # 单元测试

修改：
- apps/web-admin/src/App.tsx                     # 添加 /quota 路由
```

### 4.2 API 接口

```typescript
// GET /quota
interface QuotaResponse {
  summary: {
    todayTotal: number;
    monthTotal: number;
    avgUsageRate: number;
    exceededCount: number;
  };
  projects: Array<{
    projectId: string;
    projectName: string;
    todayUsed: number;
    todayLimit: number;
    monthUsed: number;
    monthLimit: number;
    usageRate: number; // 0-100
    status: "normal" | "warning" | "exceeded";
  }>;
}
```

### 4.3 组件结构

```
QuotaPage
├── StatisticCard.Group（4 张 KPI）
├── ProTable（配额明细）
│   ├── 搜索栏（项目名称）
│   ├── 列：名称 | 今日 | 本月 | 使用率 | 状态
│   └── 分页（pageSize: 10）
└── useQuotaData hook（useRequest 封装）
```

### 4.4 约束条件

- [ ] 不使用 any 类型
- [ ] 表格列定义提取为 `const columns` 变量
- [ ] Loading 状态使用 ProTable 内置 `loading` 属性
- [ ] 错误处理：`message.error('获取配额数据失败')`
- [ ] 空状态：ProTable 内置 `toolBarRender` 配置
- [ ] 从 URL 读取参数时必须做非空断言处理

---

## 5. 依赖与阻塞

| 依赖项              | 状态      | 说明                     |
| ------------------- | --------- | ------------------------ |
| 后端 API GET /quota | ✅ 已完成 | services/mcp-hub 已提供  |
| @kk-ai/types        | ✅ 已完成 | QuotaResponse 类型已定义 |
| Ant Design Pro      | ✅ 已安装 | ProTable + StatisticCard |

---

## 6. 测试策略

### 6.1 单元测试

```typescript
// src/test/pages/quota.test.tsx
describe("QuotaPage", () => {
  it("renders KPI cards", () => {
    // 断言 4 张 StatisticCard 渲染
  });

  it("renders project table", () => {
    // 断言 ProTable 渲染，包含列头
  });

  it("marks exceeded projects in red", () => {
    // mock 数据包含 exceeded 项目
    // 断言红色 Tag 存在
  });
});
```

### 6.2 集成测试

```bash
# 启动服务后访问
curl http://localhost:5173/quota
# 页面应展示 KPI 和表格
```

---

## 7. 给 AI 的 Prompt

```markdown
【Situation】
项目是 React 18 + TypeScript + Ant Design Pro Monorepo。
需要在管理后台新增"配额管理"页面，路径 /quota。

【Task】
实现配额管理页面，详见 TASK-100。

【Action】

1. 创建 apps/web-admin/src/pages/quota/index.tsx
2. 顶部用 StatisticCard.Group 展示 4 个 KPI（今日总调用、本月总调用、配额使用率、超限项目数）
3. 下方用 ProTable 展示项目配额明细
4. 列：projectName, todayUsed/todayLimit, monthUsed/monthLimit, usageRate, status
5. usageRate >= 80% 黄色 Tag，>= 100% 红色 Tag
6. 支持按 projectName 搜索和按 usageRate 排序
7. 数据通过 fetch GET /quota 获取，类型使用 QuotaResponse
8. 修改 App.tsx 添加 /quota 路由

【Constraint】

- 不使用 any
- 表格列定义提取为 const columns
- Loading 用 ProTable loading 属性
- 错误处理：message.error()

【Verification】

- pnpm run typecheck
- pnpm run test:unit
- pnpm run build
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |

---

## 9. 复盘

[任务完成后填写]
