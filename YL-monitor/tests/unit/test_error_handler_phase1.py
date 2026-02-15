"""
阶段1验证测试：统一错误处理和堆栈跟踪

测试目标：
1. 验证环境配置正确
2. 验证生产环境堆栈不泄露
3. 验证调用链追踪正常
4. 验证错误恢复服务集成

作者: AI Assistant
创建时间: 2026-01-12
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# 设置测试环境
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

# 添加应用路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestEnvironmentConfig:
    """环境配置测试"""

    def test_production_env_detection(self):
        """测试生产环境检测"""
        from app.middleware.error_handler import IS_PRODUCTION, ENV, DEBUG_MODE

        # 测试环境变量读取
        assert ENV in ["development", "production", "test"]
        assert isinstance(IS_PRODUCTION, bool)
        assert isinstance(DEBUG_MODE, bool)

    def test_stack_trace_level_config(self):
        """测试堆栈跟踪级别配置"""
        from app.middleware.error_handler import (
            StackTraceLevel,
            CURRENT_STACK_LEVEL
        )

        # 验证枚举值
        assert hasattr(StackTraceLevel, 'NONE')
        assert hasattr(StackTraceLevel, 'MINIMAL')
        assert hasattr(StackTraceLevel, 'FULL')
        assert hasattr(StackTraceLevel, 'DEV_ONLY')

        # 验证当前级别
        assert isinstance(CURRENT_STACK_LEVEL, str)


class TestErrorResponse:
    """错误响应测试"""

    def test_error_response_creation(self):
        """测试错误响应创建"""
        from app.middleware.error_handler import ErrorResponse

        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="测试错误",
            details={"key": "value"},
            request_id="test-123"
        )

        assert response.error_code == "TEST_ERROR"
        assert response.message == "测试错误"
        assert response.details == {"key": "value"}
        assert response.request_id == "test-123"
        assert response.timestamp is not None

    def test_error_response_with_stack_trace(self):
        """测试带堆栈跟踪的错误响应"""
        from app.middleware.error_handler import ErrorResponse

        response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="内部错误",
            stack_trace="Traceback (most recent call last):..."
        )

        assert response.stack_trace is not None
        assert "Traceback" in response.stack_trace

    def test_error_response_with_call_chain(self):
        """测试带调用链的错误响应"""
        from app.middleware.error_handler import ErrorResponse

        call_chain = ["api:2026-01-12T10:00:00", "service:2026-01-12T10:00:01"]
        response = ErrorResponse(
            error_code="BAD_REQUEST",
            message="请求错误",
            call_chain=call_chain
        )

        assert len(response.call_chain) == 2
        assert response.call_chain == call_chain


class TestStackTraceFormatting:
    """堆栈格式化测试"""

    def test_format_stack_trace_none(self):
        """测试NONE级别返回None"""
        from app.middleware.error_handler import format_stack_trace, StackTraceLevel

        result = format_stack_trace(Exception("test"), StackTraceLevel.NONE)
        assert result is None

    def test_format_stack_trace_minimal(self):
        """测试MINIMAL级别"""
        from app.middleware.error_handler import format_stack_trace, StackTraceLevel

        exc = Exception("测试异常")
        result = format_stack_trace(exc, StackTraceLevel.MINIMAL)

        assert result is not None
        assert "Exception" in result
        assert "测试异常" in result

    def test_format_stack_trace_full(self):
        """测试FULL级别"""
        from app.middleware.error_handler import format_stack_trace, StackTraceLevel

        exc = Exception("测试异常")
        result = format_stack_trace(exc, StackTraceLevel.FULL)

        assert result is not None
        assert "Traceback" in result
        assert "Exception" in result


class TestErrorRecoveryService:
    """错误恢复服务测试"""

    def test_error_recovery_service_creation(self):
        """测试错误恢复服务创建"""
        from app.services.error_recovery import ErrorRecoveryService

        service = ErrorRecoveryService()
        assert service is not None
        assert hasattr(service, '_error_history')
        assert hasattr(service, '_checkpoints')

    def test_error_context_creation(self):
        """测试错误上下文创建"""
        from app.services.error_recovery import ErrorContext

        context = ErrorContext(
            error_id="err-001",
            error_type="TIMEOUT",
            error_message="请求超时",
            component="api",
            operation="fetch_data",
            timestamp=datetime.now(),
            context={"retry_count": 0}
        )

        assert context.error_id == "err-001"
        assert context.error_type == "TIMEOUT"
        assert context.context["retry_count"] == 0

    def test_recovery_strategy_base(self):
        """测试恢复策略基类"""
        from app.services.error_recovery import RecoveryStrategyBase, ErrorContext

        strategy = RecoveryStrategyBase(
            name="test_strategy",
            description="测试策略",
            max_attempts=3
        )

        assert strategy.name == "test_strategy"
        assert strategy.max_attempts == 3

    def test_resource_exhausted_strategy(self):
        """测试资源耗尽恢复策略"""
        from app.services.error_recovery import ResourceExhaustedRecoveryStrategy

        strategy = ResourceExhaustedRecoveryStrategy()
        assert strategy.name == "resource_exhausted_recovery"

        # 测试can_handle
        context = Mock()
        context.error_message = "MemoryError: out of memory"
        context.error_type = "MEMORY_ERROR"

        assert strategy.can_handle(context) is True

    def test_stack_trace_analyzer(self):
        """测试堆栈分析器"""
        from app.services.error_recovery import StackTraceAnalyzer

        analyzer = StackTraceAnalyzer()

        # 测试空堆栈
        result = analyzer.analyze(None)
        assert result["error"] == "no_stack_trace"

        # 测试FileNotFoundError
        stack = '''Traceback (most recent call last):
  File "/app/script.py", line 10, in <module>
    open("/nonexistent/file.txt")
FileNotFoundError: No such file or directory
'''
        result = analyzer.analyze(stack)
        assert result["error_type"] == "file_not_found"
        assert len(result["affected_files"]) > 0
        assert len(result["suggestions"]) > 0


class TestScriptEngineIntegration:
    """脚本引擎集成测试"""

    def test_script_execution_dataclass(self):
        """测试ScriptExecution数据类"""
        from app.services.script_engine import ScriptExecution, ScriptStatus

        execution = ScriptExecution(
            id="exec-001",
            script_id="test_script",
            script_name="测试脚本",
            script_path="/scripts/test.py"
        )

        assert execution.id == "exec-001"
        assert execution.script_id == "test_script"
        assert execution.status == ScriptStatus.PENDING
        assert execution.call_chain == []
        assert execution.stack_trace is None

    def test_resource_limits(self):
        """测试资源限制"""
        from app.services.script_engine import ResourceLimits

        limits = ResourceLimits(
            max_cpu_percent=50.0,
            max_memory_mb=256,
            max_execution_time=600
        )

        assert limits.max_cpu_percent == 50.0
        assert limits.max_memory_mb == 256
        assert limits.max_execution_time == 600

    def test_retry_policy(self):
        """测试重试策略"""
        from app.services.script_engine import RetryPolicy

        policy = RetryPolicy(
            max_retries=5,
            retry_delay=10.0,
            exponential_backoff=True
        )

        # 验证延迟计算
        assert policy.get_delay(0) == 10.0
        assert policy.get_delay(1) == 20.0  # 2^1 * 10
        assert policy.get_delay(2) == 40.0  # 2^2 * 10


class TestProductionSecurity:
    """生产环境安全性测试"""

    @patch.dict(os.environ, {"APP_ENV": "production"})
    def test_production_no_stack_trace_in_response(self):
        """验证生产环境响应中不包含堆栈跟踪"""
        from app.middleware.error_handler import ErrorResponse, IS_PRODUCTION

        assert IS_PRODUCTION is True

        response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="内部服务器错误",
            stack_trace="This should be hidden in production"
        )

        result = response.to_dict()
        assert "stack_trace" not in result

    @patch.dict(os.environ, {"APP_ENV": "development"})
    def test_development_shows_stack_trace(self):
        """验证开发环境响应中包含堆栈跟踪"""
        from app.middleware.error_handler import ErrorResponse, IS_PRODUCTION

        assert IS_PRODUCTION is False

        response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="开发环境错误",
            stack_trace="This should be visible in development"
        )

        result = response.to_dict()
        assert "stack_trace" in result
        assert result["stack_trace"] == "This should be visible in development"


# ==================== 运行测试 ====================

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])

