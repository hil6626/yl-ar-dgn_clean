#!/usr/bin/env python3
"""
【文件功能】
队列监控器，提供任务队列状态监控和拥塞告警功能

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现队列监控核心功能

【依赖说明】
- 标准库: asyncio, json, logging, time, typing, datetime, collections
- 第三方库: 无
- 内部模块: app.services.event_bus

【使用示例】
```python
from app.services.queue_monitor import queue_monitor

# 注册队列
queue_monitor.register_queue("script_queue", script_queue_instance)

# 获取队列统计
stats = await queue_monitor.get_queue_stats()

# 检查拥塞
is_congested = await queue_monitor.check_congestion("script_queue")
```
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import deque
from enum import Enum


class QueueStatus(Enum):
    """【队列状态】队列运行状态"""
    HEALTHY = "healthy"                # 【健康】运行正常
    WARNING = "warning"                # 【警告】需要关注
    CRITICAL = "critical"              # 【紧急】严重拥塞
    UNKNOWN = "unknown"                # 【未知】状态未知


@dataclass
class QueueMetrics:
    """【队列指标】队列性能指标"""
    queue_name: str                    # 【队列名称】唯一标识
    pending_count: int = 0             # 【待处理】待处理任务数
    processing_count: int = 0          # 【处理中】正在处理的任务数
    completed_count: int = 0           # 【已完成】已完成任务数
    failed_count: int = 0              # 【失败】失败任务数
    avg_wait_time_ms: float = 0.0      # 【平均等待】平均等待时间（毫秒）
    avg_process_time_ms: float = 0.0   # 【平均处理】平均处理时间（毫秒）
    throughput_per_sec: float = 0.0    # 【吞吐量】每秒处理任务数
    error_rate: float = 0.0            # 【错误率】错误任务比例
    timestamp: datetime = field(default_factory=datetime.now)  # 【时间戳】


@dataclass
class CongestionAlert:
    """【拥塞告警】队列拥塞告警信息"""
    alert_id: str                      # 【告警ID】唯一标识
    queue_name: str                    # 【队列名称】
    severity: str                      # 【严重级别】warning/critical
    message: str                       # 【告警消息】
    metrics: QueueMetrics              # 【指标快照】
    timestamp: datetime                # 【时间戳】
    acknowledged: bool = False         # 【已确认】是否已确认


class QueueMonitor:
    """
    【类职责】
    队列监控器，监控任务队列状态并提供拥塞告警
    
    【主要功能】
    1. 队列注册管理: 注册和管理多个队列
    2. 实时指标采集: 采集队列性能指标
    3. 拥塞检测: 检测队列拥塞并触发告警
    4. 历史趋势分析: 分析队列性能趋势
    
    【属性说明】
    - _queues: 注册的队列字典
    - _metrics_history: 指标历史记录
    - _alert_handlers: 告警处理器列表
    - _congestion_thresholds: 拥塞阈值配置
    
    【使用示例】
    ```python
    monitor = QueueMonitor()
    
    # 注册队列
    monitor.register_queue("email_queue", email_queue)
    
    # 设置告警处理器
    monitor.add_alert_handler(lambda alert: print(f"告警: {alert.message}"))
    
    # 启动监控
    await monitor.start_monitoring(interval=5)
    ```
    """
    
    def __init__(self):
        """【初始化】创建队列监控器实例"""
        self._queues: Dict[str, Any] = {}
        self._queue_getters: Dict[str, Callable] = {}
        self._metrics_history: Dict[str, deque] = {}
        self._alert_handlers: List[Callable[[CongestionAlert], None]] = []
        self._congestion_thresholds = {
            "queue_depth": 1000,           # 【队列深度阈值】
            "wait_time_ms": 60000,         # 【等待时间阈值】60秒
            "error_rate": 0.05,            # 【错误率阈值】5%
            "throughput_drop": 0.5,        # 【吞吐量下降阈值】50%
        }
        self._logger = logging.getLogger(__name__)
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def register_queue(
        self,
        queue_name: str,
        queue_instance: Any,
        metrics_getter: Optional[Callable[[], QueueMetrics]] = None
    ) -> None:
        """
        【注册队列】注册要监控的队列
        
        【参数说明】
        - queue_name (str): 队列名称
        - queue_instance (Any): 队列实例
        - metrics_getter (Callable, 可选): 自定义指标获取函数
        
        【使用示例】
        ```python
        monitor.register_queue(
            "script_queue",
            script_queue,
            lambda: QueueMetrics(
                queue_name="script_queue",
                pending_count=len(script_queue.pending),
                processing_count=len(script_queue.processing)
            )
        )
        ```
        """
        self._queues[queue_name] = queue_instance
        
        if metrics_getter:
            self._queue_getters[queue_name] = metrics_getter
        
        # 【初始化历史记录】
        self._metrics_history[queue_name] = deque(maxlen=1000)
        
        self._logger.info(f"【队列注册】{queue_name}")
    
    def unregister_queue(self, queue_name: str) -> bool:
        """
        【注销队列】注销队列监控
        
        【参数说明】
        - queue_name (str): 队列名称
        
        【返回值】
        - bool: 是否成功注销
        
        【使用示例】
        ```python
        success = monitor.unregister_queue("old_queue")
        ```
        """
        if queue_name in self._queues:
            del self._queues[queue_name]
            self._queue_getters.pop(queue_name, None)
            self._metrics_history.pop(queue_name, None)
            self._logger.info(f"【队列注销】{queue_name}")
            return True
        return False
    
    async def get_queue_stats(self, queue_name: Optional[str] = None) -> Union[QueueMetrics, Dict[str, QueueMetrics]]:
        """
        【获取队列统计】获取队列统计信息
        
        【参数说明】
        - queue_name (str, 可选): 队列名称，为None则返回所有队列
        
        【返回值】
        - QueueMetrics 或 Dict[str, QueueMetrics]: 队列统计信息
        
        【使用示例】
        ```python
        # 获取单个队列
        stats = await monitor.get_queue_stats("script_queue")
        
        # 获取所有队列
        all_stats = await monitor.get_queue_stats()
        ```
        """
        if queue_name:
            return await self._get_single_queue_stats(queue_name)
        
        # 【获取所有队列统计】
        all_stats = {}
        for name in self._queues.keys():
            all_stats[name] = await self._get_single_queue_stats(name)
        
        return all_stats
    
    async def _get_single_queue_stats(self, queue_name: str) -> QueueMetrics:
        """【获取单个队列统计】内部方法"""
        # 【使用自定义获取器】
        if queue_name in self._queue_getters:
            return self._queue_getters[queue_name]()
        
        # 【默认实现】
        queue = self._queues.get(queue_name)
        
        if not queue:
            return QueueMetrics(
                queue_name=queue_name,
                timestamp=datetime.now()
            )
        
        # 【尝试从队列获取指标】
        try:
            if hasattr(queue, 'qsize'):
                pending = queue.qsize()
            elif hasattr(queue, 'pending_count'):
                pending = queue.pending_count
            else:
                pending = 0
            
            if hasattr(queue, 'processing_count'):
                processing = queue.processing_count
            else:
                processing = 0
            
            if hasattr(queue, 'completed_count'):
                completed = queue.completed_count
            else:
                completed = 0
            
            if hasattr(queue, 'failed_count'):
                failed = queue.failed_count
            else:
                failed = 0
            
            metrics = QueueMetrics(
                queue_name=queue_name,
                pending_count=pending,
                processing_count=processing,
                completed_count=completed,
                failed_count=failed,
                timestamp=datetime.now()
            )
            
            # 【计算错误率】
            total = completed + failed
            if total > 0:
                metrics.error_rate = failed / total
            
            return metrics
            
        except Exception as e:
            self._logger.error(f"【获取队列统计失败】{queue_name}: {e}")
            return QueueMetrics(
                queue_name=queue_name,
                timestamp=datetime.now()
            )
    
    async def check_congestion(self, queue_name: str) -> Optional[CongestionAlert]:
        """
        【检查拥塞】检查队列是否拥塞
        
        【参数说明】
        - queue_name (str): 队列名称
        
        【返回值】
        - Optional[CongestionAlert]: 拥塞告警，如果没有拥塞返回None
        
        【使用示例】
        ```python
        alert = await monitor.check_congestion("script_queue")
        if alert:
            print(f"队列拥塞: {alert.message}")
        ```
        """
        metrics = await self._get_single_queue_stats(queue_name)
        
        # 【保存历史】
        self._metrics_history[queue_name].append(metrics)
        
        # 【检查拥塞条件】
        alerts = []
        
        # 【检查队列深度】
        if metrics.pending_count > self._congestion_thresholds["queue_depth"]:
            alerts.append(f"队列深度过高: {metrics.pending_count}")
        
        # 【检查等待时间】
        if metrics.avg_wait_time_ms > self._congestion_thresholds["wait_time_ms"]:
            alerts.append(f"平均等待时间过长: {metrics.avg_wait_time_ms}ms")
        
        # 【检查错误率】
        if metrics.error_rate > self._congestion_thresholds["error_rate"]:
            alerts.append(f"错误率过高: {metrics.error_rate:.2%}")
        
        # 【检查吞吐量下降】
        if len(self._metrics_history[queue_name]) >= 2:
            prev_metrics = list(self._metrics_history[queue_name])[-2]
            if prev_metrics.throughput_per_sec > 0:
                throughput_drop = 1 - (metrics.throughput_per_sec / prev_metrics.throughput_per_sec)
                if throughput_drop > self._congestion_thresholds["throughput_drop"]:
                    alerts.append(f"吞吐量下降: {throughput_drop:.2%}")
        
        # 【生成告警】
        if alerts:
            severity = "critical" if len(alerts) >= 2 else "warning"
            alert = CongestionAlert(
                alert_id=f"{queue_name}-{int(time.time())}",
                queue_name=queue_name,
                severity=severity,
                message="; ".join(alerts),
                metrics=metrics,
                timestamp=datetime.now()
            )
            
            # 【触发告警处理器】
            await self._trigger_alert_handlers(alert)
            
            return alert
        
        return None
    
    async def check_all_congestion(self) -> List[CongestionAlert]:
        """
        【检查所有队列拥塞】检查所有注册队列的拥塞状态
        
        【返回值】
        - List[CongestionAlert]: 拥塞告警列表
        
        【使用示例】
        ```python
        alerts = await monitor.check_all_congestion()
        for alert in alerts:
            print(f"{alert.queue_name}: {alert.message}")
        ```
        """
        alerts = []
        
        for queue_name in self._queues.keys():
            alert = await self.check_congestion(queue_name)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def add_alert_handler(self, handler: Callable[[CongestionAlert], None]) -> None:
        """
        【添加告警处理器】添加拥塞告警处理器
        
        【参数说明】
        - handler (Callable): 告警处理函数，接收CongestionAlert参数
        
        【使用示例】
        ```python
        def on_alert(alert: CongestionAlert):
            send_email(f"队列告警: {alert.queue_name}", alert.message)
        
        monitor.add_alert_handler(on_alert)
        ```
        """
        self._alert_handlers.append(handler)
        self._logger.info("【告警处理器添加】")
    
    def remove_alert_handler(self, handler: Callable[[CongestionAlert], None]) -> bool:
        """
        【移除告警处理器】移除告警处理器
        
        【参数说明】
        - handler (Callable): 要移除的处理函数
        
        【返回值】
        - bool: 是否成功移除
        """
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)
            return True
        return False
    
    async def _trigger_alert_handlers(self, alert: CongestionAlert) -> None:
        """【触发告警处理器】内部方法"""
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                self._logger.error(f"【告警处理器执行失败】: {e}")
    
    async def start_monitoring(self, interval: int = 5) -> None:
        """
        【启动监控】启动队列监控循环
        
        【参数说明】
        - interval (int): 监控间隔（秒），默认5秒
        
        【使用示例】
        ```python
        await monitor.start_monitoring(interval=10)
        ```
        """
        if self._monitoring:
            self._logger.warning("【监控已在运行】")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        self._logger.info(f"【监控启动】间隔: {interval}秒")
    
    async def stop_monitoring(self) -> None:
        """
        【停止监控】停止队列监控循环
        
        【使用示例】
        ```python
        await monitor.stop_monitoring()
        ```
        """
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self._logger.info("【监控停止】")
    
    async def _monitor_loop(self, interval: int) -> None:
        """【监控循环】内部监控循环"""
        while self._monitoring:
            try:
                # 【检查所有队列拥塞】
                await self.check_all_congestion()
                
                # 【等待下一次检查】
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"【监控循环错误】: {e}")
                await asyncio.sleep(interval)
    
    def get_queue_status(self, queue_name: str) -> QueueStatus:
        """
        【获取队列状态】获取队列整体健康状态
        
        【参数说明】
        - queue_name (str): 队列名称
        
        【返回值】
        - QueueStatus: 队列状态
        
        【使用示例】
        ```python
        status = monitor.get_queue_status("script_queue")
        if status == QueueStatus.CRITICAL:
            print("队列严重拥塞！")
        ```
        """
        if queue_name not in self._queues:
            return QueueStatus.UNKNOWN
        
        history = self._metrics_history.get(queue_name, deque())
        
        if not history:
            return QueueStatus.UNKNOWN
        
        latest = history[-1]
        
        # 【判断状态】
        if (latest.pending_count > self._congestion_thresholds["queue_depth"] * 2 or
            latest.error_rate > self._congestion_thresholds["error_rate"] * 2):
            return QueueStatus.CRITICAL
        
        if (latest.pending_count > self._congestion_thresholds["queue_depth"] or
            latest.error_rate > self._congestion_thresholds["error_rate"]):
            return QueueStatus.WARNING
        
        return QueueStatus.HEALTHY
    
    def get_historical_trends(self, queue_name: str, 
                             duration_minutes: int = 60) -> Dict[str, Any]:
        """
        【获取历史趋势】获取队列历史趋势数据
        
        【参数说明】
        - queue_name (str): 队列名称
        - duration_minutes (int): 时间范围（分钟），默认60分钟
        
        【返回值】
        - Dict[str, Any]: 趋势数据
        
        【使用示例】
        ```python
        trends = monitor.get_historical_trends("script_queue", duration_minutes=30)
        print(f"平均队列深度: {trends['avg_pending']}")
        ```
        """
        history = self._metrics_history.get(queue_name, deque())
        
        if not history:
            return {}
        
        # 【过滤时间范围】
        cutoff = datetime.now() - timedelta(minutes=duration_minutes)
        recent = [m for m in history if m.timestamp > cutoff]
        
        if not recent:
            return {}
        
        # 【计算趋势】
        pending_values = [m.pending_count for m in recent]
        wait_times = [m.avg_wait_time_ms for m in recent if m.avg_wait_time_ms > 0]
        error_rates = [m.error_rate for m in recent]
        
        return {
            "queue_name": queue_name,
            "duration_minutes": duration_minutes,
            "data_points": len(recent),
            "avg_pending": sum(pending_values) / len(pending_values),
            "max_pending": max(pending_values),
            "min_pending": min(pending_values),
            "avg_wait_time_ms": sum(wait_times) / len(wait_times) if wait_times else 0,
            "avg_error_rate": sum(error_rates) / len(error_rates) if error_rates else 0,
            "latest_status": self.get_queue_status(queue_name).value,
        }
    
    def set_congestion_thresholds(self, thresholds: Dict[str, Union[int, float]]) -> None:
        """
        【设置拥塞阈值】设置拥塞检测阈值
        
        【参数说明】
        - thresholds (Dict): 阈值配置
        
        【使用示例】
        ```python
        monitor.set_congestion_thresholds({
            "queue_depth": 500,        # 队列深度阈值
            "wait_time_ms": 30000,     # 等待时间阈值30秒
            "error_rate": 0.02,        # 错误率阈值2%
        })
        ```
        """
        self._congestion_thresholds.update(thresholds)
        self._logger.info(f"【阈值更新】{thresholds}")


# 【全局监控器实例】
queue_monitor = QueueMonitor()


# 【便捷函数】
async def get_queue_stats(queue_name: Optional[str] = None) -> Union[QueueMetrics, Dict[str, QueueMetrics]]:
    """【便捷函数】获取队列统计"""
    return await queue_monitor.get_queue_stats(queue_name)


async def check_congestion(queue_name: str) -> Optional[CongestionAlert]:
    """【便捷函数】检查队列拥塞"""
    return await queue_monitor.check_congestion(queue_name)


def register_queue(queue_name: str, queue_instance: Any, 
                   metrics_getter: Optional[Callable[[], QueueMetrics]] = None) -> None:
    """【便捷函数】注册队列"""
    queue_monitor.register_queue(queue_name, queue_instance, metrics_getter)


def get_queue_status(queue_name: str) -> QueueStatus:
    """【便捷函数】获取队列状态"""
    return queue_monitor.get_queue_status(queue_name)
