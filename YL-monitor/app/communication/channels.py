"""
通信通道实现
"""

import asyncio
import json
from typing import Optional, Dict, List, Callable
from .protocol import CommunicationChannel, BaseMessage, JSONMessage, CommunicationProtocol

class DirectCallChannel(CommunicationChannel):
    """直接调用通道"""
    
    def __init__(self, channel_id: str):
        super().__init__(channel_id, CommunicationProtocol.DIRECT_CALL)
        self._callbacks: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> bool:
        """连接通道"""
        self.is_connected = True
        return True
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.is_connected = False
        self._callbacks.clear()
        return True
    
    async def send(self, message: BaseMessage) -> bool:
        """发送消息"""
        if not self.is_connected:
            return False
        
        callbacks = self._callbacks.get(message.type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                print(f"回调处理失败: {e}")
        
        return True
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[BaseMessage]:
        """接收消息（直接调用通道不支持接收）"""
        return None
    
    async def subscribe(self, message_type: str, callback: Callable) -> str:
        """订阅消息类型"""
        if message_type not in self._callbacks:
            self._callbacks[message_type] = []
        self._callbacks[message_type].append(callback)
        return f"direct_{message_type}_{id(callback)}"
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        # 在直接调用通道中，取消订阅比较困难，因为没有保存subscription_id
        # 这里简化处理，实际应用中需要更好的实现
        return True

class WebSocketChannel(CommunicationChannel):
    """WebSocket通道"""
    
    def __init__(self, channel_id: str, websocket):
        super().__init__(channel_id, CommunicationProtocol.WEBSOCKET)
        self.websocket = websocket
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._listening_task = None
    
    async def connect(self) -> bool:
        """连接通道"""
        if not self.websocket or self.websocket.closed:
            return False
        
        self.is_connected = True
        # 启动监听任务
        self._listening_task = asyncio.create_task(self._listen_for_messages())
        return True
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.is_connected = False
        if self._listening_task:
            self._listening_task.cancel()
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        return True
    
    async def send(self, message: BaseMessage) -> bool:
        """发送消息"""
        if not self.is_connected or not self.websocket or self.websocket.closed:
            return False
        
        try:
            await self.websocket.send_bytes(message.serialize())
            return True
        except Exception as e:
            print(f"WebSocket发送消息失败: {e}")
            return False
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[BaseMessage]:
        """接收消息"""
        if not self.is_connected or not self.websocket or self.websocket.closed:
            return None
        
        try:
            # 这里需要一个队列来存储接收到的消息
            # 为简化，我们假设有一个消息队列
            # 实际实现中需要更复杂的机制
            pass
        except Exception as e:
            print(f"WebSocket接收消息失败: {e}")
        
        return None
    
    async def subscribe(self, message_type: str, callback: Callable) -> str:
        """订阅消息类型"""
        if message_type not in self._subscriptions:
            self._subscriptions[message_type] = []
        self._subscriptions[message_type].append(callback)
        return f"ws_{message_type}_{id(callback)}"
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        # 简化处理
        return True
    
    async def _listen_for_messages(self):
        """监听WebSocket消息"""
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    try:
                        msg = JSONMessage.deserialize(message)
                        await self._handle_message(msg)
                    except Exception as e:
                        print(f"解析WebSocket消息失败: {e}")
        except Exception as e:
            print(f"WebSocket监听出错: {e}")
        finally:
            self.is_connected = False
    
    async def _handle_message(self, message: BaseMessage):
        """处理接收到的消息"""
        callbacks = self._subscriptions.get(message.type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                print(f"处理WebSocket消息失败: {e}")

# 全局消息路由器实例
from .protocol import MessageRouter
message_router = MessageRouter()
