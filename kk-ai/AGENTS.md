# AGENTS.md - 康康 AI 项目编码规范

## 项目全景

```
康康 AI 全栈系统（kk-ai）
├── apps/
│   └── web-admin/          # 管理后台（React 18 + Ant Design Pro）
│       ├── src/
│       │   ├── App.tsx     # ProLayout 主页面 + 路由/菜单
│       │   ├── main.tsx    # ConfigProvider + 主题管理
│       │   ├── services/   # API 封装（按模块）
│       │   ├── pages/      # 页面组件
│       │   └── test/       # Vitest 测试
│       └── e2e/            # Playwright E2E 测试
│
├── packages/
│   ├── types/              # 共享类型（纯 TS）
│   ├── ui/                 # 共享 UI 组件（CSS Modules + CSS Variables）
│   └── utils/              # 共享工具函数（storage, generateTraceId）
│
├── services/
│   └── mcp-hub/            # Gateway 入口（FastAPI + Pydantic v2）
│       ├── app/
│       │   ├── main.py              # FastAPI 入口
│       │   ├── router/              # API 路由
│       │   ├── middleware/          # Auth → RateLimit → Quota → Logger
│       │   ├── services/            # 业务逻辑
│       │   └── models/              # Pydantic 模型
│       └── tests/                   # pytest
│
├── .ai-harness/            # AI Harness 框架
│   ├── prompts/            # System / Frontend / Backend 提示词
│   └── scripts/verify.sh   # 6 阶段 TASK 验证脚本
│
├── docs/
│   ├── tasks/              # TASK 规范库（TASK-100, TASK-101...）
│   └── engineering/        # 工程规范文档
│
└── .github/workflows/      # CI/CD（ci.yml + e2e.yml）
```

---

## 技术栈约束

### 前端

- **框架**: React 18 + Vite 5 + TypeScript 5.4（Strict 模式）
- **组件库**: Ant Design 6.x + ProComponents 2.x
- **路由**: react-router-dom v7
- **样式**: CSS Modules + CSS Variables（**已移除 Tailwind**）
- **测试**: Vitest 2.1 + jsdom 24 + @testing-library/react
- **构建**: pnpm workspace + Turbo 2.x

### 后端

- **框架**: FastAPI 0.115 + Pydantic v2
- **Python**: 3.13+
- **缓存**: Redis（降级内存模式）
- **测试**: pytest + pytest-cov（阈值 50%）
- **部署**: uvicorn + Docker

---

## 强制编码规范

### 通用

1. **禁止 `any`** — 所有接口必须定义完整类型
2. **单一职责** — 一个文件只做一件事
3. **向后兼容** — 修改接口不得破坏已有调用方

### 前端

4. **API 封装** — 所有请求统一放 `src/services/{module}.ts`，禁止组件内直接 `fetch`
5. **路由菜单同步** — 新增/修改路由必须同步更新 `App.tsx` 的 `routeConfig` 和 `Routes`
6. **暗色模式** — 新增页面/组件必须测试暗色模式兼容性
7. **ProLayout 菜单** — 父菜单点击默认跳转第一个子路由（`menuItemRender` 中处理）

### 后端

8. **API 前缀** — 所有接口统一 `/api/v1` 前缀
9. **错误格式** — 统一 `{"error":"ERROR_CODE","message":"...","detail":{}}`
10. **配额规则** — soft delete（`status='deleted'`），**禁止物理删除**
11. **Redis 键安全** — 项目名中的 `/` `:` 替换为 `_`，防止键注入
12. **路由注册顺序** — `quota_router` 必须在 `proxy_router` **之前**注册（catch-all 冲突）

---

## 文件操作规范

| 操作           | 必须同步做的事                                                                                                                    |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 新增前端页面   | 1. 路由注册（App.tsx）<br>2. 菜单配置（App.tsx routeConfig）<br>3. 单元测试（`__tests__/*.test.tsx`）                             |
| 新增后端 API   | 1. router 注册（main.py）<br>2. 模型定义（models/）<br>3. pytest 测试（tests/）<br>4. AuthMiddleware EXEMPT_PATHS（如需要免鉴权） |
| 修改中间件     | 1. 检查 EXEMPT_PATHS 是否包含新增 API 路径<br>2. 确保中间件执行顺序正确                                                           |
| 修改 TASK 规范 | 1. 更新 docs/tasks/\*_/TASK-_.md<br>2. 同步更新 AGENTS.md（如规范升级）                                                           |

---

## TASK 开发流程（SDD）

```
接到需求
  → 写 TASK 规范（AC 必须可逐项勾选）
  → AI 按规范生成代码
  → 自动跑 verify.sh 或对应验证命令
  → 人按 AC 验收
  → 通过？合并并记录度量
  → 失败？复盘 → 升级 system-prompt / TASK 模板
```

**验证命令速查**：

```bash
# 前端
cd apps/web-admin && pnpm typecheck && pnpm test:unit

# 后端
cd services/mcp-hub && pytest tests/test_{module}.py -v --cov=app

# 全量
sh .ai-harness/scripts/verify.sh {TASK_ID}
```

---

## 调试备忘

| 问题                        | 原因                        | 解决方案                                |
| --------------------------- | --------------------------- | --------------------------------------- |
| 配额 API 返回 404           | proxy_router catch-all 拦截 | quota_router 先于 proxy_router 注册     |
| 前端白屏 Routes not defined | react-router-dom 组件未导入 | 检查 `import { Routes, Route }`         |
| CORS 预检失败               | 缺少 CORSMiddleware         | 已在 main.py 配置 `allow_origins=["*"]` |
| ProLayout 菜单 key 冲突     | 父子菜单 path 重复          | 正常现象，不影响功能                    |
| 测试 ResizeObserver 报错    | jsdom 不支持                | 已在 `test/setup.ts` 中 mock            |
| Redis 连接失败              | 本地未启动 Redis            | 后端自动降级内存模式，不影响开发        |

---

## 相关文档索引

- [SDD 最佳实践](docs/engineering/ai-harness-sdd-best-practice.md)
- [TASK-100 配额展示页面](docs/tasks/frontend/TASK-100-quota-page.md)
- [TASK-101 配额规则管理前端](docs/tasks/frontend/TASK-101-quota-rule-management.md)
- [TASK-102 配额管理后端 API](docs/tasks/backend/TASK-102-quota-api.md)
