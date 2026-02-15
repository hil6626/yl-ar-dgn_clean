"""
监控API路由模块
提供系统资源和实时监控数据
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter(tags=["monitor"])


@router.get("/system/resources")
async def get_system_resources() -> Dict[str, Any]:
    """
    获取系统资源使用情况
    
    返回:
    - cpu: CPU使用率百分比
    - memory: 内存使用率百分比
    - disk: 磁盘使用率百分比
    """
    try:
        import psutil
        
        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源数据失败: {str(e)}")


@router.get("/monitor/api")
async def get_api_monitor() -> Dict[str, Any]:
    """
    获取API实时监控数据
    """
    try:
        # 模拟API监控数据
        return {
            "items": [
                {"name": "告警API", "status": "online", "latency": 45},
                {"name": "指标API", "status": "online", "latency": 32},
                {"name": "DAG API", "status": "online", "latency": 28},
                {"name": "脚本API", "status": "offline", "latency": 0},
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取API监控失败: {str(e)}")


@router.get("/monitor/dag")
async def get_dag_monitor() -> Dict[str, Any]:
    """
    获取DAG执行监控数据
    """
    try:
        # 模拟DAG监控数据
        return {
            "executions": [
                {"dag_name": "日常巡检", "status": "running", "progress": 65},
                {"dag_name": "数据备份", "status": "completed", "progress": 100},
                {"dag_name": "日志清理", "status": "pending", "progress": 0},
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取DAG监控失败: {str(e)}")


@router.get("/monitor/scripts")
async def get_scripts_monitor() -> Dict[str, Any]:
    """
    获取脚本执行监控数据
    """
    try:
        # 模拟脚本监控数据
        return {
            "executions": [
                {"script_name": "cpu_monitor.py", "status": "running",
                 "duration": 45},
                {"script_name": "disk_check.py", "status": "completed",
                 "duration": 12},
                {"script_name": "alert_notify.py", "status": "failed",
                 "duration": 3},
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取脚本监控失败: {str(e)}")
