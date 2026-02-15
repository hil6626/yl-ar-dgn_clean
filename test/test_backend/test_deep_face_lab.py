#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepFaceLab 模块单元测试
AR 综合实时合成与监控系统

测试内容:
- 模块初始化测试
- 人脸提取测试
- 视频处理测试
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

from deep_face_lab import DeepFaceLabModule, create_deep_face_lab

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestDeepFaceLabModule(unittest.TestCase):
    """DeepFaceLab 模块测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.test_data_dir = PROJECT_ROOT / "test" / "test_data"
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("DeepFaceLab 测试类初始化完成")
    
    def setUp(self):
        """测试用例设置"""
        self.module = DeepFaceLabModule()
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
        module = DeepFaceLabModule()
        self.assertFalse(module.initialized)
        
        # 测试带配置初始化
        config = {
            'gpu_id': 0,
            'batch_size': 2,
            'iterations': 500,
            'face_size': 128
        }
        module = DeepFaceLabModule(config)
        self.assertFalse(module.initialized)
        self.assertEqual(module.config['gpu_id'], 0)
        self.assertEqual(module.config['batch_size'], 2)
        self.assertEqual(module.config['iterations'], 500)
        
        logger.info("测试初始化: 通过")
    
    def test_initialize_module(self):
        """测试模块初始化方法"""
        result = self.module.initialize()
        self.assertTrue(result)
        self.assertTrue(self.module.initialized)
        
        # 验证检测器已加载
        self.assertIsNotNone(self.module.face_detector)
        self.assertIn(self.module.detector_type, ['dnn', 'haar'])
        
        # 验证GPU状态
        self.assertIn('gpu_enabled', dir(self.module))
        
        logger.info("测试initialize_module: 通过")
    
    def test_default_model_structure(self):
        """测试默认模型目录创建"""
        import os
        import tempfile
        
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {'model_path': os.path.join(tmpdir, 'models')}
            module = DeepFaceLabModule(config)
            
            # 初始化应该创建目录
            result = module.initialize()
            self.assertTrue(result)
            
            # 验证目录结构
            model_path = config['model_path']
            self.assertTrue(os.path.exists(model_path))
            self.assertTrue(os.path.exists(os.path.join(model_path, 'original')))
            self.assertTrue(os.path.exists(os.path.join(model_path, 'modified')))
            self.assertTrue(os.path.exists(os.path.join(model_path, 'aligned')))
            self.assertTrue(os.path.exists(os.path.join(model_path, 'merged')))
            
            logger.info("测试default_model_structure: 通过")
    
    def test_get_status(self):
        """测试获取模块状态"""
        self.module.initialize()
        
        status = self.module.get_status()
        
        self.assertIn('initialized', status)
        self.assertIn('is_processing', status)
        self.assertIn('progress', status)
        self.assertIn('source_faces_count', status)
        self.assertIn('frame_count', status)
        self.assertIn('avg_process_time', status)
        
        logger.info("测试get_status: 通过")
    
    def test_health_check(self):
        """测试健康检查"""
        # 未初始化状态
        health = self.module.health_check()
        self.assertEqual(health['status'], 'error')
        
        # 初始化后状态
        self.module.initialize()
        health = self.module.health_check()
        self.assertEqual(health['name'], 'DeepFaceLab')
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
    
    def test_process_frame_with_source(self):
        """测试设置源人脸后的帧处理"""
        self.module.initialize()
        
        # 创建源人脸
        source = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        self.module.source_faces = [source]
        
        # 创建测试帧
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 处理帧
        result = self.module.process_frame(frame)
        
        # 验证输出
        self.assertEqual(result.shape, frame.shape)
        self.assertEqual(result.dtype, frame.dtype)
        
        # 验证帧计数增加
        self.assertEqual(self.module.frame_count, 1)
        
        logger.info("测试process_frame_with_source: 通过")
    
    def test_reset(self):
        """测试模块重置"""
        self.module.initialize()
        
        # 设置源人脸
        source = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        self.module.source_faces = [source]
        self.module.frame_count = 10
        
        # 重置
        self.module.reset()
        
        # 验证状态已重置
        self.assertEqual(len(self.module.source_faces), 0)
        self.assertEqual(self.module.frame_count, 0)
        self.assertEqual(self.module.progress, 0.0)
        
        logger.info("测试reset: 通过")
    
    def test_cleanup(self):
        """测试资源清理"""
        self.module.initialize()
        
        # 清理
        self.module.cleanup()
        
        # 验证状态
        self.assertFalse(self.module.initialized)
        self.assertEqual(len(self.module.source_faces), 0)
        
        logger.info("测试cleanup: 通过")
    
    def test_progress_callback(self):
        """测试进度回调"""
        self.module.initialize()
        
        progress_values = []
        
        def on_progress(p):
            progress_values.append(p)
        
        self.module.set_progress_callback(on_progress)
        
        # 模拟进度更新
        for i in range(10):
            self.module.progress = (i + 1) / 10
            if self.module.on_progress_update:
                self.module.on_progress_update(self.module.progress)
        
        self.assertEqual(len(progress_values), 10)
        self.assertAlmostEqual(progress_values[-1], 1.0)
        
        logger.info("测试progress_callback: 通过")
    
    def test_status_callback(self):
        """测试状态回调"""
        self.module.initialize()
        
        status_values = []
        
        def on_status(s):
            status_values.append(s)
        
        self.module.set_status_callback(on_status)
        
        # 模拟状态变化
        if self.module.on_status_change:
            self.module.on_status_change('processing')
            self.module.on_status_change('completed')
        
        self.assertIn('processing', status_values)
        self.assertIn('completed', status_values)
        
        logger.info("测试status_callback: 通过")
    
    def test_create_deep_face_lab(self):
        """测试便捷创建函数"""
        config = {'gpu_id': 0, 'batch_size': 2}
        module = create_deep_face_lab(config)
        
        self.assertIsInstance(module, DeepFaceLabModule)
        self.assertEqual(module.config['gpu_id'], 0)
        self.assertEqual(module.config['batch_size'], 2)
        
        module.cleanup()
        logger.info("测试create_deep_face_lab: 通过")
    
    def test_color_match(self):
        """测试颜色匹配功能"""
        self.module.initialize()
        
        # 创建源和目标
        source = np.ones((100, 100, 3), dtype=np.uint8) * 100
        target = np.ones((100, 100, 3), dtype=np.uint8) * 150
        
        # 颜色匹配
        result = self.module._color_match(source, target)
        
        # 验证结果
        self.assertEqual(result.shape, source.shape)
        self.assertEqual(result.dtype, source.dtype)
        
        logger.info("测试color_match: 通过")
    
    def test_get_comparison_view(self):
        """测试对比视图功能"""
        self.module.initialize()
        
        # 创建原始和处理后的帧
        original = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 获取对比视图
        comparison = self.module.get_comparison_view(original, processed)
        
        # 验证结果
        expected_height = 480
        expected_width = 640 * 2 + 10
        self.assertEqual(comparison.shape[0], expected_height)
        self.assertEqual(comparison.shape[1], expected_width)
        self.assertEqual(comparison.shape[2], 3)
        
        logger.info("测试get_comparison_view: 通过")
    
    def test_performance(self):
        """测试处理性能"""
        self.module.initialize()
        
        # 创建源人脸
        source = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        self.module.source_faces = [source]
        
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


class TestDeepFaceLabBatchProcessing(unittest.TestCase):
    """DeepFaceLab 批量处理测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.module = DeepFaceLabModule()
        cls.module.initialize()
        logger.info("批量处理测试类初始化完成")
    
    @classmethod
    def tearDownClass(cls):
        """类级别清理"""
        if cls.module:
            cls.module.cleanup()
        logger.info("批量处理测试类清理完成")
    
    def test_batch_process_empty(self):
        """测试空批量处理"""
        results = self.module.batch_process([])
        self.assertEqual(len(results), 0)
        logger.info("测试batch_process_empty: 通过")
    
    def test_batch_process_sequential(self):
        """测试顺序批量处理"""
        # 创建测试任务（使用内存中的数据）
        tasks = [
            {'source': np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)},
            {'source': np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)},
        ]
        
        # 顺序处理
        results = self.module.batch_process(tasks, parallel=False)
        
        self.assertEqual(len(results), 2)
        logger.info("测试batch_process_sequential: 通过")


class TestDeepFaceLabPerformance(unittest.TestCase):
    """DeepFaceLab 性能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.module = DeepFaceLabModule()
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
        # 创建源人脸
        source = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        self.module.source_faces = [source]
        
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
        source = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        self.module.source_faces = [source]
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
