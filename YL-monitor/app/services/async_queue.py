"""
异步队列服务

功能:
- 任务队列管理
- 异步任务执行
- 任务状态跟踪
- 优先级队列支持
- 批量操作支持

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Coroutine
from functools import wraps
import heapq

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskPriority(int, Enum):
    """任务优先级"""
    CRITICAL = 0    # 紧急
    HIGH = 1        # 高
    NORMAL = 2      # 正常
    LOW = 3         # 低
    BACKGROUND = 4  # 后台


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"       # 等待中
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消
    TIMEOUT = "timeout"       # 超时


@dataclass
class TaskResult:
    """任务结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0  # 毫秒


@dataclass
class AsyncTask:
    """异步任务"""
    id: str
    name: str
    func: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[TaskResult] = None
    max_retries: int = 3
    retry_count: int = 0
    timeout: float = 300.0  # 默认5分钟超时
    
    def __lt__(self, other: 'AsyncTask') -> bool:
        """用于优先级队列比较"""
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": {
                "success": self.result.success if self.result else None,
                "error": self.result.error if self.result else None,
                "execution_time": self.result.execution_time if self.result else None,
            } if self.result else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


class AsyncQueue:
    """
    异步队列
    
    支持优先级、并发控制、任务状态跟踪
    """
    
    def __init__(
        self,
        max_workers: int = 5,
        max_queue_size: int = 1000
    ):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # 任务队列 (使用堆实现优先级队列)
        self._queue: List[AsyncTask] = []
        self._queue_lock = asyncio.Lock()
        
        # 任务存储
        self._tasks: Dict[str, AsyncTask] = {}
        self._task_lock = asyncio.Lock()
        
        # 工作信号量
        self._semaphore = asyncio.Semaphore(max_workers)
        
        # 运行状态
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        # 统计
        self._stats = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
    
    async def start(self):
        """启动队列处理器"""
        if self._running:
            return
        
        self._running = True
        self._worker_tasks = [
            asyncio.create_task(self._worker_loop())
            for _ in range(self.max_workers)
        ]
        logger.info(f"异步队列已启动: {self.max_workers} 个工作者")
    
    async def stop(self, wait: bool = True, timeout: float = 30.0):
        """停止队列处理器"""
        if not self._running:
            return
        
        self._running = False
        
        if wait:
            # 等待所有任务完成或超时
            try:
                await asyncio.wait_for(
                    self._wait_for_empty(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning("队列停止超时，强制取消剩余任务")
        
        # 取消工作者
        for task in self._worker_tasks:
            task.cancel()
        
        self._worker_tasks = []
        logger.info("异步队列已停止")
    
    async def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        name: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 300.0,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        提交任务到队列
        
        返回任务ID
        """
        task_id = str(uuid.uuid4())
        task_name = name or func.__name__
        
        task = AsyncTask(
            id=task_id,
            name=task_name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        
        async with self._queue_lock:
            if len(self._queue) >= self.max_queue_size:
                raise QueueFullError(f"队列已满: {self.max_queue_size}")
            
            heapq.heappush(self._queue, task)
            self._stats["submitted"] += 1
        
        async with self._task_lock:
            self._tasks[task_id] = task
        
        logger.debug(f"任务已提交: {task_name} (ID: {task_id}, 优先级: {priority.name})")
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[AsyncTask]:
        """获取任务信息"""
        async with self._task_lock:
            return self._tasks.get(task_id)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = await self.get_task(task_id)
        return task.status if task else None
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING]:
            task.status = TaskStatus.CANCELLED
            self._stats["cancelled"] += 1
            logger.info(f"任务已取消: {task.name} (ID: {task_id})")
            return True
        
        return False  # 运行中的任务无法取消
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._queue_lock:
            queue_size = len(self._queue)
        
        async with self._task_lock:
            running = sum(
                1 for t in self._tasks.values()
                if t.status == TaskStatus.RUNNING
            )
            pending = sum(
                1 for t in self._tasks.values()
                if t.status == TaskStatus.PENDING
            )
        
        return {
            **self._stats,
            "queue_size": queue_size,
            "running": running,
            "pending": pending,
            "max_workers": self.max_workers,
        }
    
    async def _worker_loop(self):
        """工作者循环"""
        while self._running:
            try:
                # 获取任务
                task = await self._get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # 执行任务
                async with self._semaphore:
                    await self._execute_task(task)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作者循环错误: {e}")
                await asyncio.sleep(1)
    
    async def _get_next_task(self) -> Optional[AsyncTask]:
        """获取下一个任务"""
        async with self._queue_lock:
            if not self._queue:
                return None
            
            task = heapq.heappop(self._queue)
            
            # 检查是否已取消
            if task.status == TaskStatus.CANCELLED:
                return None
            
            return task
    
    async def _execute_task(self, task: AsyncTask):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # 设置超时
            result = await asyncio.wait_for(
                task.func(*task.args, **task.kwargs),
                timeout=task.timeout
            )
            
            # 成功完成
            execution_time = (time.time() - task.started_at) * 1000
            task.result = TaskResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            self._stats["completed"] += 1
            
            logger.debug(
                f"任务完成: {task.name} (ID: {task.id}, "
                f"耗时: {execution_time:.2f}ms)"
            )
            
        except asyncio.TimeoutError:
            await self._handle_task_timeout(task)
        except Exception as e:
            await self._handle_task_error(task, e)
    
    async def _handle_task_timeout(self, task: AsyncTask):
        """处理任务超时"""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # 重新入队
            task.status = TaskStatus.PENDING
            async with self._queue_lock:
                heapq.heappush(self._queue, task)
            logger.warning(
                f"任务超时重试: {task.name} (ID: {task.id}, "
                f"重试: {task.retry_count}/{task.max_retries})"
            )
        else:
            task.status = TaskStatus.TIMEOUT
            task.result = TaskResult(
                success=False,
                error="任务执行超时",
                execution_time=task.timeout * 1000
            )
            task.completed_at = time.time()
            self._stats["failed"] += 1
            logger.error(f"任务超时失败: {task.name} (ID: {task.id})")
    
    async def _handle_task_error(self, task: AsyncTask, error: Exception):
        """处理任务错误"""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # 重新入队
            task.status = TaskStatus.PENDING
            async with self._queue_lock:
                heapq.heappush(self._queue, task)
            logger.warning(
                f"任务错误重试: {task.name} (ID: {task.id}, "
                f"错误: {error}, 重试: {task.retry_count}/{task.max_retries})"
            )
        else:
            task.status = TaskStatus.FAILED
            task.result = TaskResult(
                success=False,
                error=str(error),
                execution_time=(time.time() - task.started_at) * 1000
            )
            task.completed_at = time.time()
            self._stats["failed"] += 1
            logger.error(f"任务失败: {task.name} (ID: {task.id}, 错误: {error})")
    
    async def _wait_for_empty(self):
        """等待队列为空"""
        while True:
            async with self._queue_lock:
                if not self._queue:
                    return
            await asyncio.sleep(0.1)


class QueueFullError(Exception):
    """队列已满错误"""
    pass


# 全局队列实例
_global_queue: Optional[AsyncQueue] = None


def get_async_queue() -> AsyncQueue:
    """获取全局异步队列"""
    global _global_queue
    if _global_queue is None:
        _global_queue = AsyncQueue()
    return _global_queue


def set_async_queue(queue: AsyncQueue):
    """设置全局异步队列"""
    global _global_queue
    _global_queue = queue


# 装饰器支持
def async_task(
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: float = 300.0,
    max_retries: int = 3,
    queue: Optional[AsyncQueue] = None
):
    """
    异步任务装饰器
    
    用法:
        @async_task(priority=TaskPriority.HIGH)
        async def send_email(to, subject, body):
            ...
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, str]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> str:
            q = queue or get_async_queue()
            return await q.submit(
                func,
                *args,
                name=func.__name__,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                **kwargs
            )
        return wrapper
    return decorator


# 批量操作支持
class BatchProcessor:
    """批量处理器"""
    
    def __init__(
        self,
        batch_size: int = 100,
        max_concurrency: int = 5
    ):
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
    
    async def process(
        self,
        items: List[T],
        processor: Callable[[List[T]], Coroutine[Any, Any, List[Any]]],
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        批量处理项目
        
        Args:
            items: 待处理项目列表
            processor: 处理函数，接收一批项目，返回结果
            on_progress: 进度回调函数 (当前数量, 总数)
        
        Returns:
            所有处理结果
        """
        results = []
        total = len(items)
        processed = 0
        
        # 分割批次
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        # 并发控制
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def process_batch(batch: List[T]) -> List[Any]:
            async with semaphore:
                try:
                    return await processor(batch)
                except Exception as e:
                    logger.error(f"批次处理失败: {e}")
                    raise
        
        # 处理所有批次
        tasks = [process_batch(batch) for batch in batches]
        
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                batch_results = await task
                results.extend(batch_results)
                processed += len(batches[i])
                
                if on_progress:
                    on_progress(processed, total)
                    
            except Exception as e:
                logger.error(f"批次 {i+1} 处理失败: {e}")
                raise
        
        return results


# 常用异步任务类型
class CommonAsyncTasks:
    """常用异步任务"""
    
    @staticmethod
    async def send_notification(
        channel: str,
        message: str,
        recipients: List[str]
    ) -> bool:
        """发送通知"""
        # 实际实现中调用对应的服务
        logger.info(f"发送通知: {channel} -> {recipients}")
        await asyncio.sleep(0.1)  # 模拟延迟
        return True
    
    @staticmethod
    async def send_email(
        to: List[str],
        subject: str,
        body: str
    ) -> bool:
        """发送邮件"""
        from app.services.email_service import EmailService
        
        service = EmailService()
        try:
            await service.send_alert_email(subject, body, to)
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    @staticmethod
    async def call_webhook(
        url: str,
        payload: Dict[str, Any]
    ) -> bool:
        """调用Webhook"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Webhook调用失败: {e}")
            return False
    
    @staticmethod
    async def process_large_data(
        data: List[Dict[str, Any]],
        processor: Callable[[Dict[str, Any]], Any]
    ) -> List[Any]:
        """处理大数据"""
        batch_processor = BatchProcessor(batch_size=100)
        return await batch_processor.process(
            data,
            lambda batch: [processor(item) for item in batch]
        )


# 任务状态查询API (用于路由集成)
async def get_task_status_api(task_id: str) -> Dict[str, Any]:
    """获取任务状态API"""
    queue = get_async_queue()
    task = await queue.get_task(task_id)
    
    if not task:
        return {
            "success": False,
            "error": "任务不存在",
            "task_id": task_id
        }
    
    return {
        "success": True,
        "task": task.to_dict()
    }


async def get_queue_stats_api() -> Dict[str, Any]:
    """获取队列统计API"""
    queue = get_async_queue()
    stats = await queue.get_stats()
    
    return {
        "success": True,
        "stats": stats
    }
