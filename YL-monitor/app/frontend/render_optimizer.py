"""
【文件功能】
渲染优化器，实现页面呈现内容优化、DOM优化和资源加载优化

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现渲染优化核心功能

【依赖说明】
- 标准库: asyncio, typing, dataclasses, enum, json, re
- 第三方库: 无
- 内部模块: 无

【使用示例】
```python
from app.frontend.render_optimizer import render_optimizer, RenderStrategy

# 创建渲染任务
task = render_optimizer.create_render_task(
    component_id="dashboard",
    data=large_dataset,
    strategy=RenderStrategy.VIRTUAL,
    priority=3
)

# 调度渲染
result = await render_optimizer.schedule_render(task)
```
"""

import asyncio
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re


class RenderStrategy(Enum):
    """【渲染策略】页面渲染策略类型"""
    IMMEDIATE = "immediate"      # 【立即渲染】直接渲染
    LAZY = "lazy"                # 【懒渲染】可见时渲染
    VIRTUAL = "virtual"          # 【虚拟渲染】大数据集虚拟滚动
    INCREMENTAL = "incremental"  # 【增量渲染】分批渲染
    PRIORITY = "priority"        # 【优先级渲染】按优先级调度


@dataclass
class RenderTask:
    """【渲染任务】单个渲染任务定义"""
    task_id: str                 # 【任务ID】唯一标识
    component_id: str            # 【组件ID】目标组件
    priority: int = 5            # 【优先级】1-10，数字越小优先级越高
    strategy: RenderStrategy = RenderStrategy.IMMEDIATE  # 【策略】渲染策略
    data: Any = None             # 【数据】渲染数据
    dependencies: List[str] = field(default_factory=list)  # 【依赖】依赖任务ID列表
    estimated_time: float = 0.0    # 【预估时间】预估渲染时间（毫秒）
    completed: bool = False        # 【已完成】是否已完成


@dataclass
class DOMOptimization:
    """【DOM优化配置】DOM操作优化配置"""
    batch_updates: bool = True           # 【批量更新】合并DOM操作
    use_document_fragment: bool = True   # 【使用DocumentFragment】减少重排
    minimize_reflow: bool = True         # 【最小化重排】优化布局计算
    debounce_time: int = 16              # 【防抖时间】防抖延迟（毫秒）
    throttle_time: int = 16              # 【节流时间】节流间隔（毫秒）


@dataclass
class ResourceLoading:
    """【资源加载配置】资源加载优化配置"""
    preload_critical: bool = True            # 【预加载关键资源】优先加载
    lazy_load_images: bool = True            # 【懒加载图片】延迟加载图片
    async_scripts: bool = True               # 【异步加载脚本】非阻塞加载
    defer_non_critical: bool = True          # 【延迟非关键资源】延后加载
    critical_css_inline: bool = True         # 【关键CSS内联】内联关键样式


class RenderOptimizer:
    """
    【类职责】
    渲染优化器，提供页面渲染性能优化、DOM优化和资源加载优化
    
    【主要功能】
    1. 渲染性能优化: 根据策略选择最优渲染方式（立即、懒加载、虚拟滚动等）
    2. DOM优化: 批量更新、使用DocumentFragment、防抖节流
    3. 资源加载优化: 预加载关键资源、懒加载图片、异步加载脚本
    4. 性能监控: 记录渲染时间、分析性能瓶颈
    
    【属性说明】
    - _render_queue: 渲染任务队列
    - _completed_tasks: 已完成任务集合
    - _dom_optimization: DOM优化配置
    - _resource_loading: 资源加载配置
    - _performance_metrics: 性能指标历史
    - _virtual_scrollers: 虚拟滚动器状态
    - _stats: 渲染统计信息
    
    【使用示例】
    ```python
    optimizer = RenderOptimizer()
    
    # 配置DOM优化
    optimizer.set_dom_optimization(DOMOptimization(
        batch_updates=True,
        debounce_time=16
    ))
    
    # 创建并调度渲染任务
    task = optimizer.create_render_task("list", data, RenderStrategy.VIRTUAL)
    result = await optimizer.schedule_render(task)
    ```
    """
    
    def __init__(self):
        """【初始化】创建渲染优化器实例"""
        self._render_queue: List[RenderTask] = []
        self._completed_tasks: Set[str] = set()
        self._dom_optimization = DOMOptimization()
        self._resource_loading = ResourceLoading()
        self._performance_metrics: List[Dict] = []
        self._virtual_scrollers: Dict[str, Any] = {}
        self._observers: Dict[str, Any] = {}
        
        # 【渲染统计】
        self._stats = {
            "total_renders": 0,
            "avg_render_time": 0.0,
            "dom_nodes_created": 0,
            "dom_nodes_reused": 0
        }
    
    def set_dom_optimization(self, config: DOMOptimization) -> None:
        """
        【设置DOM优化配置】
        
        【参数说明】
        - config (DOMOptimization): DOM优化配置对象
        """
        self._dom_optimization = config
    
    def set_resource_loading(self, config: ResourceLoading) -> None:
        """
        【设置资源加载配置】
        
        【参数说明】
        - config (ResourceLoading): 资源加载配置对象
        """
        self._resource_loading = config
    
    def create_render_task(
        self,
        component_id: str,
        data: Any,
        strategy: RenderStrategy = RenderStrategy.IMMEDIATE,
        priority: int = 5,
        dependencies: List[str] = None
    ) -> RenderTask:
        """
        【创建渲染任务】创建新的渲染任务
        
        【参数说明】
        - component_id (str): 组件ID
        - data (Any): 渲染数据
        - strategy (RenderStrategy): 渲染策略，默认立即渲染
        - priority (int): 优先级1-10，数字越小优先级越高
        - dependencies (List[str]): 依赖任务ID列表
        
        【返回值】
        - RenderTask: 创建的渲染任务
        
        【使用示例】
        ```python
        task = optimizer.create_render_task(
            component_id="dashboard",
            data=metrics_data,
            strategy=RenderStrategy.INCREMENTAL,
            priority=3
        )
        ```
        """
        task_id = f"render_{component_id}_{asyncio.get_event_loop().time()}"
        
        task = RenderTask(
            task_id=task_id,
            component_id=component_id,
            priority=priority,
            strategy=strategy,
            data=data,
            dependencies=dependencies or [],
            estimated_time=self._estimate_render_time(data, strategy)
        )
        
        return task
    
    def _estimate_render_time(self, data: Any, 
                              strategy: RenderStrategy) -> float:
        """预估渲染时间"""
        base_time = 10.0  # 基础时间10ms
        
        # 根据数据量调整
        if isinstance(data, list):
            base_time += len(data) * 0.5
        elif isinstance(data, dict):
            base_time += len(data) * 0.3
        
        # 根据策略调整
        multipliers = {
            RenderStrategy.IMMEDIATE: 1.0,
            RenderStrategy.LAZY: 0.8,
            RenderStrategy.VIRTUAL: 0.3,
            RenderStrategy.INCREMENTAL: 0.6,
            RenderStrategy.PRIORITY: 1.2
        }
        
        return base_time * multipliers.get(strategy, 1.0)
    
    async def schedule_render(self, task: RenderTask) -> bool:
        """
        【调度渲染任务】根据策略选择最优渲染方式
        
        【参数说明】
        - task (RenderTask): 渲染任务
        
        【返回值】
        - bool: 渲染是否成功
        
        【处理流程】
        1. 检查依赖是否完成
        2. 根据策略选择渲染方式
        3. 执行渲染
        4. 记录性能指标
        """
        # 检查依赖
        for dep in task.dependencies:
            if dep not in self._completed_tasks:
                # 依赖未完成，等待
                await self._wait_for_dependency(dep)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            if task.strategy == RenderStrategy.IMMEDIATE:
                await self._render_immediate(task)
            elif task.strategy == RenderStrategy.LAZY:
                await self._render_lazy(task)
            elif task.strategy == RenderStrategy.VIRTUAL:
                await self._render_virtual(task)
            elif task.strategy == RenderStrategy.INCREMENTAL:
                await self._render_incremental(task)
            elif task.strategy == RenderStrategy.PRIORITY:
                await self._render_priority(task)
            
            # 记录完成
            task.completed = True
            self._completed_tasks.add(task.task_id)
            
            # 记录性能指标
            end_time = asyncio.get_event_loop().time()
            render_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            self._record_performance(task, render_time)
            
            return True
            
        except Exception as e:
            print(f"渲染任务 {task.task_id} 失败: {e}")
            return False
    
    async def _render_immediate(self, task: RenderTask) -> None:
        """立即渲染"""
        # 直接执行渲染
        await self._execute_render(task.data)
    
    async def _render_lazy(self, task: RenderTask) -> None:
        """懒渲染"""
        # 使用Intersection Observer检测可见性
        # 当元素进入视口时才渲染
        await self._wait_for_visibility(task.component_id)
        await self._execute_render(task.data)
    
    async def _render_virtual(self, task: RenderTask) -> None:
        """虚拟渲染（用于大数据集）"""
        if isinstance(task.data, list) and len(task.data) > 100:
            # 只渲染可见区域的数据
            await self._render_virtual_list(task)
        else:
            await self._execute_render(task.data)
    
    async def _render_incremental(self, task: RenderTask) -> None:
        """增量渲染"""
        if isinstance(task.data, list):
            # 分批渲染
            batch_size = 50
            for i in range(0, len(task.data), batch_size):
                batch = task.data[i:i + batch_size]
                await self._execute_render(batch)
                
                # 让出控制权，避免阻塞
                if i + batch_size < len(task.data):
                    await asyncio.sleep(0)
        else:
            await self._execute_render(task.data)
    
    async def _render_priority(self, task: RenderTask) -> None:
        """优先级渲染"""
        # 高优先级任务优先执行
        if task.priority <= 3:
            # 立即执行
            await self._execute_render(task.data)
        else:
            # 低优先级，使用requestIdleCallback模拟
            await self._wait_for_idle()
            await self._execute_render(task.data)
    
    async def _execute_render(self, data: Any) -> None:
        """执行实际渲染（模拟）"""
        # 实际实现中，这里会操作DOM
        # 模拟渲染延迟
        await asyncio.sleep(0.001)
        
        # 更新统计
        self._stats["total_renders"] += 1
        if isinstance(data, list):
            self._stats["dom_nodes_created"] += len(data)
    
    async def _wait_for_dependency(self, dependency_id: str, 
                                    timeout: float = 5.0) -> bool:
        """等待依赖完成"""
        start_time = asyncio.get_event_loop().time()
        
        while dependency_id not in self._completed_tasks:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            await asyncio.sleep(0.01)
        
        return True
    
    async def _wait_for_visibility(self, component_id: str) -> None:
        """等待元素可见"""
        # 模拟Intersection Observer行为
        await asyncio.sleep(0.1)
    
    async def _wait_for_idle(self) -> None:
        """等待空闲时间"""
        # 模拟requestIdleCallback
        await asyncio.sleep(0.05)
    
    async def _render_virtual_list(self, task: RenderTask) -> None:
        """渲染虚拟列表"""
        data = task.data
        item_height = 50  # 假设每个项目50px
        viewport_height = 600  # 视口高度
        buffer_size = 5  # 缓冲区大小
        
        # 计算可见范围
        visible_count = viewport_height // item_height
        start_index = 0  # 实际应根据滚动位置计算
        end_index = start_index + visible_count + buffer_size * 2
        
        # 只渲染可见区域
        visible_data = data[max(0, start_index):min(len(data), end_index)]
        
        await self._execute_render(visible_data)
        
        # 记录虚拟滚动器状态
        self._virtual_scrollers[task.component_id] = {
            "total_items": len(data),
            "visible_items": len(visible_data),
            "start_index": start_index,
            "item_height": item_height
        }
    
    def batch_dom_updates(self, updates: List[Callable]) -> None:
        """
        批量DOM更新
        
        使用DocumentFragment减少重排
        """
        if not self._dom_optimization.batch_updates:
            # 不批量处理，直接执行
            for update in updates:
                update()
            return
        
        # 使用DocumentFragment批量更新
        # 实际实现中，这里会创建DocumentFragment
        # 模拟批量更新
        for update in updates:
            update()
        
        # 一次性插入DOM
        # fragment.appendChild(...) 等操作
    
    def debounce_render(self, func: Callable, wait: int = None) -> Callable:
        """防抖渲染"""
        if wait is None:
            wait = self._dom_optimization.debounce_time
        
        last_call_time = [0]
        timer = [None]
        
        async def debounced(*args, **kwargs):
            current_time = asyncio.get_event_loop().time() * 1000
            
            # 取消之前的定时器
            if timer[0]:
                timer[0].cancel()
            
            # 设置新的定时器
            async def delayed():
                await asyncio.sleep(wait / 1000)
                await func(*args, **kwargs)
            
            timer[0] = asyncio.create_task(delayed())
            last_call_time[0] = current_time
        
        return debounced
    
    def throttle_render(self, func: Callable, limit: int = None) -> Callable:
        """节流渲染"""
        if limit is None:
            limit = self._dom_optimization.throttle_time
        
        last_call_time = [0]
        pending = [False]
        
        async def throttled(*args, **kwargs):
            current_time = asyncio.get_event_loop().time() * 1000
            
            if current_time - last_call_time[0] >= limit:
                # 超过限制时间，立即执行
                last_call_time[0] = current_time
                await func(*args, **kwargs)
                pending[0] = False
            elif not pending[0]:
                # 在限制时间内，延迟执行
                pending[0] = True
                delay = limit - (current_time - last_call_time[0])
                await asyncio.sleep(delay / 1000)
                last_call_time[0] = asyncio.get_event_loop().time() * 1000
                await func(*args, **kwargs)
                pending[0] = False
        
        return throttled
    
    def optimize_resource_loading(self, resources: List[Dict]) -> List[Dict]:
        """
        优化资源加载顺序
        
        根据优先级和类型优化加载策略
        """
        optimized = []
        
        # 分类资源
        critical_css = []
        critical_js = []
        async_js = []
        lazy_images = []
        prefetch = []
        
        for resource in resources:
            res_type = resource.get("type", "")
            priority = resource.get("priority", "normal")
            
            if res_type == "css" and priority == "critical":
                critical_css.append(resource)
            elif res_type == "js" and priority == "critical":
                critical_js.append(resource)
            elif res_type == "js" and self._resource_loading.async_scripts:
                async_js.append({**resource, "async": True})
            elif res_type == "image" and self._resource_loading.lazy_load_images:
                lazy_images.append({**resource, "loading": "lazy"})
            else:
                prefetch.append(resource)
        
        # 按优先级排序
        optimized.extend(critical_css)
        optimized.extend(critical_js)
        optimized.extend(async_js)
        optimized.extend(lazy_images)
        optimized.extend(prefetch)
        
        return optimized
    
    def generate_critical_css(self, css_content: str, 
                             used_selectors: List[str]) -> str:
        """
        生成关键CSS
        
        提取首屏渲染必需的CSS
        """
        critical_rules = []
        
        # 简单的CSS解析（实际应使用CSS解析库）
        rules = css_content.split("}")
        
        for rule in rules:
            for selector in used_selectors:
                if selector in rule:
                    critical_rules.append(rule + "}")
                    break
        
        return "\n".join(critical_rules)
    
    def _record_performance(self, task: RenderTask, render_time: float) -> None:
        """记录性能指标"""
        self._performance_metrics.append({
            "timestamp": asyncio.get_event_loop().time(),
            "task_id": task.task_id,
            "component_id": task.component_id,
            "strategy": task.strategy.value,
            "priority": task.priority,
            "render_time_ms": render_time,
            "estimated_time_ms": task.estimated_time
        })
        
        # 更新平均渲染时间
        total_time = sum(m["render_time_ms"] for m in self._performance_metrics)
        self._stats["avg_render_time"] = total_time / len(self._performance_metrics)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        【获取性能报告】获取渲染性能分析报告
        
        【返回值】
        - Dict[str, Any]: 性能报告，包含：
            - total_renders: 总渲染次数
            - avg_render_time_ms: 平均渲染时间
            - strategy_distribution: 策略分布
            - slow_renders_count: 慢渲染次数
            - slow_renders: 慢渲染详情列表
        """
        if not self._performance_metrics:
            return {
                "total_renders": 0,
                "avg_render_time_ms": 0,
                "strategy_distribution": {},
                "slow_renders": []
            }
        
        # 策略分布
        strategies = {}
        for metric in self._performance_metrics:
            strategy = metric["strategy"]
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        # 慢渲染（超过100ms）
        slow_renders = [
            m for m in self._performance_metrics
            if m["render_time_ms"] > 100
        ]
        
        return {
            "total_renders": len(self._performance_metrics),
            "avg_render_time_ms": round(
                sum(m["render_time_ms"] for m in self._performance_metrics) / 
                len(self._performance_metrics), 2
            ),
            "strategy_distribution": strategies,
            "slow_renders_count": len(slow_renders),
            "slow_renders": sorted(
                slow_renders, 
                key=lambda x: x["render_time_ms"], 
                reverse=True
            )[:10]  # 只返回前10个
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        【获取渲染统计】获取渲染统计信息
        
        【返回值】
        - Dict[str, Any]: 统计信息，包含：
            - total_renders: 总渲染次数
            - avg_render_time: 平均渲染时间
            - dom_nodes_created: 创建的DOM节点数
            - dom_nodes_reused: 复用的DOM节点数
        """
        return self._stats.copy()


# 【全局渲染优化器实例】
render_optimizer = RenderOptimizer()


# 【便捷函数】
def create_optimized_render_task(
    component_id: str,
    data: Any,
    strategy: str = "immediate",
    priority: int = 5
) -> RenderTask:
    """
    【便捷函数】创建优化的渲染任务
    
    【参数说明】
    - component_id (str): 组件ID
    - data (Any): 渲染数据
    - strategy (str): 渲染策略名称，可选：immediate/lazy/virtual/incremental/priority
    - priority (int): 优先级1-10
    
    【返回值】
    - RenderTask: 创建的渲染任务
    
    【使用示例】
    ```python
    task = create_optimized_render_task(
        component_id="list",
        data=items,
        strategy="virtual",
        priority=3
    )
    ```
    """
    strategy_enum = RenderStrategy(strategy)
    return render_optimizer.create_render_task(
        component_id=component_id,
        data=data,
        strategy=strategy_enum,
        priority=priority
    )


async def schedule_optimized_render(task: RenderTask) -> bool:
    """
    【便捷函数】调度优化的渲染任务
    
    【参数说明】
    - task (RenderTask): 渲染任务
    
    【返回值】
    - bool: 是否成功
    """
    return await render_optimizer.schedule_render(task)
