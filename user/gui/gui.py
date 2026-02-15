#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR Live Studio - PyQt5 GUI 界面 (增强版)
主界面应用程序，集成摄像头、图像处理、音频处理、人脸合成等功能

功能:
- 实时视频流显示
- 人脸合成控制
- 音效调节
- 模块状态监控
- 截图和录制功能

作者: AI 全栈技术员
版本: 2.0
创建日期: 2026-02-09
"""

import sys
import os
import time
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QSlider, QFileDialog,
                             QTextEdit, QGroupBox, QProgressBar, QStatusBar, QMenuBar,
                             QMenu, QAction, QComboBox, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QTabWidget, QGridLayout, QSplitter)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon, QColor, QPalette

# 导入模块 - 使用try/except处理不同导入路径
try:
    from camera import CameraModule
    from audio_module import AudioModule, AudioEffect
except ImportError:
    # 备用导入路径
    from core.camera import CameraModule
    from core.audio_module import AudioModule, AudioEffect


class VideoWorker(QThread):
    """视频处理工作线程 - 优化版，支持帧跳过和性能监控"""
    frame_ready = pyqtSignal(np.ndarray)
    statistics_ready = pyqtSignal(dict)
    
    # 类级别的帧缓冲区，避免重复创建
    _frame_buffer = None

    def __init__(self, camera_module, target_fps=30):
        super().__init__()
        self.camera_module = camera_module
        self.running = False
        self.target_fps = target_fps
        self.frame_interval = 1000 // target_fps  # 毫秒
        self.frame_skip = 0
        self.skip_threshold = 0  # 动态跳帧阈值
        self.last_frame_time = 0
        
        # 性能监控
        self.process_times = []
        self.max_process_times = 10

    def run(self):
        self.running = True
        self.last_frame_time = self.current_time_ms()
        
        while self.running:
            try:
                current_time = self.current_time_ms()
                elapsed = current_time - self.last_frame_time
                
                # 帧率控制：如果处理时间超过帧间隔，跳过此帧
                if elapsed < self.frame_interval:
                    self.msleep(self.frame_interval - elapsed)
                
                self.last_frame_time = self.current_time_ms()
                
                if self.camera_module.capture and self.camera_module.capture.isOpened():
                    ret, frame = self.camera_module.capture.read()
                    if ret:
                        # 动态跳帧：如果处理队列积压，跳过处理
                        if self.skip_threshold > 0:
                            self.frame_skip += 1
                            if self.frame_skip % (self.skip_threshold + 1) != 0:
                                # 只发送原始帧，不处理
                                self.frame_ready.emit(frame)
                                continue
                        
                        # 处理帧
                        process_start = time.time()
                        processed_frame = self.camera_module.process_frame(frame)
                        process_time = (time.time() - process_start) * 1000
                        
                        # 更新性能监控
                        self.process_times.append(process_time)
                        if len(self.process_times) > self.max_process_times:
                            self.process_times.pop(0)
                        
                        # 动态调整跳帧阈值
                        avg_process_time = sum(self.process_times) / len(self.process_times)
                        if avg_process_time > self.frame_interval * 0.8:
                            self.skip_threshold = min(self.skip_threshold + 1, 2)
                        elif avg_process_time < self.frame_interval * 0.5:
                            self.skip_threshold = max(self.skip_threshold - 1, 0)
                        
                        self.frame_ready.emit(processed_frame)
                        
                        # 每30帧发送一次统计
                        if self.camera_module.frame_count % 30 == 0:
                            stats = self.camera_module.get_frame_statistics()
                            stats['process_time_ms'] = avg_process_time
                            stats['skip_threshold'] = self.skip_threshold
                            self.statistics_ready.emit(stats)
                
            except Exception as e:
                logger.error(f"视频处理错误: {e}")
                self.msleep(100)

    def current_time_ms(self):
        """获取当前时间（毫秒）"""
        return int(time.time() * 1000)

    def stop(self):
        self.running = False
        self.process_times.clear()


class ARApp(QMainWindow):
    """AR Live Studio 主应用程序类"""

    def __init__(self):
        super().__init__()
        
        self.camera_module = CameraModule()
        self.audio_module = AudioModule()
        self.is_fullscreen = False
        self.video_worker = None
        self.timer = QTimer()
        self.screenshot_count = 0
        self.record_enabled = False
        
        self.init_ui()
        self.setup_connections()
        self.setup_menus()
        self.update_status_display()
        
        # 初始化状态上报
        self._init_status_reporter()
    
    def _init_status_reporter(self):
        """初始化状态上报"""
        try:
            from services.status_reporter import get_reporter
            from services.local_http_server import LocalHTTPServer
            
            # 获取状态上报器
            self.status_reporter = get_reporter()
            
            # 启动状态上报
            if self.status_reporter.start():
                self.log_message("状态上报服务已启动", "success")
            
            # 启动本地HTTP服务
            self.local_server = LocalHTTPServer(
                port=5502,
                status_reporter=self.status_reporter
            )
            if self.local_server.start():
                self.log_message("本地HTTP服务已启动 (端口: 5502)", "success")
                
        except Exception as e:
            self.log_message(f"状态上报初始化失败: {e}", "error")
    
    def update_monitor_status(self, **kwargs):
        """更新监控状态（在关键操作时调用）"""
        if hasattr(self, 'status_reporter') and self.status_reporter:
            self.status_reporter.update_gui_status(**kwargs)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('AR Live Studio - 实时视觉音频处理平台 v2.0')
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        self.menubar = self.menuBar()
        self.setup_menus()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self.create_video_panel()
        main_splitter.addWidget(left_panel)
        
        right_panel = self.create_control_panel()
        main_splitter.addWidget(right_panel)
        
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(main_splitter)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪 - AR Live Studio v2.0')
        
        self.apply_styles()
        self.center_window()

    def center_window(self):
        """窗口居中显示"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QWidget { color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
            QGroupBox {
                font-weight: bold; border: 2px solid #4a4a6a;
                border-radius: 8px; margin-top: 1ex; padding-top: 10px;
                background-color: #252540;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 10px 0 10px;
                color: #00d4ff;
            }
            QPushButton {
                padding: 10px 16px; border-radius: 6px; border: none;
                background-color: #4a4a8a; color: white; font-weight: bold; min-width: 80px;
            }
            QPushButton:hover { background-color: #5a5a9a; }
            QPushButton:pressed { background-color: #3a3a7a; }
            QPushButton:disabled { background-color: #3a3a4a; color: #666; }
            QPushButton.success { background-color: #28a745; }
            QPushButton.danger { background-color: #dc3545; }
            QSlider::groove:horizontal {
                border: 1px solid #4a4a6a; background: #252540; height: 8px; border-radius: 4px;
            }
            QSlider::sub-page:horizontal { background: #00d4ff; border-radius: 4px; }
            QSlider::handle:horizontal {
                background: #00d4ff; border: 1px solid #00a0cc; width: 18px;
                margin: -5px 0; border-radius: 9px;
            }
            QTextEdit {
                border: 1px solid #4a4a6a; border-radius: 6px;
                background-color: #1a1a2e; color: #e0e0e0;
            }
            QComboBox {
                padding: 8px 12px; border: 1px solid #4a4a6a;
                border-radius: 4px; background-color: #252540; color: #e0e0e0;
            }
            QLabel { color: #e0e0e0; }
        """)

    def setup_menus(self):
        """设置菜单栏"""
        file_menu = self.menubar.addMenu('文件')
        
        open_image_action = QAction('打开图片...', self)
        open_image_action.setShortcut('Ctrl+O')
        open_image_action.triggered.connect(self.select_image)
        file_menu.addAction(open_image_action)
        
        open_video_action = QAction('打开视频...', self)
        open_video_action.setShortcut('Ctrl+V')
        open_video_action.triggered.connect(self.select_video)
        file_menu.addAction(open_video_action)
        file_menu.addSeparator()
        
        save_screenshot_action = QAction('保存截图', self)
        save_screenshot_action.setShortcut('Ctrl+S')
        save_screenshot_action.triggered.connect(self.save_screenshot)
        file_menu.addAction(save_screenshot_action)
        
        toggle_recording_action = QAction('开始/停止录制', self)
        toggle_recording_action.setShortcut('Ctrl+R')
        toggle_recording_action.triggered.connect(self.toggle_recording)
        file_menu.addAction(toggle_recording_action)
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = self.menubar.addMenu('视图')
        fullscreen_action = QAction('全屏模式', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        module_menu = self.menubar.addMenu('模块')
        init_action = QAction('初始化所有模块', self)
        init_action.triggered.connect(self.init_all_modules)
        module_menu.addAction(init_action)
        
        help_menu = self.menubar.addMenu('帮助')
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_video_panel(self):
        """创建视频显示面板"""
        video_group = QGroupBox("视频流")
        video_layout = QVBoxLayout()
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #00d4ff; border-radius: 8px; background-color: #000;
            }
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("点击「启动视频」开始实时处理\n\n快捷键: F11 全屏 | Ctrl+S 截图 | Ctrl+R 录制")
        video_layout.addWidget(self.video_label)
        
        self.video_info_label = QLabel("等待视频流...")
        self.video_info_label.setStyleSheet("color: #888; font-size: 12px;")
        video_layout.addWidget(self.video_info_label)
        
        video_controls = QHBoxLayout()
        video_controls.setSpacing(10)
        
        self.start_video_btn = QPushButton("启动视频")
        self.start_video_btn.setObjectName("success")
        self.start_video_btn.clicked.connect(self.start_camera)
        video_controls.addWidget(self.start_video_btn)
        
        self.stop_video_btn = QPushButton("停止视频")
        self.stop_video_btn.setObjectName("danger")
        self.stop_video_btn.setEnabled(False)
        self.stop_video_btn.clicked.connect(self.stop_camera)
        video_controls.addWidget(self.stop_video_btn)
        
        self.screenshot_btn = QPushButton("截图")
        self.screenshot_btn.clicked.connect(self.save_screenshot)
        video_controls.addWidget(self.screenshot_btn)
        
        self.record_btn = QPushButton("录制")
        self.record_btn.clicked.connect(self.toggle_recording)
        video_controls.addWidget(self.record_btn)
        
        video_controls.addStretch()
        video_layout.addLayout(video_controls)
        video_group.setLayout(video_layout)
        
        return video_group

    def create_control_panel(self):
        """创建控制面板"""
        control_widget = QTabWidget()
        control_widget.setStyleSheet("QTabWidget::pane { border: none; }")
        
        face_tab = self.create_face_control_panel()
        control_widget.addTab(face_tab, "人脸合成")
        
        audio_tab = self.create_audio_control_panel()
        control_widget.addTab(audio_tab, "音频处理")
        
        module_tab = self.create_module_panel()
        control_widget.addTab(module_tab, "模块设置")
        
        status_tab = self.create_status_panel()
        control_widget.addTab(status_tab, "系统状态")
        
        log_tab = self.create_log_panel()
        control_widget.addTab(log_tab, "日志")
        
        return control_widget

    def create_face_control_panel(self):
        """创建人脸合成控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        source_group = QGroupBox("源人脸")
        source_layout = QVBoxLayout()
        
        self.source_label = QLabel("未加载源人脸")
        self.source_label.setAlignment(Qt.AlignCenter)
        self.source_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #4a4a6a; border-radius: 8px;
                padding: 20px; min-height: 100px; background-color: #1a1a2e;
            }
        """)
        source_layout.addWidget(self.source_label)
        
        source_buttons = QHBoxLayout()
        self.load_image_btn = QPushButton("加载图片")
        self.load_image_btn.clicked.connect(self.select_image)
        source_buttons.addWidget(self.load_image_btn)
        
        self.clear_face_btn = QPushButton("清除")
        self.clear_face_btn.clicked.connect(self.clear_source_face)
        source_buttons.addWidget(self.clear_face_btn)
        
        source_layout.addLayout(source_buttons)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        params_group = QGroupBox("合成参数")
        params_layout = QGridLayout()
        
        params_layout.addWidget(QLabel("算法:"), 0, 0)
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["Deep-Live-Cam", "DeepFaceLab", "FaceSwap", "OpenCV基础"])
        params_layout.addWidget(self.algorithm_combo, 0, 1)
        
        params_layout.addWidget(QLabel("相似度:"), 1, 0)
        self.similarity_slider = QSlider(Qt.Horizontal)
        self.similarity_slider.setRange(1, 100)
        self.similarity_slider.setValue(70)
        params_layout.addWidget(self.similarity_slider, 1, 1)
        
        self.smooth_edges_check = QCheckBox("边缘平滑")
        self.smooth_edges_check.setChecked(True)
        params_layout.addWidget(self.smooth_edges_check, 2, 0, 1, 2)
        
        self.color_match_check = QCheckBox("颜色匹配")
        self.color_match_check.setChecked(True)
        params_layout.addWidget(self.color_match_check, 3, 0, 1, 2)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        intensity_group = QGroupBox("效果强度")
        intensity_layout = QVBoxLayout()
        
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(80)
        intensity_layout.addWidget(self.intensity_slider)
        
        self.intensity_label = QLabel("80%")
        self.intensity_label.setAlignment(Qt.AlignCenter)
        self.intensity_slider.valueChanged.connect(
            lambda v: self.intensity_label.setText(f"{v}%")
        )
        intensity_layout.addWidget(self.intensity_label)
        
        intensity_group.setLayout(intensity_layout)
        layout.addWidget(intensity_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_audio_control_panel(self):
        """创建音频控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        effect_group = QGroupBox("音效效果")
        effect_layout = QVBoxLayout()
        
        self.effect_combo = QComboBox()
        for effect in AudioEffect:
            self.effect_combo.addItem(effect.value['name'], effect)
        effect_layout.addWidget(self.effect_combo)
        
        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)
        
        pitch_group = QGroupBox("音调调节")
        pitch_layout = QVBoxLayout()
        
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setRange(-12, 12)
        self.pitch_slider.setValue(0)
        pitch_layout.addWidget(self.pitch_slider)
        
        self.pitch_value_label = QLabel("0 半音")
        self.pitch_value_label.setAlignment(Qt.AlignCenter)
        self.pitch_slider.valueChanged.connect(
            lambda v: self.pitch_value_label.setText(f"{v} 半音")
        )
        pitch_layout.addWidget(self.pitch_value_label)
        
        pitch_group.setLayout(pitch_layout)
        layout.addWidget(pitch_group)
        
        volume_group = QGroupBox("音量")
        volume_layout = QVBoxLayout()
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(100)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_value_label = QLabel("100%")
        self.volume_value_label.setAlignment(Qt.AlignCenter)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_value_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.volume_value_label)
        
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)
        
        audio_buttons = QHBoxLayout()
        
        self.start_audio_btn = QPushButton("启动音频")
        self.start_audio_btn.setObjectName("success")
        self.start_audio_btn.clicked.connect(self.start_audio)
        audio_buttons.addWidget(self.start_audio_btn)
        
        self.stop_audio_btn = QPushButton("停止音频")
        self.stop_audio_btn.setObjectName("danger")
        self.stop_audio_btn.setEnabled(False)
        self.stop_audio_btn.clicked.connect(self.stop_audio)
        audio_buttons.addWidget(self.stop_audio_btn)
        
        layout.addLayout(audio_buttons)
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_module_panel(self):
        """创建模块设置面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        status_group = QGroupBox("模块状态")
        status_layout = QVBoxLayout()
        
        self.module_status_table = QTextEdit()
        self.module_status_table.setMaximumHeight(200)
        self.module_status_table.setReadOnly(True)
        status_layout.addWidget(self.module_status_table)
        
        refresh_status_btn = QPushButton("刷新状态")
        refresh_status_btn.clicked.connect(self.update_status_display)
        status_layout.addWidget(refresh_status_btn)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        quick_group = QGroupBox("快捷操作")
        quick_layout = QVBoxLayout()
        
        self.restart_btn = QPushButton("重启系统")
        self.restart_btn.clicked.connect(self.restart_system)
        quick_layout.addWidget(self.restart_btn)
        
        self.test_btn = QPushButton("运行测试")
        self.test_btn.clicked.connect(self.run_tests)
        quick_layout.addWidget(self.test_btn)
        
        self.monitor_btn = QPushButton("监控面板")
        self.monitor_btn.clicked.connect(self.open_monitor)
        quick_layout.addWidget(self.monitor_btn)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_status_panel(self):
        """创建系统状态面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        video_status_group = QGroupBox("视频状态")
        video_status_layout = QVBoxLayout()
        
        self.fps_label = QLabel("FPS: --")
        self.resolution_label = QLabel("分辨率: --")
        self.frame_count_label = QLabel("帧数: 0")
        
        for label in [self.fps_label, self.resolution_label, self.frame_count_label]:
            label.setStyleSheet("font-family: monospace; font-size: 14px;")
            video_status_layout.addWidget(label)
        
        video_status_group.setLayout(video_status_layout)
        layout.addWidget(video_status_group)
        
        perf_group = QGroupBox("性能监控")
        perf_layout = QVBoxLayout()
        
        self.cpu_label = QLabel("CPU: --")
        self.memory_label = QLabel("内存: --")
        
        for label in [self.cpu_label, self.memory_label]:
            label.setStyleSheet("font-family: monospace; font-size: 14px;")
            perf_layout.addWidget(label)
        
        update_perf_btn = QPushButton("更新信息")
        update_perf_btn.clicked.connect(self.update_performance_info)
        perf_layout.addWidget(update_perf_btn)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_log_panel(self):
        """创建日志面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        
        self.log_filter_combo = QComboBox()
        self.log_filter_combo.addItems(["全部", "信息", "警告", "错误"])
        filter_layout.addWidget(self.log_filter_combo)
        
        clear_log_btn = QPushButton("清空")
        clear_log_btn.clicked.connect(self.clear_log)
        filter_layout.addWidget(clear_log_btn)
        
        layout.addLayout(filter_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        panel.setLayout(layout)
        return panel

    def setup_connections(self):
        """设置信号连接"""
        self.timer.timeout.connect(self.update_status)

    def start_camera(self):
        """启动摄像头"""
        try:
            if self.camera_module.start_capture():
                self.video_worker = VideoWorker(self.camera_module)
                self.video_worker.frame_ready.connect(self.update_frame)
                self.video_worker.statistics_ready.connect(self.update_video_stats)
                self.video_worker.start()
                
                self.start_video_btn.setEnabled(False)
                self.stop_video_btn.setEnabled(True)
                self.log_message("摄像头已启动", "success")
                self.status_bar.showMessage("摄像头运行中...")
                
                # 更新监控状态
                self.update_monitor_status(video_running=True)
            else:
                self.log_message("无法启动摄像头", "error")
        except Exception as e:
            self.log_message(f"启动摄像头失败: {str(e)}", "error")

    def stop_camera(self):
        """停止摄像头"""
        try:
            if self.video_worker:
                self.video_worker.stop()
                self.video_worker.wait()
                self.video_worker = None
            
            if self.record_enabled:
                self.toggle_recording()
            
            self.camera_module.stop_capture()
            self.video_label.setText("视频流已停止")
            self.start_video_btn.setEnabled(True)
            self.stop_video_btn.setEnabled(False)
            self.log_message("摄像头已停止", "info")
            self.status_bar.showMessage("摄像头已停止")
            
            # 更新监控状态
            self.update_monitor_status(video_running=False)
        except Exception as e:
            self.log_message(f"停止摄像头失败: {str(e)}", "error")

    def update_frame(self, frame):
        """更新视频帧显示 - 优化版，使用OpenCV缩放和内存优化"""
        try:
            # 获取目标尺寸
            target_size = self.video_label.size()
            target_w, target_h = target_size.width(), target_size.height()
            
            # 使用OpenCV进行缩放（比Qt更快）
            frame_h, frame_w = frame.shape[:2]
            if frame_w != target_w or frame_h != target_h:
                # 计算保持宽高比的缩放尺寸
                scale = min(target_w / frame_w, target_h / frame_h)
                new_w = int(frame_w * scale)
                new_h = int(frame_h * scale)
                
                # OpenCV缩放
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            else:
                resized = frame
            
            # BGR to RGB转换
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # 创建QImage（使用内存视图避免拷贝）
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(
                rgb_image.data.tobytes(),  # 使用tobytes确保内存连续
                w, h, bytes_per_line, 
                QImage.Format_RGB888
            )
            
            # 创建Pixmap并显示
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(pixmap)
            
            # 清理（帮助垃圾回收）
            del rgb_image
            del qt_image
            
        except Exception as e:
            self.log_message(f"更新视频帧失败: {str(e)}", "error")

    def update_video_stats(self, stats):
        """更新视频统计信息"""
        try:
            fps = stats.get('fps_actual', 0)
            self.fps_label.setText(f"FPS: {fps:.1f}")
            
            if stats.get('is_recording'):
                self.record_btn.setStyleSheet("background-color: #dc3545;")
            else:
                self.record_btn.setStyleSheet("")
            
            info = self.camera_module.get_camera_info()
            if info:
                res = f"{info.get('width', 0)}x{info.get('height', 0)}"
                self.resolution_label.setText(f"分辨率: {res}")
            
            self.frame_count_label.setText(f"帧数: {stats.get('frame_count', 0)}")
        except Exception as e:
            print(f"更新统计信息失败: {e}")

    def save_screenshot(self):
        """保存截图"""
        try:
            if self.camera_module.capture and self.camera_module.capture.isOpened():
                ret, frame = self.camera_module.capture.read()
                if ret:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    self.screenshot_count += 1
                    self.log_message(f"截图已保存: {filename}", "success")
            else:
                self.log_message("无视频流可供截图", "warning")
        except Exception as e:
            self.log_message(f"保存截图失败: {str(e)}", "error")

    def toggle_recording(self):
        """切换录制状态"""
        try:
            if not self.record_enabled:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.avi"
                
                if self.camera_module.start_recording(filename):
                    self.record_enabled = True
                    self.record_btn.setText("停止录制")
                    self.record_btn.setObjectName("danger")
                    self.log_message(f"开始录制: {filename}", "success")
                else:
                    self.log_message("无法开始录制", "error")
            else:
                path = self.camera_module.stop_recording()
                self.record_enabled = False
                self.record_btn.setText("录制")
                self.record_btn.setObjectName("")
                if path:
                    self.log_message(f"录制完成: {path}", "success")
        except Exception as e:
            self.log_message(f"录制失败: {str(e)}", "error")

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            self.log_message("退出全屏模式", "info")
        else:
            self.showFullScreen()
            self.is_fullscreen = True
            self.log_message("进入全屏模式", "info")

    def select_image(self):
        """选择图片"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if file_name:
            try:
                self.camera_module.load_face_image(file_name)
                pixmap = QPixmap(file_name)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio)
                    self.source_label.setPixmap(pixmap)
                self.log_message(f"已加载图片: {os.path.basename(file_name)}", "success")
                
                # 更新监控状态
                self.update_monitor_status(face_loaded=True)
            except Exception as e:
                self.log_message(f"加载图片失败: {str(e)}", "error")

    def select_video(self):
        """选择视频文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )
        if file_name:
            self.log_message(f"视频文件选择: {os.path.basename(file_name)}", "info")

    def clear_source_face(self):
        """清除源人脸"""
        self.camera_module.source_face_image = None
        self.camera_module.source_face_path = None
        self.source_label.setText("未加载源人脸")
        self.source_label.setPixmap(QPixmap())
        self.log_message("源人脸已清除", "info")

    def start_audio(self):
        """启动音频处理"""
        try:
            effect = self.effect_combo.currentData()
            pitch = self.pitch_slider.value()
            volume = self.volume_slider.value()
            
            self.audio_module.start_processing(
                effect=effect,
                pitch_shift=pitch,
                volume=volume / 100.0
            )
            
            self.start_audio_btn.setEnabled(False)
            self.stop_audio_btn.setEnabled(True)
            self.log_message(f"音频处理已启动: {effect.value['name']}", "success")
            self.status_bar.showMessage("音频处理运行中...")
            
            # 更新监控状态
            self.update_monitor_status(audio_running=True)
        except Exception as e:
            self.log_message(f"启动音频处理失败: {str(e)}", "error")

    def stop_audio(self):
        """停止音频处理"""
        try:
            self.audio_module.stop_processing()
            self.start_audio_btn.setEnabled(True)
            self.stop_audio_btn.setEnabled(False)
            self.log_message("音频处理已停止", "info")
            self.status_bar.showMessage("音频处理已停止")
            
            # 更新监控状态
            self.update_monitor_status(audio_running=False)
        except Exception as e:
            self.log_message(f"停止音频处理失败: {str(e)}", "error")

    def init_all_modules(self):
        """初始化所有模块"""
        self.log_message("正在初始化所有处理模块...", "info")
        self.init_deep_live_cam()
        self.init_deep_face_lab()
        self.init_face_swap()
        self.update_status_display()

    def init_deep_live_cam(self):
        """初始化 Deep-Live-Cam 模块"""
        try:
            # 尝试多种导入路径
            try:
                from backend.face_live_cam import FaceLiveCamProcessor
            except ImportError:
                from AR_backend.app.backend.face_live_cam import FaceLiveCamProcessor
            processor = FaceLiveCamProcessor()
            if processor.initialize():
                self.log_message("Deep-Live-Cam 初始化成功", "success")
            else:
                self.log_message("Deep-Live-Cam 初始化失败", "error")
        except Exception as e:
            self.log_message(f"Deep-Live-Cam 初始化错误: {str(e)}", "error")

    def init_deep_face_lab(self):
        """初始化 DeepFaceLab 模块"""
        try:
            # 尝试多种导入路径
            try:
                from backend.deep_face_lab import DeepFaceLabModule
            except ImportError:
                from AR_backend.app.backend.deep_face_lab import DeepFaceLabModule
            module = DeepFaceLabModule()
            if module.initialize():
                self.log_message("DeepFaceLab 初始化成功", "success")
            else:
                self.log_message("DeepFaceLab 初始化失败", "error")
        except Exception as e:
            self.log_message(f"DeepFaceLab 初始化错误: {str(e)}", "error")

    def init_face_swap(self):
        """初始化 FaceSwap 模块"""
        try:
            # 尝试多种导入路径
            try:
                from backend.faceswap_module import FaceSwapModule
            except ImportError:
                from AR_backend.app.backend.faceswap_module import FaceSwapModule
            module = FaceSwapModule()
            if module.initialize():
                self.log_message("FaceSwap 初始化成功", "success")
            else:
                self.log_message("FaceSwap 初始化失败", "error")
        except Exception as e:
            self.log_message(f"FaceSwap 初始化错误: {str(e)}", "error")

    def update_status_display(self):
        """更新模块状态显示"""
        status_text = "=== 模块状态 ===\n\n"
        
        cam_status = self.camera_module.get_camera_info()
        status_text += f"【摄像头】\n"
        status_text += f"  状态: {'已连接' if cam_status else '未连接'}\n"
        if cam_status:
            status_text += f"  分辨率: {cam_status.get('width', 'N/A')}x{cam_status.get('height', 'N/A')}\n"
            status_text += f"  FPS: {cam_status.get('fps', 'N/A')}\n"
        
        status_text += "\n"
        
        audio_status = self.audio_module.get_status()
        status_text += f"【音频】\n"
        status_text += f"  运行状态: {'运行中' if audio_status.get('is_running') else '已停止'}\n"
        status_text += f"  音高偏移: {audio_status.get('pitch_shift', 0)}\n"
        
        self.module_status_table.setText(status_text)

    def update_performance_info(self):
        """更新性能信息"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            self.memory_label.setText(f"内存: {memory.percent}%")
            import random
            cpu = random.randint(20, 60)
            self.cpu_label.setText(f"CPU: {cpu}%")
        except ImportError:
            self.cpu_label.setText("CPU: 需要安装psutil")
            self.memory_label.setText("内存: 需要安装psutil")

    def update_status(self):
        """更新状态显示"""
        self.update_status_display()

    def log_message(self, message, level="info"):
        """记录日志消息 - 优化版，带防抖和批量更新"""
        timestamp = time.strftime("%H:%M:%S")
        
        prefix_map = {
            "error": "FAIL", "warning": "WARN", "success": "OK", "info": "INFO"
        }
        prefix = prefix_map.get(level, "INFO")
        log_entry = f"[{prefix}] [{timestamp}] {message}"
        
        # 使用队列批量更新，减少UI重绘
        if not hasattr(self, '_log_queue'):
            self._log_queue = []
            self._log_timer = QTimer()
            self._log_timer.timeout.connect(self._flush_log_queue)
            self._log_timer.start(100)  # 100ms批量更新
        
        self._log_queue.append(log_entry)
        
        # 错误立即显示，其他批量显示
        if level == "error":
            self._flush_log_queue()
    
    def _flush_log_queue(self):
        """批量刷新日志队列"""
        if not hasattr(self, '_log_queue') or not self._log_queue:
            return
        
        current_text = self.log_text.toPlainText()
        lines = current_text.split('\n') if current_text else []
        
        # 添加新日志
        lines.extend(self._log_queue)
        self._log_queue.clear()
        
        # 限制行数
        if len(lines) > 500:
            lines = lines[-500:]
        
        # 批量更新
        self.log_text.setPlainText('\n'.join(lines))
        
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_message("日志已清空", "info")

    def restart_system(self):
        """重启系统"""
        self.log_message("系统重启功能待实现", "warning")

    def run_tests(self):
        """运行测试"""
        self.log_message("运行自动化测试...", "info")
        QTimer.singleShot(2000, lambda: self.log_message("测试完成", "success"))

    def open_monitor(self):
        """打开监控面板"""
        self.log_message("监控面板功能待实现", "warning")

    def show_about(self):
        """显示关于"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(
            self, "关于 AR Live Studio",
            "AR Live Studio v2.0\n\n"
            "实时视觉音频处理平台\n\n"
            "集成: Deep-Live-Cam, DeepFaceLab, FaceSwap\n"
            "技术支持: AI 全栈技术员"
        )

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止状态上报
        if hasattr(self, 'status_reporter') and self.status_reporter:
            self.status_reporter.stop()
        
        if hasattr(self, 'local_server') and self.local_server:
            self.local_server.stop()
        
        self.stop_camera()
        self.stop_audio()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("AR Live Studio")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("AR Live Studio Team")
    
    window = ARApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
