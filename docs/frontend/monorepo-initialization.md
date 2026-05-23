# AI 前端 Monorepo 初始化文档分析

> 项目：康康 AI 全栈系统（kk-ai）  
> 文档版本：v1.1（CSS Modules 方案）  
> 适用范围：前端 Monorepo 架构设计、初始化与团队协作规范

---

## 一、项目概述

本项目采用 **Monorepo** 架构管理前端应用与共享资源，核心目标：

- **代码复用**：类型定义、UI 组件、工具函数跨应用共享
- **统一管控**：依赖版本、构建流程、代码规范集中管理
- **独立部署**：各应用（web-admin、未来扩展）可独立构建与发布
- **类型安全**：全链路 TypeScript 严格模式覆盖
- **样式隔离**：CSS Modules 保证组件样式作用域隔离

---

## 二、技术栈选型

| 层级 | 技术 | 版本 | 职责 |
|------|------|------|------|
| 包管理 | pnpm | 9.x | workspace 依赖管理与磁盘去重 |
| 构建编排 | Turbo | 2.x | 任务缓存与并行构建加速 |
| 前端框架 | React | 18.x | UI 组件与页面渲染 |
| 构建工具 | Vite | 5.x | 应用与组件库的快速构建（内置 CSS Modules 支持） |
| 类型系统 | TypeScript | 5.4+ | 全链路类型检查 |
| 样式方案 | CSS Modules | 原生 | 组件级样式隔离，避免全局污染 |
| 主题系统 | CSS Variables | 原生 | 亮色/暗色主题动态切换 |
| 类名合并 | clsx | 2.x | 条件类名组合工具 |

---

## 三、Monorepo 目录结构

```
kk-ai/                          # Monorepo 根目录
├── apps/
│   └── web-admin/              # 管理后台应用（Vite + React）
│       ├── src/
│       │   ├── App.tsx
│       │   ├── App.module.css          # 页面级 CSS Modules
│       │   ├── css-modules.d.ts        # CSS Modules 类型声明
│       │   ├── main.tsx
│       │   └── index.css               # 全局样式入口
│       ├── tsconfig.json
│       ├── vite.config.ts
│       └── package.json
├── packages/
│   ├── types/                  # 共享类型定义（纯 TS）
│   ├── ui/                     # 共享 UI 组件库
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── button.tsx
│   │   │   │   ├── button.module.css   # 组件级 CSS Modules
│   │   │   │   └── theme-provider.tsx
│   │   │   ├── lib/
│   │   │   │   └── utils.ts            # cn() 工具（clsx 版）
│   │   │   ├── styles/
│   │   │   │   ├── globals.css         # CSS Variables 设计系统
│   │   │   │   └── css-modules.d.ts    # CSS Modules 类型声明
│   │   │   └── index.ts
│   │   └── vite.config.ts
│   └── utils/                  # 共享工具函数（纯 TS）
├── pnpm-workspace.yaml
├── turbo.json
├── tsconfig.base.json
├── package.json
└── .gitignore
```

### 3.1 Workspace 声明（pnpm-workspace.yaml）

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**设计要点**：
- `apps/*`：面向用户的前端应用，可独立部署
- `packages/*`：内部共享包，不直接对外发布（通过 `workspace:*` 引用）

---

## 四、TypeScript 配置策略（继承化设计）

### 4.1 核心原则：一基座 + 多覆盖

避免每个项目复制粘贴相同的 `compilerOptions`，采用 **基座继承 + 局部覆盖** 模式：

```
tsconfig.base.json          # 共享核心规则
    ├── apps/web-admin/tsconfig.json      # 应用：noEmit + jsx
    ├── packages/ui/tsconfig.json         # 组件库：outDir + jsx
    ├── packages/types/tsconfig.json      # 类型包：outDir
    └── packages/utils/tsconfig.json      # 工具包：outDir
```

### 4.2 基座配置（tsconfig.base.json）

```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

### 4.3 ⚠️ 重要约束

`allowImportingTsExtensions` **只能在 `noEmit` 或 `emitDeclarationOnly` 时使用**。因此：

- ✅ 应用级（`noEmit: true`）可以使用
- ❌ 库级（需要输出完整 JS）**不能**在基座中开启，否则 `tsc` 编译报错

### 4.4 CSS Modules 类型声明

每个使用 CSS Modules 的项目需创建类型声明文件：

```ts
// src/css-modules.d.ts（或 packages/ui/src/styles/css-modules.d.ts）
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}
```

确保 `.d.ts` 文件位于 `tsconfig.json` 的 `include` 范围内（如 `src/**/*`）。

---

## 五、样式方案：CSS Modules + CSS Variables

### 5.1 为什么不用 Tailwind CSS？

| 维度 | Tailwind CSS | CSS Modules |
|------|-------------|-------------|
| 样式隔离 | 依赖类名约定，易冲突 | 编译时自动哈希，天然隔离 |
| 可读性 | 类名冗长，HTML 臃肿 | 语义化命名，结构清晰 |
| 调试 | 需映射原子类到实际样式 | 浏览器 DevTools 直接查看 |
| 构建体积 | 需 PurgeCSS 优化 | 仅打包使用到的样式 |
| 团队协作 | 需全员熟悉工具类命名 | 标准 CSS，上手零成本 |

### 5.2 设计系统：CSS Variables

全局主题变量统一定义在 `packages/ui/src/styles/globals.css`：

```css
:root {
  --background: #ffffff;
  --foreground: #09090b;
  --primary: #18181b;
  --primary-foreground: #fafafa;
  --secondary: #f4f4f5;
  --secondary-foreground: #18181b;
  --muted: #f4f4f5;
  --muted-foreground: #71717a;
  --accent: #f4f4f5;
  --accent-foreground: #18181b;
  --destructive: #ef4444;
  --destructive-foreground: #fafafa;
  --border: #e4e4e7;
  --input: #e4e4e7;
  --ring: #18181b;
  --radius: 0.5rem;
}

.dark {
  --background: #09090b;
  --foreground: #fafafa;
  /* ... 暗色主题变量覆盖 */
}
```

**主题切换原理**：`theme-provider.tsx` 通过切换 `document.documentElement` 的 `className`（`light` / `dark`），CSS Variables 自动响应变化。

### 5.3 组件样式：CSS Modules

以 Button 组件为例：

```tsx
// packages/ui/src/components/button.tsx
import styles from './button.module.css';

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'default', size = 'md', className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(styles.button, styles[variant], styles[size], className)}
        {...props}
      />
    );
  }
);
```

```css
/* packages/ui/src/components/button.module.css */
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: background-color 0.2s, color 0.2s;
}

.default {
  background-color: var(--primary);
  color: var(--primary-foreground);
}

.default:hover:not(:disabled) {
  background-color: hsl(from var(--primary) h s calc(l - 0.1));
}

.sm { height: 2rem; padding: 0 0.75rem; font-size: 0.75rem; }
.md { height: 2.5rem; padding: 0.5rem 1rem; }
```

**CSS Modules 优势**：
- `.button` 编译后变为 `.button_hash123`，避免全局命名冲突
- 支持 `:hover`、`:focus-visible`、`@keyframes` 等原生 CSS 特性
- Vite 原生支持，无需额外配置

### 5.4 类名合并工具（cn）

```ts
// packages/ui/src/lib/utils.ts
import { type ClassValue, clsx } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}
```

**说明**：移除 `tailwind-merge` 后，`cn` 仅使用 `clsx` 处理条件类名和数组展开。在 CSS Modules 方案中，样式冲突由模块作用域天然解决，无需运行时合并类名优先级。

### 5.5 全局样式导入

应用入口导入 UI 库的全局 CSS Variables：

```css
/* apps/web-admin/src/index.css */
@import '@kk-ai/ui/globals.css';
```

`packages/ui/package.json` 配置 exports：

```json
{
  "exports": {
    ".": { "types": "./dist/index.d.ts", "default": "./dist/index.js" },
    "./globals.css": "./src/styles/globals.css"
  }
}
```

---

## 六、忽略文件策略（分层 .gitignore）

Monorepo 采用 **根级通用 + 子项目特定** 的分层策略：

### 6.1 根级 .gitignore（kk-ai/.gitignore）

```gitignore
# Dependencies
node_modules/

# Build outputs
dist/
build/
*.tsbuildinfo

# Turbo
.turbo/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/*
*.swp

# OS
.DS_Store

# Logs
*.log

# Testing
coverage/

# Cache
.eslintcache
*.cache
```

### 6.2 应用级 .gitignore（apps/web-admin/.gitignore）

```gitignore
# Vite
.vite/
vite.config.ts.timestamp-*

# Local env files
.env.*.local
```

### 6.3 分层策略的优势

| 层级 | 职责 | 示例 |
|------|------|------|
| 根级 | 全仓库通用 | `node_modules`、`.env`、`.DS_Store` |
| 应用级 | 构建工具特定 | `.vite/`、`.react-router/` |
| 包级 | 库输出控制 | `dist/`（根级已覆盖，但显式声明更清晰） |

---

## 七、Turbo 任务管道配置

### 7.1 turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "typecheck": {
      "dependsOn": ["^build"]
    }
  }
}
```

### 7.2 任务依赖解析

```
typecheck ──> ^build ──> 先构建所有依赖包（types/utils/ui）
                         再对当前应用执行 tsc --noEmit

build ──> ^build ──> 按依赖拓扑顺序构建（types → utils → ui → web-admin）
```

---

## 八、共享包设计

### 8.1 @kk-ai/types（类型定义包）

纯类型定义，无运行时代码，构建后仅输出 `.d.ts`。

### 8.2 @kk-ai/ui（UI 组件库）

```ts
// packages/ui/src/index.ts
export { cn } from './lib/utils';
export { ThemeProvider, useTheme } from './components/theme-provider';
export { Button } from './components/button';

import './styles/globals.css';
```

**构建配置要点**：
- `vite-plugin-dts` 自动生成 `.d.ts` 声明文件
- CSS Modules 文件由 Vite 自动处理，无需额外 loader
- CSS 被内联到 `dist/index.js`，应用导入 JS 时自动注入样式

### 8.3 @kk-ai/utils（工具函数包）

纯工具函数，无 UI 依赖。

### 8.4 Workspace 依赖引用

```json
// apps/web-admin/package.json
{
  "dependencies": {
    "@kk-ai/types": "workspace:*",
    "@kk-ai/ui": "workspace:*",
    "@kk-ai/utils": "workspace:*",
    "react": "^18.2.0"
  }
}
```

`workspace:*` 表示始终使用本地 workspace 中的最新版本，无需手动维护版本号。

---

## 九、初始化与日常开发流程

### 9.1 首次初始化

```bash
# 1. 安装根依赖（自动安装所有 workspace 依赖）
pnpm install

# 2. 验证类型检查
pnpm run typecheck

# 3. 验证构建
pnpm run build
```

### 9.2 日常开发

```bash
# 启动所有应用的 dev 服务（turbo 并行）
pnpm run dev

# 仅构建某个应用
pnpm --filter @kk-ai/web-admin run build

# 添加依赖到特定包
pnpm --filter @kk-ai/ui add lodash-es
pnpm --filter @kk-ai/ui add -D @types/lodash-es
```

### 9.3 添加新应用/包

```bash
# 新增前端应用
cd apps
mkdir web-portal
cd web-portal
pnpm init
```

**必须配置**：
1. 在 `pnpm-workspace.yaml` 中确认路径匹配（已通配无需修改）
2. 创建 `tsconfig.json` 继承 `../../tsconfig.base.json`
3. 创建 `.gitignore`（建议从现有包复制）
4. 创建 `src/css-modules.d.ts`（如使用 CSS Modules）
5. 在 `turbo.json` 中添加需要的新任务（如有）

---

## 十、最佳实践清单

### 10.1 ✅ 推荐做法

| 实践 | 说明 |
|------|------|
| TS 严格模式 | 基座开启 `strict: true`，全链路覆盖 |
| 配置继承 | 所有子项目 `extends` 基座，避免重复 |
| 分层 .gitignore | 根级通用 + 项目级特定 |
| CSS Modules 隔离 | 每个组件配套 `.module.css`，禁止全局类名 |
| CSS Variables 主题 | 通过切换 `html` 的 class 实现无闪烁主题切换 |
| workspace 协议 | 内部包使用 `workspace:*` 引用 |
| 类型优先 | 先定义 `@kk-ai/types`，再实现功能 |
| 库 external React | UI 包不打包 React，避免多实例 |
| Turbo 缓存 | 利用 `dependsOn` 和缓存加速 CI |

### 10.2 ❌ 避免事项

| 反模式 | 风险 |
|--------|------|
| 在基座中开启 `allowImportingTsExtensions` | 库级 `tsc` 编译会报错 |
| 忽略 `.gitignore` | `node_modules` / `dist` 可能误提交 |
| 使用裸 CSS（非 Modules）写组件样式 | 全局命名冲突，维护困难 |
| 在组件中硬编码颜色值 | 破坏主题切换一致性 |
| 跨包直接相对路径引用 | 破坏封装，应使用包名导入 |

---

## 十一、后续扩展方向

| 方向 | 建议 |
|------|------|
| ESLint / Prettier | 根级统一配置，子项目继承 |
| 单元测试 | 引入 Vitest + React Testing Library |
| Storybook | 为 `@kk-ai/ui` 建立组件文档站 |
| CI/CD | GitHub Actions + Turbo Remote Cache |
| 后端对接 | `services/` 目录初始化 API 服务 |
| 路径别名 | 统一 `@/` 指向各包 `src` 目录 |
| PostCSS 插件 | 按需引入 `autoprefixer`、`postcss-nested` 等 |

---

## 附录：文件索引

| 文件 | 路径 | 作用 |
|------|------|------|
| 包管理配置 | `pnpm-workspace.yaml` | 声明 workspace 范围 |
| 构建编排 | `turbo.json` | Turbo 任务管道 |
| TS 基座 | `tsconfig.base.json` | 共享编译器选项 |
| 根忽略 | `.gitignore` | 全局忽略规则 |
| CSS Variables | `packages/ui/src/styles/globals.css` | 设计系统主题变量 |
| CSS Modules 声明 | `packages/ui/src/styles/css-modules.d.ts` | 模块类型声明 |
| 应用 TS | `apps/*/tsconfig.json` | 应用级 TS 配置 |
| 包 TS | `packages/*/tsconfig.json` | 库级 TS 配置 |
| Button 组件 | `packages/ui/src/components/button.tsx` | CSS Modules 示例组件 |
| Button 样式 | `packages/ui/src/components/button.module.css` | 组件级隔离样式 |
