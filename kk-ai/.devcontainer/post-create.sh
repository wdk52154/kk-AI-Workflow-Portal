#!/bin/bash
set -e

echo "🚀 DevContainer 初始化中..."

# 安装 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "→ 安装 pnpm..."
    npm install -g pnpm@9
fi

# 安装前端依赖
echo "→ 安装前端依赖..."
cd /workspace/kk-ai
pnpm install

# 安装后端依赖
echo "→ 安装后端依赖..."
cd /workspace/kk-ai/services/mcp-hub
pip install -r requirements.txt
pip install pytest pytest-asyncio mypy ruff httpx

# 安装 Playwright
echo "→ 安装 Playwright..."
cd /workspace/kk-ai/apps/web-admin
pnpm add -D @playwright/test
npx playwright install chromium

echo "✅ DevContainer 初始化完成！"
echo ""
echo "可用命令："
echo "  pnpm run dev       # 启动前端 + 后端 dev server"
echo "  pnpm run build     # 构建全仓库"
echo "  pnpm run test      # 运行全仓库测试"
echo ""
