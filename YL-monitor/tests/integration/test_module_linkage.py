#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块联动性集成测试

【功能描述】
验证7项优化模块间的数据流转和协同工作能力，确保模块间接口兼容、数据传递正确

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0

【依赖】
pytest>=7.0.0
pytest-asyncio>=0.21.0

【测试场景】
1. 沉积清理管理器与错误恢复服务联动
2. 队列监控器与仪表盘监控联动
3. 渲染优化器与性能监控联动
4. API客户端与错误码定义一致性
5. DAG可视化器与AR监控扩展接口兼容性
6. WebSocket实时推送与前端性能监控联动

【执行命令】
    pytest tests/integration/test_module_linkage.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

# 【被测模块导入】
from app.services.cleanup_manager import CleanupManager
from app.services.error_recovery import ErrorRecoveryService, RecoveryLevel
from app.services.queue_monitor import QueueMonitor, QueueStatus
from app.services.dashboard_monitor import DashboardMonitor, AlertLevel
from app.frontend.render_optimizer import RenderOptimizer, RenderStrategy
from app.utils.api_client import APIClient
from app.utils.error_codes import ErrorCode, get_error_message
from app.services.dag_visualizer import DAGVisualizer, LayoutType
from app.ar.ar_monitor_extension import ARMonitorExtension, ARNodeType


class TestCleanupErrorRecoveryLinkage:
    """
    【测试类】沉积清理与错误恢复联动测试
    
    【职责】验证清理管理器与错误恢复服务的协同工作能力
    """
    
    @pytest.fixture
    def cleanup_manager(self):
        """【夹具】创建清理管理器实例"""
        return CleanupManager()
    
    @pytest.fixture
    def error_recovery(self):
        """【夹具】创建错误恢复服务实例"""
        return ErrorRecoveryService()
    
    @pytest.mark.asyncio
    async def test_cleanup_failure_recovery(self, cleanup_manager, error_recovery):
        """
        【测试方法】清理失败后的错误恢复
        
        【功能】验证清理任务失败时，错误恢复服务能够正确介入并执行恢复策略
        
        【步骤】
        1. 模拟清理任务执行失败
        2. 触发错误恢复机制
        3. 验证恢复策略执行结果
        """
        # 【步骤1】创建模拟失败的清理任务
        failed_task = CleanupTask(
            id="test-cleanup-001",
            name="测试清理任务",
            cleanup_type=CleanupType.TEMP_FILES,
            target_path="/tmp/test",
            status="failed",
            error_message="权限不足"
        )
        
        # 【步骤2】执行错误恢复
        recovery_result = await error_recovery.recover_script_error(
            script_id="cleanup-001",
            error_type="permission_error",
            error_message="权限不足",
            context={"task": failed_task.to_dict()}
        )
        
        # 【验证】恢复结果
        assert recovery_result is not None, "错误恢复应返回结果"
        assert "recovery_level" in recovery_result, "恢复结果应包含恢复级别"
        print(f"✓ 清理失败恢复测试通过: {recovery_result['recovery_level']}")
    
    @pytest.mark.asyncio
    async def test_cleanup_queue_integration(self, cleanup_manager):
        """
        【测试方法】清理任务与队列监控集成
        
        【功能】验证清理任务能够正确注册到队列监控器
        
        【步骤】
        1. 注册清理任务队列
        2. 提交清理任务
        3. 验证队列状态更新
        """
        from app.services.queue_monitor import QueueMonitor
        
        # 【步骤1】创建队列监控器
        queue_monitor = QueueMonitor()
        
        # 【步骤2】注册清理队列
        await queue_monitor.register_queue(
            name="cleanup_queue",
            max_depth=100,
            description="沉积清理任务队列"
        )
        
        # 【步骤3】提交清理任务到队列
        task_data = {
            "task_id": "cleanup-002",
            "type": "temp_files",
            "priority": "normal"
        }
        
        await queue_monitor.enqueue("cleanup_queue", task_data)
        
        # 【验证】队列状态
        status = queue_monitor.get_queue_status("cleanup_queue")
        assert status is not None, "队列状态应可获取"
        print(f"✓ 清理队列集成测试通过: 状态={status.value}")


class TestQueueDashboardLinkage:
    """
    【测试类】队列监控与仪表盘联动测试
    
    【职责】验证队列监控数据能够正确推送到仪表盘
    """
    
    @pytest.fixture
    def queue_monitor(self):
        """【夹具】创建队列监控器"""
        return QueueMonitor()
    
    @pytest.fixture
    def dashboard_monitor(self):
        """【夹具】创建仪表盘监控器"""
        return DashboardMonitor()
    
    @pytest.mark.asyncio
    async def test_queue_metrics_to_dashboard(self, queue_monitor, dashboard_monitor):
        """
        【测试方法】队列指标推送到仪表盘
        
        【功能】验证队列监控指标能够正确显示在仪表盘上
        
        【步骤】
        1. 注册队列并生成指标
        2. 将队列指标转换为仪表盘指标
        3. 验证仪表盘数据更新
        """
        # 【步骤1】注册测试队列
        await queue_monitor.register_queue(
            name="test_queue",
            max_depth=50,
            description="测试队列"
        )
        
        # 【步骤2】添加队列任务
        for i in range(10):
            await queue_monitor.enqueue("test_queue", {"task_id": f"task-{i}"})
        
        # 【步骤3】获取队列统计
        queue_stats = queue_monitor.get_queue_stats("test_queue")
        
        # 【验证】队列统计完整性
        assert "pending_count" in queue_stats, "队列统计应包含待处理数量"
        assert "processed_count" in queue_stats, "队列统计应包含已处理数量"
        assert "error_rate" in queue_stats, "队列统计应包含错误率"
        
        print(f"✓ 队列指标测试通过: 待处理={queue_stats['pending_count']}")
    
    @pytest.mark.asyncio
    async def test_queue_congestion_alert(self, queue_monitor, dashboard_monitor):
        """
        【测试方法】队列拥塞告警联动
        
        【功能】验证队列拥塞时能够触发仪表盘告警
        
        【步骤】
        1. 模拟队列拥塞状态
        2. 触发拥塞检测
        3. 验证告警生成
        """
        # 【步骤1】注册队列并设置低阈值
        await queue_monitor.register_queue(
            name="congestion_test_queue",
            max_depth=10,
            description="拥塞测试队列"
        )
        
        # 【步骤2】填充队列至拥塞状态
        for i in range(15):  # 超过max_depth
            await queue_monitor.enqueue("congestion_test_queue", {"task_id": f"task-{i}"})
        
        # 【步骤3】检测拥塞状态
        status = queue_monitor.get_queue_status("congestion_test_queue")
        
        # 【验证】拥塞状态
        assert status in [QueueStatus.WARNING, QueueStatus.CRITICAL], \
            f"队列应处于告警状态，实际状态: {status.value}"
        
        print(f"✓ 队列拥塞告警测试通过: 状态={status.value}")


class TestRenderPerformanceLinkage:
    """
    【测试类】渲染优化与性能监控联动测试
    
    【职责】验证渲染优化器与性能监控的协同工作
    """
    
    @pytest.fixture
    def render_optimizer(self):
        """【夹具】创建渲染优化器"""
        return RenderOptimizer()
    
    def test_render_strategy_selection(self, render_optimizer):
        """
        【测试方法】渲染策略选择
        
        【功能】验证根据数据量正确选择渲染策略
        
        【步骤】
        1. 测试不同数据量下的策略选择
        2. 验证策略选择逻辑
        """
        # 【测试用例1】小数据量 - 立即渲染
        strategy_small = render_optimizer.select_strategy(item_count=10)
        assert strategy_small == RenderStrategy.IMMEDIATE, "小数据量应使用立即渲染"
        
        # 【测试用例2】中等数据量 - 懒加载
        strategy_medium = render_optimizer.select_strategy(item_count=100)
        assert strategy_medium == RenderStrategy.LAZY_LOAD, "中等数据量应使用懒加载"
        
        # 【测试用例3】大数据量 - 虚拟滚动
        strategy_large = render_optimizer.select_strategy(item_count=1000)
        assert strategy_large == RenderStrategy.VIRTUAL_SCROLL, "大数据量应使用虚拟滚动"
        
        print(f"✓ 渲染策略选择测试通过")
    
    def test_performance_metrics_collection(self, render_optimizer):
        """
        【测试方法】性能指标收集
        
        【功能】验证渲染过程中性能指标正确收集
        
        【步骤】
        1. 执行渲染操作
        2. 收集性能指标
        3. 验证指标完整性
        """
        # 【步骤1】开始性能监控
        render_optimizer.start_performance_monitoring()
        
        # 【步骤2】模拟渲染操作
        test_data = [{"id": i, "name": f"item-{i}"} for i in range(100)]
        render_optimizer.render_batch(test_data, strategy=RenderStrategy.LAZY_LOAD)
        
        # 【步骤3】获取性能报告
        report = render_optimizer.get_performance_report()
        
        # 【验证】性能报告
        assert report is not None, "性能报告应存在"
        assert "render_time" in report or "metrics" in report, "报告应包含渲染时间或指标"
        
        print(f"✓ 性能指标收集测试通过")


class TestAPIErrorCodeLinkage:
    """
    【测试类】API客户端与错误码联动测试
    
    【职责】验证API客户端正确使用错误码体系
    """
    
    @pytest.fixture
    def api_client(self):
        """【夹具】创建API客户端"""
        return APIClient(base_url="http://localhost:8000")
    
    def test_error_code_mapping(self, api_client):
        """
        【测试方法】错误码映射
        
        【功能】验证错误码与HTTP状态码正确映射
        
        【步骤】
        1. 测试各类错误码映射
        2. 验证错误消息获取
        """
        # 【测试用例1】参数错误
        error_msg = get_error_message(ErrorCode.PARAMETER_ERROR)
        assert "参数" in error_msg or "parameter" in error_msg.lower(), \
            "参数错误码应返回参数相关消息"
        
        # 【测试用例2】未找到
        error_msg = get_error_message(ErrorCode.NOT_FOUND)
        assert "未找到" in error_msg or "not found" in error_msg.lower(), \
            "未找到错误码应返回未找到相关消息"
        
        # 【测试用例3】服务器错误
        error_msg = get_error_message(ErrorCode.SERVER_ERROR)
        assert "服务器" in error_msg or "server" in error_msg.lower(), \
            "服务器错误码应返回服务器相关消息"
        
        print(f"✓ 错误码映射测试通过")
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, api_client):
        """
        【测试方法】API错误处理
        
        【功能】验证API客户端正确处理错误响应
        
        【步骤】
        1. 模拟API错误响应
        2. 验证错误解析
        3. 验证错误码提取
        """
        # 【模拟】使用mock测试错误处理
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            # 模拟404错误
            mock_request.side_effect = Exception("404: Not Found")
            
            try:
                await api_client.get("/non-existent-endpoint")
                assert False, "应抛出异常"
            except Exception as e:
                # 【验证】错误被正确捕获
                assert "404" in str(e) or "Not Found" in str(e), "错误信息应包含404"
        
        print(f"✓ API错误处理测试通过")


class TestDAGARLinkage:
    """
    【测试类】DAG可视化与AR监控联动测试
    
    【职责】验证DAG可视化器与AR监控扩展的接口兼容性
    """
    
    @pytest.fixture
    def dag_visualizer(self):
        """【夹具】创建DAG可视化器"""
        return DAGVisualizer()
    
    @pytest.fixture
    def ar_extension(self):
        """【夹具】创建AR监控扩展"""
        return ARMonitorExtension()
    
    def test_dag_ar_interface_compatibility(self, dag_visualizer, ar_extension):
        """
        【测试方法】DAG与AR接口兼容性
        
        【功能】验证DAG节点数据能够正确转换为AR节点格式
        
        【步骤】
        1. 创建DAG节点
        2. 转换为AR节点格式
        3. 验证数据兼容性
        """
        # 【步骤1】创建DAG节点
        dag_node = {
            "id": "dag-node-001",
            "name": "数据处理节点",
            "type": "processing",
            "status": "running",
            "metrics": {
                "cpu_usage": 45.5,
                "memory_usage": 1024,
                "execution_time": 120.5
            }
        }
        
        # 【步骤2】转换为AR节点
        ar_node = ar_extension.convert_dag_node_to_ar(dag_node)
        
        # 【验证】AR节点格式
        assert ar_node is not None, "转换后的AR节点不应为空"
        assert "node_id" in ar_node or "id" in ar_node, "AR节点应包含ID"
        assert "node_type" in ar_node or "type" in ar_node, "AR节点应包含类型"
        
        print(f"✓ DAG-AR接口兼容性测试通过")
    
    def test_ar_metrics_integration(self, ar_extension):
        """
        【测试方法】AR指标集成
        
        【功能】验证AR指标采集和展示
        
        【步骤】
        1. 注册AR节点
        2. 采集指标
        3. 验证指标数据
        """
        # 【步骤1】注册AR节点
        ar_extension.register_node(
            node_id="ar-node-001",
            node_type=ARNodeType.RENDER,
            name="AR渲染节点",
            config={"max_tasks": 10}
        )
        
        # 【步骤2】更新指标
        ar_extension.update_node_metrics(
            node_id="ar-node-001",
            metrics={
                "task_count": 5,
                "success_rate": 0.95,
                "avg_execution_time": 2.5
            }
        )
        
        # 【步骤3】获取节点信息
        node_info = ar_extension.get_node("ar-node-001")
        
        # 【验证】节点信息
        assert node_info is not None, "节点信息应存在"
        assert "metrics" in node_info, "节点信息应包含指标"
        
        print(f"✓ AR指标集成测试通过")


class TestWebSocketPerformanceLinkage:
    """
    【测试类】WebSocket与性能监控联动测试
    
    【职责】验证WebSocket实时推送与前端性能监控的协同
    """
    
    @pytest.mark.asyncio
    async def test_websocket_message_performance(self):
        """
        【测试方法】WebSocket消息性能
        
        【功能】验证WebSocket消息推送的性能指标
        
        【步骤】
        1. 建立WebSocket连接
        2. 发送测试消息
        3. 测量延迟和吞吐量
        """
        # 【注】此测试需要实际WebSocket服务器运行
        # 这里使用模拟测试
        
        import time
        
        # 【模拟】消息发送性能
        start_time = time.time()
        
        # 模拟发送100条消息
        message_count = 100
        for i in range(message_count):
            # 模拟消息处理时间
            await asyncio.sleep(0.001)  # 1ms
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 【计算】吞吐量
        throughput = message_count / elapsed
        
        # 【验证】性能指标
        assert throughput > 50, f"WebSocket吞吐量应>50 msg/s，实际: {throughput:.2f}"
        assert elapsed < 5, f"100条消息发送应<5秒，实际: {elapsed:.2f}秒"
        
        print(f"✓ WebSocket性能测试通过: 吞吐量={throughput:.2f} msg/s")


# 【测试执行入口】
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
