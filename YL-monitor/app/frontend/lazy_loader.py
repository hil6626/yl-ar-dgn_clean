"""
懒加载管理器
实现资源懒加载策略
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class LoadTask:
    """加载任务"""
    resource_id: str
    resource_type: str  # script, style, template, data
    url: str
    priority: int = 5  # 1-10, 数字越小优先级越高
    dependencies: List[str] = None
    loaded: bool = False
    error: Optional[str] = None
    load_time: Optional[float] = None


class LazyLoader:
    """
    懒加载管理器
    
    特性：
    1. 按优先级加载资源
    2. 依赖管理（确保依赖先加载）
    3. 并发控制（限制同时加载数量）
    4. 缓存管理
    5. 预加载策略
    """
    
    def __init__(self, max_concurrent: int = 6):
        self.max_concurrent = max_concurrent
        self._tasks: Dict[str, LoadTask] = {}
        self._loaded: Set[str] = set()
        self._loading: Set[str] = set()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._default_ttl = 300  # 默认缓存5分钟
        
        # 预加载队列
        self._preload_queue: List[str] = []
        self._preload_enabled = True
    
    def register(self, task: LoadTask) -> None:
        """注册加载任务"""
        self._tasks[task.resource_id] = task
    
    async def load(self, resource_id: str, force: bool = False) -> bool:
        """
        加载指定资源
        
        参数：
            resource_id: 资源ID
            force: 是否强制重新加载（忽略缓存）
        
        返回：
            bool: 是否加载成功
        """
        # 检查是否已加载
        if not force and resource_id in self._loaded:
            return True
        
        # 检查是否正在加载
        if resource_id in self._loading:
            # 等待加载完成
            while resource_id in self._loading:
                await asyncio.sleep(0.1)
            return resource_id in self._loaded
        
        task = self._tasks.get(resource_id)
        if not task:
            return False
        
        # 标记为正在加载
        self._loading.add(resource_id)
        
        try:
            # 先加载依赖
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id not in self._loaded:
                        await self.load(dep_id)
            
            # 模拟加载（实际实现中这里会加载真实资源）
            start_time = asyncio.get_event_loop().time()
            
            # 这里应该是真实的资源加载逻辑
            # 例如：加载JS文件、CSS文件、模板等
            await self._do_load(task)
            
            end_time = asyncio.get_event_loop().time()
            task.load_time = end_time - start_time
            task.loaded = True
            
            self._loaded.add(resource_id)
            self._cache[resource_id] = task
            
            return True
            
        except Exception as e:
            task.error = str(e)
            return False
            
        finally:
            self._loading.discard(resource_id)
    
    async def _do_load(self, task: LoadTask) -> None:
        """执行实际加载（模拟）"""
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 实际实现中，这里会：
        # 1. 对于script: 创建script标签并加载
        # 2. 对于style: 创建link标签并加载
        # 3. 对于template: 通过AJAX获取模板内容
        # 4. 对于data: 通过API获取数据
    
    async def load_batch(self, resource_ids: List[str]) -> Dict[str, bool]:
        """批量加载资源"""
        results = {}
        
        # 按优先级排序
        sorted_ids = sorted(
            resource_ids,
            key=lambda rid: self._tasks.get(rid, LoadTask(rid, "", "")).priority
        )
        
        # 控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def load_with_limit(rid: str) -> bool:
            async with semaphore:
                return await self.load(rid)
        
        # 并发加载
        tasks = [load_with_limit(rid) for rid in sorted_ids]
        loaded_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for rid, result in zip(sorted_ids, loaded_results):
            if isinstance(result, Exception):
                results[rid] = False
            else:
                results[rid] = result
        
        return results
    
    def preload(self, resource_id: str) -> None:
        """预加载资源（空闲时加载）"""
        if self._preload_enabled and resource_id not in self._preload_queue:
            self._preload_queue.append(resource_id)
            # 触发预加载（实际实现中应该使用requestIdleCallback）
            asyncio.create_task(self._process_preload())
    
    async def _process_preload(self) -> None:
        """处理预加载队列"""
        while self._preload_queue:
            # 检查系统是否空闲（简化实现）
            await asyncio.sleep(1)
            
            if self._preload_queue:
                resource_id = self._preload_queue.pop(0)
                if resource_id not in self._loaded:
                    await self.load(resource_id)
    
    def is_loaded(self, resource_id: str) -> bool:
        """检查资源是否已加载"""
        return resource_id in self._loaded
    
    def get_cache(self, resource_id: str) -> Optional[Any]:
        """获取缓存"""
        if resource_id in self._cache:
            timestamp = self._cache_timestamps.get(resource_id)
            if timestamp:
                ttl = self._default_ttl
                if datetime.now() - timestamp < timedelta(seconds=ttl):
                    return self._cache[resource_id]
                else:
                    # 缓存过期，清除
                    del self._cache[resource_id]
                    del self._cache_timestamps[resource_id]
        return None
    
    def set_cache(self, resource_id: str, data: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        self._cache[resource_id] = data
        self._cache_timestamps[resource_id] = datetime.now()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取加载统计"""
        total = len(self._tasks)
        loaded = len(self._loaded)
        loading = len(self._loading)
        cached = len(self._cache)
        
        return {
            "total_tasks": total,
            "loaded": loaded,
            "loading": loading,
            "cached": cached,
            "pending": total - loaded - loading,
            "preload_queue": len(self._preload_queue)
        }


# 全局懒加载器实例
lazy_loader = LazyLoader(max_concurrent=6)


# 使用示例
async def example_usage():
    """使用示例"""
    # 注册资源
    lazy_loader.register(LoadTask(
        resource_id="chart_component",
        resource_type="script",
        url="/static/js/components/chart.js",
        priority=3,
        dependencies=["chart_lib"]
    ))
    
    lazy_loader.register(LoadTask(
        resource_id="chart_lib",
        resource_type="script",
        url="/static/js/lib/chart.min.js",
        priority=1
    ))
    
    # 加载资源
    success = await lazy_loader.load("chart_component")
    print(f"加载结果: {success}")
    
    # 批量加载
    results = await lazy_loader.load_batch(["comp1", "comp2", "comp3"])
    print(f"批量加载结果: {results}")
    
    # 获取统计
    stats = lazy_loader.get_stats()
    print(f"加载统计: {stats}")
