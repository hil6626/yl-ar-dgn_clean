#!/bin/bash
# Deployment Script for YL-AR-DGN
# Usage: ./scripts/deploy.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check parameters
if [ $# -lt 1 ]; then
    log_error "请指定环境: staging 或 production"
    exit 1
fi

ENVIRONMENT=$1
log_info "开始部署到 ${ENVIRONMENT} 环境"

# Load environment configuration
CONFIG_FILE="config/${ENVIRONMENT}.env"
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

source "$CONFIG_FILE"

# Load environment variables
export IMAGE_TAG=${IMAGE_TAG:-latest}
export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-yl-ar-dgn}

log_info "使用镜像标签: ${IMAGE_TAG}"

# Pull latest images
log_info "拉取最新镜像..."
docker-compose pull

# Backup database
log_info "备份数据库..."
BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
docker-compose exec -T postgres pg_dump -U ${DB_USER:-ar_dgn} ${DB_NAME:-ar_dgn} > "$BACKUP_FILE" 2>/dev/null || log_warn "数据库备份失败，跳过"

# Stop old services
log_info "停止旧服务..."
docker-compose down --remove-orphans

# Start new services
log_info "启动新服务..."
docker-compose up -d

# Wait for services to be healthy
log_info "等待服务启动..."
sleep 30

# Run health checks
log_info "运行健康检查..."
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    HEALTHY=true
    
    # Check AR-backend
    if ! curl -sf http://0.0.0.0:8000/health > /dev/null 2>&1; then
        log_warn "AR-backend 健康检查失败"
        HEALTHY=false
    fi
    
    # Check Prometheus
    if ! curl -sf http://0.0.0.0:9090/api/v1/query?query=up > /dev/null 2>&1; then
        log_warn "Prometheus 健康检查失败"
        HEALTHY=false
    fi
    
    # Check Grafana
    if ! curl -sf http://0.0.0.0:3000/api/health > /dev/null 2>&1; then
        log_warn "Grafana 健康检查失败"
        HEALTHY=false
    fi
    
    if [ "$HEALTHY" = true ]; then
        log_info "所有服务健康检查通过"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_warn "健康检查失败，${RETRY_COUNT}/${MAX_RETRIES}，等待10秒后重试..."
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "健康检查失败，执行回滚..."
    ./scripts/rollback.sh $ENVIRONMENT
    exit 1
fi

# Run smoke tests
log_info "运行冒烟测试..."
SMOKE_TEST_PASSED=true

# Test API endpoint
if ! curl -sf http://0.0.0.0:8000/api/users > /dev/null 2>&1; then
    log_warn "API冒烟测试失败"
    SMOKE_TEST_PASSED=false
fi

# Test monitoring endpoint
if ! curl -sf http://0.0.0.0:9090/api/v1/alerts > /dev/null 2>&1; then
    log_warn "监控冒烟测试失败"
    SMOKE_TEST_PASSED=false
fi

if [ "$SMOKE_TEST_PASSED" = false ]; then
    log_error "冒烟测试失败，执行回滚..."
    ./scripts/rollback.sh $ENVIRONMENT
    exit 1
fi

log_info "部署完成！"

# Cleanup old images
log_info "清理旧镜像..."
docker image prune -af --filter "until=24h" 2>/dev/null || true

# Send deployment notification
log_info "发送部署通知..."
python3 scripts/notify_deployment.py $ENVIRONMENT ${IMAGE_TAG} 2>/dev/null || log_warn "部署通知发送失败"

log_info "✅ 部署成功完成"

