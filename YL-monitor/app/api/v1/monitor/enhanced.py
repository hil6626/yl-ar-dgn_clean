#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强监控API端点
提供详细进程、CPU、内存监控接口
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from datetime import datetime
import logging

# 导入增强监控器
from app.services.enhanced_monitors.detailed_process_monitor import (
    DetailedProcessMonitor, ProcessMonitorManager, MONITOR_CONFIGS
)
from app.services.enhanced_monitors.detailed_cpu_monitor import DetailedCPUMonitor
from app.services.enhanced_monitors.detailed_memory_monitor import DetailedMemoryMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced", tags=["enhanced_monitoring"])

# 全局监控器实例
process_manager = ProcessMonitorManager()
cpu_monitor = DetailedCPUMonitor()
memory_monitor = DetailedMemoryMonitor()

# 初始化默认监控器
process_manager.create_default_monitors()


@router.get("/process/{service_name}")
async def get_process_metrics(service_name: str) -> Dict:
    """
    获取指定服务的详细进程指标
    """
    try:
        monitor = process_manager.monitors.get(service_name)
        if not monitor:
            raise HTTPException(
                status_code=404, 
                detail=f"未找到服务监控器: {service_name}"
            )
        
        metrics = monitor.get_latest_metrics()
        if not metrics:
            return {
                "service_name": service_name,
                "status": "not_running",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "service_name": service_name,
            "status": "running",
            "metrics": metrics.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取进程指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process")
async def get_all_process_metrics() -> Dict:
    """
    获取所有服务的进程指标
    """
    try:
        all_metrics = {}
        for name, monitor in process_manager.monitors.items():
            metrics = monitor.get_latest_metrics()
            all_metrics[name] = {
                "status": "running" if metrics else "not_running",
                "metrics": metrics.to_dict() if metrics else None,
                "average": monitor.get_average_metrics(60)
            }
        
        return {
            "services": all_metrics,
            "count": len(all_metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取所有进程指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cpu")
async def get_cpu_metrics() -> Dict:
    """
    获取详细CPU指标
    """
    try:
        metrics = cpu_monitor.get_latest_metrics()
        pressure = cpu_monitor.get_cpu_pressure()
        
        if not metrics:
            return {
                "status": "no_data",
                "message": "暂无CPU数据",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "ok",
            "metrics": metrics.to_dict(),
            "pressure": pressure,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取CPU指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cpu/history")
async def get_cpu_history(count: int = 100) -> Dict:
    """
    获取CPU历史指标
    """
    try:
        history = cpu_monitor.get_metrics_history(count)
        return {
            "count": len(history),
            "history": [m.to_dict() for m in history],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取CPU历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_metrics() -> Dict:
    """
    获取详细内存指标
    """
    try:
        metrics = memory_monitor.get_latest_metrics()
        pressure = memory_monitor.get_memory_pressure()
        top_processes = memory_monitor.get_top_memory_processes(5)
        
        if not metrics:
            return {
                "status": "no_data",
                "message": "暂无内存数据",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "ok",
            "metrics": metrics.to_dict(),
            "pressure": pressure,
            "top_processes": [p.to_dict() for p in top_processes],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取内存指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/history")
async def get_memory_history(count: int = 100) -> Dict:
    """
    获取内存历史指标
    """
    try:
        history = memory_monitor.get_metrics_history(count)
        return {
            "count": len(history),
            "history": [m.to_dict() for m in history],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取内存历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_enhanced_summary() -> Dict:
    """
    获取增强监控汇总
    """
    try:
        # 进程汇总
        process_summary = {}
        for name, monitor in process_manager.monitors.items():
            metrics = monitor.get_latest_metrics()
            avg = monitor.get_average_metrics(60)
            process_summary[name] = {
                "status": "running" if metrics else "not_running",
                "cpu_percent": metrics.cpu_percent if metrics else 0,
                "memory_percent": metrics.memory_percent if metrics else 0,
                "avg_cpu": avg.get("avg_cpu_percent", 0) if avg else 0,
                "avg_memory": avg.get("avg_memory_percent", 0) if avg else 0
            }
        
        # CPU压力
        cpu_pressure = cpu_monitor.get_cpu_pressure()
        
        # 内存压力
        memory_pressure = memory_monitor.get_memory_pressure()
        
        return {
            "processes": process_summary,
            "cpu_pressure": cpu_pressure,
            "memory_pressure": memory_pressure,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取增强监控汇总失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
