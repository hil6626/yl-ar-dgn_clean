#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API性能测试

【功能描述】
测试API的性能指标，包括响应时间、吞吐量、并发处理能力

【作者】
AI Assistant

【创建时间】
2026-02-10

【版本】
1.0.0

【测试覆盖】
- API响应时间测试（P95 < 500ms）
- API吞吐量测试（>= 50 req/s）
- 并发请求测试
- 长时间稳定性测试
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


@pytest.mark.performance
class TestAPIPerformance:
    """API性能测试类"""
    
    # ==================== 响应时间测试 ====================
    
    def test_api_response_time_alerts_list(self, client, performance_thresholds):
        """
        【性能测试】告警列表API响应时间
        
        【场景】单次请求告警列表
        【预期】响应时间 < 500ms
        """
        # 执行
        start_time = time.time()
        response = client.get("/api/v1/alerts/rules")
        end_time = time.time()
        
        # 验证
        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000
        threshold = performance_thresholds["api_p95_ms"]
        
        assert response_time_ms < threshold, \
            f"响应时间 {response_time_ms:.2f}ms 超过阈值 {threshold}ms"
    
    def test_api_response_time_metrics_realtime(self, client, performance_thresholds):
        """
        【性能测试】实时指标API响应时间
        
        【场景】单次请求实时指标
        【预期】响应时间 < 500ms
        """
        # 执行
        start_time = time.time()
        response = client.get("/api/v1/metrics/realtime")
        end_time = time.time()
        
        # 验证
        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000
        threshold = performance_thresholds["api_p95_ms"]
        
        assert response_time_ms < threshold, \
            f"响应时间 {response_time_ms:.2f}ms 超过阈值 {threshold}ms"
    
    def test_api_response_time_p95_multiple_requests(self, client, performance_thresholds):
        """
        【性能测试】多次请求P95响应时间
        
        【场景】连续发送100次请求
        【预期】P95响应时间 < 500ms
        """
        # 准备
        request_count = 100
        response_times = []
        
        # 执行
        for i in range(request_count):
            start_time = time.time()
            response = client.get("/api/v1/alerts/rules")
            end_time = time.time()
            
            if response.status_code == 200:
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
        
        # 计算P95
        if len(response_times) > 0:
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95) - 1
            p95_index = max(0, p95_index)
            p95_time = sorted_times[p95_index]
            
            threshold = performance_thresholds["api_p95_ms"]
            assert p95_time < threshold, \
                f"P95响应时间 {p95_time:.2f}ms 超过阈值 {threshold}ms"
            
            # 输出统计信息
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            print(f"\n响应时间统计: 平均={avg_time:.2f}ms, 最小={min_time:.2f}ms, 最大={max_time:.2f}ms, P95={p95_time:.2f}ms")
    
    # ==================== 吞吐量测试 ====================
    
    def test_api_throughput_alerts_list(self, client, performance_thresholds, test_config):
        """
        【性能测试】告警列表API吞吐量
        
        【场景】在指定时间内发送尽可能多的请求
        【预期】吞吐量 >= 50 req/s
        """
        # 准备
        duration = test_config["performance_test_duration"]  # 5秒
        start_time = time.time()
        request_count = 0
        
        # 执行
        while (time.time() - start_time) < duration:
            response = client.get("/api/v1/alerts/rules")
            if response.status_code == 200:
                request_count += 1
        
        # 计算吞吐量
        elapsed_time = time.time() - start_time
        throughput = request_count / elapsed_time
        
        # 验证
        threshold = performance_thresholds["api_throughput_rps"]
        assert throughput >= threshold, \
            f"吞吐量 {throughput:.2f} req/s 低于阈值 {threshold} req/s"
        
        print(f"\n吞吐量: {throughput:.2f} req/s ({request_count} 请求 / {elapsed_time:.2f} 秒)")
    
    # ==================== 并发测试 ====================
    
    def test_api_concurrent_requests_alerts(self, client, test_config):
        """
        【性能测试】并发请求测试 - 告警API
        
        【场景】同时发送多个并发请求
        【预期】所有请求都成功
        """
        # 准备
        concurrent_users = 20
        
        # 执行
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(client.get, "/api/v1/alerts/rules")
                for _ in range(concurrent_users)
            ]
            
            # 收集结果
            results = []
            for future in as_completed(futures):
                try:
                    response = future.result()
                    results.append(response.status_code)
                except Exception as e:
                    results.append(f"error: {e}")
        
        # 验证
        success_count = results.count(200)
        assert success_count == concurrent_users, \
            f"只有 {success_count}/{concurrent_users} 个并发请求成功"
    
    def test_api_concurrent_requests_metrics(self, client, test_config):
        """
        【性能测试】并发请求测试 - 指标API
        
        【场景】同时发送多个并发请求
        【预期】所有请求都成功
        """
        # 准备
        concurrent_users = 20
        
        # 执行
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(client.get, "/api/v1/metrics/realtime")
                for _ in range(concurrent_users)
            ]
            
            # 收集结果
            results = []
            for future in as_completed(futures):
                try:
                    response = future.result()
                    results.append(response.status_code)
                except Exception as e:
                    results.append(f"error: {e}")
        
        # 验证
        success_count = results.count(200)
        assert success_count == concurrent_users, \
            f"只有 {success_count}/{concurrent_users} 个并发请求成功"
    
    # ==================== 稳定性测试 ====================
    
    def test_api_stability_alerts_list(self, client):
        """
        【性能测试】API稳定性测试
        
        【场景】连续发送请求，检查稳定性
        【预期】无错误，响应时间稳定
        """
        # 准备
        request_count = 200
        response_times = []
        errors = []
        
        # 执行
        for i in range(request_count):
            start_time = time.time()
            try:
                response = client.get("/api/v1/alerts/rules")
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)
                else:
                    errors.append(f"Request {i}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"Request {i}: {str(e)}")
        
        # 验证
        error_rate = len(errors) / request_count * 100
        assert error_rate < 1, \
            f"错误率 {error_rate:.1f}% 超过 1%"
        
        if len(response_times) > 0:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            print(f"\n稳定性测试: {len(response_times)} 成功, {len(errors)} 失败")
            print(f"平均响应时间: {avg_time:.2f}ms, 最大响应时间: {max_time:.2f}ms")


@pytest.mark.performance
class TestAPIPerformanceComparison:
    """API性能对比测试"""
    
    def test_api_performance_comparison(self, client):
        """
        【性能测试】不同端点性能对比
        
        【场景】对比不同API端点的响应时间
        【预期】所有端点都满足性能要求
        """
        # 准备
        endpoints = {
            "告警列表": "/api/v1/alerts/rules",
            "实时指标": "/api/v1/metrics/realtime",
            "告警统计": "/api/v1/alerts/stats",
            "系统摘要": "/api/summary",
            "健康检查": "/api/health"
        }
        
        results = {}
        
        # 执行
        for name, endpoint in endpoints.items():
            times = []
            for _ in range(10):  # 每个端点测试10次
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                if response.status_code == 200:
                    times.append((end_time - start_time) * 1000)
            
            if times:
                results[name] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
        
        # 输出对比结果
        print("\nAPI性能对比:")
        print("-" * 60)
        for name, stats in results.items():
            print(f"{name:12s}: 平均={stats['avg']:6.2f}ms, 最小={stats['min']:6.2f}ms, 最大={stats['max']:6.2f}ms")
        print("-" * 60)
        
        # 验证所有端点平均响应时间 < 500ms
        for name, stats in results.items():
            assert stats["avg"] < 500, \
                f"{name} 平均响应时间 {stats['avg']:.2f}ms 超过 500ms"
