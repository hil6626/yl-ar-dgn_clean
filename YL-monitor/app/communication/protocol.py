"""
通信协议定义
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from enum import Enum
import json
import uuid
from datetime import datetime

class CommunicationProtocol(Enum):
    """通信协议枚举"""
    DIRECT_CALL = "direct_call"
    MESSAGE_QUEUE = "message_queue"
    HTTP_API = "http_api"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"

class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class BaseMessage(ABC):
    """基础消息类"""
    
    def __init__(
        self,
        message_type: str,
        data: Dict[str, Any],
        sender: str = None,
        receiver: str = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str = None,
        timeout: int = 30
    ):
        self.id = str(uuid.uuid4())
        self.type = message_type
        self.data = data
        self.sender = sender
        self.receiver = receiver
        self.priority = priority
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timeout = timeout
        self.timestamp = datetime.now()
        self.status = MessageStatus.PENDING
        self.retry_count = 0
        self.metadata = {}
    
    @abstractmethod
    def serialize(self) -> bytes:
        """序列化消息"""
        pass
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> 'BaseMessage':
        """反序列化消息"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'sender': self.sender,
            'receiver': self.receiver,
            'priority': self.priority.name,
            'correlation_id': self.correlation_id,
            'timeout': self.timeout,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.name,
            'retry_count': self.retry_count,
            'metadata': self.metadata
        }

class JSONMessage(BaseMessage):
    """JSON消息实现"""
    
    def serialize(self) -> bytes:
        """序列化消息为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False).encode('utf-8')
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'JSONMessage':
        """从JSON反序列化消息"""
        msg_dict = json.loads(data.decode('utf-8'))
        msg = cls(
            message_type=msg_dict['type'],
            data=msg_dict['data'],
            sender=msg_dict.get('sender'),
            receiver=msg_dict.get('receiver'),
            priority=MessagePriority[msg_dict.get('priority', 'NORMAL')],
            correlation_id=msg_dict.get('correlation_id'),
            timeout=msg_dict.get('timeout', 30)
        )
        msg.id = msg_dict['id']
        msg.timestamp = datetime.fromisoformat(msg_dict['timestamp'])
        msg.status = MessageStatus[msg_dict.get('status', 'PENDING')]
        msg.retry_count = msg_dict.get('retry_count', 0)
        msg.metadata = msg_dict.get('metadata', {})
        return msg

class CommunicationChannel(ABC):
    """通信通道抽象基类"""
    
    def __init__(self, channel_id: str, protocol: CommunicationProtocol):
        self.channel_id = channel_id
        self.protocol = protocol
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接通道"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def send(self, message: BaseMessage) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    async def receive(self, timeout: Optional[float] = None) -> Optional[BaseMessage]:
        """接收消息"""
        pass
    
    @abstractmethod
    async def subscribe(self, message_type: str, callback: callable) -> str:
        """订阅消息类型"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        pass

# 消息路由器
class MessageRouter:
    """消息路由器"""
    
    def __init__(self):
        self.channels: Dict[str, CommunicationChannel] = {}
        self.routes: Dict[str, str] = {}  # message_type -> channel_id
        self.handlers: Dict[str, callable] = {}
    
    def register_channel(self, channel_id: str, channel: CommunicationChannel) -> None:
        """注册通信通道"""
        self.channels[channel_id] = channel
    
    def unregister_channel(self, channel_id: str) -> bool:
        """注销通信通道"""
        if channel_id in self.channels:
            del self.channels[channel_id]
            
            # 移除相关路由
            routes_to_remove = [msg_type for msg_type, ch_id in self.routes.items() if ch_id == channel_id]
            for msg_type in routes_to_remove:
                del self.routes[msg_type]
            
            return True
        return False
    
    def add_route(self, message_type: str, channel_id: str) -> bool:
        """添加路由"""
        if channel_id in self.channels:
            self.routes[message_type] = channel_id
            return True
        return False
    
    def remove_route(self, message_type: str) -> bool:
        """移除路由"""
        if message_type in self.routes:
            del self.routes[message_type]
            return True
        return False
    
    def register_handler(self, message_type: str, handler: callable) -> None:
        """注册消息处理器"""
        self.handlers[message_type] = handler
    
    async def route_message(self, message: BaseMessage) -> bool:
        """路由消息"""
        # 查找路由
        channel_id = self.routes.get(message.type)
        if not channel_id:
            # 没有找到路由，尝试本地处理
            return await self._handle_locally(message)
        
        # 获取通道
        channel = self.channels.get(channel_id)
        if not channel:
            return False
        
        # 发送消息
        try:
            return await channel.send(message)
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    async def _handle_locally(self, message: BaseMessage) -> bool:
        """本地处理消息"""
        handler = self.handlers.get(message.type)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
                return True
            except Exception as e:
                print(f"处理消息失败: {e}")
                return False
        return False
    
    async def start_listening(self, channel_id: str) -> None:
        """开始监听通道"""
        channel = self.channels.get(channel_id)
        if not channel:
            return
        
        while channel.is_connected:
            try:
                message = await channel.receive(timeout=1.0)
                if message:
                    await self.route_message(message)
            except Exception as e:
                print(f"监听通道 {channel_id} 出错: {e}")
