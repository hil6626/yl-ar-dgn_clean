"""
API集成测试
测试所有API端点的完整流程
"""

import pytest
import asyncio
from httpx import AsyncClient
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app


# 移除本地fixture，使用conftest.py中的全局fixture


class TestHealthCheck:
    """健康检查测试"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestDashboardAPI:
    """Dashboard API测试"""
    
    @pytest.mark.asyncio
    async def test_get_overview(self, client):
        """测试获取概览统计"""
        response = await client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "api" in data
        assert "nodes" in data
        assert "scripts" in data
        assert "completion" in data
        
        # 验证数据结构
        assert "total" in data["api"]
        assert "healthy" in data["api"]
        assert "error" in data["api"]
    
    @pytest.mark.asyncio
    async def test_get_function_matrix(self, client):
        """测试获取功能矩阵"""
        response = await client.get("/api/v1/dashboard/function-matrix")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # 验证第一条数据的结构
            first_item = data[0]
            assert "id" in first_item
            assert "name" in first_item
            assert "completion" in first_item
    
    @pytest.mark.asyncio
    async def test_get_system_resources(self, client):
        """测试获取系统资源"""
        response = await client.get("/api/v1/system/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        
        # 验证数值范围
        assert 0 <= data["cpu"] <= 100
        assert 0 <= data["memory"] <= 100
        assert 0 <= data["disk"] <= 100


class TestAPIDocAPI:
    """API Doc API测试"""
    
    @pytest.mark.asyncio
    async def test_get_validation_matrix(self, client):
        """测试获取验证矩阵"""
        response = await client.get("/api/v1/api-doc/validation-matrix")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_bubble_check(self, client):
        """测试冒泡检测"""
        # 测试存在的功能
        response = await client.get("/api/v1/api-doc/bubble-check/alert-management")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "color" in data
    
    @pytest.mark.asyncio
    async def test_get_api_doc_stats(self, client):
        """测试获取API文档统计"""
        response = await client.get("/api/v1/api-doc/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_functions" in data
        assert "completed_functions" in data
        assert "completion_rate" in data


class TestDAGAPI:
    """DAG API测试"""
    
    @pytest.mark.asyncio
    async def test_get_dag_definition(self, client):
        """测试获取DAG定义"""
        response = await client.get("/api/v1/dag/definition")
        assert response.status_code == 200
        
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
    
    @pytest.mark.asyncio
    async def test_execute_dag(self, client):
        """测试执行DAG"""
        response = await client.post("/api/v1/dag/execute")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "execution_id" in data
    
    @pytest.mark.asyncio
    async def test_execute_node(self, client):
        """测试执行节点"""
        # 使用示例节点ID
        response = await client.post("/api/v1/dag/nodes/node-1/execute")
        # 可能成功或失败，但应该返回200或404
        assert response.status_code in [200, 404]


class TestScriptsAPI:
    """Scripts API测试"""
    
    @pytest.mark.asyncio
    async def test_get_scripts(self, client):
        """测试获取脚本列表"""
        response = await client.get("/api/v1/scripts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # 验证脚本数据结构
            script = data[0]
            assert "id" in script
            assert "name" in script
            assert "description" in script
            assert "category" in script
            assert "status" in script
    
    @pytest.mark.asyncio
    async def test_execute_script(self, client):
        """测试执行脚本"""
        # 使用示例脚本ID
        response = await client.post("/api/v1/scripts/cpu-monitor/execute")
        # 可能成功或失败，但应该返回200或500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "output" in data
    
    @pytest.mark.asyncio
    async def test_set_polling_config(self, client):
        """测试设置轮询配置"""
        config = {
            "enabled": True,
            "interval": 300
        }
        
        response = await client.post(
            "/api/v1/scripts/cpu-monitor/polling",
            json=config
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_get_script_logs(self, client):
        """测试获取脚本日志"""
        response = await client.get("/api/v1/scripts/cpu-monitor/logs?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_404_error(self, client):
        """测试404错误"""
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invalid_script_id(self, client):
        """测试无效脚本ID"""
        response = await client.post("/api/v1/scripts/invalid-id/execute")
        # 应该返回500错误
        assert response.status_code in [404, 500]


# ============================================================================
# 性能测试
# ============================================================================
class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_api_response_time(self, client):
        """测试API响应时间"""
        import time
        
        start = time.time()
        response = await client.get("/api/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # 响应时间应小于1秒
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """测试并发请求"""
        async def make_request():
            response = await client.get("/api/health")
            return response.status_code == 200
        
        # 并发发送10个请求
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # 所有请求都应该成功
        assert all(results)


# ============================================================================
# 主函数
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
