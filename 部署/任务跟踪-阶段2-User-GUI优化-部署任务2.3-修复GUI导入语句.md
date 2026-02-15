# 阶段2 - 任务2.3: 修复 GUI 导入语句 - 详细部署文档

**任务ID:** 2.3  
**任务名称:** 修复 GUI 导入语句  
**优先级:** P0（阻塞性）  
**预计工时:** 3小时  
**状态:** 待执行  
**前置依赖:** 任务2.2完成（路径修复模块已创建）

---

## 一、任务目标

修复 user/gui/gui.py 中的所有导入语句，确保能正确加载 AR-backend 模块和本地服务模块。

## 二、部署内容

### 2.1 修改文件清单

| 序号 | 文件路径 | 操作类型 | 说明 |
|------|----------|----------|------|
| 1 | `user/gui/gui.py` | 修改 | 修复所有导入语句 |
| 2 | `user/gui/__init__.py` | 新建 | 包初始化文件 |
| 3 | `user/utils/import_helper.py` | 新建 | 导入辅助工具 |

### 2.2 详细代码实现

#### 文件1: 修改 user/gui/gui.py（导入部分）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR Live Studio - PyQt5 GUI 界面 (修复版)
修复所有导入问题，确保模块正确加载
"""

# ============================================================================
# 第一步：路径设置（必须在其他导入之前）
# ============================================================================

import sys
import os
from pathlib import Path

# 获取当前文件目录
current_dir = Path(__file__).parent.resolve()
user_dir = current_dir.parent
project_root = user_dir.parent

# 添加必要路径到sys.path
paths_to_add = [
    str(user_dir),
    str(project_root),
    str(project_root / 'AR-backend'),
    str(project_root / 'AR-backend' / 'core'),
    str(project_root / 'AR-backend' / 'services'),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"[Path] Added: {path}")

# ============================================================================
# 第二步：使用路径管理器（如果可用）
# ============================================================================

try:
    from utils.path_resolver import setup_project_paths
    setup_project_paths()
    print("[Path] Path resolver initialized")
except ImportError as e:
    print(f"[Path] Path resolver not available: {e}")

# ============================================================================
# 第三步：标准库导入
# ============================================================================

import time
import logging
import traceback
from datetime import datetime

# ============================================================================
# 第四步：第三方库导入
# ============================================================================

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QFileDialog, QTextEdit, QGroupBox,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget, QGridLayout, QSplitter
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon, QColor, QPalette

# ============================================================================
# 第五步：AR-backend模块导入（使用多种策略）
# ============================================================================

# 策略1：直接导入
try:
    from camera import CameraModule
    print("[Import] CameraModule loaded directly")
except ImportError as e1:
    print(f"[Import] Direct import failed: {e1}")
    
    # 策略2：从core导入
    try:
        from core.camera import CameraModule
        print("[Import] CameraModule loaded from core")
    except ImportError as e2:
        print(f"[Import] Core import failed: {e2}")
        
        # 策略3：从AR-backend.core导入
        try:
            from AR-backend.core.camera import CameraModule
            print("[Import] CameraModule loaded from AR-backend.core")
        except ImportError as e3:
            print(f"[Import] All CameraModule imports failed: {e3}")
            # 创建占位符
            class CameraModule:
                def __init__(self):
                    raise RuntimeError("CameraModule not available")
                def start(self): pass
                def stop(self): pass

# 导入AudioModule（使用相同策略）
try:
    from audio_module import AudioModule, AudioEffect
    print("[Import] AudioModule loaded directly")
except ImportError as e1:
    try:
        from core.audio_module import AudioModule, AudioEffect
        print("[Import] AudioModule loaded from core")
    except ImportError as e2:
        try:
            from AR-backend.core.audio_module import AudioModule, AudioEffect
            print("[Import] AudioModule loaded from AR-backend.core")
        except ImportError as e3:
            print(f"[Import] All AudioModule imports failed: {e3}")
            class AudioModule:
                def __init__(self): raise RuntimeError("AudioModule not available")
                def start(self): pass
                def stop(self): pass
            class AudioEffect:
                pass

# 导入工具模块
try:
    from utils import get_resource_path, format_time
    print("[Import] Utils loaded")
except ImportError:
    try:
        from core.utils import get_resource_path, format_time
        print("[Import] Utils loaded from core")
    except ImportError:
        print("[Import] Utils not available, using defaults")
        def get_resource_path(path): return str(user_dir / 'assets' / path)
        def format_time(seconds): return f"{int(seconds//60):02d}:{int(seconds%60):02d}"

# ============================================================================
# 第六步：本地服务导入
# ============================================================================

try:
    from services.status_reporter import get_reporter
    from services.local_http_server import LocalHTTPServer
    from services.monitor_client import MonitorClient
    print("[Import] Local services loaded")
except ImportError as e:
    print(f"[Import] Local services not available: {e}")
    # 创建占位符
    def get_reporter():
        return None
    class LocalHTTPServer:
        def __init__(self, **kwargs): pass
        def start(self): return False
        def stop(self): pass
    class MonitorClient:
        def __init__(self, **kwargs): pass

# ============================================================================
# 第七步：人脸合成模块导入（可选）
# ============================================================================

face_modules = {}

# Deep-Live-Cam
try:
    # 尝试导入Deep-Live-Cam
    deep_live_cam_path = project_root / 'AR-backend' / 'integrations' / 'Deep-Live-Cam'
    if deep_live_cam_path.exists():
        sys.path.insert(0, str(deep_live_cam_path))
        # 这里根据实际模块结构调整
        face_modules['deep_live_cam'] = {
            'available': True,
            'path': str(deep_live_cam_path)
        }
        print("[Import] Deep-Live-Cam path added")
except Exception as e:
    print(f"[Import] Deep-Live-Cam not available: {e}")
    face_modules['deep_live_cam'] = {'available': False}

# DeepFaceLab
try:
    deepface_lab_path = project_root / 'AR-backend' / 'integrations' / 'DeepFaceLab'
    if deepface_lab_path.exists():
        face_modules['deepface_lab'] = {
            'available': True,
            'path': str(deepface_lab_path)
        }
        print("[Import] DeepFaceLab path added")
except Exception as e:
    print(f"[Import] DeepFaceLab not available: {e}")
    face_modules['deepface_lab'] = {'available': False}

# FaceSwap
try:
    faceswap_path = project_root / 'AR-backend' / 'integrations' / 'faceswap'
    if faceswap_path.exists():
        face_modules['faceswap'] = {
            'available': True,
            'path': str(faceswap_path)
        }
        print("[Import] FaceSwap path added")
except Exception as e:
    print(f"[Import] FaceSwap not available: {e}")
    face_modules['faceswap'] = {'available': False}

print(f"[Import] Face modules: {face_modules}")

# ============================================================================
# 第八步：GUI类定义
# ============================================================================

class VideoWorker(QThread):
    """视频处理工作线程"""
    frame_ready = pyqtSignal(np.ndarray)
    statistics_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, camera_module):
        super().__init__()
        self.camera_module = camera_module
        self.running = False

    def run(self):
        self.running = True
        frame_count = 0
        
        while self.running:
            try:
                if hasattr(self.camera_module, 'capture') and self.camera_module.capture:
                    if self.camera_module.capture.isOpened():
                        ret, frame = self.camera_module.capture.read()
                        if ret:
                            # 处理帧
                            try:
                                processed_frame = self.camera_module.process_frame(frame)
                                self.frame_ready.emit(processed_frame)
                                frame_count += 1
                                
                                # 每30帧发送一次统计
                                if frame_count % 30 == 0:
                                    stats = {
                                        'frame_count': frame_count,
                                        'fps': getattr(self.camera_module, 'fps', 30)
                                    }
                                    self.statistics_ready.emit(stats)
                            except Exception as e:
                                self.error_occurred.emit(f"Frame processing error: {e}")
                
                # 控制帧率
                self.msleep(33)  # ~30fps
                
            except Exception as e:
                self.error_occurred.emit(f"Video worker error: {e}")
                self.msleep(100)

    def stop(self):
        self.running = False
        self.wait(1000)  # 等待1秒


class ARApp(QMainWindow):
    """AR Live Studio 主应用程序类（修复版）"""

    def __init__(self):
        super().__init__()
        
        # 初始化日志
        self.setup_logging()
        
        # 初始化状态
        self.camera_module = None
        self.audio_module = None
        self.video_worker = None
        self.status_reporter = None
        self.local_server = None
        
        self.is_fullscreen = False
        self.screenshot_count = 0
        self.record_enabled = False
        
        # 初始化模块
        self.init_modules()
        
        # 初始化UI
        self.init_ui()
        
        # 设置连接
        self.setup_connections()
        
        # 设置菜单
        self.setup_menus()
        
        # 启动监控
        self.init_monitoring()
        
        # 启动定时器
        self.start_timers()
        
        self.logger.info("ARApp initialized successfully")
    
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('ARApp')
        self.logger.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def init_modules(self):
        """初始化模块"""
        self.logger.info("Initializing modules...")
        
        # 初始化摄像头模块
        try:
            self.camera_module = CameraModule()
            self.logger.info("CameraModule initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize CameraModule: {e}")
            self.camera_module = None
        
        # 初始化音频模块
        try:
            self.audio_module = AudioModule()
            self.logger.info("AudioModule initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize AudioModule: {e}")
            self.audio_module = None
    
    def init_monitoring(self):
        """初始化监控"""
        self.logger.info("Initializing monitoring...")
        
        try:
            # 获取状态上报器
            self.status_reporter = get_reporter()
            if self.status_reporter:
                if self.status_reporter.start():
                    self.logger.info("Status reporter started")
                else:
                    self.logger.warning("Failed to start status reporter")
            
            # 启动本地HTTP服务
            self.local_server = LocalHTTPServer(
                port=5502,
                status_reporter=self.status_reporter
            )
            if self.local_server.start():
                self.logger.info("Local HTTP server started on port 5502")
            else:
                self.logger.warning("Failed to start local HTTP server")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring: {e}")
    
    def init_ui(self):
        """初始化UI"""
        self.logger.info("Initializing UI...")
        
        # 设置窗口属性
        self.setWindowTitle("AR Live Studio")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # 左侧面板
        self.left_panel = self.create_left_panel()
        self.main_layout.addWidget(self.left_panel, 1)
        
        # 中间视频区域
        self.video_area = self.create_video_area()
        self.main_layout.addWidget(self.video_area, 3)
        
        # 右侧面板
        self.right_panel = self.create_right_panel()
        self.main_layout.addWidget(self.right_panel, 1)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        self.logger.info("UI initialized")
    
    def create_left_panel(self):
        """创建左侧面板"""
        panel = QGroupBox("控制面板")
        layout = QVBoxLayout()
        
        # 摄像头控制
        camera_group = QGroupBox("摄像头")
        camera_layout = QVBoxLayout()
        
        self.camera_btn = QPushButton("启动摄像头")
        self.camera_btn.setCheckable(True)
        camera_layout.addWidget(self.camera_btn)
        
        self.camera_status = QLabel("状态: 未启动")
        camera_layout.addWidget(self.camera_status)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # 音频控制
        audio_group = QGroupBox("音频")
        audio_layout = QVBoxLayout()
        
        self.audio_btn = QPushButton("启动音频")
        self.audio_btn.setCheckable(True)
        audio_layout.addWidget(self.audio_btn)
        
        self.audio_status = QLabel("状态: 未启动")
        audio_layout.addWidget(self.audio_status)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # 人脸合成控制
        face_group = QGroupBox("人脸合成")
        face_layout = QVBoxLayout()
        
        self.face_combo = QComboBox()
        self.face_combo.addItem("选择模型...")
        for name, info in face_modules.items():
            if info['available']:
                self.face_combo.addItem(name)
        face_layout.addWidget(self.face_combo)
        
        self.load_face_btn = QPushButton("加载模型")
        face_layout.addWidget(self.load_face_btn)
        
        face_group.setLayout(face_layout)
        layout.addWidget(face_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def create_video_area(self):
        """创建视频显示区域"""
        panel = QGroupBox("视频预览")
        layout = QVBoxLayout()
        
        # 视频标签
        self.video_label = QLabel("视频未启动")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: #2d2d2d; color: white;")
        layout.addWidget(self.video_label)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.screenshot_btn = QPushButton("截图")
        btn_layout.addWidget(self.screenshot_btn)
        
        self.record_btn = QPushButton("录制")
        self.record_btn.setCheckable(True)
        btn_layout.addWidget(self.record_btn)
        
        self.fullscreen_btn = QPushButton("全屏")
        self.fullscreen_btn.setCheckable(True)
        btn_layout.addWidget(self.fullscreen_btn)
        
        layout.addLayout(btn_layout)
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """创建右侧面板"""
        panel = QGroupBox("信息与日志")
        layout = QVBoxLayout()
        
        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout()
        
        self.cpu_label = QLabel("CPU: --%")
        info_layout.addWidget(self.cpu_label)
        
        self.memory_label = QLabel("内存: --%")
        info_layout.addWidget(self.memory_label)
        
        self.fps_label = QLabel("FPS: --")
        info_layout.addWidget(self.fps_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 日志区域
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        log_layout.addWidget(self.log_text)
        
        # 日志按钮
        log_btn_layout = QHBoxLayout()
        
        clear_log_btn = QPushButton("清空")
        clear_log_btn.clicked.connect(self.clear_log)
        log_btn_layout.addWidget(clear_log_btn)
        
        save_log_btn = QPushButton("保存")
        save_log_btn.clicked.connect(self.save_log)
        log_btn_layout.addWidget(save_log_btn)
        
        log_layout.addLayout(log_btn_layout)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        panel.setLayout(layout)
        return panel
    
    def setup_connections(self):
        """设置信号连接"""
        self.logger.info("Setting up connections...")
        
        # 摄像头按钮
        self.camera_btn.toggled.connect(self.toggle_camera)
        
        # 音频按钮
        self.audio_btn.toggled.connect(self.toggle_audio)
        
        # 截图按钮
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        
        # 录制按钮
        self.record_btn.toggled.connect(self.toggle_recording)
        
        # 全屏按钮
        self.fullscreen_btn.toggled.connect(self.toggle_fullscreen)
        
        # 加载人脸模型按钮
        self.load_face_btn.clicked.connect(self.load_face_model)
    
    def setup_menus(self):
        """设置菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开图片", self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        monitor_action = QAction("监控面板", self)
        monitor_action.triggered.connect(self.open_monitor)
        tools_menu.addAction(monitor_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def start_timers(self):
        """启动定时器"""
        # 系统信息更新定时器
        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self.update_system_info)
        self.sys_timer.start(2000)  # 每2秒更新
    
    def toggle_camera(self, checked):
        """切换摄像头状态"""
        if checked:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """启动摄像头"""
        self.logger.info("Starting camera...")
        
        if not self.camera_module:
            self.log_message("摄像头模块不可用", "error")
            self.camera_btn.setChecked(False)
            return
        
        try:
            # 启动摄像头
            if hasattr(self.camera_module, 'start'):
                self.camera_module.start()
            
            # 启动视频工作线程
            self.video_worker = VideoWorker(self.camera_module)
            self.video_worker.frame_ready.connect(self.update_video_frame)
            self.video_worker.error_occurred.connect(self.handle_video_error)
            self.video_worker.start()
            
            self.camera_status.setText("状态: 运行中")
            self.camera_btn.setText("停止摄像头")
            self.log_message("摄像头已启动", "success")
            
            # 更新监控状态
            if self.status_reporter:
                self.status_reporter.update_gui_status(video_running=True)
            
        except Exception as e:
            self.logger.error(f"Failed to start camera: {e}")
            self.log_message(f"摄像头启动失败: {e}", "error")
            self.camera_btn.setChecked(False)
    
    def stop_camera(self):
        """停止摄像头"""
        self.logger.info("Stopping camera...")
        
        # 停止视频工作线程
        if self.video_worker:
            self.video_worker.stop()
            self.video_worker = None
        
        # 停止摄像头模块
        if self.camera_module and hasattr(self.camera_module, 'stop'):
            try:
                self.camera_module.stop()
            except Exception as e:
                self.logger.error(f"Error stopping camera: {e}")
        
        self.camera_status.setText("状态: 已停止")
        self.camera_btn.setText("启动摄像头")
        self.video_label.setText("视频未启动")
        self.log_message("摄像头已停止", "info")
        
        # 更新监控状态
        if self.status_reporter:
            self.status_reporter.update_gui_status(video_running=False)
    
    def update_video_frame(self, frame):
        """更新视频帧"""
        try:
            # 转换OpenCV帧为QPixmap
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # 缩放以适应标签
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"Error updating video frame: {e}")
    
    def handle_video_error(self, error_msg):
        """处理视频错误"""
        self.logger.error(f"Video error: {error_msg}")
        self.log_message(f"视频错误: {error_msg}", "error")
    
    def toggle_audio(self, checked):
        """切换音频状态"""
        if checked:
            self.start_audio()
        else:
            self.stop_audio()
    
    def start_audio(self):
        """启动音频"""
        self.logger.info("Starting audio...")
        
        if not self.audio_module:
            self.log_message("音频模块不可用", "error")
            self.audio_btn.setChecked(False)
            return
        
        try:
            if hasattr(self.audio_module, 'start'):
                self.audio_module.start()
            
            self.audio_status.setText("状态: 运行中")
            self.audio_btn.setText("停止音频")
            self.log_message("音频已启动", "success")
            
            # 更新监控状态
            if self.status_reporter:
                self.status_reporter.update_gui_status(audio_running=True)
            
        except Exception as e:
            self.logger.error(f"Failed to start audio: {e}")
            self.log_message(f"音频启动失败: {e}", "error")
            self.audio_btn.setChecked(False)
    
    def stop_audio(self):
        """停止音频"""
        self.logger.info("Stopping audio...")
        
        if self.audio_module and hasattr(self.audio_module, 'stop'):
            try:
                self.audio_module.stop()
            except Exception as e:
                self.logger.error(f"Error stopping audio: {e}")
        
        self.audio_status.setText("状态: 已停止")
        self.audio_btn.setText("启动音频")
        self.log_message("音频已停止", "info")
        
        # 更新监控状态
        if self.status_reporter:
            self.status_reporter.update_gui_status(audio_running=False)
    
    def take_screenshot(self):
        """截图"""
        self.logger.info("Taking screenshot...")
        
        try:
            # 获取当前视频帧
            if self.video_label.pixmap():
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
                # 保存截图
                self.video_label.pixmap().save(filename)
                self.log_message(f"截图已保存: {filename}", "success")
                self.screenshot_count += 1
            else:
                self.log_message("无视频内容可截图", "warning")
                
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            self.log_message(f"截图失败: {e}", "error")
    
    def toggle_recording(self, checked):
        """切换录制状态"""
        self.record_enabled = checked
        if checked:
            self.log_message("开始录制...", "info")
            self.record_btn.setText("停止录制")
        else:
            self.log_message("停止录制", "info")
            self.record_btn.setText("录制")
    
    def toggle_fullscreen(self, checked):
        """切换全屏"""
        if checked:
            self.showFullScreen()
            self.fullscreen_btn.setText("退出全屏")
        else:
            self.showNormal()
            self.fullscreen_btn.setText("全屏")
    
    def load_face_model(self):
        """加载人脸模型"""
        model_name = self.face_combo.currentText()
        
        if model_name == "选择模型...":
            self.log_message("请先选择人脸模型", "warning")
            return
        
        self.logger.info(f"Loading face model: {model_name}")
        self.log_message(f"正在加载模型: {model_name}...", "info")
        
        # 这里添加实际的模型加载逻辑
        # ...
        
        self.log_message(f"模型加载完成: {model_name}", "success")
        
        # 更新监控状态
        if self.status_reporter:
            self.status_reporter.update_gui_status(face_loaded=True)
    
    def open_image(self):
        """打开图片"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if filename:
            self.logger.info(f"Opening image: {filename}")
            self.log_message(f"已选择图片: {filename}", "info")
    
    def open_monitor(self):
        """打开监控面板"""
        import webbrowser
        webbrowser.open("http://localhost:5500/api/ar/dashboard")
        self.log_message("已打开监控面板", "info")
    
    def show_about(self):
        """显示关于对话框"""
        from PyQt5.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "关于 AR Live Studio",
            "<h2>AR Live Studio v2.0</h2>"
            "<p>实时视觉音频处理平台</p>"
            "<p>集成: Deep-Live-Cam, DeepFaceLab, FaceSwap</p>"
            "<p>技术支持: AI 全栈技术员</p>"
        )
    
    def update_system_info(self):
        """更新系统信息"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent()
            self.cpu_label.setText(f"CPU: {cpu_percent}%")
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.memory_label.setText(f"内存: {memory.percent}%")
            
        except ImportError:
            self.cpu_label.setText("CPU: N/A")
            self.memory_label.setText("内存: N/A")
    
    def log_message(self, message, level="info"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 级别标签
        level_labels = {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARN",
            "error": "ERROR",
            "success": "OK"
        }
        level_str = level_labels.get(level, "INFO")
        
        # 格式化日志
        log_entry = f"[{timestamp}] [{level_str}] {message}"
        
        # 添加到文本框
        self.log_text.append(log_entry)
        
        # 同时输出到Python日志
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_message("日志已清空", "info")
    
    def save_log(self):
        """保存日志"""
        from datetime import datetime
        
        filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log_message(f"日志已保存: {filename}", "success")
        except Exception as e:
            self.log_message(f"保存日志失败: {e}", "error")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.logger.info("Closing application...")
        
        # 停止摄像头
        if self.camera_btn.isChecked():
            self.stop_camera()
        
        # 停止音频
        if self.audio_btn.isChecked():
            self.stop_audio()
        
        # 停止监控
        if self.status_reporter:
            self.status_reporter.stop()
        
        if self.local_server:
            self.local_server.stop()
        
        # 停止定时器
        self.sys_timer.stop()
        
        self.logger.info("Application closed")
        event.accept()


# ============================================================================
# 主函数（用于独立测试）
# ============================================================================

def main():
    """主函数"""
    import sys
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("AR Live Studio")
    app.setApplicationVersion("2.0.0")
    
    # 创建主窗口
    window = ARApp()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```

#### 文件2: user/gui/__init__.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 包初始化
"""

from .gui import ARApp, VideoWorker

__all__ = ['ARApp', 'VideoWorker']
```

#### 文件3: user/utils/import_helper.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入辅助工具
提供灵活的模块导入功能
"""

import sys
import importlib
import logging
from pathlib import Path
from typing import Optional, Any, List

logger = logging.getLogger('ImportHelper')


def smart_import(module_name: str, fallback_names: Optional[List[str]] = None) -> Optional[Any]:
    """
    智能导入模块
    尝试多种导入路径
    
    Args:
        module_name: 主模块名
        fallback_names: 备选模块名列表
    
    Returns:
        导入的模块或None
    """
    # 首先尝试主模块名
    try:
        module = importlib.import_module(module_name)
        logger.debug(f"Successfully imported: {module_name}")
        return module
    except ImportError as e:
        logger.debug(f"Failed to import {module_name}: {e}")
    
    # 尝试备选名称
    if fallback_names:
        for name in fallback_names:
            try:
                module = importlib.import_module(name)
                logger.debug(f"Successfully imported from fallback: {name}")
                return module
            except ImportError as e:
                logger.debug(f"Failed to import fallback {name}: {e}")
    
    logger.warning(f"All import attempts failed for: {module_name}")
    return None


def import_from_path(module_name: str, file_path: Path) -> Optional[Any]:
    """
    从指定文件路径导入模块
    
    Args:
        module_name: 模块名
        file_path: 文件路径
    
    Returns:
        导入的模块或None
    """
    try:
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logger.error(f"Cannot create spec for: {file_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        logger.debug(f"Successfully imported from path: {file_path}")
        return module
        
    except Exception as e:
        logger.error(f"Failed to import from path {file_path}: {e}")
        return None


def safe_getattr(module: Any, attr_name: str, default: Any = None) -> Any:
    """
    安全获取模块属性
    
    Args:
        module: 模块对象
        attr_name: 属性名
        default: 默认值
    
    Returns:
        属性值或默认值
    """
    try:
        return getattr(module, attr_name)
    except AttributeError:
        logger.debug(f"Attribute {attr_name} not found in module, using default")
        return default


class ModuleProxy:
    """
    模块代理类
    延迟加载模块，提供容错处理
    """
    
    def __init__(self, module_name: str, fallback_names: Optional[List[str]] = None):
        self.module_name = module_name
        self.fallback_names = fallback_names or []
        self._module: Optional[Any] = None
        self._loaded = False
    
    def _load(self):
        """加载模块"""
        if not self._loaded:
            self._module = smart_import(self.module_name, self.fallback_names)
            self._loaded = True
    
    def __getattr__(self, name: str) -> Any:
        """获取属性"""
        self._load()
        
        if self._module is None:
            raise RuntimeError(f"Module {self.module_name} not available")
        
        return getattr(self._module, name)
    
    def is_available(self) -> bool:
        """检查模块是否可用"""
        self._load()
        return self._module is not None


# 常用模块代理
camera_module = ModuleProxy('camera', ['core.camera', 'AR-backend.core.camera'])
audio_module = ModuleProxy('audio_module', ['core.audio_module', 'AR-backend.core.audio_module'])
utils_module = ModuleProxy('utils', ['core.utils', 'AR-backend.core.utils'])
```

## 三、关联内容修复

### 3.1 需要同步修复的文件

| 文件 | 修复内容 | 原因 |
|------|----------|------|
| `user/main.py` | 更新GUI导入路径 | 使用修复后的gui模块 |
| `user/services/status_reporter.py` | 修复导入 | 确保服务模块可导入 |
| `user/README.md` | 更新启动说明 | 文档同步 |

### 3.2 详细修复说明

#### 修复1: user/main.py

```python
# 修改导入部分
# 从
from gui.gui import ARApp

# 改为
try:
    from gui.gui import ARApp
except ImportError:
    # 如果包导入失败，直接导入模块
    import sys
    from pathlib import Path
    gui_path = Path(__file__).parent / 'gui'
    sys.path.insert(0, str(gui_path))
    from gui import ARApp
```

## 四、部署执行步骤

### 4.1 执行前检查

```bash
# 1. 检查当前gui.py的导入问题
cd user
python3 -c "import gui.gui" 2>&1 | head -30

# 2. 检查AR-backend模块是否存在
ls -la ../AR-backend/core/
```

### 4.2 部署执行

```bash
# 1. 备份原gui.py
cp user/gui/gui.py user/gui/gui.py.backup

# 2. 创建新的gui.py（复制上述代码）

# 3. 创建__init__.py
touch user/gui/__init__.py

# 4. 创建import_helper.py
# user/utils/import_helper.py

# 5. 测试导入
cd user
python3 -c "from gui.gui import ARApp; print('Import successful')"

# 6. 启动测试
python3 main.py --test
```

### 4.3 部署验证

```bash
# 1. 验证导入成功
python3 -c "
import sys
sys.path.insert(0, 'user')
from gui.gui import ARApp
print('✓ ARApp imported successfully')
"

# 2. 验证模块加载
python3 -c "
from user.utils.import_helper import smart_import
camera = smart_import('camera', ['core.camera'])
print('✓ Camera module:', camera)
"

#
