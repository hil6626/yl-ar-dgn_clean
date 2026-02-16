#!/bin/bash
# -*- coding: utf-8 -*-
# shellcheck disable=SC1090,SC1091

# YL-AR-DGN 项目统一入口脚本
# 提供部署、监控、验证、状态查询等统一管理功能
#
# 用法: ./yl-ar-dgn.sh <command> [options]
#
# 命令:
#   deploy     - 部署所有组件
#   start      - 启动所有服务
#   stop       - 停止所有服务
#   restart    - 重启所有服务
#   status     - 显示所有组件状态
#   monitor    - 启动监控面板
#   validate   - 验证项目完整性
#   logs       - 查看组件日志
#   cleanup    - 清理临时文件
#   backup     - 备份项目数据
#   docker-build - 构建Docker镜像
#   docker-start - 启动Docker容器
#   docker-stop  - 停止Docker容器
#   help       - 显示帮助信息

set -euo pipefail

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
YL-AR-DGN 项目管理脚本

用法: $0 <command> [options]

命令:
  deploy [component]     部署指定组件或所有组件
                         组件: yl-monitor, ar-backend, user-gui, all

  start [component]      启动指定服务或所有服务
                         组件: yl-monitor, ar-backend, user-gui, all

  stop [component]       停止指定服务或所有服务

  restart [component]    重启指定服务或所有服务

  status                 显示所有组件状态

  monitor                打开监控面板 (YL-monitor)

  validate               验证项目完整性和配置

  logs [component]       查看指定组件日志
                         组件: yl-monitor, ar-backend, user-gui

  cleanup                清理临时文件和缓存

  backup [name]          备份项目数据
                         名称: 可选，默认为当前日期

  docker-build           构建Docker镜像

  docker-start           启动Docker容器

  docker-stop            停止Docker容器

  health                 执行健康检查

  version                显示版本信息

  help                   显示此帮助信息

示例:
  $0 deploy all          # 部署所有组件
  $0 start yl-monitor    # 启动YL-monitor
  $0 status              # 查看所有组件状态
  $0 logs ar-backend     # 查看AR-backend日志
  $0 backup 20240216     # 备份项目数据
  $0 docker-build        # 构建Docker镜像

EOF
}

# 检查依赖
check_dependencies() {
    local deps=("curl" "python3" "ps")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "缺少依赖: ${missing[*]}"
        log_info "请安装缺少的依赖后重试"
        exit 1
    fi
}

# 获取组件状态
get_component_status() {
    local component=$1
    local url=""
    local port=""

    case $component in
        "yl-monitor")
            port=5500
            url="http://0.0.0.0:${port}/api/health"
            ;;
        "ar-backend")
            port=5501
            url="http://0.0.0.0:${port}/health"
            ;;
        "user-gui")
            port=5502
            url="http://0.0.0.0:${port}/health"
            ;;
        *)
            echo "unknown"
            return
            ;;
    esac

    # 检查端口是否被占用
    if ! lsof -i ":$port" &> /dev/null; then
        echo "stopped"
        return
    fi

    # 尝试健康检查
    if curl -sf "$url" &> /dev/null; then
        echo "running"
    else
        echo "error"
    fi
}

# 显示状态
show_status() {
    log_info "YL-AR-DGN 项目组件状态"
    echo "========================================"

    local components=("yl-monitor" "ar-backend" "user-gui")
    local names=("YL-Monitor" "AR-Backend" "User GUI")
    local ports=(5500 5501 5502)

    for i in "${!components[@]}"; do
        local component=${components[$i]}
        local name=${names[$i]}
        local port=${ports[$i]}
        local status=$(get_component_status "$component")

        case $status in
            "running")
                echo -e "✓ ${name} (端口: $port): ${GREEN}运行中${NC}"
                ;;
            "stopped")
                echo -e "✗ ${name} (端口: $port): ${RED}已停止${NC}"
                ;;
            "error")
                echo -e "⚠ ${name} (端口: $port): ${YELLOW}异常${NC}"
                ;;
            *)
                echo -e "? ${name} (端口: $port): ${YELLOW}未知${NC}"
                ;;
        esac
    done

    echo "========================================"
    log_info "使用 '$0 logs <component>' 查看详细日志"
}

# 部署组件
deploy_component() {
    local component=$1

    case $component in
        "yl-monitor")
            log_info "部署 YL-monitor..."
            cd "${PROJECT_ROOT}/YL-monitor"
            if [ -f "requirements.txt" ]; then
                pip3 install -q -r requirements.txt 2>/dev/null || log_warning "依赖安装可能失败"
            fi
            log_success "YL-monitor 部署完成"
            ;;
        "ar-backend")
            log_info "部署 AR-backend..."
            cd "${PROJECT_ROOT}/AR-backend"
            if [ -f "requirements.txt" ]; then
                pip3 install -q -r requirements.txt 2>/dev/null || log_warning "依赖安装可能失败"
            fi
            log_success "AR-backend 部署完成"
            ;;
        "user-gui")
            log_info "部署 User GUI..."
            cd "${PROJECT_ROOT}/user"
            # 检查PyQt5
            if ! python3 -c "import PyQt5" 2>/dev/null; then
                log_warning "PyQt5 未安装，请手动安装: pip3 install PyQt5"
            fi
            log_success "User GUI 部署完成"
            ;;
        "all")
            deploy_component "yl-monitor"
            deploy_component "ar-backend"
            deploy_component "user-gui"
            log_success "所有组件部署完成"
            ;;
        *)
            log_error "未知组件: $component"
            log_info "可用组件: yl-monitor, ar-backend, user-gui, all"
            exit 1
            ;;
    esac
}

# 启动组件
start_component() {
    local component=$1

    case $component in
        "yl-monitor")
            log_info "启动 YL-monitor..."
            cd "${PROJECT_ROOT}/YL-monitor"
            nohup python3 start_server.py > logs/start_server.log 2>&1 &
            sleep 2
            if [ "$(get_component_status yl-monitor)" == "running" ]; then
                log_success "YL-monitor 启动成功 (端口: 5500)"
            else
                log_error "YL-monitor 启动失败"
            fi
            ;;
        "ar-backend")
            log_info "启动 AR-backend 监控服务..."
            cd "${PROJECT_ROOT}/AR-backend"
            nohup python3 monitor_server.py > logs/monitor_server.log 2>&1 &
            sleep 2
            if [ "$(get_component_status ar-backend)" == "running" ]; then
                log_success "AR-backend 启动成功 (端口: 5501)"
            else
                log_error "AR-backend 启动失败"
            fi
            ;;
        "user-gui")
            log_info "启动 User GUI..."
            cd "${PROJECT_ROOT}/user"
            nohup python3 main.py > logs/gui.log 2>&1 &
            sleep 2
            if [ "$(get_component_status user-gui)" == "running" ]; then
                log_success "User GUI 启动成功 (端口: 5502)"
            else
                log_error "User GUI 启动失败"
            fi
            ;;
        "all")
            start_component "yl-monitor"
            start_component "ar-backend"
            start_component "user-gui"
            log_success "所有服务已启动"
            log_info "使用 '$0 status' 查看状态"
            ;;
        *)
            log_error "未知组件: $component"
            exit 1
            ;;
    esac
}

# 停止组件
stop_component() {
    local component=$1

    case $component in
        "yl-monitor")
            log_info "停止 YL-monitor..."
            pkill -f "YL-monitor/start_server.py" 2>/dev/null || true
            log_success "YL-monitor 已停止"
            ;;
        "ar-backend")
            log_info "停止 AR-backend..."
            pkill -f "AR-backend/monitor_server.py" 2>/dev/null || true
            log_success "AR-backend 已停止"
            ;;
        "user-gui")
            log_info "停止 User GUI..."
            pkill -f "user/main.py" 2>/dev/null || true
            log_success "User GUI 已停止"
            ;;
        "all")
            stop_component "yl-monitor"
            stop_component "ar-backend"
            stop_component "user-gui"
            log_success "所有服务已停止"
            ;;
        *)
            log_error "未知组件: $component"
            exit 1
            ;;
    esac
}

# 查看日志
show_logs() {
    local component=$1
    local log_file=""

    case $component in
        "yl-monitor")
            log_file="${PROJECT_ROOT}/YL-monitor/logs/start_server.log"
            ;;
        "ar-backend")
            log_file="${PROJECT_ROOT}/AR-backend/logs/monitor_server.log"
            ;;
        "user-gui")
            log_file="${PROJECT_ROOT}/user/logs/gui.log"
            ;;
        *)
            log_error "未知组件: $component"
            log_info "可用组件: yl-monitor, ar-backend, user-gui"
            exit 1
            ;;
    esac

    if [ -f "$log_file" ]; then
        log_info "显示 $component 日志 (最后50行):"
        echo "========================================"
        tail -n 50 "$log_file"
        echo "========================================"
        log_info "日志文件: $log_file"
    else
        log_warning "日志文件不存在: $log_file"
    fi
}

# 执行健康检查
health_check() {
    log_info "执行健康检查..."
    echo "========================================"

    local all_healthy=true

    # 检查YL-monitor
    if curl -sf http://0.0.0.0:5500/api/health &> /dev/null; then
        echo -e "✓ YL-monitor: ${GREEN}健康${NC}"
    else
        echo -e "✗ YL-monitor: ${RED}异常${NC}"
        all_healthy=false
    fi

    # 检查AR-backend
    if curl -sf http://0.0.0.0:5501/health &> /dev/null; then
        echo -e "✓ AR-backend: ${GREEN}健康${NC}"
    else
        echo -e "✗ AR-backend: ${RED}异常${NC}"
        all_healthy=false
    fi

    # 检查User GUI
    if curl -sf http://0.0.0.0:5502/health &> /dev/null; then
        echo -e "✓ User GUI: ${GREEN}健康${NC}"
    else
        echo -e "✗ User GUI: ${RED}异常${NC}"
        all_healthy=false
    fi

    echo "========================================"

    if $all_healthy; then
        log_success "所有组件健康"
        return 0
    else
        log_error "部分组件异常"
        return 1
    fi
}

# 验证项目
validate_project() {
    log_info "验证项目完整性..."
    echo "========================================"

    local errors=0

    # 检查目录结构
    for dir in "YL-monitor" "AR-backend" "user" "rules" "scripts"; do
        if [ -d "${PROJECT_ROOT}/${dir}" ]; then
            echo -e "✓ 目录存在: $dir"
        else
            echo -e "✗ 目录缺失: $dir"
            ((errors++))
        fi
    done

    echo "----------------------------------------"

    # 检查关键文件
    local files=(
        "YL-monitor/start_server.py"
        "AR-backend/monitor_server.py"
        "user/main.py"
        "rules/index.js"
        "scripts/yl-ar-dgn.sh"
    )

    for file in "${files[@]}"; do
        if [ -f "${PROJECT_ROOT}/${file}" ]; then
            echo -e "✓ 文件存在: $file"
        else
            echo -e "✗ 文件缺失: $file"
            ((errors++))
        fi
    done

    echo "========================================"

    if [ $errors -eq 0 ]; then
        log_success "项目验证通过"
        return 0
    else
        log_error "项目验证失败 ($errors 个错误)"
        return 1
    fi
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    
    # 清理Python缓存
    find "${PROJECT_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${PROJECT_ROOT}" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "${PROJECT_ROOT}" -type f -name "*.pyo" -delete 2>/dev/null || true
    
    # 清理临时文件
    find "${PROJECT_ROOT}" -type f -name "*.tmp" -delete 2>/dev/null || true
    find "${PROJECT_ROOT}" -type f -name "*.log.old" -delete 2>/dev/null || true
    
    log_success "清理完成"
}

# 备份项目数据
backup_project() {
    local backup_name="${1:-$(date +%Y%m%d_%H%M%S)}"
    local backup_dir="${PROJECT_ROOT}/backups/${backup_name}"
    
    log_info "备份项目数据到: $backup_dir"
    
    # 创建备份目录
    mkdir -p "$backup_dir"
    
    # 备份配置文件
    if [ -d "${PROJECT_ROOT}/config" ]; then
        cp -r "${PROJECT_ROOT}/config" "${backup_dir}/"
    fi
    
    # 备份规则文件
    if [ -d "${PROJECT_ROOT}/rules" ]; then
        cp -r "${PROJECT_ROOT}/rules" "${backup_dir}/"
    fi
    
    # 备份数据目录
    if [ -d "${PROJECT_ROOT}/data" ]; then
        cp -r "${PROJECT_ROOT}/data" "${backup_dir}/"
    fi
    
    # 创建备份信息文件
    cat > "${backup_dir}/backup_info.txt" << EOF
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份名称: $backup_name
项目版本: 2.3.0
EOF
    
    log_success "备份完成: $backup_dir"
}

# Docker构建
docker_build() {
    log_info "构建Docker镜像..."
    cd "${PROJECT_ROOT}"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose build
        log_success "Docker镜像构建完成"
    else
        log_error "docker-compose.yml 不存在"
        exit 1
    fi
}

# Docker启动
docker_start() {
    log_info "启动Docker容器..."
    cd "${PROJECT_ROOT}"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        log_success "Docker容器启动完成"
    else
        log_error "docker-compose.yml 不存在"
        exit 1
    fi
}

# Docker停止
docker_stop() {
    log_info "停止Docker容器..."
    cd "${PROJECT_ROOT}"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        log_success "Docker容器已停止"
    else
        log_error "docker-compose.yml 不存在"
        exit 1
    fi
}

# 打开监控面板
open_monitor() {
    log_info "打开监控面板..."
    local monitor_url="http://0.0.0.0:5500/monitor/monitor.html"
    
    # 检查YL-monitor是否运行
    if [ "$(get_component_status yl-monitor)" != "running" ]; then
        log_warning "YL-monitor 未运行，尝试启动..."
        start_component "yl-monitor"
        sleep 3
    fi
    
    # 尝试打开浏览器
    if command -v xdg-open &> /dev/null; then
        xdg-open "$monitor_url" &
    elif command -v open &> /dev/null; then
        open "$monitor_url" &
    else
        log_info "请手动打开: $monitor_url"
    fi
}

# 显示版本信息
show_version() {
    echo "YL-AR-DGN 项目管理脚本"
    echo "版本: 1.0.0"
    echo "项目路径: $PROJECT_ROOT"
    echo ""
    echo "组件版本:"
    echo "  - YL-monitor: 2.0.0"
    echo "  - AR-backend: 2.0.0"
    echo "  - User GUI: 2.0.0"
}

# 主函数
main() {
    # 检查依赖
    check_dependencies

    # 解析命令
    local command="${1:-help}"
    local option="${2:-all}"

    case $command in
        "help"|"-h"|"--help")
            show_help
            ;;
        "deploy")
            deploy_component "$option"
            ;;
        "start")
            start_component "$option"
            ;;
        "stop")
            stop_component "$option"
            ;;
        "restart")
            stop_component "$option"
            sleep 2
            start_component "$option"
            ;;
        "status")
            show_status
            ;;
        "monitor")
            open_monitor
            ;;
        "validate")
            validate_project
            ;;
        "logs")
            if [ "$option" == "all" ]; then
                log_error "请指定组件: yl-monitor, ar-backend, user-gui"
                exit 1
            fi
            show_logs "$option"
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            backup_project "$option"
            ;;
        "docker-build")
            docker_build
            ;;
        "docker-start")
            docker_start
            ;;
        "docker-stop")
            docker_stop
            ;;
        "health")
            health_check
            ;;
        "version"|"-v"|"--version")
            show_version
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
