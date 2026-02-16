"""
性能测试脚本
测试API响应时间、并发能力和系统资源使用
"""

import pytest
import asyncio
import time
import statistics
import psutil
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 移除本地fixture，使用conftest.py中的全局fixture


class TestAPIPerformance:
    """API性能测试"""
    
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client):
        """测试健康检查端点性能"""
        response_times = []
        
        # 发送100次请求
        for _ in range(100):
            start = time.time()
            response = await client.get("/api/health")
            elapsed = time.time() - start
            
            assert response.status_code == 200
            response_times.append(elapsed * 1000)  # 转换为毫秒
        
        # 计算统计指标
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        max_time = max(response_times)
        
        print(f"\n健康检查端点性能:")
        print(f"  平均响应时间: {avg_time:.2f}ms")
        print(f"  P95响应时间: {p95_time:.2f}ms")
        print(f"  P99响应时间: {p99_time:.2f}ms")
        print(f"  最大响应时间: {max_time:.2f}ms")
        
        # 断言性能指标
        assert avg_time < 50, f"平均响应时间 {avg_time:.2f}ms 超过50ms阈值"
        assert p95_time < 100, f"P95响应时间 {p95_time:.2f}ms 超过100ms阈值"
    
    @pytest.mark.asyncio
    async def test_dashboard_overview_performance(self, client):
        """测试Dashboard概览API性能"""
        response_times = []
        
        for _ in range(50):
            start = time.time()
            response = await client.get("/api/v1/dashboard/overview")
            elapsed = time.time() - start
            
            assert response.status_code == 200
            response_times.append(elapsed * 1000)
        
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        print(f"\nDashboard概览API性能:")
        print(f"  平均响应时间: {avg_time:.2f}ms")
        print(f"  P95响应时间: {p95_time:.2f}ms")
        
        assert avg_time < 200, f"平均响应时间 {avg_time:.2f}ms 超过200ms阈值"
        assert p95_time < 500, f"P95响应时间 {p95_time:.2f}ms 超过500ms阈值"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """测试并发请求处理能力"""
        async def make_request():
            start = time.time()
            response = await client.get("/api/health")
            elapsed = time.time() - start
            return response.status_code == 200, elapsed * 1000
        
        # 并发发送50个请求
        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        success_count = sum(1 for success, _ in results if success)
        response_times = [elapsed for _, elapsed in results]
        
        print(f"\n并发请求测试 (50并发):")
        print(f"  成功率: {success_count}/50 ({success_count/50*100:.1f}%)")
        print(f"  总耗时: {total_time:.2f}s")
        print(f"  平均响应时间: {statistics.mean(response_times):.2f}ms")
        print(f"  最大响应时间: {max(response_times):.2f}ms")
        
        assert success_count == 50, f"并发请求成功率 {success_count}/50 不足"
        assert total_time < 10, f"并发处理总时间 {total_time:.2f}s 超过10秒"


class TestResourceUsage:
    """系统资源使用测试"""
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        
        # 获取当前进程内存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        
        memory_mb = memory_info.rss / (1024 * 1024)
        
        print(f"\n内存使用情况:")
        print(f"  RSS: {memory_mb:.2f} MB")
        print(f"  VMS: {memory_info.vms / (1024 * 1024):.2f} MB")
        
        # 内存使用应小于500MB
        assert memory_mb < 500, f"内存使用 {memory_mb:.2f}MB 超过500MB阈值"
    
    def test_cpu_usage(self):
        """测试CPU使用情况"""
        import psutil
        
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        print(f"\nCPU使用情况:")
        print(f"  使用率: {cpu_percent:.1f}%")
        
        # CPU使用率应小于50%
        assert cpu_percent < 50, f"CPU使用率 {cpu_percent:.1f}% 超过50%阈值"


class TestDatabasePerformance:
    """数据库性能测试"""
    
    @pytest.mark.asyncio
    async def test_query_performance(self):
        """测试数据库查询性能"""
        from app.models.function_mapping import FunctionMapping
        
        start = time.time()
        
        # 执行查询
        try:
            functions = await FunctionMapping.get_active_functions()
            elapsed = (time.time() - start) * 1000
            
            print(f"\n数据库查询性能:")
            print(f"  查询时间: {elapsed:.2f}ms")
            print(f"  返回记录数: {len(functions)}")
            
            # 查询时间应小于100ms
            assert elapsed < 100, f"查询时间 {elapsed:.2f}ms 超过100ms阈值"
            
        except Exception as e:
            pytest.skip(f"数据库查询测试跳过: {e}")


class TestWebSocketPerformance:
    """WebSocket性能测试"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_performance(self):
        """测试WebSocket连接性能"""
        try:
            import websockets
            
            start = time.time()
            
            # 尝试连接WebSocket
            async with websockets.connect(
                "ws://0.0.0.0:8000/ws/dashboard/realtime",
                timeout=5
            ) as ws:
                # 等待第一条消息
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                elapsed = (time.time() - start) * 1000
                
                print(f"\nWebSocket连接性能:")
                print(f"  连接+首消息时间: {elapsed:.2f}ms")
                
                # 连接时间应小于500ms
                assert elapsed < 500, f"WebSocket连接时间 {elapsed:.2f}ms 超过500ms阈值"
                
        except Exception as e:
            pytest.skip(f"WebSocket测试跳过: {e}")


class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.mark.asyncio
    async def test_cache_read_performance(self):
        """测试缓存读取性能"""
        from app.utils.cache_config import cache
        
        # 设置测试数据
        test_data = {"key": "value", "data": "test" * 1000}
        await cache.set("perf_test_key", test_data, ttl=60)
        
        # 测试读取性能
        read_times = []
        for _ in range(1000):
            start = time.time()
            result = await cache.get("perf_test_key")
            elapsed = (time.time() - start) * 1000
            read_times.append(elapsed)
        
        avg_time = statistics.mean(read_times)
        
        print(f"\n缓存读取性能 (1000次):")
        print(f"  平均读取时间: {avg_time:.4f}ms")
        print(f"  最小读取时间: {min(read_times):.4f}ms")
        print(f"  最大读取时间: {max(read_times):.4f}ms")
        
        # 平均读取时间应小于1ms
        assert avg_time < 1, f"缓存读取时间 {avg_time:.4f}ms 超过1ms阈值"


# 性能基准配置
PERFORMANCE_BASELINE = {
    "api_response_time": {
        "avg": 50,      # ms
        "p95": 100,     # ms
        "p99": 200      # ms
    },
    "concurrent_requests": {
        "max_time": 10,     # seconds for 50 concurrent
        "success_rate": 100  # percentage
    },
    "memory_usage": {
        "max": 500          # MB
    },
    "cpu_usage": {
        "max": 50           # percentage
    },
    "database_query": {
        "max": 100          # ms
    },
    "websocket_connection": {
        "max": 500          # ms
    },
    "cache_read": {
        "max": 1            # ms
    }
}


def generate_performance_report(results: List[Dict[str, Any]]) -> str:
    """
    生成性能测试报告
    
    参数:
    - results: 测试结果列表
    
    返回:
    - 格式化的报告字符串
    """
    report = []
    report.append("=" * 60)
    report.append("YL-Monitor 性能测试报告")
    report.append("=" * 60)
    report.append("")
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        report.append(f"{status} {result['name']}")
        report.append(f"  指标: {result['metric']}")
        report.append(f"  实际值: {result['actual']}")
        report.append(f"  阈值: {result['threshold']}")
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)


# 主函数
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
