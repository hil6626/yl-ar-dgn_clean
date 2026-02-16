"""
用户界面监控路由
监控 User GUI 桌面应用状态
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime

from app.services.user_gui_monitor import user_gui_monitor, get_user_gui_status

router = APIRouter(tags=["UI Monitor"])


@router.get("/status")
async def get_ui_status(request: Request) -> Dict[str, Any]:
    """
    获取 User GUI 状态
    """
    status_info = get_user_gui_status()
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "ui",
        "data": status_info
    }


@router.get("/metrics")
async def get_ui_metrics(request: Request) -> Dict[str, Any]:
    """
    获取 User GUI 性能指标
    """
    is_running = user_gui_monitor.check_process_running()
    
    if not is_running:
        return {
            "status": "error",
            "message": "User GUI not running",
            "timestamp": datetime.utcnow().isoformat(),
            "component": "ui",
            "data": {
                "process_running": False,
                "cpu_percent": 0,
                "memory_mb": 0
            }
        }
    
    # 获取系统指标
    import psutil
    
    # 查找 User GUI 进程
    process_info = None
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.cmdline())
                if 'user/main.py' in cmdline:
                    process_info = {
                        "pid": proc.info['pid'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_mb": proc.info['memory_info'].rss / 1024 / 1024
                    }
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "ui",
        "data": {
            "process_running": True,
            "metrics": process_info or {}
        }
    }


@router.get("/logs")
async def get_ui_logs(request: Request, lines: int = 50) -> Dict[str, Any]:
    """
    获取 User GUI 日志
    """
    import subprocess
    
    try:
        # 尝试读取日志文件
        result = subprocess.run(
            ["tail", "-n", str(lines), "/tmp/user_gui.log"],
            capture_output=True,
            text=True
        )
        logs = result.stdout if result.returncode == 0 else "No logs available"
    except Exception as e:
        logs = f"Error reading logs: {str(e)}"
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "ui",
        "data": {
            "logs": logs,
            "lines": lines
        }
    }


@router.post("/restart")
async def restart_ui(request: Request) -> Dict[str, Any]:
    """
    重启 User GUI
    """
    try:
        # 停止现有进程
        user_gui_monitor.stop_process()
        
        # 启动新进程
        success = user_gui_monitor.start_process()
        
        return {
            "status": "ok" if success else "error",
            "timestamp": datetime.utcnow().isoformat(),
            "component": "ui",
            "message": "User GUI restarted successfully" if success else "Failed to restart User GUI"
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "component": "ui",
            "message": f"Error restarting User GUI: {str(e)}"
        }
