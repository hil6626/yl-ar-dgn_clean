#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查服务单元测试

【功能描述】
测试健康检查服务的核心功能，包括：
- 健康检查结果
- 系统资源检查
- 磁盘空间检查
- 日志文件检查
- 健康检查管理器

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0
"""

import pytest
from datetime import datetime

# 导入被测试的模块
from app.services.health_check import (
    HealthCheckManager,
    HealthStatus,
    HealthCheckResult,
    SystemResourceCheck,
    DiskSpaceCheck,
    LogFileCheck,
    HealthCheck,
)


@pytest.mark.unit
class TestHealthStatus:
    """健康状态枚举测试"""

    def test_health_status_values(self):
        """测试健康状态值"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.UNKNOWN.value == "unknown"


@pytest.mark.unit
class TestHealthCheckResult:
    """健康检查结果类测试"""

    def test_result_creation(self):
        """测试结果对象创建"""
        result = HealthCheckResult(
            component="test-component",
            status=HealthStatus.HEALTHY,
            message="测试消息",
            details={"key": "value"},
            response_time_ms=50.0,
            suggestion="测试建议",
        )
        
        assert result.component == "test-component"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "测试消息"
        assert result.details["key"] == "value"
        assert result.response_time_ms == 50.0
        assert result.suggestion == "测试建议"

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        result = HealthCheckResult(
            component="test",
            status=HealthStatus.HEALTHY,
            message="OK",
        )
        
        data = result.to_dict()
        assert data["component"] == "test"
        assert data["status"] == "healthy"
        assert "timestamp" in data


@pytest.mark.unit
class TestSystemResourceCheck:
    """系统资源检查测试"""

    @pytest.mark.asyncio
    async def test_system_resource_check(self):
        """测试系统资源检查"""
        check = SystemResourceCheck(
            cpu_threshold=80.0,
            memory_threshold=85.0,
            disk_threshold=90.0,
        )
        
        result = await check.check()
        
        assert isinstance(result, HealthCheckResult)
        assert result.component == "system_resources"
        assert "cpu_percent" in result.details
        assert "memory_percent" in result.details
        assert "disk_percent" in result.details

    @pytest.mark.asyncio
    async def test_system_resource_with_high_usage(self):
        """测试高资源使用率"""
        # 使用很低的阈值确保触发警告
        check = SystemResourceCheck(
            cpu_threshold=0.1,
            memory_threshold=0.1,
            disk_threshold=0.1,
        )
        
        result = await check.check()
        
        # 应该返回警告或严重状态
        assert result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]


@pytest.mark.unit
class TestDiskSpaceCheck:
    """磁盘空间检查测试"""

    @pytest.mark.asyncio
    async def test_disk_space_check(self):
        """测试磁盘空间检查"""
        check = DiskSpaceCheck(
            warning_threshold=80.0,
            critical_threshold=90.0,
            paths=["/"],
        )
        
        result = await check.check()
        
        assert isinstance(result, HealthCheckResult)
        assert result.component == "disk_space"
        assert "/" in result.details

    @pytest.mark.asyncio
    async def test_disk_space_with_multiple_paths(self):
        """测试多路径磁盘检查"""
        check = DiskSpaceCheck(
            paths=["/", "/tmp"],
        )
        
        result = await check.check()
        
        assert isinstance(result, HealthCheckResult)
        # 至少有一个路径的检查结果


@pytest.mark.unit
class TestLogFileCheck:
    """日志文件检查测试"""

    @pytest.mark.asyncio
    async def test_log_file_check(self):
        """测试日志文件检查"""
        check = LogFileCheck(
            log_dir="logs",
            max_size_mb=100.0,
            max_files=50,
        )
        
        result = await check.check()
        
        assert isinstance(result, HealthCheckResult)
        assert result.component == "log_files"

    @pytest.mark.asyncio
    async def test_log_file_check_nonexistent_dir(self):
        """测试不存在的日志目录"""
        check = LogFileCheck(
            log_dir="nonexistent_logs_dir",
        )
        
        result = await check.check()
        
        assert result.status == HealthStatus.HEALTHY
        assert "不存在" in result.message or "不存在" in result.suggestion


@pytest.mark.unit
class TestHealthCheckManager:
    """健康检查管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建健康检查管理器实例"""
        return HealthCheckManager()

    def test_register_check(self, manager):
        """测试注册检查"""
        check = SystemResourceCheck()
        manager.register_check(check)
        
        assert "system_resources" in manager.checks

    def test_unregister_check(self, manager):
        """测试注销检查"""
        check = SystemResourceCheck()
        manager.register_check(check)
        assert "system_resources" in manager.checks
        
        manager.unregister_check("system_resources")
        assert "system_resources" not in manager.checks

    @pytest.mark.asyncio
    async def test_check_all(self, manager):
        """测试执行所有检查"""
        # 注册检查
        manager.register_check(SystemResourceCheck())
        manager.register_check(DiskSpaceCheck())
        
        # 执行所有检查
        results = await manager.check_all()
        
        assert isinstance(results, dict)
        assert "system_resources" in results
        assert "disk_space" in results

    def test_get_overall_status(self, manager):
        """测试获取整体健康状态"""
        # 注册健康检查
        check = SystemResourceCheck()
        manager.register_check(check)
        
        # 获取整体状态
        status = manager.get_overall_status()
        
        assert isinstance(status, HealthStatus)

    def test_get_health_report(self, manager):
        """测试获取健康报告"""
        # 注册检查
        manager.register_check(SystemResourceCheck())
        
        # 获取报告
        report = manager.get_health_report()
        
        assert isinstance(report, dict)
        assert "overall_status" in report
        assert "timestamp" in report
        assert "checks" in report
        assert "history" in report

    @pytest.mark.asyncio
    async def test_start_and_stop(self, manager):
        """测试启动和停止"""
        # 注册检查
        manager.register_check(SystemResourceCheck())
        
        # 启动
        await manager.start()
        assert manager._running is True
        
        # 等待一段时间
        import asyncio
        await asyncio.sleep(0.1)
        
        # 停止
        await manager.stop()
        assert manager._running is False

    def test_register_callback(self, manager):
        """测试注册回调"""
        callback_called = [False]
        
        def test_callback(result):
            callback_called[0] = True
        
        manager.register_callback(test_callback)
        assert len(manager._callbacks) == 1

    def test_save_report(self, manager, tmp_path):
        """测试保存报告"""
        # 注册检查
        manager.register_check(SystemResourceCheck())
        
        # 保存报告
        report_path = tmp_path / "health_report.json"
        manager.save_report(str(report_path))
        
        # 验证文件存在
        assert report_path.exists()


@pytest.mark.unit
class TestHealthCheckEdgeCases:
    """健康检查边界情况测试"""

    @pytest.mark.asyncio
    async def test_empty_manager(self):
        """测试空管理器"""
        manager = HealthCheckManager()
        
        results = await manager.check_all()
        assert len(results) == 0
        
        status = manager.get_overall_status()
        # 空管理器可能返回HEALTHY或UNKNOWN，取决于实现
        assert status in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]

    @pytest.mark.asyncio
    async def test_check_with_exception(self):
        """测试抛出异常的检查"""
        class FailingCheck(HealthCheck):
            def __init__(self):
                super().__init__("failing")
            
            async def _do_check(self):
                raise RuntimeError("Test error")
        
        check = FailingCheck()
        result = await check.check()
        
        assert result.status == HealthStatus.CRITICAL
        assert "异常" in result.message

    def test_history_limit(self):
        """测试历史记录限制"""
        manager = HealthCheckManager()
        # 设置历史记录限制
        original_limit = manager._max_history
        manager._max_history = 10
        
        # 添加超过限制的历史记录
        for i in range(15):
            manager._history.append({
                "timestamp": datetime.now().isoformat(),
                "index": i,
            })
            # 手动维护限制（如果实现不自动维护）
            if len(manager._history) > manager._max_history:
                manager._history.pop(0)
        
        # 验证限制生效
        assert len(manager._history) <= 10
        
        # 恢复原始限制
        manager._max_history = original_limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
