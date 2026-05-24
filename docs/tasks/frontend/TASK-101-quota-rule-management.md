# TASK-101: 配额规则管理页面

## 元信息

| 字段 | 值 |
|------|-----|
| **ID** | TASK-101 |
| **Type** | frontend |
| **Est** | 3h |
| **Priority** | P1 |
| **Depends On** | TASK-100（配额展示页面） |
| **Author** | @dekang |
| **Created** | 2026-05-23 |

---

## 背景与目标

TASK-100 完成了配额数据的**只读展示**。本 TASK 在前端实现配额规则的**全生命周期管理**——管理员可以在页面上直接创建、编辑、删除配额规则，无需操作数据库。

**目标**：提供一个完整的配额规则配置界面，与后端 API 对接。

---

## 验收标准（AC）

### AC-1: 路由与菜单

- [ ] 在 `/quota/rules` 路径新增"规则配置"页面
- [ ] `App.tsx` 中 ProLayout 菜单添加"规则配置"项，图标使用 `<SettingOutlined />`
- [ ] 菜单结构：
  - 配额管理（父菜单，图标 `<DatabaseOutlined />`）
    - 数据概览 → `/quota`（TASK-100 已有）
    - 规则配置 → `/quota/rules`（本 TASK 新增）

### AC-2: 配额规则列表

- [ ] 使用 ProTable 展示配额规则列表
- [ ] 表格列定义：
  | 列名 | 数据字段 | 说明 |
  |------|---------|------|
  | 项目名称 | `project_name` | 可搜索 |
  | 日限额 | `daily_limit` | 数字，千分位格式化 |
  | 月限额 | `monthly_limit` | 数字，千分位格式化 |
  | 告警阈值 | `alert_threshold` | 显示为百分比，如 "80%" |
  | 状态 | `status` | Tag 显示：`active`(绿色) / `deleted`(灰色) |
  | 操作 | - | 编辑 + 删除按钮 |
- [ ] 工具栏右侧显示"新建规则"按钮（蓝色主按钮）
- [ ] 支持按项目名称搜索、按状态筛选
- [ ] 空数据时显示 Empty 占位图

### AC-3: 创建/编辑弹窗

- [ ] 点击"新建规则"或"编辑"打开 Modal（宽度 560px）
- [ ] 表单字段：
  | 字段 | 组件 | 校验规则 |
  |------|------|---------|
  | 项目名称 | Select | 必填，从 `/api/v1/projects` 下拉选择 |
  | 日限额 | InputNumber | 必填，≥ 1，≤ 月限额 |
  | 月限额 | InputNumber | 必填，≥ 日限额 |
  | 告警阈值 | Slider + 数字显示 | 1-100，步长 1，显示 "80%" |
- [ ] 自定义校验：月限额必须 ≥ 日限额，不满足时提示"月限额不能小于日限额"
- [ ] 编辑模式下，项目名称字段禁用（不可修改）
- [ ] 提交成功：`message.success('保存成功')` 并关闭弹窗刷新列表
- [ ] 提交失败：显示后端返回的错误信息

### AC-4: 删除确认

- [ ] 点击删除按钮弹出 `Popconfirm`，文案："确定删除项目 XXX 的配额规则吗？删除后该项目将不再受配额限制。"
- [ ] 确认后调用删除 API，成功提示 `message.success('删除成功')`
- [ ] 删除后列表自动刷新

### AC-5: 数据对接

- [ ] 创建 `src/services/quota.ts` 封装所有配额相关 API：
  ```typescript
  getQuotaRules(params: QueryParams): Promise<QuotaRuleListResponse>
  createQuotaRule(data: QuotaRuleCreate): Promise<QuotaRule>
  updateQuotaRule(id: string, data: QuotaRuleUpdate): Promise<QuotaRule>
  deleteQuotaRule(id: string): Promise<void>
  getProjects(): Promise<string[]> // 用于下拉选择
  ```
- [ ] ProTable 使用 `request` 属性对接分页 API
- [ ] 所有 API 请求统一使用 `@kk-ai/utils` 的 `request` 工具
- [ ] 后端未启动或请求失败时，表格显示错误状态并可重试

### AC-6: 暗色模式兼容

- [ ] 弹窗、表单、表格在暗色模式下文字/边框/背景色正常
- [ ] Slider 轨道颜色随主题切换

### AC-7: 测试覆盖

- [ ] 规则列表渲染测试（mock API 数据）
- [ ] 新建规则弹窗打开/关闭测试
- [ ] 表单校验测试（月限额 < 日限额时应阻止提交）
- [ ] 删除确认弹窗测试
- [ ] 空数据状态测试

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `apps/web-admin/src/pages/quota/rules.tsx` | 新增 | 配额规则管理页面（主文件） |
| `apps/web-admin/src/services/quota.ts` | 新增 | 配额 API 封装 |
| `apps/web-admin/src/App.tsx` | 修改 | 添加 `/quota/rules` 路由和子菜单 |
| `apps/web-admin/src/pages/quota/index.tsx` | 修改 | 父菜单结构改造（如果需要） |
| `apps/web-admin/src/pages/quota/__tests__/rules.test.tsx` | 新增 | 单元测试 |

---

## 技术约束

1. **组件库**：Ant Design 6.x + ProComponents 2.x
2. **路由**：react-router-dom v7，使用 `useNavigate` + `useLocation`
3. **状态管理**：页面级 `useState` + `useEffect`，不引入全局状态
4. **API 封装**：所有请求走 `src/services/quota.ts`，错误统一处理
5. **类型定义**：所有接口必须定义 TypeScript 类型，禁止 `any`
6. **样式**：不使用 Tailwind，使用 Ant Design 内置样式 + 少量 CSS Modules（如需要）

---

## 类型定义

```typescript
// src/services/quota.ts

export interface QuotaRule {
  id: string;
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number; // 1-100
  status: 'active' | 'deleted';
  created_at: string;
  updated_at: string;
}

export interface QuotaRuleListResponse {
  items: QuotaRule[];
  total: number;
  page: number;
  page_size: number;
}

export interface QuotaRuleCreate {
  project_name: string;
  daily_limit: number;
  monthly_limit: number;
  alert_threshold: number;
}

export interface QuotaRuleUpdate {
  daily_limit?: number;
  monthly_limit?: number;
  alert_threshold?: number;
  status?: 'active' | 'deleted';
}

export interface QuotaQueryParams {
  project_name?: string;
  status?: string;
  page?: number;
  page_size?: number;
}
```

---

## 边界条件

| 场景 | 预期行为 |
|------|---------|
| 后端未启动 | 表格显示 `Result` 错误状态，带"重新加载"按钮 |
| 创建重复项目规则 | 后端返回 409，前端 Form.Item 显示错误信息 |
| 日限额 > 月限额 | 前端表单校验拦截，不发送请求 |
| 快速连续点击提交 | Button 显示 loading 状态，防止重复提交 |
| 编辑时后端规则已被删除 | 提交返回 404，提示"规则不存在或已被删除" |
| 项目列表为空 | Select 显示"暂无项目"占位，禁用新建按钮 |

---

## UI 参考

### 列表页布局
```
┌─────────────────────────────────────────────────────┐
│ 配额管理 > 规则配置                     [新建规则]   │
├─────────────────────────────────────────────────────┤
│ 搜索: [项目名称          ] 状态: [全部 ▼]            │
├─────────────────────────────────────────────────────┤
│ 项目名称 │ 日限额 │ 月限额 │ 告警阈值 │ 状态 │ 操作 │
│ projectA │ 1,000 │ 30,000 │   80%   │ 生效 │ ✏️ 🗑 │
│ projectB │ 5,000 │ 100,000│   90%   │ 生效 │ ✏️ 🗑 │
├─────────────────────────────────────────────────────┤
│                          < 1 / 1 >                  │
└─────────────────────────────────────────────────────┘
```

### 弹窗表单
```
┌─────────────────────────────────────┐
│  新建配额规则                    [×] │
├─────────────────────────────────────┤
│  项目名称 *  [请选择项目        ▼]   │
│  日限额 *    [        ] 次/天       │
│  月限额 *    [        ] 次/月       │
│  告警阈值      [━━━━●━━━━]  80%     │
├─────────────────────────────────────┤
│                    [取消]  [确定]    │
└─────────────────────────────────────────────────────┘
```

---

## 实现 Prompt（给 AI 的指令）

```markdown
你是前端工程师，精通 React 18 + TypeScript + Ant Design Pro。

请实现 TASK-101：配额规则管理页面。

**约束**：
1. 严格按 AC 逐条实现，完成后逐项自检
2. 使用现有项目结构（apps/web-admin/），不得修改不相关文件
3. 所有组件使用 TypeScript，禁止 any
4. API 请求统一封装在 src/services/quota.ts
5. 路由使用 react-router-dom v7
6. 表单校验必须包含月限额 ≥ 日限额的自定义规则
7. 暗色模式必须兼容

**特别注意**：
- ProTable 的 request 属性用于分页加载数据
- Modal 的 confirmLoading 用于防止重复提交
- Select 的项目列表先 mock 几个项目名（['project-a', 'project-b', 'project-c']），等后端 TASK 完成后联调
- 删除操作必须使用 Popconfirm 二次确认

**验证**：
完成后执行：
```bash
cd kk-ai/apps/web-admin && pnpm typecheck && pnpm test:unit
```
确保类型检查和单元测试通过。
```

---

## 迭代记录

### Round 1

- **时间**：2026-05-23
- **结果**：待执行
- **问题记录**：
  - 
- **规范升级**：
  - 

---

## 参考

- [TASK-100 配额展示页面](./TASK-100-quota-page.md)
- [前端组件规范](../../engineering/frontend-component-spec.md)
