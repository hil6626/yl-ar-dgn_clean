#!/bin/bash
# AR-backend 监控服务启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}[*] AR-backend 监控服务启动脚本${NC}"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] 错误: 未找到 python3${NC}"
    exit 1
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${GREEN}[*] 激活虚拟环境...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}[!] 警告: 未找到虚拟环境，使用系统Python${NC}"
fi

# 检查依赖
echo -e "${GREEN}[*] 检查依赖...${NC}"
pip list | grep -i flask > /dev/null || {
    echo -e "${YELLOW}[!] 安装 Flask...${NC}"
    pip install flask flask-cors pyyaml psutil
}

# 创建日志目录
mkdir -p logs

# 检查端口占用
PORT=5501
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}[!] 警告: 端口 $PORT 已被占用${NC}"
    echo -e "${YELLOW}[!] 尝试查找占用进程...${NC}"
    lsof -Pi :$PORT -sTCP:LISTEN
    read -p "是否终止占用进程并继续? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}[*] 终止占用进程...${NC}"
        lsof -Pi :$PORT -sTCP:LISTEN -t | xargs kill -9
        sleep 2
    else
        echo -e "${RED}[!] 退出${NC}"
        exit 1
    fi
fi

# 启动服务
echo -e "${GREEN}[*] 启动监控服务...${NC}"
echo -e "${GREEN}[*] 访问地址: http://localhost:$PORT${NC}"
echo -e "${GREEN}[*] 健康检查: http://localhost:$PORT/health${NC}"
echo -e "${GREEN}[*] 按 Ctrl+C 停止服务${NC}"
echo ""

# 使用nohup后台运行（可选）
if [ "$1" == "--daemon" ]; then
    nohup python3 monitor_server.py > logs/monitor_server.log 2>&1 &
    echo $! > monitor_server.pid
    echo -e "${GREEN}[*] 服务已在后台启动，PID: $(cat monitor_server.pid)${NC}"
else
    python3 monitor_server.py
fi
