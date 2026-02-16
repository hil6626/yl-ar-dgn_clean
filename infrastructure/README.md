# YL-AR-DGN 基础设施文档

**版本:** 1.0.0  
**更新日期:** 2026-02-04  
**状态:** 🔄 进行中

---

## 📋 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [组件配置](#组件配置)
4. [监控配置](#监控配置)
5. [部署指南](#部署指南)
6. [验证步骤](#验证步骤)
7. [故障排除](#故障排除)
8. [维护指南](#维护指南)

---

## 概述

本文档描述了YL-AR-DGN项目的基础设施架构，包括网络配置、存储配置、监控配置和部署流程。

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户访问层                            │
│         (Web浏览器 / 移动设备 / API客户端)               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     反向代理层                           │
│                  (Nginx / Traefik)                      │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Web服务    │    │   API服务    │    │  监控服务    │
│   (可选)     │    │ AR-backend   │    │ YL-monitor  │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PostgreSQL │    │    Redis    │    │ Prometheus  │
│   数据库     │    │   缓存      │    │   监控      │
└─────────────┘    └─────────────┘    └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Grafana    │
                                        │   仪表板    │
                                        └─────────────┘
```

### 核心组件

| 组件 | 版本 | 用途 | 端口 |
|------|------|------|------|
| PostgreSQL | 14 | 主数据库 | 5432 |
| Redis | 7 | 缓存和会话 | 6379 |
| Prometheus | v2.40.0 | 指标收集 | 9090 |
| Grafana | 9.4.0 | 可视化仪表板 | 3000 |
| Alertmanager | v0.25.0 | 报警管理 | 9093 |
| Node Exporter | v1.5.0 | 系统指标 | 9100 |
| Postgres Exporter | v0.11.1 | 数据库指标 | 9187 |
| Redis Exporter | v1.45.0 | 缓存指标 | 9121 |

---

## 架构设计

### 网络架构

#### Docker网络

```yaml
# 网络配置
networks:
  backend_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
  
  monitoring_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.21.0.0/16
```

#### 网络拓扑

```
                    ┌─────────────────────┐
                    │   外部网络          │
                    │   (互联网)          │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │     防火墙/路由       │
                    │    (UFW/iptables)    │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │  Web    │          │   API   │          │  监控   │
   │  80/443 │          │  8080   │          │  3000   │
   └─────────┘          └─────────┘          └─────────┘
```

### 存储架构

#### 数据目录

```
infrastructure/
├── backups/              # 数据库备份
│   ├── daily/           # 日备份
│   ├── weekly/          # 周备份
│   └── monthly/         # 月备份
├── configs/             # 配置文件
├── data/                # 应用数据
├── logs/                # 日志文件
├── prometheus/          # Prometheus配置
│   └── rules/          # 告警规则
├── grafana/            # Grafana配置
│   └── dashboards/     # 仪表板
└── recovery.sh         # 恢复脚本
```

#### 存储卷

```yaml
volumes:
  postgres_data:    # PostgreSQL数据
  redis_data:       # Redis数据
  prometheus_data: # Prometheus数据
  grafana_data:    # Grafana数据
```

---

## 组件配置

### PostgreSQL配置

```yaml
postgres:
  image: postgres:14
  environment:
    POSTGRES_DB: ar_dgn
    POSTGRES_USER: admin
    POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./infrastructure/backups:/backups
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U admin"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Redis配置

```yaml
redis:
  image: redis:7
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

### Prometheus配置

```yaml
prometheus:
  image: prom/prometheus:v2.40.0
  volumes:
    - ./infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml
    - ./infrastructure/prometheus/rules:/etc/prometheus/rules
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=200h'
```

### Grafana配置

```yaml
grafana:
  image: grafana/grafana:9.4.0
  volumes:
    - grafana_data:/var/lib/grafana
    - ./infrastructure/grafana/provisioning:/etc/grafana/provisioning
    - ./infrastructure/grafana/dashboards:/var/lib/grafana/dashboards
  environment:
    - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
```

---

## 监控配置

### 告警规则

#### CPU使用率告警

```yaml
- alert: HighCPUUsage
  expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "CPU使用率过高"
    description: "实例 {{ $labels.instance }} CPU使用率超过80%: {{ $value }}%"
```

#### 内存使用率告警

```yaml
- alert: HighMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "内存使用率过高"
    description: "实例 {{ $labels.instance }} 内存使用率超过85%: {{ $value }}%"
```

#### 磁盘使用率告警

```yaml
- alert: HighDiskUsage
  expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 90
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "磁盘使用率过高"
    description: "实例 {{ $labels.instance }} 磁盘使用率超过90%: {{ $value }}%"
```

### 报警通知配置

```yaml
route:
  group_by: ['alertname', 'severity']
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'critical-alerts'
    webhook_configs:
      - url: 'http://0.0.0.0:5001/alerts/critical'
      - url: 'https://hooks.slack.com/services/xxx/yyy/zzz'
```

---

## 部署指南

### 前置条件

1. Docker Engine 20.10+
2. Docker Compose 2.0+
3. 至少2GB可用内存
4. 至少20GB可用磁盘空间

### 部署步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd yl-ar-dgn
```

#### 2. 配置环境变量

```bash
# 创建环境变量文件
cp .env.example .env

# 编辑环境变量
vim .env
```

```bash
# 环境变量示例
DB_PASSWORD=your_secure_password
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_secure_password
TZ=Asia/Shanghai
```

#### 3. 部署基础设施

```bash
# 方法1: 使用恢复脚本
./infrastructure/recovery.sh

# 方法2: 手动启动
docker-compose up -d
```

#### 4. 验证部署

```bash
# 运行验证脚本
./scripts/verify_infrastructure.sh

# 验证服务状态
docker-compose ps

# 检查健康状态
curl http://0.0.0.0:9090/api/v1/query?query=up
```

### 访问地址

| 服务 | 地址 | 凭据 |
|------|------|------|
| Grafana | http://0.0.0.0:3000 | admin/admin |
| Prometheus | http://0.0.0.0:9090 | 无需认证 |
| Alertmanager | http://0.0.0.0:9093 | 无需认证 |

---

## 验证步骤

### 1. Docker环境验证

```bash
# 检查Docker状态
docker info

# 检查Docker Compose版本
docker-compose --version
```

### 2. 服务状态验证

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### 3. 健康检查验证

```bash
# PostgreSQL
docker-compose exec -T postgres pg_isready -U admin

# Redis
docker-compose exec -T redis redis-cli ping

# Prometheus
curl http://0.0.0.0:9090/api/v1/query?query=up

# Grafana
curl http://0.0.0.0:3000/api/health
```

### 4. 监控数据验证

```bash
# 检查Prometheus目标
curl http://0.0.0.0:9090/api/v1/targets

# 检查告警规则
curl http://0.0.0.0:9090/api/v1/rules

# 检查Grafana数据源
curl -u admin:admin http://0.0.0.0:3000/api/datasources
```

---

## 故障排除

### 常见问题

#### 1. 服务启动失败

**症状:** 容器状态为"Exit"或"Restarting"

**解决方案:**
```bash
# 查看错误日志
docker-compose logs <service-name>

# 检查容器状态
docker-compose ps

# 重新启动服务
docker-compose restart <service-name>
```

#### 2. 端口冲突

**症状:** 启动时提示端口已被占用

**解决方案:**
```bash
# 查看端口占用
netstat -tlnp | grep <port>

# 修改docker-compose.yml中的端口映射
```

#### 3. 数据库连接失败

**症状:** 应用无法连接到数据库

**解决方案:**
```bash
# 检查数据库状态
docker-compose exec -T postgres pg_isready -U admin

# 检查连接字符串
docker-compose exec -T postgres psql -U admin -d ar_dgn -c "SELECT 1"

# 检查网络连接
docker network inspect yl-ar-dgn_backend_network
```

#### 4. 监控数据缺失

**症状:** Grafana仪表板无数据

**解决方案:**
```bash
# 检查Prometheus目标状态
curl http://0.0.0.0:9090/api/v1/targets

# 检查exporter状态
curl http://0.0.0.0:9100/metrics
curl http://0.0.0.0:9187/metrics
```

### 回滚步骤

```bash
# 停止所有服务
docker-compose down

# 恢复到上一个版本
git checkout <previous-commit>

# 重新部署
docker-compose up -d
```

---

## 维护指南

### 日常维护

#### 1. 日志管理

```bash
# 查看服务日志
docker-compose logs -f --tail=100

# 清理日志文件
find logs/ -name "*.log" -mtime +7 -delete
```

#### 2. 磁盘空间管理

```bash
# 检查磁盘使用
df -h

# 检查Docker磁盘使用
docker system df

# 清理Docker资源
docker system prune -af
docker volume prune -f
```

#### 3. 数据库备份

```bash
# 手动备份
docker-compose exec -T postgres pg_dump -U admin ar_dgn > backup.sql

# 清理旧备份
find infrastructure/backups/ -name "*.sql" -mtime +30 -delete
```

### 定期任务

#### 每日任务

- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 确认备份完成

#### 每周任务

- [ ] 磁盘空间检查
- [ ] 性能指标审查
- [ ] 告警规则优化

#### 每月任务

- [ ] 安全更新检查
- [ ] 配置优化
- [ ] 容量规划

---

## 附录

### 配置文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| docker-compose.yml | ./docker-compose.yml | 主编排文件 |
| config.yaml | infrastructure/config.yaml | 主配置 |
| prometheus.yml | infrastructure/prometheus.yml | Prometheus配置 |
| alertmanager.yml | infrastructure/alertmanager.yml | Alertmanager配置 |
| infrastructure_alerts.yml | infrastructure/prometheus/rules/ | 告警规则 |

### 端口清单

| 端口 | 服务 | 协议 |
|------|------|------|
| 5432 | PostgreSQL | TCP |
| 6379 | Redis | TCP |
| 9090 | Prometheus | TCP |
| 3000 | Grafana | TCP |
| 9093 | Alertmanager | TCP |
| 9100 | Node Exporter | TCP |
| 9187 | Postgres Exporter | TCP |
| 9121 | Redis Exporter | TCP |

### 相关文档

- [部署总结](../../docs/DEPLOYMENT_SUMMARY.md)
- [执行规则](../../docs/EXECUTION_RULES.md)
- [任务跟踪](TODO.md)

---

**文档版本:** 1.0.0  
**最后更新:** 2026-02-04  
**维护者:** AI 编程代理  
**审核状态:** 待审核

