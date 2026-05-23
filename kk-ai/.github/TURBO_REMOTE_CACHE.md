# Turbo Remote Cache 配置指南

## 为什么需要远程缓存？

```
本地开发                    CI 环境
  ├── 构建 cache              ├── 没有 cache（每次从零构建）
  └── 2s 完成                  └── 5min 完成

启用 Remote Cache 后：
  本地构建 → 上传 cache → CI 下载 cache → 秒级完成
```

## 方案一：Vercel Remote Cache（推荐，免费）

### 1. 注册并创建项目

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 在 kk-ai 目录下创建项目
vercel link
# 按提示选择项目名，如 kk-ai-monorepo
```

### 2. 获取 Token

```bash
# 生成个人访问令牌
vercel tokens create
# 保存输出的 token（如: abc123xyz）
```

### 3. 配置环境变量

```bash
# 本地开发
export TURBO_TOKEN=your_token_here
export TURBO_TEAM=your_team_slug       # 个人用户是你的用户名

# 添加到 CI Secrets
echo "your_token_here" | gh secret set TURBO_TOKEN --repo your-org/kk-ai
echo "your_team_slug" | gh secret set TURBO_TEAM --repo your-org/kk-ai
```

### 4. 启用远程缓存

修改 `turbo.json`：

```json
{
  "remoteCache": {
    "enabled": true,
    "signature": true
  }
}
```

### 5. 更新 CI 配置

在 `.github/workflows/ci.yml` 中添加：

```yaml
- name: Build
  run: cd kk-ai && pnpm run build
  env:
    TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
    TURBO_TEAM: ${{ secrets.TURBO_TEAM }}
```

## 方案二：GitHub Actions Cache（无需额外账号）

已在 `ci.yml` 中配置，使用 `actions/cache@v4` 缓存 `.turbo` 目录：

```yaml
- name: Setup Turbo Cache
  uses: actions/cache@v4
  with:
    path: .turbo
    key: ${{ runner.os }}-turbo-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-turbo-
```

**缺点**：仅在同一次 CI 运行的 job 间共享，跨 PR/分支不共享。

## 验证远程缓存

```bash
cd kk-ai
pnpm run build
# 输出应包含: "remote caching enabled"
```

## 配额说明

| 方案                 | 免费额度  | 付费          |
| -------------------- | --------- | ------------- |
| Vercel Remote Cache  | 14GB/月   | $20/月/100GB  |
| GitHub Actions Cache | 10GB/仓库 | 额外 $0.25/GB |

对于中小团队，Vercel 免费额度足够使用。
