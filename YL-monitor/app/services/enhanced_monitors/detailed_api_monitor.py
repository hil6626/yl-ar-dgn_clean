#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细API监控器 - 增强版
提供API响应时间详细监控（P50/P95/P99），5秒采集频率
"""

import time
import asyncio
import statistics
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from collections import deque
import logging
import requests

logger = logging.getLogger(__name__)


@dataclass
class APIMetrics:
    """API指标"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class APIEndpointStats:
    """API端点统计"""
    endpoint: str
    method: str
    total_requests: int
    success_count: int
    error_count: int
    error_rate: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    qps: float
    last_updated: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DetailedAPIMonitor:
    """
    详细API监控器
    监控API响应时间和错误率
    """
    
    def __init__(self, base_url: str = "http://localhost:5500"):
        self.base_url = base_url
        self.metrics_history: deque = deque(maxlen=10000)  # 保留最近10000条
        self.endpoint_stats: Dict[str, APIEndpointStats] = {}
        self.running = False
        self.endpoints_to_monitor = [
            {"path": "/api/health", "method": "GET"},
            {"path": "/api/v1/monitor/ui/status", "method": "GET"},
            {"path": "/api/v1/monitor/ar/status", "method": "GET"},
            {"path": "/api/v1/monitor/infrastructure", "method": "GET"},
            {"path": "/api/v1/monitor/system-resources", "method": "GET"},
        ]
        
    def measure_endpoint(self, endpoint: str, method: str = "GET") -> Optional[APIMetrics]:
        """测量单个端点"""
        try:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            
            response = requests.request(method, url, timeout=10)
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            metrics = APIMetrics(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # 保存到历史
            self.metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"测量端点失败 {endpoint}: {e}")
            # 记录失败
            metrics = APIMetrics(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time_ms=0,
                timestamp=datetime.utcnow().isoformat()
            )
            self.metrics_history.append(metrics)
            return metrics
    
    def collect_all_metrics(self) -> List[APIMetrics]:
        """采集所有端点指标"""
        metrics_list = []
        for endpoint_config in self.endpoints_to_monitor:
            metrics = self.measure_endpoint(
                endpoint_config["path"],
                endpoint_config["method"]
            )
            if metrics:
                metrics_list.append(metrics)
        return metrics_list
    
    def calculate_endpoint_stats(self, endpoint: str, method: str = "GET", 
                                  window_seconds: int = 60) -> Optional[APIEndpointStats]:
        """计算端点统计信息"""
        # 筛选时间窗口内的指标
        cutoff_time = time.time() - window_seconds
        recent_metrics = [
            m for m in self.metrics_history
            if m.endpoint == endpoint 
            and m.method == method
            and datetime.fromisoformat(m.timestamp).timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        # 计算统计
        response_times = [m.response_time_ms for m in recent_metrics if m.status_code > 0]
        if not response_times:
            return None
        
        total = len(recent_metrics)
        success = sum(1 for m in recent_metrics if 200 <= m.status_code < 300)
        errors = total - success
        
        # 计算百分位数
        sorted_times = sorted(response_times)
        p50 = statistics.median(sorted_times)
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
        
        stats = APIEndpointStats(
            endpoint=endpoint,
            method=method,
            total_requests=total,
            success_count=success,
            error_count=errors,
            error_rate=round(errors / total * 100, 2) if total > 0 else 0,
            p50_ms=round(p50, 2),
            p95_ms=round(p95, 2),
            p99_ms=round(p99, 2),
            min_ms=round(min(response_times), 2),
            max_ms=round(max(response_times), 2),
            avg_ms=round(statistics.mean(response_times), 2),
            qps=round(total / window_seconds, 2),
            last_updated=datetime.utcnow().isoformat()
        )
        
        # 保存统计
        key = f"{method}:{endpoint}"
        self.endpoint_stats[key] = stats
        
        return stats
    
    def calculate_all_stats(self, window_seconds: int = 60) -> Dict[str, APIEndpointStats]:
        """计算所有端点统计"""
        stats = {}
        for endpoint_config in self.endpoints_to_monitor:
            endpoint_stats = self.calculate_endpoint_stats(
                endpoint_config["path"],
                endpoint_config["method"],
                window_seconds
            )
            if endpoint_stats:
                key = f"{endpoint_config['method']}:{endpoint_config['path']}"
                stats[key] = endpoint_stats
        return stats
    
    async def start_monitoring(self, interval: int = 5):
        """启动持续监控"""
        self.running = True
        logger.info(f"启动详细API监控 (间隔: {interval}秒)")
        
        while self.running:
            try:
                # 采集所有端点
                self.collect_all_metrics()
                
                # 计算统计（每60秒计算一次）
                if len(self.metrics_history) % 12 == 0:  # 每60秒
                    self.calculate_all_stats(60)
                    logger.debug("API统计已更新")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"API监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("停止详细API监控")
    
    def get_endpoint_stats(self, endpoint: str, method: str = "GET") -> Optional[APIEndpointStats]:
        """获取端点统计"""
        key = f"{method}:{endpoint}"
        return self.endpoint_stats.get(key)
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有端点统计"""
        return {k: v.to_dict() for k, v in self.endpoint_stats.items()}
    
    def get_slow_endpoints(self, threshold_ms: float = 1000) -> List[Dict]:
        """获取慢端点"""
        slow = []
        for key, stats in self.endpoint_stats.items():
            if stats.p95_ms > threshold_ms:
                slow.append({
                    "endpoint": stats.endpoint,
                    "method": stats.method,
                    "p95_ms": stats.p95_ms,
                    "p99_ms": stats.p99_ms,
                    "error_rate": stats.error_rate
                })
        return sorted(slow, key=lambda x: x["p95_ms"], reverse=True)
    
    def get_api_health(self) -> Dict:
        """获取API健康状态"""
        if not self.endpoint_stats:
            return {"status": "unknown", "message": "无数据"}
        
        total_requests = sum(s.total_requests for s in self.endpoint_stats.values())
        total_errors = sum(s.error_count for s in self.endpoint_stats.values())
        avg_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # 评估状态
        if avg_error_rate > 10:
            status = "critical"
        elif avg_error_rate > 5:
            status = "warning"
        elif avg_error_rate > 1:
            status = "elevated"
        else:
            status = "healthy"
        
        # 慢端点
        slow_endpoints = self.get_slow_endpoints(500)
        
        return {
            "status": status,
            "total_endpoints": len(self.endpoint_stats),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(avg_error_rate, 2),
            "slow_endpoints_count": len(slow_endpoints),
            "slow_endpoints": slow_endpoints[:5],  # Top 5
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        monitor = DetailedAPIMonitor()
        
        # 启动监控
        task = asyncio.create_task(monitor.start_monitoring(interval=5))
        
        # 运行60秒
        await asyncio.sleep(60)
        
        # 获取统计
        stats = monitor.get_all_stats()
        print(f"\nAPI端点统计 ({len(stats)}个端点):")
        for key, s in stats.items():
            print(f"\n  {key}:")
            print(f"    总请求: {s['total_requests']}")
            print(f"    错误率: {s['error_rate']}%")
            print(f"    P50: {s['p50_ms']}ms")
            print(f"    P95: {s['p95_ms']}ms")
            print(f"    P99: {s['p99_ms']}ms")
            print(f"    QPS: {s['qps']}")
        
        # 健康状态
        health = monitor.get_api_health()
        print(f"\nAPI健康状态:")
        print(f"  状态: {health['status']}")
        print(f"  错误率: {health['error_rate']}%")
        print(f"  慢端点数: {health['slow_endpoints_count']}")
        
        # 停止监控
        monitor.stop_monitoring()
        task.cancel()
    
    asyncio.run(test())
