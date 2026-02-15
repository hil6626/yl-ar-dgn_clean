"""
缓存管理器服务

功能:
- 多级缓存策略 (内存 + Redis/Memcached)
- 查询结果缓存
- 缓存失效管理
- 性能监控

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheBackend(str, Enum):
    """缓存后端类型"""
    MEMORY = "memory"      # 内存缓存
    REDIS = "redis"        # Redis缓存
    MEMCACHED = "memcached"  # Memcached缓存


class CacheStrategy(str, Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    TTL = "ttl"           # 生存时间
    LFU = "lfu"           # 最少使用频率


@dataclass
class CacheConfig:
    """缓存配置"""
    backend: CacheBackend = CacheBackend.MEMORY
    default_ttl: int = 300  # 默认5分钟
    max_size: int = 1000    # 最大缓存条目数
    strategy: CacheStrategy = CacheStrategy.TTL
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    memcached_servers: List[str] = field(default_factory=lambda: ["localhost:11211"])


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_keys: int = 0
    memory_usage: int = 0  # 字节
    hit_rate: float = 0.0   # 命中率


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # 检查TTL
            if entry.get('expire_at') and current_time > entry['expire_at']:
                del self._cache[key]
                del self._access_times[key]
                if key in self._access_counts:
                    del self._access_counts[key]
                self._stats.evictions += 1
                self._stats.misses += 1
                return None
            
            # 更新访问统计
            self._access_times[key] = current_time
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            self._stats.hits += 1
            self._update_hit_rate()
            
            return entry['value']
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """设置缓存值"""
        async with self._lock:
            # 检查是否需要淘汰
            await self._evict_if_needed()
            
            expire_at = None
            if ttl or self.config.default_ttl:
                expire_at = time.time() + (ttl or self.config.default_ttl)
            
            self._cache[key] = {
                'value': value,
                'expire_at': expire_at,
                'tags': tags or [],
                'created_at': time.time()
            }
            self._access_times[key] = time.time()
            self._access_counts[key] = 0
            self._stats.total_keys = len(self._cache)
            
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                if key in self._access_counts:
                    del self._access_counts[key]
                self._stats.total_keys = len(self._cache)
                return True
            return False
    
    async def clear(self) -> bool:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._access_counts.clear()
            self._stats.total_keys = 0
            return True
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """按标签失效缓存"""
        async with self._lock:
            keys_to_delete = [
                key for key, entry in self._cache.items() 
                if tag in entry.get('tags', [])
            ]
            for key in keys_to_delete:
                del self._cache[key]
                del self._access_times[key]
                if key in self._access_counts:
                    del self._access_counts[key]
            
            self._stats.total_keys = len(self._cache)
            return len(keys_to_delete)
    
    async def _evict_if_needed(self):
        """根据需要淘汰缓存"""
        if len(self._cache) < self.config.max_size:
            return
        
        # 根据策略选择淘汰算法
        if self.config.strategy == CacheStrategy.LRU:
            # 淘汰最久未访问的
            oldest_key = min(self._access_times, key=self._access_times.get)
        elif self.config.strategy == CacheStrategy.LFU:
            # 淘汰访问次数最少的
            oldest_key = min(self._access_counts, key=self._access_counts.get)
        else:
            # 默认淘汰最久未访问的
            oldest_key = min(self._access_times, key=self._access_times.get)
        
        del self._cache[oldest_key]
        del self._access_times[oldest_key]
        if oldest_key in self._access_counts:
            del self._access_counts[oldest_key]
        self._stats.evictions += 1
    
    def _update_hit_rate(self):
        """更新命中率"""
        total = self._stats.hits + self._stats.misses
        if total > 0:
            self._stats.hit_rate = self._stats.hits / total
    
    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        self._update_hit_rate()
        self._stats.total_keys = len(self._cache)
        self._stats.memory_usage = self._estimate_memory_usage()
        return self._stats
    
    def _estimate_memory_usage(self) -> int:
        """估算内存使用量"""
        try:
            import sys
            total = sys.getsizeof(self._cache)
            for key, entry in self._cache.items():
                total += sys.getsizeof(key)
                total += sys.getsizeof(entry)
            return total
        except:
            return len(self._cache) * 1024  # 粗略估算


class CacheManager:
    """
    缓存管理器
    
    提供统一的缓存接口，支持多级缓存策略
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._backend: Optional[Union[MemoryCache, Any]] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化缓存后端"""
        if self._initialized:
            return
        
        if self.config.backend == CacheBackend.MEMORY:
            self._backend = MemoryCache(self.config)
            logger.info("内存缓存已初始化")
        elif self.config.backend == CacheBackend.REDIS:
            try:
                import aioredis
                self._backend = await aioredis.create_redis_pool(
                    f"redis://{self.config.redis_host}:{self.config.redis_port}/{self.config.redis_db}"
                )
                logger.info("Redis缓存已初始化")
            except ImportError:
                logger.warning("aioredis未安装，回退到内存缓存")
                self._backend = MemoryCache(self.config)
            except Exception as e:
                logger.error(f"Redis连接失败: {e}，回退到内存缓存")
                self._backend = MemoryCache(self.config)
        elif self.config.backend == CacheBackend.MEMCACHED:
            try:
                import aiomcache
                self._backend = aiomcache.Client(self.config.memcached_servers[0])
                logger.info("Memcached缓存已初始化")
            except ImportError:
                logger.warning("aiomcache未安装，回退到内存缓存")
                self._backend = MemoryCache(self.config)
            except Exception as e:
                logger.error(f"Memcached连接失败: {e}，回退到内存缓存")
                self._backend = MemoryCache(self.config)
        
        self._initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._initialized:
            await self.initialize()
        
        if self._backend is None:
            return None
        
        try:
            if isinstance(self._backend, MemoryCache):
                return await self._backend.get(key)
            else:
                # Redis/Memcached实现
                value = await self._backend.get(key.encode())
                if value:
                    return json.loads(value.decode())
                return None
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """设置缓存值"""
        if not self._initialized:
            await self.initialize()
        
        if self._backend is None:
            return False
        
        try:
            if isinstance(self._backend, MemoryCache):
                return await self._backend.set(key, value, ttl, tags)
            else:
                # Redis/Memcached实现
                expire = ttl or self.config.default_ttl
                serialized = json.dumps(value).encode()
                await self._backend.set(key.encode(), serialized, expire=expire)
                return True
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._initialized:
            await self.initialize()
        
        if self._backend is None:
            return False
        
        try:
            if isinstance(self._backend, MemoryCache):
                return await self._backend.delete(key)
            else:
                await self._backend.delete(key.encode())
                return True
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False
    
    async def clear(self) -> bool:
        """清空缓存"""
        if not self._initialized:
            await self.initialize()
        
        if self._backend is None:
            return False
        
        try:
            if isinstance(self._backend, MemoryCache):
                return await self._backend.clear()
            else:
                await self._backend.flush_all()
                return True
        except Exception as e:
            logger.error(f"缓存清空失败: {e}")
            return False
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """按标签失效缓存"""
        if not self._initialized:
            await self.initialize()
        
        if isinstance(self._backend, MemoryCache):
            return await self._backend.invalidate_by_tag(tag)
        
        # Redis/Memcached不支持标签失效，需要其他策略
        logger.warning("当前缓存后端不支持标签失效")
        return 0
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        if isinstance(self._backend, MemoryCache):
            return self._backend.get_stats()
        return CacheStats()
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    tags: Optional[List[str]] = None,
    cache_manager: Optional[CacheManager] = None
):
    """
    缓存装饰器
    
    用法:
        @cached(ttl=300, key_prefix="alerts")
        async def get_alerts(filter_params):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 获取缓存管理器
            cm = cache_manager
            if cm is None:
                # 尝试从全局获取
                cm = getattr(wrapper, '_cache_manager', None)
            
            if cm is None:
                # 没有缓存管理器，直接执行
                return await func(*args, **kwargs)
            
            # 生成缓存键
            prefix = key_prefix or func.__name__
            cache_key = cm.generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await cm.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 写入缓存
            await cm.set(cache_key, result, ttl=ttl, tags=tags)
            logger.debug(f"缓存写入: {cache_key}")
            
            return result
        
        # 附加缓存管理器设置方法
        def set_cache_manager(cm: CacheManager):
            wrapper._cache_manager = cm
        
        wrapper.set_cache_manager = set_cache_manager
        return wrapper
    return decorator


# 全局缓存管理器实例
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def set_cache_manager(cm: CacheManager):
    """设置全局缓存管理器"""
    global _global_cache_manager
    _global_cache_manager = cm


# 常用缓存键前缀
CACHE_KEYS = {
    'ALERT_LIST': 'alerts:list',
    'ALERT_STATS': 'alerts:stats',
    'ALERT_RULES': 'alerts:rules',
    'DAG_LIST': 'dag:list',
    'DAG_STATUS': 'dag:status',
    'SCRIPT_LIST': 'scripts:list',
    'SCRIPT_STATUS': 'scripts:status',
    'METRICS_DATA': 'metrics:data',
    'DASHBOARD_SUMMARY': 'dashboard:summary',
}
