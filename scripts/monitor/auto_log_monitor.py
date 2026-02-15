#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化日志检测脚本 - Automated Log Monitoring
用于自动化扫描和分析系统日志文件，检测异常或错误信息

功能:
- 定期扫描日志文件
- 检测错误和警告模式
- 发送实时警报
- 生成日志分析报告
- 支持多种日志格式

使用方法:
    python auto_log_monitor.py                    # 启动监控
    python auto_log_monitor.py --scan             # 单次扫描
    python auto_log_monitor.py --report           # 生成报告
    python auto_log_monitor.py --config <file>    # 指定配置文件

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月10日
"""

import json
import os
import re
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 配置日志
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "auto_log_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoLogMonitor:
    """自动化日志监控器"""

    # 默认配置
    DEFAULT_CONFIG = {
        'scan_interval': 60,  # 扫描间隔（秒）
        'log_files': [
            'logs/app.log',
            'logs/error.log',
            'logs/monitor.log'
        ],
        'alert_thresholds': {
            'error_count': 5,      # 错误数量阈值
            'warning_count': 10,   # 警告数量阈值
            'critical_keywords': [  # 关键错误关键词
                'CRITICAL', 'FATAL', 'PANIC',
                'Exception', 'Traceback', 'Segmentation fault'
            ],
            'error_patterns': [     # 错误模式
                r'ERROR.*',
                r'Exception.*',
                r'Failed to.*',
                r'Connection refused',
                r'Timeout.*'
            ]
        },
        'alert_cooldown': 300,  # 警报冷却时间（秒）
        'max_log_size': 10 * 1024 * 1024,  # 最大日志文件大小（10MB）
        'retention_days': 7     # 日志保留天数
    }

    def __init__(self, config_file: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.is_running = False
        self.monitor_thread = None
        self.last_scan_time = None
        self.last_alert_time = {}
        self.scan_stats = {
            'total_scans': 0,
            'errors_found': 0,
            'warnings_found': 0,
            'alerts_sent': 0,
            'last_scan_duration': 0
        }

        # 加载配置
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)

        self.base_dir = Path(__file__).parent.parent.parent

    def load_config(self, config_file: str):
        """加载配置文件"""
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self.config.update(user_config)
            logger.info(f"已加载配置文件: {config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控已在运行中")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("自动化日志监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("自动化日志监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                start_time = time.time()
                self.scan_logs()
                self.scan_stats['last_scan_duration'] = time.time() - start_time
                self.last_scan_time = datetime.now()

                # 等待下次扫描
                time.sleep(self.config['scan_interval'])

            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(10)  # 出错后等待10秒再试

    def scan_logs(self) -> Dict[str, Any]:
        """扫描日志文件"""
        scan_results = {
            'timestamp': datetime.now().isoformat(),
            'files_scanned': 0,
            'errors_found': [],
            'warnings_found': [],
            'critical_issues': [],
            'file_stats': {}
        }

        for log_file in self.config['log_files']:
            file_path = self.base_dir / log_file

            if not file_path.exists():
                continue

            try:
                scan_results['files_scanned'] += 1

                # 检查文件大小
                file_size = file_path.stat().st_size
                if file_size > self.config['max_log_size']:
                    scan_results['critical_issues'].append({
                        'type': 'file_too_large',
                        'file': str(log_file),
                        'size': file_size,
                        'max_size': self.config['max_log_size']
                    })

                # 读取新内容（最后1分钟的内容）
                new_lines = self._read_recent_lines(file_path, minutes=1)
                file_results = self._analyze_log_content(new_lines, log_file)

                scan_results['errors_found'].extend(file_results['errors'])
                scan_results['warnings_found'].extend(file_results['warnings'])
                scan_results['critical_issues'].extend(file_results['critical'])
                scan_results['file_stats'][str(log_file)] = file_results['stats']

            except Exception as e:
                logger.error(f"扫描日志文件 {log_file} 失败: {e}")
                scan_results['critical_issues'].append({
                    'type': 'scan_error',
                    'file': str(log_file),
                    'error': str(e)
                })

        # 更新统计
        self.scan_stats['total_scans'] += 1
        self.scan_stats['errors_found'] = len(scan_results['errors_found'])
        self.scan_stats['warnings_found'] = len(scan_results['warnings_found'])

        # 检查是否需要发送警报
        self._check_alerts(scan_results)

        return scan_results

    def _read_recent_lines(self, file_path: Path, minutes: int = 1) -> List[str]:
        """读取最近几分钟的日志行"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取最后1000行
                lines = []
                for line in f:
                    lines.append(line.strip())

                if len(lines) > 1000:
                    lines = lines[-1000:]

                # 过滤最近几分钟的行
                recent_lines = []
                cutoff_time = datetime.now() - timedelta(minutes=minutes)

                for line in reversed(lines):
                    try:
                        # 尝试解析时间戳（多种格式）
                        timestamp = None

                        # ISO格式: 2026-01-30T10:00:00
                        iso_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                        if iso_match:
                            timestamp = datetime.fromisoformat(iso_match.group(1))

                        # 标准格式: 2026-01-30 10:00:00
                        std_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if std_match and not timestamp:
                            timestamp = datetime.strptime(std_match.group(1), '%Y-%m-%d %H:%M:%S')

                        if timestamp and timestamp >= cutoff_time:
                            recent_lines.append(line)
                        elif timestamp and timestamp < cutoff_time:
                            break  # 超出时间范围，停止

                    except:
                        # 如果无法解析时间戳，假设是最近的
                        recent_lines.append(line)

                return recent_lines

        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")
            return []

    def _analyze_log_content(self, lines: List[str], log_file: str) -> Dict[str, Any]:
        """分析日志内容"""
        results = {
            'errors': [],
            'warnings': [],
            'critical': [],
            'stats': {
                'total_lines': len(lines),
                'error_lines': 0,
                'warning_lines': 0,
                'critical_lines': 0
            }
        }

        for line in lines:
            line_lower = line.lower()

            # 检查关键错误关键词
            for keyword in self.config['alert_thresholds']['critical_keywords']:
                if keyword.lower() in line_lower:
                    results['critical'].append({
                        'file': log_file,
                        'line': line,
                        'keyword': keyword,
                        'timestamp': datetime.now().isoformat()
                    })
                    results['stats']['critical_lines'] += 1
                    break

            # 检查错误模式
            for pattern in self.config['alert_thresholds']['error_patterns']:
                if re.search(pattern, line, re.IGNORECASE):
                    results['errors'].append({
                        'file': log_file,
                        'line': line,
                        'pattern': pattern,
                        'timestamp': datetime.now().isoformat()
                    })
                    results['stats']['error_lines'] += 1
                    break

            # 检查警告
            if 'warning' in line_lower or 'warn' in line_lower:
                results['warnings'].append({
                    'file': log_file,
                    'line': line,
                    'timestamp': datetime.now().isoformat()
                })
                results['stats']['warning_lines'] += 1

        return results

    def _check_alerts(self, scan_results: Dict[str, Any]):
        """检查是否需要发送警报"""
        current_time = time.time()

        # 错误数量警报
        error_count = len(scan_results['errors_found'])
        if error_count >= self.config['alert_thresholds']['error_count']:
            alert_key = 'error_threshold'
            if self._should_send_alert(alert_key):
                self._send_alert('error_threshold', {
                    'error_count': error_count,
                    'threshold': self.config['alert_thresholds']['error_count'],
                    'recent_errors': scan_results['errors_found'][:5]
                })
                self.last_alert_time[alert_key] = current_time

        # 警告数量警报
        warning_count = len(scan_results['warnings_found'])
        if warning_count >= self.config['alert_thresholds']['warning_count']:
            alert_key = 'warning_threshold'
            if self._should_send_alert(alert_key):
                self._send_alert('warning_threshold', {
                    'warning_count': warning_count,
                    'threshold': self.config['alert_thresholds']['warning_count'],
                    'recent_warnings': scan_results['warnings_found'][:5]
                })
                self.last_alert_time[alert_key] = current_time

        # 关键问题警报
        if scan_results['critical_issues']:
            alert_key = 'critical_issues'
            if self._should_send_alert(alert_key):
                self._send_alert('critical_issues', {
                    'issues': scan_results['critical_issues']
                })
                self.last_alert_time[alert_key] = current_time

    def _should_send_alert(self, alert_key: str) -> bool:
        """检查是否应该发送警报（冷却时间检查）"""
        if alert_key not in self.last_alert_time:
            return True

        time_since_last = time.time() - self.last_alert_time[alert_key]
        return time_since_last >= self.config['alert_cooldown']

    def _send_alert(self, alert_type: str, data: Dict[str, Any]):
        """发送警报"""
        self.scan_stats['alerts_sent'] += 1

        alert_message = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # 记录到日志
        logger.warning(f"日志监控警报: {alert_type} - {data}")

        # 这里可以集成其他警报系统（如邮件、Slack等）
        # 例如：发送到监控API
        try:
            # 通知监控应用
            monitor_app_path = self.base_dir / "src" / "backend" / "monitor_app.py"
            if monitor_app_path.exists():
                # 这里可以调用monitor_app的日志记录功能
                pass
        except Exception as e:
            logger.error(f"发送警报失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'scan_stats': self.scan_stats,
            'config': self.config,
            'last_alerts': {
                key: datetime.fromtimestamp(ts).isoformat()
                for key, ts in self.last_alert_time.items()
            }
        }

    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        status = self.get_status()

        # 执行一次扫描获取最新数据
        if self.is_running:
            recent_scan = self.scan_logs()
        else:
            recent_scan = None

        report = {
            'generated_at': datetime.now().isoformat(),
            'monitor_status': status,
            'recent_scan': recent_scan,
            'configuration': self.config,
            'recommendations': self._generate_recommendations(status, recent_scan)
        }

        return report

    def _generate_recommendations(self, status: Dict[str, Any], recent_scan: Optional[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []

        if not status['is_running']:
            recommendations.append("建议启动自动化日志监控")

        if status['scan_stats']['errors_found'] > 10:
            recommendations.append("错误数量较多，建议检查系统状态")

        if recent_scan and recent_scan['critical_issues']:
            recommendations.append("检测到关键问题，建议立即处理")

        if status['scan_stats']['alerts_sent'] > 5:
            recommendations.append("警报频率较高，可能需要调整阈值")

        return recommendations

    def print_status(self):
        """打印监控状态"""
        status = self.get_status()

        print("\n" + "=" * 70)
        print("📋 自动化日志监控状态")
        print("=" * 70)

        print(f"运行状态: {'🟢 运行中' if status['is_running'] else '🔴 已停止'}")
        print(f"最后扫描: {status['last_scan_time'] or '从未'}")

        stats = status['scan_stats']
        print(f"\n📊 统计信息:")
        print(f"   总扫描次数: {stats['total_scans']}")
        print(f"   发现错误: {stats['errors_found']}")
        print(f"   发现警告: {stats['warnings_found']}")
        print(f"   发送警报: {stats['alerts_sent']}")
        print(f"   最后扫描耗时: {stats['last_scan_duration']:.2f}秒")

        if status['last_alerts']:
            print(f"\n🚨 最近警报:")
            for alert_type, timestamp in status['last_alerts'].items():
                print(f"   {alert_type}: {timestamp}")

        print("=" * 70 + "\n")


def run_auto_log_monitor_api(action: str = 'status') -> Dict[str, Any]:
    """API接口：自动化日志监控"""
    monitor = AutoLogMonitor()

    try:
        if action == 'start':
            monitor.start_monitoring()
            return {'success': True, 'message': '监控已启动'}
        elif action == 'stop':
            monitor.stop_monitoring()
            return {'success': True, 'message': '监控已停止'}
        elif action == 'scan':
            results = monitor.scan_logs()
            return {'success': True, 'data': results}
        elif action == 'report':
            report = monitor.generate_report()
            return {'success': True, 'data': report}
        else:  # status
            status = monitor.get_status()
            return {'success': True, 'data': status}

    except Exception as e:
        logger.error(f"自动化日志监控API错误: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='自动化日志监控工具')
    parser.add_argument('--start', action='store_true', help='启动监控')
    parser.add_argument('--stop', action='store_true', help='停止监控')
    parser.add_argument('--scan', action='store_true', help='执行单次扫描')
    parser.add_argument('--status', action='store_true', help='显示状态')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--config', type=str, help='配置文件路径')

    args = parser.parse_args()

    monitor = AutoLogMonitor(args.config)

    try:
        if args.start:
            monitor.start_monitoring()
            print("✅ 自动化日志监控已启动")
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\n👋 监控已停止")

        elif args.stop:
            monitor.stop_monitoring()
            print("✅ 监控已停止")

        elif args.scan:
            results = monitor.scan_logs()
            print(json.dumps(results, ensure_ascii=False, indent=2))

        elif args.report:
            report = monitor.generate_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))

        else:  # 默认显示状态
            monitor.print_status()

    except Exception as e:
        print(f"❌ 错误: {e}")
        exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化日志检测脚本 - Automated Log Monitoring
用于自动化扫描和分析系统日志文件，检测异常或错误信息

功能:
- 定期扫描日志文件
- 检测错误和警告模式
- 发送实时警报
- 生成日志分析报告
- 支持多种日志格式

使用方法:
    python auto_log_monitor.py                    # 启动监控
    python auto_log_monitor.py --scan             # 单次扫描
    python auto_log_monitor.py --report           # 生成报告
    python auto_log_monitor.py --config <file>    # 指定配置文件

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月10日
"""

import json
import os
import re
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 配置日志
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "auto_log_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoLogMonitor:
    """自动化日志监控器"""

    # 默认配置
    DEFAULT_CONFIG = {
        'scan_interval': 60,  # 扫描间隔（秒）
        'log_files': [
            'logs/app.log',
            'logs/error.log',
            'logs/monitor.log'
        ],
        'alert_thresholds': {
            'error_count': 5,      # 错误数量阈值
            'warning_count': 10,   # 警告数量阈值
            'critical_keywords': [  # 关键错误关键词
                'CRITICAL', 'FATAL', 'PANIC',
                'Exception', 'Traceback', 'Segmentation fault'
            ],
            'error_patterns': [     # 错误模式
                r'ERROR.*',
                r'Exception.*',
                r'Failed to.*',
                r'Connection refused',
                r'Timeout.*'
            ]
        },
        'alert_cooldown': 300,  # 警报冷却时间（秒）
        'max_log_size': 10 * 1024 * 1024,  # 最大日志文件大小（10MB）
        'retention_days': 7     # 日志保留天数
    }

    def __init__(self, config_file: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.is_running = False
        self.monitor_thread = None
        self.last_scan_time = None
        self.last_alert_time = {}
        self.scan_stats = {
            'total_scans': 0,
            'errors_found': 0,
            'warnings_found': 0,
            'alerts_sent': 0,
            'last_scan_duration': 0
        }

        # 加载配置
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)

        self.base_dir = Path(__file__).parent.parent.parent

    def load_config(self, config_file: str):
        """加载配置文件"""
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self.config.update(user_config)
            logger.info(f"已加载配置文件: {config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控已在运行中")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("自动化日志监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("自动化日志监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                start_time = time.time()
                self.scan_logs()
                self.scan_stats['last_scan_duration'] = time.time() - start_time
                self.last_scan_time = datetime.now()

                # 等待下次扫描
                time.sleep(self.config['scan_interval'])

            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(10)  # 出错后等待10秒再试

    def scan_logs(self) -> Dict[str, Any]:
        """扫描日志文件"""
        scan_results = {
            'timestamp': datetime.now().isoformat(),
            'files_scanned': 0,
            'errors_found': [],
            'warnings_found': [],
            'critical_issues': [],
            'file_stats': {}
        }

        for log_file in self.config['log_files']:
            file_path = self.base_dir / log_file

            if not file_path.exists():
                continue

            try:
                scan_results['files_scanned'] += 1

                # 检查文件大小
                file_size = file_path.stat().st_size
                if file_size > self.config['max_log_size']:
                    scan_results['critical_issues'].append({
                        'type': 'file_too_large',
                        'file': str(log_file),
                        'size': file_size,
                        'max_size': self.config['max_log_size']
                    })

                # 读取新内容（最后1分钟的内容）
                new_lines = self._read_recent_lines(file_path, minutes=1)
                file_results = self._analyze_log_content(new_lines, log_file)

                scan_results['errors_found'].extend(file_results['errors'])
                scan_results['warnings_found'].extend(file_results['warnings'])
                scan_results['critical_issues'].extend(file_results['critical'])
                scan_results['file_stats'][str(log_file)] = file_results['stats']

            except Exception as e:
                logger.error(f"扫描日志文件 {log_file} 失败: {e}")
                scan_results['critical_issues'].append({
                    'type': 'scan_error',
                    'file': str(log_file),
                    'error': str(e)
                })

        # 更新统计
        self.scan_stats['total_scans'] += 1
        self.scan_stats['errors_found'] = len(scan_results['errors_found'])
        self.scan_stats['warnings_found'] = len(scan_results['warnings_found'])

        # 检查是否需要发送警报
        self._check_alerts(scan_results)

        return scan_results

    def _read_recent_lines(self, file_path: Path, minutes: int = 1) -> List[str]:
        """读取最近几分钟的日志行"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取最后1000行
                lines = []
                for line in f:
                    lines.append(line.strip())

                if len(lines) > 1000:
                    lines = lines[-1000:]

                # 过滤最近几分钟的行
                recent_lines = []
                cutoff_time = datetime.now() - timedelta(minutes=minutes)

                for line in reversed(lines):
                    try:
                        # 尝试解析时间戳（多种格式）
                        timestamp = None

                        # ISO格式: 2026-01-30T10:00:00
                        iso_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                        if iso_match:
                            timestamp = datetime.fromisoformat(iso_match.group(1))

                        # 标准格式: 2026-01-30 10:00:00
                        std_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if std_match and not timestamp:
                            timestamp = datetime.strptime(std_match.group(1), '%Y-%m-%d %H:%M:%S')

                        if timestamp and timestamp >= cutoff_time:
                            recent_lines.append(line)
                        elif timestamp and timestamp < cutoff_time:
                            break  # 超出时间范围，停止

                    except:
                        # 如果无法解析时间戳，假设是最近的
                        recent_lines.append(line)

                return recent_lines

        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")
            return []

    def _analyze_log_content(self, lines: List[str], log_file: str) -> Dict[str, Any]:
        """分析日志内容"""
        results = {
            'errors': [],
            'warnings': [],
            'critical': [],
            'stats': {
                'total_lines': len(lines),
                'error_lines': 0,
                'warning_lines': 0,
                'critical_lines': 0
            }
        }

        for line in lines:
            line_lower = line.lower()

            # 检查关键错误关键词
            for keyword in self.config['alert_thresholds']['critical_keywords']:
                if keyword.lower() in line_lower:
                    results['critical'].append({
                        'file': log_file,
                        'line': line,
                        'keyword': keyword,
                        'timestamp': datetime.now().isoformat()
                    })
                    results['stats']['critical_lines'] += 1
                    break

            # 检查错误模式
            for pattern in self.config['alert_thresholds']['error_patterns']:
                if re.search(pattern, line, re.IGNORECASE):
                    results['errors'].append({
                        'file': log_file,
                        'line': line,
                        'pattern': pattern,
                        'timestamp': datetime.now().isoformat()
                    })
                    results['stats']['error_lines'] += 1
                    break

            # 检查警告
            if 'warning' in line_lower or 'warn' in line_lower:
                results['warnings'].append({
                    'file': log_file,
                    'line': line,
                    'timestamp': datetime.now().isoformat()
                })
                results['stats']['warning_lines'] += 1

        return results

    def _check_alerts(self, scan_results: Dict[str, Any]):
        """检查是否需要发送警报"""
        current_time = time.time()

        # 错误数量警报
        error_count = len(scan_results['errors_found'])
        if error_count >= self.config['alert_thresholds']['error_count']:
            alert_key = 'error_threshold'
            if self._should_send_alert(alert_key):
                self._send_alert('error_threshold', {
                    'error_count': error_count,
                    'threshold': self.config['alert_thresholds']['error_count'],
                    'recent_errors': scan_results['errors_found'][:5]
                })
                self.last_alert_time[alert_key] = current_time

        # 警告数量警报
        warning_count = len(scan_results['warnings_found'])
        if warning_count >= self.config['alert_thresholds']['warning_count']:
            alert_key = 'warning_threshold'
            if self._should_send_alert(alert_key):
                self._send_alert('warning_threshold', {
                    'warning_count': warning_count,
                    'threshold': self.config['alert_thresholds']['warning_count'],
                    'recent_warnings': scan_results['warnings_found'][:5]
                })
                self.last_alert_time[alert_key] = current_time

        # 关键问题警报
        if scan_results['critical_issues']:
            alert_key = 'critical_issues'
            if self._should_send_alert(alert_key):
                self._send_alert('critical_issues', {
                    'issues': scan_results['critical_issues']
                })
                self.last_alert_time[alert_key] = current_time

    def _should_send_alert(self, alert_key: str) -> bool:
        """检查是否应该发送警报（冷却时间检查）"""
        if alert_key not in self.last_alert_time:
            return True

        time_since_last = time.time() - self.last_alert_time[alert_key]
        return time_since_last >= self.config['alert_cooldown']

    def _send_alert(self, alert_type: str, data: Dict[str, Any]):
        """发送警报"""
        self.scan_stats['alerts_sent'] += 1

        alert_message = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # 记录到日志
        logger.warning(f"日志监控警报: {alert_type} - {data}")

        # 这里可以集成其他警报系统（如邮件、Slack等）
        # 例如：发送到监控API
        try:
            # 通知监控应用
            monitor_app_path = self.base_dir / "src" / "backend" / "monitor_app.py"
            if monitor_app_path.exists():
                # 这里可以调用monitor_app的日志记录功能
                pass
        except Exception as e:
            logger.error(f"发送警报失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'scan_stats': self.scan_stats,
            'config': self.config,
            'last_alerts': {
                key: datetime.fromtimestamp(ts).isoformat()
                for key, ts in self.last_alert_time.items()
            }
        }

    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        status = self.get_status()

        # 执行一次扫描获取最新数据
        if self.is_running:
            recent_scan = self.scan_logs()
        else:
            recent_scan = None

        report = {
            'generated_at': datetime.now().isoformat(),
            'monitor_status': status,
            'recent_scan': recent_scan,
            'configuration': self.config,
            'recommendations': self._generate_recommendations(status, recent_scan)
        }

        return report

    def _generate_recommendations(self, status: Dict[str, Any], recent_scan: Optional[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []

        if not status['is_running']:
            recommendations.append("建议启动自动化日志监控")

        if status['scan_stats']['errors_found'] > 10:
            recommendations.append("错误数量较多，建议检查系统状态")

        if recent_scan and recent_scan['critical_issues']:
            recommendations.append("检测到关键问题，建议立即处理")

        if status['scan_stats']['alerts_sent'] > 5:
            recommendations.append("警报频率较高，可能需要调整阈值")

        return recommendations

    def print_status(self):
        """打印监控状态"""
        status = self.get_status()

        print("\n" + "=" * 70)
        print("📋 自动化日志监控状态")
        print("=" * 70)

        print(f"运行状态: {'🟢 运行中' if status['is_running'] else '🔴 已停止'}")
        print(f"最后扫描: {status['last_scan_time'] or '从未'}")

        stats = status['scan_stats']
        print(f"\n📊 统计信息:")
        print(f"   总扫描次数: {stats['total_scans']}")
        print(f"   发现错误: {stats['errors_found']}")
        print(f"   发现警告: {stats['warnings_found']}")
        print(f"   发送警报: {stats['alerts_sent']}")
        print(f"   最后扫描耗时: {stats['last_scan_duration']:.2f}秒")

        if status['last_alerts']:
            print(f"\n🚨 最近警报:")
            for alert_type, timestamp in status['last_alerts'].items():
                print(f"   {alert_type}: {timestamp}")

        print("=" * 70 + "\n")


def run_auto_log_monitor_api(action: str = 'status') -> Dict[str, Any]:
    """API接口：自动化日志监控"""
    monitor = AutoLogMonitor()

    try:
        if action == 'start':
            monitor.start_monitoring()
            return {'success': True, 'message': '监控已启动'}
        elif action == 'stop':
            monitor.stop_monitoring()
            return {'success': True, 'message': '监控已停止'}
        elif action == 'scan':
            results = monitor.scan_logs()
            return {'success': True, 'data': results}
        elif action == 'report':
            report = monitor.generate_report()
            return {'success': True, 'data': report}
        else:  # status
            status = monitor.get_status()
            return {'success': True, 'data': status}

    except Exception as e:
        logger.error(f"自动化日志监控API错误: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='自动化日志监控工具')
    parser.add_argument('--start', action='store_true', help='启动监控')
    parser.add_argument('--stop', action='store_true', help='停止监控')
    parser.add_argument('--scan', action='store_true', help='执行单次扫描')
    parser.add_argument('--status', action='store_true', help='显示状态')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--config', type=str, help='配置文件路径')

    args = parser.parse_args()

    monitor = AutoLogMonitor(args.config)

    try:
        if args.start:
            monitor.start_monitoring()
            print("✅ 自动化日志监控已启动")
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\n👋 监控已停止")

        elif args.stop:
            monitor.stop_monitoring()
            print("✅ 监控已停止")

        elif args.scan:
            results = monitor.scan_logs()
            print(json.dumps(results, ensure_ascii=False, indent=2))

        elif args.report:
            report = monitor.generate_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))

        else:  # 默认显示状态
            monitor.print_status()

    except Exception as e:
        print(f"❌ 错误: {e}")
        exit(1)


if __name__ == '__main__':
    main()
