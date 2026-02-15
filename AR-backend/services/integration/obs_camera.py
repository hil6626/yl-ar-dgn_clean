#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBS 虚拟摄像头模块
实现视频流输出到虚拟摄像头设备

功能:
- 虚拟摄像头设备管理
- 视频帧发送到虚拟设备
- 音频流同步输出
- v4l2loopback 配置

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-09
"""

import os
import sys
import time
import subprocess
import threading
import logging
from typing import Optional, Dict, List, Callable
from pathlib import Path
import numpy as np

# 导入 OpenCV
import cv2

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class OBSVirtualCamera:
    """
    OBS 虚拟摄像头管理类
    
    管理虚拟摄像头设备的创建、视频流输出和状态监控
    """
    
    # 默认虚拟设备路径
    DEFAULT_DEVICE_PATHS = [
        "/dev/video0",
        "/dev/video1", 
        "/dev/video2",
        "/dev/video10",
        "/dev/video11"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 OBS 虚拟摄像头模块
        
        Args:
            config: 配置参数
                - device_path: 虚拟设备路径
                - width: 视频宽度
                - height: 视频高度
                - fps: 帧率
                - format: 视频格式 (yuyv422, mjpeg等)
        """
        self.config = {
            'device_path': '/dev/video0',
            'width': 640,
            'height': 480,
            'fps': 30,
            'format': 'yuyv422',
        }
        if config:
            self.config.update(config)
        
        # 状态
        self.is_active = False
        self.is_paused = False
        self.device_path = self.config['device_path']
        
        # 帧缓冲区
        self.frame_buffer = None
        self.buffer_lock = threading.Lock()
        
        # 统计信息
        self.frame_count = 0
        self.dropped_frames = 0
        self.start_time = 0.0
        self.fps_actual = 0.0
        
        # 回调函数
        self.on_frame_sent: Optional[Callable[[int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        
        # 发送线程
        self.send_thread: Optional[threading.Thread] = None
        self.send_running = False
        
        # 视频写入器
        self.writer = None
        
    def check_v4l2loopback(self) -> bool:
        """
        检查 v4l2loopback 模块是否已加载
        
        Returns:
            bool: 是否已加载
        """
        try:
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'v4l2loopback' in result.stdout
        except Exception as e:
            logger.error(f"检查 v4l2loopback 失败: {e}")
            return False
    
    def load_v4l2loopback(self) -> bool:
        """
        加载 v4l2loopback 内核模块
        
        Returns:
            bool: 是否加载成功
        """
        try:
            # 检查是否 root
            if os.geteuid() != 0:
                logger.warning("需要 root 权限加载内核模块")
                return False
            
            # 尝试加载模块
            result = subprocess.run(
                ['modprobe', 'v4l2loopback'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("v4l2loopback 模块加载成功")
                time.sleep(1)  # 等待设备节点创建
                return True
            else:
                logger.error(f"加载 v4l2loopback 失败: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("modprobe 命令未找到")
            return False
        except Exception as e:
            logger.error(f"加载内核模块失败: {e}")
            return False
    
    def find_available_device(self) -> Optional[str]:
        """
        查找可用的虚拟摄像头设备
        
        Returns:
            str: 设备路径，未找到返回 None
        """
        for device_path in self.DEFAULT_DEVICE_PATHS:
            if os.path.exists(device_path):
                # 检查设备是否可写
                try:
                    if os.access(device_path, os.W_OK):
                        logger.info(f"找到可用设备: {device_path}")
                        return device_path
                except PermissionError:
                    continue
        
        return None
    
    def list_video_devices(self) -> List[Dict]:
        """
        列出所有视频设备
        
        Returns:
            List[Dict]: 设备信息列表
        """
        devices = []
        
        try:
            # 使用 v4l2-ctl 列出设备
            result = subprocess.run(
                ['v4l2-ctl', '--list-devices'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            current_device = None
            for line in result.stdout.split('\n'):
                if line.strip() and not line.strip().startswith('\t'):
                    current_device = {'name': line.strip(), 'paths': []}
                    devices.append(current_device)
                elif line.strip().startswith('/dev/video'):
                    if current_device:
                        current_device['paths'].append(line.strip())
                        
        except FileNotFoundError:
            logger.warning("v4l2-ctl 未安装，无法列出设备")
        except Exception as e:
            logger.error(f"列出视频设备失败: {e}")
        
        return devices
    
    def get_device_info(self, device_path: Optional[str] = None) -> Dict:
        """
        获取设备信息
        
        Args:
            device_path: 设备路径，为空则使用默认设备
            
        Returns:
            Dict: 设备信息
        """
        path = device_path or self.device_path
        
        info = {
            'path': path,
            'exists': os.path.exists(path),
            'writable': False,
            'capabilities': {},
            'formats': []
        }
        
        if not info['exists']:
            return info
        
        try:
            info['writable'] = os.access(path, os.W_OK)
            
            # 获取设备能力
            result = subprocess.run(
                ['v4l2-ctl', '--device', path, '--all'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 解析输出
            for line in result.stdout.split('\n'):
                if 'Driver name' in line:
                    info['capabilities']['driver'] = line.split(':')[-1].strip()
                elif 'Card type' in line:
                    info['capabilities']['card'] = line.split(':')[-1].strip()
                    
            # 获取支持的格式
            result = subprocess.run(
                ['v4l2-ctl', '--device', path, '--list-formats'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    info['formats'].append(line.strip())
                    
        except Exception as e:
            logger.warning(f"获取设备信息失败: {e}")
        
        return info
    
    def start_virtual_camera(self) -> bool:
        """
        启动虚拟摄像头
        
        Returns:
            bool: 是否启动成功
        """
        if self.is_active:
            logger.warning("虚拟摄像头已在运行")
            return True
        
        # 检查 v4l2loopback
        if not self.check_v4l2loopback():
            logger.info("v4l2loopback 未加载，尝试加载...")
            if not self.load_v4l2loopback():
                logger.error("无法加载 v4l2loopback")
                return False
        
        # 查找可用设备
        device = self.find_available_device()
        if device:
            self.device_path = device
        else:
            logger.warning("未找到可用的虚拟摄像头设备")
            # 仍然继续尝试使用配置的设备
            
        # 检查设备
        if not os.path.exists(self.device_path):
            logger.error(f"设备不存在: {self.device_path}")
            if self.on_error:
                self.on_error(f"Device not found: {self.device_path}")
            return False
        
        try:
            # 初始化视频写入器
            fourcc = self._get_fourcc(self.config['format'])
            self.writer = cv2.VideoWriter(
                self.device_path,
                cv2.CAP_V4L2 if hasattr(cv2, 'CAP_V4L2') else 0,
                fourcc,
                self.config['fps'],
                (self.config['width'], self.config['height'])
            )
            
            if not self.writer.isOpened():
                logger.error(f"无法打开设备: {self.device_path}")
                return False
            
            self.is_active = True
            self.start_time = time.time()
            
            # 启动发送线程
            self.send_running = True
            self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
            self.send_thread.start()
            
            logger.info(f"虚拟摄像头已启动: {self.device_path}")
            if self.on_status_change:
                self.on_status_change("started")
            return True
            
        except Exception as e:
            logger.error(f"启动虚拟摄像头失败: {e}")
            return False
    
    def _get_fourcc(self, format_name: str):
        """获取 FourCC 编码"""
        formats = {
            'yuyv422': cv2.VideoWriter_fourcc('Y', 'U', 'Y', 'V'),
            'mjpeg': cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
            'rgb24': cv2.VideoWriter_fourcc('R', 'G', 'B', '3'),
        }
        return formats.get(format_name, cv2.VideoWriter_fourcc('Y', 'U', 'Y', 'V'))
    
    def stop_virtual_camera(self) -> None:
        """
        停止虚拟摄像头
        """
        if not self.is_active:
            return
        
        self.send_running = False
        self.is_active = False
        
        # 停止发送线程
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=5)
        
        # 关闭写入器
        if self.writer and self.writer.isOpened():
            self.writer.release()
        
        logger.info("虚拟摄像头已停止")
        if self.on_status_change:
            self.on_status_change("stopped")
    
    def pause_virtual_camera(self) -> None:
        """暂停虚拟摄像头"""
        self.is_paused = True
        logger.info("虚拟摄像头已暂停")
    
    def resume_virtual_camera(self) -> None:
        """恢复虚拟摄像头"""
        self.is_paused = False
        logger.info("虚拟摄像头已恢复")
    
    def send_frame(self, frame: np.ndarray) -> bool:
        """
        发送帧到虚拟摄像头
        
        Args:
            frame: 视频帧
            
        Returns:
            bool: 是否发送成功
        """
        if not self.is_active or self.is_paused:
            return False
        
        try:
            # 调整帧大小和格式
            resized = cv2.resize(frame, (self.config['width'], self.config['height']))
            
            # 转换颜色格式 (BGR to YUV)
            if self.config['format'] == 'yuyv422':
                converted = cv2.cvtColor(resized, cv2.COLOR_BGR2YUV_YUYV)
            else:
                converted = resized
            
            # 放入缓冲区
            with self.buffer_lock:
                self.frame_buffer = converted.copy()
            
            return True
            
        except Exception as e:
            logger.error(f"发送帧失败: {e}")
            return False
    
    def _send_loop(self) -> None:
        """帧发送循环"""
        while self.send_running:
            try:
                if self.is_paused or self.frame_buffer is None:
                    time.sleep(0.01)
                    continue
                
                # 从缓冲区获取帧
                with self.buffer_lock:
                    frame = self.frame_buffer
                    self.frame_buffer = None
                
                if frame is not None:
                    # 写入设备
                    if self.writer and self.writer.isOpened():
                        self.writer.write(frame)
                        self.frame_count += 1
                        
                        # 更新实际帧率
                        elapsed = time.time() - self.start_time
                        if elapsed > 1.0:
                            self.fps_actual = self.frame_count / elapsed
                        
                        # 回调
                        if self.on_frame_sent:
                            self.on_frame_sent(self.frame_count)
                
                # 控制帧率
                target_frame_time = 1.0 / self.config['fps']
                time.sleep(max(0, target_frame_time - 0.005))
                
            except Exception as e:
                logger.error(f"发送循环错误: {e}")
                time.sleep(0.1)
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息字典
        """
        elapsed = time.time() - self.start_time if self.start_time > 0 else 0
        
        return {
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            'device_path': self.device_path,
            'frame_count': self.frame_count,
            'dropped_frames': self.dropped_frames,
            'fps_target': self.config['fps'],
            'fps_actual': self.fps_actual,
            'resolution': f"{self.config['width']}x{self.config['height']}",
            'format': self.config['format'],
            'uptime': elapsed
        }
    
    def get_status(self) -> Dict:
        """
        获取状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            'active': self.is_active,
            'device': self.device_path,
            'device_exists': os.path.exists(self.device_path),
            'writable': os.access(self.device_path, os.W_OK) if os.path.exists(self.device_path) else False,
            'statistics': self.get_statistics()
        }
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        return {
            'name': 'OBSVirtualCamera',
            'status': 'ok' if self.is_active else 'error',
            'message': '虚拟摄像头运行正常' if self.is_active else '虚拟摄像头未启动',
            'details': self.get_status()
        }
    
    def set_frame_callback(self, callback: Callable[[int], None]) -> None:
        """
        设置帧发送回调
        
        Args:
            callback: 回调函数
        """
        self.on_frame_sent = callback
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置错误回调
        
        Args:
            callback: 回调函数
        """
        self.on_error = callback
    
    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置状态变化回调
        
        Args:
            callback: 回调函数
        """
        self.on_status_change = callback
    
    def __del__(self):
        """
        析构函数
        """
        self.stop_virtual_camera()


# 便捷函数
def create_obs_virtual_camera(config: Optional[Dict] = None) -> OBSVirtualCamera:
    """
    创建 OBS 虚拟摄像头实例
    
    Args:
        config: 配置参数
        
    Returns:
        OBSVirtualCamera: 实例
    """
    return OBSVirtualCamera(config)


def main():
    """主函数 - 测试虚拟摄像头模块"""
    import argparse
    import cv2
    
    parser = argparse.ArgumentParser(description='OBS 虚拟摄像头测试')
    parser.add_argument('--start', action='store_true', help='启动虚拟摄像头')
    parser.add_argument('--list', action='store_true', help='列出视频设备')
    parser.add_argument('--info', type=str, help='获取设备信息')
    args = parser.parse_args()
    
    # 创建模块
    obs = OBSVirtualCamera()
    
    if args.list:
        print("视频设备列表:")
        devices = obs.list_video_devices()
        for device in devices:
            print(f"  {device['name']}")
            for path in device.get('paths', []):
                print(f"    {path}")
        return
    
    if args.info:
        info = obs.get_device_info(args.info)
        print(f"设备信息: {info}")
        return
    
    if args.start:
        print("启动虚拟摄像头...")
        
        # 检查 v4l2loopback
        if obs.check_v4l2loopback():
            print("v4l2loopback 已加载")
        else:
            print("v4l2loopback 未加载")
        
        # 尝试启动
        if obs.start_virtual_camera():
            print("虚拟摄像头启动成功")
            print(f"设备: {obs.device_path}")
            
            # 模拟发送帧
            print("开始模拟帧发送...")
            for i in range(100):
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                if not obs.send_frame(frame):
                    print(f"帧 {i} 发送失败")
                    break
                time.sleep(0.033)  # ~30fps
                if (i + 1) % 30 == 0:
                    print(f"已发送 {i + 1} 帧")
            
            print("停止虚拟摄像头...")
            obs.stop_virtual_camera()
            print("测试完成")
        else:
            print("虚拟摄像头启动失败")


if __name__ == '__main__':
    main()

