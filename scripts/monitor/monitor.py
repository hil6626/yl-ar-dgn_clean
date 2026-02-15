#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控守护进程 - Monitor
提供一个简单的监控守护进程示例，定期收集资源使用并生成报告

用法:
    python monitor.py --interval 10

作者: AI 全栈技术员
版本: 1.0
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    import psutil
except ImportError:
    psutil = None

BASE_DIR = Path(__file__).parent.parent.parent
REPORT_DIR = BASE_DIR / 'reports'
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class HealthMonitor:
    def __init__(self):
        self.interval = 30

    def get_cpu_info(self) -> Dict:
        if psutil is None:
            return {'error': 'psutil not installed'}
        return {'percent': psutil.cpu_percent(interval=1)}

    def get_memory_info(self) -> Dict:
        if psutil is None:
            return {'error': 'psutil not installed'}
        m = psutil.virtual_memory()
        return {'total': m.total, 'available': m.available, 'percent': m.percent}

    def get_disk_info(self) -> Dict:
        if psutil is None:
            return {'error': 'psutil not installed'}
        d = psutil.disk_usage('/')
        return {'total': d.total, 'used': d.used, 'free': d.free, 'percent': d.percent}

    def get_network_info(self) -> Dict:
        if psutil is None:
            return {'error': 'psutil not installed'}
        net = psutil.net_io_counters()
        return {'bytes_sent': net.bytes_sent, 'bytes_recv': net.bytes_recv}

    def check_health(self) -> Dict:
        report = {
            'time': datetime.now().isoformat(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info()
        }
        return report

    def generate_report(self, report: Dict) -> str:
        filepath = REPORT_DIR / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return str(filepath)

    def run_continuous(self, interval: int = 30):
        self.interval = interval
        try:
            while True:
                report = self.check_health()
                path = self.generate_report(report)
                print(f"[{datetime.now().isoformat()}] 报告已写入: {path}")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print('\n停止监控')


def main():
    parser = argparse.ArgumentParser(description='实时监控守护进程')
    parser.add_argument('--interval', type=int, default=30, help='采样间隔秒')
    parser.add_argument('--once', action='store_true', help='仅采样一次')
    args = parser.parse_args()

    hm = HealthMonitor()
    if args.once:
        report = hm.check_health()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        hm.run_continuous(args.interval)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康监控脚本 - Monitor Script (优化版)
用于监控系统健康状态，包括 CPU、内存、磁盘、网络等资源使用情况

功能:
- 实时监控系统资源使用情况
- 支持超时控制和重试机制
- 支持分级告警
- 支持定时任务模式

使用方法:
    python monitor.py --json             # JSON 输出模式
    python monitor.py --report           # 生成报告
    python monitor.py --interval 10      # 每10秒更新一次
    python monitor.py --threshold 80     # 设置告警阈值80%

作者: AI 全栈技术员
版本: 2.0
创建日期: 2026年1月30日
更新日期: 2026年2月
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil 未安装，将使用系统命令替代")

try:
    from scripts.monitor.utils import retry, timeout, TimeoutException
except ImportError:
    def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
        def decorator(func):
            def wrapper(*args, **kwargs):
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions:
                        if attempt < max_attempts:
                            time.sleep(delay)
                return None
            return wrapper
        return decorator
    
    def timeout(seconds):
        def decorator(func):
            def wrapper(*args, **kwargs):
                import threading
                result = [None]
                def worker():
                    try:
                        result[0] = func(*args, **kwargs)
                    except:
                        pass
                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
                thread.join(seconds)
                if thread.is_alive():
                    raise TimeoutException(f"Timeout after {seconds}s")
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
        logging.FileHandler(LOG_DIR / "monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """健康监控类"""
    
    DEFAULT_THRESHOLDS = {
        'cpu': 80.0,
        'memory': 80.0,
        'disk': 85.0,
        'network': 1000,
        'load': 5.0
    }
    
    def __init__(self, thresholds=None, verbose=False, max_retries=3, global_timeout=30):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.verbose = verbose
        self.max_retries = max_retries
        self.global_timeout = global_timeout
        self.start_time = datetime.now()
        self.base_dir = Path(__file__).parent.parent.parent
        self.logs_dir = self.base_dir / "logs"
        
        self._check_count = 0
        self._success_count = 0
        self._failure_count = 0
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_cpu_info(self):
        """获取 CPU 使用信息"""
        self._check_count += 1
        if not PSUTIL_AVAILABLE:
            self._failure_count += 1
            return {'percent': 0, 'cores': [0], 'frequency': 'N/A'}
        
        try:
            percent = psutil.cpu_percent(interval=1)
            cores = psutil.cpu_percent(interval=None, percpu=True)
            freq = psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'
            self._success_count += 1
            logger.debug(f"CPU信息采集成功: {percent}%")
            return {'percent': percent, 'cores': cores, 'frequency': freq}
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取CPU信息失败: {e}")
            return {'percent': 0, 'cores': [0], 'frequency': 'N/A'}
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_memory_info(self):
        """获取内存使用信息"""
        if not PSUTIL_AVAILABLE:
            self._failure_count += 1
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}
        
        try:
            memory = psutil.virtual_memory()
            self._success_count += 1
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取内存信息失败: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_disk_info(self, mount_point='/'):
        """获取磁盘使用信息"""
        if not PSUTIL_AVAILABLE:
            self._failure_count += 1
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
        """获取网络使用信息"""
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
    
    @retry(max_attempts=3, delay=1, exceptions=(Exception,))
    @timeout(seconds=10)
    def get_process_info(self):
        """获取进程信息"""
        if not PSUTIL_AVAILABLE:
            return {'count': 0, 'running': 0, 'sleeping': 0}
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            running = len([p for p in processes if p.get('status') == psutil.STATUS_RUNNING])
            sleeping = len([p for p in processes if p.get('status') == psutil.STATUS_SLEEPING])
            self._success_count += 1
            
            return {'total': len(processes), 'running': running, 'sleeping': sleeping}
        except Exception as e:
            self._failure_count += 1
            logger.error(f"获取进程信息失败: {e}")
            return {'total': 0, 'running': 0, 'sleeping': 0}
    
    def get_uptime(self):
        """获取系统运行时间"""
        try:
            uptime_seconds = time.time() - self.start_time.timestamp()
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"
    
    def format_bytes(self, bytes_value):
        """格式化字节单位"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} PB"
    
    def check_health(self):
        """执行健康检查（带超时保护）"""
        try:
            import threading
            result = [None]
            exception = [None]
            
            def worker():
                try:
                    cpu_info = self.get_cpu_info()
                    memory_info = self.get_memory_info()
                    disk_info = self.get_disk_info()
                    network_info = self.get_network_info()
                    process_info = self.get_process_info()
                    
                    status, warnings = self._calculate_health_status(
                        cpu_info, memory_info, disk_info
                    )
                    
                    result[0] = {
                        'timestamp': datetime.now().isoformat(),
                        'status': status,
                        'warnings': warnings,
                        'cpu': cpu_info,
                        'memory': memory_info,
                        'disk': disk_info,
                        'network': network_info,
                        'processes': process_info,
                        'uptime': self.get_uptime()
                    }
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            thread.join(self.global_timeout)
            
            if thread.is_alive():
                logger.warning("健康检查超时")
                return self._get_health_fallback()
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return self._get_health_fallback()
    
    def _get_health_fallback(self):
        """健康检查的降级方案"""
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'Unknown',
            'warnings': ['健康检查执行失败'],
            'cpu': {'percent': 0},
            'memory': {'percent': 0},
            'disk': {'percent': 0},
            'network': {'bytes_sent': 0, 'bytes_recv': 0},
            'processes': {'total': 0},
            'uptime': 'Unknown'
        }
    
    def _calculate_health_status(self, cpu_info, memory_info, disk_info):
        """计算健康状态（分级告警）"""
        status = 'OK'
        warnings = []
        
        # CPU告警
        if cpu_info['percent'] > 95:
            status = 'Critical'
            warnings.append(f"CPU使用率过高: {cpu_info['percent']}%")
        elif cpu_info['percent'] > self.thresholds['cpu']:
            status = 'Warning' if status == 'OK' else status
            warnings.append(f"CPU使用率偏高: {cpu_info['percent']}%")
        
        # 内存告警
        if memory_info['percent'] > 95:
            status = 'Critical'
            warnings.append(f"内存使用率过高: {memory_info['percent']}%")
        elif memory_info['percent'] > self.thresholds['memory']:
            status = 'Warning' if status == 'OK' else status
            warnings.append(f"内存使用率偏高: {memory_info['percent']}%")
        
        # 磁盘告警
        if disk_info['percent'] > 95:
            status = 'Critical'
            warnings.append(f"磁盘使用率过高: {disk_info['percent']}%")
        elif disk_info['percent'] > self.thresholds['disk']:
            status = 'Warning' if status == 'OK' else status
            warnings.append(f"磁盘使用率偏高: {disk_info['percent']}%")
        
        return status, warnings
    
    def print_console(self, health_data):
        """控制台输出格式化结果"""
        print("\n" + "=" * 60)
        print("系统健康监控报告")
        print("=" * 60)
        print(f"时间: {health_data['timestamp']}")
        print(f"状态: {health_data['status']}")
        print(f"运行时间: {health_data['uptime']}")
        
        print("\nCPU 信息:")
        print(f"   使用率: {health_data['cpu']['percent']}%")
        
        print("\n内存信息:")
        mem = health_data['memory']
        print(f"   总计: {self.format_bytes(mem['total'])}")
        print(f"   已用: {self.format_bytes(mem['used'])}")
        print(f"   使用率: {mem['percent']}%")
        
        print("\n磁盘信息:")
        disk = health_data['disk']
        print(f"   使用率: {disk['percent']}%")
        
        print("\n网络信息:")
        net = health_data['network']
        print(f"   已发送: {self.format_bytes(net['bytes_sent'])}")
        print(f"   已接收: {self.format_bytes(net['bytes_recv'])}")
        
        if health_data['warnings']:
            print("\n告警信息:")
            for warning in health_data['warnings']:
                print(f"   - {warning}")
        
        print("=" * 60 + "\n")
    
    def generate_report(self, output_path=None):
        """生成健康报告"""
        health_data = self.check_health()
        
        if output_path is None:
            output_path = self.logs_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'report_type': 'System Health Report',
            'generated_at': datetime.now().isoformat(),
            'monitor_version': '2.0',
            'health_data': health_data,
            'thresholds': self.thresholds,
            'stats': {
                'total_checks': self._check_count,
                'success': self._success_count,
                'failed': self._failure_count
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"健康报告已生成: {output_path}")
            print(f"✅ 健康报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"生成健康报告失败: {e}")
            print(f"❌ 生成健康报告失败: {e}")
        
        return report
    
    def run_continuous(self, interval=5):
        """持续监控模式"""
        print(f"开始持续监控，间隔: {interval}秒")
        print("按 Ctrl+C 退出\n")
        
        try:
            while True:
                health_data = self.check_health()
                self.print_console(health_data)
                
                if health_data['status'] != 'OK':
                    logger.warning(f"Health warning: {health_data['warnings']}")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")


def main():
    parser = argparse.ArgumentParser(
        description='系统健康监控脚本（优化版）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--json', '-j', action='store_true', help='JSON 输出模式')
    parser.add_argument('--report', '-r', action='store_true', help='生成健康报告')
    parser.add_argument('--output', '-o', type=str, default=None, help='报告输出路径')
    parser.add_argument('--interval', '-i', type=int, default=5, help='监控间隔（秒）')
    parser.add_argument('--threshold', '-t', type=float, default=None, help='设置告警阈值（百分比）')
    parser.add_argument('--retries', type=int, default=3, help='最大重试次数')
    parser.add_argument('--timeout', type=int, default=30, help='全局超时时间（秒）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出模式')
    
    args = parser.parse_args()
    
    thresholds = None
    if args.threshold:
        thresholds = {
            'cpu': args.threshold,
            'memory': args.threshold,
            'disk': args.threshold,
            'network': 1000,
            'load': 5.0
        }
    
    monitor = HealthMonitor(
        thresholds=thresholds,
        verbose=args.verbose,
        max_retries=args.retries
    )
    
    try:
        if args.report:
            monitor.generate_report(args.output)
        elif args.json:
            health_data = monitor.check_health()
            print(json.dumps(health_data, ensure_ascii=False, indent=2))
        else:
            monitor.run_continuous(args.interval)
    
    except Exception as e:
        logger.error(f"监控出错: {e}")
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
