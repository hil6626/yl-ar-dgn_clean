"""
通信管理器
"""

import asyncio
from typing import Dict, Optional
from .protocol import MessageRouter, JSONMessage, MessagePriority
from .channels import DirectCallChannel

class CommunicationManager:
    """通信管理器"""
    
    def __init__(self):
        self.router = MessageRouter()
        self._initialize_channels()
    
    def _initialize_channels(self):
        """初始化通信通道"""
        # 注册直接调用通道
        direct_channel = DirectCallChannel("direct_default")
        asyncio.create_task(direct_channel.connect())
        self.router.register_channel("direct_default", direct_channel)
        
        # 设置默认路由
        self.router.add_route("*", "direct_default")
    
    async def send_message(
        self,
        message_type: str,
        data: dict,
        receiver: str = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        timeout: int = 30
    ) -> bool:
        """发送消息"""
        message = JSONMessage(
            message_type=message_type,
            data=data,
            receiver=receiver,
            priority=priority,
            timeout=timeout
        )
        
        return await self.router.route_message(message)
    
    def register_handler(self, message_type: str, handler: callable):
        """注册消息处理器"""
        self.router.register_handler(message_type, handler)
    
    def register_channel(self, channel_id: str, channel):
        """注册通信通道"""
        self.router.register_channel(channel_id, channel)
    
    def add_route(self, message_type: str, channel_id: str) -> bool:
        """添加路由"""
        return self.router.add_route(message_type, channel_id)
    
    async def start(self):
        """启动通信管理器"""
        # 启动所有通道的监听
        for channel_id, channel in self.router.channels.items():
            if hasattr(channel, 'start_listening'):
                asyncio.create_task(channel.start_listening(channel_id))

# 全局通信管理器实例
comm_manager = CommunicationManager()

# 使用装饰器简化消息处理
def message_handler(message_type: str):
    """消息处理器装饰器"""
    def decorator(func):
        comm_manager.register_handler(message_type, func)
        return func
    return decorator

# 使用示例
@message_handler("script.execute")
async def handle_script_execute(message):
    """处理脚本执行消息"""
    print(f"收到脚本执行请求: {message.data}")
    # 实际的脚本执行逻辑
    # ...
    
    # 发送执行结果
    await comm_manager.send_message(
        "script.execute.result",
        {
            "script_name": message.data.get("script_name"),
            "status": "success",
            "result": "脚本执行完成"
        },
        receiver=message.sender
    )
