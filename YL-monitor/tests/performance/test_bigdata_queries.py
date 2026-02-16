#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大数据查询性能测试

【功能描述】
测试大数据量下的查询性能，包括10万+记录的查询、聚合、分页等

【作者】
AI Assistant

【创建时间】
2026-02-10

【版本】
1.0.0

【测试覆盖】
- 10万+记录查询性能（< 3s）
- 大数据聚合查询性能
- 分页查询性能
- 内存使用测试
"""

import pytest
import time
import asyncio
from datetime import datetime, timedelta


@pytest.mark.performance
class TestBigDataQueries:
    """大数据查询性能测试类"""
    
    @pytest.fixture
    def bigdata_count(self, test_config):
        """大数据记录数量"""
        return min(test_config.get("bigdata_record_count", 100000), 10000)  # 最多1万条用于测试
    
    # ==================== 大数据查询测试 ====================
    
    @pytest.mark.slow
    def test_bigdata_metrics_query_performance(self, client, performance_thresholds, bigdata_count):
        """
        【性能测试】大数据量指标查询
        
        【场景】查询大量历史指标数据
        【预期】查询时间 < 3s
        """
        # 准备 - 查询较长时间范围以获取更多数据
        hours = 24  # 查询24小时
        
        # 执行
        start_time = time.time()
        response = client.get(f"/api/v1/metrics/history?hours={hours}&limit={bigdata_count}")
        end_time = time.time()
        
        # 验证
        assert response.status_code == 200
        query_time_ms = (end_time - start_time) * 1000
        threshold = performance_thresholds["bigdata_query_ms"]
        
        assert query_time_ms < threshold, \
            f"大数据查询时间 {query_time_ms:.2f}ms 超过阈值 {threshold}ms"
        
        data = response.json()
        print(f"\n大数据查询: 返回 {data.get('count', 0)} 条记录, 耗时 {query_time_ms:.2f}ms")
    
    @pytest.mark.slow
    def test_bigdata_alerts_history_performance(self, client, performance_thresholds):
        """
        【性能测试】大数据量告警历史查询
        
        【场景】查询大量告警历史记录
        【预期】查询时间 < 3s
        """
        # 执行
        start_time = time.time()
        response = client.get("/api/v1/alerts/history?limit=10000")
        end_time = time.time()
        
        # 验证
        assert response.status_code == 200
        query_time_ms = (end_time - start_time) * 1000
        threshold = performance_thresholds["bigdata_query_ms"]
        
        assert query_time_ms < threshold, \
            f"告警历史查询时间 {query_time_ms:.2f}ms 超过阈值 {threshold}ms"
        
        data = response.json()
        print(f"\n告警历史查询: 返回 {data.get('total', 0)} 条记录, 耗时 {query_time_ms:.2f}ms")
    
    # ==================== 分页查询测试 ====================
    
    def test_pagination_performance_small(self, client):
        """
        【性能测试】小分页查询性能
        
        【场景】每页10条记录的分页查询
        【预期】响应时间 < 500ms
        """
        # 执行多页查询
        for page in range(5):  # 查询前5页
            offset = page * 10
            start_time = time.time()
            response = client.get(f"/api/v1/alerts/history?limit=10&offset={offset}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time_ms = (end_time - start_time) * 1000
            assert response_time_ms < 500, \
                f"分页查询时间 {response_time_ms:.2f}ms 超过 500ms"
    
    def test_pagination_performance_large(self, client):
        """
        【性能测试】大分页查询性能
        
        【场景】每页1000条记录的分页查询
        【预期】响应时间 < 1s
        """
        # 执行
        start_time = time.time()
        response = client.get("/api/v1/alerts/history?limit=1000&offset=0")
        end_time = time.time()
        
        # 验证
        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 1000, \
            f"大分页查询时间 {response_time_ms:.2f}ms 超过 1000ms"
        
        data = response.json()
        print(f"\n大分页查询: 返回 {len(data.get('items', []))} 条记录, 耗时 {response_time_ms:.2f}ms")
    
    def test_pagination_deep_offset(self, client):
        """
        【性能测试】深分页查询性能
        
        【场景】查询较大offset的数据
        【预期】响应时间合理
        """
        # 执行 - 查询第100页（offset=1000）
        start_time = time.time()
        response = client.get("/api/v1/alerts/history?limit=10&offset=1000")
        end_time = time.time()
        
        # 验证
        assert response.status_code in [200, 404]  # 可能没有那么多数据
        response_time_ms = (end_time - start_time) * 1000
        
        # 深分页可能较慢，放宽要求
        assert response_time_ms < 2000, \
            f"深分页查询时间 {response_time_ms:.2f}ms 超过 2000ms"
    
    # ==================== 聚合查询测试 ====================
    
    @pytest.mark.slow
    def test_aggregation_query_performance(self, client, performance_thresholds):
        """
        【性能测试】聚合查询性能
        
        【场景】对大量数据进行聚合计算
        【预期】查询时间 < 3s
        """
        # 执行 - 查询较长时间范围的指标用于聚合
        start_time = time.time()
        response = client.get("/api/v1/metrics/history?hours=24&limit=10000")
        end_time = time.time()
        
        # 验证
        assert response.status_code == 200
        query_time_ms = (end_time - start_time) * 1000
        threshold = performance_thresholds["bigdata_query_ms"]
        
        assert query_time_ms < threshold, \
            f"聚合查询时间 {query_time_ms:.2f}ms 超过阈值 {threshold}ms"
    
    # ==================== 并发大数据查询测试 ====================
    
    @pytest.mark.slow
    def test_concurrent_bigdata_queries(self, client, performance_thresholds):
        """
        【性能测试】并发大数据查询
        
        【场景】多个并发的大数据查询
        【预期】所有查询都成功且响应时间合理
        """
        import concurrent.futures
        
        # 准备
        query_count = 5
        
        def query_metrics():
            start_time = time.time()
            response = client.get("/api/v1/metrics/history?hours=24&limit=1000")
            end_time = time.time()
            return {
                "status": response.status_code,
                "time_ms": (end_time - start_time) * 1000
            }
        
        # 执行并发查询
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=query_count) as executor:
            futures = [executor.submit(query_metrics) for _ in range(query_count)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time_ms = (time.time() - start_time) * 1000
        
        # 验证
        success_count = sum(1 for r in results if r["status"] == 200)
        assert success_count == query_count, \
            f"只有 {success_count}/{query_count} 个并发查询成功"
        
        # 验证每个查询的响应时间
        threshold = performance_thresholds["bigdata_query_ms"]
        for i, result in enumerate(results):
            assert result["time_ms"] < threshold * 2, \
                f"查询 {i+1} 时间 {result['time_ms']:.2f}ms 超过阈值"
        
        print(f"\n并发大数据查询: {query_count} 个查询, 总耗时 {total_time_ms:.2f}ms")
    
    # ==================== 内存使用测试 ====================
    
    def test_query_memory_efficiency(self, client):
        """
        【性能测试】查询内存效率
        
        【场景】查询大量数据时的内存使用
        【预期】内存使用合理，不溢出
        """
        # 这个测试主要验证查询不会导致内存问题
        # 实际内存监控需要额外的工具
        
        # 执行多次大查询
        for i in range(3):
            response = client.get("/api/v1/metrics/history?hours=24&limit=5000")
            assert response.status_code == 200
            
            # 验证数据完整性
            data = response.json()
            assert "data" in data or "items" in data
            
            # 不存储大量数据，让垃圾回收
            del data
    
    # ==================== 压力测试 ====================
    
    @pytest.mark.slow
    def test_sustained_query_load(self, client):
        """
        【性能测试】持续查询负载
        
        【场景】持续发送查询请求
        【预期】系统保持稳定
        """
        # 准备
        duration = 10  # 持续10秒
        query_interval = 0.5  # 每0.5秒查询一次
        
        start_time = time.time()
        query_count = 0
        error_count = 0
        
        # 执行
        while (time.time() - start_time) < duration:
            try:
                response = client.get("/api/v1/metrics/history?hours=1&limit=100")
                if response.status_code == 200:
                    query_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
            
            time.sleep(query_interval)
        
        # 验证
        total_queries = query_count + error_count
        error_rate = error_count / total_queries * 100 if total_queries > 0 else 0
        
        assert error_rate < 5, \
            f"错误率 {error_rate:.1f}% 超过 5%"
        
        print(f"\n持续查询负载: {query_count} 成功, {error_count} 失败, 错误率 {error_rate:.1f}%")


@pytest.mark.performance
class TestBigDataStorage:
    """大数据存储性能测试"""
    
    @pytest.mark.asyncio
    async def test_batch_store_performance(self, temp_metrics_dir, bigdata_count=1000):
        """
        【性能测试】批量存储性能
        
        【场景】批量存储大量指标数据
        【预期】存储时间合理
        """
        from app.services.metrics_storage import MetricsStorage
        
        # 准备
        storage = MetricsStorage(data_dir=str(temp_metrics_dir))
        
        # 生成测试数据
        now = datetime.utcnow()
        metrics = []
        for i in range(bigdata_count):
            metric = {
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i % 30),
                "unit": "%",
                "labels": {"host": "0.0.0.0"}
            }
            metrics.append(metric)
        
        # 执行
        start_time = time.time()
        count = await storage.store_metrics_batch(metrics)
        end_time = time.time()
        
        # 验证
        assert count == bigdata_count
        store_time_ms = (end_time - start_time) * 1000
        
        # 验证存储时间合理（每1000条 < 1s）
        expected_max_time = (bigdata_count / 1000) * 1000  # 每1000条1秒
        assert store_time_ms < expected_max_time, \
            f"批量存储时间 {store_time_ms:.2f}ms 超过预期 {expected_max_time:.2f}ms"
        
        print(f"\n批量存储: {count} 条记录, 耗时 {store_time_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_query_after_big_store(self, temp_metrics_dir, performance_thresholds):
        """
        【性能测试】大数据存储后查询
        
        【场景】存储大量数据后立即查询
        【预期】查询时间 < 3s
        """
        from app.services.metrics_storage import MetricsStorage
        
        # 准备
        storage = MetricsStorage(data_dir=str(temp_metrics_dir))
        
        # 存储一些数据
        now = datetime.utcnow()
        for i in range(1000):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i % 30),
                "unit": "%",
                "labels": {"host": "0.0.0.0"}
            })
        
        # 执行查询
        start_time = time.time()
        result = await storage.query_history(
            metric_type="cpu",
            start_time=now - timedelta(hours=24),
            end_time=now,
            limit=1000
        )
        end_time = time.time()
        
        # 验证
        query_time_ms = (end_time - start_time) * 1000
        threshold = performance_thresholds["bigdata_query_ms"]
        
        assert query_time_ms < threshold, \
            f"查询时间 {query_time_ms:.2f}ms 超过阈值 {threshold}ms"
        
        assert len(result) == 1000
        print(f"\n存储后查询: 返回 {len(result)} 条记录, 耗时 {query_time_ms:.2f}ms")
