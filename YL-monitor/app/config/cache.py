"""
缓存配置模块
支持Redis和本地内存缓存
"""

import os
import json
import hashlib
import logging
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheConfig:
    """缓存配置类"""
    
    def __init__(self):
        self.cache_type = os.getenv('CACHE_TYPE', 'simple')
        self.default_timeout = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
        
        # Redis配置
        self.redis_host = os.getenv('CACHE_REDIS_HOST', '0.0.0.0')
        self.redis_port = int(os.getenv('CACHE_REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('CACHE_REDIS_DB', '0'))
        self.redis_password = os.getenv('CACHE_REDIS_PASSWORD', '')
        
    def get_cache(self):
        """获取缓存实例"""
        if self.cache_type == 'redis':
            return RedisCache(self)
        else:
            return SimpleCache(self)

class SimpleCache:
    """简单内存缓存（基于字典）"""
    
    def __init__(self, config):
        self.config = config
        self._cache = {}
        self._timeouts = {}
        
    def get(self, key):
        """获取缓存值"""
        if key in self._cache:
            # 检查是否过期
            if key in self._timeouts:
                if datetime.now() > self._timeouts[key]:
                    self.delete(key)
                    return None
            return self._cache[key]
        return None
        
    def set(self, key, value, timeout=None):
        """设置缓存值"""
        if timeout is None:
            timeout = self.config.default_timeout
            
        self._cache[key] = value
        self._timeouts[key] = datetime.now() + timedelta(seconds=timeout)
        
    def delete(self, key):
        """删除缓存值"""
        self._cache.pop(key, None)
        self._timeouts.pop(key, None)
        
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._timeouts.clear()
        
    def get_stats(self):
        """获取缓存统计"""
        # 清理过期项
        now = datetime.now()
        expired = [k for k, v in self._timeouts.items() if v < now]
        for k in expired:
            self.delete(k)
            
        return {
            "type": "simple",
            "size": len(self._cache),
            "max_size": "unlimited"
        }

class RedisCache:
    """Redis缓存（需要redis-py包）"""
    
    def __init__(self, config):
        self.config = config
        self._redis = None
        self._connect()
        
    def _connect(self):
        """连接Redis"""
        try:
            import redis
            self._redis = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password or None,
                decode_responses=True
            )
            self._redis.ping()
            logger.info("Redis缓存连接成功")
        except ImportError:
            logger.warning("redis-py未安装，回退到简单缓存")
            raise
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
            
    def get(self, key):
        """获取缓存值"""
        try:
            value = self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get失败: {e}")
            return None
            
    def set(self, key, value, timeout=None):
        """设置缓存值"""
        if timeout is None:
            timeout = self.config.default_timeout
            
        try:
            serialized = json.dumps(value)
            self._redis.setex(key, timeout, serialized)
        except Exception as e:
            logger.error(f"Redis set失败: {e}")
            
    def delete(self, key):
        """删除缓存值"""
        try:
            self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete失败: {e}")
            
    def clear(self):
        """清空缓存"""
        try:
            self._redis.flushdb()
        except Exception as e:
            logger.error(f"Redis clear失败: {e}")
            
    def get_stats(self):
        """获取缓存统计"""
        try:
            info = self._redis.info()
            return {
                "type": "redis",
                "used_memory": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "total_keys": self._redis.dbsize()
            }
        except Exception as e:
            logger.error(f"Redis stats失败: {e}")
            return {"type": "redis", "error": str(e)}

# 全局缓存实例
_cache_instance = None

def init_cache():
    """初始化缓存"""
    global _cache_instance
    
    if _cache_instance is None:
        config = CacheConfig()
        _cache_instance = config.get_cache()
        logger.info(f"缓存初始化完成: {config.cache_type}")
        
    return _cache_instance

def get_cache():
    """获取缓存实例"""
    global _cache_instance
    
    if _cache_instance is None:
        init_cache()
        
    return _cache_instance

def cached(timeout=None, key_prefix=''):
    """
    缓存装饰器
    
    用法:
        @cached(timeout=60, key_prefix='user')
        def get_user(user_id):
            return db.query(user_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            cache = get_cache()
            result = cache.get(cache_key)
            
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
                
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator

def _generate_cache_key(prefix, func_name, args, kwargs):
    """生成缓存键"""
    key_data = {
        'prefix': prefix,
        'func': func_name,
        'args': args,
        'kwargs': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()

def clear_cache():
    """清空缓存"""
    cache = get_cache()
    cache.clear()
    logger.info("缓存已清空")
    
def get_cache_stats():
    """获取缓存统计"""
    cache = get_cache()
    return cache.get_stats()
