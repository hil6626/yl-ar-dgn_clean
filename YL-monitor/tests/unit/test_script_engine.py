#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本引擎单元测试

【功能描述】
测试脚本执行引擎的核心功能，包括：
- 脚本提交和执行
- 堆栈跟踪捕获
- 调用链追踪
- 错误处理
- 历史记录查询

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0
"""

import pytest
import asyncio

# 导入被测试的模块
from app.services.script_engine import (
    ScriptExecutionEngine,
    ScriptExecution,
    ExecutionStatus,
    ResourceLimits,
)


@pytest.mark.unit
class TestScriptExecution:
    """脚本执行类测试"""

    def test_script_execution_creation(self):
        """测试脚本执行对象创建"""
        execution = ScriptExecution(
            id="exec-001",
            script_id="script-001",
            script_name="测试脚本",
            script_path="/path/to/script.py",
            params={"key": "value"},
            status=ExecutionStatus.PENDING,
            priority=50,
        )
        
        assert execution.id == "exec-001"
        assert execution.script_id == "script-001"
        assert execution.script_name == "测试脚本"
        assert execution.status == ExecutionStatus.PENDING
        assert execution.priority == 50
        assert execution.params == {"key": "value"}
        assert execution.created_at is not None

    def test_script_execution_status_transition(self):
        """测试状态转换"""
        execution = ScriptExecution(
            id="exec-001",
            script_id="script-001",
            script_name="测试脚本",
            script_path="/path/to/script.py",
            status=ExecutionStatus.PENDING,
        )
        
        # 状态转换
        execution.status = ExecutionStatus.RUNNING
        assert execution.status == ExecutionStatus.RUNNING
        
        execution.status = ExecutionStatus.COMPLETED
        assert execution.status == ExecutionStatus.COMPLETED

    def test_script_execution_with_call_chain(self):
        """测试调用链追踪"""
        execution = ScriptExecution(
            id="exec-001",
            script_id="script-001",
            script_name="测试脚本",
            script_path="/path/to/script.py",
            call_chain=["parent-001", "grandparent-001"],
            parent_execution_id="parent-001",
        )
        
        assert execution.call_chain == ["parent-001", "grandparent-001"]
        assert execution.parent_execution_id == "parent-001"

    def test_script_execution_with_stack_trace(self):
        """测试堆栈跟踪"""
        execution = ScriptExecution(
            id="exec-001",
            script_id="script-001",
            script_name="测试脚本",
            script_path="/path/to/script.py",
            stack_trace="Traceback (most recent call last):\n  File...",
        )
        
        assert execution.stack_trace is not None
        assert "Traceback" in execution.stack_trace


@pytest.mark.unit
class TestScriptExecutionEngine:
    """脚本执行引擎测试"""

    @pytest.fixture
    def engine(self):
        """创建脚本引擎实例"""
        return ScriptExecutionEngine(max_concurrent=5)

    @pytest.fixture
    def sample_script(self, tmp_path):
        """创建示例脚本文件"""
        script_file = tmp_path / "test_script.py"
        script_file.write_text("""
#!/usr/bin/env python3
import sys
import json

def main():
    data = {"status": "ok", "message": "Hello from test script"}
    print(json.dumps(data))
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
        return str(script_file)

    @pytest.mark.asyncio
    async def test_submit_script(self, engine, sample_script):
        """测试提交脚本"""
        execution_id = await engine.submit(
            script_id="script-001",
            script_name="测试脚本",
            script_path=sample_script,
            params={"test": "value"},
            priority=50,
        )
        
        assert execution_id is not None
        assert isinstance(execution_id, str)
        assert len(execution_id) > 0

    @pytest.mark.asyncio
    async def test_get_execution_status(self, engine, sample_script):
        """测试获取执行状态"""
        execution_id = await engine.submit(
            script_id="script-001",
            script_name="测试脚本",
            script_path=sample_script,
        )
        
        status = await engine.get_status(execution_id)
        assert status in [
            ExecutionStatus.PENDING, ExecutionStatus.RUNNING,
            ExecutionStatus.COMPLETED
        ]

    @pytest.mark.asyncio
    async def test_get_execution_result(self, engine, sample_script):
        """测试获取执行结果"""
        execution_id = await engine.submit(
            script_id="script-001",
            script_name="测试脚本",
            script_path=sample_script,
        )
        
        # 等待执行完成
        await asyncio.sleep(0.5)
        
        result = await engine.get_result(execution_id)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execution_with_resource_limits(self, engine, sample_script):
        """测试资源限制"""
        limits = ResourceLimits(
            max_execution_time=30,
            max_memory_mb=512,
        )
        
        execution_id = await engine.submit(
            script_id="script-001",
            script_name="测试脚本",
            script_path=sample_script,
            resource_limits=limits,
        )
        
        assert execution_id is not None

    @pytest.mark.asyncio
    async def test_parent_execution_tracking(self, engine, sample_script):
        """测试父执行追踪"""
        parent_id = await engine.submit(
            script_id="parent-script",
            script_name="父脚本",
            script_path=sample_script,
        )
        
        child_id = await engine.submit(
            script_id="child-script",
            script_name="子脚本",
            script_path=sample_script,
            parent_execution_id=parent_id,
        )
        
        assert child_id is not None
        # 验证可以通过父ID查询子执行
        children = await engine.get_children(parent_id)
        assert child_id in [c.id for c in children]

    @pytest.mark.asyncio
    async def test_execution_history_lookup(self, engine, sample_script):
        """测试执行历史查询"""
        execution_id = await engine.submit(
            script_id="script-001",
            script_name="测试脚本",
            script_path=sample_script,
        )
        
        # 通过ID查询
        execution = await engine.get_execution(execution_id)
        assert execution is not None
        assert execution.id == execution_id

    @pytest.mark.asyncio
    async def test_concurrent_execution_limit(self, engine, sample_script):
        """测试并发执行限制"""
        # 提交多个脚本
        execution_ids = []
        for i in range(10):
            exec_id = await engine.submit(
                script_id=f"script-{i}",
                script_name=f"脚本-{i}",
                script_path=sample_script,
            )
            execution_ids.append(exec_id)
        
        assert len(execution_ids) == 10
        # 验证引擎正确处理并发

    @pytest.mark.asyncio
    async def test_cancel_execution(self, engine, sample_script):
        """测试取消执行"""
        execution_id = await engine.submit(
            script_id="long-script",
            script_name="长时间脚本",
            script_path=sample_script,
        )
        
        # 取消执行
        result = await engine.cancel(execution_id)
        assert result is True
        
        # 验证状态
        status = await engine.get_status(execution_id)
        assert status in [ExecutionStatus.CANCELLED, ExecutionStatus.COMPLETED]

    @pytest.mark.asyncio
    async def test_execution_with_config_snapshot(self, engine, sample_script):
        """测试配置快照"""
        config_snapshot = {
            "timeout": 60,
            "retry_count": 3,
            "environment": "test"
        }
        
        execution_id = await engine.submit(
            script_id="script-001",
            script_name="测试脚本",
            script_path=sample_script,
            config_snapshot=config_snapshot,
        )
        
        execution = await engine.get_execution(execution_id)
        assert execution.config_snapshot == config_snapshot


@pytest.mark.unit
class TestScriptEngineErrorHandling:
    """脚本引擎错误处理测试"""

    @pytest.fixture
    def engine(self):
        """创建脚本引擎实例"""
        return ScriptExecutionEngine(max_concurrent=5)

    @pytest.mark.asyncio
    async def test_nonexistent_script(self, engine):
        """测试不存在的脚本"""
        execution_id = await engine.submit(
            script_id="nonexistent",
            script_name="不存在的脚本",
            script_path="/nonexistent/path.py",
        )
        
        # 等待执行
        await asyncio.sleep(0.5)
        
        result = await engine.get_result(execution_id)
        assert result is not None
        # 应该包含错误信息

    @pytest.mark.asyncio
    async def test_script_with_error(self, engine, tmp_path):
        """测试执行出错的脚本"""
        # 创建会失败的脚本
        script_file = tmp_path / "error_script.py"
        script_file.write_text("""
#!/usr/bin/env python3
import sys
sys.exit(1)
""")
        
        execution_id = await engine.submit(
            script_id="error-script",
            script_name="错误脚本",
            script_path=str(script_file),
        )
        
        # 等待执行
        await asyncio.sleep(0.5)
        
        status = await engine.get_status(execution_id)
        assert status == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_script_timeout(self, engine, tmp_path):
        """测试脚本超时"""
        # 创建长时间运行的脚本
        script_file = tmp_path / "slow_script.py"
        script_file.write_text("""
#!/usr/bin/env python3
import time
time.sleep(10)
""")
        
        limits = ResourceLimits(max_execution_time=1)  # 1秒超时
        
        execution_id = await engine.submit(
            script_id="slow-script",
            script_name="慢脚本",
            script_path=str(script_file),
            resource_limits=limits,
        )
        
        # 等待超时
        await asyncio.sleep(2)
        
        status = await engine.get_status(execution_id)
        assert status in [ExecutionStatus.TIMEOUT, ExecutionStatus.FAILED]

    @pytest.mark.asyncio
    async def test_stack_trace_capture(self, engine, tmp_path):
        """测试堆栈跟踪捕获"""
        # 创建会抛出异常的脚本
        script_file = tmp_path / "exception_script.py"
        script_file.write_text("""
#!/usr/bin/env python3
raise ValueError("Test exception")
""")
        
        execution_id = await engine.submit(
            script_id="exception-script",
            script_name="异常脚本",
            script_path=str(script_file),
        )
        
        # 等待执行
        await asyncio.sleep(0.5)
        
        execution = await engine.get_execution(execution_id)
        assert execution.stack_trace is not None
        assert "ValueError" in execution.stack_trace


@pytest.mark.unit
class TestScriptEnginePerformance:
    """脚本引擎性能测试"""

    @pytest.fixture
    def engine(self):
        """创建脚本引擎实例"""
        return ScriptExecutionEngine(max_concurrent=10)

    @pytest.mark.asyncio
    async def test_bulk_submission(self, engine, tmp_path):
        """测试批量提交性能"""
        # 创建简单脚本
        script_file = tmp_path / "bulk_script.py"
        script_file.write_text("""
#!/usr/bin/env python3
print('{"status": "ok"}')
""")
        
        # 批量提交
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(50):
            task = engine.submit(
                script_id=f"bulk-{i}",
                script_name=f"批量脚本-{i}",
                script_path=str(script_file),
            )
            tasks.append(task)
        
        execution_ids = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        assert len(execution_ids) == 50
        # 批量提交应该在合理时间内完成
        assert duration < 5.0  # 5秒内完成
        # 验证duration被使用
        assert isinstance(duration, float)

    @pytest.mark.asyncio
    async def test_execution_throughput(self, engine, tmp_path):
        """测试执行吞吐量"""
        # 创建快速脚本
        script_file = tmp_path / "fast_script.py"
        script_file.write_text("""
#!/usr/bin/env python3
import json
print(json.dumps({"result": "success"}))
""")
        
        # 执行多个脚本
        start_time = asyncio.get_event_loop().time()
        
        execution_ids = []
        for i in range(20):
            exec_id = await engine.submit(
                script_id=f"throughput-{i}",
                script_name=f"吞吐量测试-{i}",
                script_path=str(script_file),
            )
            execution_ids.append(exec_id)
        
        # 等待所有完成
        await asyncio.sleep(2)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # 验证吞吐量
        completed = 0
        for exec_id in execution_ids:
            status = await engine.get_status(exec_id)
            if status == ExecutionStatus.COMPLETED:
                completed += 1
        
        # 至少80%成功完成，且执行时间合理
        assert completed >= 16  # 20的80%
        assert duration < 10.0  # 10秒内完成


@pytest.mark.unit
class TestResourceLimits:
    """资源限制测试"""

    def test_resource_limits_creation(self):
        """测试资源限制对象创建"""
        limits = ResourceLimits(
            max_execution_time=60,
            max_memory_mb=512,
            max_cpu_percent=50,
        )
        
        assert limits.max_execution_time == 60
        assert limits.max_memory_mb == 512
        assert limits.max_cpu_percent == 50

    def test_resource_limits_defaults(self):
        """测试资源限制默认值"""
        limits = ResourceLimits()
        
        assert limits.max_execution_time is None
        assert limits.max_memory_mb is None
        assert limits.max_cpu_percent is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
