#!/bin/bash

# YL-Monitor 应用启动脚本
# 用途：快速启动 YL-Monitor 应用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数定义
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅  $1${NC}"
}

print_error() {
    echo -e "${RED}❌  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️   $1${NC}"
}

# 获取项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# 外部虚拟环境路径
VENV_PATH="/home/vboxuser/桌面/环境目录/浏览器页面环境/venv"

print_header "YL-Monitor 应用启动向导"

# 加载环境变量（若存在）
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

is_port_in_use() {
    local port="$1"
    python3 - <<PY 2>/dev/null
import socket, sys
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", port))
except OSError:
    sys.exit(0)  # in use
else:
    sys.exit(1)  # free
finally:
    s.close()
PY
    return $?
}

resolve_port() {
    local base_port="${YL_MONITOR_PORT:-5500}"
    local port="$base_port"

    if is_port_in_use "$port"; then
        print_info "端口 ${port} 已被占用，尝试自动选择可用端口..."
        for p in $(seq "$base_port" 5599); do
            if ! is_port_in_use "$p"; then
                port="$p"
                break
            fi
        done
    fi

    export YL_MONITOR_HOST="${YL_MONITOR_HOST:-0.0.0.0}"
    export YL_MONITOR_PORT="$port"

    if [ "$port" != "$base_port" ] && [ -f ".env" ]; then
        print_info "已选择可用端口 ${port}，同步更新 .env 保证端口一致..."
        python3 - "$port" <<'PY' 2>/dev/null || true
from pathlib import Path
import sys

port = int(sys.argv[1])
env_path = Path(".env")
lines = env_path.read_text(encoding="utf-8").splitlines(True)
out = []
updated = False
for line in lines:
    if line.startswith("YL_MONITOR_PORT="):
        out.append(f"YL_MONITOR_PORT={port}\n")
        updated = True
    else:
        out.append(line)
if not updated:
    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    out.append(f"YL_MONITOR_PORT={port}\n")
env_path.write_text("".join(out), encoding="utf-8")
PY
    fi
}

resolve_port

# 检查 Python
print_info "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python 版本: $PYTHON_VERSION"

# 检查外部虚拟环境
if [ ! -d "$VENV_PATH" ]; then
    print_error "外部虚拟环境不存在: $VENV_PATH"
    print_info "请确认外部虚拟环境路径正确，或创建虚拟环境:"
    print_info "  python3 -m venv \"$VENV_PATH\""
    exit 1
else
    print_success "外部虚拟环境已存在: $VENV_PATH"
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source "$VENV_PATH/bin/activate"
print_success "虚拟环境已激活"

# 安装依赖
print_info "检查和安装依赖..."
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
    print_success "依赖安装完成"
else
    print_error "requirements.txt 未找到"
    exit 1
fi

# 检查必要的目录
print_info "检查目录结构..."
for dir in app scripts dags templates logs; do
    if [ -d "$dir" ]; then
        print_success "目录存在: $dir/"
    else
        print_error "目录缺失: $dir/"
        exit 1
    fi
done

# 创建 static 目录（如果不存在）
if [ ! -d "static" ]; then
    mkdir -p static/{css,js,images}
    print_success "创建静态资源目录: static/"
fi

# 选择运行模式
print_header "选择运行模式"

echo -e "请选择运行模式:"
echo -e "  ${GREEN}1${NC}) 开发模式 (带自动重载) - 推荐用于开发"
echo -e "  ${GREEN}2${NC}) 生产模式 (前台运行) - 推荐用于测试"
echo -e "  ${GREEN}3${NC}) 后台运行 (nohup) - 推荐用于生产"
echo -e "  ${GREEN}4${NC}) Docker 容器模式 - 推荐用于容器化部署"
echo -e "  ${GREEN}5${NC}) 仅验证 (不启动) - 运行验证脚本"

read -p "请输入选项 [1-5]: " choice

case $choice in
    1)
        print_header "启动开发模式"
        print_info "应用将在 http://0.0.0.0:${YL_MONITOR_PORT} 运行"
        print_info "按 Ctrl+C 停止应用"
        sleep 2
        uvicorn app.main:app --reload --host "${YL_MONITOR_HOST}" --port "${YL_MONITOR_PORT}"
        ;;
    2)
        print_header "启动生产模式"
        print_info "应用将在 http://0.0.0.0:${YL_MONITOR_PORT} 运行"
        print_info "按 Ctrl+C 停止应用"
        sleep 2
        uvicorn app.main:app --host "${YL_MONITOR_HOST}" --port "${YL_MONITOR_PORT}" --workers 4
        ;;
    3)
        print_header "启动后台运行"
        print_info "应用将在后台运行..."
        resolve_port
        
        # 启动应用
        nohup uvicorn app.main:app --host "${YL_MONITOR_HOST}" --port "${YL_MONITOR_PORT}" > yl-monitor.log 2>&1 &
        APP_PID=$!
        
        # 等待应用启动
        sleep 2
        
        # 检查应用是否成功启动
        if kill -0 $APP_PID 2>/dev/null; then
            print_success "应用已启动，PID: $APP_PID"
            print_info "日志文件: yl-monitor.log"
            print_info "访问地址: http://0.0.0.0:${YL_MONITOR_PORT}"
            print_info "停止应用: kill $APP_PID"
        else
            print_error "应用启动失败，请查看日志"
            cat yl-monitor.log
            exit 1
        fi
        ;;
    4)
        print_header "Docker 容器模式"
        
        if ! command -v docker &> /dev/null; then
            print_error "Docker 未安装"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            print_error "Docker Compose 未安装"
            exit 1
        fi
        
        print_info "使用 docker-compose 启动..."
        
        if [ ! -f "docker-compose.yml" ]; then
            print_error "docker-compose.yml 未找到"
            exit 1
        fi
        
        docker-compose build
        docker-compose up -d
        
        print_success "Docker 容器已启动"
        print_info "查看日志: docker-compose logs -f"
        print_info "停止容器: docker-compose down"
        print_info "访问地址: http://0.0.0.0:${YL_MONITOR_PORT}"
        ;;
    5)
        print_header "运行验证脚本"
        
        if [ -f "verify_deployment.py" ]; then
            python3 verify_deployment.py
        else
            print_error "验证脚本不存在: verify_deployment.py"
            exit 1
        fi
        
        print_info "验证完成，按任意键查看 API 功能测试..."
        read
        
        if [ -f "test_api_functionality.py" ]; then
            python3 test_api_functionality.py
        else
            print_error "API 测试脚本不存在: test_api_functionality.py"
        fi
        ;;
    *)
        print_error "无效的选项"
        exit 1
        ;;
esac

print_success "启动完成！"
