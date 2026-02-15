# 任务009：AR Backend 长期优化 - Docker化与部署完善

**任务ID:** ar-backend-009-long-term  
**任务名称:** AR Backend 长期优化 - Docker化与部署完善  
**优先级:** 中  
**计划周期:** 3个月内  
**负责人:** AI 编程代理

---

## 一、任务背景

### 1.1 问题描述

当前部署方式存在以下问题：

| 问题 | 影响 | 现状 |
|------|------|------|
| 手动部署 | 部署复杂，易出错 | 无Docker化 |
| 环境依赖 | 依赖管理困难 | pip requirements |
| 外部项目 | 集成复杂 | 直接在代码库中 |
| 监控不足 | 问题发现滞后 | 基础监控 |

### 1.2 优化目标

```
┌─────────────────────────────────────────────────────────┐
│                   AR Backend 目标架构                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Nginx     │  │   Docker    │  │  Prometheus │   │
│  │  反向代理    │  │  容器化部署   │  │   监控      │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│         │                │                │             │
│  ┌──────┴──────┐ ┌─────┴─────┐ ┌──────┴──────┐      │
│  │  AR Backend │ │  YL-Monitor│ │  Grafana    │      │
│  │   Service   │ │  Service   │ │  Dashboard  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
│         │                │                │             │
│  ┌──────┴─────────┐ ┌───┴────────┐ ┌────┴─────┐       │
│  │  Docker Compose │ │   Logs     │ │  Alerts  │       │
│  │  统一编排       │ │  (ELK)     │ │(Alertmanager)│    │
│  └────────────────┘ └────────────┘ └───────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## 二、任务目标

### 2.1 具体目标

| # | 目标 | 状态 | 预估时间 |
|---|------|------|----------|
| 1 | Docker化部署 | ⏳ 待执行 | 4小时 |
| 2 | Docker Compose编排 | ⏳ 待执行 | 2小时 |
| 3 | 外部依赖Docker化 | ⏳ 待执行 | 4小时 |
| 4 | 监控体系完善 | ⏳ 待执行 | 4小时 |
| 5 | CI/CD集成 | ⏳ 待执行 | 4小时 |
| 6 | 文档更新 | ⏳ 待执行 | 2小时 |

### 2.2 验收标准

- [ ] Docker镜像构建成功
- [ ] Docker Compose一键部署
- [ ] 外部服务Docker化
- [ ] 监控告警可用
- [ ] CI/CD流水线完整

---

## 三、执行计划

### 3.1 阶段1: Docker化部署

#### 3.1.1 优化Dockerfile

```dockerfile
# AR-backend/Dockerfile (优化版)

# ============ 基础镜像 ============
FROM python:3.10-slim AS builder

# ============ 构建依赖 ============
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ============ 安装Python依赖 ============
WORKDIR /build

# 复制依赖文件
COPY requirements/requirements.txt .

# 安装依赖（使用国内镜像）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============ 生产镜像 ============
FROM python:3.10-slim AS production

# ============ 安装运行时依赖 ============
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxkbcommon0 \
    libasound2 \
    libpulse0 \
   .sox \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ============ 创建用户 ============
RUN groupadd -r appuser && useradd -r -g appuser appuser

# ============ 复制依赖 ============
COPY --from=builder /install /usr/local

# ============ 设置工作目录 ============
WORKDIR /app

# ============ 复制应用代码 ============
COPY --chown=appuser:appuser . .

# ============ 创建必要目录 ============
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R appuser:appuser /app

# ============ 切换用户 ============
USER appuser

# ============ 环境变量 ============
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AR_LOG_LEVEL=INFO

# ============ 健康检查 ============
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# ============ 端口暴露 ============
EXPOSE 8000

# ============ 启动命令 ============
CMD ["python", "app/launcher.py"]
```

#### 3.1.2 构建脚本

```bash
#!/bin/bash
# AR-backend/build_docker.sh

set -e

IMAGE_NAME="yl-ar-dgn/ar-backend"
VERSION=$(cat VERSION 2>/dev/null || echo "latest")
CONTAINER_NAME="ar-backend"

echo "========================================"
echo "  构建 AR Backend Docker 镜像"
echo "========================================"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

# 构建镜像
echo "构建镜像: ${IMAGE_NAME}:${VERSION}"
docker build \
    --tag "${IMAGE_NAME}:${VERSION}" \
    --tag "${IMAGE_NAME}:latest" \
    .

# 打印镜像信息
echo ""
echo "镜像构建成功:"
docker images "${IMAGE_NAME}"

echo ""
echo "✅ 可用命令:"
echo "  运行: docker run -d -p 8000:8000 --name ${CONTAINER_NAME} ${IMAGE_NAME}:${VERSION}"
echo "  停止: docker stop ${CONTAINER_NAME}"
echo "  查看日志: docker logs -f ${CONTAINER_NAME}"
```

### 3.2 阶段2: Docker Compose编排

#### 3.2.1 Docker Compose配置

```yaml
# AR-backend/docker-compose.yml

version: '3.8'

services:
  # AR Backend 主服务
  ar-backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ar-backend
    ports:
      - "8000:8000"
    environment:
      - AR_ENV=production
      - AR_LOG_LEVEL=INFO
      - AR_MONITOR_PORT=8000
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - ar-network
    depends_on:
      - redis

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: ar-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - ar-network

  # 监控服务
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: ar-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    restart: unless-stopped
    networks:
      - ar-network
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'

  # Grafana
  grafana:
    image: grafana/grafana:10.0.0
    container_name: ar-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./infrastructure/grafana/provisioning:/etc/grafana/provisioning:ro
    restart: unless-stopped
    networks:
      - ar-network
    depends_on:
      - prometheus

  # 日志收集
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
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    restart: unless-stopped
    networks:
      - ar-network
    depends_on:
      - elasticsearch

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: ar-elasticsearch
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    restart: unless-stopped
    networks:
      - ar-network

networks:
  ar-network:
    driver: bridge

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
  elasticsearch-data:
```

#### 3.2.2 Docker Compose脚本

```bash
#!/bin/bash
# AR-backend/manage_docker.sh

COMPOSE_FILE="docker-compose.yml"
ACTION=${1:-"up"}

case "$ACTION" in
    up)
        echo "启动所有服务..."
        docker compose -f "$COMPOSE_FILE" up -d
        echo "✅ 服务已启动"
        echo ""
        echo "服务状态:"
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    down)
        echo "停止所有服务..."
        docker compose -f "$COMPOSE_FILE" down
        echo "✅ 服务已停止"
        ;;
    restart)
        echo "重启所有服务..."
        docker compose -f "$COMPOSE_FILE" restart
        echo "✅ 服务已重启"
        ;;
    logs)
        echo "查看日志..."
        docker compose -f "$COMPOSE_FILE" logs -f
        ;;
    build)
        echo "构建镜像..."
        docker compose -f "$COMPOSE_FILE" build --no-cache
        echo "✅ 镜像构建完成"
        ;;
    status)
        echo "查看服务状态..."
        docker compose -f "$COMPOSE_FILE" ps
        echo ""
        echo "资源使用:"
        docker stats --no-stream $(docker compose -f "$COMPOSE_FILE" ps -q)
        ;;
    *)
        echo "用法: $0 {up|down|restart|logs|build|status}"
        exit 1
        ;;
esac
```

### 3.3 阶段3: 外部依赖Docker化

#### 3.3.1 OBS Studio Docker

```dockerfile
# integrations/obs-studio/Dockerfile
FROM ubuntu:22.04

# 安装OBS Studio
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    ca-certificates \
    && wget -O- https://obsproject.com/obs_signing_key.pub | gpg --dearmor > /usr/share/keyrings/obsproject.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/obsproject.gpg] https://obsproject.com/repo/ubuntu/$(lsb_release -sc) stable" > /etc/apt/sources.list.d/obsproject.list \
    && apt-get update \
    && apt-get install -y obs-studio \
    && rm -rf /var/lib/apt/lists/*

# 安装虚拟摄像头插件
RUN apt-get install -y --no-install-recommends \
    v4l2loopback-dkms \
    v4l2loopback-utils

# 创建虚拟摄像头设备节点
RUN mknod /dev/video0 c 81 0 || true

EXPOSE 5900

CMD ["obs", "--startvirtualcam", "--portable"]
```

#### 3.3.2 DeepFaceLab Docker

```dockerfile
# integrations/DeepFaceLab/Dockerfile
FROM nvidia/cuda:11.8-devel-ubuntu22.04

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements-cuda.txt .
RUN pip install --no-cache-dir -r requirements-cuda.txt

# 克隆DeepFaceLab
RUN git clone https://github.com/iperov/DeepFaceLab.git /app
WORKDIR /app

# 创建模型目录
RUN mkdir -p /data/models

# 设置工作目录
WORKDIR /data

CMD ["python3", "/app/main.py"]
```

### 3.4 阶段4: 监控体系完善

#### 3.4.1 Prometheus配置

```yaml
# infrastructure/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  - job_name: 'ar-backend'
    static_configs:
      - targets: ['ar-backend:8000']
    metrics_path: /metrics

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    metrics_path: /metrics

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
```

#### 3.4.2 告警规则

```yaml
# infrastructure/prometheus/rules/ar-backend.yml

groups:
  - name: ar-backend-alerts
    rules:
      - alert: ARBackendDown
        expr: up{job="ar-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AR Backend 服务不可用"
          description: "AR Backend服务已停止超过1分钟"

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率超过80%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过85%"

      - alert: HighDiskUsage
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "磁盘空间不足"
          description: "磁盘使用率超过90%"
```

### 3.5 阶段5: CI/CD集成

#### 3.5.1 GitHub Actions Workflow

```yaml
# .github/workflows/ar-backend.yml

name: AR Backend CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'AR-backend/**'
  pull_request:
    branches: [main]
    paths:
      - 'AR-backend/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./AR-backend
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ${{ secrets.DOCKER_REGISTRY }}/yl-ar-dgn/ar-backend:${{ github.sha }}
            ${{ secrets.DOCKER_REGISTRY }}/yl-ar-dgn/ar-backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r AR-backend/requirements/requirements.txt

      - name: Run tests
        run: |
          cd AR-backend
          python -m pytest test/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  deploy:
    needs: [build, test]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/ar-backend
            docker compose pull
            docker compose up -d
            docker image prune -f
```

---

## 四、时间线

### 4.1 执行时间

| 阶段 | 任务 | 时间 |
|------|------|------|
| 0h | Docker化部署 | 4小时 |
| 4h | Docker Compose | 2小时 |
| 6h | 外部依赖Docker化 | 4小时 |
| 10h | 监控体系完善 | 4小时 |
| 14h | CI/CD集成 | 4小时 |
| 18h | 文档更新 | 2小时 |
| **总计** | | **20小时** |

### 4.2 检查点

| 时间 | 检查项 | 负责人 |
|------|--------|--------|
| T+4h | Docker镜像构建 | AI |
| T+6h | Docker Compose可用 | AI |
| T+10h | 外部服务Docker化 | AI |
| T+14h | 监控告警可用 | AI |
| T+18h | CI/CD流水线完整 | AI |
| T+20h | 文档更新完成 | AI |

---

## 五、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Docker构建失败 | 无法部署 | 多阶段构建优化 |
| 外部项目Docker化复杂 | 进度延迟 | 使用现有Docker镜像 |
| 监控数据量大 | 存储压力 | 数据保留策略 |
| CI/CD配置错误 | 自动部署失败 | 测试环境验证 |

---

## 六、验证标准

### 6.1 Docker验证

```bash
# 构建测试
cd /workspaces/yl-ar-dgn/AR-backend
docker build -t ar-backend:test .

# 运行测试
docker run -d -p 8000:8000 --name ar-backend-test ar-backend:test

# 健康检查
curl http://localhost:8000/health

# 停止测试
docker stop ar-backend-test && docker rm ar-backend-test
```

**通过标准:**
- [ ] Docker镜像构建成功
- [ ] 容器可正常启动
- [ ] 健康检查通过

### 6.2 Docker Compose验证

```bash
# 启动所有服务
./manage_docker.sh up

# 检查状态
./manage_docker.sh status

# 查看日志
./manage_docker.sh logs

# 停止服务
./manage_docker.sh down
```

**通过标准:**
- [ ] 所有服务启动成功
- [ ] 服务间通信正常
- [ ] 数据持久化正常

### 6.3 CI/CD验证

```bash
# 触发GitHub Actions
git add .
git commit -m "test: trigger CI/CD"
git push

# 检查Actions状态
gh run list --workflow ar-backend.yml
```

**通过标准:**
- [ ] CI流水线通过
- [ ] CD部署成功

---

## 七、输出产物

### 7.1 Docker文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `AR-backend/Dockerfile` | 主服务Dockerfile | 待创建 |
| `AR-backend/docker-compose.yml` | 编排配置 | 待创建 |
| `AR-backend/manage_docker.sh` | 管理脚本 | 待创建 |
| `AR-backend/build_docker.sh` | 构建脚本 | 待创建 |
| `integrations/obs-studio/Dockerfile` | OBS Docker | 待创建 |
| `integrations/DeepFaceLab/Dockerfile` | DFL Docker | 待创建 |

### 7.2 监控配置

| 文件 | 描述 | 状态 |
|------|------|------|
| `infrastructure/prometheus.yml` | Prometheus配置 | 待创建 |
| `infrastructure/prometheus/rules/*.yml` | 告警规则 | 待创建 |
| `infrastructure/grafana/provisioning/*` | Grafana配置 | 待创建 |

### 7.3 CI/CD配置

| 文件 | 描述 | 状态 |
|------|------|------|
| `.github/workflows/ar-backend.yml` | GitHub Actions | 待创建 |

### 7.4 文档

| 文件 | 描述 | 状态 |
|------|------|------|
| `docs/tasks/task-009-execution-report.md` | 执行报告 | 待创建 |

---

## 八、依赖与前置任务

| 任务ID | 依赖内容 | 状态 |
|--------|----------|------|
| task-008 | 中期优化完成 | ⏳ 待执行 |

---

## 九、相关文档

| 文档 | 描述 |
|------|------|
| [短期优化任务007](task-007-ar-backend-short-term-optimization.md) | 短期优化 |
| [中期优化任务008](task-008-ar-backend-mid-term-optimization.md) | 中期优化 |
| [AR Backend分析报告](../task-006-ar-backend-analysis.md) | 完整分析 |

---

**文档版本:** 1.0.0  
**创建时间:** 2026-02-04  
**计划完成时间:** 2026-05-04

