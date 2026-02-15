#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faceswap 模块单元测试
AR 综合实时合成与监控系统

测试内容:
- 模块初始化测试
- 人脸检测测试
- 人脸交换测试
- 性能测试

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import time
import numpy as np
from pathlib import Path

import sys

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()
PROJECT_ROOT = PATHS.root

from faceswap_module import FaceSwapModule, create_face_swap

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestFaceSwapModule(unittest.TestCase):
    """Faceswap 模块测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.test_data_dir = PROJECT_ROOT / "test" / "test_data"
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Faceswap 测试类初始化完成")
    
    def setUp(self):
        """测试用例设置"""
        self.module = FaceSwapModule()
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
        module = FaceSwapModule()
        self.assertFalse(module.initialized)
        
        # 测试带配置初始化
        config = {
            'align_eyes': True,
            'smooth_edges': True,
            'color_adjust': 'histogram',
            'face_size': 256
        }
        module = FaceSwapModule(config)
        self.assertFalse(module.initialized)
        self.assertEqual(module.config['align_eyes'], True)
        self.assertEqual(module.config['smooth_edges'], True)
        self.assertEqual(module.config['color_adjust'], 'histogram')
        
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
    
    def test_get_status(self):
        """测试获取模块状态"""
        self.module.initialize()
        
        status = self.module.get_status()
        
        self.assertIn('initialized', status)
        self.assertIn('is_processing', status)
        self.assertIn('source_loaded', status)
        self.assertIn('frame_count', status)
        self.assertIn('avg_process_time', status)
        self.assertIn('config', status)
        
        logger.info("测试get_status: 通过")
    
    def test_health_check(self):
        """测试健康检查"""
        # 未初始化状态
        health = self.module.health_check()
        self.assertEqual(health['status'], 'error')
        
        # 初始化后状态
        self.module.initialize()
        health = self.module.health_check()
        self.assertEqual(health['name'], 'FaceSwap')
        self.assertIn('status', health)
        self.assertIn('message', health)
        
        logger.info("测试health_check: 通过")
    
    def test_set_parameter(self):
        """测试设置参数"""
        self.module.initialize()
        
        # 设置参数
        self.module.set_parameter('align_eyes', False)
        self.module.set_parameter('smooth_edges', False)
        self.module.set_parameter('color_adjust', 'none')
        
        # 验证参数已更改
        self.assertEqual(self.module.config['align_eyes'], False)
        self.assertEqual(self.module.config['smooth_edges'], False)
        self.assertEqual(self.module.config['color_adjust'], 'none')
        
        logger.info("测试set_parameter: 通过")
    
    def test_get_parameters(self):
        """测试获取参数"""
        self.module.initialize()
        
        params = self.module.get_parameters()
        
        self.assertIn('align_eyes', params)
        self.assertIn('smooth_edges', params)
        self.assertIn('color_adjust', params)
        self.assertIn('face_size', params)
        self.assertIn('blend_alpha', params)
        
        logger.info("测试get_parameters: 通过")
    
    def test_process_frame_without_source(self):
        """测试未设置源人脸时的帧处理"""
        self.module.initialize()
        
        # 创建测试帧
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 应该直接返回原帧
        result = self.module.process_frame(frame)
        np.testing.assert_array_equal(result, frame)
        
        logger.info("测试process_frame_without_source: 通过")
    
    def test_swap_faces(self):
        """测试人脸交换"""
        self.module.initialize()
        
        # 创建源和目标图像
        source = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        target = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 交换人脸
        result = self.module.swap_faces(source, target)
        
        # 验证输出
        self.assertEqual(result.shape, target.shape)
        self.assertEqual(result.dtype, target.dtype)
        
        logger.info("测试swap_faces: 通过")
    
    def test_color_match(self):
        """测试颜色匹配功能"""
        self.module.initialize()
        
        # 创建源和目标
        source = np.ones((100, 100, 3), dtype=np.uint8) * 100
        target = np.ones((100, 100, 3), dtype=np.uint8) * 150
        
        # 颜色匹配
        result = self.module._match_colors(source, target)
        
        # 验证结果
        self.assertEqual(result.shape, source.shape)
        self.assertEqual(result.dtype, source.dtype)
        
        logger.info("测试color_match: 通过")
    
    def test_face_mask_creation(self):
        """测试人脸掩码创建"""
        self.module.initialize()
        
        # 测试带关键点的掩码
        size = (100, 100)
        landmarks = np.array([
            [30, 35],  # left_eye
            [70, 35],  # right_eye
            [50, 50],  # nose
            [50, 75],  # mouth
            [25, 75],  # left_mouth
            [75, 75],  # right_mouth
        ], dtype=np.float32)
        
        mask = self.module._create_face_mask(size, landmarks)
        
        # 验证结果
        self.assertEqual(mask.shape, size)
        self.assertEqual(mask.dtype, np.uint8)
        
        logger.info("测试face_mask_creation: 通过")
    
    def test_reset(self):
        """测试模块重置"""
        self.module.initialize()
        
        # 模拟一些状态
        self.module.frame_count = 10
        self.module.process_time_total = 5.0
        
        # 重置
        self.module.reset()
        
        # 验证状态已重置
        self.assertIsNone(self.module.source_face)
        self.assertIsNone(self.module.source_landmarks)
        self.assertEqual(self.module.frame_count, 0)
        self.assertEqual(self.module.process_time_total, 0)
        
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
    
    def test_create_face_swap(self):
        """测试便捷创建函数"""
        config = {'face_size': 128}
        module = create_face_swap(config)
        
        self.assertIsInstance(module, FaceSwapModule)
        self.assertEqual(module.config['face_size'], 128)
        
        module.cleanup()
        logger.info("测试create_face_swap: 通过")
    
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


class TestFaceSwapPerformance(unittest.TestCase):
    """Faceswap 性能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.module = FaceSwapModule()
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
            
            # 验证最小帧率要求（10 FPS）
            self.assertGreater(avg_fps, 10, f"帧率过低: {avg_fps:.2f} FPS")
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        
        # 连续处理50帧
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        for _ in range(50):
            self.module.process_frame(frame)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 验证内存增长在可接受范围内（< 100MB）
        self.assertLess(memory_increase, 100 * 1024 * 1024, 
                       f"内存增长过高: {memory_increase / 1024 / 1024:.2f} MB")
        
        logger.info(f"测试memory_usage: 通过 (内存增长: {memory_increase / 1024 / 1024:.2f} MB)")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
