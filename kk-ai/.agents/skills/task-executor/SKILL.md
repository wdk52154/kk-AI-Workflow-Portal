---
name: task-executor
description: 执行康康 AI 项目的 TASK 规范开发任务。当用户要求"实现 TASK-XXX"、"按 TASK 规范开发"、"完成某个 TASK"或提供 TASK 文件路径时触发。支持前端(React+AntD)、后端(FastAPI)、全栈任务的代码生成、验证和迭代修复。
---

# TASK 执行器

## 触发条件

以下任意情况触发本 skill：

- 用户提到 "TASK-XXX" 并要求实现
- 用户提供 `docs/tasks/**/TASK-*.md` 文件路径
- 用户说 "按规范实现"、"完成这个 TASK"
- 用户要求执行前后端联调功能开发

## 执行工作流

### Step 1: 读取 TASK 规范

1. 从用户提供的路径读取 TASK 文件，或搜索 `docs/tasks/**/TASK-{ID}.md`
2. 提取关键信息：
   - **Type**: frontend / backend / fullstack
   - **AC**: 验收标准（必须逐项自检）
   - **文件变更清单**: 新增/修改/删除的文件
   - **技术约束**: 版本、架构决策
   - **边界条件**: 异常场景

### Step 2: 分析依赖

检查 TASK 的 `Depends On` 字段：

- 依赖的 TASK 已实现？继续
- 依赖未实现？提示用户先完成依赖 TASK

### Step 3: 读取现有代码

按 Type 读取相关文件：

**前端**：

```
- App.tsx（路由、菜单、布局）
- pages/ 下相关页面
- services/ 下 API 封装
- test/ 下已有测试
```

**后端**：

```
- main.py（路由注册、中间件、 lifespan）
- router/ 下已有路由
- middleware/ 下相关中间件
- models/ 下已有模型
- tests/ 下已有测试
- config.py（配置项）
```

### Step 4: 按 AC 逐条实现

**实现顺序**：

1. 后端模型/服务（如果有后端部分）
2. 后端路由/API
3. 后端测试
4. 前端 API 封装
5. 前端页面组件
6. 前端路由注册
7. 前端测试

**编码约束**：

- 严格按 AC 逐条实现，完成后逐项自检
- 所有新增文件必须包含完整类型注解
- 禁止修改与 TASK 无关的文件
- 前端：API 请求统一封装在 `services/` 下
- 后端：错误响应用统一 `ErrorResponse` 格式

### Step 5: 运行验证

**前端验证**：

```bash
cd apps/web-admin && pnpm typecheck
cd apps/web-admin && pnpm test:unit
```

**后端验证**：

```bash
cd services/mcp-hub && pytest tests/test_{module}.py -v --cov=app
```

**全量验证**：

```bash
sh .ai-harness/scripts/verify.sh {TASK_ID}
```

### Step 6: 修复问题

验证失败时：

1. 读取错误信息
2. 定位问题文件
3. 修复后重新验证
4. 重复直到全部通过

## 技术约束

### 前端

- React 18 + TypeScript Strict
- Ant Design 6 + ProComponents 2
- react-router-dom v7（useNavigate / useLocation）
- CSS Modules + CSS Variables（无 Tailwind）
- 暗色模式必须兼容
- 测试：Vitest + jsdom + @testing-library/react

### 后端

- Python 3.13 + FastAPI 0.115 + Pydantic v2
- 内存存储 + Redis 降级模式
- 配额规则 soft delete（status='deleted'）
- 错误码统一：VALIDATION_ERROR / RULE_EXISTS / RULE_NOT_FOUND / QUOTA_EXCEEDED
- 测试：pytest + pytest-cov（阈值 50%）

### 路由特殊约束

- **quota_router 必须先于 proxy_router 注册**（避免 catch-all 拦截）
- **AuthMiddleware EXEMPT_PATHS** 必须包含免鉴权路径（如 `/api/v1/quota`）
- **CORS** 已配置，跨域请求正常

## 常见陷阱与解决方案

| 陷阱                         | 现象                                                         | 解决方案                                       |
| ---------------------------- | ------------------------------------------------------------ | ---------------------------------------------- |
| proxy_router 拦截 API        | API 返回 404，日志 `Service not found`                       | quota_router 先于 proxy_router include         |
| Auth 拦截开发 API            | 返回 401 Unauthorized                                        | 在 auth.py EXEMPT_PATHS 中添加路径             |
| vi.mock hoisting             | 测试报错 `Cannot access before initialization`               | mock 工厂内不使用顶层变量                      |
| ResizeObserver 缺失          | 测试报错 `ResizeObserver is not defined`                     | 已在 test/setup.ts mock，确认生效              |
| useNavigate 无 Router 上下文 | 测试报错 `useNavigate may be used only in context of Router` | 测试用 BrowserRouter 包裹                      |
| import.meta.env 类型         | 报错 `Property env does not exist on type ImportMeta`        | 用 `(import.meta as unknown as {env:...}).env` |
| ProLayout key 冲突           | 控制台 warning `Duplicated key used in Menu`                 | 正常现象，忽略                                 |

## 迭代记录模板

TASK 完成后，更新 TASK 文件的迭代记录：

```markdown
### Round N

- **时间**: YYYY-MM-DD
- **结果**: 通过 / 失败
- **问题记录**:
  - 问题 1：... → 修复方式：...
- **规范升级**:
  - 新增约束：...
```
