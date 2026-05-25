# 面试话术：AI 工程化范式跃迁

> 简历原文：AI工程化范式跃迁：以Harness Engineering + SDD 创构研发流，借Cursor Rules/Skills建立"人定规范、AI执工程"之则，完成从手工编码到智能交付的跃迁。
>
> 案例载体：营销平台 CRM 客户管理模块（列表+详情+标签+分群）

---

## 一、30 秒电梯演讲（必背）

```
我探索了一套 Harness Engineering + SDD 的研发流，核心是八个字：人定规范，AI 执工程。

接到需求先写 TASK 规范——逐条可勾选的验收标准、文件变更清单、边界条件。
AI 按规范生成代码，verify.sh 六阶段自动验收，CI 兜底，失败就复盘升级模板。

CRM 客户管理四个模块，传统估 3 周，我们 4 天交付，上线零 P0。
本质是把经验存在规范里，规范会自我进化，越用越强。
```

---

## 二、完整面试回答（2-3 分钟版）

### Step 1：一句话定义（10秒）

> 我探索了一套 **Harness Engineering + SDD** 的研发流，核心是八个字：**人定规范，AI 执工程**。人负责定义"什么叫对"，机器负责"确保做到对"。

### Step 2：方法拆解（30秒）

> **SDD** 是 Specification-Driven Development，规范驱动开发。接到需求不是直接写代码，而是先写 TASK 规范——里面包含逐条可勾选的验收标准（AC）、文件变更清单、边界条件、测试策略。
>
> **Harness** 是工程化约束体系。Git 钩子拦截不规范提交，verify.sh 脚本六阶段自动验收，CI 流水线跑测试+覆盖率。AI 生成的代码必须过机器检查，不过关合并不了。
>
> **Rules + Skills** 是知识沉淀。AGENTS.md 是项目级全局规则，每次对话自动注入；Skills 把领域经验封装成可复用模板，换模块直接复用。

### Step 3：CRM 客户管理案例（60秒）

> 以营销平台的**客户管理模块**为例，传统做法是产品画原型、开发写代码、测试提 bug、来回改三轮。
>
> 用 Harness + SDD 我是这么做的：
>
> **第一步，写 TASK 规范**。比如"客户列表"功能，AC 逐条定义：
> - 手机号必须脱敏，用 `maskPhone` 工具函数，禁止手写正则
> - 筛选条件变化时 URL 同步，刷新不丢状态
> - 批量操作上限 500 条，超限 toast 提示
> - 重点客户后端校验删除权限，不能只靠前端隐藏按钮
>
> **第二步，AI 按规范生成**。把 TASK 文件 + System Prompt + Frontend Prompt 喂给 AI，它按 AC 逐项实现。
>
> **第三步，自动验收**。跑 `verify.sh` 六阶段检查：类型检查 → 单元测试 → 构建 → 质量门禁 → 规范文档完整性。漏了"批量上限校验"？机器直接拦住。
>
> **第四步，复盘进化**。如果这次 AI 漏了"URL 同步筛选"，复盘后升级 TASK 模板。下次做"客户分群"，AI 自动带上这条约束，**不会再犯**。

### Step 4：量化效果（20秒）

> 客户管理四个模块（列表+详情+标签+分群），传统估 3 周，我们 **4 天交付**，上线零 P0。而且这 4 天里 2 天是沉淀规范模板，后面三个模块平均每个 **3 小时**。

### Step 5：升华（20秒）

> 传统开发把经验存在人脑子里，人走了经验就没了，换个人做客户分群重新踩坑。我们把经验存在规范里——**TASK 模板记业务边界，AGENTS.md 记技术约束，Skills 记领域模式**。规范会自我进化，越用越强。这才是真正的从手工编码到智能交付的跃迁。

---

## 三、技术面深度版（3-4 分钟）

### 架构总览

> 我设计了一套**分层约束架构**，分四层：
>
> ```
> L1 规范层（SDD）: TASK 模板 + AC 验收清单 + Prompt 规范
> L2 约束层（Harness）: Git 钩子 + verify.sh + CI 流水线
> L3 执行层（AI）: Agent 按规范生成代码
> L4 进化层（Metrics）: 周度复盘 + 规范飞轮
> ```

### 规范层技术细节

> **TASK 规范模板**是我设计的核心数据结构，包含六个必填字段：
>
> | 字段 | 作用 | 示例（客户列表）|
> |------|------|---------------|
> | 元信息 | ID/类型/预估/依赖 | TASK-201, frontend, 2h |
> | AC | 逐条可勾选 | 手机号脱敏、URL 同步筛选、批量上限 500 |
> | 文件变更清单 | 精确到新增/修改/删除 | `src/services/customer.ts` 新增 |
> | 技术约束 | 版本、架构决策 | Ant Design 6 + ProTable, React Router v7 |
> | 边界条件 | 异常场景 | 网络错误时显示 Empty + 重试按钮 |
> | 测试策略 | 覆盖要求 | Vitest: 列表渲染 + 筛选测试 + 批量测试 |
>
> 为什么强制这六字段？因为**模糊需求是 AI 出错的最大根源**。AC 把"做个客户列表"翻译成机器可执行的检查项。
>
> 另外我建立了**三层 Prompt 体系**：System Prompt 定义全局行为、Role Prompt 定义场景角色、TASK Prompt 定义具体指令。AI 执行时三层叠加注入。

### 约束层技术细节

> **verify.sh 六阶段验收脚本**：
>
> ```bash
> # Stage 1: 规范符合性 — TASK 文件存在性检查
> # Stage 2: 类型安全 — tsc --noEmit
> # Stage 3: 测试 Harness — vitest run / pytest
> # Stage 4: 构建 Harness — vite build
> # Stage 5: 质量门禁 — turbo run lint / prettier --check
> # Stage 6: 规范文档检查 — AC 完整性 + 迭代复盘记录
> ```
>
> 每个阶段失败输出报告到 `.ai-harness/reports/TASK-{ID}-{timestamp}.md`。
>
> **CI 流水线**用 GitHub Actions 做变更检测：`dorny/paths-filter` 检测改了 `apps/**` 还是 `services/**`，只跑受影响包的测试。覆盖率策略渐进提升——后端 pytest 阈值 50%（当前 56%），不追求一步到位。
>
> **Git 钩子链**：Husky v9 + lint-staged v15 + Commitlint v19。Node 18 兼容性踩过坑——lint-staged v17 依赖 listr2 v10 要求 Node 20，降级到 v15 解决。

### 执行层技术细节

> **Rules（AGENTS.md）**是项目级编码规范，每次对话通过 `${KIMI_AGENTS_MD}` 自动注入。设计为精简高频规则（~50 行），只放每次编码必查的约束：禁止 `any`、API 前缀 `/api/v1`、quota_router 先于 proxy_router 注册、Redis 键名安全处理。
>
> **Skills** 是可复用任务模板，放在 `.agents/skills/` 下。以 `task-executor` Skill 为例：SKILL.md 定义触发条件 + 六步工作流 + 常见陷阱；references/ 下放详细参考（测试 mock 方法、类型断言技巧）。加载机制：metadata 始终在线，references 按需加载。

### 技术难点与解法

> **难点 1：proxy_router catch-all 拦截 API 路由**
>
> FastAPI 中 `proxy_router` 注册了 `/{service_name}/{path:path}`，会把 `/api/v1/customer/rules` 匹配成 `service_name=api`。解决：**路由注册顺序**，`quota_router` 必须在 `proxy_router` 之前 `app.include_router()`。
>
> **难点 2：CORS 预检请求被中间件拦截**
>
> 前端 dev server（localhost:5174）调后端（localhost:8000），浏览器先发 OPTIONS 预检。AuthMiddleware 没有 `/api/v1` 在 EXEMPT_PATHS 中，返回 401。解决：在 main.py 中注册 `CORSMiddleware`（`allow_origins=["*"]`），并确保它在中间件链最外层。
>
> **难点 3：jsdom 测试 Ant Design ProTable + Tabs**
>
> ProTable 依赖 ResizeObserver，jsdom 不支持；Tabs 组件也有同样问题。解决：在 `test/setup.ts` 中 mock ResizeObserver + IntersectionObserver，同时 ProLayout 的 `menuItemRender` 中父菜单跳转逻辑需要在 BrowserRouter 下测试。

---

## 四、量化对比表（面试杀手锏）

### 显性成本：工时对比

| 环节 | 传统方式 | Harness + SDD |
|------|---------|--------------|
| 需求对齐 | PRD 评审会 2h × 5人 = **10人时** | 写 TASK 规范 **30分钟** |
| 前端开发 | 列表+筛选+批量+详情 ≈ **3天** | AI 生成 + 人调整 ≈ **0.5天** |
| 后端开发 | CRUD + 搜索 + 权限 ≈ **3天** | AI 生成 + 联调 ≈ **0.5天** |
| 联调修 bug | 手机号脱敏漏了、批量上限没做 ≈ **1.5天** | verify.sh 拦截，**0.2天** |
| Code Review | 风格不统一、类型缺失 ≈ **0.5天** | lint-staged + typecheck 预提交拦截，**0天** |
| **总计** | **~9天** | **~1.3天** |

### 隐性成本

| 隐性成本 | 传统方式 | Harness + SDD |
|---------|---------|--------------|
| **知识流失** | 老员工离职，客户状态流转规则全丢了，新人翻代码翻两周 | 规则在 AGENTS.md + Skill references 里，**读 30 分钟上手** |
| **返工率** | 产品经理验收发现"批量分配没做权限校验"，开发返工 **30% 功能** | AC 里提前写了权限校验，**返工率 < 5%** |
| **沟通成本** | "这个筛选是实时还是点搜索按钮？"来回确认 3 轮 | TASK 规范里写死"筛选条件变化实时触发，debounce 300ms"，**0 轮确认** |
| **质量债** | "先上线后面再补测试"，半年后发现核心流程没单测，不敢重构 | verify.sh 强制"类型检查 + 测试覆盖"才能合并，**质量债不累积** |

---

## 五、常见面试追问 & 回答

### Q1：如果 AI 生成的代码 verify 失败了怎么办？

> 三步走：第一步看失败日志定位是哪条 AC 没通过；第二步修复代码；第三步最关键——复盘为什么 AI 会犯这个错，是规范描述不清、约束缺失、还是 Prompt 没覆盖这个场景，然后把教训写回 system-prompt 或 TASK 模板。下次同样的场景 AI 自动避免。这就是飞轮。

### Q2：这跟传统的 TDD/DDD 有什么区别？

> TDD 是"先写测试再写代码"，但测试是人写的；SDD 是"先写规范再写代码"，规范是给 AI 消费的契约文档，包含了 AC、边界条件、文件清单、Prompt 指令。Harness 层比 TDD 多了一道自动化执法——verify.sh + CI 不是人手动跑，是嵌入工作流的强制检查。

### Q3：Rules 和 Skills 具体怎么用？

> Rules 是 AGENTS.md 项目级编码规范，每次对话自动注入上下文，解决"AI 不知道项目约束"的问题。Skills 是可复用的任务模板，比如 task-executor Skill 封装了"读取 TASK → 按 AC 实现 → 自动验证 → 修复"的完整工作流。有新的前端页面需求，丢一个 TASK 规范给 AI，Skill 自动触发执行流程。

### Q4：你们团队产出提升了多少？

> 客户管理模块（列表+详情+标签+分群）传统估 3 周，我们用 Harness + SDD 实际 4 天。而且这 4 天里，有 2 天是第一轮写 TASK 模板和规范沉淀，后面三个模块复用模板，平均每个模块 0.5 天。更关键的是——不是快，是稳。上线后零 P0 故障，因为边界条件在 AC 里写死了，verify.sh 在合并前全拦住了。

### Q5：规范模板谁来维护？会不会变成负担？

> 规范不是一个人维护的，是**团队共建 + 飞轮驱动**。每周五 30 分钟周度复盘：运行 collect-metrics.sh → 填写周度报告 → 讨论 Top 3 问题。失败的 TASK 必须复盘归因，把教训写回模板。成功的 TASK 抽象成最佳实践，也写回模板。规范库每周自然进化 1-3 条约束，不是负担，是团队在"用规范喂 AI，AI 帮团队省时间"的正循环里。

### Q6：AI 生成代码质量怎么样？会不会有安全问题？

> 这正是 Harness 层的价值——AI 生成的不直接进仓库，必须经过六阶段验收：类型检查拦截类型错误、测试拦截逻辑错误、构建拦截打包错误、质量门禁拦截风格错误。安全层面，AuthMiddleware 做 API Key 鉴权、RateLimitMiddleware 做滑动窗口限流、QuotaMiddleware 做配额检查，三层防护不是 AI 写的，是工程化的基础设施。

---

## 六、背诵口诀

```
人定规范：先写 TASK，AC 逐条可勾选
AI 执工程：AI 按规范生成，机器自动验收
CRM 案例：客户列表 4 天交 3 周活，零 P0
飞轮进化：失败复盘升级模板，下次自动避免
数据说话：一次性通过率 80%，迭代轮次 1.4
本质跃迁：经验存在规范里，规范自我进化
```

---

*文档版本：v1.0*
*最后更新：2026-05-24*
