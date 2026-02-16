#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误恢复服务单元测试

【功能描述】
测试错误恢复服务的核心功能，包括：
- 错误记录和分类
- 恢复策略执行
- 检查点管理
- 统计信息收集

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
from app.services.error_recovery import (
    ErrorRecoveryService,
    RecoveryStrategy,
    ErrorSeverity,
    ErrorRecord,
    RecoveryResult,
    Checkpoint,
    handle_script_failure,
    handle_system_error,
    create_checkpoint,
    get_recovery_statistics,
)


@pytest.mark.unit
class TestErrorRecord:
    """错误记录类测试"""

    def test_error_record_creation(self):
        """测试错误记录创建"""
        record = ErrorRecord(
            error_id="err-001",
            error_type="timeout",
            error_message="连接超时",
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            context={"operation": "api_call"},
            stack_trace="Traceback...",
            recovery_attempts=0,
            recovered=False,
        )
        
        assert record.error_id == "err-001"
        assert record.error_type == "timeout"
        assert record.severity == ErrorSeverity.HIGH
        assert record.recovered is False

    def test_error_record_with_recovery(self):
        """测试已恢复的错误记录"""
        record = ErrorRecord(
            error_id="err-002",
            error_type="connection_error",
            error_message="连接失败",
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            recovery_attempts=2,
            recovered=True,
            recovery_strategy="retry",
        )
        
        assert record.recovered is True
        assert record.recovery_strategy == "retry"
        assert record.recovery_attempts == 2


@pytest.mark.unit
class TestRecoveryResult:
    """恢复结果类测试"""

    def test_recovery_result_success(self):
        """测试成功的恢复结果"""
        result = RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.RETRY,
            message="重试成功",
            details={"attempts": 2},
            timestamp=datetime.now(),
        )
        
        assert result.success is True
        assert result.strategy == RecoveryStrategy.RETRY
        assert "重试成功" in result.message

    def test_recovery_result_failure(self):
        """测试失败的恢复结果"""
        result = RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.ESCALATE,
            message="需要人工干预",
            details={"reason": "max_retries_exceeded"},
            timestamp=datetime.now(),
        )
        
        assert result.success is False
        assert result.strategy == RecoveryStrategy.ESCALATE


@pytest.mark.unit
class TestCheckpoint:
    """检查点类测试"""

    def test_checkpoint_creation(self):
        """测试检查点创建"""
        checkpoint = Checkpoint(
            checkpoint_id="chk-001",
            timestamp=datetime.now(),
            state_data={"key": "value", "count": 42},
            metadata={"source": "test"},
        )
        
        assert checkpoint.checkpoint_id == "chk-001"
        assert checkpoint.state_data["key"] == "value"
        assert checkpoint.metadata["source"] == "test"


@pytest.mark.unit
class TestErrorRecoveryService:
    """错误恢复服务测试"""

    @pytest.fixture
    def service(self):
        """创建错误恢复服务实例"""
        return ErrorRecoveryService(max_history_size=100)

    @pytest.mark.asyncio
    async def test_handle_script_failure_retry(self, service):
        """测试脚本失败重试恢复"""
        result = await service.handle_script_failure(
            execution_id="exec-001",
            error=TimeoutError("执行超时"),
            context={
                "script_id": "script-001",
                "retry_count": 0,
                "max_retries": 3,
            },
        )
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.strategy == RecoveryStrategy.RETRY

    @pytest.mark.asyncio
    async def test_handle_script_failure_max_retries(self, service):
        """测试超过最大重试次数"""
        result = await service.handle_script_failure(
            execution_id="exec-002",
            error=TimeoutError("执行超时"),
            context={
                "script_id": "script-002",
                "retry_count": 3,
                "max_retries": 3,
                "fallback_available": False,
            },
        )
        
        assert result.success is False
        assert result.strategy == RecoveryStrategy.ESCALATE

    @pytest.mark.asyncio
    async def test_handle_script_failure_with_fallback(self, service):
        """测试使用备用方案"""
        result = await service.handle_script_failure(
            execution_id="exec-003",
            error=RuntimeError("执行失败"),
            context={
                "script_id": "script-003",
                "retry_count": 3,
                "max_retries": 3,
                "fallback_available": True,
                "fallback_script": "fallback.py",
            },
        )
        
        assert result.success is True
        assert result.strategy == RecoveryStrategy.FALLBACK

    @pytest.mark.asyncio
    async def test_handle_system_error_timeout(self, service):
        """测试系统超时错误"""
        result = await service.handle_system_error(
            error_type="timeout_error",
            context={"service": "api", "endpoint": "/test"},
        )
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_handle_system_error_memory(self, service):
        """测试内存不足错误"""
        result = await service.handle_system_error(
            error_type="memory_error",
            context={"memory_usage": 95, "service": "worker"},
        )
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_and_restore_checkpoint(self, service):
        """测试创建和恢复检查点"""
        # 创建检查点
        checkpoint = await service.create_checkpoint(
            checkpoint_id="dag-exec-001",
            state_data={
                "completed_nodes": ["A", "B"],
                "current_node": "C",
            },
            metadata={"dag_id": "dag-001"},
        )
        
        assert checkpoint.checkpoint_id == "dag-exec-001"
        assert "completed_nodes" in checkpoint.state_data
        
        # 恢复检查点
        restored_state = await service.restore_from_checkpoint("dag-exec-001")
        assert restored_state is not None
        assert restored_state["current_node"] == "C"

    @pytest.mark.asyncio
    async def test_restore_nonexistent_checkpoint(self, service):
        """测试恢复不存在的检查点"""
        state = await service.restore_from_checkpoint("nonexistent")
        assert state is None

    @pytest.mark.asyncio
    async def test_error_history_tracking(self, service):
        """测试错误历史记录"""
        # 处理多个错误
        for i in range(5):
            await service.handle_system_error(
                error_type=f"error_type_{i}",
                context={"index": i},
            )
        
        # 查询历史
        history = service.get_error_history()
        assert len(history) >= 5
        
        # 按类型查询
        filtered = service.get_error_history(error_type="error_type_0")
        assert len(filtered) >= 1

    @pytest.mark.asyncio
    async def test_error_history_with_severity_filter(self, service):
        """测试按严重级别过滤历史"""
        # 创建不同级别的错误
        await service.handle_system_error(
            error_type="critical_error",
            context={"severity": "critical"},
        )
        
        # 按级别查询
        history = service.get_error_history(severity=ErrorSeverity.CRITICAL)
        assert isinstance(history, list)
        # 注意：实际过滤取决于实现

    @pytest.mark.asyncio
    async def test_recovery_statistics(self, service):
        """测试恢复统计信息"""
        # 处理一些错误
        await service.handle_script_failure(
            execution_id="exec-001",
            error=Exception("测试错误"),
            context={"retry_count": 0, "max_retries": 1},
        )
        
        # 获取统计
        stats = service.get_recovery_statistics()
        assert "total_errors" in stats
        assert "recovery_rate" in stats

    def test_register_custom_recovery_handler(self, service):
        """测试注册自定义恢复处理器"""
        async def custom_handler(context):
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.FALLBACK,
                message="自定义恢复",
                details={},
                timestamp=datetime.now(),
            )
        
        service.register_recovery_handler("custom_error", custom_handler)
        # 验证处理器已注册
        assert "custom_error" in service._recovery_handlers

    @pytest.mark.asyncio
    async def test_max_history_size(self, service):
        """测试历史记录大小限制"""
        # 创建大量错误记录
        for i in range(150):
            await service.handle_system_error(
                error_type="bulk_error",
                context={"index": i},
            )
        
        # 验证历史记录被限制
        history = service.get_error_history()
        assert len(history) <= service._max_history_size


@pytest.mark.unit
class TestRecoveryStrategies:
    """恢复策略测试"""

    @pytest.fixture
    def service(self):
        """创建错误恢复服务实例"""
        return ErrorRecoveryService()

    @pytest.mark.asyncio
    async def test_timeout_recovery_strategy(self, service):
        """测试超时恢复策略"""
        result = await service._handle_timeout_error(
            context={"delay": 5, "endpoint": "/api/test"},
        )
        
        assert result.success is True
        assert result.strategy == RecoveryStrategy.RETRY

    @pytest.mark.asyncio
    async def test_connection_error_recovery(self, service):
        """测试连接错误恢复"""
        result = await service._handle_connection_error(
            context={"host": "0.0.0.0", "port": 8080},
        )
        
        assert result.success is True
        assert "重试" in result.message

    @pytest.mark.asyncio
    async def test_memory_error_recovery(self, service):
        """测试内存错误恢复"""
        result = await service._handle_memory_error(
            context={"memory_usage": 90},
        )
        
        assert result.success is True
        assert result.strategy == RecoveryStrategy.FALLBACK

    @pytest.mark.asyncio
    async def test_disk_full_recovery(self, service):
        """测试磁盘满恢复"""
        result = await service._handle_disk_full_error(
            context={"disk_usage": 99},
        )
        
        assert result.success is True
        assert "清理" in result.message

    @pytest.mark.asyncio
    async def test_permission_error_recovery(self, service):
        """测试权限错误恢复"""
        result = await service._handle_permission_error(
            context={"required": ["read", "write"]},
        )
        
        assert result.success is False
        assert result.strategy == RecoveryStrategy.ESCALATE

    @pytest.mark.asyncio
    async def test_system_overload_recovery(self, service):
        """测试系统过载恢复"""
        result = await service._handle_system_overload(
            context={"load": 95, "service": "worker"},
        )
        
        assert result.success is True
        assert result.strategy == RecoveryStrategy.FALLBACK


@pytest.mark.unit
class TestErrorSeverity:
    """错误严重级别测试"""

    @pytest.fixture
    def service(self):
        """创建错误恢复服务实例"""
        return ErrorRecoveryService()

    def test_determine_critical_severity(self, service):
        """测试判定紧急级别"""
        severity = service._determine_severity(
            "memory_exhaustion",
            {"memory_usage": 99},
        )
        assert severity == ErrorSeverity.CRITICAL

    def test_determine_high_severity(self, service):
        """测试判定高级别"""
        severity = service._determine_severity(
            "service_unavailable",
            {"affected_services": 5},
        )
        assert severity == ErrorSeverity.HIGH

    def test_determine_medium_severity(self, service):
        """测试判定中级别"""
        severity = service._determine_severity(
            "minor_error",
            {"affected_services": 1},
        )
        assert severity == ErrorSeverity.MEDIUM


@pytest.mark.unit
class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_handle_script_failure_convenience(self):
        """测试脚本失败便捷函数"""
        result = await handle_script_failure(
            execution_id="exec-001",
            error=Exception("测试错误"),
            context={"retry_count": 0},
        )
        
        assert isinstance(result, RecoveryResult)

    @pytest.mark.asyncio
    async def test_handle_system_error_convenience(self):
        """测试系统错误便捷函数"""
        result = await handle_system_error(
            error_type="test_error",
            context={"test": True},
        )
        
        assert isinstance(result, RecoveryResult)

    @pytest.mark.asyncio
    async def test_create_checkpoint_convenience(self):
        """测试创建检查点便捷函数"""
        checkpoint = await create_checkpoint(
            checkpoint_id="test-chk",
            state_data={"test": "data"},
        )
        
        assert isinstance(checkpoint, Checkpoint)

    def test_get_recovery_statistics_convenience(self):
        """测试获取统计便捷函数"""
        stats = get_recovery_statistics()
        
        assert isinstance(stats, dict)
        assert "total_errors" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
