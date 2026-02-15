"""
系统指标 API 路由

功能:
- 获取实时系统指标
- 查询历史指标数据
- 指标统计汇总

作者: AI Assistant
版本: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.metrics_service import get_metrics_service


router = APIRouter(prefix="/metrics", tags=["Metrics"])


def _get_service(request: Request):
    """获取指标服务实例"""
    return get_metrics_service()


@router.get("/realtime")
async def get_realtime_metrics(request: Request):
    """
    获取实时系统指标

    返回当前最新的系统指标数据，包括 CPU、内存、磁盘、网络等信息
    """
    service = _get_service(request)
    metrics = service.get_current_metrics()

    return {
        "success": True,
        "data": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/history")
async def get_metrics_history(
    request: Request,
    hours: int = Query(1, ge=1, le=24, description="查询最近几小时的数据"),
    limit: int = Query(100, ge=1, le=1000, description="返回数据点数量限制")
):
    """
    获取历史指标数据

    支持按时间范围查询历史指标数据
    """
    service = _get_service(request)

    start_time = datetime.utcnow() - timedelta(hours=hours)
    history = service.get_metrics_history(
        start_time=start_time,
        limit=limit
    )

    return {
        "success": True,
        "data": history,
        "count": len(history),
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/summary")
async def get_metrics_summary(
    request: Request,
    hours: int = Query(1, ge=1, le=24, description="统计时间范围（小时）")
):
    """
    获取指标统计汇总

    返回指定时间范围内的指标统计信息（最小值、最大值、平均值、当前值）
    """
    service = _get_service(request)
    summary = service.get_metrics_summary(hours=hours)

    if not summary:
        raise HTTPException(status_code=404, detail="暂无指标数据")

    return {
        "success": True,
        "data": summary,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/cpu")
async def get_cpu_metrics(request: Request, hours: int = Query(1, ge=1, le=24)):
    """
    获取 CPU 指标历史
    """
    service = _get_service(request)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    history = service.get_metrics_history(start_time=start_time)

    cpu_data = [
        {
            "timestamp": m["timestamp"],
            "value": m["cpu"]["percent"],
            "count": m["cpu"]["count"],
            "freq": m["cpu"]["freq_current"]
        }
        for m in history
    ]

    return {
        "success": True,
        "data": cpu_data,
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/memory")
async def get_memory_metrics(request: Request, hours: int = Query(1, ge=1, le=24)):
    """
    获取内存指标历史
    """
    service = _get_service(request)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    history = service.get_metrics_history(start_time=start_time)

    memory_data = [
        {
            "timestamp": m["timestamp"],
            "percent": m["memory"]["percent"],
            "used_gb": m["memory"]["used_gb"],
            "total_gb": m["memory"]["total_gb"],
            "available_gb": m["memory"]["available_gb"]
        }
        for m in history
    ]

    return {
        "success": True,
        "data": memory_data,
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/disk")
async def get_disk_metrics(request: Request, hours: int = Query(1, ge=1, le=24)):
    """
    获取磁盘指标历史
    """
    service = _get_service(request)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    history = service.get_metrics_history(start_time=start_time)

    disk_data = [
        {
            "timestamp": m["timestamp"],
            "percent": m["disk"]["percent"],
            "used_gb": m["disk"]["used_gb"],
            "total_gb": m["disk"]["total_gb"],
            "free_gb": m["disk"]["free_gb"]
        }
        for m in history
    ]

    return {
        "success": True,
        "data": disk_data,
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/network")
async def get_network_metrics(request: Request, hours: int = Query(1, ge=1, le=24)):
    """
    获取网络指标历史
    """
    service = _get_service(request)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    history = service.get_metrics_history(start_time=start_time)

    network_data = [
        {
            "timestamp": m["timestamp"],
            "sent_mb": m["network"]["sent_mb"],
            "recv_mb": m["network"]["recv_mb"],
            "packets_sent": m["network"]["packets_sent"],
            "packets_recv": m["network"]["packets_recv"]
        }
        for m in history
    ]

    return {
        "success": True,
        "data": network_data,
        "period_hours": hours,
        "timestamp": datetime.utcnow().isoformat()
    }
