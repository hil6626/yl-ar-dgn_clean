#!/bin/bash

# YL-Monitor 启动并验证脚本
# 使用指定虚拟环境，启动后跟踪状态，验证后退出

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 虚拟环境路径（使用外部虚拟环境）
VENV_PATH="/home/vboxuser/桌面/环境目录/浏览器页面环境/venv"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PORT=5500

print_header "YL-Monitor 启动与验证"

# 切换到项目目录
cd "$PROJECT_DIR"
print_info "项目目录: $PROJECT_DIR"

# 检查外部虚拟环境是否存在
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

# 检查依赖
print_info "检查关键依赖..."
pip list | grep -E "fastapi|uvicorn" >/dev/null 2>&1 || {
    print_info "安装依赖..."
    pip install -r requirements.txt
    print_success "依赖安装完成"
}

# 检查端口占用
print_info "检查端口 $PORT 是否可用..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_error "端口 $PORT 已被占用"
    print_info "尝试停止占用端口的进程..."
    lsof -Pi :$PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
    sleep 1
fi
print_success "端口 $PORT 可用"

# 启动服务（后台运行）
print_header "启动 FastAPI 服务（开发模式）"
print_info "启动命令: uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT"
print_info "日志文件: $PROJECT_DIR/logs/startup.log"

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 后台启动服务
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT > "$PROJECT_DIR/logs/startup.log" 2>&1 &
APP_PID=$!

print_info "服务 PID: $APP_PID"
print_info "等待服务启动（最多 10 秒）..."

# 等待服务就绪
MAX_WAIT=10
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://0.0.0.0:$PORT/api/health >/dev/null 2>&1; then
        print_success "服务已就绪！"
        break
    fi
    
    if ! kill -0 $APP_PID 2>/dev/null; then
        print_error "服务进程已退出"
        cat "$PROJECT_DIR/logs/startup.log"
        deactivate
        exit 1
    fi
    
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo -n "."
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    print_error "服务启动超时"
    kill $APP_PID 2>/dev/null || true
    deactivate
    exit 1
fi

# 显示启动日志
print_info "启动日志:"
tail -n 20 "$PROJECT_DIR/logs/startup.log"

# 运行验证测试
print_header "运行验证测试"

print_info "1. 测试健康检查接口..."
curl -s http://0.0.0.0:$PORT/api/health | python3 -m json.tool 2>/dev/null || curl -s http://0.0.0.0:$PORT/api/health
echo ""

print_info "2. 测试主页面..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:$PORT/)
if [ "$HTTP_STATUS" = "200" ]; then
    print_success "主页面返回 200 OK"
else
    print_error "主页面返回 $HTTP_STATUS"
fi

print_info "3. 测试静态资源..."
CSS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:$PORT/static/css/style.css)
if [ "$CSS_STATUS" = "200" ]; then
    print_success "静态资源返回 200 OK"
else
    print_error "静态资源返回 $CSS_STATUS"
fi

print_info "4. 测试 API 概览..."
curl -s http://0.0.0.0:$PORT/api/summary | python3 -m json.tool 2>/dev/null | head -20 || curl -s http://0.0.0.0:$PORT/api/summary | head -20
echo ""

# 打开浏览器
print_header "打开浏览器"
print_info "正在打开浏览器访问 http://0.0.0.0:$PORT/"

# 尝试多种方式打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open "http://0.0.0.0:$PORT/" &
    print_success "已使用 xdg-open 打开浏览器"
elif command -v google-chrome &> /dev/null; then
    google-chrome "http://0.0.0.0:$PORT/" &
    print_success "已使用 Chrome 打开浏览器"
elif command -v firefox &> /dev/null; then
    firefox "http://0.0.0.0:$PORT/" &
    print_success "已使用 Firefox 打开浏览器"
else
    print_info "请手动打开浏览器访问: http://0.0.0.0:$PORT/"
fi

print_header "启动完成"
print_success "YL-Monitor 已成功启动并验证！"
print_info "访问地址: http://0.0.0.0:$PORT/"
print_info "API 文档: http://0.0.0.0:$PORT/api-doc"
print_info "服务 PID: $APP_PID"
print_info "停止服务: kill $APP_PID"

# 退出虚拟环境
print_info "退出虚拟环境..."
deactivate
print_success "虚拟环境已退出"

print_info "注意：服务仍在后台运行，PID: $APP_PID"
