#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源监控脚本 - Resource Monitor
收集系统资源的快照并提供汇总

用法:
    python resource_monitor.py --json

作者: AI 全栈技术员
版本: 1.0
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    import psutil
except ImportError:
    psutil = None

BASE_DIR = Path(__file__).parent.parent.parent


class ResourceMonitor:
    def snapshot(self) -> Dict:
        if psutil is None:
            return {'error': 'psutil not installed'}
        return {
            'time': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'root': psutil.disk_usage('/').percent
            }
        }


def main():
    parser = argparse.ArgumentParser(description='资源监控工具')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()

    rm = ResourceMonitor()
    snap = rm.snapshot()
    if args.json:
        print(json.dumps(snap, ensure_ascii=False, indent=2))
    else:
        print(snap)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源监控脚本 - Resource Monitor (优化版)
用于实时监控系统资源使用情况

功能:
- 实时监控系统资源使用情况
- 支持超时控制和重试机制
- 支持阈值告警
- 可生成资源使用报告

使用方法:
    python resource_monitor.py --report         # 生成报告
    python resource_monitor.py --interval 10    # 每10秒更新
    python resource_monitor.py --json           # JSON 输出

作者: AI 全栈技术员
版本: 2.0
创建日期: 2026年1月30日
更新日期: 2026年2月
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil 未安装，将使用受限功能")

# 导入工具模块
try:
    from scripts.monitor.utils import retry, timeout, TimeoutException
except ImportError:
    UTILS_AVAILABLE = False
    def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
        def decorator(func):
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts:
                            time.sleep(delay)
                raise last_exception
            return wrapper
        return decorator
    
    def timeout(seconds):
        def decorator(func):
            def wrapper(*args, **kwargs):
                import threading
                result = [None]
                exception = [None]
                def worker():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e
                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
                thread.join(seconds)
                if thread.is_alive():
                    raise TimeoutException(f"Function timed out after {seconds} seconds")
                if exception[0]:
                    raise exception[0]
                return result[0]
            return wrapper
        return decorator
    
    class TimeoutException(Exception):
        pass

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "resource_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ResourceMonitor:
    """资源监控器类"""
    
    DEFAULT_THRESHOLDS = {
        'cpu_percent': 80.0,
        'memory_percent': 80.0,
        'disk_percent': 85.0,
        'network_bytes_sent_rate': 1024 * 1024,
        'network_bytes_recv_rate': 1024 * 1024,
    }
    
    def __init__(self, thresholds=None, history_size=60, verbose=False,
                 max_retries=3, global_timeout=30):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.history_size = history_size
        self.verbose = verbose
        self.max_retries = max_retries
        self.global_timeout = global_timeout
        
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        
        self.last_network_data = None
        self.last_network_time = None
        
        self.base_dir = Path(__file__).parent.parent.parent
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self._collection_count = 0
        self._success_count = 0
        self._failure_count = 0
    
    @retry(max_attempts=3, delay=1, exceptions=(psutil.NoSuchProcess, psutil.AccessDenied))
    @timeout(seconds=10)
    def get_cpu_info(self):
        """获取 CPU 信息"""
        self._collection_count += 1
        
        if not PSUTIL_AVAILABLE:
            self._failure_count += 1
            return {'percent': 0, 'cores': [0], 'load_avg': 'N/A', 'count': 0}
        
        try:
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            percent = psutil.cpu_percent(interval=1)
            cores = psutil.cpu_percent(interval=None, percpu=True)
            count = psutil.cpu_count()
            self._success_count += 1
            logger.debug(f"CPU信息采集成功: {percent}%")
            return {'percent': percent, 'cores': cores, 'load_avg': load_avg, 'count': count}
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取CPU信息失败: {e}")
            return {'percent': 0, 'cores': [0], 'load_avg': (0, 0, 0), 'count': 0}
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_memory_info(self):
        """获取内存信息"""
        if not PSUTIL_AVAILABLE:
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            self._success_count += 1
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            }
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取内存信息失败: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_disk_info(self, mount_point='/'):
        """获取磁盘信息"""
        if not PSUTIL_AVAILABLE:
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
        try:
            disk = psutil.disk_usage(mount_point)
            self._success_count += 1
            return {'total': disk.total, 'used': disk.used, 'free': disk.free, 'percent': disk.percent}
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取磁盘信息失败: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_network_info(self):
        """获取网络信息"""
        if not PSUTIL_AVAILABLE:
            return {'bytes_sent': 0, 'bytes_recv': 0}
        try:
            network = psutil.net_io_counters()
            self._success_count += 1
            return {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取网络信息失败: {e}")
            return {'bytes_sent': 0, 'bytes_recv': 0}
    
    def format_bytes(self, bytes_value):
        """格式化字节单位"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(bytes_value) < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} PB"
    
    def get_all_resources(self):
        """获取所有资源信息（带超时保护）"""
        try:
            import threading
            result = [None]
            exception = [None]
            
            def worker():
                try:
                    cpu = self.get_cpu_info()
                    memory = self.get_memory_info()
                    disk = self.get_disk_info()
                    network = self.get_network_info()
                    
                    current_time = time.time()
                    network_rate = {'sent_rate': 0, 'recv_rate': 0}
                    
                    if self.last_network_data and self.last_network_time:
                        time_diff = current_time - self.last_network_time
                        if time_diff > 0:
                            network_rate['sent_rate'] = (network['bytes_sent'] - self.last_network_data['bytes_sent']) / time_diff
                            network_rate['recv_rate'] = (network['bytes_recv'] - self.last_network_data['bytes_recv']) / time_diff
                    
                    self.last_network_data = network
                    self.last_network_time = current_time
                    
                    self.cpu_history.append(cpu['percent'])
                    self.memory_history.append(memory['percent'])
                    self.disk_history.append(disk['percent'])
                    self.network_history.append(network_rate['recv_rate'])
                    
                    result[0] = {
                        'timestamp': datetime.now().isoformat(),
                        'cpu': cpu,
                        'memory': memory,
                        'disk': disk,
                        'network': network,
                        'network_rate': network_rate
                    }
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            thread.join(self.global_timeout)
            
            if thread.is_alive():
                logger.warning("获取资源信息超时")
                return self._get_resources_fallback()
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
            
        except Exception as e:
            logger.error(f"获取资源信息失败: {e}")
            return self._get_resources_fallback()
    
    def _get_resources_fallback(self):
        """获取资源信息的降级方案"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {'percent': 0, 'cores': [0]},
            'memory': {'percent': 0, 'total': 0},
            'disk': {'percent': 0},
            'network': {'bytes_sent': 0, 'bytes_recv': 0},
            'network_rate': {'sent_rate': 0, 'recv_rate': 0}
        }
    
    def check_thresholds(self, resources):
        """检查阈值告警"""
        alerts = []
        
        if resources['cpu']['percent'] > self.thresholds['cpu_percent']:
            level = 'critical' if resources['cpu']['percent'] > 95 else 'warning'
            alerts.append({'type': 'CPU', 'level': level, 'message': f"CPU使用率过高: {resources['cpu']['percent']}%"})
        
        if resources['memory']['percent'] > self.thresholds['memory_percent']:
            level = 'critical' if resources['memory']['percent'] > 95 else 'warning'
            alerts.append({'type': 'Memory', 'level': level, 'message': f"内存使用率过高: {resources['memory']['percent']}%"})
        
        if resources['disk']['percent'] > self.thresholds['disk_percent']:
            level = 'critical' if resources['disk']['percent'] > 95 else 'warning'
            alerts.append({'type': 'Disk', 'level': level, 'message': f"磁盘使用率过高: {resources['disk']['percent']}%"})
        
        return alerts
    
    def get_averages(self):
        """获取历史平均值"""
        return {
            'cpu_avg': sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
            'memory_avg': sum(self.memory_history) / len(self.memory_history) if self.memory_history else 0
        }
    
    def print_console(self, resources, alerts=None):
        """控制台输出资源信息"""
        if alerts is None:
            alerts = self.check_thresholds(resources)
        
        print("\n" + "=" * 70)
        print("系统资源监控")
        print("=" * 70)
        
        print(f"\n时间: {resources['timestamp']}")
        
        print("\nCPU 信息:")
        print(f"   使用率: {resources['cpu']['percent']}%")
        print(f"   核心数: {resources['cpu']['count']}")
        
        print("\n内存信息:")
        mem = resources['memory']
        print(f"   总计: {self.format_bytes(mem['total'])}")
        print(f"   已用: {self.format_bytes(mem['used'])}")
        print(f"   使用率: {mem['percent']}%")
        
        print("\n磁盘信息:")
        disk = resources['disk']
        print(f"   使用率: {disk['percent']}%")
        
        print("\n网络信息:")
        net = resources['network']
        print(f"   已发送: {self.format_bytes(net['bytes_sent'])}")
        print(f"   已接收: {self.format_bytes(net['bytes_recv'])}")
        
        if alerts:
            print("\n告警:")
            for alert in alerts:
                icon = '🔴' if alert['level'] == 'critical' else '🟡'
                print(f"   {icon} [{alert['type']}] {alert['message']}")
        
        avgs = self.get_averages()
        print(f"\n历史平均 - CPU: {avgs['cpu_avg']:.1f}%, Memory: {avgs['memory_avg']:.1f}%")
        print("=" * 70 + "\n")
    
    def generate_report(self, output_path=None):
        """生成资源报告"""
        resources = self.get_all_resources()
        alerts = self.check_thresholds(resources)
        avgs = self.get_averages()
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.logs_dir / f"resource_report_{timestamp}.json"
        
        report = {
            'report_type': 'System Resource Report',
            'generated_at': datetime.now().isoformat(),
            'monitor_version': '2.0',
            'resources': resources,
            'alerts': alerts,
            'averages': avgs,
            'thresholds': self.thresholds,
            'stats': {
                'total_collections': self._collection_count,
                'success': self._success_count,
                'failed': self._failure_count
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"资源报告已生成: {output_path}")
            print(f"✅ 资源报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            print(f"❌ 生成报告失败: {e}")
        
        return report
    
    def run_continuous(self, interval=5):
        """持续监控模式"""
        print(f"开始资源监控，间隔: {interval}秒")
        print("按 Ctrl+C 退出\n")
        
        try:
            while True:
                resources = self.get_all_resources()
                alerts = self.check_thresholds(resources)
                self.print_console(resources, alerts)
                
                for alert in alerts:
                    logger.warning(f"Resource alert: {alert}")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")


def main():
    parser = argparse.ArgumentParser(description='系统资源监控工具（优化版）')
    parser.add_argument('--report', '-r', action='store_true', help='生成资源报告')
    parser.add_argument('--output', '-o', type=str, default=None, help='报告输出路径')
    parser.add_argument('--interval', '-i', type=int, default=5, help='监控间隔（秒）')
    parser.add_argument('--json', '-j', action='store_true', help='JSON 输出模式')
    parser.add_argument('--threshold', '-t', type=float, default=None, help='设置告警阈值')
    parser.add_argument('--retries', type=int, default=3, help='最大重试次数')
    parser.add_argument('--timeout', type=int, default=30, help='全局超时时间（秒）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出模式')
    
    args = parser.parse_args()
    
    thresholds = None
    if args.threshold:
        thresholds = {
            'cpu_percent': args.threshold,
            'memory_percent': args.threshold,
            'disk_percent': args.threshold,
            'network_bytes_sent_rate': 1024 * 1024,
            'network_bytes_recv_rate': 1024 * 1024
        }
    
    monitor = ResourceMonitor(
        thresholds=thresholds,
        verbose=args.verbose,
        max_retries=args.retries,
        global_timeout=args.timeout
    )
    
    try:
        if args.report:
            monitor.generate_report(args.output)
        elif args.json:
            resources = monitor.get_all_resources()
            print(json.dumps(resources, ensure_ascii=False, indent=2))
        else:
            monitor.run_continuous(args.interval)
    except Exception as e:
        logger.error(f"资源监控出错: {e}")
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
