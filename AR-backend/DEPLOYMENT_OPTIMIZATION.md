#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR Backend - 优化部署方案
=============================
部署架构设计文档

模块依赖关系:
├── app/launcher.py          → core/ + services/
├── core/path_manager.py     → 无外部依赖
├── core/utils.py            → 无外部依赖
├── services/core/           → core/
├── services/face/           → core/ + services/core/
├── services/integration/    → core/ + services/core/
├── services/monitor/        → core/ + services/core/
├── services/pipeline/       → core/ + services/core/
└── services/security/       → core/ + services/core/

作者: AI 架构师
版本: 1.0
最后更新: 2026-02-04
"""

# ============================================================================
# 第一部分: 技术架构设计
# ============================================================================

"""
## 一、当前架构分析

### 1.1 现有组件
├── AR-backend (单体应用)
│   ├── app/           # 应用入口
│   ├── core/          # 核心模块
│   ├── services/      # 业务服务
│   ├── integrations/  # 第三方集成
│   ├── config/        # 配置
│   └── data/          # 数据存储
└── 基础设施
    ├── Redis          # 缓存
    ├── Prometheus     # 监控
    ├── Grafana        # 可视化
    ├── Elasticsearch  # 日志存储
    ├── Fluentd        # 日志收集
    └── Alertmanager    # 告警

### 1.2 业务模块
├── face/              # 人脸处理
│   ├── detection/    # 人脸检测
│   ├── recognition/   # 人脸识别
│   └── synthesis/     # 人脸合成
├── integration/       # 集成模块
│   ├── DeepFaceLab/  # 高质量人脸
│   ├── faceswap/      # 人脸交换
│   └── obs_camera/    # 虚拟摄像头
├── monitor/           # 监控服务
│   └── health/        # 健康检查
├── pipeline/          # 处理流水线
│   ├── image_pipeline.py
│   ├── video_pipeline.py
│   └── pipeline_manager.py
└── security/          # 安全模块

## 二、优化后架构设计

### 2.1 微服务架构
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway (Nginx)                          │
│                    (负载均衡 + SSL终止 + 静态资源)                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│ Face Service  │    │ Video Process       │    │ Audio Service   │
│ (人脸合成)    │    │ Service (视频处理)  │    │ (音频合成)      │
│ Port: 8001    │    │ Port: 8002          │    │ Port: 8003      │
└───────────────┘    └─────────────────────┘    └─────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│ Monitor Svc   │    │ Scheduler Svc      │    │ API Gateway     │
│ (系统监控)    │    │ (任务调度)          │    │ (路由分发)      │
│ Port: 8004    │    │ Port: 8005          │    │ Port: 8000      │
└───────────────┘    └─────────────────────┘    └─────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Shared Infrastructure                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │
│  │  Redis   │ │   MQ     │ │   DB     │ │  Monitoring Stack     │   │
│  │ Cache    │ │ Queue    │ │ Storage  │ │  (Prometheus+Grafana) │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

### 2.2 服务划分
"""

# ============================================================================
# 第二部分: Docker Compose 优化配置
# ============================================================================

DOCKER_COMPOSE_TEMPLATE = '''# AR Backend - 优化部署配置
# ================================
# 部署命令:
#   开发环境: docker compose -f docker-compose.dev.yml up -d
#   生产环境: docker compose -f docker-compose.prod.yml up -d
#   GPU支持:  docker compose -f docker-compose.gpu.yml up -d

version: '3.8'

services:
  # -------------------------------------------------------------------------
  # API Gateway & 负载均衡
  # -------------------------------------------------------------------------
  nginx:
    image: nginx:alpine
    container_name: ar-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infrastructure/nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/var/www/static:ro
    restart: unless-stopped
    depends_on:
      - face-service
      - video-service
      - audio-service
      - monitor-service
    networks:
      - ar-internal
      - ar-external
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # -------------------------------------------------------------------------
  # 核心业务服务
  # -------------------------------------------------------------------------
  face-service:
    build:
      context: .
      dockerfile: Dockerfile.face-service
    container_name: ar-face-service
    ports:
      - "8001:8001"
    environment:
      - SERVICE_NAME=face-service
      - REDIS_URL=redis://redis:6379/0
      - MQ_URL=rabbitmq://rabbitmq:5672/
      - AR_LOG_LEVEL=INFO
      - GPU_ENABLED=${GPU_ENABLED:-false}
    volumes:
      - ./logs/face-service:/app/logs
      - ./data/faces:/app/data/faces
      - ./models:/app/models:ro
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8001/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: ${GPU_COUNT:-1}
              capabilities: [gpu]
      replicas: ${FACE_SERVICE_REPLICAS:-1}

  video-service:
    build:
      context: .
      dockerfile: Dockerfile.video-service
    container_name: ar-video-service
    ports:
      - "8002:8002"
    environment:
      - SERVICE_NAME=video-service
      - REDIS_URL=redis://redis:6379/0
      - MQ_URL=rabbitmq://rabbitmq:5672/
      - AR_LOG_LEVEL=INFO
      - GPU_ENABLED=${GPU_ENABLED:-false}
    volumes:
      - ./logs/video-service:/app/logs
      - ./data/videos:/app/data/videos
      - ./models:/app/models:ro
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8002/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3

  audio-service:
    build:
      context: .
      dockerfile: Dockerfile.audio-service
    container_name: ar-audio-service
    ports:
      - "8003:8003"
    environment:
      - SERVICE_NAME=audio-service
      - REDIS_URL=redis://redis:6379/0
      - MQ_URL=rabbitmq://rabbitmq:5672/
      - AR_LOG_LEVEL=INFO
    volumes:
      - ./logs/audio-service:/app/logs
      - ./data/audio:/app/data/audio
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8003/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3

  monitor-service:
    build:
      context: .
      dockerfile: Dockerfile.monitor-service
    container_name: ar-monitor-service
    ports:
      - "8004:8004"
    environment:
      - SERVICE_NAME=monitor-service
      - REDIS_URL=redis://redis:6379/0
      - PROMETHEUS_URL=http://prometheus:9090
      - AR_LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs:ro
      - ./data/metrics:/app/data/metrics
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      redis:
        condition: service_healthy
      prometheus:
        condition: service_started

  scheduler-service:
    build:
      context: .
      dockerfile: Dockerfile.scheduler-service
    container_name: ar-scheduler-service
    ports:
      - "8005:8005"
    environment:
      - SERVICE_NAME=scheduler-service
      - REDIS_URL=redis://redis:6379/0
      - MQ_URL=rabbitmq://rabbitmq:5672/
      - AR_LOG_LEVEL=INFO
    volumes:
      - ./logs/scheduler:/app/logs
      - ./data/tasks:/app/data/tasks
      - ./scripts:/app/scripts:ro
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  # -------------------------------------------------------------------------
  # 基础设施服务
  # -------------------------------------------------------------------------
  redis:
    image: redis:7-alpine
    container_name: ar-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - ar-internal
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  rabbitmq:
    image: rabbitmq:3.12-alpine
    container_name: ar-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=ar_user
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD:-ar_secret}
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    restart: unless-stopped
    networks:
      - ar-internal
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_port_connectivity"]
      interval: 30s
      timeout: 10s
      retries: 3

  # -------------------------------------------------------------------------
  # 监控与日志
  # -------------------------------------------------------------------------
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: ar-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    restart: unless-stopped
    networks:
      - ar-internal
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:10.0.0
    container_name: ar-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./infrastructure/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./infrastructure/grafana/dashboards:/var/lib/grafana/dashboards:ro
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      prometheus:
        condition: service_started

  alertmanager:
    image: prom/alertmanager:v0.25.0
    container_name: ar-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./infrastructure/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    restart: unless-stopped
    networks:
      - ar-internal
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: ar-elasticsearch
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    restart: unless-stopped
    networks:
      - ar-internal
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  fluentd:
    image: fluent/fluentd-kubernetes-daemonset:v1.16-debian-elasticsearch8-1
    container_name: ar-fluentd
    ports:
      - "24224:24224"
      - "24224:24224/udp"
    environment:
      - FLUENT_ELASTICSEARCH_HOST=elasticsearch
      - FLUENT_ELASTICSEARCH_PORT=9200
    volumes:
      - ./logs:/var/log/app:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    restart: unless-stopped
    networks:
      - ar-internal
    depends_on:
      elasticsearch:
        condition: service_healthy

  # -------------------------------------------------------------------------
  # 外部服务（可选）
  # -------------------------------------------------------------------------
  # 数据库（如果需要持久化存储）
  # postgres:
  #   image: postgres:15-alpine
  #   container_name: ar-postgres
  #   environment:
  #     - POSTGRES_USER=ar_user
  #     - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-ar_secret}
  #     - POSTGRES_DB=ar_backend
  #   volumes:
  #     - postgres-data:/var/lib/postgresql/data
  #   networks:
  #     - ar-internal

networks:
  ar-internal:
    driver: bridge
    internal: false

  ar-external:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

volumes:
  redis-data:
    driver: local
  rabbitmq-data:
    driver: local
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
  alertmanager-data:
    driver: local
  elasticsearch-data:
    driver: local
'''

# ============================================================================
# 第三部分: 部署检查清单
# ============================================================================

DEPLOYMENT_CHECKLIST = """
## 部署检查清单 (Deployment Checklist)

### 1. 环境准备
- [ ] Python 3.8+ 已安装
- [ ] Docker & Docker Compose 已安装
- [ ] GPU驱动 (如需要) 已安装
- [ ] NVIDIA Container Toolkit 已安装

### 2. 配置检查
- [ ] .env 文件已创建并配置
- [ ] 证书文件已准备 (如使用HTTPS)
- [ ] 模型文件已下载
- [ ] 端口未被占用

### 3. 依赖安装
- [ ] Docker 镜像构建成功
- [ ] 所有容器启动正常
- [ ] 健康检查通过

### 4. 功能验证
- [ ] Face Service API 可访问
- [ ] Video Service API 可访问
- [ ] Audio Service API 可访问
- [ ] Monitor Service 可访问
- [ ] Grafana 面板正常显示
- [ ] 告警配置生效

### 5. 性能测试
- [ ] 并发请求测试通过
- [ ] 资源使用率监控正常
- [ ] 日志收集功能正常
"""

# ============================================================================
# 第四部分: 部署脚本
# ============================================================================

DEPLOYMENT_SCRIPT = '''#!/bin/bash
# AR Backend - 一键部署脚本
# ================================
# 用法:
#   ./deploy.sh develop    # 开发环境
#   ./deploy.sh production # 生产环境
#   ./deploy.sh gpu        # GPU环境
#   ./deploy.sh status     # 查看状态
#   ./deploy.sh stop       # 停止服务
#   ./deploy.sh logs       # 查看日志

set -e  # 遇到错误立即退出

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# 配置
PROJECT_NAME="ar-backend"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

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
    log_info "检查 Docker 环境..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    
    log_success "Docker 环境检查通过"
}

# 加载环境变量
load_env() {
    if [ -f "$ENV_FILE" ]; then
        log_info "加载环境变量..."
        set -a
        source "$ENV_FILE"
        set +a
        log_success "环境变量已加载"
    else
        log_warning "未找到 $ENV_FILE 文件，使用默认配置"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    mkdir -p logs data/{faces,videos,audio,metrics,tasks} models static
    mkdir -p infrastructure/{nginx/ssl,prometheus,grafana/provisioning,grafana/dashboards,alertmanager}
    log_success "目录创建完成"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    docker compose build --no-cache
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    local mode=${1:-""}
    local compose_args="-d"
    
    if [ "$mode" == "gpu" ]; then
        export GPU_ENABLED=true
        export GPU_COUNT=all
    fi
    
    log_info "启动服务..."
    docker compose $compose_args up
    
    log_success "服务启动完成"
}

# 查看状态
status() {
    log_info "服务状态:"
    docker compose ps
}

# 查看日志
logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        docker compose logs -f "$service"
    else
        docker compose logs -f
    fi
}

# 停止服务
stop() {
    log_info "停止服务..."
    docker compose down --remove-orphans
    log_success "服务已停止"
}

# 清理资源
cleanup() {
    log_warning "清理 Docker 资源..."
    docker system prune -af --volumes
    log_success "清理完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local services=("face-service" "video-service" "audio-service" "monitor-service")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        local status=$(docker inspect -f '{{.State.Health.Status}}' "$service" 2>/dev/null || echo "not_found")
        if [ "$status" == "healthy" ]; then
            log_success "$service: healthy"
        else
            log_error "$service: $status"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" == true ]; then
        log_success "所有服务健康检查通过"
        return 0
    else
        log_error "部分服务健康检查失败"
        return 1
    fi
}

# 主函数
main() {
    local command=${1:-help}
    
    echo "=========================================="
    echo "  AR Backend 部署工具 v1.0"
    echo "=========================================="
    
    case $command in
        develop|development)
            check_docker
            load_env
            create_directories
            build_images
            start_services
            health_check
            ;;
        production|prod)
            check_docker
            load_env
            create_directories
            build_images
            start_services
            health_check
            ;;
        gpu)
            check_docker
            load_env
            create_directories
            build_images
            start_services "gpu"
            health_check
            ;;
        status)
            status
            ;;
        logs)
            logs "$2"
            ;;
        stop)
            stop
            ;;
        restart)
            stop
            sleep 3
            start_services
            health_check
            ;;
        cleanup)
            stop
            cleanup
            ;;
        health|check)
            health_check
            ;;
        help|*)
            echo "用法: $0 <command> [options]"
            echo ""
            echo "可用命令:"
            echo "  develop     - 启动开发环境"
            echo "  production - 启动生产环境"
            echo "  gpu         - 启动 GPU 环境"
            echo "  status      - 查看服务状态"
            echo "  logs        - 查看日志"
            echo "  stop        - 停止服务"
            echo "  restart     - 重启服务"
            echo "  cleanup     - 清理资源"
            echo "  health      - 健康检查"
            echo "  help        - 显示帮助"
            ;;
    esac
}

main "$@"
'''

if __name__ == "__main__":
    print(__doc__)

