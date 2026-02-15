"""
增强型事件总线
支持事件追踪、中间件、优先级、持久化
"""

import asyncio
import json
import uuid
import time
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from collections import deque
import threading


class EventPriority(Enum):
    """事件优先级"""
    CRITICAL = 0   # 关键事件，立即处理
    HIGH = 1       # 高优先级
    NORMAL = 2     # 普通优先级
    LOW = 3        # 低优先级
    BACKGROUND = 4 # 后台任务


@dataclass
class Event:
    """事件对象"""
    id: str
    type: str
    data: Any
    source: str
    timestamp: datetime
    priority: EventPriority
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.priority, int):
            self.priority = EventPriority(self.priority)


class EventMiddleware:
    """事件中间件基类"""
    
    def before_emit(self, event: Event) -> Optional[Event]:
        """
        事件发送前处理
        
        返回：
            Event: 继续处理事件
            None: 拦截事件
        """
        return event
    
    def after_emit(self, event: Event, result: Any):
        """事件发送后处理"""
        pass
    
    def on_error(self, event: Event, error: Exception):
        """事件处理错误时调用"""
        pass


class EnhancedEventBus:
    """
    增强型事件总线
    
    特性：
    1. 事件优先级队列
    2. 中间件支持
    3. 事件历史追踪
    4. 异步/同步双模式
    5. 事件持久化
    6. 订阅者管理
    7. 性能指标统计
    """
    
    def __init__(self, max_history: int = 10000, enable_persistence: bool = False):
        self._handlers: Dict[str, List[Dict]] = {}  # event_type -> [{handler, priority, filter}]
        self._middleware: List[EventMiddleware] = []
        self._history: deque = deque(maxlen=max_history)
        self._enable_persistence = enable_persistence
        self._persistence_file = "logs/event_bus.jsonl"
        self._lock = threading.RLock()
        self._stats = {
            'emitted': 0,
            'handled': 0,
            'errors': 0,
            'dropped': 0
        }
        self._running = False
        self._event_queue: asyncio.PriorityQueue = None
        self._worker_task = None
        
        if enable_persistence:
            self._init_persistence()
    
    def _init_persistence(self):
        """初始化持久化"""
        import os
        os.makedirs(os.path.dirname(self._persistence_file), exist_ok=True)
    
    def _persist_event(self, event: Event):
        """持久化事件"""
        if not self._enable_persistence:
            return
        
        try:
            with open(self._persistence_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event), default=str, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"事件持久化失败: {e}")
    
    def add_middleware(self, middleware: EventMiddleware):
        """添加中间件"""
        self._middleware.append(middleware)
    
    def remove_middleware(self, middleware: EventMiddleware):
        """移除中间件"""
        self._middleware = [m for m in self._middleware if m != middleware]
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None,
        subscriber_id: Optional[str] = None
    ):
        """
        订阅事件
        
        参数：
            event_type: 事件类型
            handler: 事件处理函数
            priority: 处理优先级
            filter_func: 事件过滤函数
            subscriber_id: 订阅者标识
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            self._handlers[event_type].append({
                'handler': handler,
                'priority': priority.value,
                'filter': filter_func,
                'subscriber_id': subscriber_id or str(uuid.uuid4()),
                'subscribed_at': datetime.now().isoformat()
            })
            
            # 按优先级排序
            self._handlers[event_type].sort(key=lambda x: x['priority'])
    
    def unsubscribe(self, event_type: str, subscriber_id: str) -> bool:
        """取消订阅"""
        with self._lock:
            if event_type not in self._handlers:
                return False
            
            original_count = len(self._handlers[event_type])
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h['subscriber_id'] != subscriber_id
            ]
            
            return len(self._handlers[event_type]) < original_count
    
    def emit(
        self,
        event_type: str,
        data: Any,
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        发送事件（同步模式）
        
        返回：
            str: 事件ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now(),
            priority=priority,
            metadata=metadata or {}
        )
        
        # 执行中间件（前置）
        for middleware in self._middleware:
            event = middleware.before_emit(event)
            if event is None:
                self._stats['dropped'] += 1
                return None
        
        # 记录历史
        self._history.append(asdict(event))
        self._persist_event(event)
        self._stats['emitted'] += 1
        
        # 分发事件
        self._dispatch_sync(event)
        
        # 执行中间件（后置）
        for middleware in self._middleware:
            try:
                middleware.after_emit(event, None)
            except Exception as e:
                middleware.on_error(event, e)
        
        return event.id
    
    async def emit_async(
        self,
        event_type: str,
        data: Any,
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        发送事件（异步模式）
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now(),
            priority=priority,
            metadata=metadata or {}
        )
        
        # 执行中间件
        for middleware in self._middleware:
            event = middleware.before_emit(event)
            if event is None:
                self._stats['dropped'] += 1
                return None
        
        # 记录历史
        self._history.append(asdict(event))
        self._persist_event(event)
        self._stats['emitted'] += 1
        
        # 异步分发
        await self._dispatch_async(event)
        
        return event.id
    
    def _dispatch_sync(self, event: Event):
        """同步分发事件"""
        handlers = self._handlers.get(event.type, [])
        
        for handler_info in handlers:
            try:
                # 检查过滤器
                if handler_info['filter'] and not handler_info['filter'](event):
                    continue
                
                # 调用处理器
                handler_info['handler'](event)
                self._stats['handled'] += 1
                
            except Exception as e:
                self._stats['errors'] += 1
                print(f"事件处理错误 [{event.type}]: {e}")
                
                # 通知中间件
                for middleware in self._middleware:
                    middleware.on_error(event, e)
    
    async def _dispatch_async(self, event: Event):
        """异步分发事件"""
        handlers = self._handlers.get(event.type, [])
        
        tasks = []
        for handler_info in handlers:
            try:
                if handler_info['filter'] and not handler_info['filter'](event):
                    continue
                
                # 创建任务
                task = self._run_handler(handler_info['handler'], event)
                tasks.append(task)
                
            except Exception as e:
                self._stats['errors'] += 1
                print(f"创建事件处理任务失败 [{event.type}]: {e}")
        
        # 并发执行
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_handler(self, handler: Callable, event: Event):
        """运行事件处理器"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
            self._stats['handled'] += 1
        except Exception as e:
            self._stats['errors'] += 1
            print(f"异步事件处理错误 [{event.type}]: {e}")
    
    def get_history(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取事件历史
        
        支持按类型、时间范围过滤
        """
        history = list(self._history)
        
        if event_type:
            history = [h for h in history if h['type'] == event_type]
        
        if start_time:
            history = [
                h for h in history
                if datetime.fromisoformat(h['timestamp']) >= start_time
            ]
        
        if end_time:
            history = [
                h for h in history
                if datetime.fromisoformat(h['timestamp']) <= end_time
            ]
        
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self._stats.copy()
    
    def get_subscribers(self, event_type: Optional[str] = None) -> Dict[str, List[Dict]]:
        """获取订阅者信息"""
        with self._lock:
            if event_type:
                return {event_type: self._handlers.get(event_type, [])}
            return dict(self._handlers)
    
    def clear_history(self):
        """清空历史"""
        self._history.clear()
    
    def start_async_processor(self):
        """启动异步处理器"""
        if self._running:
            return
        
        self._running = True
        self._event_queue = asyncio.PriorityQueue()
        self._worker_task = asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        """处理事件队列"""
        while self._running:
            try:
                # 获取事件（优先级队列）
                priority, event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._dispatch_async(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"队列处理错误: {e}")
    
    def stop_async_processor(self):
        """停止异步处理器"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()


# 全局事件总线实例
enhanced_event_bus = EnhancedEventBus(
    max_history=10000,
    enable_persistence=True
)


# 使用示例
if __name__ == "__main__":
    # 定义事件处理器
    def on_script_started(event: Event):
        print(f"脚本启动: {event.data.get('script_id')}")
    
    def on_dag_completed(event: Event):
        print(f"DAG完成: {event.data.get('dag_id')}")
    
    # 订阅事件
    enhanced_event_bus.subscribe('script.started', on_script_started)
    enhanced_event_bus.subscribe('dag.completed', on_dag_completed, priority=EventPriority.HIGH)
    
    # 发送事件
    enhanced_event_bus.emit('script.started', {
        'script_id': '01_cpu_usage_monitor',
        'params': {}
    }, source='scripts_runner')
    
    # 获取统计
    print(f"事件统计: {enhanced_event_bus.get_stats()}")
