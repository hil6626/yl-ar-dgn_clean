# YL-Monitor 启动文档

## 1. 项目概述

YL-Monitor 是一个基于 FastAPI + Jinja2 + WebSocket 的浏览器监控与控制平台，提供系统健康监控、Python 自动化脚本管理、DAG 流水线编排、AR 合成项目监控等功能。

## 2. 环境要求

- Python 3.9 或更高版本
- 至少 512MB 内存
- 至少 100MB 可用磁盘空间
- 支持的操作系统：Linux/macOS/Windows

## 3. 安装依赖项

### 3.1 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
# .\venv\Scripts\activate
```

### 3.2 安装Python依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

## 4. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件（可选，使用默认值也可以）
# vim .env
```

主要环境变量：
- `YL_MONITOR_PORT`: 服务端口，默认 5500
- `YL_MONITOR_HOST`: 监听地址，默认 0.0.0.0
- `YL_MONITOR_LOG_LEVEL`: 日志级别，默认 info
- `DATABASE_URL`: 数据库连接URL，默认 sqlite:///data/monitor.db

## 5. 启动前后端

### 5.1 开发模式启动

```bash
# 启动应用（开发模式，带热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 5500
```

### 5.2 生产模式启动

```bash
# 启动应用（生产模式，无热重载）
uvicorn app.main:app --host 0.0.0.0 --port 5500 --workers 4
```

### 5.3 使用启动脚本

项目提供了便捷的启动脚本：

```bash
# 简单启动（使用系统Python环境）
./scripts/start_app_simple.sh

# 完整部署启动
./scripts/deploy.sh start

# Docker 启动
./scripts/docker_start.sh
```

## 6. 访问应用

启动成功后，可以通过以下地址访问应用：

- **平台入口（SPA）**: http://localhost:5500
- **仪表盘（独立页）**: http://localhost:5500/dashboard
- **API 文档**: http://localhost:5500/api-doc
- **OpenAPI 规范**: http://localhost:5500/openapi.json

## 7. Docker 部署

### 7.1 使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 7.2 手动 Docker 部署

```bash
# 构建镜像
docker build -t yl-monitor:latest .

# 运行容器
docker run -d \
  -p 5500:5500 \
  -v logs:/app/logs \
  --name yl-monitor \
  --restart unless-stopped \
  yl-monitor:latest
```

## 8. Systemd 部署（生产环境推荐）

### 8.1 部署到系统目录

```bash
# 以 root 身份操作
sudo bash

# 创建应用用户
useradd -m -s /bin/bash -d /opt/yl-monitor yl-monitor

# 克隆项目到 /opt
cd /opt
git clone <repository> yl-monitor
cd yl-monitor

# 创建虚拟环境
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 调整权限
chown -R yl-monitor:yl-monitor /opt/yl-monitor
chmod -R 755 /opt/yl-monitor
chmod -R 700 /opt/yl-monitor/logs

# 创建 .env 文件
cp .env.example /opt/yl-monitor/.env
chown yl-monitor:yl-monitor /opt/yl-monitor/.env
chmod 600 /opt/yl-monitor/.env
```

### 8.2 安装 Systemd 服务

```bash
# 复制服务文件
sudo cp systemd/yl-monitor.service /etc/systemd/system/

# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable yl-monitor

# 启动服务
sudo systemctl start yl-monitor

# 查看状态
sudo systemctl status yl-monitor
```

## 9. 热监控

项目支持实时监控功能，通过 WebSocket 实现：

- 系统资源实时监控（CPU、内存、磁盘、网络）
- 脚本执行进度实时推送
- DAG 节点状态变化实时推送
- AR 节点资源实时推送

前端会自动连接 WebSocket 服务，实时接收和显示监控数据。

## 10. 常见问题

### 10.1 端口被占用

```bash
# 检查端口占用
lsof -i :5500

# 杀死占用进程
kill -9 <PID>
```

### 10.2 依赖安装失败

```bash
# 清理缓存重新安装
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### 10.3 数据库连接失败

```bash
# 检查数据库文件权限
ls -la data/monitor.db

# 重新初始化数据库
python3 migrations/001_create_function_mappings.py
python3 migrations/002_create_scripts_table.py
```

## 11. 停止服务

### 11.1 开发模式停止

按 `Ctrl+C` 停止服务。

### 11.2 生产模式停止

```bash
# 停止 Systemd 服务
sudo systemctl stop yl-monitor

# 停止 Docker 容器
docker stop yl-monitor
```

## 12. 验证部署

```bash
# 检查健康状态
curl http://localhost:5500/api/health

# 检查系统状态
curl http://localhost:5500/api/summary

# 查看 API 文档
curl http://localhost:5500/docs
```

