"""
【文件功能】告警历史查询API
实现告警历史的查询、统计和分析功能

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现告警历史查询核心功能

【依赖说明】
- 标准库: datetime, typing
- 第三方库: fastapi, pydantic
- 内部模块: app.models.alert

【使用示例】
```python
from app.routes.v1.alerts_history import router

# 在FastAPI应用中注册
app.include_router(router, prefix="/api/v1")
```
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.models.alert import AlertHistory, AlertLevel, AlertStatus, MetricType

router = APIRouter(prefix="/alerts-history", tags=["告警历史与分析"])


class AlertHistoryListResponse(BaseModel):
    """【告警历史列表响应】"""
    total: int = Field(..., description="总数")
    items: List[AlertHistory] = Field(..., description="告警历史列表")
    summary: Dict[str, Any] = Field(default_factory=dict, description="汇总信息")


class AlertStatsResponse(BaseModel):
    """【告警统计响应】"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="统计数据")
    message: str = Field(default="获取统计成功", description="响应消息")


class AlertTrendResponse(BaseModel):
    """【告警趋势响应】"""
    success: bool = Field(..., description="是否成功")
    data: List[Dict[str, Any]] = Field(..., description="趋势数据")
    message: str = Field(default="获取趋势成功", description="响应消息")


class AlertDistributionResponse(BaseModel):
    """【告警分布响应】"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="分布数据")
    message: str = Field(default="获取分布成功", description="响应消息")


# 【内存存储】告警历史记录（生产环境应使用数据库）
_alert_history: List[AlertHistory] = []
_history_loaded = False


def _load_default_history():
    """【加载默认历史数据】初始化示例告警历史"""
    global _history_loaded
    if _history_loaded:
        return
    
    # 生成一些示例数据
    now = datetime.utcnow()
    default_history = [
        AlertHistory(
            id=f"alert-{uuid.uuid4().hex[:8]}",
            rule_id="rule-cpu-high",
            rule_name="CPU 高使用率告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.RECOVERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.5,
            message="CPU 使用率达到 85.5%，超过阈值 80%",
            triggered_at=now - timedelta(hours=2),
            recovered_at=now - timedelta(hours=1, minutes=30),
            duration_minutes=30,
            notifications_sent=[{"channel": "browser", "sent_at": (now - timedelta(hours=2)).isoformat()}]
        ),
        AlertHistory(
            id=f"alert-{uuid.uuid4().hex[:8]}",
            rule_id="rule-memory-high",
            rule_name="内存高使用率告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.ACKNOWLEDGED,
            metric=MetricType.MEMORY,
            threshold=85.0,
            actual_value=88.2,
            message="内存使用率达到 88.2%，超过阈值 85%",
            triggered_at=now - timedelta(hours=4),
            acknowledged_at=now - timedelta(hours=3, minutes=45),
            acknowledged_by="admin",
            duration_minutes=15,
            notifications_sent=[{"channel": "browser", "sent_at": (now - timedelta(hours=4)).isoformat()}]
        ),
        AlertHistory(
            id=f"alert-{uuid.uuid4().hex[:8]}",
            rule_id="rule-disk-high",
            rule_name="磁盘空间不足告警",
            level=AlertLevel.CRITICAL,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.DISK,
            threshold=90.0,
            actual_value=92.3,
            message="磁盘使用率达到 92.3%，超过阈值 90%",
            triggered_at=now - timedelta(minutes=30),
            duration_minutes=30,
            notifications_sent=[
                {"channel": "browser", "sent_at": (now - timedelta(minutes=30)).isoformat()},
                {"channel": "email", "sent_at": (now - timedelta(minutes=30)).isoformat()}
            ]
        ),
        AlertHistory(
            id=f"alert-{uuid.uuid4().hex[:8]}",
            rule_id="rule-load-high",
            rule_name="系统负载过高告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.RECOVERED,
            metric=MetricType.LOAD,
            threshold=5.0,
            actual_value=6.2,
            message="系统负载达到 6.2，超过阈值 5.0",
            triggered_at=now - timedelta(hours=6),
            recovered_at=now - timedelta(hours=5, minutes=15),
            duration_minutes=45,
            notifications_sent=[{"channel": "browser", "sent_at": (now - timedelta(hours=6)).isoformat()}]
        ),
        AlertHistory(
            id=f"alert-{uuid.uuid4().hex[:8]}",
            rule_id="rule-cpu-high",
            rule_name="CPU 高使用率告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.RECOVERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=82.1,
            message="CPU 使用率达到 82.1%，超过阈值 80%",
            triggered_at=now - timedelta(days=1, hours=3),
            recovered_at=now - timedelta(days=1, hours=2, minutes=20),
            duration_minutes=40,
            notifications_sent=[{"channel": "browser", "sent_at": (now - timedelta(days=1, hours=3)).isoformat()}]
        )
    ]
    
    _alert_history.extend(default_history)
    _history_loaded = True


def _get_history_store():
    """【获取历史存储】获取告警历史存储"""
    _load_default_history()
    return _alert_history


@router.get("", response_model=AlertHistoryListResponse)
async def list_alert_history(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    level: Optional[AlertLevel] = Query(None, description="告警级别筛选"),
    status: Optional[AlertStatus] = Query(None, description="告警状态筛选"),
    metric: Optional[MetricType] = Query(None, description="监控指标筛选"),
    rule_id: Optional[str] = Query(None, description="规则ID筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """
    【获取告警历史列表】分页查询告警历史
    
    【参数说明】
    - start_time: 开始时间（ISO格式）
    - end_time: 结束时间（ISO格式）
    - level: 按告警级别筛选（warning/critical/info）
    - status: 按告警状态筛选（triggered/recovered/acknowledged）
    - metric: 按监控指标筛选（cpu/memory/disk/network/load/process）
    - rule_id: 按规则ID筛选
    - skip: 分页偏移量
    - limit: 每页数量
    
    【返回值】
    - total: 符合条件的总数量
    - items: 告警历史列表
    - summary: 汇总信息（各级别数量）
    """
    store = _get_history_store()
    alerts = list(store)
    
    # 应用筛选条件
    if start_time:
        alerts = [a for a in alerts if a.triggered_at >= start_time]
    
    if end_time:
        alerts = [a for a in alerts if a.triggered_at <= end_time]
    
    if level:
        alerts = [a for a in alerts if a.level == level]
    
    if status:
        alerts = [a for a in alerts if a.status == status]
    
    if metric:
        alerts = [a for a in alerts if a.metric == metric]
    
    if rule_id:
        alerts = [a for a in alerts if a.rule_id == rule_id]
    
    # 按触发时间倒序
    alerts.sort(key=lambda x: x.triggered_at, reverse=True)
    
    # 计算汇总
    summary = {
        "total": len(alerts),
        "by_level": {
            "warning": sum(1 for a in alerts if a.level == AlertLevel.WARNING),
            "critical": sum(1 for a in alerts if a.level == AlertLevel.CRITICAL),
            "info": sum(1 for a in alerts if a.level == AlertLevel.INFO)
        },
        "by_status": {
            "triggered": sum(1 for a in alerts if a.status == AlertStatus.TRIGGERED),
            "recovered": sum(1 for a in alerts if a.status == AlertStatus.RECOVERED),
            "acknowledged": sum(1 for a in alerts if a.status == AlertStatus.ACKNOWLEDGED)
        }
    }
    
    total = len(alerts)
    alerts = alerts[skip:skip + limit]
    
    return AlertHistoryListResponse(total=total, items=alerts, summary=summary)


@router.get("/stats/overview", response_model=AlertStatsResponse)
async def get_alert_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """
    【获取告警统计概览】获取指定时间范围内的告警统计
    
    【参数说明】
    - days: 统计天数（1-90天）
    
    【返回值】
    - total_alerts: 总告警数
    - triggered_alerts: 触发中告警数
    - recovered_alerts: 已恢复告警数
    - acknowledged_alerts: 已确认告警数
    - avg_resolution_time: 平均恢复时间（分钟）
    - by_level: 按级别统计
    - by_metric: 按指标统计
    - by_day: 按天统计
    """
    store = _get_history_store()
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # 筛选时间范围内的告警
    alerts = [a for a in store if a.triggered_at >= cutoff]
    
    # 基础统计
    total = len(alerts)
    triggered = sum(1 for a in alerts if a.status == AlertStatus.TRIGGERED)
    recovered = sum(1 for a in alerts if a.status == AlertStatus.RECOVERED)
    acknowledged = sum(1 for a in alerts if a.status == AlertStatus.ACKNOWLEDGED)
    
    # 计算平均恢复时间
    resolved_alerts = [a for a in alerts if a.recovered_at and a.duration_minutes]
    avg_resolution_time = sum(a.duration_minutes for a in resolved_alerts) / len(resolved_alerts) if resolved_alerts else 0
    
    # 按级别统计
    by_level = {
        "warning": sum(1 for a in alerts if a.level == AlertLevel.WARNING),
        "critical": sum(1 for a in alerts if a.level == AlertLevel.CRITICAL),
        "info": sum(1 for a in alerts if a.level == AlertLevel.INFO)
    }
    
    # 按指标统计
    by_metric = {}
    for metric in MetricType:
        by_metric[metric.value] = sum(1 for a in alerts if a.metric == metric)
    
    # 按天统计
    by_day = {}
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_start = datetime.utcnow() - timedelta(days=i+1)
        day_end = datetime.utcnow() - timedelta(days=i)
        day_count = sum(1 for a in alerts if day_start <= a.triggered_at < day_end)
        by_day[day] = day_count
    
    return AlertStatsResponse(
        success=True,
        data={
            "period_days": days,
            "total_alerts": total,
            "triggered_alerts": triggered,
            "recovered_alerts": recovered,
            "acknowledged_alerts": acknowledged,
            "avg_resolution_time_minutes": round(avg_resolution_time, 2),
            "by_level": by_level,
            "by_metric": by_metric,
            "by_day": by_day
        }
    )


@router.get("/trend/hourly", response_model=AlertTrendResponse)
async def get_hourly_trend(
    hours: int = Query(24, ge=1, le=168, description="统计小时数")
):
    """
    【获取小时级告警趋势】获取最近N小时的告警趋势
    
    【参数说明】
    - hours: 统计小时数（1-168小时，即1周）
    
    【返回值】
    - 每小时告警数量，按级别分组
    """
    store = _get_history_store()
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours)
    
    # 筛选时间范围内的告警
    alerts = [a for a in store if a.triggered_at >= cutoff]
    
    # 按小时统计
    hourly_data = []
    for i in range(hours):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)
        hour_label = hour_start.strftime("%H:00")
        
        hour_alerts = [a for a in alerts if hour_start <= a.triggered_at < hour_end]
        
        hourly_data.append({
            "hour": hour_label,
            "total": len(hour_alerts),
            "warning": sum(1 for a in hour_alerts if a.level == AlertLevel.WARNING),
            "critical": sum(1 for a in hour_alerts if a.level == AlertLevel.CRITICAL),
            "info": sum(1 for a in hour_alerts if a.level == AlertLevel.INFO)
        })
    
    # 倒序排列（从早到晚）
    hourly_data.reverse()
    
    return AlertTrendResponse(
        success=True,
        data=hourly_data
    )


@router.get("/trend/daily", response_model=AlertTrendResponse)
async def get_daily_trend(
    days: int = Query(7, ge=1, le=30, description="统计天数")
):
    """
    【获取天级告警趋势】获取最近N天的告警趋势
    
    【参数说明】
    - days: 统计天数（1-30天）
    
    【返回值】
    - 每天告警数量，按级别分组
    """
    store = _get_history_store()
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    
    # 筛选时间范围内的告警
    alerts = [a for a in store if a.triggered_at >= cutoff]
    
    # 按天统计
    daily_data = []
    for i in range(days):
        day_start = now - timedelta(days=i+1)
        day_end = now - timedelta(days=i)
        day_label = day_start.strftime("%m-%d")
        
        day_alerts = [a for a in alerts if day_start <= a.triggered_at < day_end]
        
        daily_data.append({
            "date": day_label,
            "total": len(day_alerts),
            "warning": sum(1 for a in day_alerts if a.level == AlertLevel.WARNING),
            "critical": sum(1 for a in day_alerts if a.level == AlertLevel.CRITICAL),
            "info": sum(1 for a in day_alerts if a.level == AlertLevel.INFO)
        })
    
    # 倒序排列（从早到晚）
    daily_data.reverse()
    
    return AlertTrendResponse(
        success=True,
        data=daily_data
    )


@router.get("/distribution/level", response_model=AlertDistributionResponse)
async def get_level_distribution(
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """
    【获取告警级别分布】获取告警级别的分布情况
    
    【参数说明】
    - days: 统计天数
    
    【返回值】
    - 各级别告警数量和占比
    """
    store = _get_history_store()
    cutoff = datetime.utcnow() - timedelta(days=days)
    alerts = [a for a in store if a.triggered_at >= cutoff]
    
    total = len(alerts)
    
    distribution = {
        "warning": {
            "count": sum(1 for a in alerts if a.level == AlertLevel.WARNING),
            "color": "#ffc107"
        },
        "critical": {
            "count": sum(1 for a in alerts if a.level == AlertLevel.CRITICAL),
            "color": "#dc3545"
        },
        "info": {
            "count": sum(1 for a in alerts if a.level == AlertLevel.INFO),
            "color": "#17a2b8"
        }
    }
    
    # 计算百分比
    for key in distribution:
        distribution[key]["percentage"] = round(
            distribution[key]["count"] / total * 100, 2
        ) if total > 0 else 0
    
    return AlertDistributionResponse(
        success=True,
        data={
            "total": total,
            "distribution": distribution
        }
    )


@router.get("/distribution/metric", response_model=AlertDistributionResponse)
async def get_metric_distribution(
    days: int = Query(7, ge=1, le=90, description="统计天数")
):
    """
    【获取告警指标分布】获取各监控指标的告警分布情况
    
    【参数说明】
    - days: 统计天数
    
    【返回值】
    - 各指标告警数量和占比
    """
    store = _get_history_store()
    cutoff = datetime.utcnow() - timedelta(days=days)
    alerts = [a for a in store if a.triggered_at >= cutoff]
    
    total = len(alerts)
    
    # 按指标统计
    distribution = {}
    metric_colors = {
        "cpu": "#007bff",
        "memory": "#28a745",
        "disk": "#ffc107",
        "network": "#17a2b8",
        "load": "#6f42c1",
        "process": "#fd7e14",
        "custom": "#6c757d"
    }
    
    for metric in MetricType:
        count = sum(1 for a in alerts if a.metric == metric)
        distribution[metric.value] = {
            "count": count,
            "color": metric_colors.get(metric.value, "#6c757d"),
            "percentage": round(count / total * 100, 2) if total > 0 else 0
        }
    
    return AlertDistributionResponse(
        success=True,
        data={
            "total": total,
            "distribution": distribution
        }
    )


@router.get("/top/rules", response_model=AlertStatsResponse)
async def get_top_rules(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """
    【获取触发最多的规则】获取触发次数最多的告警规则
    
    【参数说明】
    - days: 统计天数
    - limit: 返回数量限制
    
    【返回值】
    - 触发次数最多的规则列表
    """
    store = _get_history_store()
    cutoff = datetime.utcnow() - timedelta(days=days)
    alerts = [a for a in store if a.triggered_at >= cutoff]
    
    # 按规则统计
    rule_stats = {}
    for alert in alerts:
        if alert.rule_id not in rule_stats:
            rule_stats[alert.rule_id] = {
                "rule_id": alert.rule_id,
                "rule_name": alert.rule_name,
                "count": 0,
                "levels": set()
            }
        rule_stats[alert.rule_id]["count"] += 1
        rule_stats[alert.rule_id]["levels"].add(alert.level.value)
    
    # 转换为列表并排序
    top_rules = sorted(
        rule_stats.values(),
        key=lambda x: x["count"],
        reverse=True
    )[:limit]
    
    # 转换set为list
    for rule in top_rules:
        rule["levels"] = list(rule["levels"])
    
    return AlertStatsResponse(
        success=True,
        data={
            "period_days": days,
            "top_rules": top_rules
        }
    )
