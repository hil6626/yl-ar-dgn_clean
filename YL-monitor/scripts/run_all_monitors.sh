#!/bin/bash
# YL-Monitor 统一监控入口脚本
# 功能：顺序执行所有监控脚本，聚合输出结果

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 设置 Python 路径，确保能导入 _common 模块
export PYTHONPATH="${PROJECT_ROOT}/scripts:${PYTHONPATH:-}"

# 日志和报告目录
LOG_DIR="$PROJECT_ROOT/logs"
REPORT_DIR="$PROJECT_ROOT/data/metrics"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/monitor_run_$TIMESTAMP.log"
JSON_REPORT="$REPORT_DIR/monitor_report_$TIMESTAMP.json"
HTML_REPORT="$REPORT_DIR/monitor_report_$TIMESTAMP.html"

# 创建目录
mkdir -p "$LOG_DIR" "$REPORT_DIR"

# 监控脚本列表（按优先级排序）
MONITOR_SCRIPTS=(
    "scripts/monitor/01_cpu_usage_monitor.py"
    "scripts/monitor/02_memory_usage_monitor.py"
    "scripts/monitor/03_disk_space_io_monitor.py"
    "scripts/monitor/04_system_load_process_monitor.py"
    "scripts/monitor/05_port_service_availability_check.py"
    "scripts/monitor/07_external_api_health_check.py"
    "scripts/monitor/10_log_anomaly_scan.py"
)

# 统计变量
TOTAL=0
SUCCESS=0
FAILED=0
RESULTS=()

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         YL-Monitor 系统监控任务启动                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo -e "${YELLOW}启动时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${YELLOW}日志文件: $LOG_FILE${NC}"
echo -e "${YELLOW}JSON报告: $JSON_REPORT${NC}"
echo ""

# 执行监控脚本
for script in "${MONITOR_SCRIPTS[@]}"; do
    TOTAL=$((TOTAL + 1))
    script_name=$(basename "$script" .py)
    
    echo -e "${BLUE}[${TOTAL}/${#MONITOR_SCRIPTS[@]}] 执行: ${script_name}${NC}"
    
    if [ -f "$script" ]; then
        # 执行脚本并捕获输出（在脚本所在目录运行）
        script_dir=$(dirname "$script")
        script_name=$(basename "$script")
        output=$(cd "$script_dir" && python3 "$script_name" --pretty 2>&1) && exit_code=0 || exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo -e "  ${GREEN}✓ 成功${NC}"
            SUCCESS=$((SUCCESS + 1))
            status="ok"
        else
            echo -e "  ${RED}✗ 失败 (退出码: $exit_code)${NC}"
            FAILED=$((FAILED + 1))
            status="error"
        fi
        
        # 保存结果
        RESULTS+=("{\"script\":\"$script_name\",\"status\":\"$status\",\"exit_code\":$exit_code,\"output\":$(echo "$output" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))" 2>/dev/null || echo '\"\"')}")
        
        # 记录到日志
        echo "[$script_name] Exit: $exit_code" >> "$LOG_FILE"
        echo "$output" >> "$LOG_FILE"
        echo "---" >> "$LOG_FILE"
    else
        echo -e "  ${YELLOW}⚠ 脚本不存在: $script${NC}"
        RESULTS+=("{\"script\":\"$script_name\",\"status\":\"missing\",\"exit_code\":-1,\"output\":\"\"}")
    fi
done

# 生成 JSON 报告
echo "{" > "$JSON_REPORT"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$JSON_REPORT"
echo "  \"summary\": {" >> "$JSON_REPORT"
echo "    \"total\": $TOTAL," >> "$JSON_REPORT"
echo "    \"success\": $SUCCESS," >> "$JSON_REPORT"
echo "    \"failed\": $FAILED," >> "$JSON_REPORT"
echo "    \"success_rate\": $(awk "BEGIN {printf \"%.2f\", $SUCCESS/$TOTAL*100}")" >> "$JSON_REPORT"
echo "  }," >> "$JSON_REPORT"
echo "  \"results\": [" >> "$JSON_REPORT"

# 写入结果数组
first=true
for result in "${RESULTS[@]}"; do
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$JSON_REPORT"
    fi
    echo -n "    $result" >> "$JSON_REPORT"
done

echo "" >> "$JSON_REPORT"
echo "  ]" >> "$JSON_REPORT"
echo "}" >> "$JSON_REPORT"

# 生成 HTML 报告
cat > "$HTML_REPORT" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YL-Monitor 监控报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2rem; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label { color: #666; margin-top: 5px; }
        .results { padding: 30px; }
        .result-item {
            display: flex;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            background: #f8f9fa;
        }
        .status-ok { border-left: 4px solid #28a745; }
        .status-error { border-left: 4px solid #dc3545; }
        .status-missing { border-left: 4px solid #ffc107; }
        .status-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-size: 1.2rem;
        }
        .status-ok .status-icon { background: #d4edda; color: #155724; }
        .status-error .status-icon { background: #f8d7da; color: #721c24; }
        .status-missing .status-icon { background: #fff3cd; color: #856404; }
        .result-info { flex: 1; }
        .result-name { font-weight: 600; color: #333; }
        .result-status { font-size: 0.9rem; color: #666; }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 YL-Monitor 监控报告</h1>
            <p>生成时间: $(date '+%Y-%m-%d %H:%M:%S')</p>
        </div>
        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">$TOTAL</div>
                <div class="stat-label">总任务数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">$SUCCESS</div>
                <div class="stat-label">成功</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">$FAILED</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #667eea;">$(awk "BEGIN {printf \"%.1f\", $SUCCESS/$TOTAL*100}")%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
        <div class="results">
            <h2 style="margin-bottom: 20px; color: #333;">执行详情</h2>
HTMLEOF

# 添加结果项到 HTML
for i in "${!RESULTS[@]}"; do
    result="${RESULTS[$i]}"
    script_name=$(echo "$result" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['script'])" 2>/dev/null || echo "unknown")
    status=$(echo "$result" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['status'])" 2>/dev/null || echo "unknown")
    
    case $status in
        "ok") icon="✓"; class="status-ok"; status_text="成功" ;;
        "error") icon="✗"; class="status-error"; status_text="失败" ;;
        *) icon="⚠"; class="status-missing"; status_text="未找到" ;;
    esac
    
    cat >> "$HTML_REPORT" << HTMLEOF
            <div class="result-item $class">
                <div class="status-icon">$icon</div>
                <div class="result-info">
                    <div class="result-name">$script_name</div>
                    <div class="result-status">状态: $status_text</div>
                </div>
            </div>
HTMLEOF
done

cat >> "$HTML_REPORT" << 'HTMLEOF'
        </div>
        <div class="footer">
            <p>YL-Monitor 自动化监控系统 | 实时守护您的应用健康</p>
        </div>
    </div>
</body>
</html>
HTMLEOF

# 输出总结
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    执行完成总结                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo -e "总任务数: ${TOTAL}"
echo -e "成功: ${GREEN}${SUCCESS}${NC}"
echo -e "失败: ${RED}${FAILED}${NC}"
echo -e "成功率: ${YELLOW}$(awk "BEGIN {printf \"%.1f\", $SUCCESS/$TOTAL*100}")%${NC}"
echo ""
echo -e "📄 日志文件: ${BLUE}$LOG_FILE${NC}"
echo -e "📊 JSON报告: ${BLUE}$JSON_REPORT${NC}"
echo -e "🌐 HTML报告: ${BLUE}$HTML_REPORT${NC}"

# 创建最新报告的符号链接
ln -sf "$HTML_REPORT" "$REPORT_DIR/latest_report.html"

# 输出最新报告路径（供其他脚本使用）
echo ""
echo "LATEST_REPORT=$REPORT_DIR/latest_report.html"

exit $FAILED
