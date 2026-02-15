"""
事件总线服务 - 模块间联动核心

提供发布-订阅模式的事件处理系统，支持 Scripts、DAG、AR 模块间的数据流转和状态同步。
支持同步和异步回调。
"""

from typing import Callable, Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    # 脚本相关事件
    SCRIPT_STARTED = "script:started"
    SCRIPT_COMPLETED = "script:completed"
    SCRIPT_FAILED = "script:failed"
    
    # DAG 相关事件
    DAG_NODE_STARTED = "dag:node_started"
    DAG_NODE_COMPLETED = "dag:node_completed"
    DAG_NODE_FAILED = "dag:node_failed"
    DAG_STARTED = "dag:started"
    DAG_COMPLETED = "dag:completed"
    
    # AR 相关事件
    AR_NODE_UPDATED = "ar:node_updated"
    AR_STATUS_CHANGED = "ar:status_changed"
    
    # 系统指标事件
    METRIC_CPU = "metric:cpu"
    METRIC_MEMORY = "metric:memory"
    METRIC_DISK = "metric:disk"
    METRIC_NETWORK = "metric:network"
    
    # 告警相关事件
    ALERT_TRIGGERED = "alert:triggered"
    ALERT_RECOVERED = "alert:recovered"
    ALERT_ACKNOWLEDGED = "alert:acknowledged"
    
    # 通知事件
    NOTIFICATION_BROWSER = "notification:browser"
    NOTIFICATION_EMAIL = "notification:email"
    NOTIFICATION_WEBHOOK = "notification:webhook"
    
    # 通用事件
    STATE_CHANGED = "state:changed"
    ERROR_OCCURRED = "error:occurred"
    
    # 系统事件
    SYSTEM_STARTUP = "system:startup"
    SYSTEM_SHUTDOWN = "system:shutdown"


@dataclass
class Event:
    """事件数据类"""
    type: EventType
    source: str
    target: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.type.value}:{self.source}:{self.timestamp.timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class EventSubscriber:
    """事件订阅者"""
    def __init__(
        self,
        callback: Union[Callable[['Event'], None], Callable[['Event'], Any]],
        filter_types: Optional[List[EventType]] = None,
        subscriber_id: Optional[str] = None,
    ):
        self.callback = callback
        self.filter_types = filter_types or []
        self.active = True
        self.is_async = asyncio.iscoroutinefunction(callback)
        self.subscriber_id = subscriber_id
    
    def matches(self, event: Event) -> bool:
        """检查事件是否匹配过滤条件"""
        if not self.filter_types:
            return True
        return event.type in self.filter_types


class EventBus:
    """
    事件总线 - 单例模式
    
    提供全局事件发布-订阅能力，支持模块间解耦通信。
    
    使用示例:
        # 订阅事件
        event_bus.subscribe(
            callback=on_script_completed,
            filter_types=[EventType.SCRIPT_COMPLETED]
        )
        
        # 发布事件
        event_bus.publish(Event(
            type=EventType.SCRIPT_COMPLETED,
            source="scripts_runner",
            data={"script_name": "example.py", "result": "success"}
        ))
    """
    
    _instance: Optional['EventBus'] = None
    _subscribers: List[EventSubscriber]
    _event_history: List[Event]
    _max_history: int = 1000
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._subscribers = []
        self._event_history = []
        self._initialized = True
        logger.info("事件总线初始化完成")
    
    def subscribe(
        self,
        callback: Union[Callable[[Event], None], Callable[[Event], Any]],
        filter_types: Optional[List[EventType]] = None,
        subscriber_id: Optional[str] = None
    ) -> str:
        """
        订阅事件
        
        Args:
            callback: 事件处理回调函数（支持同步或异步）
            filter_types: 过滤的事件类型列表
            subscriber_id: 订阅者标识
            
        Returns:
            订阅 ID
        """
        sid = subscriber_id or f"sub_{len(self._subscribers)}"
        subscriber = EventSubscriber(callback, filter_types, subscriber_id=sid)
        self._subscribers.append(subscriber)
        logger.info(f"事件订阅已注册: {sid}, 过滤类型: {filter_types}, 异步: {subscriber.is_async}")
        return sid
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscriber_id: 订阅 ID
            
        Returns:
            是否成功取消
        """
        for i, sub in enumerate(list(self._subscribers)):
            if sub.subscriber_id == subscriber_id:
                self._subscribers.pop(i)
                logger.info(f"事件订阅已取消: {subscriber_id}")
                return True
        return False
    
    async def publish(self, event: Event) -> List[Any]:
        """
        发布事件（异步版本）
        
        Args:
            event: 事件对象
            
        Returns:
            各订阅者处理结果列表
        """
        # 添加到历史记录
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # 通知所有匹配的订阅者
        results = []
        for subscriber in self._subscribers:
            if subscriber.active and subscriber.matches(event):
                try:
                    if subscriber.is_async:
                        result = await subscriber.callback(event)
                    else:
                        result = subscriber.callback(event)
                    results.append(result)
                    logger.debug(f"事件 {event.type.value} 已处理: {event.source}")
                except Exception as e:
                    logger.error(f"事件处理失败: {event.type.value}, 错误: {str(e)}")
                    results.append(e)
        
        return results
    
    def publish_nowait(self, event: Event):
        """
        发布事件（同步版本，不等待结果）
        
        Args:
            event: 事件对象
        """
        # 添加到历史记录
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # 同步通知所有匹配的订阅者
        for subscriber in self._subscribers:
            if subscriber.active and subscriber.matches(event):
                try:
                    if subscriber.is_async:
                        # 对于异步回调，创建任务但不等待
                        asyncio.create_task(subscriber.callback(event))
                    else:
                        subscriber.callback(event)
                    logger.debug(f"事件 {event.type.value} 已触发: {event.source}")
                except Exception as e:
                    logger.error(f"事件处理失败: {event.type.value}, 错误: {str(e)}")
    
    def publish_event(
        self,
        event_type: EventType,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        async_publish: bool = False
    ) -> Event:
        """
        便捷方法：发布事件
        
        Args:
            event_type: 事件类型
            source: 事件源
            data: 事件数据
            target: 目标模块
            async_publish: 是否异步发布
            
        Returns:
            发布的事件对象
        """
        event = Event(
            type=event_type,
            source=source,
            target=target,
            data=data or {}
        )
        if async_publish:
            asyncio.create_task(self.publish(event))
        else:
            self.publish_nowait(event)
        return event
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        获取事件历史
        
        Args:
            event_type: 过滤的事件类型
            limit: 返回数量限制
            
        Returns:
            事件列表
        """
        events = self._event_history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]
    
    def get_subscribers(self) -> List[Dict[str, Any]]:
        """获取所有订阅者信息"""
        return [
            {
                "callback": f"{sub.callback.__module__}.{sub.callback.__qualname__}",
                "filter_types": [t.value for t in sub.filter_types],
                "active": sub.active,
                "is_async": sub.is_async
            }
            for sub in self._subscribers
        ]
    
    def clear(self):
        """清空事件历史和订阅者"""
        self._event_history.clear()
        self._subscribers.clear()
        logger.info("事件总线已清空")


# 全局事件总线实例
event_bus = EventBus()
