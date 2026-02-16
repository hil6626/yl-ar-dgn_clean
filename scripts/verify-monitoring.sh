#!/bin/bash
# YL-AR-DGN 监控验证工具
# 验证五层监控架构可用性

YL_MONITOR="http://0.0.0.0:5500"
AR_BACKEND="http://0.0.0.0:5501"
USER_GUI="http://0.0.0.0:5502"

echo "🔍 YL-AR-DGN 监控系统验证"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 计数器
passed=0
failed=0

check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "  检查 ${name}... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${url}" 2>/dev/null)
    
    if [ "$response" == "$expected_code" ]; then
        echo -e "${GREEN}✅ 通过${NC} (HTTP ${response})"
        ((passed++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC} (HTTP ${response:-无响应})"
        ((failed++))
        return 1
    fi
}

echo "1️⃣  基础服务健康检查"
echo "─────────────────────────────────────────────────────────"
check_endpoint "YL-monitor Health" "${YL_MONITOR}/api/health"
check_endpoint "AR-backend Health" "${AR_BACKEND}/health"
check_endpoint "User GUI Status" "${USER_GUI}/status"

echo ""
echo "2️⃣  五层监控架构检查"
echo "─────────────────────────────────────────────────────────"
check_endpoint "L1 基础设施监控" "${YL_MONITOR}/api/v1/monitor/infrastructure"
check_endpoint "L2 系统资源监控" "${YL_MONITOR}/api/v1/monitor/system-resources"
check_endpoint "L3 应用服务监控" "${YL_MONITOR}/api/v1/monitor/application"
check_endpoint "L4 业务功能监控" "${YL_MONITOR}/api/v1/monitor/business"
check_endpoint "L5 用户体验监控" "${YL_MONITOR}/api/v1/monitor/user-experience"

echo ""
echo "3️⃣  监控数据验证"
echo "─────────────────────────────────────────────────────────"

# 获取并显示监控概览
echo "  📊 监控概览:"
overview=$(curl -s --max-time 5 "${YL_MONITOR}/api/v1/monitor/overview" 2>/dev/null)
if [ -n "$overview" ]; then
    echo "$overview" | python3 -m json.tool 2>/dev/null | sed 's/^/    /'
else
    echo -e "    ${YELLOW}⚠️  无法获取概览数据${NC}"
fi

echo ""
echo "4️⃣  详细监控数据采样"
echo "─────────────────────────────────────────────────────────"

# 采样各层数据
layers=(
    "infrastructure:基础设施"
    "system-resources:系统资源"
    "application:应用服务"
    "business:业务功能"
    "user-experience:用户体验"
)

for layer in "${layers[@]}"; do
    IFS=':' read -r endpoint name <<< "$layer"
    
    echo "  🔍 ${name}层数据:"
    data=$(curl -s --max-time 3 "${YL_MONITOR}/api/v1/monitor/${endpoint}" 2>/dev/null)
    
    if [ -n "$data" ]; then
        # 提取关键指标数量
        metrics_count=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "N/A")
        echo -e "    ${GREEN}✅${NC} 数据正常 (${metrics_count} 个指标)"
    else
        echo -e "    ${RED}❌${NC} 无法获取数据"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📈 验证结果统计"
echo "═══════════════════════════════════════════════════════════"
echo -e "  通过: ${GREEN}${passed}${NC}"
echo -e "  失败: ${RED}${failed}${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过！监控系统运行正常。${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  发现 ${failed} 个问题，请检查服务状态。${NC}"
    echo ""
    echo "排查建议:"
    echo "  1. 检查服务是否已启动: ./check-status.sh"
    echo "  2. 启动所有服务: ./start-all.sh"
    echo "  3. 查看日志: tail -f logs/*.log"
    exit 1
fi
