"""
数据库查询优化工具
提供查询优化、批量操作和连接池管理
"""

from functools import wraps
from typing import Callable, Any, List, Optional, Dict
import asyncio
import time
from contextlib import asynccontextmanager


class QueryOptimizer:
    """
    查询优化器
    
    功能：
    1. 查询缓存
    2. 批量查询合并
    3. N+1查询检测
    4. 查询性能分析
    """
    
    def __init__(self):
        self._query_stats: Dict[str, Dict[str, Any]] = {}
        self._batch_queue: Dict[str, List] = {}
        self._batch_timers: Dict[str, asyncio.Task] = {}
    
    def track_query(self, query_name: str, duration: float, rows: int = 0):
        """
        跟踪查询性能
        
        参数:
        - query_name: 查询名称
        - duration: 执行时间（秒）
        - rows: 返回行数
        """
        if query_name not in self._query_stats:
            self._query_stats[query_name] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "max_time": 0,
                "min_time": float('inf'),
                "rows": 0
            }
        
        stats = self._query_stats[query_name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["max_time"] = max(stats["max_time"], duration)
        stats["min_time"] = min(stats["min_time"], duration)
        stats["rows"] += rows
    
    def get_slow_queries(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        获取慢查询
        
        参数:
        - threshold: 慢查询阈值（秒）
        
        返回:
        - 慢查询列表
        """
        slow_queries = []
        for name, stats in self._query_stats.items():
            if stats["avg_time"] > threshold:
                slow_queries.append({
                    "name": name,
                    "avg_time": round(stats["avg_time"], 3),
                    "max_time": round(stats["max_time"], 3),
                    "count": stats["count"]
                })
        
        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取查询统计
        
        返回:
        - 统计信息
        """
        total_queries = sum(s["count"] for s in self._query_stats.values())
        total_time = sum(s["total_time"] for s in self._query_stats.values())
        
        return {
            "total_queries": total_queries,
            "total_time": round(total_time, 3),
            "avg_time": round(total_time / total_queries, 3) if total_queries > 0 else 0,
            "query_count": len(self._query_stats),
            "slow_queries": len(self.get_slow_queries())
        }


# 全局查询优化器实例
query_optimizer = QueryOptimizer()


def optimized_query(query_name: Optional[str] = None):
    """
    查询优化装饰器
    
    自动跟踪查询性能
    
    用法:
    @optimized_query("get_user_by_id")
    async def get_user(user_id: int):
        return await db.query(User).filter_by(id=user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        name = query_name or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 计算执行时间
                duration = time.time() - start_time
                
                # 估算返回行数
                rows = 0
                if isinstance(result, list):
                    rows = len(result)
                elif result is not None:
                    rows = 1
                
                # 跟踪查询
                query_optimizer.track_query(name, duration, rows)
                
                return result
                
            except Exception as e:
                # 记录失败查询
                duration = time.time() - start_time
                query_optimizer.track_query(f"{name}_error", duration, 0)
                raise
        
        return wrapper
    return decorator


class BatchQueryManager:
    """
    批量查询管理器
    
    将多个小查询合并为批量查询，减少数据库往返
    """
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 0.01):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._queues: Dict[str, List] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._timers: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def add(
        self,
        queue_name: str,
        item: Any,
        callback: Callable[[List[Any]], Any]
    ) -> Any:
        """
        添加查询到批量队列
        
        参数:
        - queue_name: 队列名称
        - item: 查询项
        - callback: 批量处理回调函数
        
        返回:
        - 查询结果
        """
        async with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = []
                self._callbacks[queue_name] = callback
            
            # 创建Future等待结果
            future = asyncio.Future()
            self._queues[queue_name].append((item, future))
            
            # 检查是否需要立即刷新
            if len(self._queues[queue_name]) >= self.batch_size:
                await self._flush(queue_name)
            elif queue_name not in self._timers or self._timers[queue_name].done():
                # 设置定时刷新
                self._timers[queue_name] = asyncio.create_task(
                    self._schedule_flush(queue_name)
                )
            
            return await future
    
    async def _schedule_flush(self, queue_name: str):
        """定时刷新队列"""
        await asyncio.sleep(self.flush_interval)
        await self._flush(queue_name)
    
    async def _flush(self, queue_name: str):
        """刷新队列"""
        async with self._lock:
            if queue_name not in self._queues or not self._queues[queue_name]:
                return
            
            # 获取队列数据
            queue_data = self._queues[queue_name]
            self._queues[queue_name] = []
            
            # 分离items和futures
            items = [item for item, _ in queue_data]
            futures = [future for _, future in queue_data]
            
            # 执行批量查询
            try:
                callback = self._callbacks[queue_name]
                results = await callback(items)
                
                # 分发结果
                for future, result in zip(futures, results):
                    if not future.done():
                        future.set_result(result)
                        
            except Exception as e:
                # 通知所有等待者
                for future in futures:
                    if not future.done():
                        future.set_exception(e)
    
    async def flush_all(self):
        """刷新所有队列"""
        for queue_name in list(self._queues.keys()):
            await self._flush(queue_name)


# 全局批量查询管理器
batch_manager = BatchQueryManager(batch_size=100, flush_interval=0.01)


def batch_query(batch_size: int = 100, flush_interval: float = 0.01):
    """
    批量查询装饰器
    
    将多个小查询合并为批量查询
    
    用法:
    @batch_query(batch_size=50)
    async def get_users_by_ids(user_ids: List[int]) -> List[User]:
        return await db.query(User).filter(User.id.in_(user_ids)).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取ID参数（假设第一个参数是ID列表）
            if not args or not isinstance(args[0], list):
                # 如果不是批量查询，直接执行
                return await func(*args, **kwargs)
            
            ids = args[0]
            
            # 使用批量查询管理器
            results = []
            for id in ids:
                result = await batch_manager.add(
                    func.__name__,
                    id,
                    func
                )
                results.append(result)
            
            return results
        
        return wrapper
    return decorator


class ConnectionPoolManager:
    """
    连接池管理器
    
    管理数据库连接池，优化连接复用
    """
    
    def __init__(
        self,
        min_connections: int = 5,
        max_connections: int = 20,
        max_idle_time: int = 300
    ):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self._pool: List[Any] = []
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._stats = {
            "created": 0,
            "reused": 0,
            "closed": 0
        }
    
    @asynccontextmanager
    async def acquire(self):
        """
        获取连接上下文管理器
        
        用法:
        async with pool.acquire() as conn:
            await conn.execute(query)
        """
        conn = None
        try:
            conn = await self._get_connection()
            self._in_use.add(id(conn))
            yield conn
        finally:
            if conn:
                self._in_use.discard(id(conn))
                await self._release_connection(conn)
    
    async def _get_connection(self) -> Any:
        """获取可用连接"""
        async with self._lock:
            # 尝试复用空闲连接
            while self._pool:
                conn = self._pool.pop()
                
                # 检查连接是否有效
                if await self._is_valid(conn):
                    self._stats["reused"] += 1
                    return conn
                else:
                    await self._close_connection(conn)
            
            # 创建新连接
            if len(self._in_use) < self.max_connections:
                conn = await self._create_connection()
                self._stats["created"] += 1
                return conn
            
            # 等待连接可用
            while len(self._in_use) >= self.max_connections:
                await asyncio.sleep(0.1)
            
            conn = await self._create_connection()
            self._stats["created"] += 1
            return conn
    
    async def _release_connection(self, conn: Any):
        """释放连接回池"""
        async with self._lock:
            if len(self._pool) < self.min_connections:
                self._pool.append(conn)
            else:
                await self._close_connection(conn)
    
    async def _create_connection(self) -> Any:
        """创建新连接"""
        # 这里应该实现实际的数据库连接创建
        # 返回模拟连接对象
        return {"id": id(object()), "created_at": time.time()}
    
    async def _close_connection(self, conn: Any):
        """关闭连接"""
        self._stats["closed"] += 1
    
    async def _is_valid(self, conn: Any) -> bool:
        """检查连接是否有效"""
        # 检查空闲时间
        idle_time = time.time() - conn.get("created_at", 0)
        return idle_time < self.max_idle_time
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        return {
            "pool_size": len(self._pool),
            "in_use": len(self._in_use),
            "total": len(self._pool) + len(self._in_use),
            **self._stats
        }


# 常用查询优化配置
QUERY_OPTIMIZATION_CONFIG = {
    # 默认查询超时（秒）
    "default_timeout": 30,
    
    # 慢查询阈值（秒）
    "slow_query_threshold": 0.1,
    
    # 最大返回行数
    "max_rows": 10000,
    
    # 批量查询大小
    "batch_size": 100,
    
    # 连接池配置
    "connection_pool": {
        "min_size": 5,
        "max_size": 20,
        "max_idle_time": 300
    }
}


def get_optimization_config() -> Dict[str, Any]:
    """获取优化配置"""
    return QUERY_OPTIMIZATION_CONFIG.copy()


# 查询缓存装饰器
def query_with_cache(ttl: int = 60):
    """
    带缓存的查询装饰器
    
    自动缓存查询结果，减少数据库压力
    
    参数:
    - ttl: 缓存有效期（秒）
    
    用法:
    @query_with_cache(ttl=30)
    async def get_user_by_id(user_id: int):
        return await db.query(User).filter_by(id=user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 检查缓存
            now = time.time()
            if cache_key in cache:
                result, expiry = cache[cache_key]
                if now < expiry:
                    return result
            
            # 执行查询
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache[cache_key] = (result, now + ttl)
            
            # 清理过期缓存
            expired_keys = [
                k for k, (_, exp) in cache.items() 
                if now > exp
            ]
            for k in expired_keys:
                del cache[k]
            
            return result
        
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    async def test_optimizer():
        # 测试查询优化器
        @optimized_query("test_query")
        async def sample_query():
            await asyncio.sleep(0.1)
            return [{"id": 1, "name": "test"}]
        
        # 执行多次查询
        for _ in range(5):
            await sample_query()
        
        # 打印统计
        print("查询统计:", query_optimizer.get_stats())
        print("慢查询:", query_optimizer.get_slow_queries())
    
    asyncio.run(test_optimizer())
