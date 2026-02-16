#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户体验监控器 - L5层增强
提供GUI响应时间和用户操作流畅度监控
"""

import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class UIResponseMetrics:
    """UI响应时间指标"""
    component: str
    action: str
    response_time_ms: float
    render_time_ms: float
    total_time_ms: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UserOperationMetrics:
    """用户操作指标"""
    operation_type: str
    duration_ms: float
    success: bool
    error_message: Optional[str]
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PageLoadMetrics:
    """页面加载指标"""
    page_name: str
    load_time_ms: float
    dom_ready_ms: float
    resources_loaded_ms: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class UserExperienceMonitor:
    """
    用户体验监控器
    监控GUI响应时间和用户操作流畅度
    """
    
    def __init__(self):
        self.ui_history: deque = deque(maxlen=1000)
        self.operation_history: deque = deque(maxlen=1000)
        self.page_load_history: deque = deque(maxlen=100)
        self.running = False
        
        # 模拟数据计数器
        self._interaction_count = 0
        
    def record_ui_response(self, component: str, action: str,
                          response_time_ms: float,
                          render_time_ms: float) -> UIResponseMetrics:
        """记录UI响应时间"""
        try:
            total_time = response_time_ms + render_time_ms
            
            metrics = UIResponseMetrics(
                component=component,
                action=action,
                response_time_ms=round(response_time_ms, 1),
                render_time_ms=round(render_time_ms, 1),
                total_time_ms=round(total_time, 1),
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.ui_history.append(metrics)
            self._interaction_count += 1
            
            # 记录慢响应警告
            if total_time > 1000:  # 超过1秒
                logger.warning(f"慢UI响应: {component}.{action} = {total_time}ms")
            
            return metrics
            
        except Exception as e:
            logger.error(f"记录UI响应失败: {e}")
            return None
    
    def record_user_operation(self, operation_type: str,
                               duration_ms: float,
                               success: bool = True,
                               error_message: Optional[str] = None) -> UserOperationMetrics:
        """记录用户操作"""
        try:
            metrics = UserOperationMetrics(
                operation_type=operation_type,
                duration_ms=round(duration_ms, 1),
                success=success,
                error_message=error_message,
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.operation_history.append(metrics)
            
            # 记录失败操作
            if not success:
                logger.warning(f"用户操作失败: {operation_type}, 错误: {error_message}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"记录用户操作失败: {e}")
            return None
    
    def record_page_load(self, page_name: str,
                        load_time_ms: float,
                        dom_ready_ms: float,
                        resources_loaded_ms: float) -> PageLoadMetrics:
        """记录页面加载时间"""
        try:
            metrics = PageLoadMetrics(
                page_name=page_name,
                load_time_ms=round(load_time_ms, 1),
                dom_ready_ms=round(dom_ready_ms, 1),
                resources_loaded_ms=round(resources_loaded_ms, 1),
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.page_load_history.append(metrics)
            
            # 记录慢加载警告
            if load_time_ms > 3000:  # 超过3秒
                logger.warning(f"慢页面加载: {page_name} = {load_time_ms}ms")
            
            return metrics
            
        except Exception as e:
            logger.error(f"记录页面加载失败: {e}")
            return None
    
    def simulate_user_interaction(self):
        """模拟用户交互（实际应从User GUI获取真实数据）"""
        import random
        
        # 模拟UI组件
        components = [
            "video_preview", "face_selector", "audio_controls",
            "effect_panel", "settings_dialog", "main_toolbar"
        ]
        actions = ["click", "hover", "scroll", "input", "drag"]
        
        component = random.choice(components)
        action = random.choice(actions)
        
        # 模拟响应时间（10-500ms，偶尔有慢响应）
        if random.random() < 0.1:  # 10%概率慢响应
            response_time = random.uniform(500, 2000)
        else:
            response_time = random.uniform(10, 100)
        
        render_time = random.uniform(5, 50)
        
        return self.record_ui_response(component, action, response_time, render_time)
    
    def simulate_user_operation(self):
        """模拟用户操作"""
        import random
        
        operations = [
            "start_video", "stop_video", "switch_model", "apply_effect",
            "save_config", "load_config", "reset_settings", "export_result"
        ]
        
        operation = random.choice(operations)
        
        # 模拟操作时间（100-2000ms）
        duration = random.uniform(100, 2000)
        
        # 模拟成功率（95%）
        success = random.random() < 0.95
        error = None if success else random.choice([
            "Timeout", "Network Error", "Invalid Input", "Resource Busy"
        ])
        
        return self.record_user_operation(operation, duration, success, error)
    
    def simulate_page_load(self):
        """模拟页面加载"""
        import random
        
        pages = ["main_window", "settings_page", "help_dialog", "about_dialog"]
        page = random.choice(pages)
        
        # 模拟加载时间（100-3000ms）
        load_time = random.uniform(100, 3000)
        dom_ready = load_time * 0.3
        resources_loaded = load_time * 0.8
        
        return self.record_page_load(page, load_time, dom_ready, resources_loaded)
    
    async def start_monitoring(self, interval: int = 5):
        """启动持续监控"""
        self.running = True
        logger.info(f"启动用户体验监控 (间隔: {interval}秒)")
        
        while self.running:
            try:
                # 模拟用户交互（每5秒）
                ui_metrics = self.simulate_user_interaction()
                if ui_metrics:
                    logger.debug(f"UI响应: {ui_metrics.component}.{ui_metrics.action} = "
                               f"{ui_metrics.total_time_ms}ms")
                
                # 模拟用户操作（每15秒）
                if self._interaction_count % 3 == 0:
                    op_metrics = self.simulate_user_operation()
                    if op_metrics:
                        logger.debug(f"用户操作: {op_metrics.operation_type} = "
                                   f"{op_metrics.duration_ms}ms")
                
                # 模拟页面加载（每30秒）
                if self._interaction_count % 6 == 0:
                    page_metrics = self.simulate_page_load()
                    if page_metrics:
                        logger.debug(f"页面加载: {page_metrics.page_name} = "
                                   f"{page_metrics.load_time_ms}ms")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"用户体验监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("停止用户体验监控")
    
    def get_ui_response_stats(self, count: int = 100) -> List[Dict]:
        """获取UI响应统计"""
        return [m.to_dict() for m in list(self.ui_history)[-count:]]
    
    def get_operation_stats(self, count: int = 100) -> List[Dict]:
        """获取操作统计"""
        return [m.to_dict() for m in list(self.operation_history)[-count:]]
    
    def get_page_load_stats(self, count: int = 10) -> List[Dict]:
        """获取页面加载统计"""
        return [m.to_dict() for m in list(self.page_load_history)[-count:]]
    
    def get_experience_score(self) -> Dict:
        """获取用户体验评分"""
        # 计算UI响应评分
        if self.ui_history:
            recent_ui = list(self.ui_history)[-50:]
            avg_response = sum(m.total_time_ms for m in recent_ui) / len(recent_ui)
            
            # 响应时间评分（<100ms=优秀，<300ms=良好，<1000ms=一般，>1000ms=差）
            if avg_response < 100:
                ui_score = 100
            elif avg_response < 300:
                ui_score = 80
            elif avg_response < 1000:
                ui_score = 60
            else:
                ui_score = 40
        else:
            ui_score = 0
            avg_response = 0
        
        # 计算操作成功率评分
        if self.operation_history:
            recent_ops = list(self.operation_history)[-50:]
            success_rate = sum(1 for m in recent_ops if m.success) / len(recent_ops) * 100
            op_score = success_rate
        else:
            op_score = 0
            success_rate = 0
        
        # 计算页面加载评分
        if self.page_load_history:
            recent_pages = list(self.page_load_history)[-10:]
            avg_load = sum(m.load_time_ms for m in recent_pages) / len(recent_pages)
            
            # 加载时间评分（<500ms=优秀，<1500ms=良好，<3000ms=一般，>3000ms=差）
            if avg_load < 500:
                page_score = 100
            elif avg_load < 1500:
                page_score = 80
            elif avg_load < 3000:
                page_score = 60
            else:
                page_score = 40
        else:
            page_score = 0
            avg_load = 0
        
        # 综合评分
        overall_score = (ui_score * 0.5 + op_score * 0.3 + page_score * 0.2)
        
        # 评估等级
        if overall_score >= 90:
            grade = "优秀"
        elif overall_score >= 75:
            grade = "良好"
        elif overall_score >= 60:
            grade = "一般"
        else:
            grade = "需改进"
        
        return {
            "overall_score": round(overall_score, 1),
            "grade": grade,
            "ui_response_score": round(ui_score, 1),
            "ui_response_avg_ms": round(avg_response, 1),
            "operation_success_score": round(op_score, 1),
            "operation_success_rate": round(success_rate, 1),
            "page_load_score": round(page_score, 1),
            "page_load_avg_ms": round(avg_load, 1),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_slow_interactions(self, threshold_ms: float = 500) -> List[Dict]:
        """获取慢交互列表"""
        slow = []
        for metrics in self.ui_history:
            if metrics.total_time_ms > threshold_ms:
                slow.append({
                    "component": metrics.component,
                    "action": metrics.action,
                    "response_time_ms": metrics.response_time_ms,
                    "render_time_ms": metrics.render_time_ms,
                    "total_time_ms": metrics.total_time_ms,
                    "timestamp": metrics.timestamp
                })
        return sorted(slow, key=lambda x: x["total_time_ms"], reverse=True)[:10]


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        monitor = UserExperienceMonitor()
        
        # 启动监控
        task = asyncio.create_task(monitor.start_monitoring(interval=5))
        
        # 运行60秒
        await asyncio.sleep(60)
        
        # 获取体验评分
        score = monitor.get_experience_score()
        print(f"\n用户体验评分:")
        print(f"  综合评分: {score['overall_score']} ({score['grade']})")
        print(f"  UI响应评分: {score['ui_response_score']}")
        print(f"  操作成功率评分: {score['operation_success_score']}")
        print(f"  页面加载评分: {score['page_load_score']}")
        
        # 慢交互
        slow = monitor.get_slow_interactions(500)
        print(f"\n慢交互 (Top 10):")
        for interaction in slow:
            print(f"  {interaction['component']}.{interaction['action']}: "
                  f"{interaction['total_time_ms']}ms")
        
        # 停止监控
        monitor.stop_monitoring()
        task.cancel()
    
    asyncio.run(test())
