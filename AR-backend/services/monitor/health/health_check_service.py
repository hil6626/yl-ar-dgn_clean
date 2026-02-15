#!/usr/bin/env python3
"""
健康检查处理器 - 业务逻辑实现
被路由调度器调用，不直接暴露接口
"""

import psutil
import logging
from datetime import datetime

class HealthCheckService:
    """健康检查业务逻辑"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.checks = {
            'cpu': self.check_cpu,
            'memory': self.check_memory,
            'disk': self.check_disk,
            'network': self.check_network,
            'services': self.check_services
        }

    def perform_check(self):
        """执行所有健康检查"""
        self.logger.info("执行健康检查")
        results = {}
        for check_name, check_func in self.checks.items():
            try:
                results[check_name] = check_func()
                results[check_name]['status'] = 'healthy'
            except Exception as e:
                self.logger.error(f"健康检查 {check_name} 失败: {str(e)}")
                results[check_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return {
            'overall_status': self._calculate_overall_status(results),
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }

    def check_cpu(self):
        """CPU 健康检查"""
        cpu_percent = psutil.cpu_percent(interval=1)
        return {
            'usage_percent': cpu_percent,
            'cores': psutil.cpu_count(),
            'healthy': cpu_percent < 80
        }

    def check_memory(self):
        """内存健康检查"""
        memory = psutil.virtual_memory()
        return {
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'usage_percent': memory.percent,
            'healthy': memory.percent < 85
        }

    def check_disk(self):
        """磁盘健康检查"""
        disk = psutil.disk_usage('/')
        return {
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'usage_percent': disk.percent,
            'healthy': disk.percent < 90
        }

    def check_network(self):
        """网络健康检查"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'healthy': True  # 简化检查
        }

    def check_services(self):
        """服务健康检查"""
        services = ['python', 'flask']  # 示例服务
        results = {}
        for service in services:
            results[service] = self._check_process_exists(service)
        return results

    def _check_process_exists(self, process_name):
        """检查进程是否存在"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return {'running': True, 'pid': proc.info['pid']}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {'running': False}

    def _calculate_overall_status(self, results):
        """计算整体状态"""
        unhealthy_checks = [k for k, v in results.items()
                          if v.get('status') == 'error' or not v.get('healthy', True)]
        return 'unhealthy' if unhealthy_checks else 'healthy'
