#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置文件

【功能描述】
pytest共享配置和fixture定义，为所有测试模块提供统一的测试环境

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0

【依赖】
pytest>=7.0.0
pytest-asyncio>=0.21.0

【配置说明】
- 异步测试支持
- 测试数据夹具
- 模拟对象夹具
- 性能测试配置
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Generator
from unittest.mock import Mock, AsyncMock

# 【pytest配置】
def pytest_configure(config):
    """
    【配置函数】pytest全局配置
    
    【功能】配置pytest插件和标记
    """
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 标记性能测试"
    )
    config.addinivalue_line(
        "markers", "uat: 标记用户验收测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试（执行时间较长）"
    )


# 【事件循环夹具】
@pytest.fixture(scope="session")
def event_loop():
    """
    【夹具】提供会话级事件循环
    
    【功能】为异步测试提供共享的事件循环
    
    【返回】
        asyncio.AbstractEventLoop: 事件循环实例
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 【测试数据夹具】
@pytest.fixture
def sample_metrics_data() -> Dict[str, Any]:
    """
    【夹具】示例监控指标数据
    
    【功能】提供标准的监控指标测试数据
    
    【返回】
        Dict[str, Any]: 监控指标数据
    """
    return {
        "cpu_percent": 45.5,
        "memory_percent": 60.2,
        "disk_usage": 75.0,
        "network_io": {
            "bytes_sent": 1024000,
            "bytes_recv": 2048000,
            "packets_sent": 1500,
            "packets_recv": 3000
        },
        "process_count": 150,
        "load_average": [1.5, 1.2, 1.0],
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def sample_alert_data() -> Dict[str, Any]:
    """
    【夹具】示例告警数据
    
    【功能】提供标准的告警测试数据
    
    【返回】
        Dict[str, Any]: 告警数据
    """
    return {
        "id": "alert-001",
        "rule_id": "rule-001",
        "rule_name": "CPU使用率告警",
        "level": "warning",
        "message": "CPU使用率超过阈值80%",
        "metric_name": "cpu_percent",
        "metric_value": 85.5,
        "threshold": 80.0,
        "timestamp": datetime.now().isoformat(),
        "acknowledged": False,
        "resolved": False
    }


@pytest.fixture
def sample_dag_data() -> Dict[str, Any]:
    """
    【夹具】示例DAG数据
    
    【功能】提供标准的DAG测试数据
    
    【返回】
        Dict[str, Any]: DAG数据
    """
    return {
        "id": "dag-001",
        "name": "数据处理流程",
        "description": "测试DAG",
        "nodes": [
            {
                "id": "node-1",
                "name": "数据输入",
                "type": "input",
                "status": "completed",
                "x": 100,
                "y": 100,
                "config": {"source": "database"}
            },
            {
                "id": "node-2",
                "name": "数据清洗",
                "type": "process",
                "status": "running",
                "x": 300,
                "y": 100,
                "config": {"rules": ["trim", "validate"]}
            },
            {
                "id": "node-3",
                "name": "数据输出",
                "type": "output",
                "status": "pending",
                "x": 500,
                "y": 100,
                "config": {"destination": "file"}
            }
        ],
        "edges": [
            {"source": "node-1", "target": "node-2", "type": "success"},
            {"source": "node-2", "target": "node-3", "type": "success"}
        ],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_script_data() -> Dict[str, Any]:
    """
    【夹具】示例脚本数据
    
    【功能】提供标准的脚本测试数据
    
    【返回】
        Dict[str, Any]: 脚本数据
    """
    return {
        "id": "script-001",
        "name": "CPU监控脚本",
        "description": "监控系统CPU使用率",
        "category": "monitor",
        "path": "scripts/monitor/01_cpu_usage_monitor.py",
        "params": {
            "threshold": {
                "type": "number",
                "default": 80,
                "description": "告警阈值"
            },
            "duration": {
                "type": "number",
                "default": 60,
                "description": "监控时长"
            }
        },
        "schedule": "*/5 * * * *",
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }


# 【模拟服务夹具】
@pytest.fixture
def mock_dashboard_monitor():
    """
    【夹具】模拟仪表盘监控器
    
    【功能】提供模拟的仪表盘监控器
    
    【返回】
        Mock: 模拟的监控器对象
    """
    mock = Mock()
    mock.get_current_metrics.return_value = {
        "cpu_percent": 45.5,
        "memory_percent": 60.0
    }
    mock.push_metrics = AsyncMock(return_value=True)
    mock.get_alert_history.return_value = []
    return mock


@pytest.fixture
def mock_alert_service():
    """
    【夹具】模拟告警服务
    
    【功能】提供模拟的告警服务
    
    【返回】
        Mock: 模拟的告警服务对象
    """
    mock = Mock()
    mock.create_rule = AsyncMock(return_value="rule-001")
    mock.trigger_alert = AsyncMock(return_value=True)
    mock.acknowledge_alert = AsyncMock(return_value=True)
    mock.get_active_alerts.return_value = []
    return mock


@pytest.fixture
def mock_script_engine():
    """
    【夹具】模拟脚本引擎
    
    【功能】提供模拟的脚本引擎
    
    【返回】
        Mock: 模拟的脚本引擎对象
    """
    mock = Mock()
    mock.submit = AsyncMock(return_value="exec-001")
    mock.get_status = AsyncMock(return_value="running")
    mock.get_result = AsyncMock(return_value={"output": "success"})
    mock.execute = AsyncMock(return_value={"success": True})
    return mock


# 【性能测试配置】
@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """
    【夹具】性能测试阈值
    
    【功能】提供性能测试的阈值配置
    
    【返回】
        Dict[str, float]: 性能阈值
    """
    return {
        "fcp_ms": 2000,  # First Contentful Paint < 2s
        "lcp_ms": 2500,  # Largest Contentful Paint < 2.5s
        "fid_ms": 100,   # First Input Delay < 100ms
        "cls": 0.1,      # Cumulative Layout Shift < 0.1
        "api_p95_ms": 500,  # API P95 < 500ms
        "api_throughput_rps": 50,  # API吞吐量 >= 50 req/s
        "websocket_latency_ms": 5000,  # WebSocket延迟 < 5s
        "virtual_scroll_fps": 30,  # 虚拟滚动 FPS >= 30
    }


# 【测试环境配置】
@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    【夹具】测试环境配置
    
    【功能】提供测试环境的配置信息
    
    【返回】
        Dict[str, Any]: 测试配置
    """
    return {
        "base_url": "http://0.0.0.0:8000",
        "api_prefix": "/api",
        "ws_prefix": "/ws",
        "test_timeout": 30,
        "performance_test_duration": 5,
        "concurrent_users": 100,
    }


# 【测试工具函数】
@pytest.fixture
def test_helpers():
    """
    【夹具】测试辅助函数
    
    【功能】提供常用的测试辅助函数
    
    【返回】
        object: 测试辅助函数集合
    """
    class TestHelpers:
        @staticmethod
        def assert_response_time(start_time: float, end_time: float, threshold_ms: float):
            """
            【辅助方法】验证响应时间
            
            【参数】
                start_time: 开始时间戳
                end_time: 结束时间戳
                threshold_ms: 阈值（毫秒）
            
            【异常】
                AssertionError: 响应时间超过阈值
            """
            elapsed_ms = (end_time - start_time) * 1000
            assert elapsed_ms < threshold_ms, \
                f"响应时间应<{threshold_ms}ms，实际:{elapsed_ms:.2f}ms"
            return elapsed_ms
        
        @staticmethod
        def generate_test_data(count: int, prefix: str = "item") -> list:
            """
            【辅助方法】生成测试数据
            
            【参数】
                count: 数据数量
                prefix: 数据前缀
            
            【返回】
                list: 测试数据列表
            """
            return [
                {
                    "id": f"{prefix}-{i}",
                    "name": f"测试{prefix}{i}",
                    "value": i * 10,
                    "status": "active" if i % 2 == 0 else "inactive"
                }
                for i in range(count)
            ]
        
        @staticmethod
        def calculate_statistics(values: list) -> Dict[str, float]:
            """
            【辅助方法】计算统计信息
            
            【参数】
                values: 数值列表
            
            【返回】
                Dict[str, float]: 统计信息（平均值、最小值、最大值、P95）
            """
            if not values:
                return {"avg": 0, "min": 0, "max": 0, "p95": 0}
            
            sorted_values = sorted(values)
            p95_index = int(len(sorted_values) * 0.95) - 1
            p95_index = max(0, p95_index)
            
            return {
                "avg": sum(sorted_values) / len(sorted_values),
                "min": min(sorted_values),
                "max": max(sorted_values),
                "p95": sorted_values[p95_index] if p95_index < len(sorted_values) else sorted_values[-1]
            }
    
    return TestHelpers()


# 【钩子函数】
def pytest_collection_modifyitems(config, items):
    """
    【钩子】修改测试项
    
    【功能】自动添加标记到测试项
    """
    for item in items:
        # 根据路径自动添加标记
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "uat" in str(item.fspath):
            item.add_marker(pytest.mark.uat)


def pytest_runtest_setup(item):
    """
    【钩子】测试设置
    
    【功能】每个测试前的设置
    """
    # 可以在这里添加测试前的准备工作
    pass


def pytest_runtest_teardown(item, nextitem):
    """
    【钩子】测试清理
    
    【功能】每个测试后的清理工作
    """
    # 可以在这里添加测试后的清理工作
    pass


# 【测试报告钩子】
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    【钩子】终端摘要
    
    【功能】在测试结束时输出摘要信息
    """
    print("\n" + "="*60)
    print("【YL-Monitor 测试执行摘要】")
    print("="*60)
    
    # 统计测试结果
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    skipped = len(terminalreporter.stats.get('skipped', []))
    total = passed + failed + skipped
    
    print(f"总测试数: {total}")
    print(f"通过: {passed} ✓")
    print(f"失败: {failed} ✗")
    print(f"跳过: {skipped} ⚠")
    print(f"通过率: {(passed/total*100):.1f}%" if total > 0 else "N/A")
    print("="*60)
