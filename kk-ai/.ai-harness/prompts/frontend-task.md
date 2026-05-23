# 前端任务 Prompt 模板

## Situation

项目是 React 18 + TypeScript + Ant Design Pro，Monorepo 结构。
前端应用在 `apps/web-admin/`。

## Task

{task_description}

## Action

1. 在指定目录创建/修改文件
2. 优先使用 Ant Design Pro 组件，其次用 antd，最后自定义
3. 样式方案：antd ConfigProvider 主题，不直接使用 Tailwind/CSS Modules
4. 类型定义优先放在 `packages/types/src/`

## Constraint

- [ ] 不使用 `any` 类型
- [ ] 所有函数必须有 JSDoc 注释
- [ ] 错误处理使用 `message.error()`
- [ ] 表格列定义提取为独立 `const columns` 变量
- [ ] Loading 状态使用组件内置属性
- [ ] 从 URL 参数读取值时必须处理 `undefined` 情况

## Verification

```bash
cd apps/web-admin
pnpm run typecheck
pnpm run test
pnpm run build
pnpm run lint
```
