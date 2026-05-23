#!/bin/bash
set -e

echo "🔄 DevContainer 启动检查..."

# 检查 Redis 连接
cd /workspace/kk-ai/services/mcp-hub
python -c "
import redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)
r.ping()
print('✅ Redis 连接正常')
" 2>/dev/null || echo "⚠️ Redis 未就绪（将在首次启动时自动连接）"

echo "✅ 开发环境已就绪"
