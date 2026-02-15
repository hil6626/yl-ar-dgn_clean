#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步队列服务单元测试

【功能描述】
测试异步队列服务的核心功能，包括：
- 任务提交和执行
- 队列管理
- 优先级处理
- 错误处理和重试

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0
"""

import pytest
import pytest_asyncio
import asyncio
import time

# 导入被测试的模块
from app.services.async_queue import (
    AsyncQueue,
    AsyncTask,
    TaskStatus,
    TaskPriority,
    TaskResult,
    QueueFullError,
)


@pytest.mark.unit
class TestAsyncTask:
    """异步任务类测试"""

    def test_task_creation(self):
        """测试任务创建"""
        async def sample_func():
            return "result"
        
        task = AsyncTask(
            id="task-001",
            name="测试任务",
            func=sample_func,
            args=(),
            kwargs={},
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            created_at=time.time(),
        )
        
        assert task.id == "task-001"
        assert task.name == "测试任务"
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING

    def test_task_priority_comparison(self):
        """测试任务优先级比较"""
        async def dummy_func():
            pass
        
        high_task = AsyncTask(
            id="high",
            name="高优先级",
            func=dummy_func,
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            created_at=time.time(),
        )
        
        low_task = AsyncTask(
            id="low",
            name="低优先级",
            func=dummy_func,
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            created_at=time.time(),
        )
        
        # 高优先级应该小于低优先级（数值越小优先级越高）
        assert high_task < low_task

    def test_task_to_dict(self):
        """测试任务转换为字典"""
        async def dummy_func():
            pass
        
        task = AsyncTask(
            id="task-001",
            name="测试任务",
            func=dummy_func,
            priority=TaskPriority.NORMAL,
            status=TaskStatus.COMPLETED,
            created_at=time.time(),
        )
        task.result = TaskResult(success=True, data="test")
        
        data = task.to_dict()
        assert data["id"] == "task-001"
        assert data["name"] == "测试任务"
        assert data["status"] == "completed"


@pytest.mark.unit
class TestAsyncQueue:
    """异步队列测试"""

    @pytest_asyncio.fixture
    async def queue(self):
        """创建队列实例"""
        q = AsyncQueue(max_workers=3)
        await q.start()
        yield q
        await q.stop()

    @pytest.mark.asyncio
    async def test_submit_task(self, queue):
        """测试提交任务"""
        async def sample_task():
            return "success"
        
        task_id = await queue.submit(
            sample_task,
            name="sample",
            priority=TaskPriority.NORMAL,
        )
        
        assert task_id is not None
        assert isinstance(task_id, str)

    @pytest.mark.asyncio
    async def test_get_task(self, queue):
        """测试获取任务"""
        async def sample_task():
            return "done"
        
        task_id = await queue.submit(
            sample_task,
            name="test-task",
        )
        
        task = await queue.get_task(task_id)
        assert task is not None
        assert task.id == task_id
        assert task.name == "test-task"

    @pytest.mark.asyncio
    async def test_get_task_status(self, queue):
        """测试获取任务状态"""
        async def sample_task():
            await asyncio.sleep(0.1)
            return "done"
        
        task_id = await queue.submit(
            sample_task,
            name="status-test",
        )
        
        # 初始状态应该是PENDING或RUNNING
        status = await queue.get_task_status(task_id)
        assert status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        
        # 等待完成
        await asyncio.sleep(0.3)
        status = await queue.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_task_execution(self, queue):
        """测试任务执行"""
        result_container = {}
        
        async def sample_task():
            result_container["executed"] = True
            return "done"
        
        task_id = await queue.submit(
            sample_task,
            name="exec-test",
        )
        
        # 等待任务执行
        await asyncio.sleep(0.3)
        
        # 获取任务并验证结果
        task = await queue.get_task(task_id)
        assert task.result is not None
        assert task.result.success is True
        assert task.result.data == "done"
        assert result_container.get("executed") is True

    @pytest.mark.asyncio
    async def test_task_priority(self, queue):
        """测试任务优先级"""
        execution_order = []
        
        async def make_task(name):
            async def task():
                execution_order.append(name)
                return name
            return task
        
        # 提交低优先级任务（先提交）
        low_func = await make_task("low")
        await queue.submit(
            low_func,
            name="low",
            priority=TaskPriority.LOW,
        )
        
        # 提交高优先级任务（后提交）
        high_func = await make_task("high")
        await queue.submit(
            high_func,
            name="high",
            priority=TaskPriority.HIGH,
        )
        
        # 等待执行
        await asyncio.sleep(0.3)
        
        # 高优先级应该先执行
        assert execution_order[0] == "high"

    @pytest.mark.asyncio
    async def test_cancel_task(self, queue):
        """测试任务取消"""
        async def long_task():
            await asyncio.sleep(10)
            return "completed"
        
        task_id = await queue.submit(
            long_task,
            name="long",
        )
        
        # 取消任务
        cancelled = await queue.cancel_task(task_id)
        assert cancelled is True
        
        # 验证状态
        status = await queue.get_task_status(task_id)
        assert status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_queue_stats(self, queue):
        """测试队列统计"""
        # 提交一些任务
        for i in range(5):
            await queue.submit(
                lambda: f"result-{i}",
                name=f"task-{i}",
            )
        
        stats = await queue.get_stats()
        
        assert isinstance(stats, dict)
        assert "submitted" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert "queue_size" in stats

    @pytest.mark.asyncio
    async def test_task_retry_on_error(self, queue):
        """测试错误重试"""
        attempt_count = [0]
        
        async def failing_task():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise RuntimeError("Failed")
            return "success"
        
        task_id = await queue.submit(
            failing_task,
            name="retry-test",
            max_retries=3,
        )
        
        # 等待重试完成
        await asyncio.sleep(0.5)
        
        # 获取任务
        task = await queue.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result.success is True

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, queue):
        """测试超过最大重试次数"""
        async def always_fails():
            raise RuntimeError("Always fails")
        
        task_id = await queue.submit(
            always_fails,
            name="fail-test",
            max_retries=2,
        )
        
        # 等待重试完成
        await asyncio.sleep(0.5)
        
        # 获取任务
        task = await queue.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.result.success is False

    @pytest.mark.asyncio
    async def test_task_timeout(self, queue):
        """测试任务超时"""
        async def slow_task():
            await asyncio.sleep(10)
            return "completed"
        
        task_id = await queue.submit(
            slow_task,
            name="timeout-test",
            timeout=0.5,
            max_retries=0,  # 禁用重试，确保超时后状态正确
        )
        
        # 等待超时（考虑重试等待时间）
        await asyncio.sleep(2)
        
        # 获取任务
        task = await queue.get_task(task_id)
        # 任务可能处于TIMEOUT或FAILED状态（取决于实现）
        assert task.status in [TaskStatus.TIMEOUT, TaskStatus.FAILED]
        assert task.result is not None
        assert task.result.success is False

    @pytest.mark.asyncio
    async def test_queue_full_error(self, queue):
        """测试队列已满错误"""
        # 设置小队列
        queue.max_queue_size = 2
        
        async def slow_task():
            await asyncio.sleep(5)
            return "done"
        
        # 填满队列
        await queue.submit(slow_task, name="task-1")
        await queue.submit(slow_task, name="task-2")
        
        # 第三个应该失败
        with pytest.raises(QueueFullError):
            await queue.submit(slow_task, name="task-3")


@pytest.mark.unit
class TestQueueEdgeCases:
    """队列边界情况测试"""

    @pytest_asyncio.fixture
    async def queue(self):
        """创建队列实例"""
        q = AsyncQueue(max_workers=2)
        await q.start()
        yield q
        await q.stop()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, queue):
        """测试取消不存在的任务"""
        cancelled = await queue.cancel_task("nonexistent")
        assert cancelled is False

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, queue):
        """测试获取不存在的任务"""
        task = await queue.get_task("nonexistent")
        assert task is None
        
        status = await queue.get_task_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_task_with_exception(self, queue):
        """测试抛出异常的任务"""
        async def error_task():
            raise ValueError("Test error")
        
        task_id = await queue.submit(
            error_task,
            name="error-task",
        )
        
        # 等待执行
        await asyncio.sleep(0.3)
        
        # 获取任务
        task = await queue.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.result.success is False
        assert "Test error" in task.result.error

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """测试启动和停止"""
        queue = AsyncQueue(max_workers=2)
        
        # 初始状态
        assert queue._running is False
        
        # 启动
        await queue.start()
        assert queue._running is True
        
        # 停止
        await queue.stop()
        assert queue._running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
