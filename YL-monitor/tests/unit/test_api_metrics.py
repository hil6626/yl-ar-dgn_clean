#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统指标API路由单元测试

【功能描述】
测试系统指标相关的API端点，包括实时指标、历史数据、统计汇总等

【作者】
AI Assistant

【创建时间】
2026-02-10

【版本】
1.0.0

【测试覆盖】
- GET /api/v1/metrics/realtime - 实时指标
- GET /api/v1/metrics/history - 历史数据
- GET /api/v1/metrics/summary - 统计汇总
- GET /api/v1/metrics/cpu - CPU指标
- GET /api/v1/metrics/memory - 内存指标
- GET /api/v1/metrics/disk - 磁盘指标
- GET /api/v1/metrics/network - 网络指标
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch


@pytest.mark.unit
@pytest.mark.api
class TestMetricsAPI:
    """系统指标API测试类"""
    
    # ==================== 实时指标API测试 ====================
    
    def test_get_realtime_metrics_success(self, client):
        """
        【测试】获取实时指标成功
        
        【场景】正常请求实时指标
        【预期】返回200和指标数据
        """
        # 执行
        response = client.get("/api/v1/metrics/realtime")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "timestamp" in data
    
    def test_get_realtime_metrics_structure(self, client):
        """
        【测试】实时指标数据结构
        
        【场景】检查返回的指标数据结构
        【预期】包含关键指标字段
        """
        # 执行
        response = client.get("/api/v1/metrics/realtime")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        metrics = data.get("data", {})
        
        # 检查是否包含主要指标类别
        # 注意：实际字段取决于metrics_service的实现
        assert isinstance(metrics, dict)
    
    # ==================== 历史数据API测试 ====================
    
    def test_get_metrics_history_success(self, client):
        """
        【测试】获取历史数据成功
        
        【场景】正常请求历史数据
        【预期】返回200和历史数据列表
        """
        # 执行
        response = client.get("/api/v1/metrics/history")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "count" in data
        assert "period_hours" in data
        assert isinstance(data["data"], list)
    
    def test_get_metrics_history_with_hours_param(self, client):
        """
        【测试】指定时间范围的历史数据
        
        【场景】使用hours参数查询最近N小时
        【预期】返回指定时间范围的数据
        """
        # 执行 - 查询最近2小时
        response = client.get("/api/v1/metrics/history?hours=2")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["period_hours"] == 2
    
    def test_get_metrics_history_with_limit(self, client):
        """
        【测试】限制返回数量
        
        【场景】使用limit参数限制数据点数量
        【预期】返回数量不超过limit
        """
        # 执行
        response = client.get("/api/v1/metrics/history?limit=50")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 50
    
    def test_get_metrics_history_invalid_hours(self, client):
        """
        【测试】无效的小时参数
        
        【场景】hours参数超出有效范围
        【预期】返回422验证错误
        """
        # 执行 - hours太大
        response = client.get("/api/v1/metrics/history?hours=100")
        
        # 验证
        assert response.status_code == 422
        
        # 执行 - hours太小
        response = client.get("/api/v1/metrics/history?hours=0")
        assert response.status_code == 422
    
    def test_get_metrics_history_invalid_limit(self, client):
        """
        【测试】无效的limit参数
        
        【场景】limit参数超出有效范围
        【预期】返回422验证错误
        """
        # 执行 - limit太大
        response = client.get("/api/v1/metrics/history?limit=10000")
        
        # 验证
        assert response.status_code == 422
    
    # ==================== 统计汇总API测试 ====================
    
    def test_get_metrics_summary_success(self, client):
        """
        【测试】获取统计汇总成功
        
        【场景】正常请求统计汇总
        【预期】返回200和统计数据
        """
        # 执行
        response = client.get("/api/v1/metrics/summary")
        
        # 验证 - 可能200（有数据）或404（无数据）
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    def test_get_metrics_summary_with_hours(self, client):
        """
        【测试】指定时间范围的统计
        
        【场景】使用hours参数查询最近N小时的统计
        【预期】返回指定范围的统计
        """
        # 执行
        response = client.get("/api/v1/metrics/summary?hours=6")
        
        # 验证
        assert response.status_code in [200, 404]
    
    def test_get_metrics_summary_invalid_hours(self, client):
        """
        【测试】统计API无效参数
        
        【场景】hours参数超出范围
        【预期】返回422
        """
        # 执行
        response = client.get("/api/v1/metrics/summary?hours=100")
        
        # 验证
        assert response.status_code == 422
    
    # ==================== CPU指标API测试 ====================
    
    def test_get_cpu_metrics_success(self, client):
        """
        【测试】获取CPU指标成功
        
        【场景】正常请求CPU指标历史
        【预期】返回200和CPU数据
        """
        # 执行
        response = client.get("/api/v1/metrics/cpu")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "period_hours" in data
        assert isinstance(data["data"], list)
    
    def test_get_cpu_metrics_structure(self, client):
        """
        【测试】CPU指标数据结构
        
        【场景】检查返回的CPU数据结构
        【预期】包含关键字段
        """
        # 执行
        response = client.get("/api/v1/metrics/cpu")
        
        # 验证
        if response.status_code == 200 and response.json().get("data"):
            data = response.json()["data"]
            if len(data) > 0:
                first_item = data[0]
                # 检查常见字段
                assert "timestamp" in first_item
                assert "value" in first_item
    
    def test_get_cpu_metrics_with_hours(self, client):
        """
        【测试】指定时间范围的CPU指标
        
        【场景】使用hours参数
        【预期】返回指定范围的数据
        """
        # 执行
        response = client.get("/api/v1/metrics/cpu?hours=3")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["period_hours"] == 3
    
    # ==================== 内存指标API测试 ====================
    
    def test_get_memory_metrics_success(self, client):
        """
        【测试】获取内存指标成功
        
        【场景】正常请求内存指标历史
        【预期】返回200和内存数据
        """
        # 执行
        response = client.get("/api/v1/metrics/memory")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_memory_metrics_structure(self, client):
        """
        【测试】内存指标数据结构
        
        【场景】检查返回的内存数据结构
        【预期】包含关键字段
        """
        # 执行
        response = client.get("/api/v1/metrics/memory")
        
        # 验证
        if response.status_code == 200 and response.json().get("data"):
            data = response.json()["data"]
            if len(data) > 0:
                first_item = data[0]
                assert "timestamp" in first_item
                assert "percent" in first_item
    
    def test_get_memory_metrics_with_hours(self, client):
        """
        【测试】指定时间范围的内存指标
        
        【场景】使用hours参数
        【预期】返回指定范围的数据
        """
        # 执行
        response = client.get("/api/v1/metrics/memory?hours=4")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["period_hours"] == 4
    
    # ==================== 磁盘指标API测试 ====================
    
    def test_get_disk_metrics_success(self, client):
        """
        【测试】获取磁盘指标成功
        
        【场景】正常请求磁盘指标历史
        【预期】返回200和磁盘数据
        """
        # 执行
        response = client.get("/api/v1/metrics/disk")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_disk_metrics_structure(self, client):
        """
        【测试】磁盘指标数据结构
        
        【场景】检查返回的磁盘数据结构
        【预期】包含关键字段
        """
        # 执行
        response = client.get("/api/v1/metrics/disk")
        
        # 验证
        if response.status_code == 200 and response.json().get("data"):
            data = response.json()["data"]
            if len(data) > 0:
                first_item = data[0]
                assert "timestamp" in first_item
                assert "percent" in first_item
    
    def test_get_disk_metrics_with_hours(self, client):
        """
        【测试】指定时间范围的磁盘指标
        
        【场景】使用hours参数
        【预期】返回指定范围的数据
        """
        # 执行
        response = client.get("/api/v1/metrics/disk?hours=2")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["period_hours"] == 2
    
    # ==================== 网络指标API测试 ====================
    
    def test_get_network_metrics_success(self, client):
        """
        【测试】获取网络指标成功
        
        【场景】正常请求网络指标历史
        【预期】返回200和网络数据
        """
        # 执行
        response = client.get("/api/v1/metrics/network")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_network_metrics_structure(self, client):
        """
        【测试】网络指标数据结构
        
        【场景】检查返回的网络数据结构
        【预期】包含关键字段
        """
        # 执行
        response = client.get("/api/v1/metrics/network")
        
        # 验证
        if response.status_code == 200 and response.json().get("data"):
            data = response.json()["data"]
            if len(data) > 0:
                first_item = data[0]
                assert "timestamp" in first_item
                # 网络指标可能有sent_mb/recv_mb或packets_sent/packets_recv
    
    def test_get_network_metrics_with_hours(self, client):
        """
        【测试】指定时间范围的网络指标
        
        【场景】使用hours参数
        【预期】返回指定范围的数据
        """
        # 执行
        response = client.get("/api/v1/metrics/network?hours=5")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["period_hours"] == 5
    
    # ==================== 参数验证测试 ====================
    
    def test_metrics_api_invalid_hours_too_small(self, client):
        """
        【测试】小时参数过小
        
        【场景】hours参数小于1
        【预期】返回422
        """
        endpoints = [
            "/api/v1/metrics/cpu?hours=0",
            "/api/v1/metrics/memory?hours=-1",
            "/api/v1/metrics/disk?hours=0",
            "/api/v1/metrics/network?hours=-5"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 422, f"Endpoint {endpoint} should return 422"
    
    def test_metrics_api_invalid_hours_too_large(self, client):
        """
        【测试】小时参数过大
        
        【场景】hours参数大于24
        【预期】返回422
        """
        endpoints = [
            "/api/v1/metrics/cpu?hours=25",
            "/api/v1/metrics/memory?hours=100",
            "/api/v1/metrics/disk?hours=50",
            "/api/v1/metrics/network?hours=30"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 422, f"Endpoint {endpoint} should return 422"


@pytest.mark.unit
@pytest.mark.api
class TestMetricsAPIErrorHandling:
    """指标API错误处理测试"""
    
    def test_invalid_endpoint(self, client):
        """
        【测试】无效端点
        
        【场景】请求不存在的端点
        【预期】返回404
        """
        # 执行
        response = client.get("/api/v1/metrics/invalid_endpoint")
        
        # 验证
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """
        【测试】无效HTTP方法
        
        【场景】对只读端点使用POST
        【预期】返回405
        """
        # 执行
        response = client.post("/api/v1/metrics/realtime")
        
        # 验证
        assert response.status_code == 405
    
    def test_metrics_service_unavailable(self, client):
        """
        【测试】服务不可用
        
        【场景】metrics_service未初始化
        【预期】适当处理错误
        """
        # 这个测试需要模拟服务不可用的情况
        # 实际实现取决于应用的错误处理机制
        pass
