"""
摄像头视频处理模块
负责捕获摄像头视频流，进行实时人脸合成处理
增强版本：添加帧缓冲管理、热插拔检测、低延迟处理

作者: AI 全栈技术员
版本: 1.1
创建日期: 2026年1月30日
最后更新: 2026年2月9日
"""

import cv2
import numpy as np
import time
import threading
import logging
from typing import Optional, Tuple, List, Dict, Callable, Any
from pathlib import Path
from collections import deque
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)


class CameraStatus(Enum):
    """摄像头状态枚举"""
    CLOSED = "closed"
    OPENING = "opening"
    OPENED = "opened"
    CAPTURING = "capturing"
    ERROR = "error"


class CameraModule:
    """
    摄像头模块类
    处理摄像头视频流的捕获、处理和输出
    增强版本：添加帧缓冲管理、热插拔检测、低延迟处理
    """

    def __init__(self, camera_id: int = 0, width: int = 1920, height: int = 1080, fps: int = 30):
        """
        初始化摄像头模块

        Args:
            camera_id: 摄像头设备ID
            width: 视频宽度
            height: 视频高度
            fps: 帧率
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps

        self.capture: Optional[cv2.VideoCapture] = None
        self.face_module = None  # 人脸合成模块（待集成）
        self.is_running = False
        self.is_capturing = False
        self.status = CameraStatus.CLOSED
        
        # 人脸图片相关
        self.source_face_image: Optional[np.ndarray] = None
        self.source_face_path: Optional[str] = None
        
        # 帧统计
        self.frame_count = 0
        self.fps_actual = 0.0
        self.last_frame_time = time.time()
        self.fps_update_interval = 1.0  # 每秒更新一次FPS
        
        # 帧缓冲管理
        self.frame_buffer_size = 3  # 缓冲帧数
        self.frame_buffer: deque = deque(maxlen=3)
        self.buffer_lock = threading.Lock()
        
        # 低延迟处理
        self.process_every_n_frames = 1  # 每N帧处理一次
        self.frame_skip_counter = 0
        self.drop_frame_mode = False  # 丢帧模式用于高延迟
        
        # 回调函数
        self.on_frame_ready: Optional[Callable[[np.ndarray], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # 多摄像头支持
        self.available_cameras: List[int] = []
        self._detect_available_cameras()
        
        # 视频录制
        self.video_writer = None
        self.is_recording = False
        self.record_path: Optional[str] = None
        
        # 热插拔检测
        self.hotplug_detection_enabled = False
        self.hotplug_thread: Optional[threading.Thread] = None
        self.hotplug_running = False
        
        # GPU加速
        self.gpu_enabled = False
        self.gpu_frame = None
        
        # 性能监控
        self.process_time_avg = 0.0
        self.process_time_total = 0.0
        self.frame_latency = 0.0
        
        logger.info(f"CameraModule 初始化完成: camera_id={camera_id}, resolution={width}x{height}, fps={fps}")

    def _detect_available_cameras(self) -> List[int]:
        """
        检测可用的摄像头设备
        
        Returns:
            List[int]: 可用的摄像头设备ID列表
        """
        available = []
        for i in range(10):  # 检测前10个设备
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        self.available_cameras = available
        return available

    def get_available_cameras(self) -> List[int]:
        """
        获取可用的摄像头列表
        
        Returns:
            List[int]: 可用的摄像头设备ID列表
        """
        return self._detect_available_cameras()

    def initialize(self) -> bool:
        """
        初始化摄像头
        优化版本：添加GPU支持和错误处理

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.status = CameraStatus.OPENING
            logger.info(f"正在初始化摄像头 {self.camera_id}...")
            
            self.capture = cv2.VideoCapture(self.camera_id)

            if not self.capture.isOpened():
                logger.error(f"无法打开摄像头 {self.camera_id}")
                self.status = CameraStatus.ERROR
                return False

            # 设置摄像头参数
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # 尝试启用硬件加速
            self._try_hardware_acceleration()

            self.status = CameraStatus.OPENED
            logger.info(f"摄像头 {self.camera_id} 初始化成功")
            logger.info(f"  分辨率: {self.width}x{self.height}, FPS: {self.fps}")
            logger.info(f"  GPU加速: {'启用' if self.gpu_enabled else '禁用'}")
            return True

        except Exception as e:
            logger.error(f"摄像头初始化失败: {e}")
            self.status = CameraStatus.ERROR
            return False
    
    def _try_hardware_acceleration(self) -> None:
        """尝试启用硬件加速"""
        try:
            # 尝试D3D11后端 (Windows)
            self.capture.set(cv2.CAP_PROP_DC1394_USE_LOW_IMPLEMENTATION, 1)
            
            # 检查是否支持硬件加速
            if hasattr(cv2, 'CAP_FFMPEG'):
                # 尝试设置硬件加速
                self.capture.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                
            self.gpu_enabled = True
            logger.info("硬件加速已启用")
        except Exception as e:
            logger.warning(f"硬件加速启用失败: {e}")
            self.gpu_enabled = False
    
    def _add_frame_to_buffer(self, frame: np.ndarray) -> None:
        """将帧添加到缓冲区"""
        with self.buffer_lock:
            self.frame_buffer.append(frame.copy())
    
    def _get_frame_from_buffer(self) -> Optional[np.ndarray]:
        """从缓冲区获取最新帧"""
        with self.buffer_lock:
            if len(self.frame_buffer) > 0:
                return self.frame_buffer[-1]
        return None
    
    def clear_buffer(self) -> None:
        """清空帧缓冲区"""
        with self.buffer_lock:
            self.frame_buffer.clear()
        logger.info("帧缓冲区已清空")

    def start_stream(self) -> None:
        """
        开始视频流处理
        优化版本：添加热插拔检测和性能监控
        """
        if not self.capture or not self.capture.isOpened():
            logger.error("摄像头未初始化")
            return

        self.is_running = True
        self.status = CameraStatus.CAPTURING
        logger.info("开始视频流处理...")

        # 启动热插拔检测
        self._start_hotplug_detection()

        try:
            frame_interval = 1.0 / self.fps
            last_frame_time = time.time()
            
            while self.is_running:
                current_time = time.time()
                elapsed = current_time - last_frame_time
                
                # 控制帧率
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                
                last_frame_time = time.time()
                
                ret, frame = self.capture.read()
                if not ret:
                    logger.warning("无法读取视频帧")
                    if self.drop_frame_mode:
                        continue
                    else:
                        break

                # 添加帧到缓冲区
                self._add_frame_to_buffer(frame)
                
                # 处理帧（可配置跳过）
                self.frame_skip_counter += 1
                should_process = (
                    self.frame_skip_counter >= self.process_every_n_frames
                )
                
                if should_process:
                    self.frame_skip_counter = 0
                    
                    # 处理视频帧
                    process_start = time.time()
                    processed_frame = self._process_frame_internal(frame)
                    process_time = time.time() - process_start
                    
                    # 更新性能统计
                    self._update_performance_stats(process_time)
                    
                    # 录制
                    if self.is_recording and self.video_writer:
                        self.video_writer.write(processed_frame)
                    
                    # 显示处理后的帧
                    cv2.imshow('AR Live Studio - Camera', processed_frame)
                    
                    # 回调
                    if self.on_frame_ready:
                        self.on_frame_ready(processed_frame)
                else:
                    # 显示原始帧
                    cv2.imshow('AR Live Studio - Camera', frame)

                # 更新FPS
                self._update_fps()

                # 按 'q' 键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            logger.error(f"视频流处理错误: {e}")
            if self.on_error:
                self.on_error(str(e))
        finally:
            self.stop_stream()
    
    def _process_frame_internal(self, frame: np.ndarray) -> np.ndarray:
        """内部帧处理 - 已集成人脸合成功能"""
        try:
            start_time = time.time()
            
            # 集成人脸合成处理 - 已启用
            if self.face_module is not None and self.source_face_image is not None:
                try:
                    # 使用人脸合成模块处理帧
                    if hasattr(self.face_module, 'process_frame'):
                        frame = self.face_module.process_frame(frame)
                    elif hasattr(self.face_module, 'swap_face'):
                        # 备选：使用swap_face方法
                        frame = self.face_module.swap_face(frame, self.source_face_image)
                except Exception as e:
                    logger.warning(f"人脸合成处理失败，使用原始帧: {e}")
                    # 失败时使用原始帧，确保视频流不中断
            
            # 添加时间戳和状态信息
            timestamp = cv2.getTickCount() / cv2.getTickFrequency()
            
            # 显示FPS
            cv2.putText(frame, f"FPS: {self.fps_actual:.1f}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 显示延迟
            if self.frame_latency > 0:
                cv2.putText(frame, f"Latency: {self.frame_latency*1000:.1f}ms",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 显示处理时间
            cv2.putText(frame, f"Process: {self.process_time_avg*1000:.1f}ms",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 显示时间戳
            cv2.putText(frame, f"Time: {timestamp:.2f}s",
                       (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            return frame
            
        except Exception as e:
            logger.error(f"帧处理错误: {e}")
            return frame
    
    def _update_performance_stats(self, process_time: float) -> None:
        """更新性能统计"""
        self.frame_count += 1
        self.process_time_total += process_time
        self.process_time_avg = self.process_time_total / self.frame_count
        self.frame_latency = process_time
    
    def _start_hotplug_detection(self) -> None:
        """启动热插拔检测"""
        if self.hotplug_detection_enabled:
            return
            
        self.hotplug_detection_enabled = True
        self.hotplug_running = True
        self.hotplug_thread = threading.Thread(target=self._hotplug_detection_loop, daemon=True)
        self.hotplug_thread.start()
        logger.info("热插拔检测已启动")
    
    def _stop_hotplug_detection(self) -> None:
        """停止热插拔检测"""
        self.hotplug_running = False
        self.hotplug_detection_enabled = False
        if self.hotplug_thread and self.hotplug_thread.is_alive():
            self.hotplug_thread.join(timeout=1)
        logger.info("热插拔检测已停止")
    
    def _hotplug_detection_loop(self) -> None:
        """热插拔检测循环"""
        last_cameras = set(self.available_cameras)
        
        while self.hotplug_running:
            try:
                time.sleep(2)  # 每2秒检测一次
                
                # 检测当前可用摄像头
                current_cameras = set(self._detect_available_cameras())
                
                # 检测新设备
                new_cameras = current_cameras - last_cameras
                removed_cameras = last_cameras - current_cameras
                
                if new_cameras:
                    logger.info(f"检测到新摄像头: {new_cameras}")
                    self.available_cameras = list(current_cameras)
                
                if removed_cameras:
                    logger.warning(f"摄像头已断开: {removed_cameras}")
                    # 如果当前使用的摄像头断开，尝试切换
                    if self.camera_id in removed_cameras:
                        logger.warning("当前摄像头断开，尝试切换...")
                        for cam_id in current_cameras:
                            if cam_id != self.camera_id:
                                self.switch_camera(cam_id)
                                break
                    self.available_cameras = list(current_cameras)
                
                last_cameras = current_cameras
                
            except Exception as e:
                logger.error(f"热插拔检测错误: {e}")
    
    def set_low_latency_mode(self, enabled: bool, max_fps: int = 60) -> None:
        """
        设置低延迟模式
        
        Args:
            enabled: 是否启用低延迟模式
            max_fps: 最大帧率
        """
        self.drop_frame_mode = enabled
        if enabled:
            self.process_every_n_frames = 1
            self.frame_buffer_size = 1
            logger.info(f"低延迟模式已启用 (max_fps={max_fps})")
        else:
            self.process_every_n_frames = 1
            self.frame_buffer_size = 3
            logger.info("低延迟模式已禁用")
    
    def set_frame_skip(self, skip_frames: int) -> None:
        """
        设置帧跳过间隔
        
        Args:
            skip_frames: 每处理skip_frames帧跳过一次
        """
        self.process_every_n_frames = max(1, skip_frames)
        logger.info(f"帧跳过间隔设置为: {skip_frames}")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理单个视频帧 - 已集成人脸合成

        Args:
            frame: 输入视频帧

        Returns:
            np.ndarray: 处理后的视频帧
        """
        try:
            # 集成人脸合成处理
            if self.face_module is not None and self.source_face_image is not None:
                try:
                    if hasattr(self.face_module, 'process_frame'):
                        frame = self.face_module.process_frame(frame)
                    elif hasattr(self.face_module, 'swap_face'):
                        frame = self.face_module.swap_face(frame, self.source_face_image)
                except Exception as e:
                    logger.warning(f"人脸合成处理失败: {e}")
            
            # 添加时间戳和状态信息
            timestamp = cv2.getTickCount() / cv2.getTickFrequency()
            cv2.putText(frame, f"AR Live Studio - {timestamp:.2f}s",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            return frame

        except Exception as e:
            logger.error(f"帧处理错误: {e}")
            return frame

    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取单帧图像

        Returns:
            Optional[np.ndarray]: 视频帧，如果失败返回None
        """
        if not self.capture or not self.capture.isOpened():
            return None

        ret, frame = self.capture.read()
        if ret:
            return self.process_frame(frame)
        return None

    def set_face_module(self, face_module) -> bool:
        """
        设置人脸合成模块 - 增强版，带验证

        Args:
            face_module: 人脸合成模块实例

        Returns:
            bool: 设置是否成功
        """
        try:
            if face_module is None:
                logger.warning("人脸合成模块为None")
                return False
            
            # 验证模块接口
            required_methods = ['process_frame']
            optional_methods = ['swap_face', 'set_source', 'initialize']
            
            available_methods = [m for m in required_methods + optional_methods 
                               if hasattr(face_module, m)]
            
            if len(available_methods) < len(required_methods):
                logger.error(f"人脸合成模块缺少必要方法: {required_methods}")
                return False
            
            self.face_module = face_module
            
            # 如果已加载源人脸，自动设置到模块
            if self.source_face_image is not None and hasattr(face_module, 'set_source'):
                try:
                    if self.source_face_path:
                        face_module.set_source(self.source_face_path)
                except Exception as e:
                    logger.warning(f"设置源人脸到模块失败: {e}")
            
            logger.info(f"人脸合成模块已设置，可用方法: {available_methods}")
            return True
            
        except Exception as e:
            logger.error(f"设置人脸合成模块失败: {e}")
            return False

    def stop_stream(self) -> None:
        """
        停止视频流处理
        """
        self.is_running = False

        if self.capture and self.capture.isOpened():
            self.capture.release()

        cv2.destroyAllWindows()
        print("视频流处理已停止")

    def get_camera_info(self) -> dict:
        """
        获取摄像头信息

        Returns:
            dict: 摄像头参数信息
        """
        if not self.capture:
            return {}

        return {
            'camera_id': self.camera_id,
            'width': int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.capture.get(cv2.CAP_PROP_FPS)),
            'is_opened': self.capture.isOpened()
        }

    def start_capture(self) -> bool:
        """
        开始视频捕获（供GUI调用）

        Returns:
            bool: 是否成功开始捕获
        """
        if self.is_capturing:
            return True
            
        if not self.capture:
            if not self.initialize():
                return False
        
        self.is_capturing = True
        self.is_running = True
        print(f"视频捕获已启动，摄像头: {self.camera_id}")
        return True

    def stop_capture(self) -> None:
        """
        停止视频捕获（供GUI调用）
        """
        self.is_capturing = False
        self.is_running = False
        print("视频捕获已停止")

    def load_face_image(self, image_path: str) -> bool:
        """
        加载人脸图片用于合成（供GUI调用）- 增强版，带验证

        Args:
            image_path: 图片路径

        Returns:
            bool: 是否加载成功
        """
        try:
            # 参数验证
            if not image_path or not isinstance(image_path, str):
                logger.error("图片路径无效")
                return False
            
            path = Path(image_path)
            if not path.exists():
                logger.error(f"图片文件不存在: {image_path}")
                return False
            
            # 检查文件类型
            valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
            if path.suffix.lower() not in valid_extensions:
                logger.error(f"不支持的图片格式: {path.suffix}")
                return False
            
            # 检查文件大小 (最大10MB)
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                logger.warning(f"图片文件过大: {file_size / 1024 / 1024:.2f}MB")
            
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"无法读取图片: {image_path}")
                return False
            
            # 验证图片内容
            if image.size == 0 or image.shape[0] < 10 or image.shape[1] < 10:
                logger.error(f"图片尺寸无效: {image.shape}")
                return False
            
            self.source_face_image = image
            self.source_face_path = image_path
            
            logger.info(f"已加载人脸图片: {image_path} ({image.shape[1]}x{image.shape[0]})")
            
            # 如果有人脸合成模块，设置源图像
            if self.face_module is not None and hasattr(self.face_module, 'set_source'):
                try:
                    self.face_module.set_source(image_path)
                    logger.info("已同步源人脸到合成模块")
                except Exception as e:
                    logger.warning(f"设置源人脸到模块失败: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"加载人脸图片失败: {e}")
            return False

    def get_source_face(self) -> Optional[np.ndarray]:
        """
        获取已加载的源人脸图像

        Returns:
            Optional[np.ndarray]: 源人脸图像
        """
        return self.source_face_image

    def start_recording(self, output_path: str, fourcc: str = 'XVID', fps: int = 30) -> bool:
        """
        开始视频录制

        Args:
            output_path: 输出文件路径
            fourcc: 视频编码器
            fps: 帧率

        Returns:
            bool: 是否成功开始录制
        """
        if self.is_recording:
            return True
            
        if not self.capture or not self.capture.isOpened():
            print("摄像头未启动，无法录制")
            return False
        
        try:
            # 获取实际帧大小
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 创建视频写入器
            fourcc_obj = cv2.VideoWriter_fourcc(*fourcc)
            self.video_writer = cv2.VideoWriter(output_path, fourcc_obj, fps, (width, height))
            
            if not self.video_writer.isOpened():
                print(f"无法创建视频写入器: {output_path}")
                return False
            
            self.record_path = output_path
            self.is_recording = True
            print(f"开始录制视频: {output_path}")
            return True
            
        except Exception as e:
            print(f"开始录制失败: {e}")
            return False

    def stop_recording(self) -> Optional[str]:
        """
        停止视频录制

        Returns:
            Optional[str]: 录制文件路径，如果未录制则返回None
        """
        if not self.is_recording:
            return None
        
        try:
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            self.is_recording = False
            print(f"录制完成: {self.record_path}")
            path = self.record_path
            self.record_path = None
            return path
            
        except Exception as e:
            print(f"停止录制失败: {e}")
            return None

    def _update_fps(self) -> float:
        """
        更新实际帧率统计

        Returns:
            float: 当前实际帧率
        """
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        
        if elapsed >= self.fps_update_interval:
            self.fps_actual = self.frame_count / elapsed
            self.frame_count = 0
            self.last_frame_time = current_time
        
        return self.fps_actual

    def get_frame_statistics(self) -> Dict:
        """
        获取帧统计信息

        Returns:
            Dict: 统计信息字典
        """
        return {
            'frame_count': self.frame_count,
            'fps_actual': self.fps_actual,
            'fps_target': self.fps,
            'is_running': self.is_running,
            'is_capturing': self.is_capturing,
            'is_recording': self.is_recording,
            'source_face_loaded': self.source_face_image is not None,
            'process_time_avg': self.process_time_avg,
            'frame_latency': self.frame_latency
        }
    
    def health_check(self) -> Dict:
        """
        健康检查

        Returns:
            Dict: 健康状态信息
        """
        return {
            'name': 'CameraModule',
            'status': self.status.value,
            'camera_id': self.camera_id,
            'resolution': f'{self.width}x{self.height}',
            'fps': self.fps,
            'fps_actual': self.fps_actual,
            'is_capturing': self.is_capturing,
            'is_recording': self.is_recording,
            'gpu_enabled': self.gpu_enabled,
            'buffer_size': len(self.frame_buffer)
        }

    def switch_camera(self, camera_id: int) -> bool:
        """
        切换摄像头

        Args:
            camera_id: 新的摄像头设备ID

        Returns:
            bool: 是否切换成功
        """
        if camera_id == self.camera_id:
            return True
        
        # 停止当前捕获
        self.stop_stream()
        
        # 切换摄像头
        self.camera_id = camera_id
        self.capture = None
        
        # 初始化新摄像头
        if self.initialize():
            print(f"已切换到摄像头: {camera_id}")
            return True
        else:
            print(f"无法切换到摄像头: {camera_id}")
            return False

    def set_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """
        设置帧回调函数

        Args:
            callback: 帧处理回调函数
        """
        self.on_frame_ready = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置错误回调函数

        Args:
            callback: 错误处理回调函数
        """
        self.on_error = callback

    def __del__(self):
        """
        析构函数，确保资源释放
        """
        self.stop_stream()
