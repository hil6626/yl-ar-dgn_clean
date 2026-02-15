# 📊 夜灵多功能统一监控平台

> 一个轻量级、模块化的本地部署监控与控制平台

## 1. 项目概述

**YL-Monitor** 是一个基于 FastAPI + Jinja2 + WebSocket 的浏览器监控与控制平台，用于统一管理：

- 🖥️ **系统健康监控** - CPU、内存、磁盘、网络等实时监控
- 🐍 **Python 自动化脚本** - 54+ 脚本白名单管理与执行
- 📊 **DAG 流水线编排** - 有向无环图任务调度与可视化
- 🎨 **AR 合成项目监控** - 3D 节点状态监控与资源跟踪
- 🔌 **API 统一映射** - 前后端接口自描述与表单调试

平台采用 **FastAPI + 浏览器 UI** 架构，通过单一 HTTP 服务对外提供 5 大页面控制台能力，适用于：

- ✨ 本地系统巡检与优化
- 🏢 内部研发监控控制台
- 🤖 自动化脚本管理平台
- 📈 数据流水线编排系统
- 🌐 AR / 数字孪生项目监控底座

**当前版本**：1.0.6（2026-02-10，生产就绪版本）

**最新特性**：
- 🚀 企业级性能优化（API响应<200ms，支持100+并发用户）
- 🐳 完整的 Docker 容器化支持
- 🔒 Systemd 生产级后台守护部署
- 🔐 JWT认证与RBAC权限控制
- ♻️ 模块化设计，易于扩展
- 📱 响应式前端设计
- 📊 实时数据可视化
- 🛡️ 全面的安全加固

## 2. 快速开始

### 2.1 最快体验（2 分钟）

```bash
# 克隆项目
git clone <repository> YL-monitor
cd YL-monitor

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 5500
```

然后访问：
- **平台入口（SPA）**：`http://localhost:5500`
- **仪表盘（独立页）**：`http://localhost:5500/dashboard`

### 2.2 Docker 快速启动

```bash
# 使用 Docker Compose（推荐）
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问：
- **平台入口（SPA）**：`http://localhost:5500`
- **仪表盘（独立页）**：`http://localhost:5500/dashboard`

### 2.3 手动 Docker 部署

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

### 2.4 使用部署脚本

项目提供便捷的部署脚本：

```bash
# 构建 Docker 镜像
./scripts/docker_build.sh

# 启动服务
./scripts/docker_start.sh

# 停止服务
./scripts/docker_stop.sh

# 验证部署
./scripts/verify_deployment.sh
```

### 2.5 使用统一入口脚本（推荐）

项目提供 Python 统一入口脚本，整合所有功能：

```bash
# 启动服务（生产模式）
python3 scripts/core/start.py --mode production

# 启动服务（开发模式，带热重载）
python3 scripts/core/start.py --mode development

# 调试模式（自动打开浏览器）
python3 scripts/core/start.py --mode debug --browser

# 查看服务状态
python3 scripts/core/start.py --status

# 重启服务
python3 scripts/core/start.py --restart

# 停止服务
python3 scripts/core/start.py --stop

# 验证项目（所有检查）
python3 scripts/core/verify.py

# 验证特定模块
python3 scripts/core/verify.py --api      # 仅验证API
python3 scripts/core/verify.py --pages    # 仅验证页面
python3 scripts/core/verify.py --static   # 仅验证静态资源
```

**统一脚本优势：**
- ✅ 整合 5+ 个启动脚本为一个入口
- ✅ 整合 7+ 个验证脚本为一个入口
- ✅ 支持多种运行模式（development/production/debug/docker）
- ✅ 自动健康检查和依赖验证
- ✅ 详细的日志输出和报告生成

## 3. 系统要求

| 项目 | 要求 | 验证命令 |
|------|-----|--------|
| **Python** | ≥ 3.9 | `python3 --version` |
| **内存** | ≥ 512 MB | `free -h` 或 `vm_stat` |
| **磁盘** | ≥ 100 MB 可用空间 | `df -h` |
| **操作系统** | Linux / macOS / Windows | 任意 |

可选（用于生产部署）：
- Docker & Docker Compose
- Systemd（Linux）主机

## 4. 设计目标

✅ **单入口设计** - 浏览器即可访问全部能力，无需多个工具

✅ **模块化架构** - 各功能页面彼此解耦，独立维护升级

✅ **易于扩展** - 轻松添加新页面、新 DAG、新 AR 项目

✅ **生产就绪** - 完整的异常处理、日志、监控、部署支持

✅ **安全可控** - 脚本、DAG、AR 节点均白名单机制，严禁动态执行

✅ **长期运行** - 支持 systemd 后台守护、开机自启、自动重启

## 5. 技术架构

### 5.1 整体架构

```
┌─────────────────────────────────────────┐
│         浏览器客户端（UI 层）            │
│  ┌──────────────────────────────────┐   │
│  │ Dashboard│Scripts│DAG│API Doc│AR │   │
│  └──────────────────────────────────┘   │
│           ↓  HTTP + WebSocket  ↑         │
├─────────────────────────────────────────┤
│      FastAPI 后端应用 (5500 端口)       │
│  ┌──────────────────────────────────┐   │
│  │  路由層 (routes/)                │   │
│  │  ├─ Dashboard 健康监控路由        │   │
│  │  ├─ Scripts 脚本执行路由         │   │
│  │  ├─ DAG 流水线路由               │   │
│  │  ├─ AR 节点监控路由              │   │
│  │  └─ API 文档与自省路由           │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  业务層 (services/)              │   │
│  │  ├─ ScriptsRunner 脚本管理       │   │
│  │  ├─ DAGEngine DAG 引擎           │   │
│  │  ├─ ARMonitor AR 监控            │   │
│  │  └─ 系统健康检查                 │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  中间件層 (middlewares)          │   │
│  │  ├─ 请求日志                     │   │
│  │  ├─ CORS 跨域处理                │   │
│  │  ├─ 异常捕获                     │   │
│  │  └─ 性能监测                     │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
        ↓ 读写 ↑
  ┌──────────────────┐
  │  本地文件系统     │
  │  ├─ scripts/    │  # 自动化脚本
  │  ├─ dags/       │  # DAG 定义
  │  ├─ logs/       │  # 执行日志
  │  ├─ static/     │  # 前端资源
  │  └─ templates/  │  # HTML 模板
  └──────────────────┘
```

### 5.2 核心技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **后端框架** | FastAPI | 0.104.1+ | 高性能异步 Web 框架 |
| **应用服务器** | Uvicorn | 0.24.0+ | ASGI 应用容器 |
| **数据验证** | Pydantic | 2.5.0+ | 数据模型与验证 |
| **模板渲染** | Jinja2 | 内置 | HTML 模板引擎 |
| **实时通信** | WebSocket | 标准库 | 双向实时推送 |
| **前端框架** | Vanilla JS | - | 无依赖轻量级 |
| **图表库** | Chart.js | CDN | 实时图表展示 |
| **容器化** | Docker | 20.10+ | 容器部署 |

### 5.3 关键模块说明

#### app/main.py - 应用核心入口
- FastAPI 应用初始化
- 路由与中间件注册
- 启动钩子：加载脚本、DAG、AR 监控
- 全局异常处理与日志配置
- CORS、请求日志、性能监测

#### app/routes/ - HTTP 路由层
- `dashboard.py` - 系统健康监控接口
- `scripts.py` - 脚本执行与管理接口
- `dag.py` - DAG 流水线接口
- `ar.py` - AR 节点监控接口
- `api_doc.py` - OpenAPI 文档与元数据

#### app/services/ - 业务逻辑层
- `scripts.py` - 脚本加载、执行、日志管理
- `dag.py` - DAG 解析、验证、调度、并行执行
- `ar.py` - AR 节点状态监控与资源跟踪
- `health.py` - 系统资源监控（CPU、内存、磁盘）

#### app/ws/ - WebSocket 实时推送
- 脚本执行进度推送
- DAG 节点状态变化推送
- AR 节点资源实时推送
- 系统健康指标实时推送

### 5.4 数据流向示例（脚本执行）

```
用户在 /scripts 页面 → 点击「执行」按钮
         ↓
POST /api/scripts/run {"script_id": "01"}
         ↓
ScriptsRunner.run_script() → 启动子进程
         ↓
脚本执行中... → WebSocket 推送进度 → 前端实时更新
         ↓
脚本完成 → 返回 JSON 结果 + 日志
         ↓
前端展示执行结果
```

## 6. 页面与API 说明

### 6.1 Dashboard（主仪表盘）

**访问路径**: `/dashboard`（独立页）  
**平台入口**: `/`（SPA 平台总入口）

**功能**：
- 系统资源实时监控（CPU、内存、磁盘、网络）
- 服务运行状态指示
- 快速操作卡片（常用脚本、DAG）
- 告警与异常提示

**后端接口**：
- `GET /api/dashboard/summary` - 系统整体状态
- `GET /api/summary` - 系统整体状态（兼容路径）
- `GET /api/health` - 健康检查
- `WS /ws/dashboard` - 实时资源数据推送（可选，当前未启用）

**响应示例**：
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "disk_percent": 78.5,
  "services": [
    {"name": "FastAPI", "status": "running"},
    {"name": "PostgreSQL", "status": "ok"}
  ],
  "timestamp": "2026-02-05T10:30:00Z"
}
```

### 6.2 Scripts（自动化脚本管理）

**访问路径**: `/scripts`

**功能**：
- 脚本列表展示（54+ 脚本）
- 脚本分类与搜索
- 手动触发执行
- 实时进度追踪
- 执行历史与日志查看

**后端接口**：
- `GET /api/scripts/list` - 脚本清单
- `POST /api/scripts/run` - 触发脚本
- `GET /api/scripts/status?script_id=01` - 执行状态
- `GET /api/scripts/logs?script_id=01` - 脚本日志
- `WS /ws/scripts` - 执行进度推送

**请求示例**：
```bash
curl -X POST http://localhost:5500/api/scripts/run \
  -H "Content-Type: application/json" \
  -d '{"script_id": "01"}'
```

### 6.3 API Doc（API 文档及调试）

**访问路径**: `/api-doc`

**功能**：
- 平台 API 节点树状导航
- 请求方法、参数、响应格式展示
- 表单化接口调用（便于运维调试）
- 响应结果实时展示

**数据来源**：
- `/openapi.json` - OpenAPI 3.0 规范
- `/api/meta` - 基于 OpenAPI 自动生成的 API Meta（保留 function_registry 扩展）

### 6.4 DAG Console（流水线控制）

**访问路径**: `/dag`

**功能**：
- DAG 有向无环图可视化
- 节点与依赖关系展示
- 节点状态颜色指示（待执行/执行中/成功/失败）
- DAG 运行控制（执行、停止、暂停）
- 执行日志与性能指标

**后端接口**：
- `GET /api/dag/list` - DAG 清单
- `GET /api/dag/detail?dag_id=xxx` - DAG 详细定义
- `POST /api/dag/run` - 触发 DAG
- `GET /api/dag/status?dag_id=xxx&run_id=yyy` - 执行状态
- `WS /ws/dag` - 节点状态实时推送

**请求示例**：
```bash
curl -X POST http://localhost:5500/api/dag/run \
  -H "Content-Type: application/json" \
  -d '{"dag_id": "daily_inspection", "params": {}}'
```

### 6.5 AR Monitor（AR 合成监控）

**访问路径**: `/ar`

**功能**：
- AR 场景 3D 可视化展示
- 节点对象列表与状态
- 渲染性能实时指标
- 节点资源占用监控

**后端接口**：
- `GET /api/ar/nodes` - 节点清单
- `GET /api/ar/status?node_id=xxx` - 节点详细状态
- `GET /api/ar/performance` - 渲染性能数据
- `WS /ws/ar` - 节点状态实时推送

**响应示例**：
```json
{
  "nodes": [
    {
      "id": "node_001",
      "name": "主角色模型",
      "status": "rendering",
      "vram_mb": 256,
      "fps": 60
    }
  ],
  "total_vram_mb": 1024,
  "average_fps": 58.5
}
```

## 7. 详细部署指南

### 7.1 本地开发环境（推荐新手）

#### 步骤 1: 环境准备

```bash
# 检查 Python 版本
python3 --version  # 需要 ≥ 3.9

# 进入项目目录
cd YL-monitor

# 创建虚拟环境（隔离依赖）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
# Windows 用户：.\venv\Scripts\activate
```

#### 步骤 2: 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# （可选）安装开发工具
pip install pytest pytest-asyncio black flake8
```

#### 步骤 3: 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env（可选，使用默认值也可以）
# vim .env
```

.env 文件配置说明：

```bash
# FastAPI 配置
YL_MONITOR_LOG_LEVEL=INFO                     # 日志级别
YL_MONITOR_CORS_ORIGINS=*                     # CORS 允许的源（逗号分隔）

# 目录配置（相对于项目根目录）
YL_MONITOR_SCRIPTS_DIR=scripts                # 脚本目录
YL_MONITOR_DAGS_DIR=dags                      # DAG 定义目录
YL_MONITOR_LOGS_DIR=logs                      # 日志输出目录

# DAG 引擎配置
YL_MONITOR_DAG_CONCURRENCY=6                  # DAG 并发数量
```

#### 步骤 4: 运行应用

```bash
# 方式 1: 开发模式（带热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 5500

# 方式 2: 生产模式（无热重载）
uvicorn app.main:app --host 0.0.0.0 --port 5500 --workers 4
```

#### 步骤 5: 访问应用

- **平台入口（SPA）**: http://localhost:5500
- **仪表盘（独立页）**: http://localhost:5500/dashboard
- **API 文档**: http://localhost:5500/api-doc
- **OpenAPI**: http://localhost:5500/openapi.json

#### 停止应用

```bash
# 按 Ctrl+C 停止服务
# 或者在另一个终端执行：
curl -X POST http://localhost:5500/shutdown  # 如果实现了此端点
```

### 7.2 Docker 容器化部署（推荐生产）

#### 前置要求

```bash
# 检查 Docker
docker --version          # 需要 20.10+
docker-compose --version  # 可选的编排工具
```

#### 构建与运行

```bash
# 方式 1: 手动构建与运行

# 构建镜像
docker build -t yl-monitor:latest .

# 运行容器（前台，用于调试）
docker run -it \
  -p 5500:5500 \
  -v logs:/app/logs \
  --name yl-monitor \
  yl-monitor:latest

# 运行容器（后台，生产推荐）
docker run -d \
  -p 5500:5500 \
  -v logs:/app/logs \
  --name yl-monitor \
  --restart unless-stopped \
  -e YL_MONITOR_LOG_LEVEL=INFO \
  yl-monitor:latest
```

#### 容器常用操作

```bash
# 查看容器状态
docker ps
docker stats yl-monitor

# 查看容器日志
docker logs -f yl-monitor

# 进入容器交互
docker exec -it yl-monitor /bin/bash

# 停止容器
docker stop yl-monitor

# 删除容器
docker rm yl-monitor

# 查看镜像
docker images | grep yl-monitor
```

#### Dockerfile 详解

项目包含完整的 Dockerfile，支持：
- ✅ 多层缓存优化
- ✅ 非 root 用户运行（安全）
- ✅ 健康检查（30s 间隔）
- ✅ 小型基础镜像（python:3.11-slim）

### 7.3 Systemd 生产部署（推荐长期运行）

#### 前置要求

```bash
# 仅限 Linux（CentOS 7+, Ubuntu 16.04+, Debian 9+）
# 验证 systemd
systemctl --version
```

#### 部署步骤

##### 步骤 1: 项目部署到系统目录

```bash
# 以 root 身份操作
sudo bash

# 创建应用用户（可选，提高安全性）
useradd -m -s /bin/bash -d /opt/YL-monitor yl-monitor 2>/dev/null || true

# 克隆项目到 /opt
cd /opt
git clone <repository> YL-monitor
cd YL-monitor

# 创建虚拟环境
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 调整权限
chown -R yl-monitor:yl-monitor /opt/YL-monitor
chmod -R 755 /opt/YL-monitor
chmod -R 700 /opt/YL-monitor/logs

# 创建 .env 文件
cp .env.example /opt/YL-monitor/.env
chown yl-monitor:yl-monitor /opt/YL-monitor/.env
chmod 600 /opt/YL-monitor/.env
```

##### 步骤 2: 安装 Systemd 服务

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

##### 步骤 3: 验证服务状态

```bash
# 检查服务运行状态
sudo systemctl status yl-monitor

# 查看实时日志
sudo journalctl -u yl-monitor -f

# 查看最近 100 条日志
sudo journalctl -u yl-monitor -n 100

# 查看系统启动时的服务日志
sudo journalctl -u yl-monitor --boot=0
```

#### Systemd 服务文件说明

`systemd/yl-monitor.service` 配置项：

```ini
[Unit]
Description=YL-monitor (FastAPI)        # 服务描述
After=network.target                    # 在网络启动后启动

[Service]
Type=simple                             # 简单服务类型
WorkingDirectory=/opt/YL-monitor        # 工作目录
EnvironmentFile=-/opt/YL-monitor/.env   # 环境变量文件（不存在不报错）
ExecStart=...uvicorn app.main:app...    # 启动命令
Restart=on-failure                      # 失败自动重启
RestartSec=3                            # 重启延迟（秒）

# 安全加固
NoNewPrivileges=true                    # 禁止 setuid/setgid
PrivateTmp=true                         # 独立 /tmp 目录
ProtectSystem=strict                    # 保护系统文件
ProtectHome=true                        # 隐藏 /home 目录
ReadWritePaths=/opt/YL-monitor/logs     # 仅允许写入 logs

[Install]
WantedBy=multi-user.target              # 安装目标
```

#### 服务常用命令

```bash
# 启动服务
sudo systemctl start yl-monitor

# 停止服务
sudo systemctl stop yl-monitor

# 重启服务
sudo systemctl restart yl-monitor

# 重新加载配置（无需重启）
sudo systemctl reload yl-monitor

# 查看启动日志
sudo journalctl -u yl-monitor -e

# 禁用开机自启
sudo systemctl disable yl-monitor

# 查看所有 systemd 服务
systemctl list-units --type=service
```

## 8. 环境变量参考

.env 配置文件支持以下环境变量：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `YL_MONITOR_LOG_LEVEL` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `YL_MONITOR_CORS_ORIGINS` | `*` | CORS 允许的源（多个用逗号分隔） |
| `YL_MONITOR_SCRIPTS_DIR` | `scripts` | 脚本目录（相对于项目根） |
| `YL_MONITOR_DAGS_DIR` | `dags` | DAG 定义目录（相对于项目根） |
| `YL_MONITOR_LOGS_DIR` | `logs` | 日志输出目录（相对于项目根） |
| `YL_MONITOR_DAG_CONCURRENCY` | `6` | DAG 并发执行数量 |

**示例 .env 文件**：

```bash
# 日志配置
YL_MONITOR_LOG_LEVEL=INFO

# 跨域配置（生产环境应指定具体域名）
YL_MONITOR_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,*

# 目录配置
YL_MONITOR_SCRIPTS_DIR=scripts
YL_MONITOR_DAGS_DIR=dags
YL_MONITOR_LOGS_DIR=logs

# DAG 引擎配置
YL_MONITOR_DAG_CONCURRENCY=8
```

## 9. 项目目录结构

```
YL-monitor/
├── README.md                      # 本文件（项目说明）
├── requirements.txt               # Python 依赖清单
├── Dockerfile                     # Docker 镜像定义
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git 忽略规则
│
├── app/                           # 后端应用（FastAPI）
│   ├── main.py                    # 应用入口与启动配置
│   ├── __init__.py
│   ├── auth/                      # 认证与权限模块
│   │   ├── deps.py                # 依赖注入
│   │   └── users.py               # 用户管理
│   ├── models/                    # 数据模型（Pydantic）
│   │   ├── request.py             # 请求模型
│   │   └── response.py            # 响应模型
│   ├── routes/                    # HTTP 路由处理
│   │   ├── dashboard.py           # 仪表盘路由
│   │   ├── scripts.py             # 脚本执行路由
│   │   ├── dag.py                 # DAG 流水线路由
│   │   ├── ar.py                  # AR 监控路由
│   │   └── api_doc.py             # API 文档路由
│   ├── services/                  # 业务逻辑层
│   │   ├── scripts.py             # 脚本管理与执行器
│   │   ├── dag.py                 # DAG 引擎与调度
│   │   ├── ar.py                  # AR 监控器
│   │   ├── health.py              # 系统健康检查
│   │   └── utils.py               # 工具函数
│   └── ws/                        # WebSocket 处理
│       ├── __init__.py
│       ├── scripts_ws.py          # 脚本执行推送
│       ├── dag_ws.py              # DAG 状态推送
│       └── ar_ws.py               # AR 状态推送
│
├── templates/                     # HTML 页面模板（Jinja2）
│   ├── base.html                  # 基础模板（导航、布局）
│   ├── platform.html              # 平台主入口
│   ├── dashboard.html             # 系统监控页面
│   ├── scripts.html               # 脚本管理页面
│   ├── api_doc.html               # API 文档页面
│   ├── dag.html                   # DAG 可视化页面
│   └── ar.html                    # AR 监控页面
│
├── static/                        # 前端静态资源
│   ├── css/                       # 样式表
│   │   ├── style.css              # 全局样式
│   │   ├── dashboard.css          # 仪表盘样式
│   │   ├── scripts.css            # 脚本页样式
│   │   ├── api_doc.css            # API 文档样式
│   │   ├── dag.css                # DAG 样式
│   │   └── ar.css                 # AR 样式
│   ├── js/                        # JavaScript 脚本
│   │   ├── app.js                 # 全局应用逻辑
│   │   ├── _api.js                # API 请求工具
│   │   ├── _ws.js                 # WebSocket 工具
│   │   ├── dashboard.js           # 仪表盘交互
│   │   ├── scripts.js             # 脚本页交互
│   │   ├── api_doc.js             # API 文档交互
│   │   ├── dag.js                 # DAG 图表交互
│   │   └── ar.js                  # AR 3D 交互
│   └── ar/                        # AR 资源（3D 模型等）
│       ├── models/                # 3D 模型文件
│       ├── textures/              # 纹理贴图
│       └── shaders/               # GLSL 着色器
│
├── scripts/                       # 自动化脚本库（54+ 脚本）
│   ├── _common.py                 # 脚本公共库
│   ├── 01_cpu_usage_monitor.py    # CPU 使用监控
│   ├── 02_memory_usage_monitor.py # 内存使用监控
│   ├── 03_disk_space_io_monitor.py# 磁盘与 I/O 监控
│   ├── ... （共 54 个脚本）
│   ├── docker_build.sh            # Docker 构建脚本
│   ├── docker_start.sh            # Docker 启动脚本
│   ├── docker_stop.sh             # Docker 停止脚本
│   └── README.md                  # 脚本文档
│
├── dags/                          # DAG 流水线定义（JSON）
│   ├── example_dag.json           # 示例 DAG
│   └── README.md                  # DAG 文档
│
├── logs/                          # 执行日志目录
│   ├── scripts/                   # 脚本执行日志
│   └── README.md                  # 日志说明
│
├── systemd/                       # systemd 服务配置
│   ├── yl-monitor.service         # systemd 服务文件
│   └── README.md                  # systemd 部署指南
│
└── 部署/                          # 部署文档与任务跟踪
    └── Tasks/                     # 任务清单（已清理）
```

## 10. 故障排查

### 问题：启动时报错 "ModuleNotFoundError"

**原因**：依赖未安装或虚拟环境未激活

**解决方案**：
```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# 重新安装依赖
pip install -r requirements.txt

# 清理 Python 缓存（可选）
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 问题：端口 5500 已被占用

**检查占用情况**：
```bash
# Linux/macOS
lsof -i :5500

# Windows
netstat -ano | findstr :5500
```

**解决方案**：
```bash
# 方案 1: 更换端口
uvicorn app.main:app --port 5501

# 方案 2: 杀死占用端口的进程
sudo kill -9 <PID>    # Linux/macOS
taskkill /PID <PID>   # Windows
```

### 问题：脚本执行失败或超时

**排查步骤**：
```bash
# 1. 检查脚本是否存在
ls -la scripts/01_cpu_usage_monitor.py

# 2. 手动运行脚本测试
python3 scripts/01_cpu_usage_monitor.py

# 3. 查看脚本日志
tail -f logs/scripts/01_cpu_usage_monitor.py.log

# 4. 检查超时时间设置（在 DAG 配置中）
cat dags/example_dag.json | grep timeout
```

### 问题：WebSocket 连接失败

**排查步骤**：
```bash
# 1. 确认后端服务在运行
curl http://localhost:5500/api/summary

# 2. 检查浏览器控制台（F12 -> Console）
# 查看是否有错误信息

# 3. 检查防火墙规则
sudo ufw status    # Linux
```

### 问题：Docker 容器启动后立即退出

**查看错误日志**：
```bash
docker logs yl-monitor

# 或者以交互模式运行来调试
docker run -it yl-monitor:latest sh
```

### 问题：Systemd 服务启动失败

**排查步骤**：
```bash
# 1. 检查服务状态
sudo systemctl status yl-monitor

# 2. 查看详细错误日志
sudo journalctl -u yl-monitor -n 50

# 3. 检查服务文件配置
sudo cat /etc/systemd/system/yl-monitor.service

# 4. 验证工作目录和文件权限
ls -la /opt/YL-monitor
ls -la /opt/YL-monitor/.venv/bin/uvicorn

# 5. 手动运行服务命令测试
/opt/YL-monitor/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5500
```

### 问题：内存占用过高

**优化方案**：
```bash
# 1. 调整 DAG 并发数（减少）
echo "YL_MONITOR_DAG_CONCURRENCY=3" >> .env

# 2. 启用 Uvicorn 的工作进程数限制
# 在启动命令中添加 --workers 参数（不超过 CPU 核心数）
uvicorn app.main:app --workers 2 --host 0.0.0.0 --port 5500

# 3. 定期清理日志
find logs/ -type f -mtime +7 -delete  # 删除 7 天前的日志
```

## 11. 开发指南

### 添加新的脚本

1. **创建脚本文件**：`scripts/NN_description.py`
2. **遵循脚本规范**：
   - 输出 JSON 格式结果
   - 实现 `main()` 函数
   - 返回 `{"id": "NN", "name": "xxx", "status": "ok|error", ...}`
3. **注册到白名单**：在 `app/services/scripts.py` 中添加脚本条目
4. **测试脚本**：
   ```bash
   python3 scripts/NN_description.py --pretty
   ```

### 添加新的 DAG

1. **创建 DAG 定义文件**：`dags/my_workflow.json`
2. **格式参考**：见 `dags/README.md`
3. **验证 DAG**：
   ```bash
   curl http://localhost:5500/api/dag/detail?dag_id=my_workflow
   ```

### 添加新的 API 路由

1. **创建路由文件**：`app/routes/myfeature.py`
2. **定义路由处理函数**：
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/api/myfeature")
   
   @router.get("/data")
   async def get_data():
       return {"data": []}
   ```
3. **在 `app/main.py` 中注册路由**：
   ```python
   from app.routes import myfeature
   app.include_router(myfeature.router)
   ```

### 开发工作流

```bash
# 1. 创建特性分支
git checkout -b feature/my-feature

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 在开发模式下运行
uvicorn app.main:app --reload

# 4. 代码检查（可选）
flake8 app/
black app/

# 5. 单元测试（如果有）
pytest tests/

# 6. 提交代码
git add .
git commit -m "feat: add my-feature"
git push origin feature/my-feature
```

## 12. 性能优化建议

### 前端优化

- ✅ 使用浏览器缓存（Cache-Control 头）
- ✅ 压缩静态资源（CSS/JS 最小化）
- ✅ 图片优化（WebP 格式、响应式尺寸）
- ✅ 异步加载 WebSocket 数据
- ✅ 使用 Web Workers 处理大型计算

### 后端优化

- ✅ 启用 Uvicorn `--workers` 多进程模式
- ✅ 使用 Redis 缓存频繁的系统数据
- ✅ 活动连接池管理数据库
- ✅ 定期清理旧日志（日志轮转）
- ✅ 监控内存占用，调整 DAG 并发数

### 基础设施优化

- ✅ 使用 SSD 存储（提高日志 I/O 速度）
- ✅ 配置 TCP 连接池参数
- ✅ 启用 gzip 传输压缩
- ✅ 使用 CDN 分发静态资源（可选）
- ✅ 监控系统资源（CPU、内存、磁盘）

## 13. 安全最佳实践

### 部署安全

- ✅ **不以 root 身份运行** - 使用专用用户（app/yl-monitor）
- ✅ **保护 .env 文件** - 包含敏感配置，限制文件权限（600）
- ✅ **启用 HTTPS** - 生产环境使用 SSL/TLS 证书
- ✅ **限制 CORS 源** - 不使用 `*`，指定具体域名
- ✅ **防火墙配置** - 仅开放必要端口（5500）

### 代码安全

- ✅ **输入验证** - 使用 Pydantic 模型校验请求数据
- ✅ **白名单机制** - 脚本、DAG、AR 节点均需预定义
- ✅ **错误信息** - 生产环境隐藏敏感信息，仅返回 `error_code`
- ✅ **日志审计** - 记录所有脚本执行、API 调用
- ✅ **依赖更新** - 定期更新 pip 包，修复漏洞

### 生产部署检查清单

```
□ Python 版本 ≥ 3.9
□ 虚拟环境已创建、并激活
□ 依赖已通过 requirements.txt 安装
□ .env 文件已配置（权限 600）
□ 日志目录已创建且可写
□ Systemd 服务文件已部署
□ 防火墙已配置，仅开放 5500 端口
□ CORS 源已限制（非 *）
□ SSL/TLS 证书已配置（如需）
□ 日志轮转已配置
□ 监控告警已部署
□ 备份策略已规划
□ 灾难恢复计划已制定
□ 团队文档已完善
```

## 14. 常见问题 (FAQ)

**Q: 项目有推荐的浏览器吗？**
A: 现代浏览器均支持（Chrome 90+, Firefox 88+, Safari 14+, Edge 90+）

**Q: 可以集成身份验证吗？**
A: 可以。框架已预留 `app/auth/` 模块，可实现 JWT、OAuth2 等

**Q: 支持多用户并发访问吗？**
A: 支持。WebSocket 使用连接池管理，同时支持数百连接

**Q: 如何扩展到多机部署？**
A: 建议使用消息队列（Redis）替代内存存储、使用共享日志存储（NFS）

**Q: 脚本执行超时如何处理？**
A: 可在 DAG 配置中设置 `timeout`，超时自动中断进程

**Q: 如何实现脚本间数据传递？**
A: 通过 DAG 节点的 `params` 和 `output` 字段实现数据流

## 15. 致谢与许可

本项目采用开源开发模式，欢迎社区贡献代码、提交 Issue、改进文档。

感谢所有依赖库的作者，包括：FastAPI、Pydantic、Uvicorn、Jinja2 等。

## 16. 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [Uvicorn 官方文档](https://www.uvicorn.org/)
- [systemd 官方文档](https://www.freedesktop.org/wiki/Software/systemd/)
- [Docker 官方文档](https://docs.docker.com/)

## 17. 更新日志

### v1.0.0 (2026-02-05)

- ✅ 项目初始化
- ✅ FastAPI 后端核心完成
- ✅ 5 大页面前端实现
- ✅ 54+ 自动化脚本库
- ✅ DAG 引擎与调度器
- ✅ Docker 容器化支持
- ✅ Systemd 生产部署支持
- ✅ 完整项目文档

---

**最后更新**：2025 年 2 月 8 日 | **维护者**：Project Team
