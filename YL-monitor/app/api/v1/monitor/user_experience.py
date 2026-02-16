#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户体验监控 API
提供GUI交互、页面加载、用户操作的详细监控数据
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.user_experience_monitor import ux_collector

router = APIRouter()


@router.get("/user-experience")
async def get_user_experience_metrics() -> Dict[str, Any]:
    """
    获取完整的用户体验层监控数据
    
    包括：
    - GUI交互指标（响应时间、渲染时间、成功率）
    - 页面加载指标（加载时间、DOM就绪、资源加载）
    - 用户操作指标（执行时间、成功率、重试次数）
    - 用户满意度评分
    """
    try:
        return ux_collector.collect_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-experience/gui")
async def get_gui_metrics() -> Dict[str, Any]:
    """
    获取GUI交互监控指标
    """
    try:
        interactions = ux_collector.gui_monitor.get_metrics()
        return {
            "interactions": [i.to_dict() for i in interactions],
            "count": len(interactions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-experience/gui/{component_id}")
async def get_component_metrics(component_id: str) -> Dict[str, Any]:
    """
    获取指定GUI组件的监控指标
    """
    try:
        return ux_collector.gui_monitor.get_component_metrics(component_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-experience/pages")
async def get_page_metrics() -> Dict[str, Any]:
    """
    获取页面加载监控指标
    """
    try:
        pages = ux_collector.page_monitor.get_metrics()
        return {
            "page_loads": [p.to_dict() for p in pages],
            "stats": ux_collector.page_monitor.get_page_stats(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-experience/actions")
async def get_user_actions() -> Dict[str, Any]:
    """
    获取用户操作监控指标
    """
    try:
        actions = ux_collector.action_monitor.get_metrics()
        return {
            "actions": [a.to_dict() for a in actions],
            "stats": ux_collector.action_monitor.get_action_stats(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-experience/health")
async def get_user_experience_health() -> Dict[str, Any]:
    """
    获取用户体验健康状态摘要
    """
    try:
        return ux_collector.get_health_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-experience/interaction")
async def record_interaction(
    component_id: str,
    interaction_type: str,
    response_time_ms: float,
    success: bool = True
) -> Dict[str, Any]:
    """
    记录GUI交互（用于前端上报）
    """
    try:
        ux_collector.gui_monitor.record_interaction(
            component_id=component_id,
            interaction_type=interaction_type,
            response_time_ms=response_time_ms,
            success=success
        )
        return {"status": "recorded", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-experience/action")
async def record_action(
    action_type: str,
    execution_time_ms: float,
    success: bool = True
) -> Dict[str, Any]:
    """
    记录用户操作（用于前端上报）
    """
    try:
        ux_collector.action_monitor.record_action(
            action_type=action_type,
            action_params={},
            execution_time_ms=execution_time_ms,
            success=success
        )
        return {"status": "recorded", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
