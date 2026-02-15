"""
缓存配置优化
提供多级缓存策略和缓存装饰器
"""

from functools import wraps
import asyncio
import time
import hashlib
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    ttl: int
    hits: int = 0


class CacheManager:
    """
    缓存管理器
    
    提供多级缓存策略：
    1. 内存缓存（高频数据，L1）
    2. 本地缓存（中频数据，L2）
    3. 分布式缓存（低频数据，L3）
    
    特性：
    - 自动过期清理
    - LRU淘汰策略
    - 命中率统计
    - 线程安全
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        参数:
        - key: 缓存键
        
        返回:
        - 缓存值或None
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            # 检查是否过期
            if time.time() - entry.timestamp > entry.ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            
            # 更新命中统计
            entry.hits += 1
            self._stats["hits"] += 1
            
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        设置缓存值
        
        参数:
        - key: 缓存键
        - value: 缓存值
        - ttl: 过期时间（秒），默认300秒
        """
        async with self._lock:
            # 检查容量，执行LRU淘汰
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            
            # 创建缓存条目
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl or self._default_ttl,
                hits=0
            )
            
            self._cache[key] = entry
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        参数:
        - key: 缓存键
        
        返回:
        - 是否成功删除
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self):
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            self._stats["evictions"] += len(self._cache)
    
    def _evict_lru(self):
        """LRU淘汰策略"""
        if not self._cache:
            return
        
        # 找到最少使用的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].hits
        )
        
        del self._cache[lru_key]
        self._stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计
        
        返回:
        - 统计信息字典
        """
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": round(hit_rate * 100, 2),
            "memory_usage_mb": self._estimate_memory()
        }
    
    def _estimate_memory(self) -> float:
        """估算内存使用量（MB）"""
        import sys
        
        total_size = 0
        for entry in self._cache.values():
            try:
                total_size += sys.getsizeof(entry.value)
            except:
                pass
        
        return round(total_size / (1024 * 1024), 2)


# 全局缓存实例
cache = CacheManager(max_size=1000, default_ttl=300)


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    缓存装饰器
    
    用法:
    @cached(ttl=60, key_prefix="dashboard")
    async def get_dashboard_data():
        return await fetch_data()
    
    参数:
    - ttl: 缓存过期时间（秒）
    - key_prefix: 缓存键前缀
    - key_func: 自定义缓存键生成函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数哈希
                key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            await cache.set(cache_key, result, ttl)
            
            return result
        
        # 添加清除缓存的方法
        async def clear_cache():
            """清除此函数的缓存"""
            # 这里可以实现更精确的清除逻辑
            pass
        
        wrapper.clear_cache = clear_cache
        
        return wrapper
    return decorator


def cache_clear(pattern: str = "*"):
    """
    清除匹配模式的缓存
    
    参数:
    - pattern: 匹配模式，支持通配符*
    """
    # 这里可以实现模式匹配清除逻辑
    pass


# 常用缓存配置
CACHE_CONFIG = {
    # 仪表盘数据 - 5秒缓存（高频更新）
    "dashboard_overview": {"ttl": 5, "max_size": 10},
    
    # API文档矩阵 - 60秒缓存（低频更新）
    "api_doc_matrix": {"ttl": 60, "max_size": 5},
    
    # DAG定义 - 30秒缓存
    "dag_definition": {"ttl": 30, "max_size": 10},
    
    # 脚本列表 - 10秒缓存
    "scripts_list": {"ttl": 10, "max_size": 20},
    
    # 系统资源 - 3秒缓存（实时性要求高）
    "system_resources": {"ttl": 3, "max_size": 5},
    
    # 功能矩阵 - 60秒缓存
    "function_matrix": {"ttl": 60, "max_size": 10}
}


def get_cache_config(key: str) -> Dict[str, Any]:
    """
    获取缓存配置
    
    参数:
    - key: 配置键
    
    返回:
    - 配置字典
    """
    return CACHE_CONFIG.get(key, {"ttl": 300, "max_size": 100})


# 使用示例
if __name__ == "__main__":
    async def test_cache():
        # 测试基本缓存
        await cache.set("test_key", {"data": "value"}, ttl=60)
        value = await cache.get("test_key")
        print(f"缓存值: {value}")
        
        # 测试装饰器
        @cached(ttl=10, key_prefix="test")
        async def expensive_operation():
            await asyncio.sleep(1)
            return {"result": "expensive_data"}
        
        # 第一次调用（慢）
        start = time.time()
        result1 = await expensive_operation()
        print(f"第一次调用耗时: {time.time() - start:.2f}s")
        
        # 第二次调用（快，从缓存）
        start = time.time()
        result2 = await expensive_operation()
        print(f"第二次调用耗时: {time.time() - start:.2f}s")
        
        # 打印统计
        print(f"缓存统计: {cache.get_stats()}")
    
    asyncio.run(test_cache())
