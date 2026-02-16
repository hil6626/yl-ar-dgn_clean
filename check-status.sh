#!/bin/bash
# YL-AR-DGN 项目状态检查脚本
# 检查所有服务运行状态

echo "🔍 检查 YL-AR-DGN 项目状态..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查端口
check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 检查HTTP端点
check_http() {
    local url=$1
    local timeout=${2:-5}
    curl -s -o /dev/null --max-time ${timeout} "${url}" 2>/dev/null
    return $?
}

# 服务配置
declare -A services
services[5500]="YL-monitor:/api/health"
services[5501]="AR-backend:/health"
services[5502]="User-GUI:/status"

echo "╔════════════════════════════════════════════════════════╗"
echo "║           YL-AR-DGN 服务状态检查                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

printf "%-15s %-8s %-12s %-10s %s\n" "服务" "端口" "进程状态" "PID" "健康检查"
echo "─────────────────────────────────────────────────────────"

for port in 5500 5501 5502; do
    IFS=':' read -r name endpoint <<< "${services[$port]}"
    
    if check_port ${port}; then
        pid=$(lsof -Pi :${port} -sTCP:LISTEN -t 2>/dev/null)
        proc_status="${GREEN}运行中${NC}"
        
        # 检查HTTP健康
        if check_http "http://0.0.0.0:${port}${endpoint}"; then
            health="${GREEN}✅ 健康${NC}"
        else
            health="${YELLOW}⚠️  异常${NC}"
        fi
        
        printf "%-15s %-8s %-20s %-10s %s\n" \
            "${name}" "${port}" "${proc_status}" "${pid}" "${health}"
    else
        proc_status="${RED}停止${NC}"
        printf "%-15s %-8s %-20s %-10s %s\n" \
            "${name}" "${port}" "${proc_status}" "-" "${RED}❌ 不可访问${NC}"
    fi
done

echo ""

# 检查五层监控端点
echo "🔍 五层监控端点检查"
echo "─────────────────────────────────────────────────────────"

monitor_endpoints=(
    "基础设施监控:/api/v1/monitor/infrastructure"
    "系统资源监控:/api/v1/monitor/system-resources"
    "应用服务监控:/api/v1/monitor/application"
    "业务功能监控:/api/v1/monitor/business"
    "用户体验监控:/api/v1/monitor/user-experience"
)

for item in "${monitor_endpoints[@]}"; do
    IFS=':' read -r name endpoint <<< "$item"
    
    if check_http "http://0.0.0.0:5500${endpoint}"; then
        echo -e "  ${GREEN}✅${NC} ${name}: 可访问"
    else
        echo -e "  ${RED}❌${NC} ${name}: 不可访问"
    fi
done

echo ""
echo "📊 监控概览"
echo "─────────────────────────────────────────────────────────"
overview=$(curl -s --max-time 5 "http://0.0.0.0:5500/api/v1/monitor/overview" 2>/dev/null)
if [ -n "$overview" ]; then
    echo "$overview" | python3 -m json.tool 2>/dev/null || echo "$overview"
else
    echo -e "${YELLOW}⚠️  无法获取监控概览${NC}"
fi

echo ""
echo "💡 操作提示"
echo "─────────────────────────────────────────────────────────"
echo "  启动服务: ./start-all.sh"
echo "  停止服务: ./stop-all.sh"
echo "  查看日志: tail -f logs/*.log"
echo ""
