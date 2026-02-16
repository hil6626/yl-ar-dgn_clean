#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础设施监控 API
提供细粒度的基础设施层监控数据
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.infrastructure_monitor import (
    infrastructure_collector,
    ProcessMonitor,
    PortMonitor,
    FilesystemMonitor
)

router = APIRouter()


@router.get("/infrastructure")
async def get_infrastructure_metrics() -> Dict[str, Any]:
    """
    获取完整的基础设施层监控数据
    
    包括：
    - 进程级指标（CPU、内存、IO、线程等）
    - 端口级指标（连通性、响应时间）
    - 文件系统指标（磁盘使用、文件统计）
    """
    try:
        return infrastructure_collector.collect_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/processes")
async def get_process_metrics() -> Dict[str, Any]:
    """
    获取所有服务的进程级指标
    """
    try:
        return infrastructure_collector.process_monitor.get_all_services_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/processes/{service_name}")
async def get_service_process_metrics(service_name: str) -> Dict[str, Any]:
    """
    获取指定服务的进程级指标
    
    Args:
        service_name: 服务名称（yl-monitor, ar-backend, user-gui）
    """
    try:
        metrics = infrastructure_collector.process_monitor.monitor_service(
            service_name
        )
        if metrics is None:
            return {
                "service": service_name,
                "status": "not_running",
                "timestamp": infrastructure_collector.process_monitor._cache.get(
                    f"service_{service_name}", (0, None)
                )[1]
            }
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/ports")
async def get_port_metrics() -> Dict[str, Any]:
    """
    获取所有服务端口的监控数据
    """
    try:
        return infrastructure_collector.port_monitor.monitor_service_ports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/ports/{service_name}")
async def get_service_port_metrics(service_name: str) -> Dict[str, Any]:
    """
    获取指定服务端口的监控数据
    
    Args:
        service_name: 服务名称
    """
    port_map = {
        'yl-monitor': ('0.0.0.0', 5500),
        'ar-backend': ('0.0.0.0', 5501),
        'user-gui': ('0.0.0.0', 5502)
    }
    
    if service_name not in port_map:
        raise HTTPException(
            status_code=404,
            detail=f"未知服务: {service_name}"
        )
    
    try:
        host, port = port_map[service_name]
        metrics = infrastructure_collector.port_monitor.check_port(host, port)
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/filesystem")
async def get_filesystem_metrics() -> Dict[str, Any]:
    """
    获取文件系统监控数据
    """
    try:
        return (
            infrastructure_collector.filesystem_monitor
            .monitor_project_directories()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/health/{service_name}")
async def get_service_health(service_name: str) -> Dict[str, Any]:
    """
    获取指定服务的综合健康状态
    
    综合评估进程状态和端口连通性
    """
    try:
        return infrastructure_collector.get_service_health(service_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure/health")
async def get_all_services_health() -> Dict[str, Any]:
    """
    获取所有服务的综合健康状态
    """
    services = ['yl-monitor', 'ar-backend', 'user-gui']
    result = {
        "timestamp": infrastructure_collector.collect_all()["timestamp"],
        "services": {}
    }
    
    for service in services:
        try:
            result["services"][service] = (
                infrastructure_collector.get_service_health(service)
            )
        except Exception as e:
            result["services"][service] = {
                "service": service,
                "healthy": False,
                "error": str(e),
                "timestamp": result["timestamp"]
            }
    
    # 计算整体健康状态
    all_healthy = all(
        s.get("healthy", False) for s in result["services"].values()
    )
    result["overall_healthy"] = all_healthy
    
    return result
