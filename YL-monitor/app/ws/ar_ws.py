"""
AR WebSocket 处理器
负责 AR 状态实时推送，集成事件总线监听
"""

from fastapi import WebSocket, APIRouter
from typing import List
import asyncio
import logging
import random

logger = logging.getLogger(__name__)

# 创建 APIRouter 实例
router = APIRouter()

clients: List[WebSocket] = []


async def send_ws_update(msg: dict):
    """发送 WebSocket 更新"""
    for client in list(clients):
        try:
            await client.send_json(msg)
        except Exception as e:
            logger.error(f"发送 WebSocket 消息失败: {e}")
            if client in clients:
                clients.remove(client)

def _compute_resources(nodes_payload):
    if not nodes_payload:
        return {"cpu": 0, "memory": 0, "gpu": 0}
    cpu_vals, mem_vals, gpu_vals = [], [], []
    for node in nodes_payload:
        resources = getattr(node, "resources", {}) or {}
        cpu_vals.append(int(resources.get("cpu", 0)))
        mem_vals.append(int(resources.get("memory", 0)))
        gpu_vals.append(int(resources.get("gpu", 0)))
    avg_cpu = int(sum(cpu_vals) / max(1, len(cpu_vals)))
    avg_mem = int(sum(mem_vals) / max(1, len(mem_vals)))
    avg_gpu = int(sum(gpu_vals) / max(1, len(gpu_vals)))
    # 轻微抖动，模拟动态
    return {
        "cpu": max(0, min(100, avg_cpu + random.randint(-3, 3))),
        "memory": max(0, min(100, avg_mem + random.randint(-3, 3))),
        "gpu": max(0, min(100, avg_gpu + random.randint(-3, 3))),
    }


@router.websocket("/ws/ar")
async def websocket_endpoint(websocket: WebSocket):
    """AR WebSocket 端点"""
    await websocket.accept()
    clients.append(websocket)
    logger.info(f"AR WebSocket 客户端连接，当前数量: {len(clients)}")
    
    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "message": "AR WebSocket 连接已建立",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 监听事件总线
        from app.services.event_bus import event_bus, EventType
        
        async def on_event(event):
            """事件处理回调"""
            try:
                await websocket.send_json({
                    "type": "event",
                    "event_type": event.type.value,
                    "source": event.source,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat()
                })
            except Exception as e:
                logger.error(f"发送事件消息失败: {e}")
        
        # 订阅 AR 相关事件
        subscription_id = event_bus.subscribe(
            on_event,
            filter_types=[
                EventType.AR_NODE_UPDATED,
                EventType.AR_STATUS_CHANGED,
                EventType.DAG_NODE_STARTED,
                EventType.DAG_NODE_COMPLETED
            ],
            subscriber_id=f"ar_ws_client_{id(websocket)}"
        )
        
        try:
            while True:
                # 定期发送状态（前端期望 ar_status）
                await asyncio.sleep(5)
                try:
                    app = websocket.scope.get("app")
                    monitor = getattr(getattr(app, "state", None), "ar_monitor", None) if app else None
                    nodes_payload = []
                    if monitor is not None:
                        nodes_payload = monitor.get_nodes().nodes
                    resources = _compute_resources(nodes_payload)
                    await websocket.send_json(
                        {
                            "type": "ar_status",
                            "nodes": [n.model_dump() for n in nodes_payload],
                            "resources": resources,
                        }
                    )
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                except Exception:
                    break
        finally:
            # 清理订阅
            event_bus.unsubscribe(subscription_id)
            if websocket in clients:
                clients.remove(websocket)
            logger.info(f"AR WebSocket 客户端断开，当前数量: {len(clients)}")
            
    except Exception as e:
        logger.error(f"AR WebSocket 错误: {e}")
        if websocket in clients:
            clients.remove(websocket)


def broadcast_ar_update(node_id: str, status: str, data: dict = None):
    """广播 AR 更新消息"""
    asyncio.create_task(send_ws_update({
        "type": "ar_update",
        "node_id": node_id,
        "status": status,
        "data": data or {}
    }))


def broadcast_event(event_type: str, source: str, data: dict):
    """广播事件消息"""
    asyncio.create_task(send_ws_update({
        "type": "event",
        "event_type": event_type,
        "source": source,
        "data": data
    }))
