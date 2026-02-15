#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试工具
AR 综合实时合成与监控系统

功能:
- 初始化时间测试
- 并发处理性能测试
- 资源使用监控
- 内存泄漏检测

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import sys
import os
import time
import psutil
import threading
import json
from typing import Dict, List, Any
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()

from camera import CameraModule
from audio_module import AudioModule
from processor_manager import ProcessorManager


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        self.start_time = time.time()

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        mem = self.process.memory_info()
        return {
            'rss': mem.rss / 1024 / 1024,  # MB
            'vms': mem.vms / 1024 / 1024,  # MB
            'percent': self.process.memory_percent()
        }

    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        return self.process.cpu_percent(interval=1.0)

    def benchmark_initialization(self) -> Dict[str, Any]:
        """测试模块初始化性能"""
        print("🔄 测试模块初始化性能...")

        results = {}

        # 测试 CameraModule 初始化
        start_time = time.time()
        camera = CameraModule()
        init_time = time.time() - start_time
        results['camera_init'] = {
            'time': init_time,
            'memory': self.get_memory_usage(),
            'success': True
        }

        # 测试 AudioModule 初始化
        start_time = time.time()
        audio = AudioModule()
        init_time = time.time() - start_time
        results['audio_init'] = {
            'time': init_time,
            'memory': self.get_memory_usage(),
            'success': True
        }

        # 测试 ProcessorManager 初始化
        start_time = time.time()
        manager = ProcessorManager()
        init_time = time.time() - start_time
        results['processor_init'] = {
            'time': init_time,
            'memory': self.get_memory_usage(),
            'success': True
        }

        return results

    def benchmark_concurrent_processing(self, duration: int = 10) -> Dict[str, Any]:
        """测试并发处理性能"""
        print(f"🔄 测试并发处理性能 ({duration}秒)...")

        results = {
            'duration': duration,
            'cpu_samples': [],
            'memory_samples': [],
            'frame_counts': []
        }

        # 启动摄像头
        camera = CameraModule()
        if not camera.start_capture():
            return {'error': '无法启动摄像头'}

        start_time = time.time()
        frame_count = 0

        try:
            while time.time() - start_time < duration:
                # 获取帧
                frame = camera.get_frame()
                if frame is not None:
                    frame_count += 1

                # 记录性能数据
                results['cpu_samples'].append(self.get_cpu_usage())
                results['memory_samples'].append(self.get_memory_usage())

                time.sleep(0.1)  # 10fps 采样

        finally:
            camera.stop_capture()

        results['frame_counts'] = frame_count
        results['fps_actual'] = frame_count / duration

        return results

    def benchmark_resource_monitoring(self, duration: int = 30) -> Dict[str, Any]:
        """测试资源监控稳定性"""
        print(f"🔄 测试资源监控稳定性 ({duration}秒)...")

        results = {
            'duration': duration,
            'cpu_stats': {'min': float('inf'), 'max': 0, 'avg': 0},
            'memory_stats': {'min': float('inf'), 'max': 0, 'avg': 0},
            'samples': []
        }

        samples = []
        start_time = time.time()

        while time.time() - start_time < duration:
            cpu = self.get_cpu_usage()
            memory = self.get_memory_usage()

            samples.append({
                'time': time.time() - start_time,
                'cpu': cpu,
                'memory': memory
            })

            time.sleep(1.0)

        # 计算统计数据
        cpu_values = [s['cpu'] for s in samples]
        memory_values = [s['memory']['percent'] for s in samples]

        results['cpu_stats'] = {
            'min': min(cpu_values),
            'max': max(cpu_values),
            'avg': sum(cpu_values) / len(cpu_values)
        }

        results['memory_stats'] = {
            'min': min(memory_values),
            'max': max(memory_values),
            'avg': sum(memory_values) / len(memory_values)
        }

        results['samples'] = samples

        return results

    def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整性能基准测试"""
        print("🚀 开始完整性能基准测试...")

        self.results = {
            'timestamp': time.time(),
            'tests': {}
        }

        # 1. 初始化性能测试
        self.results['tests']['initialization'] = self.benchmark_initialization()

        # 2. 并发处理测试
        self.results['tests']['concurrent'] = self.benchmark_concurrent_processing()

        # 3. 资源监控测试
        self.results['tests']['resources'] = self.benchmark_resource_monitoring()

        # 4. 总体统计
        self.results['summary'] = self._generate_summary()

        return self.results

    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试总结"""
        init_tests = self.results['tests']['initialization']
        concurrent_tests = self.results['tests']['concurrent']
        resource_tests = self.results['tests']['resources']

        # 检查是否达到性能目标
        targets = {
            'init_time_max': 5.0,  # 秒
            'memory_max': 800.0,   # MB
            'cpu_max': 80.0,       # %
            'fps_min': 25.0        # fps
        }

        summary = {
            'targets': targets,
            'results': {},
            'passed': True,
            'details': []
        }

        # 初始化时间检查
        total_init_time = sum(test['time'] for test in init_tests.values())
        summary['results']['init_time'] = total_init_time
        if total_init_time > targets['init_time_max']:
            summary['passed'] = False
            summary['details'].append(f"初始化时间过长: {total_init_time:.2f}s > {targets['init_time_max']}s")

        # 内存使用检查
        if 'concurrent' in self.results['tests']:
            memory_usage = concurrent_tests.get('memory_samples', [])
            if memory_usage:
                avg_memory = sum(s['percent'] for s in memory_usage) / len(memory_usage)
                summary['results']['memory_avg'] = avg_memory
                if avg_memory > targets['memory_max']:
                    summary['passed'] = False
                    summary['details'].append(f"内存使用过高: {avg_memory:.1f}% > {targets['memory_max']}%")

        # CPU使用检查
        if 'resources' in self.results['tests']:
            cpu_avg = resource_tests['cpu_stats']['avg']
            summary['results']['cpu_avg'] = cpu_avg
            if cpu_avg > targets['cpu_max']:
                summary['passed'] = False
                summary['details'].append(f"CPU使用过高: {cpu_avg:.1f}% > {targets['cpu_max']}%")

        # FPS检查
        if 'concurrent' in self.results['tests']:
            fps_actual = concurrent_tests.get('fps_actual', 0)
            summary['results']['fps_actual'] = fps_actual
            if fps_actual < targets['fps_min']:
                summary['passed'] = False
                summary['details'].append(f"FPS过低: {fps_actual:.1f} < {targets['fps_min']}")

        return summary

    def save_results(self, filename: str = None) -> str:
        """保存测试结果"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"

        filepath = Path(__file__).parent / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"✅ 测试结果已保存到: {filepath}")
        return str(filepath)

    def print_summary(self):
        """打印测试总结"""
        if not self.results:
            print("❌ 没有测试结果")
            return

        summary = self.results.get('summary', {})
        print("\n" + "="*50)
        print("📊 性能基准测试结果总结")
        print("="*50)

        if summary.get('passed', False):
            print("✅ 所有性能指标均达到要求！")
        else:
            print("❌ 部分性能指标未达到要求：")
            for detail in summary.get('details', []):
                print(f"  - {detail}")

        print("\n📈 详细指标:"        targets = summary.get('targets', {})
        results = summary.get('results', {})

        print(".2f"        print(".1f"        print(".1f"        print(".1f"
        print("\n🔍 测试详情:"        tests = self.results.get('tests', {})

        if 'initialization' in tests:
            init = tests['initialization']
            print(".2f"            print(".2f"            print(".2f"
        if 'concurrent' in tests:
            concurrent = tests['concurrent']
            print(".1f"            print(f"  - 处理帧数: {concurrent.get('frame_counts', 0)}")

        if 'resources' in tests:
            resources = tests['resources']
            cpu_stats = resources.get('cpu_stats', {})
            mem_stats = resources.get('memory_stats', {})
            print(".1f"            print(".1f"            print(".1f"            print(".1f"
        print("="*50)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='AR系统性能基准测试')
    parser.add_argument('--full', action='store_true', help='运行完整测试套件')
    parser.add_argument('--init-only', action='store_true', help='仅测试初始化性能')
    parser.add_argument('--concurrent', type=int, default=10, help='并发测试时长(秒)')
    parser.add_argument('--resources', type=int, default=30, help='资源监控时长(秒)')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')

    args = parser.parse_args()

    benchmark = PerformanceBenchmark()

    try:
        if args.full:
            results = benchmark.run_full_benchmark()
        elif args.init_only:
            results = {'tests': {'initialization': benchmark.benchmark_initialization()}}
        else:
            results = {
                'tests': {
                    'concurrent': benchmark.benchmark_concurrent_processing(args.concurrent),
                    'resources': benchmark.benchmark_resource_monitoring(args.resources)
                }
            }

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            benchmark.print_summary()

        if args.output:
            benchmark.save_results(args.output)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
