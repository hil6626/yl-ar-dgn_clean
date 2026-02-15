"""
【文件功能】告警规则管理API路由
实现告警规则的CRUD操作、批量管理和统计查询

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现告警规则管理核心功能

【依赖说明】
- 标准库: datetime, typing
- 第三方库: fastapi, pydantic
- 内部模块: app.models.alert, app.services.alert_service

【使用示例】
```python
from app.routes.v1.alert_rules import router

# 在FastAPI应用中注册
app.include_router(router, prefix="/api/v1")
```
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field

from app.models.alert import (
    AlertRule, AlertRuleCreateRequest, AlertRuleUpdateRequest,
    AlertRuleListResponse, MetricType, ComparisonOp, AlertLevel,
    NotificationChannel
)
from app.services.alert_service import get_alert_service

router = APIRouter(prefix="/alert-rules", tags=["告警规则管理"])


class AlertRuleResponse(BaseModel):
    """【告警规则响应】单个告警规则响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[AlertRule] = Field(None, description="告警规则数据")
    message: str = Field(default="操作成功", description="响应消息")


class AlertRuleBatchResponse(BaseModel):
    """【批量操作响应】批量操作结果"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="操作结果详情")
    message: str = Field(default="批量操作完成", description="响应消息")


class AlertRuleStatsResponse(BaseModel):
    """【告警规则统计响应】统计信息"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="统计数据")
    message: str = Field(default="获取统计成功", description="响应消息")


class AlertRuleToggleRequest(BaseModel):
    """【启用/禁用请求】批量启用或禁用"""
    rule_ids: List[str] = Field(..., description="规则ID列表")
    enabled: bool = Field(..., description="启用状态")


# 【内存存储】告警规则存储（生产环境应使用数据库）
_alert_rules: Dict[str, AlertRule] = {}
_alert_rules_loaded = False


def _load_default_rules():
    """【加载默认规则】初始化默认告警规则"""
    global _alert_rules_loaded
    if _alert_rules_loaded:
        return
    
    default_rules = [
        AlertRule(
            id="rule-cpu-high",
            name="CPU 高使用率告警",
            description="当 CPU 使用率超过 80% 持续 5 分钟时触发告警",
            enabled=True,
            metric=MetricType.CPU,
            comparison=ComparisonOp.GT,
            threshold=80.0,
            duration=5,
            level=AlertLevel.WARNING,
            channels=[NotificationChannel.BROWSER],
            silence_duration=30
        ),
        AlertRule(
            id="rule-memory-high",
            name="内存高使用率告警",
            description="当内存使用率超过 85% 持续 5 分钟时触发告警",
            enabled=True,
            metric=MetricType.MEMORY,
            comparison=ComparisonOp.GT,
            threshold=85.0,
            duration=5,
            level=AlertLevel.WARNING,
            channels=[NotificationChannel.BROWSER],
            silence_duration=30
        ),
        AlertRule(
            id="rule-disk-high",
            name="磁盘空间不足告警",
            description="当磁盘使用率超过 90% 时触发严重告警",
            enabled=True,
            metric=MetricType.DISK,
            comparison=ComparisonOp.GT,
            threshold=90.0,
            duration=1,
            level=AlertLevel.CRITICAL,
            channels=[NotificationChannel.BROWSER, NotificationChannel.EMAIL],
            silence_duration=60
        ),
        AlertRule(
            id="rule-load-high",
            name="系统负载过高告警",
            description="当系统负载超过 5.0 持续 10 分钟时触发告警",
            enabled=True,
            metric=MetricType.LOAD,
            comparison=ComparisonOp.GT,
            threshold=5.0,
            duration=10,
            level=AlertLevel.WARNING,
            channels=[NotificationChannel.BROWSER],
            silence_duration=30
        )
    ]
    
    for rule in default_rules:
        _alert_rules[rule.id] = rule
    
    _alert_rules_loaded = True


def _get_rules_store():
    """【获取规则存储】获取告警规则存储"""
    _load_default_rules()
    return _alert_rules


@router.get("", response_model=AlertRuleListResponse)
async def list_alert_rules(
    metric: Optional[MetricType] = Query(None, description="按指标类型筛选"),
    level: Optional[AlertLevel] = Query(None, description="按告警级别筛选"),
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """
    【获取告警规则列表】分页查询告警规则
    
    【参数说明】
    - metric: 按监控指标筛选（cpu/memory/disk/network/load/process）
    - level: 按告警级别筛选（warning/critical/info）
    - enabled: 按启用状态筛选（true/false）
    - search: 搜索规则名称和描述
    - skip: 分页偏移量
    - limit: 每页数量
    
    【返回值】
    - total: 符合条件的总数量
    - items: 告警规则列表
    """
    store = _get_rules_store()
    rules = list(store.values())
    
    # 应用筛选条件
    if metric:
        rules = [r for r in rules if r.metric == metric]
    
    if level:
        rules = [r for r in rules if r.level == level]
    
    if enabled is not None:
        rules = [r for r in rules if r.enabled == enabled]
    
    if search:
        search_lower = search.lower()
        rules = [
            r for r in rules 
            if search_lower in r.name.lower() or 
               (r.description and search_lower in r.description.lower())
        ]
    
    # 按更新时间倒序
    rules.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
    
    total = len(rules)
    rules = rules[skip:skip + limit]
    
    return AlertRuleListResponse(total=total, items=rules)


@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str = Path(..., description="告警规则ID")
):
    """
    【获取单个告警规则】根据ID获取告警规则详情
    
    【参数说明】
    - rule_id: 告警规则唯一标识
    
    【返回值】
    - success: 是否成功
    - data: 告警规则详情
    - message: 响应消息
    """
    store = _get_rules_store()
    
    if rule_id not in store:
        raise HTTPException(status_code=404, detail=f"告警规则 {rule_id} 不存在")
    
    return AlertRuleResponse(success=True, data=store[rule_id])


@router.post("", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    request: AlertRuleCreateRequest = Body(..., description="创建告警规则请求")
):
    """
    【创建告警规则】创建新的告警规则
    
    【请求体】
    - name: 规则名称（必填）
    - description: 规则描述（可选）
    - metric: 监控指标（必填）
    - comparison: 比较操作符（默认大于）
    - threshold: 阈值（必填，0-100）
    - duration: 持续时间分钟（默认5）
    - level: 告警级别（默认warning）
    - channels: 通知渠道列表
    - email_recipients: 邮件接收者列表
    - webhook_url: Webhook URL
    - silence_duration: 静默期分钟（默认30）
    
    【返回值】
    - success: 是否成功
    - data: 创建的告警规则
    - message: 响应消息
    """
    store = _get_rules_store()
    
    # 生成唯一ID
    rule_id = f"rule-{uuid.uuid4().hex[:8]}"
    
    # 创建规则
    rule = AlertRule(
        id=rule_id,
        name=request.name,
        description=request.description,
        enabled=True,
        metric=request.metric,
        comparison=request.comparison,
        threshold=request.threshold,
        duration=request.duration,
        level=request.level,
        channels=request.channels,
        email_recipients=request.email_recipients,
        webhook_url=request.webhook_url,
        silence_duration=request.silence_duration,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    store[rule_id] = rule
    
    return AlertRuleResponse(
        success=True, 
        data=rule,
        message="告警规则创建成功"
    )


@router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str = Path(..., description="告警规则ID"),
    request: AlertRuleUpdateRequest = Body(..., description="更新告警规则请求")
):
    """
    【更新告警规则】更新现有告警规则
    
    【参数说明】
    - rule_id: 要更新的规则ID
    
    【请求体】
    所有字段均为可选，只更新提供的字段
    
    【返回值】
    - success: 是否成功
    - data: 更新后的告警规则
    - message: 响应消息
    """
    store = _get_rules_store()
    
    if rule_id not in store:
        raise HTTPException(status_code=404, detail=f"告警规则 {rule_id} 不存在")
    
    existing = store[rule_id]
    
    # 更新字段
    update_data = request.dict(exclude_unset=True)
    updated_rule = existing.copy(update=update_data)
    updated_rule.updated_at = datetime.utcnow()
    
    store[rule_id] = updated_rule
    
    return AlertRuleResponse(
        success=True,
        data=updated_rule,
        message="告警规则更新成功"
    )


@router.delete("/{rule_id}", response_model=AlertRuleResponse)
async def delete_alert_rule(
    rule_id: str = Path(..., description="告警规则ID")
):
    """
    【删除告警规则】删除指定的告警规则
    
    【参数说明】
    - rule_id: 要删除的规则ID
    
    【返回值】
    - success: 是否成功
    - message: 响应消息
    """
    store = _get_rules_store()
    
    if rule_id not in store:
        raise HTTPException(status_code=404, detail=f"告警规则 {rule_id} 不存在")
    
    deleted_rule = store.pop(rule_id)
    
    return AlertRuleResponse(
        success=True,
        data=deleted_rule,
        message="告警规则删除成功"
    )


@router.post("/batch/toggle", response_model=AlertRuleBatchResponse)
async def batch_toggle_rules(
    request: AlertRuleToggleRequest = Body(..., description="批量启用/禁用请求")
):
    """
    【批量启用/禁用】批量启用或禁用告警规则
    
    【请求体】
    - rule_ids: 规则ID列表
    - enabled: 目标状态（true启用/false禁用）
    
    【返回值】
    - success: 是否成功
    - data: 操作详情（成功数量、失败数量、失败列表）
    - message: 响应消息
    """
    store = _get_rules_store()
    
    success_count = 0
    failed_ids = []
    
    for rule_id in request.rule_ids:
        if rule_id in store:
            rule = store[rule_id]
            rule.enabled = request.enabled
            rule.updated_at = datetime.utcnow()
            store[rule_id] = rule
            success_count += 1
        else:
            failed_ids.append(rule_id)
    
    return AlertRuleBatchResponse(
        success=True,
        data={
            "total": len(request.rule_ids),
            "success": success_count,
            "failed": len(failed_ids),
            "failed_ids": failed_ids,
            "enabled": request.enabled
        },
        message=f"批量{'启用' if request.enabled else '禁用'}完成"
    )


@router.post("/batch/delete", response_model=AlertRuleBatchResponse)
async def batch_delete_rules(
    rule_ids: List[str] = Body(..., description="要删除的规则ID列表")
):
    """
    【批量删除】批量删除告警规则
    
    【请求体】
    - rule_ids: 要删除的规则ID列表
    
    【返回值】
    - success: 是否成功
    - data: 操作详情
    - message: 响应消息
    """
    store = _get_rules_store()
    
    success_count = 0
    failed_ids = []
    
    for rule_id in rule_ids:
        if rule_id in store:
            store.pop(rule_id)
            success_count += 1
        else:
            failed_ids.append(rule_id)
    
    return AlertRuleBatchResponse(
        success=True,
        data={
            "total": len(rule_ids),
            "success": success_count,
            "failed": len(failed_ids),
            "failed_ids": failed_ids
        },
        message="批量删除完成"
    )


@router.get("/stats/overview", response_model=AlertRuleStatsResponse)
async def get_alert_rules_stats():
    """
    【获取告警规则统计】获取告警规则统计信息
    
    【返回值】
    - total: 规则总数
    - enabled: 启用数量
    - disabled: 禁用数量
    - by_metric: 按指标类型统计
    - by_level: 按告警级别统计
    """
    store = _get_rules_store()
    rules = list(store.values())
    
    # 基础统计
    total = len(rules)
    enabled = sum(1 for r in rules if r.enabled)
    disabled = total - enabled
    
    # 按指标统计
    by_metric = {}
    for metric in MetricType:
        count = sum(1 for r in rules if r.metric == metric)
        by_metric[metric.value] = count
    
    # 按级别统计
    by_level = {}
    for level in AlertLevel:
        count = sum(1 for r in rules if r.level == level)
        by_level[level.value] = count
    
    return AlertRuleStatsResponse(
        success=True,
        data={
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "by_metric": by_metric,
            "by_level": by_level
        }
    )


@router.get("/metrics/types")
async def get_metric_types():
    """
    【获取指标类型】获取支持的监控指标类型列表
    
    【返回值】
    - 指标类型列表，包含名称和描述
    """
    return {
        "success": True,
        "data": [
            {"value": mt.value, "label": _get_metric_label(mt), "unit": _get_metric_unit(mt)}
            for mt in MetricType
        ]
    }


@router.get("/levels/types")
async def get_alert_levels():
    """
    【获取告警级别】获取支持的告警级别列表
    
    【返回值】
    - 告警级别列表，包含名称和描述
    """
    return {
        "success": True,
        "data": [
            {"value": level.value, "label": _get_level_label(level), "color": _get_level_color(level)}
            for level in AlertLevel
        ]
    }


def _get_metric_label(metric: MetricType) -> str:
    """【获取指标标签】"""
    labels = {
        MetricType.CPU: "CPU 使用率",
        MetricType.MEMORY: "内存使用率",
        MetricType.DISK: "磁盘使用率",
        MetricType.NETWORK: "网络流量",
        MetricType.PROCESS: "进程数",
        MetricType.LOAD: "系统负载",
        MetricType.CUSTOM: "自定义指标"
    }
    return labels.get(metric, metric.value)


def _get_metric_unit(metric: MetricType) -> str:
    """【获取指标单位】"""
    units = {
        MetricType.CPU: "%",
        MetricType.MEMORY: "%",
        MetricType.DISK: "%",
        MetricType.NETWORK: "MB/s",
        MetricType.PROCESS: "个",
        MetricType.LOAD: "",
        MetricType.CUSTOM: ""
    }
    return units.get(metric, "")


def _get_level_label(level: AlertLevel) -> str:
    """【获取级别标签】"""
    labels = {
        AlertLevel.INFO: "信息",
        AlertLevel.WARNING: "警告",
        AlertLevel.CRITICAL: "严重"
    }
    return labels.get(level, level.value)


def _get_level_color(level: AlertLevel) -> str:
    """【获取级别颜色】"""
    colors = {
        AlertLevel.INFO: "#17a2b8",
        AlertLevel.WARNING: "#ffc107",
        AlertLevel.CRITICAL: "#dc3545"
    }
    return colors.get(level, "#6c757d")
