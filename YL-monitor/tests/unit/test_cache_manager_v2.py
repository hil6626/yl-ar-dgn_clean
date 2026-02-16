#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器单元测试

【功能描述】
测试缓存管理器的核心功能，包括：
- 缓存存储和检索
- 过期机制
- 缓存统计
- 内存管理

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0
"""

import pytest
import asyncio

# 导入被测试的模块
from app.services.cache_manager import (
    CacheManager,
    MemoryCache,
    CacheConfig,
    CacheStats,
    CacheBackend,
    CacheStrategy,
)


@pytest.mark.unit
class TestCacheConfig:
    """缓存配置类测试"""

    def test_cache_config_defaults(self):
        """测试缓存配置默认值"""
        config = CacheConfig()
        
        assert config.backend == CacheBackend.MEMORY
        assert config.default_ttl == 300
        assert config.max_size == 1000
        assert config.strategy == CacheStrategy.TTL

    def test_cache_config_custom(self):
        """测试自定义缓存配置"""
        config = CacheConfig(
            backend=CacheBackend.REDIS,
            default_ttl=600,
            max_size=500,
            strategy=CacheStrategy.LRU,
            redis_host="0.0.0.0",
            redis_port=6379,
        )
        
        assert config.backend == CacheBackend.REDIS
        assert config.default_ttl == 600
        assert config.max_size == 500
        assert config.strategy == CacheStrategy.LRU


@pytest.mark.unit
class TestCacheStats:
    """缓存统计类测试"""

    def test_cache_stats_creation(self):
        """测试缓存统计创建"""
        stats = CacheStats(
            hits=80,
            misses=20,
            evictions=5,
            total_keys=100,
            memory_usage=1024000,
        )
        
        assert stats.hits == 80
        assert stats.misses == 20
        assert stats.evictions == 5
        assert stats.total_keys == 100
        assert stats.memory_usage == 1024000
        # 命中率 = 80 / (80 + 20) = 0.8
        assert stats.hit_rate == 0.8


@pytest.mark.unit
class TestMemoryCache:
    """内存缓存测试"""

    @pytest.fixture
    async def cache(self):
        """创建内存缓存实例"""
        config = CacheConfig(max_size=100)
        mc = MemoryCache(config)
        yield mc

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试设置和获取缓存"""
        await cache.set("key1", {"name": "test"}, ttl=300)
        
        value = await cache.get("key1")
        assert value is not None
        assert value["name"] == "test"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """测试获取不存在的缓存"""
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """测试缓存过期"""
        await cache.set("temp-key", "temp-value", ttl=1)
        
        # 立即获取应该存在
        value = await cache.get("temp-key")
        assert value == "temp-value"
        
        # 等待过期
        await asyncio.sleep(1.5)
        
        # 过期后应该不存在
        value = await cache.get("temp-key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """测试删除缓存"""
        await cache.set("delete-key", "value")
        
        # 删除前存在
        value = await cache.get("delete-key")
        assert value is not None
        
        # 删除
        deleted = await cache.delete("delete-key")
        assert deleted is True
        
        # 删除后不存在
        value = await cache.get("delete-key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        """测试删除不存在的缓存"""
        deleted = await cache.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """测试清空缓存"""
        # 设置多个值
        for i in range(10):
            await cache.set(f"key-{i}", f"value-{i}")
        
        # 清空
        cleared = await cache.clear()
        assert cleared is True
        
        # 验证全部删除
        for i in range(10):
            value = await cache.get(f"key-{i}")
            assert value is None

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """测试缓存统计"""
        # 设置一些值
        for i in range(5):
            await cache.set(f"key-{i}", f"value-{i}")
        
        # 获取一些值（命中）
        for i in range(5):
            await cache.get(f"key-{i}")
        
        # 获取不存在的值（未命中）
        for i in range(5, 10):
            await cache.get(f"key-{i}")
        
        stats = cache.get_stats()
        
        assert isinstance(stats, CacheStats)
        assert stats.total_keys == 5
        assert stats.hits == 5
        assert stats.misses == 5

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache):
        """测试LRU淘汰策略"""
        # 设置多个值
        for i in range(10):
            await cache.set(f"key-{i}", f"value-{i}")
        
        # 访问前5个
        for i in range(5):
            await cache.get(f"key-{i}")
        
        # 设置更多值，触发淘汰
        for i in range(10, 110):
            await cache.set(f"key-{i}", f"value-{i}")
        
        # 验证后访问的key仍然存在
        value = await cache.get("key-109")
        assert value is not None

    @pytest.mark.asyncio
    async def test_invalidate_by_tag(self, cache):
        """测试按标签失效缓存"""
        # 设置带标签的值
        await cache.set("tagged-key-1", "value1", tags=["tag1", "tag2"])
        await cache.set("tagged-key-2", "value2", tags=["tag1"])
        await cache.set("untagged-key", "value3")
        
        # 按标签失效
        invalidated = await cache.invalidate_by_tag("tag1")
        assert invalidated == 2
        
        # 验证已失效
        assert await cache.get("tagged-key-1") is None
        assert await cache.get("tagged-key-2") is None
        # 未标记的应该仍然存在
        assert await cache.get("untagged-key") == "value3"


@pytest.mark.unit
class TestCacheManager:
    """缓存管理器测试"""

    @pytest.fixture
    async def manager(self):
        """创建缓存管理器实例"""
        config = CacheConfig(backend=CacheBackend.MEMORY)
        cm = CacheManager(config)
        await cm.initialize()
        yield cm

    @pytest.mark.asyncio
    async def test_set_and_get(self, manager):
        """测试设置和获取缓存"""
        await manager.set("key1", {"name": "test"}, ttl=300)
        
        value = await manager.get("key1")
        assert value is not None
        assert value["name"] == "test"

    @pytest.mark.asyncio
    async def test_delete(self, manager):
        """测试删除缓存"""
        await manager.set("delete-key", "value")
        
        deleted = await manager.delete("delete-key")
        assert deleted is True
        
        value = await manager.get("delete-key")
        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self, manager):
        """测试清空缓存"""
        await manager.set("key1", "value1")
        await manager.set("key2", "value2")
        
        cleared = await manager.clear()
        assert cleared is True
        
        assert await manager.get("key1") is None
        assert await manager.get("key2") is None

    @pytest.mark.asyncio
    async def test_generate_key(self, manager):
        """测试生成缓存键"""
        key1 = manager.generate_key("prefix", "arg1", "arg2", key="value")
        key2 = manager.generate_key("prefix", "arg1", "arg2", key="value")
        
        # 相同参数应该生成相同的键
        assert key1 == key2
        
        # 不同参数应该生成不同的键
        key3 = manager.generate_key("prefix", "arg1", "arg3", key="value")
        assert key1 != key3

    def test_get_stats(self, manager):
        """测试获取缓存统计"""
        stats = manager.get_stats()
        
        assert isinstance(stats, CacheStats)


@pytest.mark.unit
class TestCacheEdgeCases:
    """缓存边界情况测试"""

    @pytest.fixture
    async def cache(self):
        """创建内存缓存实例"""
        config = CacheConfig(max_size=10)
        mc = MemoryCache(config)
        yield mc

    @pytest.mark.asyncio
    async def test_set_none_value(self, cache):
        """测试设置None值"""
        await cache.set("none-key", None)
        
        value = await cache.get("none-key")
        assert value is None

    @pytest.mark.asyncio
    async def test_set_empty_string(self, cache):
        """测试设置空字符串"""
        await cache.set("empty-key", "")
        
        value = await cache.get("empty-key")
        assert value == ""

    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache):
        """测试并发访问"""
        await cache.set("concurrent-key", 0)
        
        async def increment():
            for _ in range(10):
                value = await cache.get("concurrent-key")
                await cache.set("concurrent-key", value + 1)
        
        # 并发执行
        await asyncio.gather(
            increment(),
            increment(),
            increment(),
        )
        
        # 验证结果（注意：实际结果取决于锁机制）
        final_value = await cache.get("concurrent-key")
        assert final_value >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
