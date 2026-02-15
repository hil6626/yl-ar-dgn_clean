#!/bin/bash
# ============================================================================
# YL-Monitor 前端修复验证脚本
# ============================================================================
# 功能：验证前端页面修复是否成功
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 检查文件是否存在
check_file() {
    if [ -f "$1" ]; then
        print_success "文件存在: $1"
        return 0
    else
        print_error "文件不存在: $1"
        return 1
    fi
}

# 检查文件内容
check_file_content() {
    local file=$1
    local pattern=$2
    local description=$3
    
    if grep -q "$pattern" "$file"; then
        print_success "$description"
        return 0
    else
        print_error "$description"
        return 1
    fi
}

# 主验证流程
main() {
    print_header "YL-Monitor 前端修复验证"
    
    local errors=0
    
    # 1. 检查关键文件是否存在
    print_header "1. 检查关键文件"
    
    check_file "static/js/config.js" || ((errors++))
    check_file "static/js/page-dashboard.js" || ((errors++))
    check_file "templates/base.html" || ((errors++))
    check_file "templates/dashboard.html" || ((errors++))
    
    # 2. 检查 config.js 修复
    print_header "2. 检查 config.js 命名空间"
    
    check_file_content "static/js/config.js" "window.YLMonitor.CONFIG = CONFIG" "CONFIG 常量命名正确" || ((errors++))
    
    # 3. 检查 page-dashboard.js 修复
    print_header "3. 检查 page-dashboard.js 修复"
    
    check_file_content "static/js/page-dashboard.js" "/api/v1/dashboard/summary" "API 路径正确" || ((errors++))
    check_file_content "static/js/page-dashboard.js" "updateMetricCard" "使用 updateMetricCard 方法" || ((errors++))
    check_file_content "static/js/page-dashboard.js" "window.YLMonitor.CONFIG" "引用 CONFIG 正确" || ((errors++))
    
    # 4. 检查模板缓存版本
    print_header "4. 检查模板缓存版本"
    
    check_file_content "templates/base.html" "?v=3" "base.html 缓存版本已更新" || ((errors++))
    check_file_content "templates/dashboard.html" "?v=3" "dashboard.html 缓存版本已更新" || ((errors++))
    check_file_content "templates/scripts.html" "?v=3" "scripts.html 缓存版本已更新" || ((errors++))
    check_file_content "templates/dag.html" "?v=3" "dag.html 缓存版本已更新" || ((errors++))
    check_file_content "templates/ar.html" "?v=3" "ar.html 缓存版本已更新" || ((errors++))
    check_file_content "templates/api_doc.html" "?v=3" "api_doc.html 缓存版本已更新" || ((errors++))
    
    # 5. 检查 dashboard.html 结构
    print_header "5. 检查 dashboard.html 结构"
    
    check_file_content "templates/dashboard.html" "cpu-progress" "CPU 进度条容器存在" || ((errors++))
    check_file_content "templates/dashboard.html" "memory-progress" "内存进度条容器存在" || ((errors++))
    check_file_content "templates/dashboard.html" "setTimeout" "使用 setTimeout 延迟加载" || ((errors++))
    
    # 6. 检查页面初始化逻辑
    print_header "6. 检查页面初始化逻辑"
    
    check_file_content "templates/dashboard.html" "window.Dashboard && Dashboard.loadData" "Dashboard 初始化正确" || ((errors++))
    check_file_content "templates/scripts.html" "window.Scripts && Scripts.loadData" "Scripts 初始化正确" || ((errors++))
    check_file_content "templates/dag.html" "window.DAG && DAG.loadData" "DAG 初始化正确" || ((errors++))
    check_file_content "templates/ar.html" "window.AR && AR.loadData" "AR 初始化正确" || ((errors++))
    check_file_content "templates/api_doc.html" "window.APIDoc && APIDoc.loadData" "APIDoc 初始化正确" || ((errors++))
    
    # 7. 检查 CSS 文件
    print_header "7. 检查 CSS 文件"
    
    check_file "static/css/style.css" || ((errors++))
    check_file "static/css/dashboard.css" || ((errors++))
    
    # 8. 检查 api-utils.js
    print_header "8. 检查 api-utils.js"
    
    check_file_content "static/js/api-utils.js" "window.YLMonitor.Config.API_BASE_URL" "API 基础 URL 配置正确" || ((errors++))
    
    # 总结
    print_header "验证结果"
    
    if [ $errors -eq 0 ]; then
        print_success "所有检查通过！前端修复验证成功。"
        print_info "建议操作："
        print_info "1. 清除浏览器缓存 (Ctrl+Shift+R 或 Cmd+Shift+R)"
        print_info "2. 重新启动后端服务"
        print_info "3. 访问 http://localhost:8000/dashboard 测试"
        exit 0
    else
        print_error "发现 $errors 个问题，请检查上述错误项"
        exit 1
    fi
}

# 执行主函数
main "$@"
