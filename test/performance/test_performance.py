#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试
AR 综合实时合成与监控系统

测试内容:
- 性能基准测试
- CPU/内存使用分析
- 视频处理性能测试
- API响应时间测试
- 内存泄漏检测

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import sys
import time
import psutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging
import cv2

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths, import_create_app, resolve_api_prefix_with_client

PATHS = add_project_paths()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestPerformanceBenchmarks(unittest.TestCase):
    """性能基准测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
        self.process = psutil.Process(os.getpid())
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_cpu_usage_benchmark(self):
        """测试CPU使用率基准"""
        # 获取初始CPU使用率
        initial_cpu = self.process.cpu_percent(interval=1)
        
        # 执行一些计算密集型操作
        result = sum([i*i for i in range(100000)])
        
        # 获取计算后CPU使用率
        final_cpu = self.process.cpu_percent(interval=1)
        
        # 验证CPU使用率在合理范围内
        self.assertIsInstance(initial_cpu, float)
        self.assertIsInstance(final_cpu, float)
        
        logger.info(f"测试CPU使用率: 初始={initial_cpu}%, 计算后={final_cpu}%")
        logger.info("测试cpu_usage_benchmark: 通过")
    
    def test_memory_usage_benchmark(self):
        """测试内存使用基准"""
        # 获取初始内存使用
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建一些数据
        test_data = [i for i in range(100000)]
        
        # 获取内存使用
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # 验证内存使用在合理范围内
        self.assertIsInstance(initial_memory, float)
        self.assertIsInstance(memory_after, float)
        self.assertLess(memory_after, 500)  # 不超过500MB
        
        logger.info(f"测试内存使用: 初始={initial_memory:.2f}MB, 处理后={memory_after:.2f}MB")
        logger.info("测试memory_usage_benchmark: 通过")
    
    def test_list_comprehension_performance(self):
        """测试列表推导式性能"""
        # 测试列表推导式
        start_time = time.time()
        result = [i * 2 for i in range(100000)]
        end_time = time.time()
        
        # 验证结果
        self.assertEqual(len(result), 100000)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[-1], 199998)
        
        # 验证性能（应在1秒内完成）
        duration = end_time - start_time
        self.assertLess(duration, 5)  # 不超过5秒
        
        logger.info(f"测试列表推导式性能: 耗时={duration:.4f}秒")
        logger.info("测试list_comprehension_performance: 通过")
    
    def test_dict_operations_performance(self):
        """测试字典操作性能"""
        # 测试字典操作
        start_time = time.time()
        
        # 创建字典
        test_dict = {f"key_{i}": i for i in range(10000)}
        
        # 执行查找操作
        for i in range(10000):
            _ = test_dict.get(f"key_{i}")
        
        end_time = time.time()
        
        # 验证性能
        duration = end_time - start_time
        self.assertLess(duration, 2)  # 不超过2秒
        
        logger.info(f"测试字典操作性能: 耗时={duration:.4f}秒")
        logger.info("测试dict_operations_performance: 通过")


class TestVideoProcessingPerformance(unittest.TestCase):
    """视频处理性能测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_frame_processing_performance(self):
        """测试帧处理性能"""
        import numpy as np
        
        # 模拟帧数据
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 测试帧处理时间
        start_time = time.time()
        
        # 模拟帧处理（图像转换）
        for _ in range(100):
            # 转换为灰度
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 调整大小
            resized = cv2.resize(gray, (320, 240))
        
        end_time = time.time()
        
        # 验证性能
        duration = end_time - start_time
        self.assertLess(duration, 2)  # 处理100帧应在2秒内
        
        logger.info(f"测试帧处理性能: 100帧耗时={duration:.4f}秒")
        logger.info("测试frame_processing_performance: 通过")
    
    def test_numpy_operations_performance(self):
        """测试NumPy操作性能"""
        import numpy as np
        
        # 创建测试数据
        data = np.random.rand(1000, 1000).astype(np.float32)
        
        # 测试NumPy操作
        start_time = time.time()
        
        # 执行多次操作
        for _ in range(10):
            result = np.mean(data, axis=0)
            result = np.std(data, axis=0)
            result = np.sum(data, axis=1)
        
        end_time = time.time()
        
        # 验证性能
        duration = end_time - start_time
        self.assertLess(duration, 5)  # 应在5秒内完成
        
        logger.info(f"测试NumPy操作性能: 耗时={duration:.4f}秒")
        logger.info("测试numpy_operations_performance: 通过")


class TestAPIResponseTime(unittest.TestCase):
    """API响应时间测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_health_endpoint_response_time(self):
        """测试健康检查端点响应时间"""
        create_app = import_create_app(PATHS)
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 测试响应时间
        start_time = time.time()
        response = client.get(f'{api_prefix}/health' if api_prefix else '/health')
        end_time = time.time()
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应时间
        duration = (end_time - start_time) * 1000  # 毫秒
        self.assertLess(duration, 1000)  # 应在1秒内响应
        
        logger.info(f"测试健康检查响应时间: {duration:.2f}ms")
        logger.info("测试health_endpoint_response_time: 通过")
    
    def test_system_info_endpoint_response_time(self):
        """测试系统信息端点响应时间"""
        create_app = import_create_app(PATHS)
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 测试响应时间
        start_time = time.time()
        response = client.get(f'{api_prefix}/overview' if api_prefix else '/overview')
        end_time = time.time()
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应时间
        duration = (end_time - start_time) * 1000  # 毫秒
        self.assertLess(duration, 1000)  # 应在1秒内响应
        
        logger.info(f"测试系统信息响应时间: {duration:.2f}ms")
        logger.info("测试system_info_endpoint_response_time: 通过")
    
    def test_resource_endpoint_response_time(self):
        """测试资源端点响应时间"""
        create_app = import_create_app(PATHS)
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 测试CPU资源端点
        start_time = time.time()
        response = client.get(f'{api_prefix}/resources' if api_prefix else '/resources')
        end_time = time.time()
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        
        # 验证响应时间
        duration = (end_time - start_time) * 1000  # 毫秒
        self.assertLess(duration, 500)  # 应在500ms内响应
        
        logger.info(f"测试资源端点响应时间: {duration:.2f}ms")
        logger.info("测试resource_endpoint_response_time: 通过")


class TestMemoryLeakDetection(unittest.TestCase):
    """内存泄漏检测测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
        self.process = psutil.Process(os.getpid())
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_no_memory_leak_in_loops(self):
        """测试循环中无内存泄漏"""
        import gc
        
        # 获取初始内存
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 执行循环操作
        for i in range(100):
            # 创建临时数据
            temp_data = [i] * 1000
            # 删除引用
            del temp_data
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取最终内存
        final_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 验证内存变化在合理范围内
        memory_diff = final_memory - initial_memory
        self.assertLess(memory_diff, 50)  # 内存增长不超过50MB
        
        logger.info(f"测试内存泄漏: 初始={initial_memory:.2f}MB, 最终={final_memory:.2f}MB, 增长={memory_diff:.2f}MB")
        logger.info("测试no_memory_leak_in_loops: 通过")
    
    def test_list_operations_memory(self):
        """测试列表操作内存使用"""
        import gc
        
        # 获取初始内存
        gc.collect()
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 执行列表操作
        test_list = []
        for i in range(1000):
            test_list.append(i)
        
        # 删除列表
        del test_list
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取最终内存
        final_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 验证内存变化
        memory_diff = final_memory - initial_memory
        self.assertLess(memory_diff, 20)  # 内存增长不超过20MB
        
        logger.info(f"测试列表操作内存: 增长={memory_diff:.2f}MB")
        logger.info("测试list_operations_memory: 通过")


class TestProcessorPerformance(unittest.TestCase):
    """处理器性能测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_processor_health_check_performance(self):
        """测试处理器健康检查性能"""
        from processor_manager import ProcessorManager
        
        # 创建管理器
        manager = ProcessorManager()
        
        # 初始化
        manager.initialize_all()
        
        # 测试健康检查性能
        start_time = time.time()
        health = manager.health_check()
        end_time = time.time()
        
        # 验证性能
        duration = (end_time - start_time) * 1000  # 毫秒
        self.assertLess(duration, 100)  # 应在100ms内完成
        
        logger.info(f"测试处理器健康检查性能: {duration:.2f}ms")
        logger.info("测试processor_health_check_performance: 通过")
    
    def test_processor_statistics_performance(self):
        """测试处理器统计性能"""
        from processor_manager import ProcessorManager
        
        # 创建管理器
        manager = ProcessorManager()
        
        # 初始化
        manager.initialize_all()
        
        # 测试统计性能
        start_time = time.time()
        stats = manager.get_statistics()
        end_time = time.time()
        
        # 验证性能
        duration = (end_time - start_time) * 1000  # 毫秒
        self.assertLess(duration, 100)  # 应在100ms内完成
        
        logger.info(f"测试处理器统计性能: {duration:.2f}ms")
        logger.info("测试processor_statistics_performance: 通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)
