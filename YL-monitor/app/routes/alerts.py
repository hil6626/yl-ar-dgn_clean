#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警路由
提供告警管理API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.models.alert import (
    AlertResponse, AlertAcknowledge, AlertStats,
    AlertLevel, AlertStatus
)
from app.services.alert_service import AlertService, get_alert_service
import random as _random

router = APIRouter(prefix="/api/alerts", tags=["告警管理"])


def get_alert_service_instance() -> AlertService:
    """获取告警服务实例"""
    return get_alert_service()


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[AlertStatus] = None,
    level: Optional[AlertLevel] = None,
    source: Optional[str] = None
):
    """获取告警列表"""
    service = get_alert_service_instance()
    
    alerts = service.get_active_alerts()
    
    if status:
        alerts = [a for a in alerts if a.status.value == status.value]
    if level:
        alerts = [a for a in alerts if a.level.value == level.value]
    if source:
        alerts = [a for a in alerts if a.rule_id == source]
    
    return [
        AlertResponse(
            alert_id=a.id,
            rule_id=a.rule_id,
            title=a.rule_name,
            message=a.message,
            level=AlertLevel(a.level.value),
            status=AlertStatus(a.status.value),
            source=a.rule_id,
            created_at=a.triggered_at,
            acknowledged_at=a.acknowledged_at,
            resolved_at=a.recovered_at,
            acknowledged_by=a.acknowledged_by,
            metadata={"actual_value": a.actual_value, "threshold": a.threshold}
        )
        for a in alerts
    ]


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats():
    """获取告警统计"""
    service = get_alert_service_instance()
    stats = service.get_stats()
    
    return AlertStats(
        total=stats.get("total_alerts", 0),
        active=stats.get("active_alerts", 0),
        by_level={
            "info": 0,
            "warning": 0,
            "error": 0,
            "critical": 0
        },
        acknowledged=stats.get("recovered_today", 0),
        resolved=stats.get("recovered_today", 0)
    )


@router.post("/{alert_key}/acknowledge")
async def acknowledge_alert(alert_key: str, ack: AlertAcknowledge):
    """确认告警"""
    service = get_alert_service_instance()
    
    alert = service.acknowledge_alert(alert_key, ack.user)
    if alert:
        return {"status": "success", "message": "告警已确认"}
    else:
        raise HTTPException(status_code=404, detail="告警不存在")


@router.post("/{alert_key}/resolve")
async def resolve_alert(alert_key: str):
    """解决告警"""
    service = get_alert_service_instance()
    
    # AlertService 使用 acknowledge 作为解决方式
    alert = service.acknowledge_alert(alert_key, "system")
    if alert:
        return {"status": "success", "message": "告警已解决"}
    else:
        raise HTTPException(status_code=404, detail="告警不存在")


@router.post("/acknowledge-all")
async def acknowledge_all_alerts():
    """确认所有活跃告警"""
    service = get_alert_service_instance()
    
    alerts = service.get_active_alerts()
    acknowledged_count = 0
    
    for alert in alerts:
        if service.acknowledge_alert(alert.id, "system"):
            acknowledged_count += 1
    
    return {
        "status": "success",
        "message": f"已确认 {acknowledged_count} 条告警",
        "count": acknowledged_count
    }


@router.get("/analytics/stats")
async def get_analytics_stats(time_range: str = "7d"):
    """获取告警分析统计"""
    service = get_alert_service_instance()
    
    # 获取统计数据
    stats = service.get_stats()
    
    return {
        "total": stats.get("total_alerts", 0),
        "warning": stats.get("warning_count", 0),
        "critical": stats.get("critical_count", 0),
        "info": stats.get("info_count", 0),
        "range": time_range
    }


@router.get("/analytics/trend")
async def get_analytics_trend(time_range: str = "7d"):
    """获取告警趋势数据"""
    # 生成模拟趋势数据
    from datetime import datetime, timedelta
    
    days = 7 if time_range == "7d" else (30 if time_range == "30d" else 1)
    trend = []
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        trend.append({
            "date": date.strftime("%m-%d"),
            "critical": _random.randint(0, 5),
            "warning": _random.randint(2, 15),
            "info": _random.randint(5, 30)
        })
    
    # 级别分布
    level_distribution = {
        "critical": _random.randint(10, 50),
        "warning": _random.randint(50, 150),
        "info": _random.randint(100, 300)
    }
    
    # 指标分布
    metric_distribution = {
        "cpu": _random.randint(20, 80),
        "memory": _random.randint(15, 60),
        "disk": _random.randint(10, 40),
        "network": _random.randint(5, 30),
        "load": _random.randint(8, 25)
    }
    
    return {
        "trend": trend,
        "level_distribution": level_distribution,
        "metric_distribution": metric_distribution,
        "range": time_range
    }


@router.get("/intelligent/config")
async def get_intelligent_config():
    """获取智能告警配置"""
    # 返回默认配置
    return {
        "noiseReduction": True,
        "trendPrediction": True,
        "rootCauseAnalysis": False,
        "similarityThreshold": 80,
        "timeWindow": 30
    }


@router.put("/intelligent/config")
async def update_intelligent_config(config: dict):
    """更新智能告警配置"""
    # 保存配置（实际项目中应持久化存储）
    return {
        "status": "success",
        "message": "配置已更新",
        "config": config
    }


@router.get("/history", response_model=List[AlertResponse])
async def get_alert_history(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    level: Optional[AlertLevel] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """获取告警历史"""
    service = get_alert_service_instance()
    
    from app.models.alert import AlertLevel as ALLevel
    alerts = service.get_alert_history(
        start_time=start_time,
        end_time=end_time,
        level=ALLevel(level) if level else None,
        limit=limit
    )
    
    return [
        AlertResponse(
            alert_id=a.id,
            rule_id=a.rule_id,
            title=a.rule_name,
            message=a.message,
            level=AlertLevel(a.level.value),
            status=AlertStatus(a.status.value),
            source=a.rule_id,
            created_at=a.triggered_at,
            acknowledged_at=a.acknowledged_at,
            resolved_at=a.recovered_at,
            acknowledged_by=a.acknowledged_by,
            metadata={"actual_value": a.actual_value, "threshold": a.threshold}
        )
        for a in alerts
    ]
