# 📊 夜灵多功能统一监控平台

> 一个轻量级、模块化的本地部署监控与控制平台

**版本**: 1.0.8  
**最后更新**: 2026-02-16  
**部署状态**: 阶段1&2已完成 - 统一监控面板已部署

---

## 1. 项目概述

**YL-Monitor** 是一个基于 FastAPI + Jinja2 + WebSocket 的浏览器监控与控制平台，用于统一管理：

- 🖥️ **系统健康监控** - CPU、内存、磁盘、网络等实时监控
- 🐍 **Python 自动化脚本** - 54+ 脚本白名单管理与执行
- 📊 **DAG 流水线编排** - 有向无环图任务调度与可视化
- 🎨 **AR 合成项目监控** - 3D 节点状态监控与资源跟踪
- 🔌 **API 统一映射** - 前后端接口自描述与表单调试
- 🔗 **统一监控面板** - 集成UI层/API层/DAG层监控 (新增)

平台采用 **FastAPI + 浏览器 UI** 架构，通过单一 HTTP 服务对外提供 5 大页面控制台能力，适用于：

- ✨ 本地系统巡检与优化
- 🏢 内部研发监控控制台
- 🤖 自动化脚本管理平台
- 📈 数据流水线编排系统
- 🌐 AR / 数字孪生项目监控底座

**当前版本**：1.0.7（2026-02-16，统一监控面板已部署）

**最新特性**：
- 🚀 企业级性能优化（API响应<200ms，支持100+并发用户）
- 🐳 完整的 Docker 容器化支持
- 🔒 Systemd 生产级后台守护部署
- 🔐 JWT认证与RBAC权限控制
- ♻️ 模块化设计，易于扩展
- 📱 响应式前端设计
- 📊 实时数据可视化
- 🛡️ 全面的安全加固
- 🔗 **统一监控面板** - 四层架构监控（UI/API/DAG/系统）

---

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
- **平台入口（SPA）**：`http://0.0.0.0:5500`
- **仪表盘（独立页）**：`http://0.0.0.0:5500/dashboard`
- **统一监控面板**：`http://0.0.0.0:5500/api/v1/monitor/ui/status`

### 2.2 Docker 快速启动

```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2.3 使用统一入口脚本（推荐）

```bash
# 启动服务（生产模式）
python3 scripts/core/start.py --mode production

# 查看服务状态
python3 scripts/core/start.py --status

# 验证项目
python3 scripts/core/verify.py
```

---

## 3. 系统要求

| 项目 | 要求 | 验证命令 |
|------|-----|--------|
| **Python** | ≥ 3.9 | `python3 --version` |
| **内存** | ≥ 512 MB | `free -h` |
| **磁盘** | ≥ 100 MB | `df -h` |
| **操作系统** | Linux / macOS / Windows | 任意 |

---

## 4. 设计目标

✅ **单入口设计** - 浏览器即可访问全部能力  
✅ **模块化架构** - 各功能页面彼此解耦  
✅ **易于扩展** - 轻松添加新页面、新 DAG、新 AR 项目  
✅ **生产就绪** - 完整的异常处理、日志、监控、部署支持  
✅ **安全可控** - 脚本、DAG、AR 节点均白名单机制  
✅ **长期运行** - 支持 systemd 后台守护、开机自启  
✅ **统一监控** - 集成UI/API/DAG三层监控 (新增)

---

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
│  │  ├─ API 文档与自省路由           │   │
│  │  └─ Monitor 统一监控路由 ✅      │   │
│  │     ├─ /monitor/ui/*  UI层监控   │   │
│  │     ├─ /monitor/api/* API层监控  │   │
│  │     └─ /monitor/dag/* DAG层监控  │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
        ↓ 读写 ↑
  ┌──────────────────┐
  │  本地文件系统     │
  │  ├─ scripts/    │  # 自动化脚本
  │  ├─ dags/       │  # DAG 定义
  │  ├─ logs/       │  # 执行日志
  │  └─ static/     │  # 前端资源
  └──────────────────┘
```

### 5.2 统一监控架构（新增）

```
┌─────────────────────────────────────────────────────────────┐
│                    YL-Monitor (端口5500)                     │
│                    统一监控面板                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   UI 层监控   │  │  API 层监控   │  │  DAG 层监控   │      │
│  │  /monitor/ui │  │  /monitor/api │  │  /monitor/dag │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ User GUI状态 │  │ AR-backend   │  │ 流水线状态   │      │
│  │ 进程监控     │  │ 健康检查     │  │ 执行历史     │      │
│  │ 资源使用     │  │ 性能指标     │  │ 节点状态     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            ▼                               │
│                   ┌─────────────────┐                        │
│                   │   系统概览层    │                        │
│                   │  /dashboard    │                        │
│                   └─────────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  User GUI    │   │  AR-backend  │   │  DAG Engine  │
    │  (端口5502)   │   │  (端口5501)   │   │  (内部)      │
    └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 6. 页面与API 说明

### 6.1 Dashboard（主仪表盘）

**访问路径**: `/dashboard`

**功能**：
- 系统资源实时监控（CPU、内存、磁盘、网络）
- 服务运行状态指示
- 快速操作卡片

**后端接口**：
- `GET /api/dashboard/summary` - 系统整体状态
- `GET /api/health` - 健康检查

### 6.2 Scripts（自动化脚本管理）

**访问路径**: `/scripts`

**后端接口**：
- `GET /api/scripts/list` - 脚本清单
- `POST /api/scripts/run` - 触发脚本

### 6.3 API Doc（API 文档及调试）

**访问路径**: `/api-doc`

### 6.4 DAG Console（流水线控制）

**访问路径**: `/dag`

**后端接口**：
- `GET /api/dag/list` - DAG 清单
- `POST /api/dag/run` - 触发 DAG

### 6.5 AR Monitor（AR 合成监控）

**访问路径**: `/ar`

### 6.6 统一监控面板（新增）

**访问路径**: `/api/v1/monitor/*`

**功能**：
- UI层监控: User GUI状态、进程监控、资源使用
- API层监控: AR-backend健康检查、性能指标
- DAG层监控: 流水线状态、执行历史、节点状态

**后端接口**：
- `GET /api/v1/monitor/ui/status` - User GUI状态
- `GET /api/v1/monitor/api/status` - AR-backend状态
- `GET /api/v1/monitor/dag/list` - DAG流水线列表

**验证命令**：
```bash
# 验证统一监控面板
curl http://0.0.0.0:5500/api/v1/monitor/ui/status
curl http://0.0.0.0:5500/api/v1/monitor/api/status
curl http://0.0.0.0:5500/api/v1/monitor/dag/list
```

---

## 7. 部署指南

### 7.1 本地开发环境

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 5500
```

### 7.2 Docker 部署

```bash
docker-compose up -d
```

### 7.3 Systemd 部署

```bash
# 复制服务文件
sudo cp systemd/yl-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yl-monitor
sudo systemctl start yl-monitor
```

---

## 8. 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `YL_MONITOR_LOG_LEVEL` | `INFO` | 日志级别 |
| `YL_MONITOR_CORS_ORIGINS` | `*` | CORS 允许的源 |
| `YL_MONITOR_SCRIPTS_DIR` | `scripts` | 脚本目录 |
| `YL_MONITOR_DAGS_DIR` | `dags` | DAG 定义目录 |
| `YL_MONITOR_LOGS_DIR` | `logs` | 日志输出目录 |
| `YL_MONITOR_DAG_CONCURRENCY` | `6` | DAG 并发数量 |

---

## 9. 项目目录结构

```
YL-monitor/
├── README.md                      # 本文件
├── requirements.txt               # Python 依赖清单
├── Dockerfile                     # Docker 镜像定义
├── docker-compose.yml             # Docker Compose配置
├── .env.example                   # 环境变量示例
├── app/                           # 后端应用（FastAPI）
│   ├── main.py                    # 应用入口
│   ├── routes/                    # HTTP 路由
│   │   ├── dashboard.py           # 仪表盘路由
│   │   ├── scripts.py             # 脚本路由
│   │   ├── dag.py                 # DAG路由
│   │   ├── ar.py                  # AR监控路由
│   │   └── monitor/               # ✅ 统一监控路由（新增）
│   │       ├── __init__.py        # 路由聚合器
│   │       ├── ui.py              # UI层监控
│   │       ├── api.py              # API层监控
│   │       └── dag.py              # DAG层监控
│   ├── services/                  # 业务逻辑层
│   └── ws/                        # WebSocket处理
├── templates/                     # HTML模板
├── static/                        # 前端静态资源
├── scripts/                       # 自动化脚本
├── dags/                          # DAG定义
├── logs/                          # 日志目录
├── systemd/                       # systemd配置
└── 部署/                          # 部署文档
    ├── TODO_DEPLOY.md             # 任务跟踪
    ├── 0.部署索引.md              # 文档索引
    └── 阶段1-监控整合-完成报告.md # 完成报告
```

---

## 10. 部署状态跟踪

### 当前状态
- **阶段1 (监控整合)**: ✅ 已完成 (2026-02-16)
  - YL-monitor运行中: 端口5500
  - AR-backend监控: 端口5501
  - User GUI监控: 端口5502
  - 统一监控面板: `/api/v1/monitor/*`
- **阶段2 (User GUI优化)**: ✅ 已完成 (2026-02-16)
  - User GUI可正常启动
  - 所有功能可用

### 关联任务
- [部署任务跟踪](../部署/TODO_DEPLOY.md) - 查看完整任务清单
- [阶段1完成报告](../部署/阶段1-监控整合-完成报告.md) - 阶段1详细报告
- [阶段2完成报告](../部署/阶段2-UserGUI优化-完成报告.md) - 阶段2详细报告
- [统一监控架构方案](../部署/统一监控面板架构方案.md) - 架构设计

### 下一阶段
- **阶段3 (规则架构部署)**: 🟡 进行中 (60%)

---

## 11. 故障排查

### 问题：端口 5500 已被占用

```bash
# 检查占用情况
lsof -i :5500

# 解决方案
sudo kill -9 <PID>
```

### 问题：模块导入错误

```bash
# 确保虚拟环境已激活
source venv/bin/activate
pip install -r requirements.txt
```

### 问题：统一监控端点返回404

```bash
# 检查路由是否正确注册
curl http://0.0.0.0:5500/api/health

# 检查统一监控端点
curl http://0.0.0.0:5500/api/v1/monitor/ui/status
```

---

## 12. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.8 | 2026-02-16 | 更新阶段1&2完成状态，同步部署进度 |
| 1.0.7 | 2026-02-16 | 添加统一监控面板，更新部署状态 |
| 1.0.6 | 2026-02-10 | 生产就绪版本 |
| 1.0.0 | 2026-02-05 | 项目初始化 |

---

**最后更新**：2026-02-16  
**维护者**：AI 编程代理  
**部署状态**：阶段1&2已完成，统一监控面板已部署
