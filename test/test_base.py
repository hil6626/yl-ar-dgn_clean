#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基础类 - Testing Base Classes
AR 综合实时合成与监控系统

提供:
- 基础测试用例类
- 测试夹具(fixtures)
- 测试工具函数
- 性能测试支持

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import shutil
import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field

from test_utils import find_project_root, add_project_paths

# 添加项目根目录到路径
PROJECT_ROOT = find_project_root(Path(__file__).resolve())
add_project_paths(PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    status: str  # passed, failed, error, skipped
    duration: float
    message: str = ""
    error_info: Optional[str] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class TestCase(unittest.TestCase):
    """
    增强的测试用例类
    
    扩展 unittest.TestCase 功能:
    - 自动测试数据生成
    - 性能计时
    - 测试结果收集
    - 资源自动清理
    """
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        cls.test_data_dir = PROJECT_ROOT / "test" / "test_data"
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)
        cls.temp_dir = PROJECT_ROOT / "test" / "temp"
        cls.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"测试类初始化: {cls.__name__}")
    
    @classmethod
    def tearDownClass(cls):
        """类级别清理"""
        # 清理临时文件
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir, ignore_errors=True)
        logger.info(f"测试类清理完成: {cls.__name__}")
    
    def setUp(self):
        """测试用例设置"""
        self.test_start_time = time.time()
        self.test_result = TestResult(
            test_name=self._testMethodName,
            status="pending",
            duration=0.0,
            message=""
        )
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试用例清理"""
        self.test_result.duration = time.time() - self.test_start_time
        status = "passed"
        outcome = getattr(self, "_outcome", None)
        result = getattr(outcome, "result", None)
        if result is not None:
            errors = list(result.errors) + list(result.failures)
            status = "passed" if not errors else "failed"
        self.test_result.status = status
        
        # 记录测试结果
        logger.info(f"测试完成: {self._testMethodName} - {status} ({self.test_result.duration:.3f}s)")
    
    def assertAlmostEqual(self, first, second, places=7, msg=None):
        """重写 assertAlmostEqual 增加日志"""
        super().assertAlmostEqual(first, second, places, msg)
        logger.debug(f"数值断言成功: {first} ≈ {second}")
    
    def assertEqual(self, first, second, msg=None):
        """重写 assertEqual 增加日志"""
        super().assertEqual(first, second, msg)
        logger.debug(f"等值断言成功: {first} == {second}")
    
    def assertTrue(self, expr, msg=None):
        """重写 assertTrue 增加日志"""
        super().assertTrue(expr, msg)
        logger.debug(f"布尔断言成功: {expr} is True")
    
    def assertFalse(self, expr, msg=None):
        """重写 assertFalse 增加日志"""
        super().assertFalse(expr, msg)
        logger.debug(f"布尔断言成功: {expr} is False")
    
    def assertRaises(self, expected_exception, callable_obj=None, msg=None, *args, **kwargs):
        """重写 assertRaises 增加日志"""
        exception_context = super().assertRaises(expected_exception, callable_obj, msg, *args, **kwargs)
        logger.debug(f"异常断言成功: 捕获到 {expected_exception.__name__}")
        return exception_context
    
    def create_test_image(self, width: int = 640, height: int = 480, 
                          color: tuple = (128, 128, 128)) -> str:
        """
        创建测试用图像文件
        
        Args:
            width: 图像宽度
            height: 图像高度
            color: 背景颜色 (BGR格式)
            
        Returns:
            str: 图像文件路径
        """
        import cv2
        import numpy as np
        
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:] = color
        
        # 添加一些几何图形用于测试
        cv2.rectangle(image, (100, 100), (300, 300), (0, 255, 0), 2)
        cv2.circle(image, (400, 200), 50, (0, 0, 255), -1)
        
        filepath = self.temp_dir / f"test_image_{int(time.time())}.jpg"
        cv2.imwrite(str(filepath), image)
        
        return str(filepath)
    
    def create_test_video(self, filepath: str, duration: float = 2.0, 
                          fps: int = 30, resolution: tuple = (640, 480)) -> str:
        """
        创建测试用视频文件
        
        Args:
            filepath: 输出文件路径
            duration: 视频时长(秒)
            fps: 帧率
            resolution: 分辨率 (宽, 高)
            
        Returns:
            str: 视频文件路径
        """
        import cv2
        import numpy as np
        
        width, height = resolution
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        frame_count = int(duration * fps)
        for i in range(frame_count):
            # 创建渐变帧
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = (i * 255 // frame_count, 128, 255 - i * 255 // frame_count)
            
            # 添加帧号
            cv2.putText(frame, f"Frame {i}", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        return filepath
    
    def create_mock_config(self, **kwargs) -> Dict:
        """
        创建测试用配置
        
        Args:
            **kwargs: 配置参数
            
        Returns:
            Dict: 配置字典
        """
        default_config = {
            'app': {
                'name': 'Test App',
                'version': '1.0.0',
                'debug': True
            },
            'server': {
                'host': '127.0.0.1',
                'port': 5000
            },
            'processing': {
                'frame_size': 640,
                'fps': 30,
                'quality': 'medium'
            }
        }
        
        # 合并用户配置
        for key, value in kwargs.items():
            if key in default_config and isinstance(default_config[key], dict):
                default_config[key].update(value)
            else:
                default_config[key] = value
        
        return default_config
    
    def measure_performance(self, func: Callable, iterations: int = 100) -> Dict:
        """
        测量函数性能
        
        Args:
            func: 要测试的函数
            iterations: 迭代次数
            
        Returns:
            Dict: 性能统计结果
        """
        import time
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'iterations': iterations,
            'total_time': sum(times),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': self._calculate_std_dev(times)
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """计算标准差"""
        import math
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        return math.sqrt(variance)
    
    def create_temp_file(self, suffix: str = ".tmp") -> str:
        """创建临时文件"""
        filepath = self.temp_dir / f"temp_{int(time.time())}_{os.getpid()}{suffix}"
        return str(filepath)
    
    def create_temp_dir(self) -> str:
        """创建临时目录"""
        dirpath = self.temp_dir / f"temp_dir_{int(time.time())}_{os.getpid()}"
        dirpath.mkdir(parents=True, exist_ok=True)
        return str(dirpath)


class IntegrationTestCase(TestCase):
    """
    集成测试用例类
    
    用于测试模块间的集成和交互:
    - 模块间通信
    - 数据流转
    - 端到端测试
    """
    
    def setUp(self):
        """集成测试设置"""
        super().setUp()
        self.modules = {}
        logger.info("集成测试初始化")
    
    def register_module(self, name: str, module: Any) -> None:
        """
        注册测试模块
        
        Args:
            name: 模块名称
            module: 模块实例
        """
        self.modules[name] = module
        logger.info(f"已注册模块: {name}")
    
    def get_module(self, name: str) -> Any:
        """
        获取已注册的模块
        
        Args:
            name: 模块名称
            
        Returns:
            Any: 模块实例
        """
        return self.modules.get(name)
    
    def test_module_integration(self, module_names: List[str]) -> bool:
        """
        测试模块间集成
        
        Args:
            module_names: 要测试的模块名称列表
            
        Returns:
            bool: 测试是否成功
        """
        try:
            for name in module_names:
                if name not in self.modules:
                    logger.error(f"模块未注册: {name}")
                    return False
            return True
        except Exception as e:
            logger.error(f"模块集成测试失败: {e}")
            return False
    
    def tearDown(self):
        """集成测试清理"""
        # 清理所有模块
        for name, module in self.modules.items():
            if hasattr(module, 'cleanup'):
                try:
                    module.cleanup()
                except Exception:
                    pass
        
        self.modules.clear()
        super().tearDown()
        logger.info("集成测试清理完成")


class PerformanceTestCase(TestCase):
    """
    性能测试用例类
    
    用于测试系统性能:
    - 响应时间测试
    - 吞吐量测试
    - 资源使用测试
    """
    
    def setUp(self):
        """性能测试设置"""
        super().setUp()
        self.performance_data = []
        logger.info("性能测试初始化")
    
    def record_performance(self, operation: str, duration: float, **kwargs) -> None:
        """
        记录性能数据
        
        Args:
            operation: 操作名称
            duration: 执行时间
            **kwargs: 额外数据
        """
        self.performance_data.append({
            'operation': operation,
            'duration': duration,
            'timestamp': time.time(),
            **kwargs
        })
    
    def get_performance_stats(self, operation: Optional[str] = None) -> Dict:
        """
        获取性能统计
        
        Args:
            operation: 操作名称过滤
            
        Returns:
            Dict: 性能统计数据
        """
        import math
        
        if operation:
            data = [d for d in self.performance_data if d['operation'] == operation]
        else:
            data = self.performance_data
        
        if not data:
            return {}
        
        durations = [d['duration'] for d in data]
        
        return {
            'operation': operation or 'all',
            'count': len(data),
            'total_time': sum(durations),
            'avg_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations),
            'throughput': len(durations) / sum(durations) if sum(durations) > 0 else 0
        }
    
    def assert_performance(self, operation: str, max_avg_time: float, 
                          min_throughput: float = 0.0) -> bool:
        """
        断言性能要求
        
        Args:
            operation: 操作名称
            max_avg_time: 最大平均时间
            min_throughput: 最小吞吐量
            
        Returns:
            bool: 是否满足性能要求
        """
        stats = self.get_performance_stats(operation)
        
        if not stats:
            return False
        
        avg_ok = stats.get('avg_time', float('inf')) <= max_avg_time
        throughput_ok = stats.get('throughput', 0) >= min_throughput
        
        return avg_ok and throughput_ok


class AsyncTestCase(TestCase):
    """
    异步测试用例类
    
    用于测试异步功能和协程:
    - 异步方法测试
    - 并发测试
    - 异步IO测试
    """
    
    def setUp(self):
        """异步测试设置"""
        super().setUp()
        self.loop = None
        logger.info("异步测试初始化")
    
    def run_async(self, coro):
        """
        运行异步协程
        
        Args:
            coro: 协程函数
            
        Returns:
            Any: 协程返回值
        """
        import asyncio
        
        if self.loop is None or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        try:
            return self.loop.run_until_complete(coro())
        except Exception as e:
            logger.error(f"异步执行失败: {e}")
            raise
    
    def tearDown(self):
        """异步测试清理"""
        if self.loop and not self.loop.is_closed():
            self.loop.close()
        self.loop = None
        super().tearDown()


# 测试夹具工厂
class TestFixtures:
    """测试夹具工厂类"""
    
    @staticmethod
    def create_processor_config() -> Dict:
        """创建处理器配置"""
        return {
            'opencv': {'enabled': True},
            'face_live_cam': {'model_type': 'quick', 'gpu_id': 0},
            'deepfacelab': {'iterations': 1000},
            'faceswap': {'align_eyes': True},
            'sox': {'effect': 'reverb'},
            'obs': {'virtual_camera': True}
        }
    
    @staticmethod
    def create_monitor_config() -> Dict:
        """创建监控配置"""
        return {
            'check_interval': 30,
            'health_thresholds': {
                'cpu_warning': 80,
                'cpu_critical': 95,
                'memory_warning': 85,
                'memory_critical': 95,
                'disk_warning': 90
            }
        }
    
    @staticmethod
    def create_alert_config() -> Dict:
        """创建告警配置"""
        return {
            'enabled': True,
            'cooldown': 300,
            'levels': {
                'warning': {'cpu': 80, 'memory': 85},
                'critical': {'cpu': 95, 'memory': 95}
            }
        }


# 测试工具函数
def run_tests(test_module: str, pattern: str = "test_*.py", 
              verbose: bool = True) -> unittest.TestResult:
    """
    运行测试套件
    
    Args:
        test_module: 测试模块路径
        pattern: 测试文件匹配模式
        verbose: 是否详细输出
        
    Returns:
        unittest.TestResult: 测试结果
    """
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 加载测试
    if isinstance(test_module, str):
        tests = loader.discover(test_module, pattern=pattern)
        suite.addTests(tests)
    else:
        suite.addTests(test_module)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result


def generate_test_report(results: List[TestResult], output_path: str) -> None:
    """
    生成测试报告
    
    Args:
        results: 测试结果列表
        output_path: 输出文件路径
    """
    report = {
        'summary': {
            'total': len(results),
            'passed': sum(1 for r in results if r.status == 'passed'),
            'failed': sum(1 for r in results if r.status == 'failed'),
            'error': sum(1 for r in results if r.status == 'error'),
            'skipped': sum(1 for r in results if r.status == 'skipped'),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        },
        'results': [r.__dict__ for r in results]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"测试报告已生成: {output_path}")


# 测试示例
class ExampleTestCase(TestCase):
    """示例测试用例"""
    
    def test_example_pass(self):
        """通过示例测试"""
        self.assertTrue(True)
        self.assertEqual(1, 1)
    
    def test_example_fail(self):
        """失败示例测试"""
        self.assertFalse(True, "此测试预期失败")
    
    def test_example_error(self):
        """错误示例测试"""
        raise ValueError("测试错误")
    
    def test_example_performance(self):
        """性能测试示例"""
        def test_func():
            time.sleep(0.01)
        
        stats = self.measure_performance(test_func, iterations=10)
        self.assertLess(stats['avg_time'], 0.1)


if __name__ == '__main__':
    # 运行示例测试
    unittest.main(verbosity=2)
