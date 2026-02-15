#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警数据模型
"""

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """告警状态"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertCreate(BaseModel):
    """创建告警请求"""
    rule_id: str
    title: str
    message: str
    level: AlertLevel
    source: str
    metadata: Optional[Dict] = None


class AlertResponse(BaseModel):
    """告警响应"""
    alert_id: str
    rule_id: str
    title: str
    message: str
    level: AlertLevel
    status: AlertStatus
    source: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Optional[Dict] = None


class AlertAcknowledge(BaseModel):
    """确认告警请求"""
    user: str


class AlertStats(BaseModel):
    """告警统计"""
    total: int
    active: int
    by_level: Dict[str, int]
    acknowledged: int
    resolved: int


class AlertRuleConfig(BaseModel):
    """告警规则配置"""
    rule_id: str
    name: str
    description: str
    level: AlertLevel
    condition: str
    duration: int
    enabled: bool
    channels: List[str]
    cooldown: int


class MetricType(str, Enum):
    """监控指标类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"
    LOAD = "load"
    CUSTOM = "custom"


class ComparisonOp(str, Enum):
    """比较操作符"""
    GT = "gt"  # 大于
    LT = "lt"  # 小于
    EQ = "eq"  # 等于
    GTE = "gte"  # 大于等于
    LTE = "lte"  # 小于等于


class NotificationChannel(str, Enum):
    """通知渠道"""
    BROWSER = "browser"
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertRule(BaseModel):
    """告警规则"""
    id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    metric: MetricType
    comparison: ComparisonOp = ComparisonOp.GT
    threshold: float
    duration: int = 5  # 分钟
    level: AlertLevel = AlertLevel.WARNING
    channels: List[NotificationChannel] = []
    email_recipients: List[str] = []
    webhook_url: Optional[str] = None
    silence_duration: int = 30  # 分钟
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AlertRuleCreateRequest(BaseModel):
    """创建告警规则请求"""
    name: str
    description: Optional[str] = None
    metric: MetricType
    comparison: ComparisonOp = ComparisonOp.GT
    threshold: float
    duration: int = 5
    level: AlertLevel = AlertLevel.WARNING
    channels: List[NotificationChannel] = []
    email_recipients: List[str] = []
    webhook_url: Optional[str] = None
    silence_duration: int = 30


class AlertRuleUpdateRequest(BaseModel):
    """更新告警规则请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    metric: Optional[MetricType] = None
    comparison: Optional[ComparisonOp] = None
    threshold: Optional[float] = None
    duration: Optional[int] = None
    level: Optional[AlertLevel] = None
    channels: Optional[List[NotificationChannel]] = None
    email_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    silence_duration: Optional[int] = None


class AlertRuleListResponse(BaseModel):
    """告警规则列表响应"""
    total: int
    items: List[AlertRule]


class AlertHistory(BaseModel):
    """告警历史记录"""
    id: str
    rule_id: str
    rule_name: str
    level: AlertLevel
    status: AlertStatus
    metric: MetricType
    threshold: float
    actual_value: float
    message: str
    triggered_at: datetime
    recovered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notifications_sent: List[str] = []


class AlertListResponse(BaseModel):
    """告警列表响应"""
    total: int
    items: List[AlertHistory]


class NotificationTestRequest(BaseModel):
    """通知测试请求"""
    channel: NotificationChannel
    email: Optional[str] = None
    webhook_url: Optional[str] = None
