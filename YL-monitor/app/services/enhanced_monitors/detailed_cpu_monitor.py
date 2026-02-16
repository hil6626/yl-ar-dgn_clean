#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细CPU监控器 - 增强版
提供每核CPU详细监控，5秒采集频率
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
class CPUDetailedMetrics:
    """CPU详细指标"""
    overall_percent: float
    per_cpu_percent: List[float]
    cpu_count_logical: int
    cpu_count_physical: int
    cpu_freq_current: float
    cpu_freq_min: float
    cpu_freq_max: float
    ctx_switches: int
    interrupts: int
    soft_interrupts: int
    syscalls: int
    load_avg_1m: float
    load_avg_5m: float
    load_avg_15m: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DetailedCPUMonitor:
    """
    详细CPU监控器
    监控每核CPU使用率和系统负载
    """
    
    def __init__(self):
        self.metrics_history: List[CPUDetailedMetrics] = []
        self.max_history = 1000
        self.running = False
        self._last_cpu_times = None
        
    def collect_metrics(self) -> CPUDetailedMetrics:
        """采集详细CPU指标"""
        try:
            # 整体CPU使用率（需要间隔采样）
            overall_percent = psutil.cpu_percent(interval=0.1)
            
            # 每核CPU使用率
            per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # CPU数量
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            
            # CPU频率
            freq = psutil.cpu_freq()
            cpu_freq_current = freq.current if freq else 0
            cpu_freq_min = freq.min if freq else 0
            cpu_freq_max = freq.max if freq else 0
            
            # 系统统计
            ctx_switches = psutil.cpu_stats().ctx_switches
            interrupts = psutil.cpu_stats().interrupts
            soft_interrupts = psutil.cpu_stats().soft_interrupts
            syscalls = psutil.cpu_stats().syscalls
            
            # 负载均衡（Unix-like系统）
            try:
                load_avg_1m, load_avg_5m, load_avg_15m = psutil.getloadavg()
            except AttributeError:
                load_avg_1m = load_avg_5m = load_avg_15m = 0.0
            
            metrics = CPUDetailedMetrics(
                overall_percent=overall_percent,
                per_cpu_percent=per_cpu_percent,
                cpu_count_logical=cpu_count_logical,
                cpu_count_physical=cpu_count_physical,
                cpu_freq_current=cpu_freq_current,
                cpu_freq_min=cpu_freq_min,
                cpu_freq_max=cpu_freq_max,
                ctx_switches=ctx_switches,
                interrupts=interrupts,
                soft_interrupts=soft_interrupts,
                syscalls=syscalls,
                load_avg_1m=load_avg_1m,
                load_avg_5m=load_avg_5m,
                load_avg_15m=load_avg_15m,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # 保存历史
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"采集CPU指标失败: {e}")
            return None
    
    async def start_monitoring(self, interval: int = 5):
        """启动持续监控"""
        self.running = True
        logger.info(f"启动详细CPU监控 (间隔: {interval}秒)")
        
        while self.running:
            try:
                metrics = self.collect_metrics()
                if metrics:
                    logger.debug(f"CPU整体: {metrics.overall_percent:.1f}%, "
                               f"负载: {metrics.load_avg_1m:.2f}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"CPU监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("停止详细CPU监控")
    
    def get_latest_metrics(self) -> Optional[CPUDetailedMetrics]:
        """获取最新指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, count: int = 100) -> List[CPUDetailedMetrics]:
        """获取历史指标"""
        return self.metrics_history[-count:]
    
    def get_cpu_pressure(self) -> Dict:
        """获取CPU压力评估"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "无数据"}
        
        recent = self.metrics_history[-10:]  # 最近10个样本
        avg_usage = sum(m.overall_percent for m in recent) / len(recent)
        avg_load = sum(m.load_avg_1m for m in recent) / len(recent)
        
        # 压力评估
        if avg_usage > 90 or avg_load > cpu_count_logical * 2:
            status = "critical"
            suggestion = "CPU严重过载，需要立即扩容或优化"
        elif avg_usage > 80 or avg_load > cpu_count_logical:
            status = "warning"
            suggestion = "CPU负载较高，建议监控并准备扩容"
        elif avg_usage > 60:
            status = "elevated"
            suggestion = "CPU负载中等，正常范围内"
        else:
            status = "normal"
            suggestion = "CPU负载正常"
        
        return {
            "status": status,
            "average_usage": round(avg_usage, 2),
            "average_load": round(avg_load, 2),
            "cpu_count": cpu_count_logical,
            "suggestion": suggestion,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        monitor = DetailedCPUMonitor()
        
        # 启动监控
        task = asyncio.create_task(monitor.start_monitoring(interval=5))
        
        # 运行30秒
        await asyncio.sleep(30)
        
        # 获取统计
        metrics = monitor.get_latest_metrics()
        if metrics:
            print(f"\nCPU详细指标:")
            print(f"  整体使用率: {metrics.overall_percent:.1f}%")
            print(f"  每核使用率: {metrics.per_cpu_percent}")
            print(f"  逻辑核心数: {metrics.cpu_count_logical}")
            print(f"  物理核心数: {metrics.cpu_count_physical}")
            print(f"  当前频率: {metrics.cpu_freq_current:.0f} MHz")
            print(f"  1分钟负载: {metrics.load_avg_1m:.2f}")
            print(f"  上下文切换: {metrics.ctx_switches}")
        
        # 压力评估
        pressure = monitor.get_cpu_pressure()
        print(f"\nCPU压力评估:")
        print(f"  状态: {pressure['status']}")
        print(f"  建议: {pressure['suggestion']}")
        
        # 停止监控
        monitor.stop_monitoring()
        task.cancel()
    
    asyncio.run(test())
