"""
任务状态查询路由

功能:
- 查询异步任务状态
- 获取队列统计信息
- 取消待执行任务
- 批量任务查询

作者: AI Assistant
版本: 1.0.0
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.async_queue import (
    get_async_queue,
    AsyncQueue,
    TaskStatus,
    TaskPriority,
    get_task_status_api,
    get_queue_stats_api
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["异步任务"])


# 响应模型
class TaskResultInfo(BaseModel):
    """任务结果信息"""
    success: Optional[bool] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None  # 毫秒


class TaskInfo(BaseModel):
    """任务信息"""
    id: str
    name: str
    priority: int
    status: str
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[TaskResultInfo] = None
    retry_count: int
    max_retries: int


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    success: bool
    task: Optional[TaskInfo] = None
    error: Optional[str] = None
    task_id: str


class QueueStats(BaseModel):
    """队列统计"""
    submitted: int
    completed: int
    failed: int
    cancelled: int
    queue_size: int
    running: int
    pending: int
    max_workers: int


class QueueStatsResponse(BaseModel):
    """队列统计响应"""
    success: bool
    stats: QueueStats


class TaskListResponse(BaseModel):
    """任务列表响应"""
    success: bool
    tasks: List[TaskInfo]
    total: int


class CancelTaskResponse(BaseModel):
    """取消任务响应"""
    success: bool
    cancelled: bool
    message: str
    task_id: str


# 获取队列实例
def get_queue() -> AsyncQueue:
    """获取异步队列实例"""
    return get_async_queue()


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    查询指定异步任务的执行状态和结果
    """
    try:
        result = await get_task_status_api(task_id)
        return TaskStatusResponse(**result)
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_statistics():
    """
    获取队列统计信息
    
    返回异步队列的整体统计信息
    """
    try:
        result = await get_queue_stats_api()
        return QueueStatsResponse(**result)
    except Exception as e:
        logger.error(f"获取队列统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{task_id}", response_model=CancelTaskResponse)
async def cancel_task(task_id: str):
    """
    取消任务
    
    取消处于等待状态的任务，运行中的任务无法取消
    """
    try:
        queue = get_queue()
        cancelled = await queue.cancel_task(task_id)
        
        if cancelled:
            return CancelTaskResponse(
                success=True,
                cancelled=True,
                message="任务已成功取消",
                task_id=task_id
            )
        else:
            # 检查任务是否存在
            task = await queue.get_task(task_id)
            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: {task_id}"
                )
            
            return CancelTaskResponse(
                success=True,
                cancelled=False,
                message=f"任务无法取消，当前状态: {task.status.value}",
                task_id=task_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取任务列表
    
    支持按状态筛选和分页
    """
    try:
        queue = get_queue()
        
        # 获取所有任务
        all_tasks = []
        async with queue._task_lock:
            for task in queue._tasks.values():
                # 状态筛选
                if status and task.status.value != status:
                    continue
                all_tasks.append(task)
        
        # 按创建时间倒序排序
        all_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # 分页
        total = len(all_tasks)
        paginated_tasks = all_tasks[offset:offset + limit]
        
        # 转换为响应模型
        task_infos = []
        for task in paginated_tasks:
            task_info = TaskInfo(
                id=task.id,
                name=task.name,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                result=TaskResultInfo(
                    success=task.result.success if task.result else None,
                    error=task.result.error if task.result else None,
                    execution_time=task.result.execution_time if task.result else None
                ) if task.result else None,
                retry_count=task.retry_count,
                max_retries=task.max_retries
            )
            task_infos.append(task_info)
        
        return TaskListResponse(
            success=True,
            tasks=task_infos,
            total=total
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status-enum")
async def get_task_status_enum():
    """
    获取任务状态枚举值
    
    返回所有可用的任务状态值
    """
    return {
        "success": True,
        "statuses": [
            {"value": s.value, "label": s.name}
            for s in TaskStatus
        ]
    }


@router.get("/priority-enum")
async def get_task_priority_enum():
    """
    获取任务优先级枚举值
    
    返回所有可用的任务优先级值
    """
    return {
        "success": True,
        "priorities": [
            {"value": p.value, "label": p.name}
            for p in TaskPriority
        ]
    }


# 健康检查
@router.get("/health")
async def health_check():
    """队列健康检查"""
    try:
        queue = get_queue()
        stats = await queue.get_stats()
        
        # 检查队列状态
        is_healthy = (
            stats["queue_size"] < queue.max_queue_size * 0.9 and
            stats["failed"] < stats["submitted"] * 0.1  # 失败率 < 10%
        )
        
        return {
            "success": True,
            "healthy": is_healthy,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }
