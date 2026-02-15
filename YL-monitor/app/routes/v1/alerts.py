"""
告警系统 API 路由

功能:
- 告警规则 CRUD
- 告警历史查询
- 告警确认
- 通知测试

作者: AI Assistant
版本: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.models.alert import (
    AlertRule, AlertHistory, AlertRuleCreateRequest, AlertRuleUpdateRequest,
    AlertListResponse, AlertRuleListResponse, AlertStats, NotificationTestRequest,
    NotificationChannel, AlertStatus, AlertLevel, MetricType
)
from app.services.alert_service import get_alert_service


router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _get_service(request: Request):
    """获取告警服务实例"""
    return get_alert_service()


# ==================== 告警列表 API ====================

@router.get("")
@router.get("/")
async def list_alerts(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    level: Optional[AlertLevel] = Query(None, description="按级别筛选"),
    status: Optional[AlertStatus] = Query(None, description="按状态筛选")
):
    """
    获取告警列表（支持分页和筛选）
    
    前端实时告警面板调用此接口
    """
    service = _get_service(request)
    
    # 获取告警历史
    alerts = service.get_alert_history(
        level=level,
        status=status,
        limit=size,
        offset=(page - 1) * size
    )
    
    # 获取总数
    total = len(service.get_alert_history(limit=10000))
    
    return {
        "items": alerts,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size
    }


# ==================== 告警规则 API ====================

@router.get("/rules", response_model=AlertRuleListResponse)
async def list_rules(
    request: Request,
    enabled_only: bool = Query(False, description="仅显示启用的规则"),
    metric: Optional[MetricType] = Query(None, description="按指标类型筛选"),
    level: Optional[AlertLevel] = Query(None, description="按告警级别筛选")
):
    """
    获取告警规则列表
    
    支持筛选条件：
    - enabled_only: 仅显示启用的规则
    - metric: 按监控指标筛选（cpu/memory/disk/network）
    - level: 按告警级别筛选（warning/critical/info）
    """
    service = _get_service(request)
    rules = service.list_rules(
        enabled_only=enabled_only,
        metric=metric,
        level=level
    )
    
    return AlertRuleListResponse(
        total=len(rules),
        items=rules
    )


@router.get("/rules/{rule_id}")
async def get_rule(request: Request, rule_id: str):
    """
    获取单个告警规则详情
    """
    service = _get_service(request)
    rule = service.get_rule(rule_id)
    
    if rule is None:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    
    return rule


@router.post("/rules")
async def create_rule(request: Request, rule_data: AlertRuleCreateRequest):
    """
    创建告警规则
    
    示例请求:
    ```json
    {
        "name": "CPU 高使用率告警",
        "description": "当 CPU 使用率超过 80% 持续 5 分钟时触发",
        "metric": "cpu",
        "comparison": "gt",
        "threshold": 80.0,
        "duration": 5,
        "level": "warning",
        "channels": ["browser", "email"],
        "email_recipients": ["admin@example.com"],
        "silence_duration": 30
    }
    ```
    """
    service = _get_service(request)
    
    # 转换 Pydantic 模型为字典
    rule_dict = rule_data.dict()
    
    rule = service.create_rule(rule_dict)
    
    return {
        "success": True,
        "message": "告警规则创建成功",
        "data": rule
    }


@router.put("/rules/{rule_id}")
async def update_rule(
    request: Request, 
    rule_id: str, 
    update_data: AlertRuleUpdateRequest
):
    """
    更新告警规则
    
    支持部分更新，只需提供需要修改的字段
    """
    service = _get_service(request)
    
    # 过滤掉 None 值
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    rule = service.update_rule(rule_id, update_dict)
    
    if rule is None:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    
    return {
        "success": True,
        "message": "告警规则更新成功",
        "data": rule
    }


@router.delete("/rules/{rule_id}")
async def delete_rule(request: Request, rule_id: str):
    """
    删除告警规则
    """
    service = _get_service(request)
    
    success = service.delete_rule(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="告警规则不存在")
    
    return {
        "success": True,
        "message": "告警规则删除成功"
    }


# ==================== 告警历史 API ====================

@router.get("/history", response_model=AlertListResponse)
async def get_alert_history(
    request: Request,
    rule_id: Optional[str] = Query(None, description="按规则 ID 筛选"),
    status: Optional[AlertStatus] = Query(None, description="按状态筛选"),
    level: Optional[AlertLevel] = Query(None, description="按级别筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取告警历史记录
    
    支持多种筛选条件和分页
    """
    service = _get_service(request)
    
    alerts = service.get_alert_history(
        rule_id=rule_id,
        status=status,
        level=level,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    
    return AlertListResponse(
        total=len(alerts),
        items=alerts
    )


@router.get("/active")
async def get_active_alerts(request: Request):
    """
    获取当前活动告警（未恢复的告警）
    """
    service = _get_service(request)
    alerts = service.get_active_alerts()
    
    return {
        "total": len(alerts),
        "items": alerts
    }


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    request: Request, 
    alert_id: str,
    user: str = Query(..., description="确认人")
):
    """
    确认告警
    
    将告警状态从 TRIGGERED 改为 ACKNOWLEDGED
    """
    service = _get_service(request)
    
    alert = service.acknowledge_alert(alert_id, user)
    
    if alert is None:
        raise HTTPException(status_code=404, detail="告警记录不存在")
    
    return {
        "success": True,
        "message": "告警已确认",
        "data": alert
    }


# ==================== 统计 API ====================

@router.get("/stats")
async def get_alert_stats(request: Request):
    """
    获取告警统计信息
    
    返回：
    - total_alerts: 总告警数
    - triggered_today: 今日触发数
    - active_alerts: 当前活动告警数
    - recovered_today: 今日恢复数
    """
    service = _get_service(request)
    stats = service.get_stats()
    
    return stats


# ==================== 通知测试 API ====================

@router.post("/test-notification")
async def test_notification(
    request: Request,
    test_data: NotificationTestRequest
):
    """
    测试通知渠道
    
    支持测试浏览器推送、邮件、Webhook 等通知方式
    """
    service = _get_service(request)
    
    success = service.test_notification(
        channel=test_data.channel,
        email=test_data.email,
        webhook_url=test_data.webhook_url
    )
    
    if success:
        return {
            "success": True,
            "message": f"测试通知已发送，请检查 {test_data.channel.value} 渠道"
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"测试通知发送失败，请检查 {test_data.channel.value} 配置"
        )


# ==================== 批量操作 API ====================

class BatchDeleteRequest(BaseModel):
    rule_ids: List[str]


@router.post("/rules/batch-delete")
async def batch_delete_rules(request: Request, data: BatchDeleteRequest):
    """
    批量删除告警规则
    """
    service = _get_service(request)
    
    deleted = 0
    failed = []
    
    for rule_id in data.rule_ids:
        if service.delete_rule(rule_id):
            deleted += 1
        else:
            failed.append(rule_id)
    
    return {
        "success": True,
        "message": f"成功删除 {deleted} 条规则",
        "deleted_count": deleted,
        "failed_ids": failed
    }


@router.post("/rules/batch-enable")
async def batch_enable_rules(
    request: Request, 
    data: BatchDeleteRequest,
    enabled: bool = Query(..., description="启用或禁用")
):
    """
    批量启用/禁用告警规则
    """
    service = _get_service(request)
    
    updated = 0
    failed = []
    
    for rule_id in data.rule_ids:
        rule = service.update_rule(rule_id, {"enabled": enabled})
        if rule:
            updated += 1
        else:
            failed.append(rule_id)
    
    action = "启用" if enabled else "禁用"
    
    return {
        "success": True,
        "message": f"成功{action} {updated} 条规则",
        "updated_count": updated,
        "failed_ids": failed
    }
