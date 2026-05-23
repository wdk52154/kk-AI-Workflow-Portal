#!/bin/bash
# 收集 AI 工程化度量数据
# 用法: ./collect-metrics.sh [WEEK_START_DATE]

WEEK_START=${1:-$(date -v-monday +%Y-%m-%d 2>/dev/null || date -d "last monday" +%Y-%m-%d 2>/dev/null || echo "$(date +%Y-%m-%d)")}
REPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../metrics"
mkdir -p "$REPORT_DIR"

OUTPUT_FILE="${REPORT_DIR}/data-${WEEK_START}.json"

echo "📊 收集度量数据: ${WEEK_START} 所在周"

# 收集 git log 中 feat/fix 提交数（作为开发活跃度参考）
FEAT_COUNT=$(git log --since="${WEEK_START}" --pretty=format:"%s" | grep -c "^feat" || echo "0")
FIX_COUNT=$(git log --since="${WEEK_START}" --pretty=format:"%s" | grep -c "^fix" || echo "0")

echo "  本周 feat 提交: ${FEAT_COUNT}"
echo "  本周 fix 提交: ${FIX_COUNT}"

# 收集 TASK 文件数
TASK_COUNT=$(find docs/tasks -name "TASK-*.md" -type f | wc -l | tr -d ' ')
echo "  TASK 总数: ${TASK_COUNT}"

# 收集验收报告数
REPORT_COUNT=$(find .ai-harness/reports -name "TASK-*-*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "  验收报告数: ${REPORT_COUNT}"

# 生成 JSON
cat > "$OUTPUT_FILE" << EOF
{
  "week_start": "${WEEK_START}",
  "collected_at": "$(date -Iseconds)",
  "git": {
    "feat_commits": ${FEAT_COUNT},
    "fix_commits": ${FIX_COUNT}
  },
  "tasks": {
    "total": ${TASK_COUNT},
    "reports": ${REPORT_COUNT}
  }
}
EOF

echo "✅ 数据已保存: ${OUTPUT_FILE}"
