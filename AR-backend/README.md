# AR-backend

> **版本:** 3.0.0  
> **最后更新:** 2026-02-04  
> **文档状态:** 整合版本（由README.md、README_backend.md、README_src.md合并）

后端核心服务，承载人脸合成、视频处理、音频合成、监控与脚本调度等业务逻辑。

---

## 目录

1. [项目概述](#一项目概述)
2. [快速开始](#二快速开始)
3. [项目结构](#三项目结构)
4. [核心模块](#四核心模块)
5. [部署指南](#五部署指南)
6. [API文档](#六api文档)
7. [常见问题](#七常见问题)
8. [性能优化](#八性能优化)

---

## 一、项目概述

### 1.1 简介

AR-backend 是 AR Live Studio 的核心业务逻辑层，提供完整的系统功能支持，包括：

- **实时视频处理**: 支持摄像头实时视频流捕获和处理
- **人脸合成**: 集成 Deep-Live-Cam、DeepFaceLab、FaceSwap 等多种人脸合成引擎
- **音频处理**: 支持多种音效效果（音高、混响、变速、相位等）
- **虚拟摄像头**: 支持 OBS 虚拟摄像头输出
- **系统监控**: 提供完整的系统健康监控和告警机制
- **Web 界面**: 提供基于 Flask 的 Web 监控界面

### 1.2 技术架构

```
AR-backend/
├── app/                    # 应用入口与路由
│   ├── launcher.py         # 智能启动器
│   └── ...
├── core/                   # 核心能力模块
│   ├── audio_module.py     # 音频处理
│   ├── camera.py           # 相机模块
│   ├── path_manager.py     # 统一路径管理
│   └── utils.py            # 工具函数
├── services/               # 业务服务层
│   ├── face_detection_processor.py
│   ├── face_recognition_processor.py
│   ├── health_check.py
│   └── ...
├── integrations/           # 第三方集成
│   ├── Deep-Live-Cam/
│   ├── DeepFaceLab/
│   ├── faceswap/
│   ├── obs-studio/
│   └── sox/
├── config/                 # 配置管理
├── data/                   # 数据存储
├── requirements/           # 依赖清单
└── main.py                 # 主程序入口
```

### 1.3 模块关系

```
┌─────────────────────────────────────────────────────┐
│                   AR-backend                         │
├─────────────────────────────────────────────────────┤
│  app/ ←→ core/ ←→ services/ ←→ integrations/       │
│                      ↓                              │
│              config/, data/                         │
└─────────────────────────────────────────────────────┘
                       ↑
                       ↓
┌─────────────────────────────────────────────────────┐
│              YL-monitor (Web界面)                   │
│              api-map (接口定义)                      │
│              scripts (任务调度)                      │
└─────────────────────────────────────────────────────┘
```

---

## 二、快速开始

### 2.1 环境准备

```bash
# 检查Python版本
python3 --version  # 需要 Python 3.8+

# 检查pip版本
pip --version  # 需要 pip 21.0+
```

### 2.2 安装依赖

```bash
# 进入项目目录
cd /workspaces/yl-ar-dgn/AR-backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装核心依赖
pip install -r requirements/requirements.txt

# 验证安装
python3 -c "import flask, cv2, numpy, psutil; print('✅ 依赖安装成功')"
```

### 2.3 启动服务

```bash
# 方式1：使用启动器（推荐）
python3 app/launcher.py

# 方式2：直接启动主程序
python3 main.py

# 方式3：后台运行
python3 main.py > logs/backend.log 2>&1 &
```

### 2.4 验证部署

```bash
# 健康检查
curl http://localhost:5501/health

# 查看服务状态
curl http://localhost:5501/api/status
```

---

## 三、项目结构

### 3.1 目录说明

| 目录 | 功能 | 说明 |
|------|------|------|
| `app/` | 应用入口与路由 | 主流程与接口定义 |
| `core/` | 核心能力 | 通用模块与基础功能 |
| `services/` | 细分业务 | 人脸合成、视频处理、音频等 |
| `integrations/` | 第三方集成 | DeepFaceLab、OBS、SOX 等 |
| `config/` | 配置管理 | 系统配置与参数 |
| `data/` | 数据存储 | 运行时数据与缓存 |
| `requirements/` | 依赖清单 | Python 包依赖 |

### 3.2 核心文件

```
AR-backend/
├── main.py                 # 主程序入口
├── app/
│   ├── launcher.py        # 智能启动器
│   └── launcher.py       # 智能启动器
├── core/
│   ├── path_manager.py    # 统一路径管理
│   ├── utils.py           # 工具函数
│   ├── camera.py          # 相机模块
│   └── audio_module.py    # 音频处理
├── services/
│   ├── health_check.py    # 健康检查
│   ├── config_service.py  # 配置服务
│   ├── face_detection_processor.py  # 人脸检测
│   ├── face_recognition_processor.py # 人脸识别
│   ├── notification_service.py      # 通知服务
│   ├── alert_system.py    # 告警系统
│   └── performance_optimizer.py    # 性能优化
├── config/
│   └── pipeline.yaml      # 流水线配置
└── requirements/
    └── requirements.txt  # 依赖清单
```

---

## 四、核心模块

### 4.1 处理流水线

| 模块 | 功能 |
|------|------|
| `face_detection_processor.py` | 人脸检测与定位 |
| `face_recognition_processor.py` | 人脸识别与匹配 |
| `face_live_cam.py` | 实时人脸合成 |
| `faceswap_module.py` | Faceswap 集成 |
| `deep_face_lab.py` | DeepFaceLab 集成 |
| `obs_virtual_camera.py` | OBS 虚拟摄像头 |

### 4.2 系统服务

| 模块 | 功能 |
|------|------|
| `processor_manager.py` | 处理器编排与管理 |
| `notification_service.py` | 消息通知 |
| `alert_system.py` | 告警系统 |
| `health_check_service.py` | 健康检查 |
| `progress_tracker.py` | 进度追踪 |
| `security_manager.py` | 安全管理 |
| `performance_optimizer.py` | 性能优化 |

### 4.3 工具服务

| 模块 | 功能 |
|------|------|
| `cache_manager_service.py` | 缓存管理 |
| `log_collector_service.py` | 日志收集 |
| `deployment_tracker_service.py` | 部署追踪 |

### 4.4 第三方集成

| 目录 | 功能描述 |
|------|---------|
| `Deep-Live-Cam/` | 实时人脸合成开源项目 |
| `DeepFaceLab/` | 深度人脸实验室，高质量人脸处理 |
| `faceswap/` | 人脸交换和替换工具 |
| `obs-studio/` | 视频录制和直播推流软件 |
| `opencv/` | OpenCV 计算机视觉库 |
| `sox/` | Sox 音频处理工具 |

---

## 五、部署指南

### 5.1 系统要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| Python | 3.8+ | 3.10 |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB | 50GB+ |
| GPU | 可选 | NVIDIA CUDA |

### 5.2 环境配置

```bash
# 设置环境变量
export AR_PROJECT_ROOT=/workspaces/yl-ar-dgn/AR-backend
export PYTHONPATH=$AR_PROJECT_ROOT:$PYTHONPATH
export AR_LOG_LEVEL=INFO
export AR_MONITOR_PORT=5501
```

### 5.3 Docker 部署

```bash
# 构建镜像
docker build -t ar-backend:latest .

# 运行容器
docker run -d -p 5501:5501 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  --name ar-backend \
  ar-backend:latest
```

### 5.4 systemd 服务（生产环境）

```ini
# /etc/systemd/system/ar-backend.service
[Unit]
Description=AR Backend Service
After=network.target

[Service]
Type=simple
User=aruser
WorkingDirectory=/workspaces/yl-ar-dgn/AR-backend
Environment=AR_PROJECT_ROOT=/workspaces/yl-ar-dgn/AR-backend
ExecStart=/workspaces/yl-ar-dgn/AR-backend/venv/bin/python app/launcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable ar-backend
sudo systemctl start ar-backend
```

---

## 六、API 文档

### 6.1 健康检查接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 系统健康检查 |
| `/api/status` | GET | 服务状态 |
| `/api/system-info` | GET | 系统信息 |

### 6.2 资源监控接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/resource/cpu` | GET | CPU 使用率 |
| `/api/resource/memory` | GET | 内存使用率 |
| `/api/resource/disk` | GET | 磁盘使用率 |
| `/api/resource/network` | GET | 网络使用情况 |

### 6.3 服务管理接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/services` | GET | 获取服务列表 |
| `/api/services/start` | POST | 启动服务 |
| `/api/services/stop` | POST | 停止服务 |
| `/api/services/restart` | POST | 重启服务 |

### 6.4 处理任务接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/process` | POST | 提交处理任务 |
| `/api/process/status` | GET | 获取任务状态 |

### 6.5 WebSocket 接口

| 事件 | 方向 | 描述 |
|------|------|------|
| `/ws/progress` | 双向 | 进度推送 |
| `/ws/logs` | 双向 | 日志推送 |

---

## 七、常见问题

### Q1: 模块导入错误

```bash
# 错误信息
ModuleNotFoundError: No module named 'core.path_manager'

# 解决方案
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Q2: 虚拟环境创建失败

```bash
# 错误信息
ERROR: venv: the environment directory exists

# 解决方案
rm -rf venv
python3 -m venv venv
```

### Q3: 依赖安装超时

```bash
# 使用国内镜像源
pip install -r requirements/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### Q4: 端口被占用

```bash
# 查看占用端口的进程
sudo lsof -i :5501

# 或杀死占用端口的进程
sudo kill $(sudo lsof -t -i:5501)
```

---

## 八、性能优化

### 8.1 GPU 加速

```python
import torch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'使用设备: {device}')
```

### 8.2 OpenCV 优化

```python
import cv2
cv2.setUseOptimized(True)  # 启用优化
cv2.setNumThreads(4)       # 设置线程数
```

### 8.3 日志异步写入

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logging.basicConfig(handlers=[handler], level=logging.INFO)
```

### 8.4 内存优化

```python
from services.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer()
optimizer.start()

# 定期清理
optimizer.force_cleanup()
```

---

## 九、监控与维护

### 9.1 日志管理

```bash
# 查看实时日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log
```

### 9.2 备份策略

```bash
# 备份配置文件
cp -r config config.backup.$(date +%Y%m%d)

# 备份数据
cp -r data data.backup.$(date +%Y%m%d)
```

### 9.3 更新流程

```bash
# 1. 停止服务
sudo systemctl stop ar-backend

# 2. 备份
cp -r AR-backend AR-backend.backup.$(date +%Y%m%d)

# 3. 更新代码
git pull

# 4. 更新依赖
source venv/bin/activate
pip install -r requirements/requirements.txt

# 5. 重启服务
sudo systemctl start ar-backend
```

---

## 十、相关文档

| 文档 | 描述 |
|------|------|
| [详细说明](README_backend.md) | 处理流程、配置详解（已废弃，内容已整合） |
| [依赖清单](requirements/README.md) | 包版本与兼容性 |
| [集成指南](integrations/README.md) | 第三方工具配置 |
| [配置说明](config/README.md) | 系统配置参数 |
| [部署计划](DEPLOYMENT_PLAN.md) | 完整部署指南 |
| [部署清单](DEPLOYMENT_TODO.md) | 部署检查清单 |

---

## 十一、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 3.0.0 | 2026-02-04 | 整合版本，合并README_backend.md和README_src.md |
| 2.0 | 2026-02-09 | 增强版GUI，优化性能 |
| 1.0 | 2026-01-30 | 初始版本 |

---

**文档版本:** 3.0.0  
**最后更新:** 2026-02-04  
**维护者:** AI 编程代理
