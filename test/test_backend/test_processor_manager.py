#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理器管理器单元测试
AR 综合实时合成与监控系统

测试内容:
    - 处理器注册与卸载
    - 流水线执行
    - 错误恢复机制
    - 性能统计

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

from processor_manager import (
    ProcessorManager, BaseProcessor, OpenCVProcessor
)

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestProcessorManager(unittest.TestCase):
    """处理器管理器测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.manager = ProcessorManager()
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试用例清理"""
        if hasattr(self, 'manager') and self.manager:
            try:
                self.manager.cleanup()
            except Exception:
                pass
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_initialization(self):
        """测试管理器初始化"""
        # 验证处理器已注册
        self.assertGreater(len(self.manager.processors), 0)
        
        # 验证默认处理器存在
        self.assertIn('opencv', self.manager.processors)
        self.assertIn('face_live_cam', self.manager.processors)
        self.assertIn('sox', self.manager.processors)
        
        logger.info("测试initialization: 通过")
    
    def test_register_processor(self):
        """测试处理器注册"""
        # 创建自定义处理器
        class TestProcessor(BaseProcessor):
            def _load_model(self):
                self.model_path = "test_model"
            
            def process(self, input_data, **kwargs):
                return {"success": True, "data": input_data}
        
        # 注册新处理器
        self.manager.register('test', TestProcessor, {})
        
        # 验证已注册
        self.assertIn('test', self.manager.processors)
        self.assertIsInstance(self.manager.get_processor('test'), TestProcessor)
        
        logger.info("测试register_processor: 通过")
    
    def test_unregister_processor(self):
        """测试处理器卸载"""
        # 卸载opencv处理器
        result = self.manager.unregister('opencv')
        
        # 验证已卸载
        self.assertTrue(result)
        self.assertNotIn('opencv', self.manager.processors)
        
        logger.info("测试unregister_processor: 通过")
    
    def test_initialize_all(self):
        """测试初始化所有处理器"""
        results = self.manager.initialize_all()
        
        # 验证每个处理器初始化结果
        for name, success in results.items():
            if name in ['opencv', 'face_live_cam', 'sox']:
                self.assertTrue(success, f"处理器 {name} 初始化失败")
        
        logger.info("测试initialize_all: 通过")
    
    def test_get_processor(self):
        """测试获取处理器"""
        processor = self.manager.get_processor('opencv')
        
        self.assertIsNotNone(processor)
        self.assertIsInstance(processor, OpenCVProcessor)
        
        # 测试不存在的处理器
        self.assertIsNone(self.manager.get_processor('nonexistent'))
        
        logger.info("测试get_processor: 通过")
    
    def test_execute_with_retry(self):
        """测试带重试的执行"""
        self.manager.initialize_all()
        
        # 创建测试帧
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 执行处理
        result = self.manager.execute_with_retry('opencv', frame, resize=(50, 50))
        
        self.assertTrue(result.get('success'))
        self.assertIn('image', result)
        
        logger.info("测试execute_with_retry: 通过")
    
    def test_statistics(self):
        """测试性能统计"""
        self.manager.initialize_all()
        
        # 执行一些处理
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        for _ in range(5):
            self.manager.execute_with_retry('opencv', frame, resize=(50, 50))
        
        # 获取统计
        stats = self.manager.get_statistics()
        
        self.assertIn('total_processes', stats)
        self.assertIn('success_count', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('avg_process_time', stats)
        
        # 验证处理次数
        self.assertEqual(stats['total_processes'], 5)
        
        logger.info(f"测试statistics: 通过 ({stats['success_rate']} 成功率)")
    
    def test_health_check(self):
        """测试健康检查"""
        self.manager.initialize_all()
        
        health = self.manager.health_check()
        
        self.assertEqual(health['manager'], 'ok')
        self.assertIn('processors', health)
        self.assertIn('statistics', health)
        
        # 验证每个处理器的健康状态
        for name, status in health['processors'].items():
            self.assertIn('name', status)
            self.assertIn('status', status)
        
        logger.info("测试health_check: 通过")
    
    def test_execute_pipeline(self):
        """测试流水线执行"""
        # 确保处理器已初始化
        self.manager.initialize_all()
        
        # 创建测试数据
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 执行简单流水线
        result = self.manager.execute_pipeline(
            "live_streaming_audio",
            frame,
            resize=(640, 480)
        )
        
        self.assertIn('success', result)
        self.assertIn('pipeline', result)
        self.assertIn('stages', result)
        
        logger.info("测试execute_pipeline: 通过")
    
    def test_retry_mechanism(self):
        """测试重试机制"""
        # 创建一个会失败的处理器
        class FailingProcessor(BaseProcessor):
            def __init__(self, config):
                super().__init__(config)
                self.call_count = 0
            
            def _load_model(self):
                self.model_path = "failing"
            
            def process(self, input_data, **kwargs):
                self.call_count += 1
                if self.call_count < 3:
                    raise Exception("模拟失败")
                return {"success": True}
        
        # 注册并测试
        self.manager.register('failing', FailingProcessor, {})
        
        result = self.manager.execute_with_retry('failing', {}, max_retries=5)
        
        # 验证重试机制工作（应该在前3次失败后成功）
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('attempts'), 3)
        
        logger.info("测试retry_mechanism: 通过 (第3次重试成功)")
    
    def test_cleanup(self):
        """测试资源清理"""
        # 初始化
        self.manager.initialize_all()
        
        # 清理
        self.manager.cleanup()
        
        # 验证所有处理器已清理
        for processor in self.manager.processors.values():
            self.assertFalse(processor.initialized)
        
        logger.info("测试cleanup: 通过")


class TestOpenCVProcessor(unittest.TestCase):
    """OpenCV处理器测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.processor = OpenCVProcessor()
    
    def test_initialization(self):
        """测试初始化"""
        result = self.processor.initialize()
        self.assertTrue(result)
        self.assertTrue(self.processor.initialized)
        self.assertIsNotNone(self.processor.model_path)
        
        logger.info("测试initialization: 通过")
    
    def test_process_image(self):
        """测试图像处理"""
        self.processor.initialize()
        
        # 创建测试图像
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 调整大小
        result = self.processor.process(image, resize=(50, 50))
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result['shape'], (50, 50, 3))
        self.assertEqual(result['processor'], 'OpenCV')
        
        logger.info("测试process_image: 通过")
    
    def test_process_grayscale(self):
        """测试灰度转换"""
        self.processor.initialize()
        
        # 创建测试图像
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 转换为灰度
        result = self.processor.process(image, to_grayscale=True)
        
        self.assertTrue(result.get('success'))
        self.assertEqual(len(result['shape']), 2)  # 灰度图是2维
        
        logger.info("测试process_grayscale: 通过")
    
    def test_detect_faces(self):
        """测试人脸检测"""
        self.processor.initialize()
        
        # 创建测试图像（模拟有人脸）
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 保存临时文件进行测试
        import tempfile
        import cv2
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            cv2.imwrite(temp_path, image)
        
        try:
            faces = self.processor.detect_faces(temp_path)
            # 随机图像可能检测不到人脸，这是正常的
            self.assertIsInstance(faces, list)
        finally:
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        logger.info("测试detect_faces: 通过")


class TestPerformanceMonitoring(unittest.TestCase):
    """性能监控测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.manager = ProcessorManager()
        self.manager.initialize_all()
    
    def tearDown(self):
        """测试用例清理"""
        if self.manager:
            self.manager.cleanup()
    
    def test_processing_speed(self):
        """测试处理速度"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        iterations = 10
        start = time.perf_counter()
        
        for _ in range(iterations):
            self.manager.execute_with_retry('opencv', frame, resize=(320, 240))
        
        elapsed = time.perf_counter() - start
        avg_time = elapsed / iterations
        
        # 验证平均处理时间小于100ms
        self.assertLess(avg_time, 0.1, f"处理时间过长: {avg_time:.3f}s")
        
        logger.info(f"测试processing_speed: 通过 (平均 {avg_time:.4f}s/次)")
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        
        # 连续处理
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        for _ in range(20):
            self.manager.execute_with_retry('opencv', frame, resize=(320, 240))
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 验证内存增长小于100MB
        self.assertLess(memory_increase, 100 * 1024 * 1024,
                       f"内存增长过高: {memory_increase / 1024 / 1024:.2f} MB")
        
        logger.info(f"测试memory_usage: 通过 (增长 {memory_increase / 1024 / 1024:.2f} MB)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
