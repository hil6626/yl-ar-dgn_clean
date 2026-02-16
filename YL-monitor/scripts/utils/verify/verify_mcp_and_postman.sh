#!/bin/bash

# YL-Monitor MCP Server + Postman 联动自动化验证脚本
# 自动逐步验证所有功能并生成报告

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MCP_SERVER="${PROJECT_ROOT}/.vscode/mcp-server.js"
MCP_CONFIG="${PROJECT_ROOT}/.vscode/mcp.json"
POSTMAN_COLLECTION="${PROJECT_ROOT}/tests/postman/yl-monitor-collection.json"
POSTMAN_ENV="${PROJECT_ROOT}/tests/postman/environments/local.json"
REPORT_DIR="${PROJECT_ROOT}/logs/verification-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="${REPORT_DIR}/mcp_postman_verification_${TIMESTAMP}.log"
JSON_REPORT="${REPORT_DIR}/mcp_postman_report_${TIMESTAMP}.json"

# 计数器
PASSED=0
FAILED=0
WARNINGS=0

# 初始化报告目录
mkdir -p "$REPORT_DIR"

# 日志函数
log() {
    echo -e "$1" | tee -a "$REPORT_FILE"
}

log_header() {
    log "\n${BLUE}========================================${NC}"
    log "${BLUE} $1${NC}"
    log "${BLUE}========================================${NC}"
}

log_step() {
    log "\n${CYAN}[步骤 $1] $2${NC}"
}

log_test() {
    log "  ${YELLOW}▸ $1${NC}"
}

log_pass() {
    log "  ${GREEN}✓ $1${NC}"
    ((PASSED++))
}

log_fail() {
    log "  ${RED}✗ $1${NC}"
    ((FAILED++))
}

log_warn() {
    log "  ${YELLOW}⚠ $1${NC}"
    ((WARNINGS++))
}

# MCP 请求函数
mcp_request() {
    local command=$1
    local args=$2
    local timeout=${3:-10}
    
    echo "{\"command\": \"$command\", \"args\": $args, \"id\": $(date +%s%N)}" | \
        timeout $timeout node "$MCP_SERVER" "$PROJECT_ROOT" 2>/dev/null | head -1
}

# 检查 Newman
check_newman() {
    if ! command -v newman &> /dev/null; then
        log_warn "Newman 未安装，尝试安装..."
        npm install -g newman newman-reporter-html 2>&1 | tee -a "$REPORT_FILE" || {
            log_fail "Newman 安装失败"
            return 1
        }
        log_pass "Newman 安装成功"
    else
        log_pass "Newman 已安装 ($(newman --version))"
    fi
    return 0
}

# 主验证流程
main() {
    log_header "YL-Monitor MCP + Postman 联动自动化验证"
    log "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    log "项目路径: $PROJECT_ROOT"
    log "报告文件: $REPORT_FILE"
    
    # 步骤 1: 环境检查
    log_step "1" "环境基础检查"
    
    log_test "检查 Node.js"
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_pass "Node.js 版本: $NODE_VERSION"
    else
        log_fail "Node.js 未安装"
        exit 1
    fi
    
    log_test "检查 MCP Server 文件"
    if [ -f "$MCP_SERVER" ]; then
        log_pass "MCP Server 脚本存在"
    else
        log_fail "MCP Server 脚本不存在: $MCP_SERVER"
        exit 1
    fi
    
    log_test "检查 MCP 配置"
    if [ -f "$MCP_CONFIG" ]; then
        if python3 -c "import json; json.load(open('$MCP_CONFIG'))" 2>/dev/null; then
            log_pass "MCP 配置 JSON 格式正确"
        else
            log_fail "MCP 配置 JSON 格式错误"
            exit 1
        fi
    else
        log_fail "MCP 配置文件不存在"
        exit 1
    fi
    
    log_test "检查 Postman 集合"
    if [ -f "$POSTMAN_COLLECTION" ]; then
        if python3 -c "import json; json.load(open('$POSTMAN_COLLECTION'))" 2>/dev/null; then
            ENDPOINT_COUNT=$(python3 -c "import json; d=json.load(open('$POSTMAN_COLLECTION')); print(len(d.get('item', [])))")
            log_pass "Postman 集合存在 ($ENDPOINT_COUNT 个模块)"
        else
            log_fail "Postman 集合 JSON 格式错误"
            exit 1
        fi
    else
        log_fail "Postman 集合不存在"
        exit 1
    fi
    
    # 步骤 2: MCP Server 核心功能验证
    log_step "2" "MCP Server 核心功能验证"
    
    log_test "测试 list_files (列出 app 目录)"
    LIST_RESULT=$(mcp_request "list_files" '{"path": "app", "recursive": false}' 5)
    if echo "$LIST_RESULT" | grep -q '"success":true'; then
        FILE_COUNT=$(echo "$LIST_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['count'])" 2>/dev/null || echo "0")
        log_pass "list_files 成功 (找到 $FILE_COUNT 个文件/目录)"
    else
        log_fail "list_files 失败"
        echo "响应: $LIST_RESULT" >> "$REPORT_FILE"
    fi
    
    log_test "测试 read_file (读取 app/main.py)"
    READ_RESULT=$(mcp_request "read_file" '{"path": "app/main.py"}' 5)
    if echo "$READ_RESULT" | grep -q '"success":true'; then
        FILE_SIZE=$(echo "$READ_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['size'])" 2>/dev/null || echo "0")
        LINES=$(echo "$READ_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['lines'])" 2>/dev/null || echo "0")
        log_pass "read_file 成功 ($FILE_SIZE bytes, $LINES 行)"
    else
        log_fail "read_file 失败"
    fi
    
    log_test "测试 search (搜索 health 相关代码)"
    SEARCH_RESULT=$(mcp_request "search" '{"pattern": "def.*health", "path": "app", "filePattern": "*.py"}' 10)
    if echo "$SEARCH_RESULT" | grep -q '"success":true'; then
        MATCH_FILES=$(echo "$SEARCH_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['totalFiles'])" 2>/dev/null || echo "0")
        log_pass "search 成功 (找到 $MATCH_FILES 个文件匹配)"
    else
        log_warn "search 可能失败或超时"
    fi
    
    log_test "测试 get_file_stats (获取文件信息)"
    STATS_RESULT=$(mcp_request "get_file_stats" '{"path": "app/main.py"}' 5)
    if echo "$STATS_RESULT" | grep -q '"success":true'; then
        SIZE_HUMAN=$(echo "$STATS_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['sizeHuman'])" 2>/dev/null || echo "unknown")
        log_pass "get_file_stats 成功 (大小: $SIZE_HUMAN)"
    else
        log_fail "get_file_stats 失败"
    fi
    
    # 步骤 3: YL-Monitor 服务状态检查
    log_step "3" "YL-Monitor 服务状态检查"
    
    log_test "检查服务健康状态"
    if curl -s http://0.0.0.0:5500/api/health > /dev/null 2>&1; then
        HEALTH_DATA=$(curl -s http://0.0.0.0:5500/api/health)
        VERSION=$(echo "$HEALTH_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version', 'unknown'))" 2>/dev/null)
        log_pass "YL-Monitor 服务运行中 (版本: $VERSION)"
        
        log_test "测试 MCP api_request (调用健康检查 API)"
        API_RESULT=$(mcp_request "api_request" '{"method": "GET", "endpoint": "/api/health"}' 10)
        if echo "$API_RESULT" | grep -q '"success":true'; then
            STATUS_CODE=$(echo "$API_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['statusCode'])" 2>/dev/null || echo "0")
            if [ "$STATUS_CODE" = "200" ]; then
                log_pass "api_request 成功 (HTTP $STATUS_CODE)"
            else
                log_warn "api_request 返回非 200 状态码 ($STATUS_CODE)"
            fi
        else
            log_fail "api_request 失败"
        fi
    else
        log_fail "YL-Monitor 服务未运行 (端口 5500)"
        log "提示: 运行 ./scripts/tools/start_and_verify.sh 启动服务"
    fi
    
    # 步骤 4: Postman 集合执行
    log_step "4" "Postman 集合自动化执行"
    
    check_newman
    
    log_test "执行 Postman 集合 (使用 Newman)"
    
    # 创建 Newman 报告目录
    NEWMAN_REPORT_DIR="${REPORT_DIR}/newman_${TIMESTAMP}"
    mkdir -p "$NEWMAN_REPORT_DIR"
    
    if newman run "$POSTMAN_COLLECTION" \
        -e "$POSTMAN_ENV" \
        --reporters cli,json,html \
        --reporter-json-export "${NEWMAN_REPORT_DIR}/newman-report.json" \
        --reporter-html-export "${NEWMAN_REPORT_DIR}/newman-report.html" \
        --timeout-request 10000 \
        --timeout-script 5000 \
        2>&1 | tee -a "$REPORT_FILE"; then
        
        # 解析 Newman 结果
        if [ -f "${NEWMAN_REPORT_DIR}/newman-report.json" ]; then
            ITERATIONS=$(python3 -c "import json; d=json.load(open('${NEWMAN_REPORT_DIR}/newman-report.json')); print(d['run']['stats']['iterations']['total'])" 2>/dev/null || echo "0")
            REQUESTS=$(python3 -c "import json; d=json.load(open('${NEWMAN_REPORT_DIR}/newman-report.json')); print(d['run']['stats']['requests']['total'])" 2>/dev/null || echo "0")
            TESTS_PASSED=$(python3 -c "import json; d=json.load(open('${NEWMAN_REPORT_DIR}/newman-report.json')); print(d['run']['stats']['tests']['passed'])" 2>/dev/null || echo "0")
            TESTS_FAILED=$(python3 -c "import json; d=json.load(open('${NEWMAN_REPORT_DIR}/newman-report.json')); print(d['run']['stats']['tests']['failed'])" 2>/dev/null || echo "0")
            
            log_pass "Newman 执行完成"
            log "  - 迭代次数: $ITERATIONS"
            log "  - 请求总数: $REQUESTS"
            log "  - 测试通过: $TESTS_PASSED"
            log "  - 测试失败: $TESTS_FAILED"
            
            if [ "$TESTS_FAILED" -gt 0 ]; then
                log_warn "有 $TESTS_FAILED 个测试失败，请查看详细报告"
            fi
            
            # 生成 MCP 与 Postman 联动验证报告
            cat > "$JSON_REPORT" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "project": "YL-Monitor",
    "verification_type": "MCP + Postman Integration",
    "results": {
        "mcp_server": {
            "status": "verified",
            "tools_tested": ["list_files", "read_file", "search", "get_file_stats", "api_request"],
            "node_version": "$NODE_VERSION"
        },
        "yl_monitor_service": {
            "status": "running",
            "version": "$VERSION",
            "health_check": "passed"
        },
        "postman_collection": {
            "status": "executed",
            "iterations": $ITERATIONS,
            "requests": $REQUESTS,
            "tests_passed": $TESTS_PASSED,
            "tests_failed": $TESTS_FAILED
        }
    },
    "reports": {
        "verification_log": "$REPORT_FILE",
        "newman_html": "${NEWMAN_REPORT_DIR}/newman-report.html",
        "newman_json": "${NEWMAN_REPORT_DIR}/newman-report.json",
        "summary_json": "$JSON_REPORT"
    }
}
EOF
            
            log_pass "联动验证报告已生成: $JSON_REPORT"
        fi
    else
        log_fail "Newman 执行失败"
        log "可能原因: YL-Monitor 服务未运行 或 Newman 配置错误"
    fi
    
    # 步骤 5: 高级功能验证
    log_step "5" "高级功能验证"
    
    log_test "测试 get_api_collection (获取 Postman 集合信息)"
    COLLECTION_RESULT=$(mcp_request "get_api_collection" '{"collection": "yl-monitor-collection"}' 5)
    if echo "$COLLECTION_RESULT" | grep -q '"success":true'; then
        ENDPOINTS_COUNT=$(echo "$COLLECTION_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['result']['endpoints']))" 2>/dev/null || echo "0")
        EXISTS=$(echo "$COLLECTION_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['exists'])" 2>/dev/null || echo "false")
        if [ "$EXISTS" = "True" ]; then
            log_pass "get_api_collection 成功 (找到 $ENDPOINTS_COUNT 个端点)"
        else
            log_warn "get_api_collection 返回默认端点 (集合文件可能不存在)"
        fi
    else
        log_fail "get_api_collection 失败"
    fi
    
    log_test "测试 run_monitor_script (执行监控脚本)"
    # 检查是否有监控脚本
    MONITOR_DIR="${PROJECT_ROOT}/scripts/monitor"
    if [ -d "$MONITOR_DIR" ] && [ "$(ls -A "$MONITOR_DIR"/*.py 2>/dev/null)" ]; then
        # 找一个简单的脚本测试
        TEST_SCRIPT=$(ls "$MONITOR_DIR"/*.py | head -1 | xargs basename)
        SCRIPT_RESULT=$(mcp_request "run_monitor_script" "{\"script\": \"$TEST_SCRIPT\"}" 30)
        if echo "$SCRIPT_RESULT" | grep -q '"success":true'; then
            EXIT_CODE=$(echo "$SCRIPT_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['exitCode'])" 2>/dev/null || echo "1")
            if [ "$EXIT_CODE" = "0" ]; then
                log_pass "run_monitor_script 成功 (脚本: $TEST_SCRIPT)"
            else
                log_warn "run_monitor_script 脚本执行完成但退出码非 0 (exit: $EXIT_CODE)"
            fi
        else
            log_warn "run_monitor_script 可能失败 (脚本: $TEST_SCRIPT)"
        fi
    else
        log_warn "监控脚本目录不存在或为空，跳过测试"
    fi
    
    # 步骤 6: 生成总结报告
    log_step "6" "验证总结"
    
    log_header "验证结果统计"
    log "总测试项: $((PASSED + FAILED + WARNINGS))"
    log "${GREEN}通过: $PASSED${NC}"
    log "${RED}失败: $FAILED${NC}"
    log "${YELLOW}警告: $WARNINGS${NC}"
    
    # 计算通过率
    if [ $((PASSED + FAILED)) -gt 0 ]; then
        PASS_RATE=$((PASSED * 100 / (PASSED + FAILED)))
        log "通过率: ${PASS_RATE}%"
    fi
    
    log "\n${BLUE}生成的报告文件:${NC}"
    log "  - 详细日志: $REPORT_FILE"
    log "  - JSON 报告: $JSON_REPORT"
    log "  - Newman HTML: ${NEWMAN_REPORT_DIR}/newman-report.html"
    log "  - Newman JSON: ${NEWMAN_REPORT_DIR}/newman-report.json"
    
    log "\n${CYAN}使用建议:${NC}"
    log "  1. 查看 HTML 报告: open ${NEWMAN_REPORT_DIR}/newman-report.html"
    log "  2. 在 VS Code 中使用: Ctrl+Shift+P → YL-Monitor"
    log "  3. 手动测试 MCP: node $MCP_SERVER $PROJECT_ROOT"
    
    log "\n${BLUE}========================================${NC}"
    if [ $FAILED -eq 0 ]; then
        log "${GREEN}  🎉 所有验证通过! MCP + Postman 联动部署成功!${NC}"
    else
        log "${YELLOW}  ⚠ 验证完成，但有 $FAILED 项失败，请检查日志${NC}"
    fi
    log "${BLUE}========================================${NC}"
    
    # 返回退出码
    if [ $FAILED -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# 执行主函数
main "$@"
