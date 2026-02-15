"""
WebSocket连接管理器
管理所有WebSocket连接，支持按类型分组和广播
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    """
    WebSocket连接管理器
    
    职责:
    1. 管理WebSocket连接生命周期
    2. 按类型分组管理连接
    3. 支持广播和单播消息
    4. 自动清理断开的连接
    """
    
    def __init__(self):
        # 按类型存储连接
        self.connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "dag": set(),
            "scripts": set(),
            "alerts": set()
        }
        
        # 连接元数据
        self.connection_meta: Dict[WebSocket, dict] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        conn_type: str,
        client_id: Optional[str] = None
    ):
        """
        建立WebSocket连接
        
        参数:
        - websocket: WebSocket对象
        - conn_type: 连接类型(dashboard/dag/scripts/alerts)
        - client_id: 客户端标识
        """
        await websocket.accept()
        
        if conn_type in self.connections:
            self.connections[conn_type].add(websocket)
        
        # 记录连接元数据
        self.connection_meta[websocket] = {
            "type": conn_type,
            "client_id": client_id or "anonymous",
            "connected_at": asyncio.get_event_loop().time()
        }
        
        print(f"[WebSocket] 新连接: {conn_type} - {client_id}")
    
    def disconnect(self, websocket: WebSocket, conn_type: Optional[str] = None):
        """
        断开WebSocket连接
        """
        # 确定连接类型
        if conn_type is None and websocket in self.connection_meta:
            conn_type = self.connection_meta[websocket].get("type")
        
        # 从对应类型中移除
        if conn_type and conn_type in self.connections:
            self.connections[conn_type].discard(websocket)
        
        # 清理元数据
        if websocket in self.connection_meta:
            del self.connection_meta[websocket]
        
        print(f"[WebSocket] 连接断开: {conn_type}")
    
    async def broadcast(
        self,
        conn_type: str,
        message: dict,
        exclude: Optional[WebSocket] = None
    ):
        """
        广播消息到指定类型的所有连接
        
        参数:
        - conn_type: 连接类型
        - message: 消息内容
        - exclude: 排除的连接
        """
        if conn_type not in self.connections:
            return
        
        disconnected = set()
        
        for conn in self.connections[conn_type]:
            if conn == exclude:
                continue
            
            try:
                await conn.send_json(message)
            except Exception as e:
                # 标记断开的连接
                disconnected.add(conn)
                print(f"[WebSocket] 发送失败，标记断开: {e}")
        
        # 清理断开的连接
        if disconnected:
            self.connections[conn_type] -= disconnected
            for conn in disconnected:
                self.connection_meta.pop(conn, None)
    
    async def send_to(self, websocket: WebSocket, message: dict):
        """
        发送消息到指定连接
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[WebSocket] 单播失败: {e}")
            # 标记断开
            self.disconnect(websocket)
    
    async def send_to_client(self, client_id: str, message: dict):
        """
        发送消息到指定客户端
        """
        for websocket, meta in self.connection_meta.items():
            if meta.get("client_id") == client_id:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"[WebSocket] 发送到客户端失败: {e}")
    
    def get_connection_count(self, conn_type: Optional[str] = None) -> int:
        """
        获取连接数量
        """
        if conn_type:
            return len(self.connections.get(conn_type, set()))
        
        return sum(len(conns) for conns in self.connections.values())
    
    def get_connection_stats(self) -> dict:
        """
        获取连接统计信息
        """
        return {
            "total": self.get_connection_count(),
            "by_type": {
                conn_type: len(conns)
                for conn_type, conns in self.connections.items()
            }
        }


# 全局连接管理器实例
manager = ConnectionManager()
