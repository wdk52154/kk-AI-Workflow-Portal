# AI 工程化落地指南：Harness Engineering + SDD 双核驱动

> 项目：康康 AI 全栈系统（kk-ai）  
> 版本：v1.0  
> 核心理念：**人定规范 → Harness 约束 → AI 执行 → 自动验收 → 规范进化**

---

## 一、为什么需要 Harness + SDD？

### 1.1 纯 AI 编程的困境

```
┌─────────────────────────────────────────────┐
│  你给 AI 一个大需求："帮我做一个管理后台"       │
│                                              │
│  AI 输出 500 行代码 → 你测试 → 发现 10 个 bug  │
│  → 让 AI 修复 → 引入 5 个新 bug → 循环往复      │
│                                              │
│  问题：AI 没有约束，输出不可控                   │
└─────────────────────────────────────────────┘
```

### 1.2 纯人工规范的低效

```
┌─────────────────────────────────────────────┐
│  你写了一份 50 页的详细设计文档                 │
│                                              │
│  → 开发还是按自己习惯写                         │
│  → Code Review 时发现风格不统一                  │
│  → 测试时发现没按文档实现边界条件                 │
│                                              │
│  问题：规范没有执行力，成了摆设                   │
└─────────────────────────────────────────────┘
```

### 1.3 Harness + SDD 的解法

```
┌──────────────────────────────────────────────────────────────┐
│                    AI 工程化双核模型                           │
│                                                               │
│   ┌──────────────┐         ┌──────────────┐                  │
│   │   SDD 规范层  │  ←────→ │ Harness 约束层 │                 │
│   │  (人定义什么) │         │ (系统强制怎么) │                 │
│   └──────┬───────┘         └──────┬───────┘                 │
│          │                        │                          │
│          └────────┬───────────────┘                          │
│                   ↓                                           │
│            ┌─────────────┐                                   │
│            │   AI 执行层  │  ← AI 在约束内自由发挥             │
│            │ (Agent 实现) │                                   │
│            └──────┬──────┘                                   │
│                   ↓                                           │
│            ┌─────────────┐                                   │
│            │ 自动验收层   │  ← Harness 自动判断合格/不合格     │
│            │ (CI/脚本)   │                                   │
│            └──────┬──────┘                                   │
│                   ↓                                           │
│            ┌─────────────┐                                   │
│            │  规范进化层  │  ← 不合格 → 升级规范 → 下次更好    │
│            │ (飞轮迭代)   │                                   │
│            └─────────────┘                                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**关键洞察**：
- **SDD** 回答 "做什么" 和 "做到什么程度算好"
- **Harness** 回答 "怎么确保真的做好了"
- **AI** 在两者之间高效执行，不需要人逐行审查

---

## 二、SDD：规范即契约

### 2.1 SDD 四层规范体系

```
L1 架构规范 (ARCH)          →  约束技术选型、目录结构、接口契约
     ↓
L2 任务规范 (TASK)          →  约束模块边界、验收标准、依赖关系
     ↓
L3 实现规范 (SPEC)          →  约束代码风格、错误处理、性能基线
     ↓
L4 Prompt 规范 (PROMPT)     →  约束 AI 的输入格式、上下文范围
```

### 2.2 规范即代码（Spec as Code）

所有规范必须满足 **ICE 原则**：

| 原则 | 含义 | 示例 |
|------|------|------|
| **I**mportable | 可导入执行 | `turbo.json` 被 CI 直接读取 |
| **C**heckable | 可自动检查 | `pyproject.toml` 被 Ruff/mypy 读取 |
| **E**volvable | 可版本进化 | Git 管理规范变更历史 |

**反例**：写在 Wiki 上的"编码规范" → 没人看，无法检查
**正例**：`.eslintrc.json` 中的 `"@typescript-eslint/no-explicit-any": "error"` → 提交即检查

### 2.3 TASK 规范模板（SDD 核心）

每个 TASK 是一份**可执行的契约**：

```markdown
# TASK-XXX：任务标题

## 1. 输入（Input）
- 背景上下文：[链接到 ARCH 或上级 TASK]
- 已有代码：[相关文件路径]
- 约束条件：[技术约束列表]

## 2. 输出（Output）
- 交付物：[文件清单]
- 接口签名：[TypeScript / Python 类型定义]
- 验收标准（AC）：[可验证的条件列表]

## 3. 验证（Verification）
- 自动检查命令：`pnpm run typecheck && pnpm run test`
- 人工确认项：[UI 效果、业务逻辑正确性]
- 性能基线：[如有]

## 4. 迭代记录
| 轮次 | AI 输出摘要 | Harness 验收结果 | 规范升级 |
|------|-----------|----------------|---------|
```

---

## 三、Harness：约束即基础设施

### 3.1 Harness 的三种形态

| 形态 | 作用时机 | 示例 | 本项目落地 |
|------|---------|------|-----------|
| **预检查** | 代码入库前 | Git Hooks | Husky + lint-staged |
| **持续检查** | PR 合并前 | CI Pipeline | GitHub Actions |
| **后检查** | 部署上线后 | 监控告警 | Sentry + 日志分析 |

### 3.2 AI 专用 Harness

传统的 Harness 检查的是**人写的代码**。AI 工程化需要新增一层 **AI Harness**，检查的是**AI 的输出**。

```
┌─────────────────────────────────────────────────────────┐
│                    AI Harness 架构                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  输入层 Harness                                          │
│  ├── Prompt 模板库（标准格式）                            │
│  ├── 上下文注入器（自动收集相关代码）                      │
│  └── 约束声明器（技术栈、命名规范）                       │
│                                                         │
│  输出层 Harness                                          │
│  ├── 代码解析器（提取 AI 输出的文件变更）                 │
│  ├── 自动应用器（应用到工作区）                           │
│  └── 验收执行器（运行 typecheck/test/build）             │
│                                                         │
│  反馈层 Harness                                          │
│  ├── 错误归类器（类型错误/逻辑错误/风格问题）             │
│  ├── 报告生成器（标准化输出）                             │
│  └── 规范升级器（TASK.md 自动更新约束）                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.3 验收脚本 Harness（核心落地）

```bash
#!/bin/bash
# .ai-harness/verify.sh —— AI 输出强制验收脚本

set -e

TASK_ID=$1
TASK_DIR="docs/tasks/${TASK_ID}"

echo "╔══════════════════════════════════════════╗"
echo "║     AI 输出验收 Harness v1.0             ║"
echo "║     TASK: ${TASK_ID}                     ║"
echo "╚══════════════════════════════════════════╝"

# ── 阶段 1：规范符合性检查 ──
echo ""
echo "📋 [1/5] 规范符合性检查..."

if [ ! -f "${TASK_DIR}/TASK.md" ]; then
    echo "❌ 缺少 TASK.md 规范文件"
    exit 1
fi

echo "✅ TASK.md 存在"

# ── 阶段 2：类型安全 Harness ──
echo ""
echo "🔒 [2/5] 类型安全 Harness..."

if grep -q "\.tsx\|\.ts" "${TASK_DIR}/changed-files.txt"; then
    echo "→ 检测到 TypeScript 变更，执行类型检查..."
    pnpm run typecheck 2>&1 | tee /tmp/typecheck.log
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo "❌ TypeScript 类型检查失败"
        exit 1
    fi
fi

if grep -q "\.py" "${TASK_DIR}/changed-files.txt"; then
    echo "→ 检测到 Python 变更，执行 mypy 检查..."
    cd services/mcp-hub && mypy app/ 2>&1 | tee /tmp/mypy.log
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo "❌ mypy 类型检查失败"
        exit 1
    fi
fi

echo "✅ 类型安全通过"

# ── 阶段 3：测试 Harness ──
echo ""
echo "🧪 [3/5] 测试 Harness..."

if grep -q "apps/web-admin" "${TASK_DIR}/changed-files.txt"; then
    echo "→ 前端测试..."
    pnpm --filter @kk-ai/web-admin run test 2>&1 | tee /tmp/test.log
fi

if grep -q "services/mcp-hub" "${TASK_DIR}/changed-files.txt"; then
    echo "→ 后端测试..."
    cd services/mcp-hub && pytest 2>&1 | tee /tmp/test.log
fi

echo "✅ 测试通过"

# ── 阶段 4：构建 Harness ──
echo ""
echo "🏗️  [4/5] 构建 Harness..."

pnpm run build 2>&1 | tee /tmp/build.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ 构建失败"
    exit 1
fi

echo "✅ 构建通过"

# ── 阶段 5：质量门禁 Harness ──
echo ""
echo "✨ [5/5] 质量门禁 Harness..."

pnpm run lint 2>&1 | tee /tmp/lint.log
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ Lint 检查失败"
    exit 1
fi

echo "✅ 质量门禁通过"

# ── 验收报告 ──
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           🎉 全部验收通过！               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "📊 验收摘要:"
echo "   - 类型检查: ✅"
echo "   - 单元测试: ✅"
echo "   - 构建产物: ✅"
echo "   - 代码质量: ✅"
echo ""
echo "📝 详细日志:"
echo "   - /tmp/typecheck.log"
echo "   - /tmp/test.log"
echo "   - /tmp/build.log"
echo "   - /tmp/lint.log"
```

---

## 四、双核协作工作流

### 4.1 标准 AI 工程化工作流

```
人                          Harness                          AI
│                            │                               │
│── 写 TASK.md ─────────────>│                              │
│   (SDD L2 规范)            │                              │
│                            │── 加载 Prompt 模板 ───────────>│
│                            │   + 注入上下文               │
│                            │   + 注入约束条件             │
│                            │                               │
│                            │<── AI 输出代码 + 文件清单 ─────│
│                            │                               │
│                            │── 自动应用变更 ───────────────>│
│                            │   (git apply / 直接写入)     │
│                            │                               │
│                            │── 运行 verify.sh ────────────>│
│                            │   (Harness 自动验收)         │
│                            │                               │
│<── 查看验收报告 ───────────│                              │
│   (通过/失败 + 日志)       │                              │
│                            │                               │
│── 如失败：补充约束 ────────>│── 反馈给 AI ─────────────────>│
│   (更新 TASK.md)           │   (错误日志 + 修复指令)      │
│                            │                               │
│   (循环直到通过)           │                               │
│                            │                               │
│── 如通过：合并代码 ────────>│                              │
│   + 更新规范库             │                              │
│                            │                               │
```

### 4.2 实战示例：实现配额管理页面

#### Step 1：人写 TASK 规范（SDD）

```markdown
# TASK-007：配额管理页面

## 输入
- 后端 API 已就绪：`GET /quota/{project_id}`
- 类型定义：`packages/types/src/quota.ts`
- UI 规范：优先使用 ProTable + StatisticCard

## 输出
- 文件：`apps/web-admin/src/pages/quota/index.tsx`
- 路由：`/quota`

## 验收标准
- [ ] AC-1：展示今日/本月调用量（StatisticCard）
- [ ] AC-2：展示各项目配额明细（ProTable，分页）
- [ ] AC-3：支持按项目名称搜索
- [ ] AC-4：超限项目用红色 Tag 标记
- [ ] AC-5：typecheck + test + build 通过

## 约束
- 不使用 any 类型
- 表格列定义提取为独立变量
- 错误处理使用 message.error()
- loading 状态使用 ProTable 内置 skeleton
```

#### Step 2：Harness 组装 Prompt

```markdown
【Situation】
项目是 React 18 + TypeScript + Ant Design Pro Monorepo。
需要在管理后台新增"配额管理"页面。

【Task】
实现配额管理页面，详见 TASK-007。

【Action】
1. 在 apps/web-admin/src/pages/quota/index.tsx 创建页面
2. 使用 StatisticCard 展示今日/本月调用量
3. 使用 ProTable 展示项目配额明细
4. 从后端 API GET /quota/{project_id} 获取数据
5. 类型使用 packages/types/src/quota.ts 中的定义
6. 表格支持搜索和分页
7. 超限项目行用红色标记

【Constraint】
- 不使用 any
- 表格列定义提取为 const columns
- 错误处理：message.error(error.message)
- Loading：使用 ProTable 的 loading 属性

【Verification】
验收脚本：pnpm run typecheck && pnpm run test && pnpm run build
```

#### Step 3：AI 执行 + Harness 验收

```
AI 输出代码 → 自动写入文件 → 运行 verify.sh

输出：
❌ [2/5] 类型安全 Harness 失败
   → apps/web-admin/src/pages/quota/index.tsx(15,23):
      error TS2345: Argument of type 'string | undefined' 
      is not assignable to parameter of type 'string'

人：补充约束到 TASK.md：
   "project_id 必须做非空断言或默认值处理"

AI 修复 → 再次验收

输出：
✅ [5/5] 全部验收通过！
```

#### Step 4：规范进化

```diff
# TASK-007.md

## 约束
  - 不使用 any 类型
  - 表格列定义提取为独立变量
  - 错误处理使用 message.error()
  - loading 状态使用 ProTable 内置 skeleton
+ - 从 URL 参数读取 project_id 时必须处理 undefined 情况
```

**下一次同类任务，AI 会自动避免这个错误。**

---

## 五、飞轮进化机制

### 5.1 规范进化矩阵

```
            AI 执行质量
         低 ────────── 高
      ┌─────────────────────┐
   高 │  规范太松          │  ✨ 理想状态
      │  → 收紧约束        │  → 保持
      ├─────────────────────┤
规  低 │  💀 双输           │  规范太严
范      │  → 重新设计       │  → 适当放宽
完      └─────────────────────┘
整
性
```

### 5.2 每周复盘模板

```markdown
# 第 N 周 AI 工程化复盘

## 统计
- 本周 TASK 总数：X
- 平均迭代轮次：Y（目标 < 3）
- 一次性通过率：Z%（目标 > 60%）
- Harness 拦截问题数：W

## 高频失败项 Top 3
1. [错误类型] - 出现 X 次 → 规范升级：[具体措施]
2. [错误类型] - 出现 X 次 → 规范升级：[具体措施]
3. [错误类型] - 出现 X 次 → 规范升级：[具体措施]

## 规范库更新
- 新增约束：X 条
- 废弃约束：Y 条
- 新增 Prompt 模板：Z 个

## 下周重点
- [ ] 优化 [某 Harness] 的反馈速度
- [ ] 补充 [某模块] 的 TASK 规范
```

---

## 六、项目级落地清单

### Phase 0：基础 Harness（Day 1-2）

```bash
# 1. 安装 Husky + lint-staged
pnpm add -D husky lint-staged
npx husky install

# 2. 配置提交门禁
echo 'pnpm exec lint-staged' > .husky/pre-commit
echo 'pnpm exec commitlint --edit $1' > .husky/commit-msg

# 3. 配置 lint-staged
# package.json:
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{py}": ["ruff check --fix", "ruff format"],
    "*": ["git add"]
  }
}
```

### Phase 1：AI Harness 框架（Day 3-5）

```
.ai-harness/
├── prompts/
│   ├── frontend-task.md      # 前端任务 Prompt 模板
│   ├── backend-task.md       # 后端任务 Prompt 模板
│   └── review-checklist.md   # 代码审查清单
├── scripts/
│   ├── verify.sh             # 验收脚本
│   ├── collect-context.sh    # 上下文收集器
│   └── apply-changes.sh      # AI 输出应用器
└── reports/
    └── template.md           # 验收报告模板
```

### Phase 2：TASK 规范库（Week 2）

```
docs/
├── tasks/
│   ├── frontend/
│   │   ├── TASK-001-theme-switch.md
│   │   ├── TASK-002-quota-page.md
│   │   └── README.md         # 前端 TASK 索引
│   └── backend/
│       ├── TASK-001-rate-limit.md
│       ├── TASK-002-auth-middleware.md
│       └── README.md         # 后端 TASK 索引
├── specs/
│   ├── frontend/
│   │   ├── component-spec.md
│   │   └── page-spec.md
│   └── backend/
│       ├── api-spec.md
│       └── middleware-spec.md
└── prompts/
    ├── system-prompt.md      # 系统级 Prompt
    ├── frontend-prompt.md    # 前端专用 Prompt
    └── backend-prompt.md     # 后端专用 Prompt
```

### Phase 3：CI/CD Harness（Week 3）

```yaml
# .github/workflows/ai-harness.yml
name: AI Harness Verification

on:
  push:
    paths:
      - 'docs/tasks/**'
      - '.ai-harness/**'

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Detect Changed TASKs
        id: detect
        run: |
          TASKS=$(git diff --name-only HEAD~1 | grep 'docs/tasks/' || true)
          echo "tasks=$TASKS" >> $GITHUB_OUTPUT
      
      - name: Run AI Harness Verification
        if: steps.detect.outputs.tasks != ''
        run: |
          for task in ${{ steps.detect.outputs.tasks }}; do
            TASK_ID=$(basename $task .md)
            echo "验证 $TASK_ID..."
            .ai-harness/scripts/verify.sh $TASK_ID
          done
```

### Phase 4：度量与进化（Week 4+）

```
metrics/
├── weekly-report.md          # 周度复盘
├── task-stats.json           # TASK 统计数据
└── harness-effectiveness.md  # Harness 效率分析
```

---

## 七、关键原则总结

| 原则 | 含义 | 落地方式 |
|------|------|---------|
| **规范即代码** | SDD 规范必须能被 Harness 读取 | TASK.md 用结构化格式，约束写入 config 文件 |
| **约束先于自由** | AI 在 Harness 约束内工作 | 先定义不能做什么，再让 AI 发挥 |
| **验收自动化** | 人的验收尽量交给 Harness | verify.sh 覆盖 80% 的验收场景 |
| **失败即进化** | 每次失败都是规范升级的机会 | TASK.md 必须记录迭代记录和约束升级 |
| **上下文即资产** | 累积的规范和 Prompt 是团队资产 | 规范库存入 Git，版本化管理 |

---

## 附录：Prompt 模板速查

### 系统级 Prompt（给 AI 的初始上下文）

```markdown
你是康康 AI 全栈系统的开发助手。

【项目结构】
- Monorepo：pnpm workspace + Turbo
- 前端：React 18 + TypeScript + Ant Design Pro（apps/web-admin/）
- 后端：FastAPI + Python 3.13（services/mcp-hub/）
- 共享包：packages/{types,ui,utils}/

【编码约束】
- TypeScript：strict 模式，禁用 any
- Python：类型注解覆盖率 > 90%，使用 Google docstring
- 错误处理：必须包含 trace_id，前端用 message.error()
- 命名：PascalCase（组件/类型）、camelCase（函数/变量）、snake_case（Python）

【Harness 约束】
- 你的输出必须通过以下检查：
  1. pnpm run typecheck（前端）/ mypy（后端）
  2. pnpm run test（前端）/ pytest（后端）
  3. pnpm run build
  4. pnpm run lint
- 如果检查失败，你会收到错误日志并需要修复。

【输出格式】
- 先输出文件变更清单
- 再输出每个文件的完整代码
- 用 ``` 包裹代码块，标明文件路径
```

### 迭代修复 Prompt

```markdown
【验收失败反馈】

TASK：TASK-XXX
轮次：Round N

Harness 检查结果：
```
[粘贴 verify.sh 的输出]
```

请分析失败原因，修复问题后重新输出完整代码。
修复原则：
1. 只修改与错误相关的代码
2. 保持其他逻辑不变
3. 如果错误是因为规范不明确，请指出需要升级的约束
```
