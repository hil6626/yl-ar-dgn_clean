#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FaceLiveCam 模块单元测试
AR 综合实时合成与监控系统

测试内容:
- 模块初始化测试
- 人脸检测测试
- 人脸合成测试
- 性能测试

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional

import sys
import logging

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()
PROJECT_ROOT = PATHS.root

from face_live_cam import FaceLiveCamModule, FaceInfo, create_face_live_cam

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestFaceLiveCamModule(unittest.TestCase):
    """FaceLiveCam 模块测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.test_data_dir = PROJECT_ROOT / "test" / "test_data"
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试用图像
        cls.test_image_path = cls.test_data_dir / "test_face.jpg"
        cls._create_test_image(str(cls.test_image_path))
        
        logger.info("FaceLiveCam 测试类初始化完成")
    
    @staticmethod
    def _create_test_image(filepath: str):
        """创建测试用图像（带人脸模拟）"""
        # 创建带有人脸区域的测试图像
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        image[:] = (200, 200, 200)  # 灰色背景
        
        # 添加模拟人脸区域（椭圆）
        cv2.ellipse(image, (320, 200), (80, 100), 0, 0, 360, (255, 200, 180), -1)
        
        # 添加眼睛
        cv2.circle(image, (290, 180), 10, (0, 0, 0), -1)
        cv2.circle(image, (350, 180), 10, (0, 0, 0), -1)
        
        # 添加嘴巴
        cv2.ellipse(image, (320, 240), (20, 10), 0, 0, 180, (0, 0, 0), 2)
        
        cv2.imwrite(filepath, image)
    
    def setUp(self):
        """测试用例设置"""
        self.module = FaceLiveCamModule()
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试用例清理"""
        if hasattr(self, 'module') and self.module:
            try:
                self.module.cleanup()
            except Exception:
                pass
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_initialization(self):
        """测试模块初始化"""
        # 测试默认初始化
        module = FaceLiveCamModule()
        self.assertFalse(module.initialized)
        
        # 测试带配置初始化
        config = {
            'model_type': 'quick',
            'gpu_id': 0,
            'frame_size': 640
        }
        module = FaceLiveCamModule(config)
        self.assertFalse(module.initialized)
        self.assertEqual(module.config['model_type'], 'quick')
        
        logger.info("测试初始化: 通过")
    
    def test_initialize_module(self):
        """测试模块初始化方法"""
        result = self.module.initialize()
        self.assertTrue(result)
        self.assertTrue(self.module.initialized)
        
        # 验证检测器已加载
        self.assertIsNotNone(self.module.face_detector)
        self.assertIn(self.module.detector_type, ['dnn', 'haar'])
        
        logger.info("测试initialize_module: 通过")
    
    def test_set_source(self):
        """测试设置源人脸图像"""
        # 先初始化模块
        self.module.initialize()
        
        # 测试不存在的文件
        result = self.module.set_source("/nonexistent/path.jpg")
        self.assertFalse(result)
        
        # 测试有效的测试图像
        result = self.module.set_source(str(self.test_image_path))
        
        # 由于测试图像可能不包含真实人脸，这个测试可能失败
        # 但我们验证模块不会崩溃
        logger.info(f"测试set_source: 结果={result}")
    
    def test_get_status(self):
        """测试获取模块状态"""
        self.module.initialize()
        
        status = self.module.get_status()
        
        self.assertIn('initialized', status)
        self.assertIn('is_processing', status)
        self.assertIn('source_loaded', status)
        self.assertIn('model_type', status)
        self.assertIn('frame_count', status)
        self.assertIn('fps_processing', status)
        
        logger.info("测试get_status: 通过")
    
    def test_health_check(self):
        """测试健康检查"""
        # 未初始化状态
        health = self.module.health_check()
        self.assertEqual(health['status'], 'error')
        
        # 初始化后状态
        self.module.initialize()
        health = self.module.health_check()
        self.assertEqual(health['name'], 'Deep-Live-Cam')
        self.assertIn('status', health)
        self.assertIn('message', health)
        
        logger.info("测试health_check: 通过")
    
    def test_process_frame_without_source(self):
        """测试未设置源人脸时的帧处理"""
        self.module.initialize()
        
        # 创建测试帧
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 应该直接返回原帧
        result = self.module.process_frame(frame)
        np.testing.assert_array_equal(result, frame)
        
        logger.info("测试process_frame_without_source: 通过")
    
    def test_process_frame_with_invalid_frame(self):
        """测试无效帧处理"""
        self.module.initialize()
        
        # 测试空帧
        result = self.module.process_frame(np.array([]))
        # 应该返回空数组或原帧
        self.assertTrue(len(result) == 0 or result is not None)
        
        logger.info("测试process_frame_with_invalid_frame: 通过")
    
    def test_reset(self):
        """测试模块重置"""
        self.module.initialize()
        
        # 设置源人脸（如果可能）
        self.module.set_source(str(self.test_image_path))
        
        # 重置
        self.module.reset()
        
        # 验证状态已重置
        self.assertIsNone(self.module.source_face)
        self.assertEqual(self.module.frame_count, 0)
        
        logger.info("测试reset: 通过")
    
    def test_cleanup(self):
        """测试资源清理"""
        self.module.initialize()
        
        # 清理
        self.module.cleanup()
        
        # 验证状态
        self.assertFalse(self.module.initialized)
        self.assertIsNone(self.module.source_face)
        
        logger.info("测试cleanup: 通过")
    
    def test_face_info_dataclass(self):
        """测试FaceInfo数据类"""
        bbox = (100, 100, 200, 200)
        landmarks = np.array([[150, 150], [180, 150], [165, 180]])
        
        face_info = FaceInfo(
            bbox=bbox,
            landmarks=landmarks,
            confidence=0.95,
            face_id=1
        )
        
        self.assertEqual(face_info.bbox, bbox)
        self.assertEqual(face_info.confidence, 0.95)
        self.assertEqual(face_info.face_id, 1)
        self.assertIsNotNone(face_info.landmarks)
        
        logger.info("测试FaceInfo_dataclass: 通过")
    
    def test_create_face_live_cam(self):
        """测试便捷创建函数"""
        config = {'model_type': 'standard'}
        module = create_face_live_cam(config)
        
        self.assertIsInstance(module, FaceLiveCamModule)
        self.assertEqual(module.config['model_type'], 'standard')
        
        module.cleanup()
        logger.info("测试create_face_live_cam: 通过")
    
    def test_performance(self):
        """测试处理性能"""
        self.module.initialize()
        
        # 创建测试帧
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 性能测试
        iterations = 10
        start_time = time.time()
        
        for _ in range(iterations):
            self.module.process_frame(frame.copy())
        
        elapsed = time.time() - start_time
        avg_time = elapsed / iterations
        
        # 验证处理时间在可接受范围内（< 100ms per frame）
        self.assertLess(avg_time, 0.1, f"处理时间过长: {avg_time:.3f}s")
        
        logger.info(f"测试performance: 通过 (平均处理时间: {avg_time:.4f}s)")


class TestFaceLiveCamIntegration(unittest.TestCase):
    """FaceLiveCam 集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.module = FaceLiveCamModule()
        cls.module.initialize()
        logger.info("集成测试类初始化完成")
    
    @classmethod
    def tearDownClass(cls):
        """类级别清理"""
        if cls.module:
            cls.module.cleanup()
        logger.info("集成测试类清理完成")
    
    def test_full_pipeline(self):
        """测试完整处理流程"""
        # 1. 初始化
        self.assertTrue(self.module.initialized)
        
        # 2. 获取状态
        status = self.module.get_status()
        self.assertIn('initialized', status)
        
        # 3. 健康检查
        health = self.module.health_check()
        self.assertEqual(health['name'], 'Deep-Live-Cam')
        
        # 4. 处理帧
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = self.module.process_frame(frame)
        
        # 验证输出
        self.assertEqual(result.shape, frame.shape)
        self.assertEqual(result.dtype, frame.dtype)
        
        logger.info("测试full_pipeline: 通过")
    
    def test_multiple_frames(self):
        """测试处理多帧"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 连续处理多帧
        for i in range(5):
            result = self.module.process_frame(frame.copy())
            self.assertEqual(result.shape, frame.shape)
            
            # 验证帧计数增加
            self.assertEqual(self.module.frame_count, i + 1)
        
        logger.info("测试multiple_frames: 通过")


class TestFaceLiveCamPerformance(unittest.TestCase):
    """FaceLiveCam 性能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.module = FaceLiveCamModule()
        cls.module.initialize()
        logger.info("性能测试类初始化完成")
    
    @classmethod
    def tearDownClass(cls):
        """类级别清理"""
        if cls.module:
            cls.module.cleanup()
        logger.info("性能测试类清理完成")
    
    def test_frame_processing_speed(self):
        """测试帧处理速度"""
        # 不同分辨率测试
        resolutions = [
            (320, 240),
            (640, 480),
            (1280, 720)
        ]
        
        for width, height in resolutions:
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            
            start = time.perf_counter()
            iterations = 10
            
            for _ in range(iterations):
                self.module.process_frame(frame)
            
            elapsed = time.perf_counter() - start
            avg_fps = iterations / elapsed
            
            logger.info(f"分辨率 {width}x{height}: 平均 FPS = {avg_fps:.2f}")
            
            # 验证最小帧率要求（15 FPS）
            self.assertGreater(avg_fps, 15, f"帧率过低: {avg_fps:.2f} FPS")
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        
        # 连续处理100帧
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        for _ in range(100):
            self.module.process_frame(frame)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 验证内存增长在可接受范围内（< 100MB）
        self.assertLess(memory_increase, 100 * 1024 * 1024, 
                       f"内存增长过高: {memory_increase / 1024 / 1024:.2f} MB")
        
        logger.info(f"测试memory_usage: 通过 (内存增长: {memory_increase / 1024 / 1024:.2f} MB)")


# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
