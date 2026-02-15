"""
DAG WebSocket模块
提供DAG执行状态实时推送
"""

from fastapi import APIRouter, WebSocket
from app.ws.connection_manager import manager
import asyncio
from datetime import datetime

router = APIRouter()


@router.websocket("/ws/dag/events")
async def dag_events_websocket(websocket: WebSocket):
    """
    DAG事件WebSocket
    
    推送DAG执行状态变更：
    - DAG开始/完成/失败
    - 节点状态变更
    - 执行进度更新
    """
    await manager.connect(websocket, "dag")
    
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        
        # 订阅DAG事件流
        async for event in engine.event_stream():
            await manager.send_to(websocket, {
                "type": event.get("type"),
                "data": event.get("data"),
                "timestamp": event.get("timestamp")
            })
            
    except Exception as e:
        print(f"[DAG WebSocket] 错误: {e}")
    finally:
        manager.disconnect(websocket, "dag")


@router.websocket("/ws/dag/{execution_id}")
async def dag_execution_websocket(websocket: WebSocket, execution_id: str):
    """
    特定DAG执行详情WebSocket
    
    推送指定执行的实时进度
    """
    await manager.connect(websocket, "dag", client_id=f"exec_{execution_id}")
    
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        
        # 获取执行详情
        last_progress = 0
        
        while True:
            detail = await engine.get_execution_detail(execution_id)
            
            if not detail:
                await manager.send_to(websocket, {
                    "type": "error",
                    "data": {"message": "执行记录不存在"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
            
            # 只在进度变化时推送
            if detail["progress"] != last_progress:
                last_progress = detail["progress"]
                
                await manager.send_to(websocket, {
                    "type": "execution_update",
                    "data": {
                        "execution_id": execution_id,
                        "status": detail["status"],
                        "progress": detail["progress"],
                        "node_states": detail["node_states"]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # 执行完成则退出
            if detail["status"] in ["completed", "failed", "cancelled"]:
                await manager.send_to(websocket, {
                    "type": "execution_finished",
                    "data": {
                        "execution_id": execution_id,
                        "status": detail["status"],
                        "completed_at": detail["completed_at"]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
            
            # 每秒检查一次
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"[DAG Execution WebSocket] 错误: {e}")
    finally:
        manager.disconnect(websocket, "dag")
