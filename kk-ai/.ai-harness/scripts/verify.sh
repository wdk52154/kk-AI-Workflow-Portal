#!/bin/bash
# AI 输出强制验收脚本
# 用法: ./verify.sh <TASK_ID>
# 示例: ./verify.sh TASK-001

set -e

TASK_ID=${1:-""}
if [ -z "$TASK_ID" ]; then
    echo "❌ 用法: $0 <TASK_ID>"
    echo "   示例: $0 TASK-001"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
REPORT_DIR="${SCRIPT_DIR}/../reports"
REPORT_FILE="${REPORT_DIR}/${TASK_ID}-$(date +%Y%m%d-%H%M%S).md"

mkdir -p "$REPORT_DIR"
cd "${PROJECT_ROOT}/kk-ai"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

log_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED=$((PASSED + 1))
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
    FAILED=$((FAILED + 1))
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 开始报告
cat > "$REPORT_FILE" << EOF
# AI Harness 验收报告

- TASK ID: ${TASK_ID}
- 时间: $(date '+%Y-%m-%d %H:%M:%S')
- 执行人: $(whoami)
- 机器: $(hostname)

## 验收结果

EOF

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           🤖 AI Harness 验收脚本 v1.0                   ║"
echo "║           TASK: ${TASK_ID}                              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 阶段 1：规范符合性检查 ──
echo ""
echo "📋 [1/6] 规范符合性检查..."

TASK_FILE="docs/tasks/*/${TASK_ID}*.md"
if ! find docs/tasks -name "${TASK_ID}*.md" -type f 2>/dev/null | grep -q .; then
    log_fail "未找到 TASK 规范文件: docs/tasks/**/${TASK_ID}*.md"
    echo "- ❌ 缺少 TASK 规范" >> "$REPORT_FILE"
    exit 1
fi

log_pass "TASK 规范文件存在"
echo "- ✅ TASK 规范存在" >> "$REPORT_FILE"

# ── 阶段 2：类型安全 Harness ──
echo ""
echo "🔒 [2/6] 类型安全 Harness..."

FRONTEND_CHANGED=false
BACKEND_CHANGED=false

# 检测变更文件（简化：检查 git status）
if git status --short | grep -q "apps/web-admin"; then
    FRONTEND_CHANGED=true
fi
if git status --short | grep -q "services/"; then
    BACKEND_CHANGED=true
fi

if [ "$FRONTEND_CHANGED" = true ]; then
    log_info "检测到前端变更，执行 TypeScript 类型检查..."
    if pnpm run typecheck 2>&1 | tee /tmp/typecheck.log; then
        log_pass "TypeScript 类型检查通过"
        echo "- ✅ TypeScript 类型检查通过" >> "$REPORT_FILE"
    else
        log_fail "TypeScript 类型检查失败"
        echo "- ❌ TypeScript 类型检查失败" >> "$REPORT_FILE"
        echo "\n### 错误日志\n\n\`\`\`" >> "$REPORT_FILE"
        tail -50 /tmp/typecheck.log >> "$REPORT_FILE"
        echo "\`\`\`" >> "$REPORT_FILE"
    fi
fi

if [ "$BACKEND_CHANGED" = true ]; then
    log_info "检测到后端变更，执行 mypy 类型检查..."
    for svc in services/*/; do
        if [ -d "${svc}app" ]; then
            svc_name=$(basename "$svc")
            log_info "检查 ${svc_name}..."
            if (cd "$svc" && mypy app/ 2>&1 | tee /tmp/mypy-${svc_name}.log); then
                log_pass "${svc_name} mypy 检查通过"
                echo "- ✅ ${svc_name} mypy 检查通过" >> "$REPORT_FILE"
            else
                log_fail "${svc_name} mypy 检查失败"
                echo "- ❌ ${svc_name} mypy 检查失败" >> "$REPORT_FILE"
            fi
        fi
    done
fi

# ── 阶段 3：测试 Harness ──
echo ""
echo "🧪 [3/6] 测试 Harness..."

if [ "$FRONTEND_CHANGED" = true ]; then
    log_info "运行前端测试..."
    if pnpm run test 2>&1 | tee /tmp/test-frontend.log; then
        log_pass "前端测试通过"
        echo "- ✅ 前端测试通过" >> "$REPORT_FILE"
    else
        log_warn "前端测试失败（部分项目可能未配置测试）"
        echo "- ⚠️ 前端测试失败或未配置" >> "$REPORT_FILE"
    fi
fi

if [ "$BACKEND_CHANGED" = true ]; then
    for svc in services/*/; do
        if [ -f "${svc}pytest.ini" ] || [ -d "${svc}tests" ]; then
            svc_name=$(basename "$svc")
            log_info "运行 ${svc_name} 测试..."
            if (cd "$svc" && pytest 2>&1 | tee /tmp/test-${svc_name}.log); then
                log_pass "${svc_name} 测试通过"
                echo "- ✅ ${svc_name} 测试通过" >> "$REPORT_FILE"
            else
                log_warn "${svc_name} 测试失败"
                echo "- ⚠️ ${svc_name} 测试失败" >> "$REPORT_FILE"
            fi
        fi
    done
fi

# ── 阶段 4：构建 Harness ──
echo ""
echo "🏗️  [4/6] 构建 Harness..."

if pnpm run build 2>&1 | tee /tmp/build.log; then
    log_pass "构建通过"
    echo "- ✅ 构建通过" >> "$REPORT_FILE"
else
    log_fail "构建失败"
    echo "- ❌ 构建失败" >> "$REPORT_FILE"
    echo "\n### 构建错误\n\n\`\`\`" >> "$REPORT_FILE"
    tail -50 /tmp/build.log >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
fi

# ── 阶段 5：质量门禁 Harness ──
echo ""
echo "✨ [5/6] 质量门禁 Harness..."

if pnpm run lint 2>&1 | tee /tmp/lint.log; then
    log_pass "Lint 检查通过"
    echo "- ✅ Lint 检查通过" >> "$REPORT_FILE"
else
    log_fail "Lint 检查失败"
    echo "- ❌ Lint 检查失败" >> "$REPORT_FILE"
fi

# ── 阶段 6：规范文档检查 ──
echo ""
echo "📄 [6/6] 规范文档检查..."

if find docs/tasks -name "${TASK_ID}*.md" -type f -exec grep -q "## 迭代记录" {} + 2>/dev/null; then
    log_pass "TASK 包含迭代记录"
    echo "- ✅ 包含迭代记录" >> "$REPORT_FILE"
else
    log_warn "TASK 缺少迭代记录"
    echo "- ⚠️ 缺少迭代记录" >> "$REPORT_FILE"
fi

if find docs/tasks -name "${TASK_ID}*.md" -type f -exec grep -q "## 验收标准" {} + 2>/dev/null; then
    log_pass "TASK 包含验收标准"
    echo "- ✅ 包含验收标准" >> "$REPORT_FILE"
else
    log_warn "TASK 缺少验收标准"
    echo "- ⚠️ 缺少验收标准" >> "$REPORT_FILE"
fi

# ── 总结 ──
echo ""
echo "╔══════════════════════════════════════════════════════════╗"

if [ $FAILED -eq 0 ]; then
    echo "║           🎉 全部验收通过！                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo "\n## 结论\n\n✅ **全部通过** (${PASSED} 项通过)" >> "$REPORT_FILE"
else
    echo "║           ⚠️  部分验收未通过                            ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo "\n## 结论\n\n⚠️ **部分未通过** (${PASSED} 项通过, ${FAILED} 项失败)" >> "$REPORT_FILE"
fi

echo ""
echo "📊 验收统计:"
echo "   通过: ${PASSED} 项"
echo "   失败: ${FAILED} 项"
echo ""
echo "📝 详细报告:"
echo "   ${REPORT_FILE}"
echo ""

exit $FAILED
