#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用服务层监控器 (L3)
提供 API、数据库、缓存的详细监控
"""

import time
import logging
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import deque
import requests
import sqlite3
import os

logger = logging.getLogger(__name__)


@dataclass
class APIEndpointMetrics:
    """API端点指标"""
    endpoint: str
    method: str
    request_count: int
    error_count: int
    error_rate: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    last_status_code: int
    last_error: Optional[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class APIServiceMetrics:
    """API服务整体指标"""
    service_name: str
    base_url: str
    total_requests: int
    total_errors: int
    overall_error_rate: float
    avg_response_time: float
    availability_percent: float
    endpoints: List[APIEndpointMetrics] = field(default_factory=list)
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['endpoints'] = [e.to_dict() for e in self.endpoints]
        return result


@dataclass
class DatabaseMetrics:
    """数据库指标"""
    db_type: str
    connection_pool_size: int
    active_connections: int
    idle_connections: int
    total_queries: int
    slow_queries: int
    slow_query_threshold_ms: float
    avg_query_time: float
    max_query_time: float
    total_transactions: int
    failed_transactions: int
    db_size_bytes: int
    table_count: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheMetrics:
    """缓存指标"""
    cache_type: str
    total_keys: int
    memory_used_bytes: int
    memory_total_bytes: int
    hit_count: int
    miss_count: int
    hit_rate: float
    eviction_count: int
    expired_count: int
    avg_ttl_seconds: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class APIDetailedMonitor:
    """
    API详细监控器
    
    监控指标：
    - 各端点请求次数
    - 响应时间分布（P50/P95/P99）
    - 错误率和错误类型
    - 服务可用性
    - 端点健康状态
    """
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self._response_times: Dict[str, deque] = {}
        self._error_counts: Dict[str, int] = {}
        self._request_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, str] = {}
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        error: Optional[str] = None
    ):
        """
        记录API请求
        
        Args:
            endpoint: 端点路径
            method: HTTP方法
            response_time_ms: 响应时间（毫秒）
            status_code: 状态码
            error: 错误信息
        """
        key = f"{method}:{endpoint}"
        
        # 初始化数据结构
        if key not in self._response_times:
            self._response_times[key] = deque(maxlen=self.history_size)
            self._error_counts[key] = 0
            self._request_counts[key] = 0
        
        # 记录数据
        self._request_counts[key] += 1
        self._response_times[key].append({
            'timestamp': datetime.now().isoformat(),
            'response_time': response_time_ms,
            'status_code': status_code
        })
        
        # 记录错误
        if status_code >= 400 or error:
            self._error_counts[key] += 1
            if error:
                self._last_errors[key] = error
    
    def check_endpoint(
        self,
        base_url: str,
        endpoint: str,
        method: str = "GET",
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        主动检查端点健康状态
        
        Args:
            base_url: 基础URL
            endpoint: 端点路径
            method: HTTP方法
            timeout: 超时时间
            
        Returns:
            检查结果
        """
        url = f"{base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, timeout=timeout)
            else:
                response = requests.request(method.upper(), url, timeout=timeout)
            
            response_time = (time.time() - start_time) * 1000
            
            # 记录请求
            self.record_request(
                endpoint=endpoint,
                method=method,
                response_time_ms=response_time,
                status_code=response.status_code,
                error=None if response.ok else f"HTTP {response.status_code}"
            )
            
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "healthy": response.ok,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.Timeout:
            self.record_request(
                endpoint=endpoint,
                method=method,
                response_time_ms=timeout * 1000,
                status_code=0,
                error="Timeout"
            )
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time_ms": timeout * 1000,
                "healthy": False,
                "error": "Timeout",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.record_request(
                endpoint=endpoint,
                method=method,
                response_time_ms=0,
                status_code=0,
                error=str(e)
            )
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time_ms": 0,
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_endpoint_metrics(self, endpoint: str, method: str) -> APIEndpointMetrics:
        """
        获取端点指标
        
        Args:
            endpoint: 端点路径
            method: HTTP方法
            
        Returns:
            端点指标
        """
        key = f"{method}:{endpoint}"
        
        request_count = self._request_counts.get(key, 0)
        error_count = self._error_counts.get(key, 0)
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0
        
        response_times = self._response_times.get(key, deque())
        
        if response_times:
            times = [r['response_time'] for r in response_times]
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            # 计算百分位数
            sorted_times = sorted(times)
            p50_idx = len(sorted_times) // 2
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            p50_time = sorted_times[p50_idx] if sorted_times else 0
            p95_time = (
                sorted_times[p95_idx] 
                if p95_idx < len(sorted_times) 
                else sorted_times[-1]
            )
            p99_time = (
                sorted_times[p99_idx] 
                if p99_idx < len(sorted_times) 
                else sorted_times[-1]
            )
            
            last_status = response_times[-1]['status_code']
        else:
            avg_time = min_time = max_time = p50_time = p95_time = p99_time = 0
            last_status = 0
        
        return APIEndpointMetrics(
            endpoint=endpoint,
            method=method,
            request_count=request_count,
            error_count=error_count,
            error_rate=round(error_rate, 2),
            avg_response_time=round(avg_time, 2),
            min_response_time=round(min_time, 2),
            max_response_time=round(max_time, 2),
            p50_response_time=round(p50_time, 2),
            p95_response_time=round(p95_time, 2),
            p99_response_time=round(p99_time, 2),
            last_status_code=last_status,
            last_error=self._last_errors.get(key),
            timestamp=datetime.now().isoformat()
        )
    
    def get_service_metrics(
        self,
        service_name: str,
        base_url: str,
        endpoints: List[Dict[str, str]]
    ) -> APIServiceMetrics:
        """
        获取服务整体指标
        
        Args:
            service_name: 服务名称
            base_url: 基础URL
            endpoints: 端点列表 [{"path": "/health", "method": "GET"}, ...]
            
        Returns:
            服务指标
        """
        endpoint_metrics = []
        total_requests = 0
        total_errors = 0
        total_response_time = 0
        healthy_count = 0
        
        for ep in endpoints:
            path = ep['path']
            method = ep.get('method', 'GET')
            
            # 主动检查端点
            check_result = self.check_endpoint(base_url, path, method)
            
            # 获取端点指标
            metrics = self.get_endpoint_metrics(path, method)
            endpoint_metrics.append(metrics)
            
            total_requests += metrics.request_count
            total_errors += metrics.error_count
            total_response_time += metrics.avg_response_time
            
            if check_result['healthy']:
                healthy_count += 1
        
        # 计算整体指标
        endpoint_count = len(endpoints)
        availability = (
            healthy_count / endpoint_count * 100
        ) if endpoint_count > 0 else 0
        overall_error_rate = (
            total_errors / total_requests * 100
        ) if total_requests > 0 else 0
        avg_response_time = (
            total_response_time / endpoint_count
        ) if endpoint_count > 0 else 0
        
        return APIServiceMetrics(
            service_name=service_name,
            base_url=base_url,
            total_requests=total_requests,
            total_errors=total_errors,
            overall_error_rate=round(overall_error_rate, 2),
            avg_response_time=round(avg_response_time, 2),
            availability_percent=round(availability, 2),
            endpoints=endpoint_metrics,
            timestamp=datetime.now().isoformat()
        )


class DatabaseMonitor:
    """
    数据库监控器
    
    监控指标：
    - 连接池状态
    - 查询性能（平均/最大时间）
    - 慢查询统计
    - 事务成功率
    - 数据库大小
    - 表数量
    """
    
    def __init__(self, slow_query_threshold_ms: float = 1000):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self._query_times: deque = deque(maxlen=1000)
        self._transaction_count = 0
        self._failed_transaction_count = 0
    
    def record_query(self, query_time_ms: float, is_slow: bool = False):
        """
        记录查询时间
        
        Args:
            query_time_ms: 查询时间（毫秒）
            is_slow: 是否为慢查询
        """
        self._query_times.append({
            'timestamp': datetime.now().isoformat(),
            'query_time': query_time_ms,
            'is_slow': is_slow
        })
    
    def record_transaction(self, success: bool):
        """
        记录事务
        
        Args:
            success: 是否成功
        """
        self._transaction_count += 1
        if not success:
            self._failed_transaction_count += 1
    
    def get_metrics(self, db_path: Optional[str] = None) -> DatabaseMetrics:
        """
        获取数据库指标
        
        Args:
            db_path: 数据库文件路径（SQLite）
            
        Returns:
            数据库指标
        """
        # 计算查询统计
        if self._query_times:
            times = [q['query_time'] for q in self._query_times]
            avg_time = statistics.mean(times)
            max_time = max(times)
            slow_count = sum(1 for q in self._query_times if q['is_slow'])
        else:
            avg_time = max_time = 0
            slow_count = 0
        
        # 获取数据库文件信息
        db_size = 0
        table_count = 0
        
        if db_path and os.path.exists(db_path):
            try:
                db_size = os.path.getsize(db_path)
                
                # 获取表数量
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table'"
                )
                table_count = cursor.fetchone()[0]
                conn.close()
            except Exception as e:
                logger.error(f"获取数据库信息失败: {e}")
        
        return DatabaseMetrics(
            db_type="sqlite",
            connection_pool_size=10,  # 默认值
            active_connections=0,  # 需要实际检测
            idle_connections=10,
            total_queries=len(self._query_times),
            slow_queries=slow_count,
            slow_query_threshold_ms=self.slow_query_threshold_ms,
            avg_query_time=round(avg_time, 2),
            max_query_time=round(max_time, 2),
            total_transactions=self._transaction_count,
            failed_transactions=self._failed_transaction_count,
            db_size_bytes=db_size,
            table_count=table_count,
            timestamp=datetime.now().isoformat()
        )


class CacheMonitor:
    """
    缓存监控器
    
    监控指标：
    - 键值数量
    - 内存使用
    - 命中率/未命中率
    - 淘汰数量
    - 过期数量
    - 平均TTL
    """
    
    def __init__(self):
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
    
    def record_hit(self):
        """记录缓存命中"""
        self._hits += 1
    
    def record_miss(self):
        """记录缓存未命中"""
        self._misses += 1
    
    def record_eviction(self):
        """记录缓存淘汰"""
        self._evictions += 1
    
    def record_expiration(self):
        """记录缓存过期"""
        self._expirations += 1
    
    def get_metrics(self) -> CacheMetrics:
        """
        获取缓存指标
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return CacheMetrics(
            cache_type="memory",
            total_keys=0,  # 需要实际统计
            memory_used_bytes=0,
            memory_total_bytes=0,
            hit_count=self._hits,
            miss_count=self._misses,
            hit_rate=round(hit_rate, 2),
            eviction_count=self._evictions,
            expired_count=self._expirations,
            avg_ttl_seconds=0,
            timestamp=datetime.now().isoformat()
        )


class ApplicationCollector:
    """
    应用服务指标采集器
    
    整合 API、数据库、缓存监控器
    """
    
    def __init__(self):
        self.api_monitor = APIDetailedMonitor()
        self.db_monitor = DatabaseMonitor()
        self.cache_monitor = CacheMonitor()
        
        # 配置监控的服务
        self.services = {
            'yl-monitor': {
                'base_url': 'http://0.0.0.0:5500',
                'endpoints': [
                    {'path': '/api/health', 'method': 'GET'},
                    {'path': '/api/v1/monitor/infrastructure', 'method': 'GET'},
                    {'path': '/api/v1/monitor/system-resources', 'method': 'GET'}
                ]
            },
            'ar-backend': {
                'base_url': 'http://0.0.0.0:5501',
                'endpoints': [
                    {'path': '/health', 'method': 'GET'},
                    {'path': '/status', 'method': 'GET'}
                ]
            },
            'user-gui': {
                'base_url': 'http://0.0.0.0:5502',
                'endpoints': [
                    {'path': '/health', 'method': 'GET'},
                    {'path': '/status', 'method': 'GET'}
                ]
            }
        }
    
    def collect_all(self) -> Dict[str, Any]:
        """
        采集所有应用服务层指标
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "layer": "L3_application_services"
        }
        
        # API 服务监控
        api_metrics = {}
        for service_name, config in self.services.items():
            try:
                metrics = self.api_monitor.get_service_metrics(
                    service_name=service_name,
                    base_url=config['base_url'],
                    endpoints=config['endpoints']
                )
                api_metrics[service_name] = metrics.to_dict()
            except Exception as e:
                logger.error(f"监控API服务失败 {service_name}: {e}")
                api_metrics[service_name] = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        result["api_services"] = api_metrics
        
        # 数据库监控
        try:
            db_path = "YL-monitor/data/monitor.db"  # 默认路径
            result["database"] = self.db_monitor.get_metrics(db_path).to_dict()
        except Exception as e:
            result["database"] = {"error": str(e)}
        
        # 缓存监控
        try:
            result["cache"] = self.cache_monitor.get_metrics().to_dict()
        except Exception as e:
            result["cache"] = {"error": str(e)}
        
        return result
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        获取指定服务的健康状态
        """
        if service_name not in self.services:
            return {
                "error": f"未知服务: {service_name}",
                "timestamp": datetime.now().isoformat()
            }
        
        config = self.services[service_name]
        
        try:
            metrics = self.api_monitor.get_service_metrics(
                service_name=service_name,
                base_url=config['base_url'],
                endpoints=config['endpoints']
            )
            
            # 评估健康状态
            is_healthy = (
                metrics.availability_percent >= 95 and
                metrics.overall_error_rate < 5
            )
            
            return {
                "service": service_name,
                "healthy": is_healthy,
                "availability": metrics.availability_percent,
                "error_rate": metrics.overall_error_rate,
                "avg_response_time": metrics.avg_response_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "service": service_name,
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局采集器实例
application_collector = ApplicationCollector()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("应用服务层监控测试")
    print("=" * 60)
    
    collector = ApplicationCollector()
    
    # 测试 API 监控
    print("\n1. API 服务监控:")
    for service_name in collector.services.keys():
        health = collector.get_service_health(service_name)
        status = "✅ 健康" if health.get('healthy') else "❌ 异常"
        print(f"  {status} {service_name}:")
        if 'error' in health:
            print(f"    错误: {health['error']}")
        else:
            avail = health.get('availability', 0)
            err_rate = health.get('error_rate', 0)
            avg_resp = health.get('avg_response_time', 0)
            print(f"    可用性: {avail:.1f}%")
            print(f"    错误率: {err_rate:.2f}%")
            print(f"    平均响应: {avg_resp:.2f}ms")
    
    # 测试数据库监控
    print("\n2. 数据库监控:")
    try:
        db_metrics = collector.db_monitor.get_metrics()
        print(f"  查询总数: {db_metrics.total_queries}")
        print(f"  慢查询: {db_metrics.slow_queries}")
        print(f"  平均查询时间: {db_metrics.avg_query_time:.2f}ms")
    except Exception as e:
        print(f"  ❌ 数据库监控失败: {e}")
    
    # 测试缓存监控
    print("\n3. 缓存监控:")
    try:
        cache_metrics = collector.cache_monitor.get_metrics()
        print(f"  命中次数: {cache_metrics.hit_count}")
        print(f"  未命中: {cache_metrics.miss_count}")
        print(f"  命中率: {cache_metrics.hit_rate:.1f}%")
    except Exception as e:
        print(f"  ❌ 缓存监控失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
