# TASK-404：Prompt Center（service-prompt）

## 元信息

| 字段     | 值                                             |
| -------- | ---------------------------------------------- |
| TASK ID  | TASK-404                                       |
| 标题     | Prompt Center - MCP 原生 Prompt 模板引擎       |
| 负责人   | @backend-lead                                  |
| 优先级   | P0                                             |
| 预估工时 | 5h                                             |
| 关联需求 | MCP HUB Gateway 路由转发、TASK-401 LLM Gateway |

---

## 1. 背景

AI 中台需要统一的 Prompt 管理中心，解决以下问题：

1. **Prompt 散落在各项目**：每个服务各自维护 Prompt，版本混乱，无法复用
2. **变量插值手动拼接**：业务代码里用 f-string 拼接 Prompt，容易出错，难以维护
3. **热更新困难**：改一个 Prompt 要重启服务，影响线上体验
4. **缺乏分类管理**：system prompt、user prompt、rag prompt、sales prompt 混在一起

MCP（Model Context Protocol）原生支持 `@server.prompt()` 装饰器来注册和暴露 Prompt。我们借鉴这一设计，但将其独立为服务，供所有下游服务统一调用。

---

## 2. 目标

实现 `service-prompt` 服务（端口 9004），作为 AI 中台的统一 Prompt 模板引擎：

- **MCP 风格接口**：兼容 `@server.prompt()` 的注册和获取语义
- **YAML 模板引擎**：Jinja2 风格变量插值 `{{variable}}`
- **热更新**：文件变更后 5 秒内生效
- **分类管理**：system / user / assistant / tool / rag / sales / voice
- **版本追踪**：支持 Prompt 版本号，便于 A/B 测试和回滚

---

## 3. 验收标准

### AC-1：Prompt 模板管理

- [ ] `GET /v1/prompts/{prompt_id}` 获取指定 Prompt 模板元数据
- [ ] 返回包含：`prompt_id`、`name`、`category`、`version`、`description`、`template`（原始 YAML 内容）
- [ ] Prompt 不存在返回 404，`{"error": "PROMPT_NOT_FOUND", "message": "..."}`

### AC-2：Prompt 渲染

- [ ] `POST /v1/prompts/{prompt_id}/render` 传入变量，渲染最终 Prompt
- [ ] 请求体：`{"variables": {"product_name": "iPhone", "price": "5999"}}`
- [ ] 支持 Jinja2 风格变量插值：`{{product_name}}`、`{{price | default('unknown')}}`
- [ ] 支持条件渲染：`{% if vip %}尊享客户{% else %}普通客户{% endif %}`
- [ ] 返回渲染后的完整文本：
  ```json
  {
    "prompt_id": "sales_intro",
    "rendered": "欢迎来到 Apple 商店，iPhone 售价 5999 元...",
    "variables_used": ["product_name", "price"],
    "variables_missing": []
  }
  ```
- [ ] 缺少必需变量时返回 400，`{"error": "MISSING_VARIABLES", "missing": ["price"]}`

### AC-3：Prompt 注册

- [ ] `POST /v1/prompts` 注册新 Prompt
- [ ] 请求体支持两种方式：
  - **内联模式**：直接传入 `prompt_id`、`category`、`template` 文本
  - **YAML 文件模式**：上传 YAML 文件，自动解析
- [ ] 自动分配版本号（v1.0.0），相同 prompt_id 更新时版本自增
- [ ] 返回：`prompt_id`、`version`、`status`

### AC-4：Prompt 分类与列表

- [ ] `GET /v1/prompts` 列出所有 Prompt，支持 `category` 过滤
- [ ] `GET /v1/prompts?category=rag` 只返回 RAG 类 Prompt
- [ ] 返回格式：
  ```json
  {
    "items": [
      {
        "prompt_id": "rag_retrieve",
        "name": "RAG 检索增强",
        "category": "rag",
        "version": "1.2.0"
      }
    ],
    "total": 1
  }
  ```

### AC-5：YAML 模板引擎

- [ ] 所有 Prompt 存储为 YAML 文件：`prompts/{category}/{prompt_id}.yaml`
- [ ] YAML 结构：
  ```yaml
  id: sales_intro
  name: 销售开场白
  category: sales
  version: 1.0.0
  description: 用于销售场景的开场白模板
  author: team-sales
  variables:
    - name: product_name
      required: true
      description: 产品名称
    - name: price
      required: true
      description: 产品价格
    - name: vip
      required: false
      default: false
      description: 是否 VIP 客户
  template: |
    欢迎来到我们的商店！
    今天为您推荐的是 {{ product_name }}，售价 {{ price }} 元。
    {% if vip %}
    作为尊享客户，您可享受额外 9 折优惠！
    {% endif %}
    请问有什么可以帮您的？
  ```

### AC-6：热更新

- [ ] 监控 `prompts/` 目录，文件变更后 5 秒内自动重载
- [ ] 使用 `watchdog` 或定时轮询（间隔 5s）
- [ ] 加载失败时保留旧版本，打印 error 日志，不影响运行中的服务

### AC-7：MCP 兼容接口

- [ ] `GET /mcp/prompts` 返回 MCP 风格的 Prompt 列表
- [ ] `GET /mcp/prompts/{prompt_id}` 返回 MCP 风格的 Prompt 详情
- [ ] 格式参考 MCP 规范：
  ```json
  {
    "name": "sales_intro",
    "description": "销售开场白模板",
    "arguments": [
      { "name": "product_name", "description": "产品名称", "required": true }
    ]
  }
  ```

### AC-8：健康检查

- [ ] `GET /health` 返回服务状态、已加载 Prompt 数量、最后更新时间

### AC-9：测试与质量

- [ ] `pytest` 全部通过，覆盖率 ≥ 50%
- [ ] 至少 2 个渲染测试（简单插值 + 条件渲染）
- [ ] 至少 2 个热更新测试（文件修改后自动生效）
- [ ] 至少 1 个 MCP 兼容接口测试
- [ ] 至少 1 个缺少变量错误处理测试

---

## 4. 技术方案

### 项目结构

```
services/service-prompt/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # Pydantic Settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── prompt.py        # Prompt Pydantic 模型
│   ├── router/
│   │   ├── __init__.py
│   │   ├── prompts.py       # /v1/prompts CRUD + render
│   │   └── mcp.py           # /mcp/prompts MCP 兼容接口
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prompt_manager.py # Prompt 加载/管理/热更新
│   │   └── template_engine.py # Jinja2 渲染引擎
│   └── middleware/
│       └── logger.py
├── prompts/                 # YAML Prompt 模板目录
│   ├── system/
│   │   └── default_system.yaml
│   ├── rag/
│   │   └── retrieve_context.yaml
│   ├── sales/
│   │   └── sales_intro.yaml
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_prompts.py
│   ├── test_render.py
│   └── test_hot_reload.py
├── pyproject.toml
├── run.py
└── .env.example
```

### Prompt YAML 格式

```yaml
# prompts/sales/sales_intro.yaml
id: sales_intro
name: 销售开场白
category: sales
version: 1.0.0
description: 用于销售场景的开场白模板
author: team-sales
tags: [销售, 开场]

variables:
  - name: product_name
    required: true
    description: 产品名称
    example: iPhone 15
  - name: price
    required: true
    description: 产品价格
    example: "5999"
  - name: vip
    required: false
    default: false
    type: boolean
    description: 是否 VIP 客户

template: |
  欢迎来到我们的商店！
  今天为您推荐的是 {{ product_name }}，售价 {{ price }} 元。
  {% if vip %}
  作为尊享客户，您可享受额外 9 折优惠！
  {% endif %}
  请问有什么可以帮您的？

# 多消息模板（支持 system/user/assistant 分离）
messages:
  - role: system
    content: |
      你是一位专业的销售顾问，正在为客户介绍 {{ product_name }}。
  - role: user
    content: |
      请给我介绍一下 {{ product_name }}，价格是 {{ price }} 元。
```

### Prompt Manager

```python
# app/services/prompt_manager.py
import os
import threading
import time
from typing import Any

import yaml

class PromptManager:
    """Manages prompt templates from YAML files with hot-reload."""

    def __init__(self, prompts_dir: str = "./prompts"):
        self.prompts_dir = prompts_dir
        self._prompts: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._last_modified: dict[str, float] = {}
        self._last_check = 0.0
        self._reload_interval = 5.0

        self._load_all()

    def _load_all(self) -> None:
        """Load all prompt YAML files."""
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir, exist_ok=True)
            return

        for root, _, files in os.walk(self.prompts_dir):
            for filename in files:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    filepath = os.path.join(root, filename)
                    self._load_file(filepath)

    def _load_file(self, filepath: str) -> None:
        """Load a single prompt YAML file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "id" not in data:
                return

            prompt_id = data["id"]
            with self._lock:
                self._prompts[prompt_id] = data
                self._last_modified[prompt_id] = os.path.getmtime(filepath)

        except Exception as exc:
            logger.error("Failed to load prompt %s: %s", filepath, exc)

    def check_reload(self) -> bool:
        """Check for file changes and reload if needed."""
        now = time.time()
        if now - self._last_check < self._reload_interval:
            return False
        self._last_check = now

        changed = False
        for root, _, files in os.walk(self.prompts_dir):
            for filename in files:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    filepath = os.path.join(root, filename)
                    try:
                        mtime = os.path.getmtime(filepath)
                        # Extract prompt_id from file to check
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        if data and "id" in data:
                            prompt_id = data["id"]
                            last = self._last_modified.get(prompt_id, 0)
                            if mtime > last:
                                self._load_file(filepath)
                                changed = True
                    except Exception:
                        pass
        return changed

    def get_prompt(self, prompt_id: str) -> dict | None:
        self.check_reload()
        with self._lock:
            return self._prompts.get(prompt_id)

    def list_prompts(self, category: str | None = None) -> list[dict]:
        self.check_reload()
        with self._lock:
            prompts = list(self._prompts.values())
            if category:
                prompts = [p for p in prompts if p.get("category") == category]
            return prompts

    def register_prompt(self, data: dict) -> str:
        """Register a new prompt (inline or from file)."""
        prompt_id = data["id"]
        category = data.get("category", "uncategorized")

        # Save to file
        category_dir = os.path.join(self.prompts_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        filepath = os.path.join(category_dir, f"{prompt_id}.yaml")

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

        with self._lock:
            self._prompts[prompt_id] = data
            self._last_modified[prompt_id] = os.path.getmtime(filepath)

        return prompt_id
```

### 模板渲染引擎

```python
# app/services/template_engine.py
from jinja2 import Environment, UndefinedError, meta

class TemplateEngine:
    """Jinja2-based template rendering engine."""

    def __init__(self):
        self.env = Environment()

    def render(self, template_text: str, variables: dict) -> str:
        """Render a template with variables."""
        template = self.env.from_string(template_text)
        return template.render(**variables)

    def get_variables(self, template_text: str) -> set[str]:
        """Extract variable names from template."""
        ast = self.env.parse(template_text)
        return meta.find_undeclared_variables(ast)

    def validate(self, prompt_data: dict, variables: dict) -> tuple[bool, list[str]]:
        """Validate that all required variables are provided."""
        template = prompt_data.get("template", "")
        declared_vars = self.get_variables(template)

        prompt_vars = {v["name"] for v in prompt_data.get("variables", []) if v.get("required")}
        missing = [v for v in prompt_vars if v not in variables]

        return len(missing) == 0, missing
```

### MCP 兼容格式转换

```python
# app/router/mcp.py
@router.get("/mcp/prompts")
async def mcp_list_prompts():
    """MCP-compatible prompt list."""
    manager = get_prompt_manager()
    prompts = manager.list_prompts()
    return {
        "prompts": [
            {
                "name": p["id"],
                "description": p.get("description", ""),
            }
            for p in prompts
        ]
    }

@router.get("/mcp/prompts/{prompt_id}")
async def mcp_get_prompt(prompt_id: str):
    """MCP-compatible prompt detail."""
    manager = get_prompt_manager()
    prompt = manager.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return {
        "name": prompt["id"],
        "description": prompt.get("description", ""),
        "arguments": [
            {
                "name": v["name"],
                "description": v.get("description", ""),
                "required": v.get("required", False),
            }
            for v in prompt.get("variables", [])
        ],
    }
```

### 约束条件

- [ ] 所有 Prompt 以 YAML 文件形式存储，禁止硬编码模板
- [ ] 模板引擎使用 Jinja2，支持变量插值、条件、循环
- [ ] 热更新不重启服务，失败时保留旧版本
- [ ] 相同 `prompt_id` 更新时版本号自增（`version` 字段）
- [ ] 缺少必需变量时返回 400，不渲染
- [ ] MCP 接口与业务接口分离，便于后续独立部署

---

## 5. 依赖与阻塞

| 依赖项            | 状态      | 说明             |
| ----------------- | --------- | ---------------- |
| FastAPI + Uvicorn | ✅ 已完成 | 框架就绪         |
| Jinja2            | ⚠️ 需安装 | 模板渲染引擎     |
| PyYAML            | ✅ 已完成 | YAML 解析        |
| watchdog（可选）  | ⚠️ 需安装 | 文件监控热更新   |
| MCP HUB Gateway   | ✅ 已完成 | 统一入口路由转发 |

---

## 6. 风险与应对

| 风险                       | 影响 | 应对策略                             |
| -------------------------- | ---- | ------------------------------------ |
| Jinja2 模板注入（SSTI）    | 高   | 沙箱渲染，禁用危险内置函数和模块     |
| YAML 语法错误导致加载失败  | 中   | 加载失败保留旧版本，打印详细错误日志 |
| 大量 Prompt 文件导致启动慢 | 低   | 懒加载 + 缓存，首次访问时加载        |
| 变量命名冲突               | 低   | 命名空间前缀，如 `{{ user.name }}`   |

---

## 7. Prompt

```markdown
【Situation】
AI 中台需要统一的 Prompt 模板引擎（端口 9004），支持 YAML 配置、Jinja2 渲染、热更新。
所有下游服务（LLM Gateway、RAG、Memory）都将从这里获取 Prompt。

【Task】
实现 service-prompt，提供 MCP 风格的 Prompt 管理和 Jinja2 渲染。

【Action】

1. 创建项目结构 `services/service-prompt/`
2. 实现 `PromptManager`（YAML 加载 + 热更新）
3. 实现 `TemplateEngine`（Jinja2 渲染 + 变量校验）
4. 实现路由：
   - GET /v1/prompts（列表）
   - GET /v1/prompts/{prompt_id}（详情）
   - POST /v1/prompts/{prompt_id}/render（渲染）
   - POST /v1/prompts（注册）
   - GET /mcp/prompts（MCP 兼容列表）
   - GET /mcp/prompts/{prompt_id}（MCP 兼容详情）
5. 预置示例 Prompt YAML（system、rag、sales 各 1 个）
6. 实现健康检查 GET /health
7. 编写测试

【Constraint】

- 所有 Prompt 存 YAML 文件
- Jinja2 渲染，支持条件/循环
- 热更新 5 秒内生效
- 沙箱渲染（禁用危险函数）
- pytest 覆盖率 ≥50%

【Verification】

- pytest tests/ -v --cov=app --cov-fail-under=50
- curl http://localhost:9004/v1/prompts
- curl -H "Content-Type: application/json" -d '{"variables":{"product_name":"iPhone","price":"5999"}}' http://localhost:9004/v1/prompts/sales_intro/render
- curl http://localhost:9004/mcp/prompts
```

---

## 8. 迭代记录

| 轮次 | AI 输出  | 人验收结果 | 修复点 |
| ---- | -------- | ---------- | ------ |
| R1   | 初始实现 | ⬜ 待验收  | -      |
