# 故障排查指南

**版本:** 1.0.0  
**最后更新:** 2026-02-16

---

## 🔍 问题分类

| 类别 | 说明 | 常见症状 |
|------|------|----------|
| **服务启动问题** | 服务无法正常启动 | 端口冲突、依赖缺失 |
| **连接问题** | 服务间无法通信 | 连接超时、拒绝连接 |
| **性能问题** | 系统响应缓慢 | CPU/内存占用高 |
| **功能问题** | 功能无法正常使用 | 视频无法加载、模型错误 |

---

## 🚨 服务启动问题

### 问题1: 端口被占用

**症状**:
```bash
# 启动服务时显示
Error: Port 5500 is already in use
```

**诊断**:
```bash
# 查找占用端口的进程
netstat -tlnp | grep 5500
# 或
lsof -i :5500

# 输出示例
tcp   0   0 0.0.0.0:5500   0.0.0.0:*   LISTEN   12345/python
```

**解决方案**:

**方案A: 停止占用进程**
```bash
# 优雅停止
kill 12345

# 强制停止
kill -9 12345
```

**方案B: 使用备用端口**
```bash
# 修改配置文件
# YL-monitor: YL-monitor/config/settings.yaml
# AR-backend: AR-backend/monitor_config.yaml
# User GUI: user/config/settings.py

# 或使用环境变量
export YL_MONITOR_PORT=5503
python YL-monitor/start_server.py
```

---

### 问题2: Python 模块导入错误

**症状**:
```python
ImportError: No module named 'fastapi'
ImportError: cannot import name 'ARBackendClient' from 'user.services'
```

**诊断**:
```bash
# 检查 Python 路径
python3 -c "import sys; print('\n'.join(sys.path))"

# 检查模块是否存在
python3 -c "import fastapi; print(fastapi.__version__)"
```

**解决方案**:

**步骤1: 安装缺失依赖**
```bash
# 基础依赖
pip3 install fastapi uvicorn flask pyqt5 opencv-python numpy requests psutil

# AR-backend 依赖
pip3 install -r AR-backend/requirements/requirements.txt

# YL-monitor 依赖
pip3 install -r YL-monitor/requirements.txt
```

**步骤2: 修复路径问题（User GUI）**
```bash
# 检查 path_manager.py 是否正确设置
python3 -c "from user.core.path_manager import PathManager; pm = PathManager(); print(pm.project_root)"
```

**步骤3: 验证修复**
```bash
cd user
python3 -c "from core.path_manager import setup_paths; setup_paths(); from services.ar_backend_client import ARBackendClient; print('导入成功')"
```

---

### 问题3: 权限不足

**症状**:
```bash
PermissionError: [Errno 13] Permission denied: './scripts/yl-ar-dgn.sh'
```

**解决方案**:
```bash
# 添加执行权限
chmod +x ./scripts/yl-ar-dgn.sh

# 验证
ls -la ./scripts/yl-ar-dgn.sh
# 应显示: -rwxr-xr-x ...
```

---

## 🔌 连接问题

### 问题4: 服务间无法通信

**症状**:
```python
requests.exceptions.ConnectionError: HTTPConnectionPool(host='0.0.0.0', port=5501): Max retries exceeded
```

**诊断**:
```bash
# 检查目标服务是否运行
curl http://0.0.0.0:5501/health
# 或
./scripts/yl-ar-dgn.sh status

# 检查网络连通性
ping0.0.0.0
telnet0.0.0.0 5501
```

**解决方案**:

**步骤1: 启动目标服务**
```bash
# 启动 AR-backend
python AR-backend/monitor_server.py &

# 启动 User GUI 状态服务
cd user && python3 main.py &
```

**步骤2: 检查防火墙**
```bash
# 检查防火墙规则
sudo iptables -L | grep 5501

# 临时关闭防火墙（测试用）
sudo systemctl stop firewalld
# 或
sudo ufw disable
```

**步骤3: 验证连接**
```bash
# 从 User GUI 测试连接
cd user
python3 -c "
from services.ar_backend_client import ARBackendClient
client = ARBackendClient()
print(client.health_check())
"
```

---

### 问题5: CORS 跨域错误

**症状**:
```
Access to XMLHttpRequest at 'http://0.0.0.0:5501/status' from origin 'http://0.0.0.0:5500' has been blocked by CORS policy
```

**解决方案**:
```python
# 在 AR-backend/monitor_server.py 中确保 CORS 配置正确
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/health": {"origins": "*"},
    r"/status": {"origins": "*"},
    r"/metrics": {"origins": "*"}
})
```

---

## ⚡ 性能问题

### 问题6: CPU 占用过高

**症状**:
- 系统响应缓慢
- 风扇高速运转
- `top` 命令显示 Python 进程 CPU > 80%

**诊断**:
```bash
# 查看 CPU 占用
top -p $(pgrep -d',' python)

# 或
ps aux | grep python | awk '{print $2, $3, $11}' | sort -k2 -nr
```

**解决方案**:

**步骤1: 限制进程资源**
```bash
# 使用 nice 降低优先级
nice -n 10 python AR-backend/monitor_server.py

# 或使用 cpulimit
cpulimit -p 12345 -l 50  # 限制50% CPU
```

**步骤2: 优化代码**
```python
# 在视频处理循环中添加适当延迟
import time
time.sleep(0.01)  # 10ms 延迟，降低 CPU 占用
```

**步骤3: 调整帧率**
```python
# 降低视频处理帧率
TARGET_FPS = 15  # 从30降到15
```

---

### 问题7: 内存不足

**症状**:
```python
MemoryError: Unable to allocate array with shape (1920, 1080, 3) and data type uint8
```

**诊断**:
```bash
# 查看内存使用
free -h

# 查看 Python 进程内存
ps aux | grep python | awk '{print $2, $4, $11}' | sort -k2 -nr
```

**解决方案**:

**步骤1: 释放内存**
```bash
# 重启服务
./scripts/yl-ar-dgn.sh restart

# 或清理缓存
echo 3 > /proc/sys/vm/drop_caches  # 需要root权限
```

**步骤2: 优化内存使用**
```python
# 及时释放大对象
import gc
del large_array
gc.collect()

# 使用生成器代替列表
def process_frames():
    for frame in camera_stream():
        yield process(frame)  # 不保存所有帧
```

---

## 🎨 功能问题

### 问题8: GUI 界面无法显示

**症状**:
- 执行 `python3 user/main.py` 无窗口弹出
- 报错 `QXcbConnection: Could not connect to display`

**诊断**:
```bash
# 检查 DISPLAY 环境变量
echo $DISPLAY

# 检查 X11 连接
xhost +  # 允许所有连接
```

**解决方案**:

**方案A: 本地运行**
```bash
# 设置 DISPLAY
export DISPLAY=:0

# 验证
python3 -c "from PyQt5.QtWidgets import QApplication; app = QApplication([]); print('OK')"
```

**方案B: SSH 远程运行**
```bash
# 启用 X11 转发
ssh -X user@host

# 或在 SSH 配置中添加
# ~/.ssh/config
Host remote-host
    ForwardX11 yes
```

**方案C: 使用虚拟显示（无头模式）**
```bash
# 安装虚拟显示
sudo apt-get install xvfb

# 启动虚拟显示
Xvfb :1 -screen 0 1024x768x16 &

# 设置 DISPLAY
export DISPLAY=:1
```

---

### 问题9: 视频无法加载

**症状**:
- GUI 中视频窗口黑屏
- 报错 `Cannot open camera`

**诊断**:
```bash
# 检查摄像头设备
ls -la /dev/video*

# 测试摄像头
vlc v4l2:///dev/video0

# 检查 OpenCV 是否能打开
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

**解决方案**:

**步骤1: 检查权限**
```bash
# 添加用户到 video 组
sudo usermod -a -G video $USER

# 重新登录生效
```

**步骤2: 指定摄像头设备**
```python
# 在配置中指定设备
CAMERA_DEVICE = "/dev/video0"  # 或 1, 2 等
```

**步骤3: 使用视频文件代替**
```python
# 调试时使用视频文件
VIDEO_SOURCE = "test_video.mp4"  # 代替摄像头
```

---

### 问题10: 人脸模型加载失败

**症状**:
```
Error: Face model not found: models/face_model.pth
RuntimeError: Error(s) in loading state_dict
```

**诊断**:
```bash
# 检查模型文件
ls -la AR-backend/models/

# 检查模型格式
python3 -c "
import torch
model = torch.load('models/face_model.pth', map_location='cpu')
print(model.keys())
"
```

**解决方案**:

**步骤1: 下载模型文件**
```bash
# 从指定位置下载
wget https://example.com/models/face_model.pth -O AR-backend/models/face_model.pth
```

**步骤2: 检查模型兼容性**
```python
# 确保模型版本匹配
import torch
print(torch.__version__)  # 应与训练时版本一致
```

**步骤3: 使用备用模型**
```python
# 配置中使用备用模型
FACE_MODEL_PATH = "models/face_model_backup.pth"
```

---

## 📝 日志收集

当问题无法解决时，收集以下日志：

```bash
# 创建日志收集脚本
cat > collect_logs.sh << 'EOF'
#!/bin/bash
LOG_DIR="logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p $LOG_DIR

# 收集服务日志
cp YL-monitor/logs/app.log $LOG_DIR/yl-monitor.log 2>/dev/null
cp AR-backend/logs/monitor.log $LOG_DIR/ar-backend.log 2>/dev/null
cp user/logs/user_gui.log $LOG_DIR/user-gui.log 2>/dev/null

# 收集系统信息
ps aux > $LOG_DIR/processes.txt
netstat -tlnp > $LOG_DIR/ports.txt
free -h > $LOG_DIR/memory.txt
df -h > $LOG_DIR/disk.txt

# 打包
tar -czf ${LOG_DIR}.tar.gz $LOG_DIR
echo "日志已收集到: ${LOG_DIR}.tar.gz"
EOF

chmod +x collect_logs.sh
./collect_logs.sh
```

---

## 📞 获取帮助

如果以上方法无法解决问题：

1. **查看详细文档**: [部署索引](../../部署/0.部署索引.md)
2. **检查任务状态**: [TODO_DEPLOY](../../部署/TODO_DEPLOY.md)
3. **查看完成报告**: [完成报告](../../部署/完成报告-阶段1到阶段3.md)

---

## ✅ 验证修复

修复问题后，执行以下验证：

```bash
# 1. 验证所有服务状态
./scripts/yl-ar-dgn.sh status

# 2. 验证健康检查
./scripts/yl-ar-dgn.sh health

# 3. 验证项目完整性
./scripts/yl-ar-dgn.sh validate

# 4. 启动 GUI 测试
cd user && python3 main.py
```

所有检查通过后，问题已解决！
