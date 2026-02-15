#!/bin/bash
# infrastructure/recovery.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查Docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
}

# 停止所有服务
stop_services() {
    log_info "停止所有服务..."
    docker-compose down --remove-orphans 2>/dev/null || true
}

# 清理Docker资源
cleanup_docker() {
    log_info "清理Docker资源..."
    docker system prune -af 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
}

# 创建网络
create_networks() {
    log_info "创建Docker网络..."
    docker network create --driver bridge backend_network 2>/dev/null || true
    docker network create --driver bridge monitoring_network 2>/dev/null || true
}

# 启动基础服务
start_infrastructure() {
    log_info "启动基础设施服务..."
    docker-compose up -d postgres redis
    sleep 10

    # 检查基础服务状态
    if ! docker-compose ps postgres | grep -q "Up"; then
        log_error "PostgreSQL启动失败"
        exit 1
    fi

    if ! docker-compose ps redis | grep -q "Up"; then
        log_error "Redis启动失败"
        exit 1
    fi

    log_info "基础服务启动成功"
}

# 启动监控服务
start_monitoring() {
    log_info "启动监控服务..."
    docker-compose up -d prometheus grafana alertmanager node-exporter
    sleep 15

    # 检查监控服务状态
    services=("prometheus" "grafana" "alertmanager" "node-exporter")
    for service in "${services[@]}"; do
        if ! docker-compose ps $service | grep -q "Up"; then
            log_warn "$service 启动失败，跳过"
        else
            log_info "$service 启动成功"
        fi
    done
}

# 验证服务健康
verify_services() {
    log_info "验证服务健康状态..."

    # 检查PostgreSQL
    if docker-compose exec -T postgres pg_isready -U admin >/dev/null 2>&1; then
        log_info "PostgreSQL健康检查通过"
    else
        log_warn "PostgreSQL健康检查失败"
    fi

    # 检查Redis
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_info "Redis健康检查通过"
    else
        log_warn "Redis健康检查失败"
    fi

    # 检查Prometheus
    if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_info "Prometheus健康检查通过"
    else
        log_warn "Prometheus健康检查失败"
    fi

    # 检查Grafana
    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        log_info "Grafana健康检查通过"
    else
        log_warn "Grafana健康检查失败"
    fi
}

# 显示服务状态
show_status() {
    log_info "当前服务状态:"
    docker-compose ps
}

# 主函数
main() {
    log_info "开始基础设施恢复..."

    check_docker
    stop_services
    cleanup_docker
    create_networks
    start_infrastructure
    start_monitoring
    verify_services
    show_status

    log_info "基础设施恢复完成！"
    log_info "访问地址:"
    log_info "  Grafana: http://localhost:3000 (admin/admin)"
    log_info "  Prometheus: http://localhost:9090"
    log_info "  Alertmanager: http://localhost:9093"
}

# 参数处理
case "${1:-}" in
    "stop")
        log_info "停止所有服务..."
        stop_services
        ;;
    "cleanup")
        log_info "清理Docker资源..."
        cleanup_docker
        ;;
    "status")
        show_status
        ;;
    "verify")
        verify_services
        ;;
    *)
        main
        ;;
esac
