# AI 前端 Monorepo 初始化文档分析

> 项目：康康 AI 全栈系统（kk-ai）  
> 文档版本：v1.0  
> 适用范围：前端 Monorepo 架构设计、初始化与团队协作规范

---

## 一、项目概述

本项目采用 **Monorepo** 架构管理前端应用与共享资源，核心目标：

- **代码复用**：类型定义、UI 组件、工具函数跨应用共享
- **统一管控**：依赖版本、构建流程、代码规范集中管理
- **独立部署**：各应用（web-admin、未来扩展）可独立构建与发布
- **类型安全**：全链路 TypeScript 严格模式覆盖

---

## 二、技术栈选型

| 层级 | 技术 | 版本 | 职责 |
|------|------|------|------|
| 包管理 | pnpm | 9.x | workspace 依赖管理与磁盘去重 |
| 构建编排 | Turbo | 2.x | 任务缓存与并行构建加速 |
| 前端框架 | React | 18.x | UI 组件与页面渲染 |
| 构建工具 | Vite | 5.x | 应用与组件库的快速构建 |
| 类型系统 | TypeScript | 5.4+ | 全链路类型检查 |
| 样式方案 | Tailwind CSS | 3.4+ | 原子化 CSS + 主题配置 |
| 组件库 | shadcn/ui | - | Headless UI 组件基座 |

---

## 三、Monorepo 目录结构

```
kk-ai/                          # Monorepo 根目录
├── apps/
│   └── web-admin/              # 管理后台应用（Vite + React）
│       ├── src/
│       ├── tsconfig.json       # 继承根配置，noEmit 模式
│       ├── vite.config.ts
│       └── package.json
├── packages/
│   ├── types/                  # 共享类型定义（纯 TS，输出 .d.ts）
│   ├── ui/                     # 共享 UI 组件库（Vite Library Mode）
│   │   ├── src/components/
│   │   ├── src/lib/
│   │   └── vite.config.ts      # vite-plugin-dts 生成声明文件
│   └── utils/                  # 共享工具函数（纯 TS）
├── pnpm-workspace.yaml         # Workspace 范围声明
├── turbo.json                  # 任务管道配置
├── tsconfig.base.json          # 共享 TS 基础配置
├── package.json                # 根依赖与 scripts
└── .gitignore                  # 根级忽略规则
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

**关键选项说明**：

| 选项 | 作用 | 说明 |
|------|------|------|
| `strict: true` | 开启所有严格类型检查 | 包含 `noImplicitAny`、`strictNullChecks` 等 8 项 |
| `noUnusedLocals/Parameters` | 未使用变量/参数报错 | 强制代码整洁，减少冗余 |
| `moduleResolution: bundler` | 适配 Vite/webpack | 支持 `exports` 字段、无扩展名导入 |
| `declaration + declarationMap` | 输出类型声明 | 包级别需要，应用级关闭 |

### 4.3 应用级覆盖（apps/web-admin/tsconfig.json）

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "jsx": "react-jsx",
    "noEmit": true,
    "allowImportingTsExtensions": true,
    "declaration": false,
    "declarationMap": false
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**覆盖逻辑**：
- `noEmit: true`：应用不输出 JS，仅做类型检查，由 Vite 负责编译
- `allowImportingTsExtensions: true`：允许 `.ts`/`.tsx` 扩展名导入（需配合 `noEmit`）
- 关闭 `declaration`：应用不需要对外输出类型声明

### 4.4 库级覆盖（packages/ui/tsconfig.json）

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "jsx": "react-jsx",
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

**覆盖逻辑**：
- 保留基座的 `declaration: true`，输出 `.d.ts` + `.d.ts.map`
- `outDir` / `rootDir`：控制编译输出结构

### 4.5 ⚠️ 重要约束

`allowImportingTsExtensions` **只能在 `noEmit` 或 `emitDeclarationOnly` 时使用**。因此：

- ✅ 应用级（`noEmit: true`）可以使用
- ❌ 库级（需要输出完整 JS）**不能**在基座中开启，否则 `tsc` 编译报错

---

## 五、忽略文件策略（分层 .gitignore）

Monorepo 采用 **根级通用 + 子项目特定** 的分层策略：

### 5.1 根级 .gitignore（kk-ai/.gitignore）

负责 Monorepo 全局忽略：

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

### 5.2 应用级 .gitignore（apps/web-admin/.gitignore）

负责前端特定忽略：

```gitignore
# Vite
.vite/
vite.config.ts.timestamp-*

# Local env files
.env.*.local
```

### 5.3 包级 .gitignore（packages/*/.gitignore）

```gitignore
# Build output
dist/

# Test output
coverage/
```

### 5.4 分层策略的优势

| 层级 | 职责 | 示例 |
|------|------|------|
| 根级 | 全仓库通用 | `node_modules`、`.env`、`.DS_Store` |
| 应用级 | 构建工具特定 | `.vite/`、`.react-router/` |
| 包级 | 库输出控制 | `dist/`（根级已覆盖，但显式声明更清晰） |

---

## 六、Turbo 任务管道配置

### 6.1 turbo.json

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

### 6.2 任务依赖解析

```
typecheck ──> ^build ──> 先构建所有依赖包（types/utils/ui）
                         再对当前应用执行 tsc --noEmit

build ──> ^build ──> 按依赖拓扑顺序构建（types → utils → ui → web-admin）
```

**Turbo 缓存机制**：
- 任务输入（源码 + 配置）未变时，直接复用缓存结果
- `dev` 任务标记为 `persistent`，不会与其他任务并行冲突

---

## 七、共享包设计

### 7.1 @kk-ai/types（类型定义包）

```ts
// packages/types/src/index.ts
export interface Theme {
  mode: 'light' | 'dark' | 'system';
  primaryColor: string;
}

export interface User {
  id: string;
  name: string;
  role: 'admin' | 'editor';
}
```

**特点**：纯类型定义，无运行时代码，构建后仅输出 `.d.ts`。

### 7.2 @kk-ai/ui（UI 组件库）

```ts
// packages/ui/src/index.ts
export { Button } from './components/button';
export { ThemeProvider } from './components/theme-provider';
export { cn } from './lib/utils';
```

**构建配置**：使用 `vite-plugin-dts` 在 Vite 构建时自动生成声明文件：

```ts
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import dts from 'vite-plugin-dts';

export default defineConfig({
  plugins: [react(), dts({ insertTypesEntry: true })],
  build: {
    lib: {
      entry: './src/index.ts',
      formats: ['es'],
      fileName: 'index',
    },
    rollupOptions: {
      external: ['react', 'react-dom'],
    },
  },
});
```

**关键设计**：
- `external: ['react', 'react-dom']`：不打包 React，由应用提供
- `formats: ['es']`：仅输出 ES Module，配合 `type: "module"`

### 7.3 @kk-ai/utils（工具函数包）

```ts
// packages/utils/src/index.ts
export const storage = {
  get: <T>(key: string): T | null => {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  },
  set: <T>(key: string, value: T) => {
    localStorage.setItem(key, JSON.stringify(value));
  },
};
```

### 7.4 Workspace 依赖引用

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

## 八、初始化与日常开发流程

### 8.1 首次初始化

```bash
# 1. 安装根依赖（自动安装所有 workspace 依赖）
pnpm install

# 2. 验证类型检查
pnpm run typecheck

# 3. 验证构建
pnpm run build
```

### 8.2 日常开发

```bash
# 启动所有应用的 dev 服务（turbo 并行）
pnpm run dev

# 仅构建某个应用
pnpm --filter @kk-ai/web-admin run build

# 添加依赖到特定包
pnpm --filter @kk-ai/ui add lodash-es
pnpm --filter @kk-ai/ui add -D @types/lodash-es
```

### 8.3 添加新应用/包

```bash
# 新增前端应用
cd apps
mkdir web-portal
cd web-portal
pnpm init

# 新增共享包
cd packages
mkdir hooks
cd hooks
pnpm init
```

**必须配置**：
1. 在 `pnpm-workspace.yaml` 中确认路径匹配（已通配无需修改）
2. 创建 `tsconfig.json` 继承 `../../tsconfig.base.json`
3. 创建 `.gitignore`（建议从现有包复制）
4. 在 `turbo.json` 中添加需要的新任务（如有）

---

## 九、最佳实践清单

### 9.1 ✅ 推荐做法

| 实践 | 说明 |
|------|------|
| TS 严格模式 | 基座开启 `strict: true`，全链路覆盖 |
| 配置继承 | 所有子项目 `extends` 基座，避免重复 |
| 分层 .gitignore | 根级通用 + 项目级特定 |
| workspace 协议 | 内部包使用 `workspace:*` 引用 |
| 类型优先 | 先定义 `@kk-ai/types`，再实现功能 |
| 库 external React | UI 包不打包 React，避免多实例 |
| Turbo 缓存 | 利用 `dependsOn` 和缓存加速 CI |

### 9.2 ❌ 避免事项

| 反模式 | 风险 |
|--------|------|
| 在基座中开启 `allowImportingTsExtensions` | 库级 `tsc` 编译会报错 |
| 忽略 `.gitignore` | `node_modules` / `dist` 可能误提交 |
| 库中打包 React | 导致应用出现多个 React 实例 |
| 跨包直接相对路径引用 | 破坏封装，应使用包名导入 |

---

## 十、后续扩展方向

| 方向 | 建议 |
|------|------|
| ESLint / Prettier | 根级统一配置，子项目继承 |
| 单元测试 | 引入 Vitest + React Testing Library |
| Storybook | 为 `@kk-ai/ui` 建立组件文档站 |
| CI/CD | GitHub Actions + Turbo Remote Cache |
| 后端对接 | `services/` 目录初始化 API 服务 |
| 路径别名 | 统一 `@/` 指向各包 `src` 目录 |

---

## 附录：文件索引

| 文件 | 路径 | 作用 |
|------|------|------|
| 包管理配置 | `pnpm-workspace.yaml` | 声明 workspace 范围 |
| 构建编排 | `turbo.json` | Turbo 任务管道 |
| TS 基座 | `tsconfig.base.json` | 共享编译器选项 |
| 根忽略 | `.gitignore` | 全局忽略规则 |
| 应用 TS | `apps/*/tsconfig.json` | 应用级 TS 配置 |
| 包 TS | `packages/*/tsconfig.json` | 库级 TS 配置 |
