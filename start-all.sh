#!/bin/bash
# YL-AR-DGN 项目快速启动脚本
# 一键启动所有服务

PROJECT_ROOT="/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

echo "🚀 启动 YL-AR-DGN 项目..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 启动服务
start_service() {
    local name=$1
    local port=$2
    local script=$3
    local workdir=$4
    
    echo -n "📡 启动 ${name} (端口: ${port})... "
    
    # 检查端口是否被占用
    if check_port ${port}; then
        pid=$(lsof -Pi :${port} -sTCP:LISTEN -t 2>/dev/null)
        echo -e "${YELLOW}已在运行 (PID: ${pid})${NC}"
        return 0
    fi
    
    # 启动服务
    cd "${PROJECT_ROOT}/${workdir}"
    nohup python3 "${script}" > "${LOG_DIR}/${name}.log" 2>&1 &
    local pid=$!
    
    # 等待服务启动
    local retries=0
    local max_retries=30
    
    while [ $retries -lt $max_retries ]; do
        if check_port ${port}; then
            echo -e "${GREEN}成功 (PID: ${pid})${NC}"
            return 0
        fi
        sleep 1
        ((retries++))
    done
    
    echo -e "${RED}失败${NC}"
    return 1
}

# 启动AR-backend
start_service "AR-backend" 5501 "monitor_server.py" "AR-backend"

# 启动User GUI
start_service "User-GUI" 5502 "main.py" "user"

# 启动YL-monitor
start_service "YL-monitor" 5500 "start_server.py" "YL-monitor"

echo ""
echo "✅ 启动完成"
echo ""
echo "服务访问地址:"
echo "  📊 YL-monitor: http://0.0.0.0:5500"
echo "  📡 AR-backend: http://0.0.0.0:5501/health"
echo "  🖥️  User GUI:  http://0.0.0.0:5502/status"
echo ""
echo "监控端点:"
echo "  🔍 五层监控概览: http://0.0.0.0:5500/api/v1/monitor/overview"
echo "  🔍 基础设施监控: http://0.0.0.0:5500/api/v1/monitor/infrastructure"
echo "  🔍 系统资源监控: http://0.0.0.0:5500/api/v1/monitor/system-resources"
echo "  🔍 应用服务监控: http://0.0.0.0:5500/api/v1/monitor/application"
echo "  🔍 业务功能监控: http://0.0.0.0:5500/api/v1/monitor/business"
echo "  🔍 用户体验监控: http://0.0.0.0:5500/api/v1/monitor/user-experience"
echo ""
echo "查看日志: tail -f ${LOG_DIR}/*.log"
echo "停止服务: ./stop-all.sh"
echo "检查状态: ./check-status.sh"
