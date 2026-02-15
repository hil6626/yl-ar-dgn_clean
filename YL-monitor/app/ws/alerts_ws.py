"""
告警 WebSocket 服务

功能:
- 实时推送告警状态变更
- 客户端实时更新
- 支持告警确认操作

作者: AI Assistant
版本: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, APIRouter

from app.services.alert_service import get_alert_service, AlertService
from app.services.event_bus import EventBus, EventType
from app.models.alert import AlertStatus

logger = logging.getLogger(__name__)

# 创建 APIRouter 实例
router = APIRouter()


class AlertsWebSocketManager:
    """告警 WebSocket 管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._alert_service: Optional[AlertService] = None
        self._event_handlers: Dict[str, callable] = {}
    
    async def connect(self, websocket: WebSocket):
        """处理客户端连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # 初始化告警服务
        if self._alert_service is None:
            self._alert_service = get_alert_service()
        
        # 发送当前活动告警
        active_alerts = self._alert_service.get_active_alerts()
        await websocket.send_json({
            "type": "init",
            "data": {
                "active_alerts": [alert.dict() for alert in active_alerts],
                "stats": self._alert_service.get_stats()
            }
        })
        
        # 订阅事件
        self._subscribe_events()
        
        logger.info(f"告警 WebSocket 客户端已连接，当前连接数: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """处理客户端断开"""
        self.active_connections.discard(websocket)
        logger.info(f"告警 WebSocket 客户端已断开，当前连接数: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        if not self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"发送 WebSocket 消息失败: {e}")
                disconnected.add(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    def _subscribe_events(self):
        """订阅告警相关事件"""
        event_bus = EventBus()
        
        # 告警触发事件
        self._event_handlers['alert_triggered'] = lambda data: asyncio.create_task(
            self._handle_alert_triggered(data)
        )
        event_bus.subscribe(
            EventType.ALERT_TRIGGERED,
            self._event_handlers['alert_triggered']
        )
        
        # 告警恢复事件
        self._event_handlers['alert_recovered'] = lambda data: asyncio.create_task(
            self._handle_alert_recovered(data)
        )
        event_bus.subscribe(
            EventType.ALERT_RECOVERED,
            self._event_handlers['alert_recovered']
        )
        
        # 浏览器通知事件
        self._event_handlers['notification_browser'] = lambda data: asyncio.create_task(
            self._handle_browser_notification(data)
        )
        event_bus.subscribe(
            EventType.NOTIFICATION_BROWSER,
            self._event_handlers['notification_browser']
        )
    
    async def _handle_alert_triggered(self, data: dict):
        """处理告警触发事件"""
        await self.broadcast({
            "type": "alert_triggered",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
    
    async def _handle_alert_recovered(self, data: dict):
        """处理告警恢复事件"""
        await self.broadcast({
            "type": "alert_recovered",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
    
    async def _handle_browser_notification(self, data: dict):
        """处理浏览器通知事件"""
        await self.broadcast({
            "type": "browser_notification",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
    
    async def handle_message(self, websocket: WebSocket, message: dict):
        """处理客户端消息"""
        msg_type = message.get("type")
        
        if msg_type == "acknowledge_alert":
            # 确认告警
            alert_id = message.get("alert_id")
            user = message.get("user", "unknown")
            
            if self._alert_service and alert_id:
                alert = self._alert_service.acknowledge_alert(alert_id, user)
                if alert:
                    await self.broadcast({
                        "type": "alert_acknowledged",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "alert_id": alert_id,
                            "acknowledged_by": user,
                            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                        }
                    })
        
        elif msg_type == "get_history":
            # 获取告警历史
            limit = message.get("limit", 100)
            if self._alert_service:
                history = self._alert_service.get_alert_history(limit=limit)
                await websocket.send_json({
                    "type": "history",
                    "data": [alert.dict() for alert in history]
                })
        
        elif msg_type == "ping":
            # 心跳响应
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })


# 全局实例
alerts_ws_manager = AlertsWebSocketManager()


async def alerts_websocket_handler(websocket: WebSocket):
    """
    告警 WebSocket 处理函数
    
    使用方式:
    @app.websocket("/ws/alerts")
    async def websocket_endpoint(websocket: WebSocket):
        await alerts_websocket_handler(websocket)
    """
    await alerts_ws_manager.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await alerts_ws_manager.handle_message(websocket, message)
            except json.JSONDecodeError:
                logger.error(f"无效的 JSON 消息: {data}")
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的 JSON 格式"
                })
            
    except WebSocketDisconnect:
        await alerts_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 处理错误: {e}")
        await alerts_ws_manager.disconnect(websocket)


# 添加 WebSocket 端点函数
@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """
    告警 WebSocket 端点
    
    注册到 FastAPI 的 WebSocket 路由:
    app.include_router(alerts_ws.router)
    """
    await alerts_websocket_handler(websocket)
