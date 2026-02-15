"""
告警监控服务

功能:
- 定时检查系统指标
- 触发告警规则
- 发送通知
- 与现有监控脚本集成

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import psutil
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from app.services.alert_service import get_alert_service, AlertService
from app.services.event_bus import EventBus, EventType
from app.models.alert import MetricType

logger = logging.getLogger(__name__)


class AlertMonitor:
    """告警监控器"""
    
    def __init__(self, check_interval: int = 60):
        """
        初始化告警监控器
        
        参数:
            check_interval: 检查间隔（秒），默认60秒
        """
        self.check_interval = check_interval
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._alert_service: Optional[AlertService] = None
        
        # 上次指标值（用于计算变化率）
        self._last_metrics: Dict[str, Any] = {}
        
        # 统计信息
        self._stats = {
            'checks_performed': 0,
            'alerts_triggered': 0,
            'errors': 0,
            'start_time': None
        }
    
    async def start(self):
        """启动监控"""
        if self.running:
            logger.warning("告警监控已在运行中")
            return
        
        self.running = True
        self._stats['start_time'] = datetime.utcnow()
        self._alert_service = get_alert_service()
        
        # 启动监控循环
        self._task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"告警监控已启动，检查间隔: {self.check_interval}秒")
        
        # 发布启动事件
        EventBus().publish_event(
            event_type=EventType.SYSTEM_STARTUP,
            source='alert_monitor',
            data={
                'component': 'alert_monitor',
                'status': 'started',
                'interval': self.check_interval
            }
        )
    
    async def stop(self):
        """停止监控"""
        if not self.running:
            return
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("告警监控已停止")
        
        # 发布停止事件
        EventBus().publish_event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            source='alert_monitor',
            data={
                'component': 'alert_monitor',
                'status': 'stopped',
                'stats': self._stats
            }
        )
    
    async def _monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                await self._check_all_metrics()
                self._stats['checks_performed'] += 1
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                self._stats['errors'] += 1
            
            # 等待下一次检查
            await asyncio.sleep(self.check_interval)
    
    async def _check_all_metrics(self):
        """检查所有系统指标"""
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        await self._check_metric(MetricType.CPU, cpu_percent)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        await self._check_metric(MetricType.MEMORY, memory.percent)
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        await self._check_metric(MetricType.DISK, disk_percent)
        
        # 系统负载
        load_avg = psutil.getloadavg()
        await self._check_metric(MetricType.LOAD, load_avg[0])  # 1分钟负载
        
        # 网络流量（计算变化率）
        net_io = psutil.net_io_counters()
        network_rate = self._calculate_network_rate(net_io)
        if network_rate is not None:
            await self._check_metric(MetricType.NETWORK, network_rate)
        
        # 进程数
        process_count = len(psutil.pids())
        await self._check_metric(MetricType.PROCESS, float(process_count))
        
        # 发布指标事件
        EventBus().publish_event(
            event_type=EventType.METRIC_CPU,
            source='alert_monitor',
            data={
                'value': cpu_percent,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        EventBus().publish_event(
            event_type=EventType.METRIC_MEMORY,
            source='alert_monitor',
            data={
                'value': memory.percent,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.debug(f"指标检查完成 - CPU: {cpu_percent}%, 内存: {memory.percent}%")
    
    async def _check_metric(self, metric_type: MetricType, value: float):
        """检查单个指标"""
        if self._alert_service:
            self._alert_service.check_alerts(metric_type, value)
    
    def _calculate_network_rate(self, net_io) -> Optional[float]:
        """计算网络流量变化率（KB/s）"""
        current_time = time.time()
        
        if 'network' in self._last_metrics:
            last_io, last_time = self._last_metrics['network']
            time_delta = current_time - last_time
            
            if time_delta > 0:
                # 计算总流量（发送 + 接收）
                bytes_sent_delta = net_io.bytes_sent - last_io.bytes_sent
                bytes_recv_delta = net_io.bytes_recv - last_io.bytes_recv
                total_bytes = bytes_sent_delta + bytes_recv_delta
                
                # 转换为 KB/s
                rate_kb_s = (total_bytes / 1024) / time_delta
                return rate_kb_s
        
        # 保存当前值
        self._last_metrics['network'] = (net_io, current_time)
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        uptime = None
        if self._stats['start_time']:
            uptime = (datetime.utcnow() - self._stats['start_time']).total_seconds()
        
        return {
            **self._stats,
            'running': self.running,
            'uptime_seconds': uptime,
            'check_interval': self.check_interval
        }
    
    async def force_check(self):
        """强制立即检查一次"""
        if not self.running:
            raise RuntimeError("监控未运行")
        
        await self._check_all_metrics()
        logger.info("强制指标检查完成")
    
    def update_interval(self, new_interval: int):
        """更新检查间隔"""
        self.check_interval = max(10, new_interval)  # 最小10秒
        logger.info(f"检查间隔已更新为: {self.check_interval}秒")


# 全局实例
_alert_monitor: Optional[AlertMonitor] = None


def get_alert_monitor() -> AlertMonitor:
    """获取告警监控器实例"""
    global _alert_monitor
    if _alert_monitor is None:
        _alert_monitor = AlertMonitor()
    return _alert_monitor


async def start_alert_monitor():
    """启动告警监控（便捷函数）"""
    monitor = get_alert_monitor()
    await monitor.start()
    return monitor


async def stop_alert_monitor():
    """停止告警监控（便捷函数）"""
    monitor = get_alert_monitor()
    await monitor.stop()
