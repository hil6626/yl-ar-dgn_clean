#!/bin/bash
# AR Backend 快速启动脚本
# 使用方法: ./start.sh [选项]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认配置
PROJECT_DIR="/workspaces/yl-ar-dgn/AR-backend"
VENV_DIR="$PROJECT_DIR/venv"
PORT=5000
LOG_LEVEL="INFO"

# 打印函数
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# 帮助信息
show_help() {
    echo "AR Backend 快速启动脚本"
    echo ""
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -p, --port PORT     设置端口 (默认: 5000)"
    echo "  -l, --level LEVEL   设置日志级别 (默认: INFO)"
    echo "  -v, --venv DIR      设置虚拟环境目录"
    echo "  -d, --daemon       后台运行模式"
    echo "  -c, --check        仅检查环境，不启动"
    echo "  -m, --monitor      仅启动监控服务"
    echo "  --no-gui           不启动GUI界面"
    echo "  --reset             重置并重新安装"
    echo ""
    echo "示例:"
    echo "  $0                  # 启动所有服务"
    echo "  $0 -c               # 仅检查环境"
    echo "  $0 -p 8080          # 使用端口8080"
    echo "  $0 -d               # 后台运行"
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -l|--level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            -v|--venv)
                VENV_DIR="$2"
                shift 2
                ;;
            -d|--daemon)
                DAEMON=true
                shift
                ;;
            -c|--check)
                CHECK_ONLY=true
                shift
                ;;
            -m|--monitor)
                MONITOR_ONLY=true
                shift
                ;;
            --no-gui)
                NO_GUI=true
                shift
                ;;
            --reset)
                RESET=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查环境
check_environment() {
    print_step "检查环境..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    print_success "Python3 已安装: $(python3 --version)"

    # 检查pip - 优先使用pip3，然后尝试python3 -m pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 已安装"
    elif python3 -m pip --version &> /dev/null; then
        print_success "python3 -m pip 可用"
    else
        print_warning "pip3 未安装，将尝试安装"
    fi

    # 检查项目目录
    if [[ ! -d "$PROJECT_DIR" ]]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    print_success "项目目录存在: $PROJECT_DIR"

    # 检查虚拟环境
    if [[ -d "$VENV_DIR" ]]; then
        print_success "虚拟环境已存在: $VENV_DIR"
    else
        print_warning "虚拟环境不存在，将自动创建"
    fi

    # 检查端口
    if command -v lsof &> /dev/null; then
        if lsof -i:$PORT &> /dev/null; then
            print_warning "端口 $PORT 已被占用"
        else
            print_success "端口 $PORT 可用"
        fi
    fi

    print_success "环境检查完成"
}

# 创建虚拟环境
create_venv() {
    print_step "创建虚拟环境..."

    if [[ -d "$VENV_DIR" ]]; then
        print_warning "虚拟环境已存在，跳过创建"
        return 0
    fi

    # 尝试创建虚拟环境
    python3 -m venv "$VENV_DIR"
    if [[ $? -eq 0 ]]; then
        print_success "虚拟环境创建成功"
    else
        print_warning "虚拟环境创建失败（ensurepip不可用）"
        print_info "将使用系统Python直接运行，无需虚拟环境"
        # 标记不需要虚拟环境
        SKIP_VENV=true
    fi
}

# 安装依赖
install_deps() {
    print_step "安装依赖..."

    # 如果跳过了虚拟环境创建，直接使用系统Python
    if [[ "$SKIP_VENV" == "true" ]]; then
        print_info "使用系统Python安装依赖..."

        # 升级pip
        if python3 -m pip --version &> /dev/null; then
            python3 -m pip install --upgrade pip
        fi

        # 安装requirements
        if [[ -f "$PROJECT_DIR/requirements/requirements.txt" ]]; then
            python3 -m pip install -r "$PROJECT_DIR/requirements/requirements.txt"
            if [[ $? -eq 0 ]]; then
                print_success "依赖安装成功"
            else
                print_error "依赖安装失败"
                exit 1
            fi
        else
            print_warning "requirements.txt 不存在，跳过"
        fi
        return 0
    fi

    source "$VENV_DIR/bin/activate" 2>/dev/null || {
        print_warning "无法激活虚拟环境，将使用系统Python"
        PYTHON_CMD="python3"
    }

    # 升级pip
    if command -v pip3 &> /dev/null; then
        pip3 install --upgrade pip
    elif command -v pip &> /dev/null; then
        pip install --upgrade pip
    elif command -v python3 &> /dev/null; then
        python3 -m pip install --upgrade pip
    fi

    # 安装requirements
    if [[ -f "$PROJECT_DIR/requirements/requirements.txt" ]]; then
        if command -v pip3 &> /dev/null; then
            pip3 install -r "$PROJECT_DIR/requirements/requirements.txt"
        elif command -v pip &> /dev/null; then
            pip install -r "$PROJECT_DIR/requirements/requirements.txt"
        elif command -v python3 &> /dev/null; then
            python3 -m pip install -r "$PROJECT_DIR/requirements/requirements.txt"
        fi
        if [[ $? -eq 0 ]]; then
            print_success "依赖安装成功"
        else
            print_error "依赖安装失败"
            exit 1
        fi
    else
        print_warning "requirements.txt 不存在，跳过"
    fi

    deactivate 2>/dev/null || true
}

# 配置环境变量
setup_env() {
    print_step "配置环境变量..."

    export AR_PROJECT_ROOT="$PROJECT_DIR"
    export AR_PROJECT_PATH="$PROJECT_DIR"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    export AR_LOG_LEVEL="$LOG_LEVEL"
    export AR_MONITOR_PORT="$PORT"

    print_success "环境变量已配置"
}

# 启动监控服务
start_monitor() {
    print_step "启动监控服务..."

    # 如果跳过了虚拟环境创建，使用系统Python
    if [[ "$SKIP_VENV" == "true" ]]; then
        print_info "使用系统Python启动监控服务..."
        PYTHON_CMD="python3"
    # 尝试激活虚拟环境，如果不存在则使用系统Python
    elif [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
        PYTHON_CMD="python"
    else
        print_warning "虚拟环境不存在，使用系统Python"
        PYTHON_CMD="python3"
    fi

    cd "$PROJECT_DIR"

    if [[ "$DAEMON" == true ]]; then
        # 后台运行
        $PYTHON_CMD monitor_server.py > logs/monitor_server.log 2>&1 &
        MONITOR_PID=$!
        print_success "监控服务已启动 (PID: $MONITOR_PID)"
        echo $MONITOR_PID > .monitor_pid
        print_success "监控地址: http://localhost:5501"
    else
        # 前台运行
        print_info "监控地址: http://localhost:5501"
        $PYTHON_CMD monitor_server.py
    fi
}

# 启动服务
start_services() {
    print_step "启动服务..."

    # 如果跳过了虚拟环境创建，使用系统Python
    if [[ "$SKIP_VENV" == "true" ]]; then
        print_info "使用系统Python启动服务..."
        PYTHON_CMD="python3"
    # 尝试激活虚拟环境，如果不存在则使用系统Python
    elif [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
        PYTHON_CMD="python"
    else
        print_warning "虚拟环境不存在，使用系统Python"
        PYTHON_CMD="python3"
    fi

    cd "$PROJECT_DIR"

    if [[ "$DAEMON" == true ]]; then
        # 后台运行
        $PYTHON_CMD app/launcher.py > logs/launcher.log 2>&1 &
        LAUNCHER_PID=$!
        print_success "启动器已启动 (PID: $LAUNCHER_PID)"
        echo $LAUNCHER_PID > .ar_launcher_pid
    else
        # 前台运行
        $PYTHON_CMD app/launcher.py
    fi
}

# 重置环境
reset_environment() {
    print_warning "重置环境..."

    # 停止运行的服务
    if [[ -f "$PROJECT_DIR/.ar_launcher_pid" ]]; then
        kill $(cat "$PROJECT_DIR/.ar_launcher_pid") 2>/dev/null || true
        rm "$PROJECT_DIR/.ar_launcher_pid"
    fi

    # 删除虚拟环境
    if [[ -d "$VENV_DIR" ]]; then
        print_step "删除虚拟环境..."
        rm -rf "$VENV_DIR"
    fi

    print_success "环境已重置"
}

# 主函数
main() {
    # 解析参数
    parse_args "$@"

    # 显示横幅
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           AR Backend 快速启动脚本 v1.0                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # 检查环境
    check_environment

    # 如果只是检查
    if [[ "$CHECK_ONLY" == true ]]; then
        exit 0
    fi

    # 如果需要重置
    if [[ "$RESET" == true ]]; then
        reset_environment
    fi

    # 创建虚拟环境
    create_venv

    # 安装依赖
    install_deps

    # 配置环境变量
    setup_env

    # 启动服务
    if [[ "$MONITOR_ONLY" == true ]]; then
        start_monitor
    else
        start_services
    fi

    echo ""
    print_success "启动完成！"
    if [[ "$MONITOR_ONLY" == true ]]; then
        print_success "监控服务: http://localhost:5501"
    else
        print_success "监控页面: http://localhost:$PORT"
    fi
}

# 运行主函数
main "$@"
