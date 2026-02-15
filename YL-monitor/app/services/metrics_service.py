"""
系统指标监控服务

功能:
- 采集系统 CPU、内存、磁盘、网络指标
- 指标数据存储和历史查询
- 实时指标推送

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import time
import logging

from app.services.event_bus import EventBus, EventType

logger = logging.getLogger(__name__)


class MetricsService:
    """系统指标服务"""

    def __init__(self, storage_dir: Optional[Path] = None, collection_interval: int = 5):
        self.storage_dir = storage_dir or Path("data/metrics")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.collection_interval = collection_interval  # 采集间隔（秒）
        self.max_history_days = 7  # 保留历史天数

        self.metrics_file = self.storage_dir / "metrics.json"
        self._metrics_history: List[Dict[str, Any]] = []
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False

        # 加载历史数据
        self._load_history()

    def start_collection(self):
        """启动指标采集"""
        if self._running:
            return

        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("系统指标采集已启动")

    def stop_collection(self):
        """停止指标采集"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
        logger.info("系统指标采集已停止")

    async def _collection_loop(self):
        """指标采集循环"""
        while self._running:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                self._publish_metrics(metrics)

                # 清理过期数据
                self._cleanup_old_data()

            except Exception as e:
                logger.error(f"指标采集失败: {e}")

            await asyncio.sleep(self.collection_interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """采集系统指标"""
        timestamp = datetime.utcnow()

        # CPU 信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 内存信息
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024**3)  # GB
        memory_total = memory.total / (1024**3)  # GB

        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = disk.used / (1024**3)  # GB
        disk_total = disk.total / (1024**3)  # GB

        # 网络信息
        network = psutil.net_io_counters()
        network_sent = network.bytes_sent / (1024**2)  # MB
        network_recv = network.bytes_recv / (1024**2)  # MB

        # 系统负载
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)

        # 进程信息
        process_count = len(psutil.pids())

        return {
            "timestamp": timestamp.isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "freq_current": cpu_freq.current if cpu_freq else 0,
                "freq_max": cpu_freq.max if cpu_freq else 0
            },
            "memory": {
                "percent": memory_percent,
                "used_gb": round(memory_used, 2),
                "total_gb": round(memory_total, 2),
                "available_gb": round(memory.available / (1024**3), 2)
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": round(disk_used, 2),
                "total_gb": round(disk_total, 2),
                "free_gb": round(disk.free / (1024**3), 2)
            },
            "network": {
                "sent_mb": round(network_sent, 2),
                "recv_mb": round(network_recv, 2),
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "system": {
                "load_1m": load_avg[0],
                "load_5m": load_avg[1],
                "load_15m": load_avg[2],
                "process_count": process_count,
                "uptime": time.time() - psutil.boot_time()
            }
        }

    def _store_metrics(self, metrics: Dict[str, Any]):
        """存储指标数据"""
        self._metrics_history.append(metrics)

        # 限制内存中的历史数量（最近 1 小时）
        max_memory_items = int(3600 / self.collection_interval)  # 1小时的数据
        if len(self._metrics_history) > max_memory_items:
            self._metrics_history = self._metrics_history[-max_memory_items:]

        # 每 10 次保存一次到文件
        if len(self._metrics_history) % 10 == 0:
            self._save_history()

    def _publish_metrics(self, metrics: Dict[str, Any]):
        """发布指标事件"""
        event_bus = EventBus()

        # 发布各个指标的事件
        event_bus.publish(EventType.METRIC_CPU, {
            "value": metrics["cpu"]["percent"],
            "timestamp": metrics["timestamp"]
        })

        event_bus.publish(EventType.METRIC_MEMORY, {
            "value": metrics["memory"]["percent"],
            "timestamp": metrics["timestamp"]
        })

        event_bus.publish(EventType.METRIC_DISK, {
            "value": metrics["disk"]["percent"],
            "timestamp": metrics["timestamp"]
        })

        event_bus.publish(EventType.METRIC_NETWORK, {
            "value": metrics["network"]["sent_mb"] + metrics["network"]["recv_mb"],
            "timestamp": metrics["timestamp"]
        })

    def _load_history(self):
        """加载历史数据"""
        if not self.metrics_file.exists():
            return

        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._metrics_history = data.get("history", [])
                logger.info(f"加载了 {len(self._metrics_history)} 条历史指标数据")
        except Exception as e:
            logger.error(f"加载历史指标数据失败: {e}")
            self._metrics_history = []

    def _save_history(self):
        """保存历史数据到文件"""
        try:
            data = {
                "last_updated": datetime.utcnow().isoformat(),
                "collection_interval": self.collection_interval,
                "history": self._metrics_history[-1000:]  # 只保存最近 1000 条
            }

            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存历史指标数据失败: {e}")

    def _cleanup_old_data(self):
        """清理过期数据"""
        if not self._metrics_history:
            return

        cutoff_time = datetime.utcnow() - timedelta(days=self.max_history_days)

        # 清理内存数据
        original_count = len(self._metrics_history)
        self._metrics_history = [
            m for m in self._metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]

        if len(self._metrics_history) < original_count:
            logger.info(f"清理了 {original_count - len(self._metrics_history)} 条过期指标数据")

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前最新指标"""
        if not self._metrics_history:
            return self._collect_metrics()

        return self._metrics_history[-1]

    def get_metrics_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取指标历史"""
        if not self._metrics_history:
            return []

        # 过滤时间范围
        history = self._metrics_history
        if start_time:
            history = [m for m in history if datetime.fromisoformat(m["timestamp"]) >= start_time]
        if end_time:
            history = [m for m in history if datetime.fromisoformat(m["timestamp"]) <= end_time]

        # 返回最新的 limit 条
        return history[-limit:]

    def get_metrics_summary(
        self,
        hours: int = 1
    ) -> Dict[str, Any]:
        """获取指标汇总统计"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        history = self.get_metrics_history(start_time=start_time)

        if not history:
            return {}

        # 计算各项指标的统计
        cpu_values = [m["cpu"]["percent"] for m in history]
        memory_values = [m["memory"]["percent"] for m in history]
        disk_values = [m["disk"]["percent"] for m in history]

        def calc_stats(values):
            if not values:
                return {"min": 0, "max": 0, "avg": 0, "current": 0}
            return {
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "avg": round(sum(values) / len(values), 2),
                "current": round(values[-1], 2)
            }

        return {
            "period_hours": hours,
            "data_points": len(history),
            "cpu": calc_stats(cpu_values),
            "memory": calc_stats(memory_values),
            "disk": calc_stats(disk_values),
            "timestamp": datetime.utcnow().isoformat()
        }


# 全局实例
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """获取指标服务实例"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
