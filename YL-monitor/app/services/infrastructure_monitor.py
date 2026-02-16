#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础设施层监控器
提供进程级、端口级、文件系统级的细粒度监控
"""

import os
import time
import socket
import psutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ProcessMetrics:
    """进程指标数据类"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_rss: int
    memory_vms: int
    memory_percent: float
    num_threads: int
    num_fds: int
    open_files: int
    connections: int
    io_read_bytes: int
    io_write_bytes: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessMonitor:
    """
    进程级监控器
    
    监控指定服务的进程级指标，包括：
    - CPU 使用率
    - 内存使用详情（RSS/VMS/共享内存）
    - IO 统计（读写字节数）
    - 线程数、文件描述符数
    - 网络连接数
    - 进程状态
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 5  # 缓存5秒
    
    def collect_process_metrics(self, pid: int) -> Optional[ProcessMetrics]:
        """
        采集指定进程的详细指标
        
        Args:
            pid: 进程ID
            
        Returns:
            ProcessMetrics 对象，如果进程不存在返回 None
        """
        try:
            process = psutil.Process(pid)
            
            # 获取进程信息
            with process.oneshot():
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_info = process.memory_info()
                io_counters = process.io_counters()
                
                metrics = ProcessMetrics(
                    pid=pid,
                    name=process.name(),
                    status=process.status(),
                    cpu_percent=cpu_percent,
                    memory_rss=memory_info.rss,
                    memory_vms=memory_info.vms,
                    memory_percent=process.memory_percent(),
                    num_threads=process.num_threads(),
                    num_fds=process.num_fds() if hasattr(process, 'num_fds') else 0,
                    open_files=len(process.open_files()),
                    connections=len(process.connections()),
                    io_read_bytes=io_counters.read_bytes,
                    io_write_bytes=io_counters.write_bytes,
                    timestamp=datetime.now().isoformat()
                )
                
                return metrics
                
        except psutil.NoSuchProcess:
            logger.warning(f"进程不存在: PID {pid}")
            return None
        except Exception as e:
            logger.error(f"采集进程指标失败 PID {pid}: {e}")
            return None
    
    def find_service_pids(self, service_name: str) -> List[int]:
        """
        根据服务名称查找进程ID
        
        Args:
            service_name: 服务名称（如 'yl-monitor', 'ar-backend', 'user-gui'）
            
        Returns:
            匹配的进程ID列表
        """
        pids = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # 匹配规则
                    if (service_name == 'yl-monitor' and
                            'start_server.py' in cmdline):
                        pids.append(proc.info['pid'])
                    elif (service_name == 'ar-backend' and 
                          'monitor_server.py' in cmdline):
                        pids.append(proc.info['pid'])
                    elif (service_name == 'user-gui' and 
                          'user/main.py' in cmdline):
                        pids.append(proc.info['pid'])
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"查找服务进程失败 {service_name}: {e}")
        
        return pids
    
    def monitor_service(self, service_name: str) -> Optional[ProcessMetrics]:
        """
        监控指定服务（自动查找进程）
        
        Args:
            service_name: 服务名称
            
        Returns:
            进程指标，如果服务未运行返回 None
        """
        # 检查缓存
        cache_key = f"service_{service_name}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_data
        
        # 查找进程
        pids = self.find_service_pids(service_name)
        
        if not pids:
            logger.warning(f"服务未运行: {service_name}")
            return None
        
        # 监控第一个匹配的进程
        metrics = self.collect_process_metrics(pids[0])
        
        # 更新缓存
        if metrics:
            self._cache[cache_key] = (time.time(), metrics)
        
        return metrics
    
    def get_all_services_metrics(self) -> Dict[str, Any]:
        """
        获取所有服务的进程指标
        
        Returns:
            包含所有服务指标的字典
        """
        services = ['yl-monitor', 'ar-backend', 'user-gui']
        result = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        for service in services:
            metrics = self.monitor_service(service)
            if metrics:
                result["services"][service] = metrics.to_dict()
            else:
                result["services"][service] = {
                    "status": "not_running",
                    "timestamp": datetime.now().isoformat()
                }
        
        return result


@dataclass
class PortMetrics:
    """端口指标数据类"""
    host: str
    port: int
    connectable: bool
    connect_time_ms: Optional[float]
    response_time_ms: Optional[float]
    error_code: Optional[int]
    error_message: Optional[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PortMonitor:
    """
    端口级监控器
    
    监控服务端口的连通性和响应性能：
    - TCP 连接测试
    - 连接建立时间
    - 服务响应时间
    - 错误码分析
    """
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    def check_port(self, host: str, port: int) -> PortMetrics:
        """
        检查端口连通性和性能
        
        Args:
            host: 主机地址
            port: 端口号
            
        Returns:
            PortMetrics 对象
        """
        metrics = PortMetrics(
            host=host,
            port=port,
            connectable=False,
            connect_time_ms=None,
            response_time_ms=None,
            error_code=None,
            error_message=None,
            timestamp=datetime.now().isoformat()
        )
        
        # 测试 TCP 连接
        start_time = time.time()
        sock = None
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((host, port))
            connect_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            metrics.connect_time_ms = connect_time
            
            if result == 0:
                metrics.connectable = True
                
                # 测试 HTTP 响应（如果是 HTTP 服务）
                try:
                    sock.send(
                        b"GET /health HTTP/1.1\r\nHost:0.0.0.0\r\n\r\n"
                    )
                    response_start = time.time()
                    
                    # 等待响应
                    sock.settimeout(2.0)
                    _ = sock.recv(1024)  # 读取响应但不使用
                    response_time = (time.time() - response_start) * 1000
                    
                    metrics.response_time_ms = response_time
                    
                except socket.timeout:
                    metrics.response_time_ms = None
                except Exception as e:
                    logger.debug(f"HTTP 响应测试失败 {host}:{port}: {e}")
            else:
                metrics.error_code = result
                metrics.error_message = (
                    os.strerror(result) if hasattr(os, 'strerror') 
                    else f"Error {result}"
                )
                
        except socket.timeout:
            metrics.error_message = "Connection timeout"
        except Exception as e:
            metrics.error_message = str(e)
            logger.error(f"端口检查失败 {host}:{port}: {e}")
        finally:
            if sock:
                sock.close()
        
        return metrics
    
    def monitor_service_ports(self) -> Dict[str, Any]:
        """
        监控所有服务的端口
        
        Returns:
            所有服务端口的监控结果
        """
        services = {
            'yl-monitor': ('0.0.0.0', 5500),
            'ar-backend': ('0.0.0.0', 5501),
            'user-gui': ('0.0.0.0', 5502)
        }
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "ports": {}
        }
        
        for service, (host, port) in services.items():
            metrics = self.check_port(host, port)
            result["ports"][service] = metrics.to_dict()
        
        return result


@dataclass
class FilesystemMetrics:
    """文件系统指标数据类"""
    path: str
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float
    file_count: int
    dir_count: int
    total_size: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FilesystemMonitor:
    """
    文件系统监控器
    
    监控文件系统使用情况：
    - 磁盘空间使用（总/已用/可用）
    - 文件和目录统计
    - 大文件识别
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存（文件系统扫描较耗时）
    
    def monitor_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """
        监控磁盘使用情况
        
        Args:
            path: 要监控的路径
            
        Returns:
            磁盘使用指标
        """
        try:
            usage = psutil.disk_usage(path)
            
            return {
                "path": path,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"监控磁盘使用失败 {path}: {e}")
            return {
                "path": path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def scan_directory(
        self, path: str, max_depth: int = 2
    ) -> FilesystemMetrics:
        """
        扫描目录统计文件信息
        
        Args:
            path: 目录路径
            max_depth: 最大扫描深度
            
        Returns:
            FilesystemMetrics 对象
        """
        # 检查缓存
        cache_key = f"scan_{path}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_data
        
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"路径不存在: {path}")
            
            # 获取磁盘使用
            disk_usage = psutil.disk_usage(path)
            
            # 统计文件
            file_count = 0
            dir_count = 0
            total_size = 0
            
            # 限制扫描深度
            for root, dirs, files in os.walk(path):
                # 计算当前深度
                current_depth = (
                    root.count(os.sep) - path.count(os.sep)
                )
                if current_depth >= max_depth:
                    del dirs[:]  # 不继续深入
                    continue
                
                dir_count += len(dirs)
                file_count += len(files)
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        pass
            
            metrics = FilesystemMetrics(
                path=path,
                disk_total=disk_usage.total,
                disk_used=disk_usage.used,
                disk_free=disk_usage.free,
                disk_percent=disk_usage.percent,
                file_count=file_count,
                dir_count=dir_count,
                total_size=total_size,
                timestamp=datetime.now().isoformat()
            )
            
            # 更新缓存
            self._cache[cache_key] = (time.time(), metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"扫描目录失败 {path}: {e}")
            raise
    
    def find_large_files(self, path: str, size_threshold_mb: int = 100) -> List[Dict[str, Any]]:
        """
        查找大文件
        
        Args:
            path: 搜索路径
            size_threshold_mb: 大小阈值（MB）
            
        Returns:
            大文件列表
        """
        large_files = []
        threshold_bytes = size_threshold_mb * 1024 * 1024
        
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        
                        if size > threshold_bytes:
                            large_files.append({
                                "path": file_path,
                                "size": size,
                                "size_mb": round(size / (1024 * 1024), 2),
                                "modified": datetime.fromtimestamp(
                                    os.path.getmtime(file_path)
                                ).isoformat()
                            })
                            
                    except (OSError, FileNotFoundError):
                        pass
                
                # 限制扫描范围
                if len(large_files) >= 50:
                    break
        
        except Exception as e:
            logger.error(f"查找大文件失败 {path}: {e}")
        
        # 按大小排序
        large_files.sort(key=lambda x: x['size'], reverse=True)
        return large_files[:20]  # 返回最大的20个
    
    def monitor_project_directories(self) -> Dict[str, Any]:
        """
        监控项目关键目录
        
        Returns:
            各目录的监控结果
        """
        project_root = Path(__file__).parent.parent.parent.parent
        
        directories = {
            'logs': project_root / 'logs',
            'data': project_root / 'data',
            'temp': project_root / 'temp',
            'backups': project_root / 'YL-monitor' / 'backups'
        }
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "directories": {}
        }
        
        for name, path in directories.items():
            try:
                if path.exists():
                    metrics = self.scan_directory(str(path), max_depth=1)
                    result["directories"][name] = metrics.to_dict()
                else:
                    result["directories"][name] = {
                        "path": str(path),
                        "status": "not_exists",
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                result["directories"][name] = {
                    "path": str(path),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # 添加大文件信息
        result["large_files"] = self.find_large_files(
            str(project_root),
            size_threshold_mb=50
        )
        
        return result


class InfrastructureCollector:
    """
    基础设施指标采集器
    
    整合所有基础设施层监控器，提供统一接口
    """
    
    def __init__(self):
        self.process_monitor = ProcessMonitor()
        self.port_monitor = PortMonitor()
        self.filesystem_monitor = FilesystemMonitor()
    
    def collect_all(self) -> Dict[str, Any]:
        """
        采集所有基础设施层指标
        
        Returns:
            完整的监控数据
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "layer": "L1_infrastructure",
            "processes": self.process_monitor.get_all_services_metrics(),
            "ports": self.port_monitor.monitor_service_ports(),
            "filesystem": self.filesystem_monitor.monitor_project_directories()
        }
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        获取指定服务的健康状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            健康状态详情
        """
        # 进程状态
        process_metrics = self.process_monitor.monitor_service(service_name)
        
        # 端口状态
        port_map = {
            'yl-monitor': 5500,
            'ar-backend': 5501,
            'user-gui': 5502
        }
        
        port_metrics = None
        if service_name in port_map:
            port_metrics = self.port_monitor.check_port('0.0.0.0', port_map[service_name])
        
        # 综合评估
        is_healthy = (
            process_metrics is not None and 
            process_metrics.status == 'running' and
            (port_metrics is None or port_metrics.connectable)
        )
        
        return {
            "service": service_name,
            "healthy": is_healthy,
            "process": process_metrics.to_dict() if process_metrics else None,
            "port": port_metrics.to_dict() if port_metrics else None,
            "timestamp": datetime.now().isoformat()
        }


# 全局采集器实例
infrastructure_collector = InfrastructureCollector()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("基础设施层监控测试")
    print("=" * 60)
    
    collector = InfrastructureCollector()
    
    # 测试进程监控
    print("\n1. 进程监控:")
    process_metrics = collector.process_monitor.get_all_services_metrics()
    for service, metrics in process_metrics['services'].items():
        if 'status' in metrics and metrics['status'] == 'not_running':
            print(f"  ⚠️  {service}: 未运行")
        else:
            cpu = metrics.get('cpu_percent', 0)
            mem = metrics.get('memory_percent', 0)
            print(f"  ✅ {service}: CPU {cpu:.1f}%, "
              f"内存 {mem:.1f}%")
    
    # 测试端口监控
    print("\n2. 端口监控:")
    port_metrics = collector.port_monitor.monitor_service_ports()
    for service, metrics in port_metrics['ports'].items():
        status = "✅ 正常" if metrics['connectable'] else "❌ 异常"
        print(f"  {status} {service} ({metrics['host']}:{metrics['port']}): "
              f"连接时间 {metrics.get('connect_time_ms', 'N/A')}ms")
    
    # 测试文件系统监控
    print("\n3. 文件系统监控:")
    fs_metrics = collector.filesystem_monitor.monitor_project_directories()
    for name, metrics in fs_metrics['directories'].items():
        if 'disk_percent' in metrics:
            print(f"  📁 {name}: {metrics['disk_percent']:.1f}% 使用率, "
                  f"{metrics['file_count']} 文件")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
