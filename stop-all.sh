#!/bin/bash
# YL-AR-DGN 项目停止脚本
# 一键停止所有服务

echo "🛑 停止 YL-AR-DGN 项目..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 停止服务
stop_service() {
    local name=$1
    local pattern=$2
    
    echo -n "🛑 停止 ${name}... "
    
    # 查找并停止进程
    local pids=$(pgrep -f "${pattern}" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -TERM 2>/dev/null
        sleep 2
        
        # 检查是否还在运行
        local remaining=$(pgrep -f "${pattern}" 2>/dev/null)
        if [ -n "$remaining" ]; then
            echo "$remaining" | xargs kill -KILL 2>/dev/null
        fi
        
        echo -e "${GREEN}已停止${NC}"
    else
        echo -e "${YELLOW}未运行${NC}"
    fi
}

# 停止各服务
stop_service "YL-monitor" "YL-monitor/start_server.py"
stop_service "AR-backend" "AR-backend/monitor_server.py"
stop_service "User-GUI" "user/main.py"

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
