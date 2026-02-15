"""
告警核心服务

功能:
- 告警规则管理（CRUD）
- 告警状态检查
- 通知发送
- 告警历史记录

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.models.alert import (
    AlertRule, AlertHistory, AlertStatus, AlertLevel,
    MetricType, NotificationChannel, ComparisonOp
)
from app.services.event_bus import EventBus, EventType, Event
from app.services.email_service import get_email_service
from app.services.webhook_service import get_webhook_service


class AlertService:
    """告警服务"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("data/alerts")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.rules_file = self.storage_dir / "rules.json"
        self.history_file = self.storage_dir / "history.json"
        
        # 内存缓存
        self._rules: Dict[str, AlertRule] = {}
        self._history: Dict[str, AlertHistory] = {}
        self._active_alerts: Dict[str, AlertHistory] = {}  # rule_id -> alert
        
        # 规则触发时间记录（用于计算持续时间）
        self._trigger_times: Dict[str, datetime] = {}
        
        # 最后通知时间（用于静默期）
        self._last_notification: Dict[str, datetime] = {}
        
        # 加载数据
        self._load_data()
        
        # 订阅系统指标事件
        self._subscribe_events()
    
    def _subscribe_events(self):
        """订阅系统指标事件"""
        event_bus = EventBus()
        event_bus.subscribe(
            callback=self._handle_metric_event,
            filter_types=[EventType.METRIC_CPU, EventType.METRIC_MEMORY, 
                         EventType.METRIC_DISK, EventType.METRIC_NETWORK]
        )
    
    def _handle_metric_event(self, event: Event):
        """处理指标事件"""
        metric_map = {
            EventType.METRIC_CPU: MetricType.CPU,
            EventType.METRIC_MEMORY: MetricType.MEMORY,
            EventType.METRIC_DISK: MetricType.DISK,
            EventType.METRIC_NETWORK: MetricType.NETWORK,
        }
        
        metric_type = metric_map.get(event.type)
        if metric_type:
            value = event.data.get("value", 0)
            self.check_alerts(metric_type, value)
    
    def _load_data(self):
        """从文件加载数据"""
        # 加载规则
        if self.rules_file.exists():
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    rules_data = json.load(f)
                    for rule_dict in rules_data:
                        rule = AlertRule(**rule_dict)
                        self._rules[rule.id] = rule
            except Exception as e:
                print(f"加载告警规则失败: {e}")
        
        # 加载历史（最近 1000 条）
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    # 只保留最近 1000 条
                    history_data = history_data[-1000:]
                    for alert_dict in history_data:
                        alert = AlertHistory(**alert_dict)
                        self._history[alert.id] = alert
                        # 恢复活动告警状态
                        if alert.status == AlertStatus.TRIGGERED:
                            self._active_alerts[alert.rule_id] = alert
            except Exception as e:
                print(f"加载告警历史失败: {e}")
    
    def _save_rules(self):
        """保存规则到文件"""
        try:
            with open(self.rules_file, "w", encoding="utf-8") as f:
                json.dump(
                    [rule.dict() for rule in self._rules.values()],
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str
                )
        except Exception as e:
            print(f"保存告警规则失败: {e}")
    
    def _save_history(self):
        """保存历史到文件"""
        try:
            # 只保留最近 1000 条
            history_list = list(self._history.values())[-1000:]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(
                    [alert.dict() for alert in history_list],
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str
                )
        except Exception as e:
            print(f"保存告警历史失败: {e}")
    
    # ==================== 规则管理 ====================
    
    def create_rule(self, rule_data: Dict[str, Any]) -> AlertRule:
        """创建告警规则"""
        rule_id = f"rule-{uuid.uuid4().hex[:8]}"
        
        rule = AlertRule(
            id=rule_id,
            created_at=datetime.utcnow(),
            **rule_data
        )
        
        self._rules[rule_id] = rule
        self._save_rules()
        
        return rule
    
    def update_rule(self, rule_id: str, update_data: Dict[str, Any]) -> Optional[AlertRule]:
        """更新告警规则"""
        if rule_id not in self._rules:
            return None
        
        rule = self._rules[rule_id]
        
        # 更新字段
        for key, value in update_data.items():
            if value is not None and hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.utcnow()
        
        self._save_rules()
        return rule
    
    def delete_rule(self, rule_id: str) -> bool:
        """删除告警规则"""
        if rule_id not in self._rules:
            return False
        
        del self._rules[rule_id]
        self._save_rules()
        return True
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """获取单个规则"""
        return self._rules.get(rule_id)
    
    def list_rules(
        self,
        enabled_only: bool = False,
        metric: Optional[MetricType] = None,
        level: Optional[AlertLevel] = None
    ) -> List[AlertRule]:
        """列出告警规则"""
        rules = list(self._rules.values())
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        if metric:
            rules = [r for r in rules if r.metric == metric]
        
        if level:
            rules = [r for r in rules if r.level == level]
        
        # 按创建时间倒序
        rules.sort(key=lambda r: r.created_at, reverse=True)
        
        return rules
    
    # ==================== 告警检查 ====================
    
    def check_alerts(self, metric: MetricType, actual_value: float):
        """检查告警条件"""
        # 获取该指标的所有启用规则
        rules = self.list_rules(enabled_only=True, metric=metric)
        
        for rule in rules:
            self._check_rule(rule, actual_value)
    
    def _check_rule(self, rule: AlertRule, actual_value: float):
        """检查单个规则"""
        rule_id = rule.id
        
        # 计算条件是否满足
        condition_met = self._evaluate_condition(
            rule.comparison, actual_value, rule.threshold
        )
        
        # 获取当前告警状态
        current_alert = self._active_alerts.get(rule_id)
        
        if condition_met:
            # 条件满足，检查是否需要触发告警
            if current_alert is None:
                # 新触发
                self._trigger_alert(rule, actual_value)
            else:
                # 已触发，更新持续时间
                current_alert.actual_value = actual_value
        else:
            # 条件不满足，检查是否需要恢复
            if current_alert is not None:
                self._recover_alert(rule_id)
    
    def _evaluate_condition(
        self, 
        comparison: ComparisonOp, 
        actual: float, 
        threshold: float
    ) -> bool:
        """评估条件"""
        if comparison == ComparisonOp.GT:
            return actual > threshold
        elif comparison == ComparisonOp.GTE:
            return actual >= threshold
        elif comparison == ComparisonOp.LT:
            return actual < threshold
        elif comparison == ComparisonOp.LTE:
            return actual <= threshold
        elif comparison == ComparisonOp.EQ:
            return abs(actual - threshold) < 0.001
        return False
    
    def _trigger_alert(self, rule: AlertRule, actual_value: float):
        """触发告警"""
        rule_id = rule.id
        
        # 检查持续时间
        now = datetime.utcnow()
        if rule_id in self._trigger_times:
            trigger_time = self._trigger_times[rule_id]
            duration_minutes = (now - trigger_time).total_seconds() / 60
            
            if duration_minutes < rule.duration:
                # 持续时间不足，等待
                return
        else:
            # 首次触发，记录时间
            self._trigger_times[rule_id] = now
            return
        
        # 创建告警记录
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"
        
        message = self._generate_alert_message(rule, actual_value)
        
        alert = AlertHistory(
            id=alert_id,
            rule_id=rule_id,
            rule_name=rule.name,
            level=rule.level,
            status=AlertStatus.TRIGGERED,
            metric=rule.metric,
            threshold=rule.threshold,
            actual_value=actual_value,
            message=message,
            triggered_at=now,
            notifications_sent=[]
        )
        
        self._history[alert_id] = alert
        self._active_alerts[rule_id] = alert
        self._save_history()
        
        # 发送通知
        asyncio.create_task(self._send_notifications(rule, alert))
        
        # 发布事件
        EventBus().publish(EventType.ALERT_TRIGGERED, {
            "alert_id": alert_id,
            "rule_id": rule_id,
            "rule_name": rule.name,
            "level": rule.level,
            "message": message,
            "value": actual_value
        })
        
        print(f"告警触发: {rule.name} - {message}")
    
    def _recover_alert(self, rule_id: str):
        """恢复告警"""
        alert = self._active_alerts.get(rule_id)
        if alert is None:
            return
        
        now = datetime.utcnow()
        
        alert.status = AlertStatus.RECOVERED
        alert.recovered_at = now
        alert.duration_minutes = int(
            (now - alert.triggered_at).total_seconds() / 60
        )
        
        # 从活动告警中移除
        del self._active_alerts[rule_id]
        if rule_id in self._trigger_times:
            del self._trigger_times[rule_id]
        
        self._save_history()
        
        # 发布恢复事件
        EventBus().publish(EventType.ALERT_RECOVERED, {
            "alert_id": alert.id,
            "rule_id": rule_id,
            "rule_name": alert.rule_name,
            "duration": alert.duration_minutes
        })
        
        print(f"告警恢复: {alert.rule_name}")
    
    def _generate_alert_message(self, rule: AlertRule, actual_value: float) -> str:
        """生成告警消息"""
        op_map = {
            ComparisonOp.GT: "超过",
            ComparisonOp.GTE: "大于等于",
            ComparisonOp.LT: "低于",
            ComparisonOp.LTE: "小于等于",
            ComparisonOp.EQ: "等于",
        }
        
        metric_names = {
            MetricType.CPU: "CPU 使用率",
            MetricType.MEMORY: "内存使用率",
            MetricType.DISK: "磁盘使用率",
            MetricType.NETWORK: "网络流量",
            MetricType.PROCESS: "进程数",
            MetricType.LOAD: "系统负载",
            MetricType.CUSTOM: "自定义指标",
        }
        
        op_str = op_map.get(rule.comparison, "超过")
        metric_name = metric_names.get(rule.metric, rule.metric.value)
        
        return f"{metric_name} {op_str} 阈值 {rule.threshold}%，当前值 {actual_value:.1f}%"
    
    # ==================== 通知发送 ====================
    
    async def _send_notifications(self, rule: AlertRule, alert: AlertHistory):
        """发送通知"""
        for channel in rule.channels:
            # 检查静默期
            if not self._should_send_notification(rule_id, channel):
                continue
            
            try:
                if channel == NotificationChannel.BROWSER:
                    await self._send_browser_notification(rule, alert)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(rule, alert)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook_notification(rule, alert)
                
                # 记录通知发送
                alert.notifications_sent.append({
                    "channel": channel.value,
                    "sent_at": datetime.utcnow().isoformat(),
                    "status": "success"
                })
                
                # 更新最后通知时间
                self._last_notification[f"{rule.id}:{channel.value}"] = datetime.utcnow()
                
            except Exception as e:
                print(f"发送通知失败 [{channel.value}]: {e}")
                alert.notifications_sent.append({
                    "channel": channel.value,
                    "sent_at": datetime.utcnow().isoformat(),
                    "status": "failed",
                    "error": str(e)
                })
        
        self._save_history()
    
    def _should_send_notification(self, rule_id: str, channel: NotificationChannel) -> bool:
        """检查是否应该发送通知（静默期检查）"""
        key = f"{rule_id}:{channel.value}"
        last_time = self._last_notification.get(key)
        
        if last_time is None:
            return True
        
        # 获取规则静默期
        rule = self._rules.get(rule_id)
        if rule is None:
            return True
        
        silence_minutes = rule.silence_duration
        elapsed = (datetime.utcnow() - last_time).total_seconds() / 60
        
        return elapsed >= silence_minutes
    
    async def _send_browser_notification(self, rule: AlertRule, alert: AlertHistory):
        """发送浏览器推送通知"""
        # 通过 WebSocket 推送到前端
        EventBus().publish(EventType.NOTIFICATION_BROWSER, {
            "title": f"【{rule.level.value.upper()}】{rule.name}",
            "body": alert.message,
            "alert_id": alert.id,
            "level": rule.level.value
        })
    
    async def _send_email_notification(self, rule: AlertRule, alert: AlertHistory):
        """发送邮件通知"""
        if not rule.email_recipients:
            return
        
        # 调用邮件服务
        email_service = get_email_service()
        
        alert_data = {
            "title": f"【{rule.level.value.upper()}】{rule.name}",
            "level": rule.level.value,
            "message": alert.message,
            "rule_name": rule.name,
            "metric": rule.metric.value,
            "actual_value": alert.actual_value,
            "threshold": alert.threshold,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else "",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        subject = f"【{rule.level.value.upper()}】{rule.name} - YL-Monitor告警"
        
        await email_service.send_alert_email(
            recipients=rule.email_recipients,
            subject=subject,
            alert_data=alert_data
        )
    
    async def _send_webhook_notification(self, rule: AlertRule, alert: AlertHistory):
        """发送 Webhook 通知"""
        if not rule.webhook_url:
            return
        
        # 调用 Webhook 服务
        webhook_service = get_webhook_service()
        
        alert_data = {
            "alert_id": alert.id,
            "rule_id": rule.id,
            "rule_name": rule.name,
            "level": rule.level.value,
            "status": alert.status.value,
            "metric": rule.metric.value,
            "threshold": rule.threshold,
            "actual_value": alert.actual_value,
            "message": alert.message,
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else "",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await webhook_service.send_alert_webhook(
            webhook_url=rule.webhook_url,
            alert_data=alert_data
        )
    
    # ==================== 告警历史 ====================
    
    def get_alert_history(
        self,
        rule_id: Optional[str] = None,
        status: Optional[AlertStatus] = None,
        level: Optional[AlertLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertHistory]:
        """获取告警历史"""
        alerts = list(self._history.values())
        
        # 过滤
        if rule_id:
            alerts = [a for a in alerts if a.rule_id == rule_id]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if start_time:
            alerts = [a for a in alerts if a.triggered_at >= start_time]
        
        if end_time:
            alerts = [a for a in alerts if a.triggered_at <= end_time]
        
        # 按时间倒序
        alerts.sort(key=lambda a: a.triggered_at, reverse=True)
        
        # 分页
        return alerts[offset:offset + limit]
    
    def get_active_alerts(self) -> List[AlertHistory]:
        """获取当前活动告警"""
        return list(self._active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str, user: str) -> Optional[AlertHistory]:
        """确认告警"""
        alert = self._history.get(alert_id)
        if alert is None:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user
        
        self._save_history()
        return alert
    
    def get_stats(self) -> Dict[str, int]:
        """获取告警统计"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total = len(self._history)
        triggered_today = sum(
            1 for a in self._history.values()
            if a.triggered_at >= today_start
        )
        active = len(self._active_alerts)
        recovered_today = sum(
            1 for a in self._history.values()
            if a.recovered_at and a.recovered_at >= today_start
        )
        
        return {
            "total_alerts": total,
            "triggered_today": triggered_today,
            "active_alerts": active,
            "recovered_today": recovered_today
        }
    
    def test_notification(
        self, 
        channel: NotificationChannel, 
        email: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> bool:
        """测试通知渠道"""
        test_alert = AlertHistory(
            id="test",
            rule_id="test",
            rule_name="测试告警",
            level=AlertLevel.INFO,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="这是一条测试告警消息",
            triggered_at=datetime.utcnow(),
            notifications_sent=[]
        )
        
        test_rule = AlertRule(
            id="test",
            name="测试规则",
            metric=MetricType.CPU,
            comparison=ComparisonOp.GT,
            threshold=80.0,
            duration=5,
            level=AlertLevel.INFO,
            channels=[channel],
            email_recipients=[email] if email else [],
            webhook_url=webhook_url or ""
        )
        
        try:
            asyncio.create_task(self._send_notifications(test_rule, test_alert))
            return True
        except Exception as e:
            print(f"测试通知失败: {e}")
            return False


# 全局实例
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """获取告警服务实例"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
