# YL-AR-DGN 增强现实架构数字孪生网络

**版本:** 2.4.0  
**最后更新:** 2026-02-16  
**状态:** 🟢 阶段1-5已完成(100%)，项目整合部署成功

[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-blue)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green)](https://flask.palletsprojects.com)

---

## 📋 项目概述

### 核心定位
YL-AR-DGN 是一个**多功能集成的 AR 实时处理与监控平台**，提供完整的增强现实后端服务、统一监控前端和用户操作界面。

### 主要核心启动项

| 启动项 | 命令 | 端口 | 说明 |
|--------|------|------|------|
| **YL-monitor** | `python YL-monitor/start_server.py` | 5500 | 统一监控平台 |
| **AR-backend** | `python AR-backend/monitor_server.py` | 5501 | 后端监控服务 |
| **User GUI** | `python user/main.py` | 5502 | 用户操作界面 |
| **统一入口** | `./scripts/yl-ar-dgn.sh start` | - | 一键启动所有服务 |
| **快速启动** | `./start-all.sh` | - | 一键启动（新增） |
| **快速停止** | `./stop-all.sh` | - | 一键停止（新增） |
| **状态检查** | `./check-status.sh` | - | 状态检查（新增） |

### 核心特征

| 特征 | 说明 |
|------|------|
| 🔴 **实时视频处理** | 支持摄像头实时视频流捕获和处理 |
| 👤 **人脸合成** | 集成 Deep-Live-Cam、DeepFaceLab、FaceSwap 等多种人脸合成引擎 |
| 🔊 **音频处理** | 支持多种音效效果（音高、混响、变速、相位等） |
| 📹 **虚拟摄像头** | 支持 OBS 虚拟摄像头输出 |
| 📊 **统一监控** | 提供完整的系统健康监控和告警机制 |
| 🌐 **Web 界面** | 基于 FastAPI 的 Web 监控界面 |
| 🎨 **用户界面** | 基于 PyQt5 的 AR 合成软件 GUI |

### 核心网页

| 页面 | 地址 | 功能 |
|------|------|------|
| **监控面板** | http://0.0.0.0:5500 | YL-monitor 统一监控平台 |
| **AR-backend 健康** | http://0.0.0.0:5501/health | 后端服务健康检查 |
| **User GUI 状态** | http://0.0.0.0:5502/health | 用户界面状态查询 |
| **API 文档** | http://0.0.0.0:5500/docs | FastAPI 自动生成的 API 文档 |

### 自动化启动项

```bash
# 一键启动所有服务
./scripts/yl-ar-dgn.sh start

# 查看所有服务状态
./scripts/yl-ar-dgn.sh status

# 验证项目完整性
./scripts/yl-ar-dgn.sh validate

# 查看帮助
./scripts/yl-ar-dgn.sh help
```

### 快速启动

```bash
# 方式1: 使用快速启动脚本（推荐）
./start-all.sh

# 方式2: 使用统一入口脚本
./scripts/yl-ar-dgn.sh start

# 方式3: 手动启动
cd /home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean

# 验证所有服务状态
curl http://0.0.0.0:5500/api/health      # YL-monitor
curl http://0.0.0.0:5501/health          # AR-backend
curl http://0.0.0.0:5502/health          # User GUI

# 启动 User GUI
cd user && python3 main.py

# 访问监控面板
# 浏览器打开 http://0.0.0.0:5500
```

### 快速运维命令

```bash
# 检查所有服务状态
./check-status.sh

# 验证五层监控架构
./scripts/verify-monitoring.sh

# 停止所有服务
./stop-all.sh
```

---

## 🏗️ 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YL-AR-DGN 系统架构                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    YL-Monitor (端口5500)                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │   │
│  │  │  Dashboard   │  │  AR Monitor  │  │  DAG Engine  │        │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│           ┌──────────────────┼──────────────────┐                    │
│           │                  │                  │                    │
│           ▼                  ▼                  ▼                    │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │  AR-backend  │   │  User GUI    │   │  Scripts     │            │
│  │  (端口5501)  │   │  (端口5502)  │   │  (统一入口)   │            │
│  │              │   │              │   │              │            │
│  │ • 视频处理   │   │ • 用户界面   │   │ • 部署控制   │            │
│  │ • 人脸合成   │   │ • 参数配置   │   │ • 监控管理   │            │
│  │ • 音频处理   │   │ • 状态显示   │   │ • 自动化     │            │
│  │ • 虚拟摄像头 │   │ • 用户交互   │   │ • 日志管理   │            │
│  └──────────────┘   └──────────────┘   └──────────────┘            │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    五层规则架构 (rules/)                     │   │
│  │  L1: 元目标层 → L2: 理解层 → L3: 约束层 → L4: 决策层 → L5: 执行层 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 组件职责

| 组件 | 技术栈 | 核心职责 | 运行方式 |
|------|--------|----------|----------|
| **YL-monitor** | FastAPI + WebSocket | 统一监控平台，监控 AR-backend 和 User GUI | HTTP服务 (5500) |
| **AR-backend** | PyQt5 + OpenCV | 实时视频处理、人脸合成、音频处理 | HTTP服务 (5501) + GUI |
| **User GUI** | PyQt5 | 用户操作界面，调用 AR-backend 接口 | HTTP服务 (5502) + GUI |
| **Scripts** | Bash + Python | 部署控制、监控管理、自动化脚本 | 命令行工具 |
| **Rules** | JSON + JS | 五层规则架构，约束系统行为 | 规则引擎 |

### 管理规范

#### 1. 服务管理规范

| 操作 | 命令 | 说明 |
|------|------|------|
| 启动所有服务 | `./scripts/yl-ar-dgn.sh start` | 按依赖顺序启动 |
| 停止所有服务 | `./scripts/yl-ar-dgn.sh stop` | 优雅停止 |
| 重启服务 | `./scripts/yl-ar-dgn.sh restart <组件>` | 重启指定组件 |
| 查看状态 | `./scripts/yl-ar-dgn.sh status` | 显示所有组件状态 |
| 健康检查 | `./scripts/yl-ar-dgn.sh health` | 检查所有服务健康 |

#### 2. 端口管理规范

| 服务 | 端口 | 用途 | 备用端口 |
|------|------|------|----------|
| YL-monitor | 5500 | 主监控平台 | 5503-5505 |
| AR-backend | 5501 | 后端监控 | 5506-5508 |
| User GUI | 5502 | 用户界面状态 | 5509 |

#### 3. 日志管理规范

| 组件 | 日志路径 | 日志级别 | 保留策略 |
|------|----------|----------|----------|
| YL-monitor | `YL-monitor/logs/app.log` | INFO | 7天滚动 |
| AR-backend | `AR-backend/logs/monitor.log` | INFO | 7天滚动 |
| User GUI | `user/logs/user_gui.log` | INFO | 7天滚动 |

#### 4. 配置管理规范

| 配置类型 | 位置 | 说明 |
|----------|------|------|
| 环境配置 | `config/` | 生产/预发布环境变量 |
| 性能配置 | `config/performance.conf` | 性能调优参数 |
| 安全配置 | `config/security.conf` | 安全策略配置 |
| 服务配置 | 各组件 `config/` | 组件特定配置 |

---

## 📊 整体项目状态

### 总体进度: **100%** (30/30任务完成)

| 阶段 | 状态 | 进度 | 完成日期 | 任务数 |
|------|------|------|----------|--------|
| **阶段1: 监控整合** | ✅ 已完成 | 100% | 2026-02-16 | 4/4 |
| **阶段2: User GUI优化** | ✅ 已完成 | 100% | 2026-02-16 | 5/5 |
| **阶段3: 规则架构部署** | ✅ 已完成 | 100% | 2026-02-16 | 7/7 |
| **阶段4: 脚本整合** | ✅ 已完成 | 100% | 2026-02-16 | 6/6 |
| **阶段5: 联调测试** | ✅ 已完成 | 100% | 2026-02-16 | 7/7 |

### 各分项目进度

| 组件 | 版本 | 状态 | 关键功能 | 完成度 |
|------|------|------|----------|--------|
| **YL-monitor** | 1.0.8 | 🟢 运行中 | 统一监控面板、五层监控架构、API层、DAG层 | 100% |
| **AR-backend** | 3.2.0 | 🟢 运行中 | 监控端点、视频处理、人脸合成、健康检查 | 100% |
| **User GUI** | 2.2.0 | 🟢 运行中 | 启动入口、路径修复、服务客户端、API通信 | 100% |
| **Scripts** | 2.4.0 | 🟢 可用 | 统一入口、部署控制、状态查询、15+命令 | 100% |
| **Rules** | 1.2.0 | ✅ 已完成 | L1-L5全部完成，规则引擎增强，33项测试通过 | 100% |

### 服务运行状态

| 服务 | 端口 | 状态 | 健康检查 | 启动时间 |
|------|------|------|----------|----------|
| YL-monitor | 5500 | 🟢 运行中 | ✅ 通过 | 2026-02-16 |
| AR-backend | 5501 | 🟢 运行中 | ✅ 通过 | 2026-02-16 |
| User GUI | 5502 | 🟢 运行中 | ✅ 通过 | 2026-02-16 |

### 测试统计
- **总测试数**: 56项
- **通过率**: 100%
- **阶段3规则测试**: 33项通过
- **阶段5联调测试**: 23项通过

---

## 🔧 环境要求

### 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | Ubuntu 20.04+ / Windows 10+ | Ubuntu 22.04 LTS |
| **CPU** | 4核 | 8核+ |
| **内存** | 8GB | 16GB+ |
| **磁盘** | 20GB 可用空间 | 50GB+ SSD |
| **网络** | 本地回环网络 | 千兆以太网 |
| **GPU** | 可选 (CUDA支持) | NVIDIA GTX 1060+ |

### Python 依赖

| 包 | 版本 | 用途 |
|----|------|------|
| **Python** | 3.8+ | 运行环境 |
| **FastAPI** | 0.104+ | YL-monitor Web框架 |
| **Flask** | 2.3+ | 监控服务 |
| **PyQt5** | 5.15+ | User GUI |
| **OpenCV** | 4.8+ | 视频处理 |
| **NumPy** | 1.24+ | 数值计算 |
| **requests** | 2.31+ | HTTP客户端 |
| **psutil** | 5.9+ | 系统监控 |
| **uvicorn** | 0.24+ | ASGI服务器 |
| **python-socketio** | 5.9+ | WebSocket支持 |

### 安装命令

```bash
# 基础依赖
pip install fastapi uvicorn flask pyqt5 opencv-python numpy requests psutil python-socketio

# AR-backend 依赖
pip install -r AR-backend/requirements/requirements.txt

# YL-monitor 依赖
pip install -r YL-monitor/requirements.txt

# User GUI 依赖
pip install -r user/requirements.txt  # 如果有
```

### Docker 环境（可选）

| 组件 | 版本 | 用途 |
|------|------|------|
| **Docker** | 20.10+ | 容器化部署 |
| **Docker Compose** | 2.20+ | 多服务编排 |

```bash
# Docker 部署
docker-compose up -d

# 或使用 Makefile
make up
```

---

## 📚 各项目集成内容

### 1. YL-monitor（统一监控平台）

**路径:** `YL-monitor/`  
**版本:** 1.0.8  
**端口:** 5500

#### 功能说明
- **统一监控面板**: 监控 AR-backend 和 User GUI 的状态
- **API 层监控**: 提供 RESTful API 接口
- **DAG 引擎**: 支持流水线编排
- **WebSocket**: 实时数据推送
- **脚本执行器**: 支持自动化脚本

#### 文档指引
- [YL-monitor README](YL-monitor/README.md) - 详细说明
- [监控整合方案](部署/3.监控整合方案.md) - 整合方案
- [统一监控面板架构](部署/统一监控面板架构方案.md) - 架构设计

#### 快速验证
```bash
curl http://0.0.0.0:5500/api/health
curl http://0.0.0.0:5500/api/v1/monitor/ui/status
```

---

### 2. AR-backend（实时视频处理后端）

**路径:** `AR-backend/`  
**版本:** 3.2.0  
**端口:** 5501

#### 功能说明
- **实时视频处理**: 摄像头实时视频流捕获和处理
- **人脸合成**: 集成多种人脸合成引擎
- **音频处理**: 多种音效效果
- **虚拟摄像头**: OBS 虚拟摄像头输出
- **监控端点**: 提供健康检查和状态查询

#### 文档指引
- [AR-backend README](AR-backend/README.md) - 详细说明
- [监控整合方案](部署/3.监控整合方案.md) - 监控端点设计
- [部署优化文档](AR-backend/DEPLOYMENT_OPTIMIZATION.md) - 部署优化

#### 快速验证
```bash
curl http://0.0.0.0:5501/health
curl http://0.0.0.0:5501/status
```

---

### 3. User GUI（用户操作界面）

**路径:** `user/`  
**版本:** 2.2.0  
**端口:** 5502

#### 功能说明
- **用户界面**: PyQt5 开发的 AR 合成软件 GUI
- **参数配置**: 模型、音效、视频源配置
- **状态显示**: 实时显示处理状态
- **服务客户端**: 与 AR-backend 通信
- **路径修复**: 解决模块导入问题

#### 核心模块
- `user/main.py` - 启动入口
- `user/core/path_manager.py` - 路径管理器
- `user/services/ar_backend_client.py` - 服务客户端
- `user/config/settings.py` - 配置管理器

#### 文档指引
- [User README](user/README.md) - 详细说明
- [User-GUI优化方案](部署/4.User-GUI优化方案.md) - 优化方案

#### 快速验证
```bash
cd user && python3 main.py
curl http://0.0.0.0:5502/health
```

---

### 4. Scripts（自动化脚本）

**路径:** `scripts/`  
**版本:** 2.4.0

#### 功能说明
- **统一入口**: `yl-ar-dgn.sh` 一键管理所有组件
- **部署控制**: 启动、停止、重启、状态查询
- **监控管理**: 健康检查、日志查看
- **自动化**: 定时任务、自动恢复

#### 核心脚本
- `scripts/yl-ar-dgn.sh` - 统一入口脚本
- `scripts/deploy/` - 部署脚本
- `scripts/monitor/` - 监控脚本
- `scripts/cleanup/` - 清理脚本

#### 文档指引
- [Scripts README](scripts/README.md) - 详细说明
- [脚本整合方案](部署/6.脚本整合方案.md) - 整合方案

#### 快速验证
```bash
./scripts/yl-ar-dgn.sh help
./scripts/yl-ar-dgn.sh status
./scripts/yl-ar-dgn.sh validate
```

---

### 5. Rules（五层规则架构）

**路径:** `rules/`  
**版本:** 1.2.0

#### 功能说明
- **L1 元目标层**: 项目愿景、核心目标
- **L2 理解层**: 功能需求、非功能需求
- **L3 约束层**: 技术约束、资源约束
- **L4 决策层**: 架构决策、技术选型
- **L5 执行层**: 开发流程、测试标准

#### 核心文件
- `rules/L1-meta-goal.json` - 元目标层
- `rules/L2-understanding.json` - 理解层
- `rules/L3-constraints.json` - 约束层
- `rules/L4-decisions.json` - 决策层
- `rules/L5-execution.json` - 执行层
- `rules/index.js` - 规则引擎

#### 文档指引
- [Rules README](rules/README.md) - 详细说明
- [规则架构部署方案](部署/5.规则架构部署.md) - 部署方案

#### 快速验证
```bash
python3 -c "import json; json.load(open('rules/L1-meta-goal.json'))"
python3 -c "import json; json.load(open('rules/L2-understanding.json'))"
python3 -c "import json; json.load(open('rules/L5-execution.json'))"
```

---

### 6. 部署文档

**路径:** `部署/`

#### 核心文档
| 文档 | 说明 |
|------|------|
| [部署索引](部署/0.部署索引.md) | 文档总入口，包含执行路线图 |
| [TODO_DEPLOY.md](部署/TODO_DEPLOY.md) | 任务跟踪清单 (29个任务) |
| [完成报告](部署/完成报告-阶段1到阶段3.md) | 阶段1-3合并完成报告 |
| [项目部署大纲](部署/1.项目部署大纲.md) | 项目整体部署规划 |
| [整体方案](部署/2.整体方案.md) | 系统整体架构方案 |
| [监控整合方案](部署/3.监控整合方案.md) | 监控整合详细方案 |
| [User-GUI优化方案](部署/4.User-GUI优化方案.md) | GUI优化详细方案 |
| [规则架构部署](部署/5.规则架构部署.md) | 规则架构详细方案 |
| [脚本整合方案](部署/6.脚本整合方案.md) | 脚本整合详细方案 |
| [联调测试方案](部署/7.联调测试方案.md) | 端到端测试方案 |

---

## 🚀 项目使用指南

### 日常运维命令
```bash
# 查看所有服务状态
./scripts/yl-ar-dgn.sh status

# 验证项目完整性
./scripts/yl-ar-dgn.sh validate

# 一键启动所有服务
./start-all.sh

# 一键停止所有服务
./stop-all.sh

# 检查服务健康状态
./check-status.sh

# 验证五层监控架构
./scripts/verify-monitoring.sh
```

### 访问服务
- **监控面板**: http://0.0.0.0:5500
- **AR-backend健康**: http://0.0.0.0:5501/health
- **User GUI状态**: http://0.0.0.0:5502/health
- **API文档**: http://0.0.0.0:5500/docs

---

## 📞 支持与反馈

### 常见问题排查
```bash
# 查看服务日志
tail -f YL-monitor/logs/app.log
tail -f AR-backend/logs/monitor.log
tail -f user/logs/user_gui.log

# 检查进程状态
ps aux | grep -E "yl-monitor|ar-backend|user-gui"

# 检查端口占用
netstat -tlnp | grep -E "5500|5501|5502"
```

### 文档导航
- **快速开始**: 本文档 📋 项目概述 → 🚀 快速启动
- **详细部署**: [部署索引](部署/0.部署索引.md) → [TODO_DEPLOY.md](部署/TODO_DEPLOY.md)
- **架构设计**: [整体方案](部署/2.整体方案.md)
- **完成状态**: [完成报告](部署/完成报告-阶段1到阶段3.md)

---

**维护者:** YL-AR-DGN 项目团队  
**许可证:** MIT  
**状态:** 🟢 阶段1-5已完成(100%)，项目整合部署成功，所有服务运行正常，可投入生产使用

---

## 📋 最新更新

### 2026-02-16 监控颗粒度优化阶段4完成 🎉
- ✅ 用户体验监控器 - GUI响应/操作/页面加载监控
- ✅ UI响应时间监控 - 组件响应+渲染时间
- ✅ 用户操作监控 - 操作耗时+成功率统计
- ✅ 用户体验评分 - 综合评分+等级评估系统
- ✅ 累计6个增强监控器，70+监控指标，项目100%完成

**实施报告:** [监控颗粒度优化-阶段4-实施完成报告](部署/监控颗粒度优化-阶段4-实施完成报告.md)

### 2026-02-16 监控颗粒度优化阶段3完成
- ✅ 业务功能监控器 - 视频/人脸/音频核心业务监控
- ✅ 视频处理监控 - FPS、丢帧率、处理延迟实时监控
- ✅ 人脸合成监控 - 推理时间、质量评分、GPU利用率
- ✅ 音频处理监控 - 延迟、实时因子、缓冲区状态
- ✅ 累计5个增强监控器，60+监控指标

**实施报告:** [监控颗粒度优化-阶段3-实施完成报告](部署/监控颗粒度优化-阶段3-实施完成报告.md)

### 2026-02-16 监控颗粒度优化阶段2完成
- ✅ 详细API监控器 - P50/P95/P99响应时间，错误率统计
- ✅ QPS吞吐量计算 - 实时API性能评估
- ✅ 慢端点识别 - 自动发现性能瓶颈
- ✅ 应用服务监控 - 5个核心API端点监控
- ✅ 累计4个增强监控器，50+监控指标

**实施报告:** [监控颗粒度优化-阶段2-实施完成报告](部署/监控颗粒度优化-阶段2-实施完成报告.md)

### 2026-02-16 监控颗粒度优化阶段1完成
- ✅ 详细进程监控器 - 5秒高频采集，线程/文件描述符/IO统计
- ✅ 详细CPU监控器 - 每核监控+频率+负载评估
- ✅ 详细内存监控器 - 分段监控+Top进程统计
- ✅ 增强监控API - 7个新端点，支持历史查询
- ✅ 监控能力提升 - 粒度6-12倍，维度5-10倍

**实施报告:** [监控颗粒度优化-阶段1-实施完成报告](部署/监控颗粒度优化-阶段1-实施完成报告.md)

### 2026-02-16 优化建议实施完成
- ✅ 修复监控器API端点 - 五层监控架构可通过HTTP访问
- ✅ 创建快速启动脚本 - `start-all.sh` 一键启动
- ✅ 创建停止脚本 - `stop-all.sh` 一键停止  
- ✅ 创建状态检查脚本 - `check-status.sh` 状态检查
- ✅ 创建监控验证工具 - `scripts/verify-monitoring.sh` 验证工具

**实施报告:** [优化建议实施完成报告](部署/优化建议实施完成报告.md)
