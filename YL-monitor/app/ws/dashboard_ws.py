"""
Dashboard WebSocket模块
提供实时系统资源监控数据推送
"""

from fastapi import APIRouter, WebSocket
from app.ws.connection_manager import manager
import asyncio
import psutil
from datetime import datetime

router = APIRouter()


@router.websocket("/ws/dashboard/realtime")
async def dashboard_websocket(websocket: WebSocket):
    """
    Dashboard实时数据WebSocket
    
    每5秒推送系统资源指标：
    - CPU使用率
    - 内存使用率
    - 磁盘使用率
    """
    await manager.connect(websocket, "dashboard")
    
    try:
        while True:
            # 收集系统资源数据
            metrics = {
                "cpu": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('/').percent
            }
            
            # 发送资源指标
            await manager.send_to(websocket, {
                "type": "resource_metrics",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 每5秒推送一次
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"[Dashboard WebSocket] 错误: {e}")
    finally:
        manager.disconnect(websocket, "dashboard")
        print("[Dashboard WebSocket] 连接已关闭")


@router.websocket("/ws/dashboard/events")
async def dashboard_events_websocket(websocket: WebSocket):
    """
    Dashboard事件WebSocket
    
    推送系统事件：
    - API状态变更
    - DAG执行状态
    - 脚本执行状态
    - 告警通知
    """
    await manager.connect(websocket, "dashboard")
    
    try:
        # 模拟事件推送
        event_types = ["api_status", "dag_execution", "script_execution", "alert"]
        
        while True:
            # 生成模拟事件
            import random
            event_type = random.choice(event_types)
            
            event_data = generate_mock_event(event_type)
            
            await manager.send_to(websocket, {
                "type": event_type,
                "data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 随机间隔2-5秒
            await asyncio.sleep(random.randint(2, 5))
            
    except Exception as e:
        print(f"[Dashboard Events] 错误: {e}")
    finally:
        manager.disconnect(websocket, "dashboard")


def generate_mock_event(event_type: str) -> dict:
    """
    生成模拟事件数据
    """
    if event_type == "api_status":
        return {
            "items": [
                {"name": "告警API", "status": "online", "latency": 45},
                {"name": "指标API", "status": "online", "latency": 32},
                {"name": "DAG API", "status": random.choice(["online", "offline"]), "latency": 28},
            ]
        }
    elif event_type == "dag_execution":
        return {
            "executions": [
                {"dag_name": "日常巡检", "status": random.choice(["running", "completed"]), "progress": 65},
                {"dag_name": "数据备份", "status": "completed", "progress": 100},
            ]
        }
    elif event_type == "script_execution":
        return {
            "executions": [
                {"script_name": "cpu_monitor.py", "status": random.choice(["running", "completed"]), "duration": 45},
                {"script_name": "disk_check.py", "status": "completed", "duration": 12},
            ]
        }
    else:
        return {"message": "系统运行正常"}
