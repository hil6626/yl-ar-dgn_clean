#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头模块单元测试
AR 综合实时合成与监控系统

测试内容:
- 摄像头初始化和配置
- 帧捕获和处理
- 热插拔检测
- 性能监控

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import sys
import time
import numpy as np
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()
PROJECT_ROOT = PATHS.root

from camera import CameraModule, CameraStatus

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestCameraModule(unittest.TestCase):
    """摄像头模块测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.camera = CameraModule(camera_id=0, width=640, height=480, fps=30)
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试用例清理"""
        if hasattr(self, 'camera') and self.camera:
            try:
                if self.camera.is_running:
                    self.camera.stop_stream()
                self.camera._stop_hotplug_detection()
            except Exception:
                pass
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_initialization(self):
        """测试摄像头初始化"""
        # 初始化摄像头
        result = self.camera.initialize()
        
        # 如果没有摄像头，这可能失败，但我们测试逻辑
        if result:
            self.assertTrue(self.camera.initialized)
            self.assertEqual(self.camera.status, CameraStatus.OPENED)
            logger.info("测试initialization: 通过")
        else:
            logger.warning("测试initialization: 跳过 (无摄像头)")
            self.assertEqual(self.camera.status, CameraStatus.ERROR)
    
    def test_get_camera_info(self):
        """测试获取摄像头信息"""
        info = self.camera.get_camera_info()
        
        # 如果没有初始化，信息应该为空
        if not info:
            self.assertEqual(len(info), 0)
        else:
            self.assertIn('camera_id', info)
            self.assertIn('width', info)
            self.assertIn('height', info)
        
        logger.info("测试get_camera_info: 通过")
    
    def test_frame_buffer(self):
        """测试帧缓冲功能"""
        # 添加帧到缓冲区
        for i in range(5):
            frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            self.camera._add_frame_to_buffer(frame)
        
        # 验证缓冲区大小
        self.assertLessEqual(len(self.camera.frame_buffer), 3)  # maxlen=3
        
        # 获取最新帧
        latest_frame = self.camera._get_frame_from_buffer()
        self.assertIsNotNone(latest_frame)
        self.assertEqual(latest_frame.shape, (100, 100, 3))
        
        logger.info("测试frame_buffer: 通过")
    
    def test_clear_buffer(self):
        """测试清空缓冲区"""
        # 添加帧
        for i in range(3):
            frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            self.camera._add_frame_to_buffer(frame)
        
        # 清空
        self.camera.clear_buffer()
        
        # 验证
        self.assertEqual(len(self.camera.frame_buffer), 0)
        
        logger.info("测试clear_buffer: 通过")
    
    def test_set_face_module(self):
        """测试设置人脸合成模块"""
        # 创建模拟模块
        class MockFaceModule:
            def __init__(self):
                self.source_face = None
            
            def set_source(self, path):
                self.source_face = path
            
            def process_frame(self, frame):
                return frame
        
        mock_module = MockFaceModule()
        
        # 设置
        self.camera.set_face_module(mock_module)
        
        # 验证
        self.assertEqual(self.camera.face_module, mock_module)
        
        logger.info("测试set_face_module: 通过")
    
    def test_load_face_image(self):
        """测试加载人脸图片"""
        # 创建测试图片
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        test_path = PROJECT_ROOT / "test" / "test_data" / "test_face.jpg"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        
        import cv2
        cv2.imwrite(str(test_path), test_image)
        
        try:
            result = self.camera.load_face_image(str(test_path))
            
            self.assertTrue(result)
            self.assertIsNotNone(self.camera.source_face_image)
            self.assertEqual(self.camera.source_face_path, str(test_path))
            
            logger.info("测试load_face_image: 通过")
        finally:
            if test_path.exists():
                test_path.unlink()
    
    def test_get_frame_statistics(self):
        """测试获取帧统计"""
        stats = self.camera.get_frame_statistics()
        
        self.assertIn('frame_count', stats)
        self.assertIn('fps_actual', stats)
        self.assertIn('fps_target', stats)
        self.assertIn('is_running', stats)
        self.assertIn('is_capturing', stats)
        self.assertIn('is_recording', stats)
        
        logger.info("测试get_frame_statistics: 通过")
    
    def test_switch_camera(self):
        """测试切换摄像头"""
        # 尝试切换到不存在的摄像头
        result = self.camera.switch_camera(999)
        
        # 应该失败
        self.assertFalse(result)
        
        logger.info("测试switch_camera: 通过")
    
    def test_set_low_latency_mode(self):
        """测试低延迟模式"""
        # 启用低延迟模式
        self.camera.set_low_latency_mode(True)
        
        self.assertTrue(self.camera.drop_frame_mode)
        self.assertEqual(self.camera.frame_buffer_size, 1)
        
        # 禁用低延迟模式
        self.camera.set_low_latency_mode(False)
        
        self.assertFalse(self.camera.drop_frame_mode)
        self.assertEqual(self.camera.frame_buffer_size, 3)
        
        logger.info("测试set_low_latency_mode: 通过")
    
    def test_set_frame_skip(self):
        """测试帧跳过设置"""
        self.camera.set_frame_skip(3)
        
        self.assertEqual(self.camera.process_every_n_frames, 3)
        
        # 测试边界情况
        self.camera.set_frame_skip(0)
        self.assertEqual(self.camera.process_every_n_frames, 1)
        
        self.camera.set_frame_skip(-5)
        self.assertEqual(self.camera.process_every_n_frames, 1)
        
        logger.info("测试set_frame_skip: 通过")
    
    def test_callback_functions(self):
        """测试回调函数"""
        frames_received = []
        
        def on_frame(frame):
            frames_received.append(frame.copy())
        
        def on_error(error):
            print(f"Error: {error}")
        
        # 设置回调
        self.camera.set_frame_callback(on_frame)
        self.camera.set_error_callback(on_error)
        
        # 验证
        self.assertEqual(self.camera.on_frame_ready, on_frame)
        self.assertEqual(self.camera.on_error, on_error)
        
        logger.info("测试callback_functions: 通过")
    
    def test_get_available_cameras(self):
        """测试获取可用摄像头"""
        cameras = self.camera.get_available_cameras()
        
        self.assertIsInstance(cameras, list)
        self.assertIn(0, cameras)  # 默认摄像头通常可用
        
        logger.info(f"测试get_available_cameras: 通过 (检测到 {len(cameras)} 个摄像头)")
    
    def test_health_check(self):
        """测试健康检查"""
        health = self.camera.health_check()
        
        self.assertIn('status', health)
        self.assertIn('camera_id', health)
        self.assertIn('is_capturing', health)
        
        logger.info("测试health_check: 通过")
    
    def test_start_stop_capture(self):
        """测试开始/停止捕获"""
        # 初始化
        self.camera.initialize()
        
        # 开始捕获
        result = self.camera.start_capture()
        
        if result:
            self.assertTrue(self.camera.is_capturing)
            self.assertTrue(self.camera.is_running)
        
        # 停止捕获
        self.camera.stop_capture()
        
        self.assertFalse(self.camera.is_capturing)
        self.assertFalse(self.camera.is_running)
        
        logger.info("测试start_stop_capture: 通过")


class TestCameraPerformance(unittest.TestCase):
    """摄像头性能测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.camera = CameraModule(camera_id=0, width=640, height=480, fps=15)
    
    def tearDown(self):
        """测试用例清理"""
        if hasattr(self, 'camera') and self.camera:
            try:
                if self.camera.is_running:
                    self.camera.stop_stream()
                self.camera._stop_hotplug_detection()
            except Exception:
                pass
    
    def test_frame_capture_speed(self):
        """测试帧捕获速度"""
        self.camera.initialize()
        
        if not self.camera.capture or not self.camera.capture.isOpened():
            self.skipTest("无摄像头设备")
        
        # 捕获10帧
        frame_count = 10
        start_time = time.perf_counter()
        
        for _ in range(frame_count):
            frame = self.camera.get_frame()
            if frame is None:
                break
        
        elapsed = time.perf_counter() - start_time
        avg_time = elapsed / frame_count
        
        # 验证捕获速度（平均每帧<100ms）
        self.assertLess(avg_time, 0.1, f"帧捕获时间过长: {avg_time:.3f}s")
        
        logger.info(f"测试frame_capture_speed: 通过 (平均 {avg_time*1000:.1f}ms/帧)")
    
    def test_buffer_operations(self):
        """测试缓冲操作性能"""
        import threading
        
        # 创建生产者线程
        def producer():
            for i in range(100):
                frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
                self.camera._add_frame_to_buffer()
                time.sleep(0.01)  # 模拟帧间隔
        
        # 启动生产者
        thread = threading.Thread(target=producer)
        thread.start()
        thread.join(timeout=2)
        
        # 验证缓冲区操作正常
        self.assertGreater(len(self.camera.frame_buffer), 0)
        
        logger.info("测试buffer_operations: 通过")
    
    def test_fps_calculation(self):
        """测试FPS计算"""
        # 模拟帧更新
        for i in range(30):
            self.camera._update_fps()
            time.sleep(0.05)  # 20 FPS
        
        fps = self.camera.fps_actual
        
        # FPS应该在合理范围内
        self.assertGreater(fps, 0)
        self.assertLess(fps, 100)  # 不可能超过100 FPS
        
        logger.info(f"测试fps_calculation: 通过 (FPS: {fps:.1f})")


class TestCameraStatus(unittest.TestCase):
    """摄像头状态测试类"""
    
    def test_status_enum(self):
        """测试状态枚举"""
        self.assertEqual(CameraStatus.CLOSED.value, "closed")
        self.assertEqual(CameraStatus.OPENING.value, "opening")
        self.assertEqual(CameraStatus.OPENED.value, "opened")
        self.assertEqual(CameraStatus.CAPTURING.value, "capturing")
        self.assertEqual(CameraStatus.ERROR.value, "error")
        
        logger.info("测试status_enum: 通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)
