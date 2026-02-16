#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细内存监控器 - 增强版
提供分段内存详细监控，5秒采集频率
"""

import psutil
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryDetailedMetrics:
    """内存详细指标"""
    total: int  # bytes
    available: int  # bytes
    used: int  # bytes
    free: int  # bytes
    percent: float
    active: int  # bytes
    inactive: int  # bytes
    buffers: int  # bytes
    cached: int  # bytes
    shared: int  # bytes
    swap_total: int  # bytes
    swap_used: int  # bytes
    swap_free: int  # bytes
    swap_percent: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TopMemoryProcess:
    """内存占用最高的进程"""
    pid: int
    name: str
    memory_rss: int  # bytes
    memory_vms: int  # bytes
    memory_percent: float
    cpu_percent: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DetailedMemoryMonitor:
    """
    详细内存监控器
    监控内存分段使用和Top进程
    """
    
    def __init__(self):
        self.metrics_history: List[MemoryDetailedMetrics] = []
        self.max_history = 1000
        self.running = False
        
    def collect_metrics(self) -> Optional[MemoryDetailedMetrics]:
        """采集详细内存指标"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics = MemoryDetailedMetrics(
                total=mem.total,
                available=mem.available,
                used=mem.used,
                free=mem.free,
                percent=mem.percent,
                active=getattr(mem, 'active', 0),
                inactive=getattr(mem, 'inactive', 0),
                buffers=getattr(mem, 'buffers', 0),
                cached=getattr(mem, 'cached', 0),
                shared=getattr(mem, 'shared', 0),
                swap_total=swap.total,
                swap_used=swap.used,
                swap_free=swap.free,
                swap_percent=swap.percent,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # 保存历史
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"采集内存指标失败: {e}")
            return None
    
    def get_top_memory_processes(self, n: int = 5) -> List[TopMemoryProcess]:
        """获取内存占用最高的N个进程"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 
                                              'memory_percent', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    processes.append(TopMemoryProcess(
                        pid=pinfo['pid'],
                        name=pinfo['name'] or 'Unknown',
                        memory_rss=pinfo['memory_info'].rss,
                        memory_vms=pinfo['memory_info'].vms,
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        cpu_percent=pinfo['cpu_percent'] or 0.0
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按内存使用率排序
            processes.sort(key=lambda x: x.memory_percent, reverse=True)
            return processes[:n]
            
        except Exception as e:
            logger.error(f"获取Top内存进程失败: {e}")
            return []
    
    async def start_monitoring(self, interval: int = 5):
        """启动持续监控"""
        self.running = True
        logger.info(f"启动详细内存监控 (间隔: {interval}秒)")
        
        while self.running:
            try:
                metrics = self.collect_metrics()
                if metrics:
                    logger.debug(f"内存使用: {metrics.percent:.1f}%, "
                               f"可用: {metrics.available / 1024 / 1024 / 1024:.1f}GB")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"内存监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("停止详细内存监控")
    
    def get_latest_metrics(self) -> Optional[MemoryDetailedMetrics]:
        """获取最新指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, count: int = 100) -> List[MemoryDetailedMetrics]:
        """获取历史指标"""
        return self.metrics_history[-count:]
    
    def get_memory_pressure(self) -> Dict:
        """获取内存压力评估"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "无数据"}
        
        recent = self.metrics_history[-10:]  # 最近10个样本
        avg_percent = sum(m.percent for m in recent) / len(recent)
        avg_swap = sum(m.swap_percent for m in recent) / len(recent)
        
        # 压力评估
        if avg_percent > 95 or avg_swap > 50:
            status = "critical"
            suggestion = "内存严重不足，需要立即扩容或释放内存"
        elif avg_percent > 85 or avg_swap > 30:
            status = "warning"
            suggestion = "内存使用较高，建议监控并准备扩容"
        elif avg_percent > 70:
            status = "elevated"
            suggestion = "内存使用中等，正常范围内"
        else:
            status = "normal"
            suggestion = "内存使用正常"
        
        latest = self.get_latest_metrics()
        available_gb = latest.available / 1024 / 1024 / 1024 if latest else 0
        
        return {
            "status": status,
            "memory_percent": round(avg_percent, 2),
            "swap_percent": round(avg_swap, 2),
            "available_gb": round(available_gb, 2),
            "suggestion": suggestion,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        monitor = DetailedMemoryMonitor()
        
        # 启动监控
        task = asyncio.create_task(monitor.start_monitoring(interval=5))
        
        # 运行30秒
        await asyncio.sleep(30)
        
        # 获取统计
        metrics = monitor.get_latest_metrics()
        if metrics:
            print(f"\n内存详细指标:")
            print(f"  总内存: {metrics.total / 1024 / 1024 / 1024:.1f} GB")
            print(f"  已使用: {metrics.used / 1024 / 1024 / 1024:.1f} GB "
                  f"({metrics.percent:.1f}%)")
            print(f"  可用: {metrics.available / 1024 / 1024 / 1024:.1f} GB")
            print(f"  活跃: {metrics.active / 1024 / 1024 / 1024:.1f} GB")
            print(f"  缓存: {metrics.cached / 1024 / 1024 / 1024:.1f} GB")
            print(f"  交换区: {metrics.swap_percent:.1f}%")
        
        # Top内存进程
        top_procs = monitor.get_top_memory_processes(5)
        print(f"\nTop 5 内存进程:")
        for proc in top_procs:
            print(f"  {proc.name} (PID: {proc.pid}): "
                  f"{proc.memory_percent:.1f}%, "
                  f"{proc.memory_rss / 1024 / 1024:.1f} MB")
        
        # 压力评估
        pressure = monitor.get_memory_pressure()
        print(f"\n内存压力评估:")
        print(f"  状态: {pressure['status']}")
        print(f"  建议: {pressure['suggestion']}")
        
        # 停止监控
        monitor.stop_monitoring()
        task.cancel()
    
    asyncio.run(test())
