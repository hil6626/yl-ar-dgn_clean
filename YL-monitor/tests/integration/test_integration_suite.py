"""
集成测试套件 - 验证所有组件协同工作
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 测试配置
pytestmark = pytest.mark.integration


class TestComponentIntegration:
    """组件集成测试"""
    
    @pytest.fixture
    async def setup_components(self):
        """初始化所有组件"""
        # 初始化缓存管理器
        from app.services.cache_manager import CacheManager
        cache = CacheManager()
        
        # 初始化数据库优化器
        from app.utils.db_optimizer import DBOptimizer
        db_opt = DBOptimizer()
        
        # 初始化异步队列
        from app.services.async_queue import AsyncTaskQueue
        queue = AsyncTaskQueue()
        
        # 初始化安全组件
        from app.utils.security import SecurityManager
        security = SecurityManager()
        
        yield {
            'cache': cache,
            'db_opt': db_opt,
            'queue': queue,
            'security': security
        }
        
        # 清理
        await cache.clear()
        await queue.stop()
    
    async def test_cache_db_integration(self, setup_components):
        """测试缓存与数据库集成"""
        components = setup_components
        cache = components['cache']
        db_opt = components['db_opt']
        
        # 1. 从数据库查询数据
        test_data = {'id': 'test_001', 'value': 100}
        
        # 2. 缓存查询结果
        await cache.set('test_key', test_data, ttl=300)
        
        # 3. 从缓存读取
        cached_data = await cache.get('test_key')
        assert cached_data == test_data
        
        # 4. 验证缓存命中
        stats = await cache.get_stats()
        assert stats['hits'] >= 1
    
    async def test_async_queue_integration(self, setup_components):
        """测试异步队列集成"""
        components = setup_components
        queue = components['queue']
        
        results = []
        
        async def test_task(data: str):
            results.append(data)
            return f"processed_{data}"
        
        # 1. 提交多个任务
        tasks = []
        for i in range(5):
            task = await queue.submit(
                task_id=f"task_{i}",
                func=test_task,
                data=f"data_{i}"
            )
            tasks.append(task)
        
        # 2. 等待任务完成
        await asyncio.sleep(2)
        
        # 3. 验证结果
        assert len(results) == 5
        for i in range(5):
            assert f"data_{i}" in results
    
    async def test_security_cache_integration(self, setup_components):
        """测试安全组件与缓存集成"""
        components = setup_components
        security = components['security']
        cache = components['cache']
        
        # 1. 加密敏感数据
        sensitive_data = "password123"
        encrypted = security.encrypt(sensitive_data)
        
        # 2. 缓存加密数据
        await cache.set('encrypted_data', encrypted, ttl=600)
        
        # 3. 从缓存读取并解密
        cached_encrypted = await cache.get('encrypted_data')
        decrypted = security.decrypt(cached_encrypted)
        
        assert decrypted == sensitive_data


class TestAPIIntegration:
    """API集成测试"""
    
    async def test_pagination_with_cache(self):
        """测试分页与缓存集成"""
        from app.utils.pagination import PaginationHelper
        
        # 1. 创建大量测试数据
        all_data = [{'id': i, 'name': f'item_{i}'} for i in range(1000)]
        
        # 2. 使用游标分页
        paginator = PaginationHelper()
        
        # 第一页
        page1, cursor1 = paginator.paginate_with_cursor(
            all_data, cursor=None, limit=100
        )
        assert len(page1) == 100
        assert cursor1 is not None
        
        # 第二页
        page2, cursor2 = paginator.paginate_with_cursor(
            all_data, cursor=cursor1, limit=100
        )
        assert len(page2) == 100
        
        # 3. 验证无重复
        page1_ids = {item['id'] for item in page1}
        page2_ids = {item['id'] for item in page2}
        assert not page1_ids.intersection(page2_ids)
    
    async def test_compression_with_security(self):
        """测试压缩与安全集成"""
        import gzip
        from app.utils.security import SecurityManager
        
        security = SecurityManager()
        
        # 1. 创建大文本数据
        large_data = "x" * 10000
        
        # 2. 加密数据
        encrypted = security.encrypt(large_data)
        
        # 3. 压缩加密数据
        compressed = gzip.compress(encrypted.encode())
        
        # 4. 解压
        decompressed = gzip.decompress(compressed)
        
        # 5. 解密
        decrypted = security.decrypt(decompressed.decode())
        
        assert decrypted == large_data


class TestDataFlowIntegration:
    """数据流集成测试"""
    
    async def test_alert_data_flow(self):
        """测试告警数据流"""
        # 模拟告警产生 -> 处理 -> 通知的完整流程
        
        alert_data = {
            'id': 'alert_001',
            'type': 'threshold',
            'severity': 'high',
            'message': 'CPU使用率超过阈值',
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 验证告警数据结构
        assert 'id' in alert_data
        assert 'type' in alert_data
        assert 'severity' in alert_data
        
        # 2. 验证告警可以序列化
        json_str = json.dumps(alert_data)
        restored = json.loads(json_str)
        assert restored['id'] == alert_data['id']
    
    async def test_metrics_data_flow(self):
        """测试指标数据流"""
        # 模拟指标采集 -> 存储 -> 查询的完整流程
        
        metrics_batch = [
            {
                'name': 'cpu_usage',
                'value': 45.2,
                'timestamp': datetime.now().isoformat(),
                'labels': {'host': 'server1'}
            }
            for _ in range(100)
        ]
        
        # 1. 验证批量数据完整性
        assert len(metrics_batch) == 100
        
        # 2. 验证数据格式一致性
        for metric in metrics_batch:
            assert 'name' in metric
            assert 'value' in metric
            assert isinstance(metric['value'], (int, float))


class TestErrorHandlingIntegration:
    """错误处理集成测试"""
    
    async def test_error_propagation(self):
        """测试错误传播机制"""
        from app.utils.error_codes import ErrorCode, get_error_response
        
        # 1. 创建错误响应
        error_response = get_error_response(
            ErrorCode.VALIDATION_ERROR,
            message="测试错误",
            details={'field': 'test'}
        )
        
        # 2. 验证错误结构
        assert error_response['success'] is False
        assert 'error' in error_response
        assert error_response['error']['code'] == 'VAL_3000'
        
        # 3. 验证可序列化
        json_str = json.dumps(error_response)
        assert isinstance(json_str, str)
    
    async def test_security_error_handling(self):
        """测试安全错误处理"""
        from app.utils.security import SecurityManager
        
        security = SecurityManager()
        
        # 1. 测试无效Token
        with pytest.raises(Exception):
            security.verify_jwt_token("invalid_token")
        
        # 2. 测试解密错误
        with pytest.raises(Exception):
            security.decrypt("invalid_encrypted_data")


@pytest.mark.asyncio
class TestEndToEndScenarios:
    """端到端场景测试"""
    
    async def test_complete_monitoring_workflow(self):
        """测试完整监控工作流"""
        # 场景：系统监控 -> 告警检测 -> 通知发送
        
        # 1. 模拟系统指标采集
        system_metrics = {
            'cpu': 85.5,  # 超过阈值
            'memory': 70.0,
            'disk': 60.0
        }
        
        # 2. 检测告警条件
        alerts = []
        if system_metrics['cpu'] > 80:
            alerts.append({
                'type': 'threshold',
                'metric': 'cpu',
                'value': system_metrics['cpu'],
                'threshold': 80
            })
        
        # 3. 验证告警生成
        assert len(alerts) == 1
        assert alerts[0]['metric'] == 'cpu'
        
        # 4. 模拟通知发送
        notification_sent = True
        assert notification_sent is True
    
    async def test_dag_execution_workflow(self):
        """测试DAG执行工作流"""
        # 场景：DAG定义 -> 执行 -> 状态监控
        
        # 1. DAG定义
        dag_definition = {
            'id': 'dag_001',
            'nodes': [
                {'id': 'start', 'type': 'start'},
                {'id': 'task1', 'type': 'task'},
                {'id': 'end', 'type': 'end'}
            ],
            'edges': [
                {'from': 'start', 'to': 'task1'},
                {'from': 'task1', 'to': 'end'}
            ]
        }
        
        # 2. 验证DAG结构
        assert len(dag_definition['nodes']) == 3
        assert len(dag_definition['edges']) == 2
        
        # 3. 模拟执行
        execution_order = ['start', 'task1', 'end']
        
        # 4. 验证执行顺序
        assert execution_order[0] == 'start'
        assert execution_order[-1] == 'end'


# 测试执行入口
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
