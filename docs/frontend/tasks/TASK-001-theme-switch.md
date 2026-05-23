# TASK-001：主题切换功能实现

## 元信息

| 字段 | 值 |
|------|---|
| TASK ID | TASK-001 |
| 标题 | 管理后台主题切换（light / dark / system） |
| 负责人 | @frontend-lead |
| 优先级 | P1 |
| 预估工时 | 2h |
| 关联 ARCH | docs/frontend/monorepo-initialization.md |

---

## 1. 背景

管理后台需要支持亮色、暗色、跟随系统三种主题模式，提升用户体验。

---

## 2. 目标

实现主题切换功能，切换后全局样式（包括 Ant Design 组件和自定义 CSS Variables）同步响应。

---

## 3. 验收标准

- [ ] AC-1：页面右上角有主题切换按钮，支持 light / dark / system 三模式
- [ ] AC-2：切换主题后，Ant Design 组件同步切换（使用 ConfigProvider algorithm）
- [ ] AC-3：切换主题后，自定义 CSS Variables（background、foreground 等）同步切换
- [ ] AC-4：主题偏好持久化到 localStorage，刷新后恢复
- [ ] AC-5：`pnpm run typecheck` 和 `pnpm run build` 通过

---

## 4. 技术方案

### 4.1 文件变更

```
新增：
- apps/web-admin/src/main.tsx 中的 ThemeWrapper 逻辑

修改：
- packages/ui/src/styles/globals.css（CSS Variables 定义）
- apps/web-admin/src/App.tsx（主题切换 UI）
```

### 4.2 关键逻辑

```typescript
// 伪代码：主题状态管理
const [theme, setTheme] = useState<Theme>(loadFromStorage() || 'system');

useEffect(() => {
  const resolved = theme === 'system' ? getSystemTheme() : theme;
  document.documentElement.classList.remove('light', 'dark');
  document.documentElement.classList.add(resolved);
  
  // Ant Design 主题
  ConfigProvider.config({
    theme: { algorithm: resolved === 'dark' ? darkAlgorithm : defaultAlgorithm }
  });
}, [theme]);
```

### 4.3 约束条件

- [ ] 不使用 Redux / Zustand 等外部状态库，用 React useState + Context 即可
- [ ] ThemeProvider 封装在 @kk-ai/ui 中，可被其他应用复用
- [ ] CSS Variables 定义在 packages/ui/src/styles/globals.css 中

---

## 5. 依赖与阻塞

| 依赖项 | 状态 | 说明 |
|--------|------|------|
| Ant Design | ✅ 已安装 | v6.x |
| @kk-ai/ui | ✅ 已就绪 | 共享 UI 包 |

---

## 6. 测试策略

- [ ] 点击主题切换按钮，观察页面背景色变化
- [ ] 刷新页面，确认主题偏好恢复
- [ ] 切换系统主题（macOS 系统偏好），确认 system 模式响应

---

## 7. 给 AI 的 Prompt

```markdown
【Situation】
项目使用 React 18 + TypeScript + Ant Design Pro，Monorepo 结构。
主题状态需要在 apps/web-admin 中管理，样式变量在 packages/ui 中定义。

【Task】
实现主题切换功能，支持 light / dark / system 三种模式。

【Action】
1. 在 main.tsx 中使用 ConfigProvider + ProConfigProvider 包裹应用
2. theme 状态使用 useState，持久化到 localStorage（key: kk-ai-theme）
3. system 模式监听 prefers-color-scheme 变化
4. 将 theme / setTheme / toggleTheme 通过 props 传给 App 组件
5. CSS Variables 已在 packages/ui/src/styles/globals.css 中定义好 light/dark

【Result】
- typecheck 通过
- build 通过
- 主题切换流畅，无闪烁
```

---

## 8. 迭代记录

| 轮次 | AI 输出 | 人验收结果 | 修复点 |
|------|---------|-----------|--------|
| R1 | 初始实现 | ✅ 通过 | - |

---

## 9. 复盘

- Ant Design 6 的 ConfigProvider 直接使用 `theme.algorithm` 即可，无需额外包
- 将 ThemeProvider 逻辑内嵌在 main.tsx 中比放在 @kk-ai/ui 中更简洁（仅 web-admin 需要）
