"""
【文件功能】监控数据历史查询API
实现监控历史数据的查询、聚合和导出功能

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现监控历史查询核心功能

【依赖说明】
- 标准库: datetime, typing
- 第三方库: fastapi, pydantic
- 内部模块: app.services.metrics_storage, app.models.alert

【使用示例】
```python
from app.routes.v1.metrics_history import router

# 在FastAPI应用中注册
app.include_router(router, prefix="/api/v1")
```
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.services.metrics_storage import metrics_storage
from app.models.alert import MetricType

router = APIRouter(prefix="/metrics", tags=["监控数据历史"])


class MetricsHistoryResponse(BaseModel):
    """【监控历史响应】"""
    success: bool = Field(..., description="是否成功")
    data: List[Dict[str, Any]] = Field(..., description="历史数据")
    total: int = Field(..., description="总数")
    message: str = Field(default="查询成功", description="响应消息")


class MetricsAggregateResponse(BaseModel):
    """【监控聚合响应】"""
    success: bool = Field(..., description="是否成功")
    data: List[Dict[str, Any]] = Field(..., description="聚合数据")
    message: str = Field(default="聚合成功", description="响应消息")


class StorageStatsResponse(BaseModel):
    """【存储统计响应】"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="统计信息")
    message: str = Field(default="获取统计成功", description="响应消息")


class ExportRequest(BaseModel):
    """【导出请求】"""
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    format: str = Field(default="json", description="导出格式（json/csv）")
    metric_type: Optional[str] = Field(None, description="指标类型筛选")


@router.get("/history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    metric_type: Optional[str] = Query(None, description="指标类型筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间（ISO格式）"),
    end_time: Optional[datetime] = Query(None, description="结束时间（ISO格式）"),
    days: int = Query(7, ge=1, le=90, description="查询最近N天"),
    limit: int = Query(1000, ge=1, le=10000, description="返回数量限制")
):
    """
    【获取监控历史数据】查询指定时间范围的监控历史
    
    【参数说明】
    - metric_type: 指标类型（cpu/memory/disk/network/load/process/custom）
    - start_time: 开始时间（ISO格式，如 2026-02-01T00:00:00）
    - end_time: 结束时间（ISO格式，如 2026-02-08T23:59:59）
    - days: 查询最近N天（如果未指定start_time/end_time）
    - limit: 返回数量限制（默认1000，最大10000）
    
    【返回值】
    - success: 是否成功
    - data: 历史数据列表
    - total: 总数
    - message: 响应消息
    
    【使用示例】
    ```
    GET /api/v1/metrics/history?metric_type=cpu&days=7&limit=100
    ```
    """
    try:
        # 处理时间范围
        if not start_time or not end_time:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
        
        # 验证指标类型
        if metric_type:
            try:
                MetricType(metric_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的指标类型: {metric_type}。有效值: {[t.value for t in MetricType]}"
                )
        
        # 查询数据
        data = await metrics_storage.query_history(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return MetricsHistoryResponse(
            success=True,
            data=data,
            total=len(data),
            message=f"成功查询到 {len(data)} 条记录"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/history/aggregate", response_model=MetricsAggregateResponse)
async def get_metrics_aggregate(
    metric_type: str = Query(..., description="指标类型（必填）"),
    aggregation: str = Query("avg", description="聚合方式（avg/max/min/sum/count）"),
    interval: str = Query("hour", description="时间间隔（hour/day）"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    days: int = Query(7, ge=1, le=90, description="查询最近N天")
):
    """
    【获取聚合监控数据】按时间间隔聚合监控数据
    
    【参数说明】
    - metric_type: 指标类型（必填）
    - aggregation: 聚合方式（avg-平均值/max-最大值/min-最小值/sum-求和/count-计数）
    - interval: 时间间隔（hour-小时/day-天）
    - start_time: 开始时间
    - end_time: 结束时间
    - days: 查询最近N天
    
    【返回值】
    - success: 是否成功
    - data: 聚合数据列表，包含timestamp/value/count等字段
    
    【使用示例】
    ```
    GET /api/v1/metrics/history/aggregate?metric_type=cpu&aggregation=avg&interval=hour&days=1
    ```
    """
    try:
        # 验证指标类型
        try:
            MetricType(metric_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的指标类型: {metric_type}"
            )
        
        # 验证聚合方式
        valid_aggregations = ["avg", "max", "min", "sum", "count"]
        if aggregation not in valid_aggregations:
            raise HTTPException(
                status_code=400,
                detail=f"无效的聚合方式: {aggregation}。有效值: {valid_aggregations}"
            )
        
        # 验证时间间隔
        valid_intervals = ["hour", "day"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"无效的时间间隔: {interval}。有效值: {valid_intervals}"
            )
        
        # 处理时间范围
        if not start_time or not end_time:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
        
        # 聚合查询
        data = await metrics_storage.aggregate(
            metric_type=metric_type,
            aggregation=aggregation,
            interval=interval,
            start_time=start_time,
            end_time=end_time
        )
        
        return MetricsAggregateResponse(
            success=True,
            data=data,
            message=f"成功聚合 {len(data)} 个时间点"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚合查询失败: {str(e)}")


@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_statistics():
    """
    【获取存储统计】获取监控数据存储的统计信息
    
    【返回值】
    - total_stored: 总存储记录数
    - total_archived: 已归档记录数
    - storage_size_bytes: 存储大小（字节）
    - storage_size_mb: 存储大小（MB）
    - file_count: 文件数量
    - earliest_date: 最早数据日期
    - latest_date: 最新数据日期
    - last_cleanup: 最后清理时间
    """
    try:
        stats = metrics_storage.get_storage_stats()
        
        return StorageStatsResponse(
            success=True,
            data=stats,
            message="获取存储统计成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/storage/cleanup")
async def cleanup_storage():
    """
    【清理存储】清理过期数据并归档
    
    【返回值】
    - success: 是否成功
    - archived_files: 归档文件数
    - deleted_files: 删除文件数
    - errors: 错误信息列表
    """
    try:
        result = await metrics_storage.cleanup_old_data()
        
        return {
            "success": True,
            "data": result,
            "message": f"清理完成：归档 {result['archived_files']} 个文件"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/export")
async def export_metrics(
    start_time: datetime = Query(..., description="开始时间（ISO格式）"),
    end_time: datetime = Query(..., description="结束时间（ISO格式）"),
    format: str = Query("json", description="导出格式（json/csv）"),
    metric_type: Optional[str] = Query(None, description="指标类型筛选")
):
    """
    【导出监控数据】导出指定时间范围的监控数据
    
    【参数说明】
    - start_time: 开始时间（必填）
    - end_time: 结束时间（必填）
    - format: 导出格式（json/csv）
    - metric_type: 指标类型筛选（可选）
    
    【返回值】
    - 文件下载（Content-Disposition: attachment）
    
    【使用示例】
    ```
    GET /api/v1/metrics/export?start_time=2026-02-01T00:00:00&end_time=2026-02-08T23:59:59&format=csv&metric_type=cpu
    ```
    """
    try:
        # 验证时间范围
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="结束时间必须大于开始时间")
        
        # 限制导出范围（最多30天）
        if (end_time - start_time).days > 30:
            raise HTTPException(status_code=400, detail="导出时间范围不能超过30天")
        
        # 验证格式
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="格式必须是 json 或 csv")
        
        # 导出数据
        filename, content = await metrics_storage.export_data(
            start_time=start_time,
            end_time=end_time,
            format=format,
            metric_type=metric_type
        )
        
        # 设置响应头
        from fastapi.responses import Response
        
        media_type = "application/json" if format == "json" else "text/csv"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/types", response_model=Dict[str, Any])
async def get_metric_types():
    """
    【获取指标类型】获取所有支持的监控指标类型
    
    【返回值】
    - 指标类型列表，包含名称和描述
    """
    types = []
    for metric_type in MetricType:
        descriptions = {
            "cpu": "CPU使用率",
            "memory": "内存使用率",
            "disk": "磁盘使用率",
            "network": "网络IO",
            "load": "系统负载",
            "process": "进程资源",
            "custom": "自定义指标"
        }
        
        types.append({
            "value": metric_type.value,
            "name": descriptions.get(metric_type.value, metric_type.value),
            "description": f"{descriptions.get(metric_type.value, metric_type.value)}监控"
        })
    
    return {
        "success": True,
        "data": types,
        "message": "获取指标类型成功"
    }


@router.get("/latest", response_model=MetricsHistoryResponse)
async def get_latest_metrics(
    metric_type: Optional[str] = Query(None, description="指标类型筛选"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量")
):
    """
    【获取最新监控数据】获取最近的监控数据
    
    【参数说明】
    - metric_type: 指标类型筛选
    - limit: 返回数量（默认100，最大1000）
    
    【返回值】
    - 最新的监控数据列表
    """
    try:
        # 查询最近1小时的数据
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        data = await metrics_storage.query_history(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return MetricsHistoryResponse(
            success=True,
            data=data,
            total=len(data),
            message=f"获取到 {len(data)} 条最新记录"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
