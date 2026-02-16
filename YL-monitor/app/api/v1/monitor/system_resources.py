#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统资源监控 API
提供 CPU、内存、GPU 的详细监控数据
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from app.services.system_resource_monitor import (
    system_resource_collector,
    CPUDetailedMonitor,
    MemoryDetailedMonitor,
    GPUMonitor
)

router = APIRouter()


@router.get("/system-resources")
async def get_system_resources() -> Dict[str, Any]:
    """
    获取完整的系统资源监控数据
    
    包括：
    - CPU 详细指标（整体/每核使用率、频率、负载、上下文切换等）
    - 内存详细指标（物理/交换内存、活跃/缓存内存等）
    - GPU 指标（利用率、显存、温度、功耗等）
    - 资源压力评估
    """
    try:
        return system_resource_collector.collect_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/cpu")
async def get_cpu_metrics() -> Dict[str, Any]:
    """
    获取 CPU 详细指标
    """
    try:
        metrics = system_resource_collector.cpu_monitor.collect_metrics()
        return {
            "metrics": metrics.to_dict(),
            "pressure": system_resource_collector.cpu_monitor.get_cpu_pressure(),
            "history": system_resource_collector.cpu_monitor.get_usage_history()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/cpu/pressure")
async def get_cpu_pressure() -> Dict[str, Any]:
    """
    获取 CPU 压力评估
    """
    try:
        return system_resource_collector.cpu_monitor.get_cpu_pressure()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/memory")
async def get_memory_metrics() -> Dict[str, Any]:
    """
    获取内存详细指标
    """
    try:
        metrics = system_resource_collector.memory_monitor.collect_metrics()
        return {
            "metrics": metrics.to_dict(),
            "pressure": (
                system_resource_collector.memory_monitor.get_memory_pressure()
            ),
            "history": (
                system_resource_collector.memory_monitor.get_usage_history()
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/memory/pressure")
async def get_memory_pressure() -> Dict[str, Any]:
    """
    获取内存压力评估
    """
    try:
        return system_resource_collector.memory_monitor.get_memory_pressure()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/memory/top-processes")
async def get_top_memory_processes(
    limit: int = 10
) -> Dict[str, Any]:
    """
    获取内存消耗最多的进程
    
    Args:
        limit: 返回进程数量（默认10）
    """
    try:
        processes = (
            system_resource_collector.memory_monitor.get_top_memory_processes(
                limit
            )
        )
        return {
            "processes": [p.to_dict() for p in processes],
            "count": len(processes),
            "timestamp": system_resource_collector.memory_monitor.collect_metrics().timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/gpu")
async def get_gpu_metrics() -> Dict[str, Any]:
    """
    获取 GPU 监控数据
    """
    try:
        return system_resource_collector.gpu_monitor.get_gpu_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-resources/pressure")
async def get_resource_pressure() -> Dict[str, Any]:
    """
    获取整体资源压力评估
    
    综合 CPU 和内存压力，给出整体评估和建议
    """
    try:
        return system_resource_collector.get_resource_pressure()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
