#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细进程监控器 - 增强版
提供进程级详细监控指标，5秒采集频率
"""

import psutil
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessMetrics:
    """进程详细指标"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_rss: int  # bytes
    memory_vms: int  # bytes
    memory_percent: float
    num_threads: int
    num_fds: int
    open_files: int
    connections: int
    io_read_bytes: int
    io_write_bytes: int
    context_switches: int
    cpu_times_user: float
    cpu_times_system: float
    create_time: float
    runtime_seconds: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DetailedProcessMonitor:
    """
    详细进程监控器
    监控指定服务的详细进程指标
    """
    
    def __init__(self, service_name: str, process_keywords: List[str]):
        self.service_name = service_name
        self.process_keywords = process_keywords
        self.metrics_history: List[ProcessMetrics] = []
        self.max_history = 1000  # 保留最近1000条记录
        self.running = False
        
    def find_process(self) -> Optional[psutil.Process]:
        """查找目标进程"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                name = proc.info['name'] or ''
                
                # 匹配关键词
                for keyword in self.process_keywords:
                    if keyword in cmdline or keyword in name:
                        return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def collect_metrics(self) -> Optional[ProcessMetrics]:
        """采集详细进程指标"""
        try:
            proc = self.find_process()
            if not proc:
                return None
            
            # 基础信息
            pid = proc.pid
            name = proc.name()
            status = proc.status()
            create_time = proc.create_time()
            runtime_seconds = time.time() - create_time
            
            # CPU和内存
            cpu_percent = proc.cpu_percent(interval=0.1)
            memory_info = proc.memory_info()
            memory_rss = memory_info.rss
            memory_vms = memory_info.vms
            memory_percent = proc.memory_percent()
            
            # 线程和文件描述符
            num_threads = proc.num_threads()
            try:
                num_fds = proc.num_fds()
            except:
                num_fds = 0
            
            # 打开文件数
            try:
                open_files = len(proc.open_files())
            except:
                open_files = 0
            
            # 网络连接
            try:
                connections = len(proc.connections())
            except:
                connections = 0
            
            # IO统计
            io_counters = proc.io_counters()
            io_read_bytes = io_counters.read_bytes
            io_write_bytes = io_counters.write_bytes
            
            # CPU时间
            cpu_times = proc.cpu_times()
            cpu_times_user = cpu_times.user
            cpu_times_system = cpu_times.system
            
            # 上下文切换（Linux only）
            try:
                ctx_switches = proc.num_ctx_switches()
                context_switches = ctx_switches.voluntary + ctx_switches.involuntary
            except:
                context_switches = 0
            
            metrics = ProcessMetrics(
                pid=pid,
                name=name,
                status=status,
                cpu_percent=cpu_percent,
                memory_rss=memory_rss,
                memory_vms=memory_vms,
                memory_percent=memory_percent,
                num_threads=num_threads,
                num_fds=num_fds,
                open_files=open_files,
                connections=connections,
                io_read_bytes=io_read_bytes,
                io_write_bytes=io_write_bytes,
                context_switches=context_switches,
                cpu_times_user=cpu_times_user,
                cpu_times_system=cpu_times_system,
                create_time=create_time,
                runtime_seconds=runtime_seconds,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # 保存历史
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"采集进程指标失败: {e}")
            return None
    
    async def start_monitoring(self, interval: int = 5):
        """启动持续监控"""
        self.running = True
        logger.info(f"启动详细进程监控: {self.service_name} (间隔: {interval}秒)")
        
        while self.running:
            try:
                metrics = self.collect_metrics()
                if metrics:
                    logger.debug(f"{self.service_name} - CPU: {metrics.cpu_percent:.1f}%, "
                               f"内存: {metrics.memory_percent:.1f}%, "
                               f"线程: {metrics.num_threads}")
                else:
                    logger.warning(f"未找到进程: {self.service_name}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info(f"停止详细进程监控: {self.service_name}")
    
    def get_latest_metrics(self) -> Optional[ProcessMetrics]:
        """获取最新指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, count: int = 100) -> List[ProcessMetrics]:
        """获取历史指标"""
        return self.metrics_history[-count:]
    
    def get_average_metrics(self, seconds: int = 60) -> Optional[Dict]:
        """获取平均值统计"""
        if not self.metrics_history:
            return None
        
        # 筛选最近seconds秒的指标
        cutoff_time = time.time() - seconds
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        # 计算平均值
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_threads = sum(m.num_threads for m in recent_metrics) / len(recent_metrics)
        
        return {
            "service_name": self.service_name,
            "sample_count": len(recent_metrics),
            "avg_cpu_percent": round(avg_cpu, 2),
            "avg_memory_percent": round(avg_memory, 2),
            "avg_threads": round(avg_threads, 1),
            "period_seconds": seconds,
            "timestamp": datetime.utcnow().isoformat()
        }


# 预定义的监控配置
MONITOR_CONFIGS = {
    "yl-monitor": {
        "keywords": ["start_server.py", "YL-monitor", "fastapi", "uvicorn"]
    },
    "ar-backend": {
        "keywords": ["monitor_server.py", "AR-backend", "flask"]
    },
    "user-gui": {
        "keywords": ["main.py", "user", "pyqt", "PyQt5"]
    }
}


class ProcessMonitorManager:
    """进程监控管理器"""
    
    def __init__(self):
        self.monitors: Dict[str, DetailedProcessMonitor] = {}
        self.tasks = []
        
    def create_monitor(self, service_name: str, keywords: List[str]) -> DetailedProcessMonitor:
        """创建监控器"""
        monitor = DetailedProcessMonitor(service_name, keywords)
        self.monitors[service_name] = monitor
        return monitor
    
    def create_default_monitors(self):
        """创建默认监控器"""
        for service_name, config in MONITOR_CONFIGS.items():
            self.create_monitor(service_name, config["keywords"])
    
    async def start_all(self, interval: int = 5):
        """启动所有监控器"""
        for service_name, monitor in self.monitors.items():
            task = asyncio.create_task(monitor.start_monitoring(interval))
            self.tasks.append(task)
            logger.info(f"启动监控任务: {service_name}")
    
    def stop_all(self):
        """停止所有监控器"""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
    
    def get_all_metrics(self) -> Dict[str, Optional[ProcessMetrics]]:
        """获取所有服务的最新指标"""
        return {
            name: monitor.get_latest_metrics()
            for name, monitor in self.monitors.items()
        }
    
    def get_all_averages(self, seconds: int = 60) -> Dict[str, Optional[Dict]]:
        """获取所有服务的平均值"""
        return {
            name: monitor.get_average_metrics(seconds)
            for name, monitor in self.monitors.items()
        }


# 全局监控管理器实例
monitor_manager = ProcessMonitorManager()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        # 创建监控器
        manager = ProcessMonitorManager()
        manager.create_default_monitors()
        
        # 启动监控
        await manager.start_all(interval=5)
        
        # 运行30秒
        await asyncio.sleep(30)
        
        # 获取统计
        metrics = manager.get_all_metrics()
        for name, m in metrics.items():
            if m:
                print(f"\n{name}:")
                print(f"  PID: {m.pid}")
                print(f"  CPU: {m.cpu_percent:.1f}%")
                print(f"  内存: {m.memory_percent:.1f}%")
                print(f"  线程: {m.num_threads}")
                print(f"  运行时间: {m.runtime_seconds:.0f}秒")
        
        # 停止监控
        manager.stop_all()
    
    asyncio.run(test())
