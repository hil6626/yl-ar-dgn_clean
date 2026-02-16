#!/bin/bash
# Rollback Script for YL-AR-DGN
# Usage: ./scripts/rollback.sh [environment] [version]

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
VERSION=${2:-latest}

log_info "开始回滚 ${ENVIRONMENT} 环境到版本: ${VERSION}"

# Load environment configuration
CONFIG_FILE="config/${ENVIRONMENT}.env"
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

source "$CONFIG_FILE"

export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-yl-ar-dgn}

# Stop current services
log_info "停止当前服务..."
docker-compose down --remove-orphans

# Pull the specified version
log_info "拉取指定版本镜像: ${VERSION}"
docker-compose pull || true

# Update image tags
log_info "更新镜像标签..."
docker tag ${{ secrets.DOCKERHUB_USERNAME }}/ar-backend:${VERSION} \
  ${{ secrets.DOCKERHUB_USERNAME }}/ar-backend:latest 2>/dev/null || true

docker tag ${{ secrets.DOCKERHUB_USERNAME }}/yl-monitor:${VERSION} \
  ${{ secrets.DOCKERHUB_USERNAME }}/yl-monitor:latest 2>/dev/null || true

docker tag ${{ secrets.DOCKERHUB_USERNAME }}/user:${VERSION} \
  ${{ secrets.DOCKERHUB_USERNAME }}/user:latest 2>/dev/null || true

# Start services with previous version
log_info "启动服务..."
docker-compose up -d

# Wait for services to be healthy
log_info "等待服务启动..."
sleep 30

# Verify services are running
log_info "验证服务状态..."
ROLLBACK_SUCCESS=true

# Check AR-backend
if ! curl -sf http://0.0.0.0:8000/health > /dev/null 2>&1; then
    log_error "AR-backend 回滚验证失败"
    ROLLBACK_SUCCESS=false
fi

# Check Prometheus
if ! curl -sf http://0.0.0.0:9090/api/v1/query?query=up > /dev/null 2>&1; then
    log_error "Prometheus 回滚验证失败"
    ROLLBACK_SUCCESS=false
fi

# Check Grafana
if ! curl -sf http://0.0.0.0:3000/api/health > /dev/null 2>&1; then
    log_error "Grafana 回滚验证失败"
    ROLLBACK_SUCCESS=false
fi

if [ "$ROLLBACK_SUCCESS" = true ]; then
    log_info "✅ 回滚成功！所有服务已恢复到版本: ${VERSION}"
else
    log_error "❌ 回滚失败，请手动检查服务状态"
    exit 1
fi

# Send rollback notification
log_info "发送回滚通知..."
python3 scripts/notify_rollback.py $ENVIRONMENT ${VERSION} 2>/dev/null || log_warn "回滚通知发送失败"

