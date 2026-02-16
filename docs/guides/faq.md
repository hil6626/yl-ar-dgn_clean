# 常见问题解答 (FAQ)

**版本:** 1.0.0  
**最后更新:** 2026-02-16  
**问题数量:** 20+

---

## 🚀 快速导航

| 类别 | 问题数量 | 说明 |
|------|----------|------|
| [入门问题](#-入门问题) | 5个 | 新用户常见问题 |
| [部署问题](#-部署问题) | 5个 | 安装和配置问题 |
| [使用问题](#-使用问题) | 5个 | 日常操作问题 |
| [技术问题](#-技术问题) | 5个 | 技术细节问题 |

---

## 🔰 入门问题

### Q1: YL-AR-DGN 是什么项目？

**A:** YL-AR-DGN 是一个**增强现实架构数字孪生网络项目**，提供：

- 🔴 **实时视频处理**: 摄像头实时视频流捕获和处理
- 👤 **人脸合成**: 集成多种人脸合成引擎（Deep-Live-Cam、DeepFaceLab、FaceSwap）
- 🔊 **音频处理**: 多种音效效果（音高、混响、变速、相位）
- 📹 **虚拟摄像头**: 支持 OBS 虚拟摄像头输出
- 📊 **统一监控**: 完整的系统健康监控和告警机制

**核心组件**:
- **YL-monitor** (端口5500): 统一监控平台
- **AR-backend** (端口5501): 实时视频处理后端
- **User GUI** (端口5502): 用户操作界面

---

### Q2: 项目需要什么样的硬件配置？

**A:** 

**最低配置**:
- CPU: 4核
- 内存: 8GB
- 磁盘: 20GB 可用空间
- 显卡: 集成显卡（可选独立显卡）

**推荐配置**:
- CPU: 8核+
- 内存: 16GB+
- 磁盘: 50GB+ SSD
- 显卡: NVIDIA GTX 1060+（用于GPU加速）

**注意**: 人脸合成和视频处理对CPU/GPU要求较高，推荐配置可获得更流畅体验。

---

### Q3: 项目支持哪些操作系统？

**A:** 

**完全支持**:
- ✅ Ubuntu 20.04/22.04 LTS
- ✅ Windows 10/11

**部分支持**:
- ⚠️ macOS（需要额外配置，部分功能可能受限）

**推荐**: Ubuntu 22.04 LTS，获得最佳兼容性和性能。

---

### Q4: 如何快速验证项目是否安装成功？

**A:** 执行以下命令：

```bash
# 1. 进入项目目录
cd /home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean

# 2. 验证所有服务
./scripts/yl-ar-dgn.sh validate

# 3. 检查服务状态
./scripts/yl-ar-dgn.sh status

# 4. 测试健康检查
curl http://0.0.0.0:5500/api/health
curl http://0.0.0.0:5501/health
curl http://0.0.0.0:5502/health
```

如果所有命令都返回成功信息，说明项目已正确安装。

---

### Q5: 项目的主要使用场景是什么？

**A:**

| 场景 | 说明 | 适用用户 |
|------|------|----------|
| **直播换脸** | 实时将主播脸部替换为指定人物 | 直播主播、内容创作者 |
| **虚拟形象** | 创建虚拟角色进行视频通话 | 远程办公、在线教育 |
| **视频制作** | 后期制作中的人物替换 | 视频编辑、影视制作 |
| **安全测试** | 人脸识别系统的对抗测试 | 安全研究员 |
| **娱乐应用** | 趣味换脸、表情包制作 | 普通用户 |

---

## 🔧 部署问题

### Q6: 如何安装项目依赖？

**A:** 

**步骤1: 安装系统依赖**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-dev python3-venv
sudo apt-get install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev

# 安装 Qt 依赖（用于GUI）
sudo apt-get install libqt5gui5 libqt5core5a libqt5widgets5
```

**步骤2: 安装Python依赖**
```bash
# 基础依赖
pip3 install fastapi uvicorn flask pyqt5 opencv-python numpy requests psutil python-socketio

# 或从requirements安装
pip3 install -r requirements.txt
pip3 install -r AR-backend/requirements/requirements.txt
pip3 install -r YL-monitor/requirements.txt
```

---

### Q7: 端口冲突如何解决？

**A:**

**方法1: 查找并停止占用进程**
```bash
# 查找占用5500端口的进程
netstat -tlnp | grep 5500
# 或
lsof -i :5500

# 停止进程
kill -9 <PID>
```

**方法2: 修改服务端口**
```bash
# 修改环境变量
export YL_MONITOR_PORT=5503
export AR_BACKEND_PORT=5504
export USER_GUI_PORT=5505

# 然后启动服务
python YL-monitor/start_server.py
```

**方法3: 使用配置文件**
```yaml
# YL-monitor/config/settings.yaml
server:
  port: 5503  # 改为其他端口
```

---

### Q8: 如何配置开机自启动？

**A:**

**方法1: 使用 systemd（推荐）**
```bash
# 创建服务文件
sudo tee /etc/systemd/system/yl-ar-dgn.service << 'EOF'
[Unit]
Description=YL-AR-DGN Project
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean
ExecStart=/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean/scripts/yl-ar-dgn.sh start
ExecStop=/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean/scripts/yl-ar-dgn.sh stop
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl enable yl-ar-dgn
sudo systemctl start yl-ar-dgn
```

**方法2: 使用 crontab**
```bash
# 编辑 crontab
crontab -e

# 添加开机启动
@reboot cd /home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean && ./scripts/yl-ar-dgn.sh start
```

---

### Q9: Docker 部署如何进行？

**A:**

**步骤1: 构建镜像**
```bash
# 构建所有服务
docker-compose build

# 或单独构建
docker build -t yl-monitor -f YL-monitor/Dockerfile .
docker build -t ar-backend -f AR-backend/Dockerfile .
```

**步骤2: 启动服务**
```bash
# 后台启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**步骤3: 验证**
```bash
# 检查容器状态
docker-compose ps

# 测试服务
curl http://0.0.0.0:5500/api/health
```

---

### Q10: 如何备份和恢复项目配置？

**A:**

**备份配置**
```bash
# 创建备份目录
mkdir -p backup/$(date +%Y%m%d)

# 备份配置文件
cp -r config/ backup/$(date +%Y%m%d)/
cp -r rules/ backup/$(date +%Y%m%d)/
cp -r YL-monitor/config/ backup/$(date +%Y%m%d)/yl-monitor/
cp -r user/config/ backup/$(date +%Y%m%d)/user/

# 备份数据
cp -r data/ backup/$(date +%Y%m%d)/

# 打包
tar -czf backup/yl-ar-dgn-backup-$(date +%Y%m%d).tar.gz backup/$(date +%Y%m%d)/
```

**恢复配置**
```bash
# 解压备份
tar -xzf backup/yl-ar-dgn-backup-20260216.tar.gz

# 恢复配置
cp -r backup/20260216/config/ ./
cp -r backup/20260216/rules/ ./
# ...
```

---

## 💡 使用问题

### Q11: 如何启动 User GUI？

**A:**

```bash
# 方法1: 使用统一入口
./scripts/yl-ar-dgn.sh start user-gui

# 方法2: 直接启动
cd user
python3 main.py

# 方法3: 使用启动脚本
cd user
./start.sh
```

**注意**: 如果使用SSH远程连接，需要启用X11转发：
```bash
ssh -X user@host
```

---

### Q12: 如何切换人脸模型？

**A:**

**步骤1: 准备模型文件**
- 将模型文件（`.pth` 或 `.onnx`）放入 `AR-backend/models/` 目录

**步骤2: 在GUI中选择**
1. 打开 User GUI
2. 点击"模型选择"按钮
3. 从列表中选择所需模型
4. 点击"加载模型"

**步骤3: 验证加载**
```bash
# 检查模型是否加载成功
curl http://0.0.0.0:5501/status | grep face_model
```

---

### Q13: 如何调整视频处理参数？

**A:**

**在GUI中调整**:
1. 打开 User GUI
2. 进入"设置"标签页
3. 调整以下参数：
   - **分辨率**: 640x480, 1280x720, 1920x1080
   - **帧率**: 15fps, 30fps, 60fps
   - **质量**: 低、中、高
   - **平滑度**: 0-100

**在配置文件中调整**:
```python
# user/config/settings.py
VIDEO_CONFIG = {
    "resolution": (1280, 720),
    "fps": 30,
    "quality": "high",
    "smoothing": 80
}
```

---

### Q14: 如何查看实时日志？

**A:**

**方法1: 使用统一入口**
```bash
# 查看所有日志
./scripts/yl-ar-dgn.sh logs

# 查看特定服务日志
./scripts/yl-ar-dgn.sh logs yl-monitor
./scripts/yl-ar-dgn.sh logs ar-backend
./scripts/yl-ar-dgn.sh logs user-gui
```

**方法2: 直接查看日志文件**
```bash
# YL-monitor
tail -f YL-monitor/logs/app.log

# AR-backend
tail -f AR-backend/logs/monitor.log

# User GUI
tail -f user/logs/user_gui.log
```

**方法3: 使用 journalctl（systemd）**
```bash
sudo journalctl -u yl-ar-dgn -f
```

---

### Q15: 如何停止所有服务？

**A:**

```bash
# 方法1: 使用统一入口（推荐）
./scripts/yl-ar-dgn.sh stop

# 方法2: 分别停止
pkill -f "start_server.py"
pkill -f "monitor_server.py"
pkill -f "user/main.py"

# 方法3: 使用 Docker
docker-compose down
```

---

## 🔬 技术问题

### Q16: 项目使用什么技术栈？

**A:**

| 组件 | 技术栈 | 用途 |
|------|--------|------|
| **YL-monitor** | FastAPI + WebSocket | 监控平台后端 |
| **AR-backend** | Flask + PyQt5 + OpenCV | 视频处理服务 |
| **User GUI** | PyQt5 | 用户界面 |
| **人脸合成** | PyTorch/ONNX | 深度学习模型 |
| **音频处理** | librosa + soundfile | 音效处理 |
| **监控** | Prometheus + Grafana | 系统监控 |

---

### Q17: API 接口有哪些？

**A:**

**YL-monitor API** (端口5500):
```
GET  /api/health              # 健康检查
GET  /api/v1/monitor/ui/status    # UI层状态
GET  /api/v1/monitor/api/status   # API层状态
GET  /api/v1/monitor/dag/list     # DAG列表
POST /api/v1/monitor/dag/execute # 执行DAG
```

**AR-backend API** (端口5501):
```
GET  /health                 # 健康检查
GET  /status                 # 详细状态
GET  /metrics                # 性能指标
POST /face/swap              # 人脸合成
POST /audio/process          # 音频处理
```

**User GUI API** (端口5502):
```
GET  /health                 # 健康检查
GET  /status                 # 状态查询
GET  /stats                  # 统计信息
```

---

### Q18: 如何扩展项目功能？

**A:**

**添加新的人脸模型**:
1. 将模型文件放入 `AR-backend/models/`
2. 在 `AR-backend/core/face_processor.py` 中添加模型加载逻辑
3. 更新 `AR-backend/config/models.yaml` 添加模型配置

**添加新的监控指标**:
1. 在 `YL-monitor/app/services/` 创建新的监控服务
2. 在 `YL-monitor/app/api/v1/monitor/` 添加API端点
3. 更新监控面板显示

**添加新的DAG任务**:
1. 在 `YL-monitor/dags/` 创建新的DAG定义文件
2. 在 `YL-monitor/app/dag_engine/` 添加任务执行逻辑
3. 通过API或界面调度新DAG

---

### Q19: 项目的数据流是怎样的？

**A:**

```
用户操作 (User GUI)
    ↓ HTTP/WebSocket
YL-monitor (统一监控)
    ↓ HTTP
AR-backend (视频处理)
    ↓ 内部调用
├─ 摄像头捕获 (OpenCV)
├─ 人脸检测/合成 (PyTorch)
├─ 音频处理 (librosa)
└─ 虚拟摄像头输出 (pyvirtualcam)
    ↓
OBS/直播软件
```

详细数据流图见: [数据流说明](../architecture/data-flow.md)

---

### Q20: 如何参与项目开发？

**A:**

**步骤1: Fork 项目**
```bash
git clone https://github.com/your-username/YL-AR-DGN.git
cd YL-AR-DGN
```

**步骤2: 创建分支**
```bash
git checkout -b feature/your-feature-name
```

**步骤3: 开发和测试**
```bash
# 编写代码
# 运行测试
./scripts/yl-ar-dgn.sh test

# 验证代码风格
./scripts/yl-ar-dgn.sh lint
```

**步骤4: 提交PR**
```bash
git add .
git commit -m "Add: 你的功能描述"
git push origin feature/your-feature-name
```

详细贡献指南: [贡献指南](../development/contribution.md)

---

## 📚 更多资源

| 资源 | 链接 | 说明 |
|------|------|------|
| 快速开始 | [quickstart.md](quickstart.md) | 5分钟上手 |
| 故障排查 | [troubleshooting.md](troubleshooting.md) | 详细问题解决方法 |
| 部署文档 | [部署索引](../../部署/0.部署索引.md) | 完整部署指南 |
| API文档 | http://0.0.0.0:5500/docs | FastAPI自动生成的API文档 |

---

## ❓ 还有其他问题？

如果以上FAQ没有解决您的问题：

1. 查看 [故障排查指南](troubleshooting.md) 获取详细解决方法
2. 查看 [部署文档](../../部署/0.部署索引.md) 了解部署详情
3. 收集日志并联系项目维护者

---

**最后更新:** 2026-02-16  
**维护者:** YL-AR-DGN 项目团队
