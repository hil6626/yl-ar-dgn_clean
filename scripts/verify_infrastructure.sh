#!/bin/bash
# scripts/verify_infrastructure.sh
# 基础设施部署验证脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 检查项计数器
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_TOTAL=0

# 检查函数
check_item() {
    local description=$1
    local command=$2
    local expected=$3
    
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    if eval "$command" >/dev/null 2>&1; then
        if [ "$expected" = "pass" ]; then
            echo -e "${GREEN}✓${NC} $description"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗${NC} $description (应失败但成功)"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            return 1
        fi
    else
        if [ "$expected" = "fail" ]; then
            echo -e "${GREEN}✓${NC} $description (预期失败)"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗${NC} $description"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            return 1
        fi
    fi
}

# 验证Docker环境
verify_docker() {
    log_section "验证Docker环境"
    
    check_item "Docker服务运行中" "docker info" "pass"
    check_item "Docker Compose可用" "docker-compose --version" "pass"
    
    # 检查网络
    log_info "检查Docker网络..."
    docker network ls | grep -E "(backend_network|monitoring_network)" || true
}

# 验证配置文件
verify_configs() {
    log_section "验证配置文件"
    
    local configs=(
        "infrastructure/config.yaml"
        "infrastructure/prometheus.yml"
        "infrastructure/alertmanager.yml"
        "infrastructure/prometheus/rules/infrastructure_alerts.yml"
        "infrastructure/grafana/provisioning/datasources/prometheus.yml"
        "infrastructure/grafana/provisioning/dashboards/dashboards.yml"
        "infrastructure/grafana/dashboards/infrastructure.json"
        "infrastructure/configs/postgres_exporter.yml"
        "infrastructure/configs/redis_exporter.yml"
        "docker-compose.yml"
    )
    
    for config in "${configs[@]}"; do
        if [ -f "$config" ]; then
            echo -e "${GREEN}✓${NC} $config 存在"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} $config 不存在"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
        fi
        CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    done
}

# 验证Docker Compose配置
verify_docker_compose() {
    log_section "验证Docker Compose配置"
    
    # 验证YAML语法
    if docker-compose config >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Docker Compose配置语法正确"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Docker Compose配置语法错误"
        docker-compose config
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    # 检查必需的服务
    local services=("postgres" "redis" "prometheus" "grafana" "alertmanager" "node-exporter")
    for service in "${services[@]}"; do
        if docker-compose config | grep -q "$service:"; then
            echo -e "${GREEN}✓${NC} 服务 $service 已配置"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} 服务 $service 未配置"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
        fi
        CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    done
}

# 验证端口占用
verify_ports() {
    log_section "验证端口配置"
    
    local ports=(
        "5432:postgres"
        "6379:redis"
        "9090:prometheus"
        "3000:grafana"
        "9093:alertmanager"
        "9100:node-exporter"
        "9187:postgres-exporter"
        "9121:redis-exporter"
    )
    
    for port_service in "${ports[@]}"; do
        port="${port_service%%:*}"
        service="${port_service##*:}"
        
        if docker-compose config | grep -q "\"$port\""; then
            echo -e "${GREEN}✓${NC} 端口 $port -> $service"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            echo -e "${YELLOW}⚠${NC} 端口 $port 配置未找到 (可能使用自定义配置)"
        fi
        CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    done
}

# 验证监控配置
verify_monitoring() {
    log_section "验证监控配置"
    
    # Prometheus配置
    if grep -q "scrape_configs:" infrastructure/prometheus.yml; then
        echo -e "${GREEN}✓${NC} Prometheus scrape配置存在"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Prometheus scrape配置缺失"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    # Alertmanager配置
    if grep -q "receivers:" infrastructure/alertmanager.yml; then
        echo -e "${GREEN}✓${NC} Alertmanager receivers配置存在"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Alertmanager receivers配置缺失"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    # 告警规则
    local alert_count=$(grep -c "^      - alert:" infrastructure/prometheus/rules/infrastructure_alerts.yml || echo "0")
    echo -e "${GREEN}✓${NC} 告警规则数量: $alert_count"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    # Grafana数据源
    if grep -q "name: Prometheus" infrastructure/grafana/provisioning/datasources/prometheus.yml; then
        echo -e "${GREEN}✓${NC} Grafana Prometheus数据源配置存在"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Grafana Prometheus数据源配置缺失"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
}

# 验证存储配置
verify_storage() {
    log_section "验证存储配置"
    
    local volumes=(
        "postgres_data"
        "redis_data"
        "prometheus_data"
        "grafana_data"
    )
    
    for volume in "${volumes[@]}"; do
        if docker-compose config | grep -q "$volume:"; then
            echo -e "${GREEN}✓${NC} 存储卷 $volume 已配置"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} 存储卷 $volume 未配置"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
        fi
        CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    done
}

# 验证网络配置
verify_network() {
    log_section "验证网络配置"
    
    local networks=(
        "backend_network"
        "monitoring_network"
    )
    
    for network in "${networks[@]}"; do
        if docker-compose config | grep -q "$network:"; then
            echo -e "${GREEN}✓${NC} 网络 $network 已配置"
            CHECKS_PASSED=$((CHECKS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} 网络 $network 未配置"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
        fi
        CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    done
}

# 验证健康检查配置
verify_healthchecks() {
    log_section "验证健康检查配置"
    
    local services_with_healthcheck=0
    local services_total=0
    
    # 检查docker-compose.yml中的健康检查
    if grep -q "healthcheck:" docker-compose.yml; then
        echo -e "${GREEN}✓${NC} 健康检查配置存在"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} 健康检查配置缺失"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
}

# 打印总结
print_summary() {
    log_section "验证总结"
    
    echo -e "总检查项: $CHECKS_TOTAL"
    echo -e "${GREEN}通过: $CHECKS_PASSED${NC}"
    echo -e "${RED}失败: $CHECKS_FAILED${NC}"
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ 所有检查通过！基础设施配置正确。${NC}"
        return 0
    else
        echo -e "\n${RED}✗ 存在失败的检查项，请修复后重试。${NC}"
        return 1
    fi
}

# 主函数
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   基础设施部署验证${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    verify_docker
    verify_configs
    verify_docker_compose
    verify_ports
    verify_monitoring
    verify_storage
    verify_network
    verify_healthchecks
    print_summary
}

# 参数处理
case "${1:-}" in
    "--docker")
        verify_docker
        ;;
    "--configs")
        verify_configs
        ;;
    "--compose")
        verify_docker_compose
        ;;
    "--ports")
        verify_ports
        ;;
    "--monitoring")
        verify_monitoring
        ;;
    "--storage")
        verify_storage
        ;;
    "--network")
        verify_network
        ;;
    "--health")
        verify_healthchecks
        ;;
    "--help"|"-h")
        echo "用法: $0 [选项]"
        echo "选项:"
        echo "  --docker     验证Docker环境"
        echo "  --configs    验证配置文件"
        echo "  --compose    验证Docker Compose配置"
        echo "  --ports      验证端口配置"
        echo "  --monitoring 验证监控配置"
        echo "  --storage    验证存储配置"
        echo "  --network    验证网络配置"
        echo "  --health     验证健康检查配置"
        echo "  --help       显示此帮助信息"
        echo "  (无参数)   运行所有验证"
        ;;
    *)
        main
        ;;
esac

