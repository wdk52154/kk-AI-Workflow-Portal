# Harness Engineering 最佳实践：构建驾驭型工程体系

> 项目：康康 AI 全栈系统（kk-ai）  
> 版本：v1.0  
> 适用范围：团队级工程基础设施标准化

---

## 一、什么是 Harness Engineering？

**Harness**（马具/束具）在工程领域的含义是：**一套框架化的基础设施，用于驾驭（控制、约束、驱动）整个软件生命周期**。

```
传统开发                      Harness Engineering
─────────────────           ─────────────────────────
人写代码 → 人测试 → 人部署     Harness 驱动全生命周期
   ↓                              ↓
  容易遗漏、风格不一          标准化、自动化、可重复
```

**核心目标**：
- **约束（Constraint）**：通过 Harness 强制团队遵守规范
- **自动化（Automation）**：把重复性工作交给 Harness
- **可观测（Observability）**：Harness 输出标准化报告和指标
- **可复现（Reproducibility）**：任何人在任何环境得到相同结果

---

## 二、Harness 分层架构

```
┌─────────────────────────────────────────────┐
│              Orchestration Harness            │
│         （编排层：Turbo / Nx / Make）          │
├─────────────────────────────────────────────┤
│  Build Harness  │  Test Harness  │  Quality  │
│  （Vite/TSC）   │（Vitest/Pytest）│Harness    │
│                 │                │(ESLint/Ruff)│
├─────────────────────────────────────────────┤
│           AI Harness（AI 辅助约束层）          │
│    （Prompt 模板 / 上下文管理 / 验收标准）      │
├─────────────────────────────────────────────┤
│         Environment Harness（环境层）          │
│      （Docker / DevContainer / Nix）          │
├─────────────────────────────────────────────┤
│         Repository Harness（仓库层）           │
│     （Git Hooks / CI / CD / Monorepo）        │
└─────────────────────────────────────────────┘
```

---

## 三、各层 Harness 在本项目中的落地

### 3.1 Repository Harness（仓库层）

**职责**：代码进入仓库前的质量门禁

#### Git Hooks（本地门禁）

```bash
# .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# 1. 格式化检查
pnpm exec lint-staged

# 2. 类型检查（仅变更的包）
pnpm exec turbo run typecheck --filter=[HEAD~1]

# 3. 单元测试（仅变更的包）
pnpm exec turbo run test --filter=[HEAD~1]
```

```bash
# .husky/commit-msg
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Commit message 规范检查
pnpm exec commitlint --edit $1
```

#### Monorepo 工作区约束

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'

# .npmrc
strict-peer-dependencies=false
auto-install-peers=true
```

**Harness 效果**：
- 提交前自动格式化 + 类型检查 + 测试
- Commit message 强制 Conventional Commits 规范
- 依赖自动解析，避免版本冲突

---

### 3.2 Environment Harness（环境层）

**职责**：确保所有开发者使用一致的环境

#### DevContainer 配置

```json
// .devcontainer/devcontainer.json
{
  "name": "康康 AI 开发环境",
  "dockerComposeFile": "docker-compose.yml",
  "service": "dev",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "20" },
    "ghcr.io/devcontainers/features/python:1": { "version": "3.13" },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/redis-server:1": {}
  },
  "postCreateCommand": "pnpm install && pip install -r services/mcp-hub/requirements.txt",
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "ms-python.python",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode"
      ]
    }
  }
}
```

#### Docker Compose（本地全栈启动）

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'

  mcp-hub:
    build: ./services/mcp-hub
    ports:
      - '8000:8000'
    environment:
      - MCPHUB_REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  web-admin:
    build: ./apps/web-admin
    ports:
      - '5173:5173'
    depends_on:
      - mcp-hub
```

**Harness 效果**：
- 新成员 5 分钟启动完整开发环境
- 消除"在我电脑上能跑"问题
- 一键启动前端 + 后端 + Redis

---

### 3.3 Build Harness（构建层）

**职责**：标准化、可缓存、可并行的构建流程

#### Turbo Pipeline（Monorepo 构建编排）

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"],
      "env": ["NODE_ENV"]
    },
    "typecheck": {
      "dependsOn": ["^build"],
      "outputs": []
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Harness 效果**：
- 构建拓扑自动排序（types → utils → ui → web-admin）
- 未变更的包直接复用缓存（本地 + 远程）
- `pnpm run build` 一键构建全仓库

---

### 3.4 Test Harness（测试层）

**职责**：统一的测试框架、覆盖率门槛、自动化执行

#### 前端测试 Harness

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      thresholds: {
        branches: 70,
        functions: 70,
        lines: 70,
        statements: 70,
      },
      exclude: ['src/test/**', '**/*.d.ts'],
    },
  },
});
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});
```

#### 后端测试 Harness

```python
# pyproject.toml（mcp-hub）
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short --cov=app --cov-report=term-missing --cov-fail-under=70"

[tool.coverage.run]
source = ["app"]
omit = ["app/test/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

**Harness 效果**：
- 统一测试框架（Vitest / pytest）
- 覆盖率阈值 70%，不达标构建失败
- Mock 统一配置，减少重复代码

---

### 3.5 Quality Harness（质量层）

**职责**：代码风格、类型安全、安全漏洞的自动化检查

#### 前端质量门禁

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "plugin:security/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "security"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "no-console": ["warn", { "allow": ["error", "warn"] }],
    "security/detect-object-injection": "warn"
  }
}
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

#### 后端质量门禁

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Harness 效果**：
- 提交前自动格式化（Prettier / Ruff）
- 类型检查严格模式（TypeScript strict / mypy strict）
- 安全扫描（eslint-security / bandit）

---

### 3.6 AI Harness（AI 辅助约束层）

**职责**：标准化 AI 辅助开发的输入输出，确保 AI 产出可控

#### Prompt 模板 Harness

```yaml
# .ai-harness/prompt-templates/
├── frontend-task.yaml
├── backend-task.yaml
└── review-checklist.yaml
```

```yaml
# frontend-task.yaml
context:
  project: "康康 AI 全栈系统"
  tech_stack: ["React 18", "TypeScript", "Ant Design Pro"]
  
constraints:
  - "不使用 any 类型"
  - "优先使用 Ant Design Pro 组件"
  - "所有函数必须有 JSDoc"
  - "错误处理使用 message.error()"
  
verification:
  - "pnpm run typecheck 通过"
  - "pnpm run build 通过"
  - "pnpm run test 通过"
```

#### AI 输出验收 Harness

```bash
# .ai-harness/verify.sh
#!/bin/bash
set -e

echo "=== AI 输出验收 ==="

# 1. 类型检查
echo "→ TypeScript 类型检查..."
cd apps/web-admin && pnpm run typecheck

# 2. 构建检查
echo "→ 构建检查..."
pnpm run build

# 3. 测试检查
echo "→ 单元测试..."
pnpm run test

# 4. Lint 检查
echo "→ 代码质量..."
pnpm run lint

echo "=== 全部通过 ✅ ==="
```

**Harness 效果**：
- AI 输出必须通过统一验收脚本
- Prompt 模板保证上下文一致性
- 减少 AI 产出"在我环境能跑"的问题

---

### 3.7 Orchestration Harness（编排层）

**职责**：把以上所有 Harness 串联为完整的开发工作流

#### CI/CD Pipeline（GitHub Actions）

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Environment
        uses: ./.github/actions/setup
        
      - name: Lint
        run: pnpm run lint
        
      - name: Type Check
        run: pnpm run typecheck
        
      - name: Test
        run: pnpm run test
        
      - name: Build
        run: pnpm run build
        
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          fail_ci_if_error: true

  e2e:
    runs-on: ubuntu-latest
    needs: quality-gate
    services:
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup
      - name: Start Services
        run: docker-compose up -d
      - name: E2E Tests
        run: pnpm exec playwright test
```

**Harness 效果**：
- PR 合并前必须通过全部质量门禁
- E2E 测试在真实服务环境中运行
- 覆盖率自动上报 Codecov

---

## 四、Harness 落地清单

### Phase 1：基础设施（Week 1）

- [ ] 安装并配置 Husky + lint-staged
- [ ] 配置 Prettier / Ruff 格式化
- [ ] 配置 ESLint / mypy 类型检查
- [ ] 配置 Commitlint（Conventional Commits）
- [ ] 编写 `docker-compose.yml`（Redis + mcp-hub + web-admin）

### Phase 2：测试体系（Week 2）

- [ ] 配置 Vitest（前端）+ pytest（后端）
- [ ] 设置覆盖率阈值（70%）
- [ ] 编写 Mock 工具（localStorage、Redis、API）
- [ ] 配置 Playwright E2E 测试

### Phase 3：CI/CD（Week 3）

- [ ] 配置 GitHub Actions CI Pipeline
- [ ] 配置 Turbo Remote Cache（Vercel / AWS）
- [ ] 配置自动化部署（Vercel 前端 / Docker 后端）
- [ ] 配置 Codecov 覆盖率上报

### Phase 4：AI Harness（Week 4）

- [ ] 建立 `docs/tasks/` 规范目录
- [ ] 编写前端/后端 Prompt 模板
- [ ] 编写 AI 输出验收脚本（`verify.sh`）
- [ ] 建立 TASK 迭代复盘机制

---

## 五、Harness 成熟度模型

| 等级 | 特征 | 状态 |
|------|------|------|
| L0 手动 | 全靠人工检查代码 | ⬜ |
| L1 脚本化 | 有脚本但不强制 | ⬜ |
| L2 门禁化 | Git Hooks + CI 强制 | ⬜ 目标 |
| L3 智能化 | AI 辅助 + 自动修复 | ⬜ 未来 |
| L4 自治化 | AI 自主完成 TASK | ⬜ 远景 |

当前项目处于 **L1 → L2 过渡期**，核心目标是建立强制性的质量门禁。

---

## 六、关键原则

1. **Harness 优先于约定**：不要依赖团队成员"自觉遵守"，用 Harness 强制
2. **本地先于远程**：本地 Git Hooks 的反馈速度远快于 CI
3. **快速失败**：有问题尽早暴露，不要在最后才发现
4. **渐进增强**：先建立基础 Harness，再逐步增加复杂度
5. **可观测**：Harness 必须输出清晰的报告，让人知道为什么失败

---

## 附录：Harness 工具链速查

| 层级 | 工具 | 配置位置 |
|------|------|---------|
| Repository | Husky + lint-staged | `.husky/` + `package.json` |
| Repository | Commitlint | `.commitlintrc.json` |
| Environment | DevContainer | `.devcontainer/` |
| Environment | Docker Compose | `docker-compose.yml` |
| Build | Turbo | `turbo.json` |
| Test | Vitest | `vitest.config.ts` |
| Test | pytest | `pyproject.toml` |
| Test | Playwright | `playwright.config.ts` |
| Quality | ESLint | `.eslintrc.json` |
| Quality | Prettier | `.prettierrc` |
| Quality | Ruff | `pyproject.toml` |
| Quality | mypy | `pyproject.toml` |
| Quality | bandit | `pyproject.toml` |
| Orchestration | GitHub Actions | `.github/workflows/` |
| Orchestration | Turbo Remote Cache | Vercel / AWS S3 |
