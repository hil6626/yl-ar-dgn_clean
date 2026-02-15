#!/bin/bash
# AR Backend Docker 管理脚本
# 
# 使用方法:
#   ./manage_docker.sh up        - 启动所有服务
#   ./manage_docker.sh down      - 停止所有服务
#   ./manage_docker.sh restart   - 重启所有服务
#   ./manage_docker.sh logs      - 查看日志
#   ./manage_docker.sh build     - 构建镜像
#   ./manage_docker.sh status    - 查看状态
#   ./manage_docker.sh ps        - 查看容器
#   ./manage_docker.sh clean     - 清理资源

set -e

# 配置
COMPOSE_FILE="docker-compose.yml"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION=${1:-"help"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose 未安装，请先安装 Docker Compose"
            exit 1
        fi
    fi
}

# 切换到项目目录
cd "$PROJECT_DIR"

# 命令处理
case "$ACTION" in
    up)
        log_info "启动所有服务..."
        check_docker
        docker compose -f "$COMPOSE_FILE" up -d
        log_success "服务已启动"
        echo ""
        echo "服务状态:"
        docker compose -f "$COMPOSE_FILE" ps
        ;;
        
    down)
        log_info "停止所有服务..."
        check_docker
        docker compose -f "$COMPOSE_FILE" down
        log_success "服务已停止"
        ;;
        
    restart)
        log_info "重启所有服务..."
        check_docker
        docker compose -f "$COMPOSE_FILE" restart
        log_success "服务已重启"
        ;;
        
    logs)
        log_info "查看日志 (Ctrl+C 退出)..."
        check_docker
        docker compose -f "$COMPOSE_FILE" logs -f
        ;;
        
    build)
        log_info "构建镜像..."
        check_docker
        docker compose -f "$COMPOSE_FILE" build --no-cache
        log_success "镜像构建完成"
        ;;
        
    status)
        log_info "查看服务状态..."
        check_docker
        docker compose -f "$COMPOSE_FILE" ps
        echo ""
        echo "资源使用:"
        docker stats --no-stream $(docker compose -f "$COMPOSE_FILE" ps -q) 2>/dev/null || echo "无法获取资源统计"
        ;;
        
    ps)
        log_info "查看容器列表..."
        check_docker
        docker compose -f "$COMPOSE_FILE" ps
        ;;
        
    clean)
        log_warning "清理 Docker 资源..."
        check_docker
        
        # 停止并删除容器
        docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
        
        # 删除悬空镜像
        docker image prune -f
        
        # 删除未使用的网络
        docker network prune -f
        
        log_success "资源清理完成"
        ;;
        
    rebuild)
        log_info "重新构建并启动..."
        check_docker
        docker compose -f "$COMPOSE_FILE" down
        docker compose -f "$COMPOSE_FILE" build --no-cache
        docker compose -f "$COMPOSE_FILE" up -d
        log_success "重建完成"
        ;;
        
    health)
        log_info "检查服务健康状态..."
        check_docker
        
        SERVICES=$(docker compose -f "$COMPOSE_FILE" ps -q)
        for container in $SERVICES; do
            NAME=$(docker inspect --format='{{.Name}}' "$container" 2>/dev/null | sed 's/^\///')
            STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")
            
            if [ "$STATUS" = "healthy" ]; then
                log_success "$NAME: healthy"
            else
                log_warning "$NAME: $STATUS"
            fi
        done
        ;;
        
    help|*)
        echo ""
        echo "=========================================="
        echo "  AR Backend Docker 管理脚本"
        echo "=========================================="
        echo ""
        echo "用法: $0 <命令>"
        echo ""
        echo "可用命令:"
        echo "  up       - 启动所有服务"
        echo "  down     - 停止所有服务"
        echo "  restart  - 重启所有服务"
        echo "  logs     - 查看日志 (实时)"
        echo "  build    - 构建镜像"
        echo "  status   - 查看状态和资源使用"
        echo "  ps       - 查看容器列表"
        echo "  clean    - 清理 Docker 资源"
        echo "  rebuild  - 重新构建并启动"
        echo "  health   - 检查服务健康状态"
        echo "  help     - 显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  $0 up        # 启动服务"
        echo "  $0 logs      # 查看日志"
        echo "  $0 down      # 停止服务"
        echo ""
        ;;
esac
