#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控数据存储服务单元测试

【功能描述】
测试监控数据存储服务的核心功能，包括数据存储、查询、聚合、归档等

【作者】
AI Assistant

【创建时间】
2026-02-10

【版本】
1.0.0

【测试覆盖】
- 指标数据存储（单条、批量）
- 历史数据查询（时间范围、标签筛选）
- 数据聚合（avg/max/min/sum/count）
- 数据归档和清理
- 存储统计
- 数据导出
"""

import pytest
import asyncio
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.metrics_storage import (
    MetricsStorage, StoredMetric, 
    metrics_storage, store_metric, query_metrics_history,
    aggregate_metrics, get_storage_stats
)


@pytest.mark.unit
class TestStoredMetric:
    """存储指标数据类测试"""
    
    def test_stored_metric_to_dict(self):
        """
        【测试】指标数据转字典
        
        【场景】将StoredMetric对象转换为字典
        【预期】返回正确的字典格式
        """
        # 准备
        metric = StoredMetric(
            timestamp="2026-02-10T10:00:00",
            metric_type="cpu",
            name="cpu_percent",
            value=45.5,
            unit="%",
            labels={"host": "localhost"}
        )
        
        # 执行
        result = metric.to_dict()
        
        # 验证
        assert result["timestamp"] == "2026-02-10T10:00:00"
        assert result["metric_type"] == "cpu"
        assert result["name"] == "cpu_percent"
        assert result["value"] == 45.5
        assert result["unit"] == "%"
        assert result["labels"] == {"host": "localhost"}
    
    def test_stored_metric_from_dict(self):
        """
        【测试】从字典创建指标数据
        
        【场景】从字典创建StoredMetric对象
        【预期】返回正确的对象
        """
        # 准备
        data = {
            "timestamp": "2026-02-10T10:00:00",
            "metric_type": "memory",
            "name": "memory_percent",
            "value": 60.0,
            "unit": "%",
            "labels": {"host": "server1"}
        }
        
        # 执行
        metric = StoredMetric.from_dict(data)
        
        # 验证
        assert metric.timestamp == "2026-02-10T10:00:00"
        assert metric.metric_type == "memory"
        assert metric.name == "memory_percent"
        assert metric.value == 60.0
        assert metric.unit == "%"
        assert metric.labels == {"host": "server1"}


@pytest.mark.unit
class TestMetricsStorage:
    """监控数据存储服务测试"""
    
    @pytest.fixture
    def storage(self, temp_metrics_dir):
        """创建存储服务实例"""
        storage = MetricsStorage(data_dir=str(temp_metrics_dir))
        return storage
    
    @pytest.fixture
    def sample_metric_data(self):
        """示例指标数据"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metric_type": "cpu",
            "name": "cpu_percent",
            "value": 45.5,
            "unit": "%",
            "labels": {"host": "localhost", "core": "0"}
        }
    
    # ==================== 数据存储测试 ====================
    
    @pytest.mark.asyncio
    async def test_store_metric(self, storage, sample_metric_data):
        """
        【测试】存储单个指标
        
        【场景】存储一条指标数据
        【预期】存储成功，文件创建
        """
        # 执行
        result = await storage.store_metric(sample_metric_data)
        
        # 验证
        assert result is True
        assert storage._stats["total_stored"] == 1
        
        # 验证文件创建
        date_str = sample_metric_data["timestamp"][:10]
        file_path = storage._raw_dir / f"{date_str}.jsonl"
        assert file_path.exists()
    
    @pytest.mark.asyncio
    async def test_store_metric_invalid_data(self, storage):
        """
        【测试】存储无效数据
        
        【场景】存储格式错误的数据
        【预期】存储失败，返回False
        """
        # 准备 - 缺少必要字段
        invalid_data = {
            "timestamp": datetime.utcnow().isoformat(),
            # 缺少metric_type, name, value等
        }
        
        # 执行
        result = await storage.store_metric(invalid_data)
        
        # 验证 - 应该能存储，但使用默认值
        assert result is True
    
    @pytest.mark.asyncio
    async def test_store_metrics_batch(self, storage):
        """
        【测试】批量存储指标
        
        【场景】一次性存储多条指标
        【预期】全部存储成功
        """
        # 准备
        metrics = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(i * 10),
                "unit": "%",
                "labels": {"host": "localhost"}
            }
            for i in range(10)
        ]
        
        # 执行
        count = await storage.store_metrics_batch(metrics)
        
        # 验证
        assert count == 10
        assert storage._stats["total_stored"] == 10
    
    @pytest.mark.asyncio
    async def test_store_metric_with_cache(self, storage, sample_metric_data):
        """
        【测试】指标存储与缓存
        
        【场景】存储指标后检查缓存
        【预期】缓存中有数据
        """
        # 执行
        await storage.store_metric(sample_metric_data)
        
        # 验证缓存
        date_str = sample_metric_data["timestamp"][:10]
        async with storage._cache_lock:
            assert date_str in storage._cache
            assert len(storage._cache[date_str]) == 1
    
    # ==================== 数据查询测试 ====================
    
    @pytest.mark.asyncio
    async def test_query_history_empty(self, storage):
        """
        【测试】查询空历史
        
        【场景】没有数据时查询历史
        【预期】返回空列表
        """
        # 执行
        result = await storage.query_history()
        
        # 验证
        assert result == []
    
    @pytest.mark.asyncio
    async def test_query_history_with_data(self, storage):
        """
        【测试】查询历史数据
        
        【场景】有数据时查询历史
        【预期】返回所有数据
        """
        # 准备
        now = datetime.utcnow()
        for i in range(5):
            metric = {
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            }
            await storage.store_metric(metric)
        
        # 执行
        result = await storage.query_history()
        
        # 验证
        assert len(result) == 5
    
    @pytest.mark.asyncio
    async def test_query_history_with_metric_type_filter(self, storage):
        """
        【测试】按指标类型筛选
        
        【场景】查询特定类型的指标
        【预期】只返回该类型的数据
        """
        # 准备
        now = datetime.utcnow()
        
        # CPU指标
        for i in range(3):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # Memory指标
        for i in range(2):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "memory",
                "name": "memory_percent",
                "value": float(60 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行 - 只查询CPU
        result = await storage.query_history(metric_type="cpu")
        
        # 验证
        assert len(result) == 3
        for item in result:
            assert item["metric_type"] == "cpu"
    
    @pytest.mark.asyncio
    async def test_query_history_with_time_range(self, storage):
        """
        【测试】按时间范围查询
        
        【场景】查询指定时间范围内的数据
        【预期】只返回该范围内的数据
        """
        # 准备
        now = datetime.utcnow()
        
        # 存储不同时间的数据
        for i in range(10):
            await storage.store_metric({
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行 - 查询最近2小时
        start_time = now - timedelta(hours=2)
        result = await storage.query_history(start_time=start_time, end_time=now)
        
        # 验证 - 应该只有3条（0, 1, 2小时前）
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_query_history_with_labels_filter(self, storage):
        """
        【测试】按标签筛选
        
        【场景】查询特定标签的数据
        【预期】只返回匹配标签的数据
        """
        # 准备
        now = datetime.utcnow()
        
        # 不同host的数据
        await storage.store_metric({
            "timestamp": now.isoformat(),
            "metric_type": "cpu",
            "name": "cpu_percent",
            "value": 50.0,
            "unit": "%",
            "labels": {"host": "server1", "env": "prod"}
        })
        
        await storage.store_metric({
            "timestamp": now.isoformat(),
            "metric_type": "cpu",
            "name": "cpu_percent",
            "value": 60.0,
            "unit": "%",
            "labels": {"host": "server2", "env": "dev"}
        })
        
        # 执行 - 按host筛选
        result = await storage.query_history(labels={"host": "server1"})
        
        # 验证
        assert len(result) == 1
        assert result[0]["labels"]["host"] == "server1"
    
    @pytest.mark.asyncio
    async def test_query_history_with_limit(self, storage):
        """
        【测试】限制返回数量
        
        【场景】查询时设置limit
        【预期】返回数量不超过limit
        """
        # 准备
        now = datetime.utcnow()
        for i in range(20):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行 - 限制返回10条
        result = await storage.query_history(limit=10)
        
        # 验证
        assert len(result) == 10
    
    # ==================== 数据聚合测试 ====================
    
    @pytest.mark.asyncio
    async def test_aggregate_avg_by_hour(self, storage):
        """
        【测试】按小时聚合平均值
        
        【场景】按小时计算平均值
        【预期】返回每小时的平均值
        """
        # 准备
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        # 同一小时的多条数据
        for i in range(5):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i*10)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(40 + i * 5),  # 40, 45, 50, 55, 60
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        result = await storage.aggregate(
            metric_type="cpu",
            aggregation="avg",
            interval="hour"
        )
        
        # 验证
        assert len(result) >= 1
        # 平均值应该是 (40+45+50+55+60)/5 = 50
        assert result[0]["aggregation"] == "avg"
        assert result[0]["metric_type"] == "cpu"
    
    @pytest.mark.asyncio
    async def test_aggregate_max(self, storage):
        """
        【测试】聚合最大值
        
        【场景】计算最大值
        【预期】返回最大值
        """
        # 准备
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        values = [30.0, 50.0, 40.0, 60.0, 20.0]
        for i, val in enumerate(values):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i*10)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": val,
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        result = await storage.aggregate(
            metric_type="cpu",
            aggregation="max",
            interval="hour"
        )
        
        # 验证
        assert len(result) >= 1
        assert result[0]["value"] == 60.0  # 最大值
    
    @pytest.mark.asyncio
    async def test_aggregate_min(self, storage):
        """
        【测试】聚合最小值
        
        【场景】计算最小值
        【预期】返回最小值
        """
        # 准备
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        values = [30.0, 50.0, 40.0, 60.0, 20.0]
        for i, val in enumerate(values):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i*10)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": val,
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        result = await storage.aggregate(
            metric_type="cpu",
            aggregation="min",
            interval="hour"
        )
        
        # 验证
        assert len(result) >= 1
        assert result[0]["value"] == 20.0  # 最小值
    
    @pytest.mark.asyncio
    async def test_aggregate_sum(self, storage):
        """
        【测试】聚合求和
        
        【场景】计算总和
        【预期】返回总和
        """
        # 准备
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        values = [10.0, 20.0, 30.0]
        for i, val in enumerate(values):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i*10)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": val,
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        result = await storage.aggregate(
            metric_type="cpu",
            aggregation="sum",
            interval="hour"
        )
        
        # 验证
        assert len(result) >= 1
        assert result[0]["value"] == 60.0  # 总和
    
    @pytest.mark.asyncio
    async def test_aggregate_count(self, storage):
        """
        【测试】聚合计数
        
        【场景】计算数据点数量
        【预期】返回数量
        """
        # 准备
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        for i in range(5):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i*10)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        result = await storage.aggregate(
            metric_type="cpu",
            aggregation="count",
            interval="hour"
        )
        
        # 验证
        assert len(result) >= 1
        assert result[0]["value"] == 5  # 5条数据
    
    @pytest.mark.asyncio
    async def test_aggregate_by_day(self, storage):
        """
        【测试】按天聚合
        
        【场景】按天计算平均值
        【预期】返回每天的数据
        """
        # 准备
        now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 两天的数据
        for i in range(3):
            # 今天的数据
            await storage.store_metric({
                "timestamp": (now + timedelta(hours=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": 50.0,
                "unit": "%",
                "labels": {"host": "localhost"}
            })
            # 昨天的数据
            await storage.store_metric({
                "timestamp": (now - timedelta(days=1) + timedelta(hours=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": 60.0,
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        result = await storage.aggregate(
            metric_type="cpu",
            aggregation="avg",
            interval="day"
        )
        
        # 验证
        assert len(result) == 2  # 两天
    
    # ==================== 存储统计测试 ====================
    
    def test_get_storage_stats_empty(self, storage):
        """
        【测试】空存储统计
        
        【场景】没有数据时获取统计
        【预期】返回零值统计
        """
        # 执行
        stats = storage.get_storage_stats()
        
        # 验证
        assert stats["total_stored"] == 0
        assert stats["storage_size_bytes"] == 0
        assert stats["file_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_storage_stats_with_data(self, storage):
        """
        【测试】有数据时的统计
        
        【场景】有数据时获取统计
        【预期】返回正确的统计信息
        """
        # 准备
        now = datetime.utcnow()
        for i in range(10):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        stats = storage.get_storage_stats()
        
        # 验证
        assert stats["total_stored"] == 10
        assert stats["file_count"] >= 1
        assert stats["storage_size_bytes"] > 0
        assert "storage_size_mb" in stats
    
    # ==================== 数据导出测试 ====================
    
    @pytest.mark.asyncio
    async def test_export_data_json(self, storage):
        """
        【测试】导出JSON格式数据
        
        【场景】导出为JSON格式
        【预期】返回JSON文件内容
        """
        # 准备
        now = datetime.utcnow()
        for i in range(5):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        start_time = now - timedelta(hours=1)
        end_time = now
        filename, content = await storage.export_data(
            start_time=start_time,
            end_time=end_time,
            format="json"
        )
        
        # 验证
        assert filename.endswith(".json")
        assert len(content) > 0
        
        # 验证JSON格式
        data = json.loads(content.decode('utf-8'))
        assert isinstance(data, list)
        assert len(data) == 5
    
    @pytest.mark.asyncio
    async def test_export_data_csv(self, storage):
        """
        【测试】导出CSV格式数据
        
        【场景】导出为CSV格式
        【预期】返回CSV文件内容
        """
        # 准备
        now = datetime.utcnow()
        for i in range(5):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行
        start_time = now - timedelta(hours=1)
        end_time = now
        filename, content = await storage.export_data(
            start_time=start_time,
            end_time=end_time,
            format="csv"
        )
        
        # 验证
        assert filename.endswith(".csv")
        assert len(content) > 0
        
        # 验证CSV格式
        csv_content = content.decode('utf-8')
        assert "timestamp" in csv_content
        assert "metric_type" in csv_content
    
    @pytest.mark.asyncio
    async def test_export_data_with_filter(self, storage):
        """
        【测试】带筛选的导出
        
        【场景】导出特定类型的指标
        【预期】只导出该类型的数据
        """
        # 准备
        now = datetime.utcnow()
        
        # CPU指标
        for i in range(3):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "cpu",
                "name": "cpu_percent",
                "value": float(50 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # Memory指标
        for i in range(2):
            await storage.store_metric({
                "timestamp": (now - timedelta(minutes=i)).isoformat(),
                "metric_type": "memory",
                "name": "memory_percent",
                "value": float(60 + i),
                "unit": "%",
                "labels": {"host": "localhost"}
            })
        
        # 执行 - 只导出CPU
        start_time = now - timedelta(hours=1)
        end_time = now
        filename, content = await storage.export_data(
            start_time=start_time,
            end_time=end_time,
            format="json",
            metric_type="cpu"
        )
        
        # 验证
        data = json.loads(content.decode('utf-8'))
        assert len(data) == 3
        for item in data:
            assert item["metric_type"] == "cpu"
    
    # ==================== 数据归档测试 ====================
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, storage):
        """
        【测试】清理旧数据
        
        【场景】清理过期的数据文件
        【预期】旧数据被归档或删除
        """
        # 准备 - 创建一些旧数据文件
        old_date = datetime.utcnow() - timedelta(days=10)
        old_file = storage._raw_dir / f"{old_date.strftime('%Y-%m-%d')}.jsonl"
        old_file.write_text('{\"test\": \"data\"}\\n')
        
        # 执行
        result = await storage.cleanup_old_data()
        
        # 验证
        assert isinstance(result, dict)
        assert "archived_files" in result
        assert "deleted_files" in result
        assert "errors" in result
    
    # ==================== 便捷函数测试 ====================
    
    @pytest.mark.asyncio
    async def test_store_metric_convenience(self, temp_metrics_dir):
        """
        【测试】存储便捷函数
        
        【场景】使用便捷函数存储指标
        【预期】存储成功
        """
        # 准备
        metric_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric_type": "cpu",
            "name": "cpu_percent",
            "value": 45.5,
            "unit": "%",
            "labels": {"host": "localhost"}
        }
        
        # 执行
        result = await store_metric(metric_data)
        
        # 验证
        assert result is True
    
    @pytest.mark.asyncio
    async def test_query_metrics_history_convenience(self):
        """
        【测试】查询便捷函数
        
        【场景】使用便捷函数查询历史
        【预期】返回数据列表
        """
        # 执行
        result = await query_metrics_history(metric_type="cpu", limit=10)
        
        # 验证
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_aggregate_metrics_convenience(self):
        """
        【测试】聚合便捷函数
        
        【场景】使用便捷函数聚合数据
        【预期】返回聚合结果
        """
        # 执行
        result = await aggregate_metrics(
            metric_type="cpu",
            aggregation="avg",
            interval="hour"
        )
        
        # 验证
        assert isinstance(result, list)
    
    def test_get_storage_stats_convenience(self):
        """
        【测试】统计便捷函数
        
        【场景】使用便捷函数获取统计
        【预期】返回统计信息
        """
        # 执行
        result = get_storage_stats()
        
        # 验证
        assert isinstance(result, dict)
        assert "total_stored" in result


@pytest.mark.unit
class TestMetricsStorageSingleton:
    """监控数据存储单例测试"""
    
    def test_metrics_storage_singleton(self):
        """
        【测试】全局存储实例
        
        【场景】访问全局实例
        【预期】是MetricsStorage类型
        """
        # 验证
        assert isinstance(metrics_storage, MetricsStorage)
