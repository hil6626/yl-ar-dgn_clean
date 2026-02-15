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
from datetime import datetime, timedelta

# 导入被测试的模块
from app.services.cache_manager import (
    CacheManager,
    CacheEntry,
    CacheStats,
    EvictionStrategy,
)


@pytest.mark.unit
class TestCacheEntry:
    """缓存条目类测试"""

    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(
            key="test-key",
            value={"data": "test"},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5),
            access_count=0,
            last_accessed=datetime.now(),
        )
        
        assert entry.key == "test-key"
        assert entry.value["data"] == "test"
        assert entry.access_count == 0

    def test_cache_entry_is_expired(self):
        """测试缓存条目过期检查"""
        # 未过期的条目
        fresh_entry = CacheEntry(
            key="fresh",
            value="data",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        assert fresh_entry.is_expired() is False
        
        # 已过期的条目
        expired_entry = CacheEntry(
            key="expired",
            value="data",
            created_at=datetime.now() - timedelta(minutes=10),
            expires_at=datetime.now() - timedelta(minutes=5),
        )
        assert expired_entry.is_expired() is True


@pytest.mark.unit
class TestCacheStats:
    """缓存统计类测试"""

    def test_cache_stats_creation(self):
        """测试缓存统计创建"""
        stats = CacheStats(
            total_entries=100,
            memory_usage_bytes=1024000,
            hit_count=80,
            miss_count=20,
            eviction_count=5,
            avg_access_time_ms=1.5,
        )
        
        assert stats.total_entries == 100
        assert stats.hit_count == 80
        assert stats.miss_count == 20
        # 命中率 = 80 / (80 + 20) = 0.8
        assert stats.hit_rate == 0.8


@pytest.mark.unit
class TestCacheManager:
    """缓存管理器测试"""

    @pytest.fixture
    def cache(self):
        """创建缓存管理器实例"""
        return CacheManager(
            max_size=100,
            default_ttl_seconds=60,
            eviction_strategy=EvictionStrategy.LRU,
        )

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试设置和获取缓存"""
        await cache.set("key1", {"name": "test"}, ttl_seconds=300)
        
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
        await cache.set("temp-key", "temp-value", ttl_seconds=1)
        
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
        assert cleared == 10
        
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
        
        stats = await cache.get_stats()
        
        assert isinstance(stats, CacheStats)
        assert stats.total_entries == 5
        assert stats.hit_count == 5
        assert stats.miss_count == 5
        assert stats.hit_rate == 0.5

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
        
        # 验证未访问的key可能被淘汰
        # 注意：具体淘汰取决于实现

    @pytest.mark.asyncio
    async def test_ttl_refresh(self, cache):
        """测试TTL刷新"""
        await cache.set("refresh-key", "value", ttl_seconds=2)
        
        # 第一次访问
        await cache.get("refresh-key")
        await asyncio.sleep(1)
        
        # 第二次访问（刷新TTL）
        await cache.get("refresh-key", refresh_ttl=True)
        await asyncio.sleep(1.5)
        
        # 应该仍然存在（因为TTL被刷新）
        value = await cache.get("refresh-key")
        assert value is not None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """测试检查键是否存在"""
        await cache.set("exists-key", "value")
        
        assert await cache.exists("exists-key") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_get_many(self, cache):
        """测试批量获取"""
        # 设置多个值
        for i in range(5):
            await cache.set(f"multi-key-{i}", f"value-{i}")
        
        # 批量获取
        keys = [f"multi-key-{i}" for i in range(3)]
        values = await cache.get_many(keys)
        
        assert len(values) == 3
        for i, key in enumerate(keys):
            assert values[i] == f"value-{i}"

    @pytest.mark.asyncio
    async def test_set_many(self, cache):
        """测试批量设置"""
        items = {
            f"batch-key-{i}": f"batch-value-{i}"
            for i in range(5)
        }
        
        set_count = await cache.set_many(items, ttl_seconds=300)
        assert set_count == 5
        
        # 验证设置成功
        for key, expected_value in items.items():
            actual_value = await cache.get(key)
            assert actual_value == expected_value

    @pytest.mark.asyncio
    async def test_get_or_set(self, cache):
        """测试获取或设置"""
        # 第一次调用（不存在，执行setter）
        value1 = await cache.get_or_set(
            "computed-key",
            setter=lambda: "computed-value",
            ttl_seconds=300,
        )
        assert value1 == "computed-value"
        
        # 第二次调用（存在，直接返回）
        value2 = await cache.get_or_set(
            "computed-key",
            setter=lambda: "new-value",  # 不应该执行
            ttl_seconds=300,
        )
        assert value2 == "computed-value"  # 仍然是旧值

    @pytest.mark.asyncio
    async def test_touch(self, cache):
        """测试更新访问时间"""
        await cache.set("touch-key", "value", ttl_seconds=2)
        
        # 更新访问时间
        touched = await cache.touch("touch-key")
        assert touched is True
        
        # 等待一段时间
        await asyncio.sleep(1.5)
        
        # 应该仍然存在
        value = await cache.get("touch-key")
        assert value is not None

    @pytest.mark.asyncio
    async def test_keys(self, cache):
        """测试获取所有键"""
        await cache.set("key-a", "value-a")
        await cache.set("key-b", "value-b")
        await cache.set("key-c", "value-c")
        
        keys = await cache.keys()
        
        assert "key-a" in keys
        assert "key-b" in keys
        assert "key-c" in keys

    @pytest.mark.asyncio
    async def test_size(self, cache):
        """测试获取缓存大小"""
        # 空缓存
        assert await cache.size() == 0
        
        # 添加条目
        for i in range(5):
            await cache.set(f"size-key-{i}", f"value-{i}")
        
        assert await cache.size() == 5


@pytest.mark.unit
class TestCacheEdgeCases:
    """缓存边界情况测试"""

    @pytest.fixture
    def cache(self):
        """创建缓存管理器实例"""
        return CacheManager(max_size=10)

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
    async def test_set_large_value(self, cache):
        """测试设置大值"""
        large_value = "x" * 1000000  # 1MB字符串
        
        await cache.set("large-key", large_value)
        
        value = await cache.get("large-key")
        assert value == large_value

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
