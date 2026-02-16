#!/bin/bash
# API 测试工作流脚本
# 支持 REST Client 和 Postman 两种模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BASE_URL="http://0.0.0.0:5500"
POSTMAN_COLLECTION="tests/postman/yl-monitor-collection.json"
POSTMAN_ENV="tests/postman/environments/local.json"
REST_CLIENT_FILE=".vscode/rest-client.http"

# 函数：打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo ""
    echo "========================================"
    echo "  $1"
    echo "========================================"
    echo ""
}

# 函数：检查服务状态
check_service() {
    print_info "检查 YL-Monitor 服务状态..."
    
    if curl -s --max-time 5 "${BASE_URL}/api/v1/dashboard/health" > /dev/null 2>&1; then
        print_success "服务运行正常"
        return 0
    else
        print_error "服务未启动或无法访问"
        return 1
    fi
}

# 函数：启动服务
start_service() {
    print_info "启动 YL-Monitor 服务..."
    
    # 检查是否已经在运行
    if pgrep -f "python.*main.py" > /dev/null; then
        print_warning "服务似乎已经在运行"
        if check_service; then
            return 0
        fi
    fi
    
    # 启动服务
    bash scripts/start_app_simple.sh > /tmp/yl-monitor-start.log 2>&1 &
    local pid=$!
    
    print_info "等待服务启动 (PID: $pid)..."
    
    # 等待服务就绪
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if check_service > /dev/null 2>&1; then
            print_success "服务启动成功"
            return 0
        fi
        
        if ! ps -p $pid > /dev/null 2>&1; then
            print_error "服务进程已退出"
            if [ -f /tmp/yl-monitor-start.log ]; then
                print_error "启动日志:"
                cat /tmp/yl-monitor-start.log
            fi
            return 1
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "服务启动超时"
    return 1
}

# 函数：运行 REST Client 测试
run_rest_client_tests() {
    print_header "REST Client 测试"
    
    if [ ! -f "$REST_CLIENT_FILE" ]; then
        print_warning "REST Client 配置文件不存在，正在生成..."
        python3 scripts/tools/sync_postman_to_rest_client.py
    fi
    
    print_info "REST Client 配置文件: $REST_CLIENT_FILE"
    print_info "请在 VS Code 中打开该文件，点击请求上方的 'Send Request' 链接进行测试"
    print_info ""
    print_info "使用 curl 执行自动化测试..."
    
    local tests_passed=0
    local tests_failed=0
    
    # 测试 1: 健康检查
    print_info "测试 1: 健康检查..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/dashboard/health" 2>/dev/null || echo '{"status": "error"}')
    if echo "$response" | grep -q '"status"'; then
        print_success "✓ 健康检查通过"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ 健康检查失败"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 2: 系统摘要
    print_info "测试 2: 系统摘要..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/dashboard/summary" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"cpu_usage"'; then
        print_success "✓ 系统摘要 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ 系统摘要 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 3: AR 节点
    print_info "测试 3: AR 节点列表..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/ar/nodes" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"nodes"\|"data"'; then
        print_success "✓ AR 节点 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ AR 节点 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 4: DAG 列表
    print_info "测试 4: DAG 列表..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/dag/list" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"dags"\|"data"'; then
        print_success "✓ DAG 列表 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ DAG 列表 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 5: 脚本列表
    print_info "测试 5: 脚本列表..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/scripts/list" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"scripts"\|"data"'; then
        print_success "✓ 脚本列表 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ 脚本列表 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 6: 告警规则
    print_info "测试 6: 告警规则..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/alerts/rules" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"rules"\|"data"'; then
        print_success "✓ 告警规则 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ 告警规则 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 7: 实时指标
    print_info "测试 7: 实时指标..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/v1/metrics/realtime" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"metrics"\|"data"'; then
        print_success "✓ 实时指标 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ 实时指标 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    # 测试 8: 任务队列统计
    print_info "测试 8: 任务队列统计..."
    response=$(curl -s --max-time 10 "${BASE_URL}/api/tasks/stats" 2>/dev/null || echo '{"error": "timeout"}')
    if echo "$response" | grep -q '"queue"\|"stats"'; then
        print_success "✓ 任务队列 API 正常"
        tests_passed=$((tests_passed + 1))
    else
        print_error "✗ 任务队列 API 异常"
        tests_failed=$((tests_failed + 1))
    fi
    
    echo ""
    print_header "REST Client 测试结果"
    print_success "通过: $tests_passed"
    if [ $tests_failed -gt 0 ]; then
        print_error "失败: $tests_failed"
    fi
    
    if [ $tests_passed -eq 8 ]; then
        print_success "所有测试通过！"
        return 0
    else
        print_warning "部分测试未通过，请检查服务状态"
        return 1
    fi
}

# 函数：运行 Postman 测试
run_postman_tests() {
    print_header "Postman 测试"
    
    # 检查 newman 是否安装
    if ! command -v newman &> /dev/null; then
        print_warning "Newman 未安装，正在安装..."
        if ! npm install -g newman newman-reporter-html 2>/dev/null; then
            print_error "Newman 安装失败，请手动安装: npm install -g newman"
            return 1
        fi
    fi
    
    # 检查集合文件
    if [ ! -f "$POSTMAN_COLLECTION" ]; then
        print_error "Postman 集合文件不存在: $POSTMAN_COLLECTION"
        return 1
    fi
    
    # 创建报告目录
    mkdir -p tests/postman/reports
    
    print_info "运行 Postman 集合测试..."
    print_info "集合: $POSTMAN_COLLECTION"
    print_info "环境: $POSTMAN_ENV"
    
    # 运行测试
    if newman run "$POSTMAN_COLLECTION" \
        -e "$POSTMAN_ENV" \
        --reporters cli,html \
        --reporter-html-export tests/postman/reports/report.html \
        --timeout-request 30000; then
        
        print_success "Postman 测试通过"
        print_info "测试报告: tests/postman/reports/report.html"
        return 0
    else
        print_error "Postman 测试失败"
        return 1
    fi
}

# 函数：同步配置
sync_config() {
    print_header "同步配置"
    print_info "同步 Postman 到 REST Client..."
    
    if python3 scripts/tools/sync_postman_to_rest_client.py; then
        print_success "同步完成"
        return 0
    else
        print_error "同步失败"
        return 1
    fi
}

# 函数：显示帮助
show_help() {
    cat << EOF
YL-Monitor API 测试工作流

用法: $0 [选项]

选项:
    rest        运行 REST Client 测试 (curl)
    postman     运行 Postman 测试 (需要 newman)
    sync        同步 Postman 集合到 REST Client
    check       检查服务状态
    start       启动服务
    stop        停止服务
    all         运行完整测试流程 (默认)
    help        显示帮助信息

示例:
    $0 rest     # 仅运行 REST Client 测试
    $0 postman  # 仅运行 Postman 测试
    $0 sync     # 同步配置
    $0 all      # 运行完整测试流程

环境变量:
    BASE_URL    服务基础 URL (默认: http://0.0.0.0:5500)
EOF
}

# 函数：停止服务
stop_service() {
    print_info "停止 YL-Monitor 服务..."
    
    local pids=$(pgrep -f "python.*main.py" || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # 强制终止
        pids=$(pgrep -f "python.*main.py" || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        print_success "服务已停止"
    else
        print_warning "没有找到运行中的服务"
    fi
}

# 函数：运行完整测试
run_all_tests() {
    print_header "YL-Monitor 完整 API 测试"
    
    # 检查或启动服务
    if ! check_service; then
        start_service || {
            print_error "无法启动服务，测试中止"
            exit 1
        }
    fi
    
    # 同步配置
    sync_config
    
    # 运行 REST Client 测试
    run_rest_client_tests || true
    
    echo ""
    
    # 运行 Postman 测试
    run_postman_tests || true
    
    print_header "测试完成"
    print_info "查看测试报告:"
    print_info "  - REST Client: 打开 .vscode/rest-client.http 手动测试"
    print_info "  - Postman: 查看 tests/postman/reports/report.html"
}

# 主函数
main() {
    case "${1:-all}" in
        rest)
            check_service || exit 1
            run_rest_client_tests
            ;;
        postman)
            check_service || exit 1
            run_postman_tests
            ;;
        sync)
            sync_config
            ;;
        check)
            check_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        all)
            run_all_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
