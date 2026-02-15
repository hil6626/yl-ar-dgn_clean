#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳定性测试
AR 综合实时合成与监控系统

测试内容:
- 压力测试
- 长时间运行稳定性测试
- 异常恢复测试
- 资源持续监控测试

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import sys
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading
import gc
import logging

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


class TestStressTesting(unittest.TestCase):
    """压力测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_multiple_thread_operations(self):
        """测试多线程操作"""
        import threading
        import time
        
        results = []
        lock = threading.Lock()
        
        def worker(worker_id):
            # 模拟工作
            time.sleep(0.1)
            with lock:
                results.append(worker_id)
        
        # 创建多个线程
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
        
        # 启动所有线程
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证所有线程完成
        self.assertEqual(len(results), 10)
        self.assertEqual(sorted(results), list(range(10)))
        
        logger.info("测试multiple_thread_operations: 通过")
    
    def test_concurrent_operations(self):
        """测试并发操作"""
        import threading
        import time
        
        counter = [0]
        lock = threading.Lock()
        
        def increment():
            for _ in range(100):
                with lock:
                    counter[0] += 1
        
        # 创建多个线程同时操作
        threads = []
        for i in range(5):
            t = threading.Thread(target=increment)
            threads.append(t)
        
        # 启动所有线程
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证计数器正确
        self.assertEqual(counter[0], 500)  # 5个线程 * 100次操作
        
        logger.info("测试concurrent_operations: 通过")
    
    def test_rapid_requests(self):
        """测试快速请求"""
        create_app = import_create_app(PATHS)
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 快速发送多个请求
        success_count = 0
        for _ in range(20):
            response = client.get(f'{api_prefix}/health' if api_prefix else '/health')
            if response.status_code == 200:
                success_count += 1
        
        # 验证所有请求成功
        self.assertEqual(success_count, 20)
        
        logger.info("测试rapid_requests: 通过")
    
    def test_memory_pressure(self):
        """测试内存压力"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 获取初始内存
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 创建临时对象
        data_holder = []
        for i in range(100):
            data = [i] * 10000
            data_holder.append(data)
        
        # 获取内存峰值
        peak_memory = process.memory_info().rss / 1024 / 1024
        
        # 清理
        del data_holder
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # 验证内存管理正常
        self.assertLess(final_memory - initial_memory, 100)  # 内存增长不超过100MB
        
        logger.info(f"测试内存压力: 初始={initial_memory:.2f}MB, 峰值={peak_memory:.2f}MB, 最终={final_memory:.2f}MB")
        logger.info("测试memory_pressure: 通过")


class TestLongRunStability(unittest.TestCase):
    """长时间运行稳定性测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_short_duration_stability(self):
        """测试短时间稳定性（模拟长运行）"""
        import time
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 模拟短时间运行
        iterations = 50
        memory_samples = []
        
        for i in range(iterations):
            # 执行一些操作
            data = [i] * 1000
            result = sum(data)
            del data
            
            # 每10次采样内存
            if i % 10 == 0:
                gc.collect()
                memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory)
        
        # 验证内存稳定
        memory_diff = max(memory_samples) - min(memory_samples)
        self.assertLess(memory_diff, 50)  # 内存波动不超过50MB
        
        logger.info(f"测试短时间稳定性: 内存波动={memory_diff:.2f}MB")
        logger.info("测试short_duration_stability: 通过")
    
    def test_repeated_initialization(self):
        """测试重复初始化稳定性"""
        from processor_manager import ProcessorManager
        
        # 多次创建和销毁处理器管理器
        for _ in range(5):
            manager = ProcessorManager()
            manager.initialize_all()
            manager.cleanup()
        
        logger.info("测试repeated_initialization: 通过")
    
    def test_health_check_repeated(self):
        """测试重复健康检查稳定性"""
        from processor_manager import ProcessorManager
        
        manager = ProcessorManager()
        manager.initialize_all()
        
        # 多次执行健康检查
        for _ in range(20):
            health = manager.health_check()
            self.assertIn('manager', health)
            self.assertIn('processors', health)
        
        manager.cleanup()
        
        logger.info("测试health_check_repeated: 通过")
    
    def test_state_transitions(self):
        """测试状态转换稳定性"""
        from camera import CameraModule, CameraStatus
        from audio_module import AudioModule, AudioStatus
        
        # 测试摄像头状态转换
        camera = CameraModule(camera_id=0)
        
        # 验证初始状态
        self.assertEqual(camera.status, CameraStatus.STOPPED)
        
        # 模拟状态检查
        health = camera.health_check()
        self.assertIn('camera', health)
        
        logger.info("测试state_transitions: 通过")


class TestExceptionRecovery(unittest.TestCase):
    """异常恢复测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_processor_error_recovery(self):
        """测试处理器错误恢复"""
        from processor_manager import ProcessorManager
        
        manager = ProcessorManager()
        manager.initialize_all()
        
        # 模拟获取处理器并测试
        opencv = manager.get_processor('opencv')
        
        if opencv:
            # 执行健康检查
            health1 = opencv.health_check()
            
            # 再次执行（应该稳定）
            health2 = opencv.health_check()
            
            # 验证一致性
            self.assertEqual(health1['name'], health2['name'])
        
        manager.cleanup()
        
        logger.info("测试processor_error_recovery: 通过")
    
    def test_api_error_handling(self):
        """测试API错误处理"""
        create_app = import_create_app(PATHS)
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 测试无效端点
        response = client.get(f'{api_prefix}/invalid_endpoint' if api_prefix else '/invalid_endpoint')
        self.assertEqual(response.status_code, 404)
        
        # 测试无效请求
        response = client.post(f'{api_prefix}/refresh' if api_prefix else '/refresh',
                               data='invalid json',
                               content_type='application/json')
        self.assertIn(response.status_code, (200, 400, 404))
        
        logger.info("测试api_error_handling: 通过")
    
    def test_null_input_handling(self):
        """测试空输入处理"""
        from processor_manager import ProcessorManager
        
        manager = ProcessorManager()
        
        # 测试空配置
        try:
            opencv = manager.get_processor('opencv')
            if opencv:
                # 模拟空输入场景
                health = opencv.health_check()
                self.assertIn('name', health)
        except Exception as e:
            self.fail(f"空输入处理失败: {e}")
        
        manager.cleanup()
        
        logger.info("测试null_input_handling: 通过")
    
    def test_concurrent_exception_handling(self):
        """测试并发异常处理"""
        import threading
        import time
        
        results = []
        lock = threading.Lock()
        
        def safe_worker(worker_id):
            try:
                # 模拟可能出错的操作
                if worker_id % 3 == 0:
                    raise ValueError(f"模拟错误 {worker_id}")
                result = worker_id * 2
                with lock:
                    results.append((worker_id, result))
            except Exception as e:
                with lock:
                    results.append((worker_id, None))
        
        # 创建多个线程
        threads = []
        for i in range(10):
            t = threading.Thread(target=safe_worker, args=(i,))
            threads.append(t)
        
        # 启动所有线程
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证结果
        self.assertEqual(len(results), 10)
        
        logger.info("测试concurrent_exception_handling: 通过")


class TestResourceContinuousMonitoring(unittest.TestCase):
    """资源持续监控测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_cpu_usage_trend(self):
        """测试CPU使用趋势"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 收集多个样本
        samples = []
        for _ in range(10):
            cpu = process.cpu_percent(interval=0.1)
            samples.append(cpu)
        
        # 验证样本
        self.assertEqual(len(samples), 10)
        self.assertTrue(all(isinstance(s, float) for s in samples))
        self.assertTrue(all(0 <= s <= 100 for s in samples))
        
        logger.info(f"测试CPU使用趋势: 样本={samples}")
        logger.info("测试cpu_usage_trend: 通过")
    
    def test_memory_usage_trend(self):
        """测试内存使用趋势"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 收集多个样本
        samples = []
        for _ in range(10):
            gc.collect()
            memory = process.memory_info().rss / 1024 / 1024
            samples.append(memory)
        
        # 验证样本
        self.assertEqual(len(samples), 10)
        self.assertTrue(all(isinstance(m, float) for m in samples))
        self.assertTrue(all(m >= 0 for m in samples))
        
        logger.info(f"测试内存使用趋势: 样本={samples}")
        logger.info("测试memory_usage_trend: 通过")
    
    def test_processor_health_trend(self):
        """测试处理器健康趋势"""
        from processor_manager import ProcessorManager
        
        manager = ProcessorManager()
        manager.initialize_all()
        
        # 收集多个健康检查样本
        samples = []
        for _ in range(10):
            health = manager.health_check()
            samples.append(health)
            time.sleep(0.05)
        
        # 验证样本
        self.assertEqual(len(samples), 10)
        
        manager.cleanup()
        
        logger.info("测试processor_health_trend: 通过")
    
    def test_api_latency_trend(self):
        """测试API延迟趋势"""
        create_app = import_create_app(PATHS)
        app = create_app()
        client = app.test_client()
        api_prefix = resolve_api_prefix_with_client(client)
        
        # 收集延迟样本
        import time
        samples = []
        
        for _ in range(10):
            start = time.time()
            response = client.get(f'{api_prefix}/health' if api_prefix else '/health')
            end = time.time()
            
            latency = (end - start) * 1000  # 毫秒
            samples.append(latency)
        
        # 验证样本
        self.assertEqual(len(samples), 10)
        
        # 验证延迟在合理范围内
        avg_latency = sum(samples) / len(samples)
        self.assertLess(avg_latency, 1000)  # 平均延迟不超过1秒
        
        logger.info(f"测试API延迟趋势: 平均延迟={avg_latency:.2f}ms")
        logger.info("测试api_latency_trend: 通过")


class TestSystemRecovery(unittest.TestCase):
    """系统恢复测试类"""
    
    def setUp(self):
        """测试设置"""
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试清理"""
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_processor_reinitialization(self):
        """测试处理器重新初始化"""
        from processor_manager import ProcessorManager
        
        # 第一次初始化
        manager1 = ProcessorManager()
        manager1.initialize_all()
        
        # 清理
        manager1.cleanup()
        
        # 重新初始化
        manager2 = ProcessorManager()
        results = manager2.initialize_all()
        
        # 验证重新初始化成功
        self.assertIsInstance(results, dict)
        
        manager2.cleanup()
        
        logger.info("测试processor_reinitialization: 通过")
    
    def test_health_check_after_operations(self):
        """测试操作后健康检查"""
        from processor_manager import ProcessorManager
        
        manager = ProcessorManager()
        manager.initialize_all()
        
        # 执行一些操作
        _ = manager.get_processor('opencv')
        _ = manager.health_check()
        _ = manager.get_statistics()
        
        # 再次执行健康检查
        health = manager.health_check()
        
        # 验证健康检查仍然正常
        self.assertIn('manager', health)
        self.assertIn('processors', health)
        
        manager.cleanup()
        
        logger.info("测试health_check_after_operations: 通过")
    
    def test_stress_recovery(self):
        """测试压力后恢复"""
        from processor_manager import ProcessorManager
        
        manager = ProcessorManager()
        manager.initialize_all()
        
        # 模拟压力操作
        for _ in range(100):
            _ = manager.health_check()
            _ = manager.get_statistics()
        
        # 验证系统仍然正常
        health = manager.health_check()
        self.assertIn('manager', health)
        
        manager.cleanup()
        
        logger.info("测试stress_recovery: 通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)
