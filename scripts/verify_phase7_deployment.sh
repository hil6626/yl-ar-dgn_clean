#!/bin/bash
# 阶段7监控体系完善 - 部署验证脚本
# 创建时间: 2026-02-11

echo "========================================"
echo "阶段7监控体系完善 - 部署验证"
echo "========================================"
echo ""

errors=0
warnings=0

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2: $1"
        return 0
    else
        echo -e "${RED}✗${NC} $2: $1 (缺失)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2: $1"
        return 0
    else
        echo -e "${RED}✗${NC} $2: $1 (缺失)"
        return 1
    fi
}

echo "1. 检查YL-monitor核心文件..."
echo "----------------------------------------"

# 检查关键文件
check_file "YL-monitor/app/routes/dashboard.py" "Dashboard路由" || ((errors++))
check_file "YL-monitor/app/ws/dashboard_ws.py" "Dashboard WebSocket" || ((errors++))
check_file "YL-monitor/app/ws/alerts_ws.py" "告警WebSocket" || ((errors++))
check_file "YL-monitor/app/services/metrics_storage.py" "指标存储服务" || ((errors++))
check_file "YL-monitor/app/services/alert_service.py" "告警服务" || ((errors++))
check_file "YL-monitor/config/alert_rules.yaml" "告警规则配置" || ((errors++))

echo ""
echo "2. 检查阶段7任务文件..."
echo "----------------------------------------"

# 检查阶段7要求的文件（任务7.1）
check_file "YL-monitor/templates/dashboard_enhanced.html" "增强版监控面板HTML" || ((errors++))
check_file "YL-monitor/static/js/dashboard_enhanced.js" "增强版监控面板JS" || ((errors++))

echo ""
echo "3. 检查AR-backend监控服务..."
echo "----------------------------------------"

check_file "AR-backend/monitor_server.py" "监控服务器" || ((errors++))
check_file "AR-backend/monitor_config.yaml" "监控配置" || ((errors++))
check_file "AR-backend/start_monitor.sh" "监控启动脚本" || ((errors++))

echo ""
echo "4. 检查WebSocket端点..."
echo "----------------------------------------"

# 检查WebSocket端点配置
if grep -q "/ws/dashboard/realtime" YL-monitor/app/ws/dashboard_ws.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Dashboard WebSocket端点: /ws/dashboard/realtime"
else
    echo -e "${RED}✗${NC} Dashboard WebSocket端点未找到"
    ((errors++))
fi

if grep -q "/ws/alerts" YL-monitor/app/ws/alerts_ws.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 告警WebSocket端点: /ws/alerts"
else
    echo -e "${RED}✗${NC} 告警WebSocket端点未找到"
    ((errors++))
fi

# 检查文档要求的端点
if grep -q "/ws/metrics" YL-monitor/app/ws/*.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 文档要求的端点 /ws/metrics 存在"
else
    echo -e "${YELLOW}⚠${NC} 文档要求的端点 /ws/metrics 缺失 (使用 /ws/dashboard/realtime 代替)"
    ((warnings++))
fi

echo ""
echo "5. 检查CORS配置..."
echo "----------------------------------------"

# 检查AR-backend CORS配置
if grep -q 'origins:.*"\*"' AR-backend/monitor_config.yaml 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} AR-backend CORS配置为 '*' (生产环境不安全)"
    ((warnings++))
else
    echo -e "${GREEN}✓${NC} AR-backend CORS配置已限制"
fi

# 检查YL-monitor CORS配置
if [ -f "YL-monitor/app/main.py" ]; then
    if grep -q "CORSMiddleware\|CORS" YL-monitor/app/main.py 2>/dev/null; then
        echo -e "${GREEN}✓${NC} YL-monitor CORS中间件已配置"
    else
        echo -e "${YELLOW}⚠${NC} YL-monitor CORS配置未找到"
        ((warnings++))
    fi
fi

echo ""
echo "6. 检查安全配置..."
echo "----------------------------------------"

# 检查API认证配置
if grep -q "api_key_enabled: true" AR-backend/monitor_config.yaml 2>/dev/null; then
    echo -e "${GREEN}✓${NC} AR-backend API认证已启用"
else
    echo -e "${YELLOW}⚠${NC} AR-backend API认证未启用"
    ((warnings++))
fi

echo ""
echo "7. 检查服务运行状态..."
echo "----------------------------------------"

# 检查AR-backend监控服务
if pgrep -f "monitor_server.py" > /dev/null; then
    echo -e "${GREEN}✓${NC} AR-backend监控服务运行中"
    
    # 测试健康检查端点
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5501/health 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} 健康检查端点 /health 响应正常 (200)"
    else
        echo -e "${YELLOW}⚠${NC} 健康检查端点 /health 响应异常 (HTTP $response)"
        ((warnings++))
    fi
else
    echo -e "${YELLOW}⚠${NC} AR-backend监控服务未运行"
    ((warnings++))
fi

# 检查YL-monitor服务
if pgrep -f "uvicorn app.main:app" > /dev/null || curl -s http://localhost:5500/api/v1/dashboard/overview > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} YL-monitor服务运行中"
else
    echo -e "${YELLOW}⚠${NC} YL-monitor服务未运行或无法访问"
    ((warnings++))
fi

echo ""
echo "========================================"
echo "验证结果汇总"
echo "========================================"
echo -e "错误数: ${RED}$errors${NC}"
echo -e "警告数: ${YELLOW}$warnings${NC}"

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ 阶段7监控体系部署验证通过${NC}"
    exit 0
elif [ $errors -eq 0 ]; then
    echo -e "${YELLOW}⚠ 阶段7监控体系部署验证通过，但有警告${NC}"
    exit 0
else
    echo -e "${RED}✗ 阶段7监控体系部署验证失败${NC}"
    echo ""
    echo "请根据上述错误信息修复问题，参考 TODO.md 中的修复建议。"
    exit 1
fi
