#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户体验层监控器 (L5)
提供GUI交互、页面加载、用户操作的详细监控
"""

import logging
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class GUIInteractionMetrics:
    """GUI交互指标"""
    component_id: str
    interaction_type: str  # click, hover, scroll, input
    response_time_ms: float
    render_time_ms: float
    success: bool
    error_message: Optional[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PageLoadMetrics:
    """页面加载指标"""
    page_name: str
    load_time_ms: float
    dom_ready_ms: float
    resources_loaded_ms: float
    first_paint_ms: float
    first_contentful_paint_ms: float
    total_resources: int
    total_size_kb: float
    error_count: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserActionMetrics:
    """用户操作指标"""
    action_type: str  # start_video, stop_video, load_model, etc.
    action_params: Dict[str, Any]
    execution_time_ms: float
    success: bool
    error_code: Optional[str]
    error_message: Optional[str]
    retry_count: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserExperienceMetrics:
    """用户体验整体指标"""
    gui_interactions: List[GUIInteractionMetrics]
    page_loads: List[PageLoadMetrics]
    user_actions: List[UserActionMetrics]
    avg_response_time_ms: float
    error_rate: float
    user_satisfaction_score: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gui_interactions": [i.to_dict() for i in self.gui_interactions],
            "page_loads": [p.to_dict() for p in self.page_loads],
            "user_actions": [a.to_dict() for a in self.user_actions],
            "avg_response_time_ms": self.avg_response_time_ms,
            "error_rate": self.error_rate,
            "user_satisfaction_score": self.user_satisfaction_score,
            "timestamp": self.timestamp
        }


class GUIInteractionMonitor:
    """
    GUI交互监控器
    
    监控指标：
    - 组件响应时间
    - 渲染时间
    - 交互成功率
    - 错误统计
    """
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self._interactions: deque = deque(maxlen=history_size)
    
    def record_interaction(
        self,
        component_id: str,
        interaction_type: str,
        response_time_ms: float,
        render_time_ms: float = 0,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        记录GUI交互
        
        Args:
            component_id: 组件ID
            interaction_type: 交互类型
            response_time_ms: 响应时间
            render_time_ms: 渲染时间
            success: 是否成功
            error_message: 错误信息
        """
        interaction = GUIInteractionMetrics(
            component_id=component_id,
            interaction_type=interaction_type,
            response_time_ms=response_time_ms,
            render_time_ms=render_time_ms,
            success=success,
            error_message=error_message,
            timestamp=datetime.now().isoformat()
        )
        self._interactions.append(interaction)
        logger.debug(f"记录交互: {component_id} {interaction_type} "
                    f"{response_time_ms:.2f}ms")
    
    def get_metrics(self) -> List[GUIInteractionMetrics]:
        """获取所有交互指标"""
        return list(self._interactions)
    
    def get_component_metrics(self, component_id: str) -> Dict[str, Any]:
        """
        获取指定组件的指标统计
        """
        component_interactions = [
            i for i in self._interactions 
            if i.component_id == component_id
        ]
        
        if not component_interactions:
            return {
                "component_id": component_id,
                "interaction_count": 0,
                "avg_response_time": 0,
                "error_rate": 0
            }
        
        times = [i.response_time_ms for i in component_interactions]
        errors = sum(1 for i in component_interactions if not i.success)
        
        return {
            "component_id": component_id,
            "interaction_count": len(component_interactions),
            "avg_response_time": round(statistics.mean(times), 2),
            "max_response_time": round(max(times), 2),
            "min_response_time": round(min(times), 2),
            "error_count": errors,
            "error_rate": round(errors / len(component_interactions) * 100, 2)
        }


class PageLoadMonitor:
    """
    页面加载监控器
    
    监控指标：
    - 加载时间
    - DOM就绪时间
    - 资源加载时间
    - 首次绘制时间
    - 资源数量和大小
    """
    
    def __init__(self, history_size: int = 50):
        self.history_size = history_size
        self._page_loads: deque = deque(maxlen=history_size)
    
    def record_page_load(
        self,
        page_name: str,
        load_time_ms: float,
        dom_ready_ms: float,
        resources_loaded_ms: float,
        first_paint_ms: float = 0,
        first_contentful_paint_ms: float = 0,
        total_resources: int = 0,
        total_size_kb: float = 0,
        error_count: int = 0
    ):
        """
        记录页面加载
        
        Args:
            page_name: 页面名称
            load_time_ms: 总加载时间
            dom_ready_ms: DOM就绪时间
            resources_loaded_ms: 资源加载时间
            first_paint_ms: 首次绘制时间
            first_contentful_paint_ms: 首次内容绘制时间
            total_resources: 资源总数
            total_size_kb: 总大小
            error_count: 错误数
        """
        page_load = PageLoadMetrics(
            page_name=page_name,
            load_time_ms=load_time_ms,
            dom_ready_ms=dom_ready_ms,
            resources_loaded_ms=resources_loaded_ms,
            first_paint_ms=first_paint_ms,
            first_contentful_paint_ms=first_contentful_paint_ms,
            total_resources=total_resources,
            total_size_kb=total_size_kb,
            error_count=error_count,
            timestamp=datetime.now().isoformat()
        )
        self._page_loads.append(page_load)
        logger.info(f"页面加载: {page_name} {load_time_ms:.2f}ms")
    
    def get_metrics(self) -> List[PageLoadMetrics]:
        """获取所有页面加载指标"""
        return list(self._page_loads)
    
    def get_page_stats(self, page_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取页面加载统计
        """
        loads = list(self._page_loads)
        if page_name:
            loads = [p for p in loads if p.page_name == page_name]
        
        if not loads:
            return {
                "page_count": 0,
                "avg_load_time": 0,
                "avg_dom_ready": 0
            }
        
        load_times = [p.load_time_ms for p in loads]
        dom_times = [p.dom_ready_ms for p in loads]
        
        return {
            "page_count": len(loads),
            "avg_load_time": round(statistics.mean(load_times), 2),
            "max_load_time": round(max(load_times), 2),
            "min_load_time": round(min(load_times), 2),
            "avg_dom_ready": round(statistics.mean(dom_times), 2),
            "avg_resources": round(
                statistics.mean([p.total_resources for p in loads]), 1
            ),
            "total_errors": sum(p.error_count for p in loads)
        }


class UserActionMonitor:
    """
    用户操作监控器
    
    监控指标：
    - 操作类型和参数
    - 执行时间
    - 成功率
    - 错误统计
    - 重试次数
    """
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self._actions: deque = deque(maxlen=history_size)
    
    def record_action(
        self,
        action_type: str,
        action_params: Dict[str, Any],
        execution_time_ms: float,
        success: bool = True,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0
    ):
        """
        记录用户操作
        
        Args:
            action_type: 操作类型
            action_params: 操作参数
            execution_time_ms: 执行时间
            success: 是否成功
            error_code: 错误代码
            error_message: 错误信息
            retry_count: 重试次数
        """
        action = UserActionMetrics(
            action_type=action_type,
            action_params=action_params,
            execution_time_ms=execution_time_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
            retry_count=retry_count,
            timestamp=datetime.now().isoformat()
        )
        self._actions.append(action)
        
        status = "成功" if success else "失败"
        logger.info(f"用户操作: {action_type} {status} "
                   f"{execution_time_ms:.2f}ms")
    
    def get_metrics(self) -> List[UserActionMetrics]:
        """获取所有用户操作指标"""
        return list(self._actions)
    
    def get_action_stats(self, action_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取操作统计
        """
        actions = list(self._actions)
        if action_type:
            actions = [a for a in actions if a.action_type == action_type]
        
        if not actions:
            return {
                "action_count": 0,
                "success_rate": 0,
                "avg_execution_time": 0
            }
        
        exec_times = [a.execution_time_ms for a in actions]
        successes = sum(1 for a in actions if a.success)
        retries = sum(a.retry_count for a in actions)
        
        return {
            "action_count": len(actions),
            "success_rate": round(successes / len(actions) * 100, 2),
            "avg_execution_time": round(statistics.mean(exec_times), 2),
            "max_execution_time": round(max(exec_times), 2),
            "total_retries": retries,
            "error_count": len(actions) - successes
        }


class UserExperienceCollector:
    """
    用户体验指标采集器
    
    整合GUI交互、页面加载、用户操作监控器
    """
    
    def __init__(self):
        self.gui_monitor = GUIInteractionMonitor()
        self.page_monitor = PageLoadMonitor()
        self.action_monitor = UserActionMonitor()
    
    def collect_all(self) -> Dict[str, Any]:
        """
        采集所有用户体验层指标
        """
        try:
            # 获取各维度指标
            gui_metrics = self.gui_monitor.get_metrics()
            page_metrics = self.page_monitor.get_metrics()
            action_metrics = self.action_monitor.get_metrics()
            
            # 计算综合指标
            all_response_times = []
            all_errors = 0
            total_interactions = 0
            
            # GUI交互统计
            for interaction in gui_metrics:
                all_response_times.append(interaction.response_time_ms)
                total_interactions += 1
                if not interaction.success:
                    all_errors += 1
            
            # 用户操作统计
            for action in action_metrics:
                all_response_times.append(action.execution_time_ms)
                total_interactions += 1
                if not action.success:
                    all_errors += 1
            
            # 计算平均响应时间和错误率
            avg_response = (
                statistics.mean(all_response_times) 
                if all_response_times else 0
            )
            error_rate = (
                all_errors / total_interactions * 100 
                if total_interactions > 0 else 0
            )
            
            # 计算用户满意度评分 (0-100)
            # 基于响应时间和错误率
            response_score = max(0, 100 - avg_response)  # 响应越快分越高
            error_score = max(0, 100 - error_rate * 10)   # 错误越少分越高
            satisfaction = (response_score * 0.6 + error_score * 0.4)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "layer": "L5_user_experience",
                "gui_interactions": [i.to_dict() for i in gui_metrics],
                "page_loads": [p.to_dict() for p in page_metrics],
                "user_actions": [a.to_dict() for a in action_metrics],
                "summary": {
                    "total_interactions": total_interactions,
                    "avg_response_time_ms": round(avg_response, 2),
                    "error_rate": round(error_rate, 2),
                    "user_satisfaction_score": round(satisfaction, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"采集用户体验指标失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "layer": "L5_user_experience",
                "error": str(e)
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        获取用户体验健康摘要
        """
        metrics = self.collect_all()
        
        if "error" in metrics:
            return {
                "status": "error",
                "error": metrics["error"],
                "timestamp": datetime.now().isoformat()
            }
        
        summary = metrics["summary"]
        avg_response = summary["avg_response_time_ms"]
        error_rate = summary["error_rate"]
        satisfaction = summary["user_satisfaction_score"]
        
        # 评估健康状态
        if satisfaction >= 80 and error_rate < 5:
            status = "excellent"
        elif satisfaction >= 60 and error_rate < 10:
            status = "good"
        elif satisfaction >= 40:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "status": status,
            "user_satisfaction": satisfaction,
            "avg_response_time": avg_response,
            "error_rate": error_rate,
            "components": {
                "gui": self._evaluate_gui_health(),
                "page_load": self._evaluate_page_health(),
                "user_actions": self._evaluate_action_health()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _evaluate_gui_health(self) -> str:
        """评估GUI健康状态"""
        interactions = self.gui_monitor.get_metrics()
        if not interactions:
            return "unknown"
        
        recent = list(interactions)[-10:]  # 最近10次
        errors = sum(1 for i in recent if not i.success)
        avg_time = statistics.mean([i.response_time_ms for i in recent])
        
        if errors == 0 and avg_time < 100:
            return "healthy"
        elif errors < 2 and avg_time < 300:
            return "degraded"
        else:
            return "unhealthy"
    
    def _evaluate_page_health(self) -> str:
        """评估页面加载健康状态"""
        loads = self.page_monitor.get_metrics()
        if not loads:
            return "unknown"
        
        recent = list(loads)[-5:]  # 最近5次
        avg_time = statistics.mean([p.load_time_ms for p in recent])
        errors = sum(p.error_count for p in recent)
        
        if avg_time < 1000 and errors == 0:
            return "healthy"
        elif avg_time < 3000:
            return "degraded"
        else:
            return "unhealthy"
    
    def _evaluate_action_health(self) -> str:
        """评估用户操作健康状态"""
        actions = self.action_monitor.get_metrics()
        if not actions:
            return "unknown"
        
        recent = list(actions)[-10:]  # 最近10次
        errors = sum(1 for a in recent if not a.success)
        avg_time = statistics.mean([a.execution_time_ms for a in recent])
        
        if errors == 0 and avg_time < 500:
            return "healthy"
        elif errors < 2 and avg_time < 1000:
            return "degraded"
        else:
            return "unhealthy"


# 全局采集器实例
ux_collector = UserExperienceCollector()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("用户体验层监控测试")
    print("=" * 60)
    
    collector = UserExperienceCollector()
    
    # 模拟GUI交互
    print("\n1. 模拟GUI交互...")
    for i in range(20):
        collector.gui_monitor.record_interaction(
            component_id=f"button_{i % 5}",
            interaction_type="click" if i % 3 == 0 else "hover",
            response_time_ms=50 + (i % 30),
            render_time_ms=10 + (i % 10),
            success=(i % 10 != 0)  # 10%失败率
        )
    
    # 模拟页面加载
    print("2. 模拟页面加载...")
    pages = ["dashboard", "settings", "monitor", "logs"]
    for i, page in enumerate(pages):
        collector.page_monitor.record_page_load(
            page_name=page,
            load_time_ms=800 + (i * 200),
            dom_ready_ms=300 + (i * 50),
            resources_loaded_ms=600 + (i * 150),
            first_paint_ms=200 + (i * 30),
            total_resources=20 + (i * 5),
            total_size_kb=500 + (i * 100),
            error_count=(1 if i == 2 else 0)
        )
    
    # 模拟用户操作
    print("3. 模拟用户操作...")
    actions = [
        ("start_video", {"source": "camera"}, 1200),
        ("load_model", {"model": "inswap_128"}, 2500),
        ("apply_effect", {"effect": "reverb"}, 300),
        ("stop_video", {}, 500),
    ]
    for i, (action, params, time_ms) in enumerate(actions):
        collector.action_monitor.record_action(
            action_type=action,
            action_params=params,
            execution_time_ms=time_ms + (i % 100),
            success=(i != 2),  # 第3个操作失败
            retry_count=(1 if i == 1 else 0)
        )
    
    # 获取指标
    print("\n4. 采集指标...")
    metrics = collector.collect_all()
    
    print(f"\n汇总信息:")
    summary = metrics["summary"]
    print(f"  总交互数: {summary['total_interactions']}")
    print(f"  平均响应时间: {summary['avg_response_time_ms']:.2f}ms")
    print(f"  错误率: {summary['error_rate']:.2f}%")
    print(f"  用户满意度: {summary['user_satisfaction_score']:.2f}/100")
    
    print("\nGUI交互统计:")
    for i in range(5):
        stats = collector.gui_monitor.get_component_metrics(f"button_{i}")
        print(f"  组件 button_{i}:")
        print(f"    交互次数: {stats['interaction_count']}")
        print(f"    平均响应: {stats['avg_response_time']:.2f}ms")
        print(f"    错误率: {stats['error_rate']:.2f}%")
    
    print("\n页面加载统计:")
    page_stats = collector.page_monitor.get_page_stats()
    print(f"  页面数: {page_stats['page_count']}")
    print(f"  平均加载: {page_stats['avg_load_time']:.2f}ms")
    print(f"  DOM就绪: {page_stats['avg_dom_ready']:.2f}ms")
    print(f"  总错误: {page_stats['total_errors']}")
    
    print("\n用户操作统计:")
    action_stats = collector.action_monitor.get_action_stats()
    print(f"  操作数: {action_stats['action_count']}")
    print(f"  成功率: {action_stats['success_rate']:.2f}%")
    print(f"  平均执行: {action_stats['avg_execution_time']:.2f}ms")
    print(f"  重试次数: {action_stats['total_retries']}")
    
    # 健康摘要
    print("\n5. 健康摘要:")
    health = collector.get_health_summary()
    print(f"  状态: {health['status']}")
    print(f"  用户满意度: {health['user_satisfaction']:.2f}")
    print(f"  平均响应: {health['avg_response_time']:.2f}ms")
    print(f"  错误率: {health['error_rate']:.2f}%")
    print("  组件状态:")
    for comp, status in health['components'].items():
        icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
        print(f"    {icon} {comp}: {status}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
