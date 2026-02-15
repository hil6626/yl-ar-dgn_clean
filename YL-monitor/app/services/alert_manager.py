#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理器
提供告警规则管理、触发、通知等功能
"""

import os
import yaml
import asyncio
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger('AlertManager')


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    level: AlertLevel
    condition: str  # 条件表达式
    duration: int  # 持续时间（秒）
    enabled: bool = True
    channels: List[str] = field(default_factory=list)
    cooldown: int = 300  # 冷却时间（秒）
    
    # 运行时状态
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class Alert:
    """告警实例"""
    alert_id: str
    rule_id: str
    title: str
    message: str
    level: AlertLevel
    status: AlertStatus
    source: str  # 告警来源
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class AlertManager:
    """
    告警管理器
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        
        self.config_path = config_path or self._find_config()
        self.notification_channels: Dict[str, Callable] = {}
        
        # 加载配置
        self._load_config()
        self._setup_channels()
        
    def _find_config(self) -> Optional[str]:
        """查找配置文件"""
        possible_paths = [
            Path(__file__).parent.parent / 'config' / 'alert_rules.yaml',
            Path.cwd() / 'config' / 'alert_rules.yaml',
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None
    
    def _load_config(self):
        """加载告警规则配置"""
        config_file = self.config_path
        if not config_file or not Path(config_file).exists():
            logger.warning("未找到告警规则配置，使用默认规则")
            self._create_default_rules()
            return
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            for rule_config in config.get('rules', []):
                rule = AlertRule(
                    rule_id=rule_config['rule_id'],
                    name=rule_config['name'],
                    description=rule_config.get('description', ''),
                    level=AlertLevel(rule_config['level']),
                    condition=rule_config['condition'],
                    duration=rule_config.get('duration', 60),
                    enabled=rule_config.get('enabled', True),
                    channels=rule_config.get('channels', ['log']),
                    cooldown=rule_config.get('cooldown', 300)
                )
                self.rules[rule.rule_id] = rule
                logger.info(f"加载告警规则: {rule.rule_id}")
                
        except Exception as e:
            logger.error(f"加载告警配置失败: {e}")
            self._create_default_rules()
    
    def _create_default_rules(self):
        """创建默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id='node_offline',
                name='节点离线',
                description='节点连续多次健康检查失败',
                level=AlertLevel.ERROR,
                condition='status == "offline"',
                duration=0,
                channels=['log', 'webhook']
            ),
            AlertRule(
                rule_id='high_cpu',
                name='CPU使用率过高',
                description='节点CPU使用率超过80%',
                level=AlertLevel.WARNING,
                condition='cpu_percent > 80',
                duration=300,
                channels=['log']
            ),
            AlertRule(
                rule_id='high_memory',
                name='内存使用率过高',
                description='节点内存使用率超过85%',
                level=AlertLevel.WARNING,
                condition='memory_percent > 85',
                duration=300,
                channels=['log']
            ),
            AlertRule(
                rule_id='service_unavailable',
                name='服务不可用',
                description='关键服务无法访问',
                level=AlertLevel.CRITICAL,
                condition='health_check_failed',
                duration=0,
                channels=['log', 'webhook', 'email']
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
        
        # 保存默认配置
        if self.config_path:
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            config_path = self.config_path
            if not config_path:
                return
                
            config = {
                'rules': [
                    {
                        'rule_id': r.rule_id,
                        'name': r.name,
                        'description': r.description,
                        'level': r.level.value,
                        'condition': r.condition,
                        'duration': r.duration,
                        'enabled': r.enabled,
                        'channels': r.channels,
                        'cooldown': r.cooldown
                    }
                    for r in self.rules.values()
                ]
            }
            
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False,
                          allow_unicode=True)
                
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def _setup_channels(self):
        """设置通知渠道"""
        self.notification_channels = {
            'log': self._send_log_notification,
            'webhook': self._send_webhook_notification,
            'email': self._send_email_notification
        }
    
    def _send_log_notification(self, alert: Alert):
        """日志通知"""
        level_map = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        
        logger.log(
            level_map.get(alert.level, logging.INFO),
            f"[ALERT] {alert.title}: {alert.message}"
        )
    
    def _send_webhook_notification(self, alert: Alert):
        """Webhook通知"""
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("未配置Webhook URL")
            return
            
        try:
            payload = {
                'alert_id': alert.alert_id,
                'title': alert.title,
                'message': alert.message,
                'level': alert.level.value,
                'source': alert.source,
                'timestamp': alert.created_at.isoformat()
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook通知发送成功: {alert.alert_id}")
            else:
                logger.warning(f"Webhook通知失败: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Webhook通知异常: {e}")
    
    def _send_email_notification(self, alert: Alert):
        """邮件通知"""
        smtp_server = os.getenv('ALERT_SMTP_SERVER')
        smtp_port = int(os.getenv('ALERT_SMTP_PORT', 587))
        username = os.getenv('ALERT_SMTP_USERNAME')
        password = os.getenv('ALERT_SMTP_PASSWORD')
        to_addresses_str = os.getenv('ALERT_EMAIL_TO', '')
        to_addresses = (to_addresses_str.split(',')
                        if to_addresses_str else [])

        if not all([smtp_server, username, password, to_addresses]):
            logger.warning("邮件配置不完整")
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
            
            body = f"""
告警详情:

告警ID: {alert.alert_id}
标题: {alert.title}
级别: {alert.level.value}
来源: {alert.source}
时间: {alert.created_at}

详情:
{alert.message}
"""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件通知发送成功: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"邮件通知异常: {e}")
    
    async def evaluate_rules(self, node_id: str, node_data: dict):
        """评估告警规则"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # 检查冷却时间
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(
                    seconds=rule.cooldown)
                if datetime.utcnow() < cooldown_end:
                    continue
            
            # 评估条件
            try:
                if self._evaluate_condition(rule.condition, node_data):
                    await self._trigger_alert(rule, node_id, node_data)
            except Exception as e:
                logger.error(f"评估规则 {rule.rule_id} 失败: {e}")
    
    def _evaluate_condition(self, condition: str, data: dict) -> bool:
        """评估条件表达式"""
        # 简单的条件评估
        try:
            # 支持的条件格式:
            # - status == "offline"
            # - cpu_percent > 80
            # - memory_percent > 85
            
            if '==' in condition:
                key, value = condition.split('==')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                return str(data.get(key)) == value
            
            elif '>' in condition:
                key, value = condition.split('>')
                key = key.strip()
                value = float(value.strip())
                return float(data.get(key, 0)) > value
            
            elif '<' in condition:
                key, value = condition.split('<')
                key = key.strip()
                value = float(value.strip())
                return float(data.get(key, 0)) < value
            
            else:
                # 特殊条件
                if condition == 'health_check_failed':
                    return data.get('consecutive_fails', 0) > 0
                
        except Exception as e:
            logger.error(f"条件评估错误: {e}")
            return False
        
        return False
    
    async def _trigger_alert(self, rule: AlertRule, node_id: str,
                             node_data: dict):
        """触发告警"""
        alert_id = (f"{rule.rule_id}-{node_id}-"
                    f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        
        # 检查是否已存在相同告警
        existing_key = f"{rule.rule_id}-{node_id}"
        if existing_key in self.active_alerts:
            logger.debug(f"告警已存在: {existing_key}")
            return
        
        # 创建告警
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            title=f"{rule.name} - {node_id}",
            message=rule.description,
            level=rule.level,
            status=AlertStatus.ACTIVE,
            source=node_id,
            created_at=datetime.utcnow(),
            metadata={
                'node_data': node_data,
                'rule_data': {
                    'condition': rule.condition,
                    'duration': rule.duration
                }
            }
        )
        
        self.active_alerts[existing_key] = alert
        self.alert_history.append(alert)
        
        # 限制历史记录
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # 更新规则统计
        rule.last_triggered = datetime.utcnow()
        rule.trigger_count += 1
        
        # 发送通知
        for channel in rule.channels:
            handler = self.notification_channels.get(channel)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error(f"通知发送失败 ({channel}): {e}")
        
        logger.warning(f"告警触发: {alert.title} ({alert.level.value})")
        
        # 广播WebSocket
        try:
            from app.ws.ar_ws import ws_manager
            if ws_manager:
                await ws_manager.broadcast_alert({
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'message': alert.message,
                    'level': alert.level.value,
                    'timestamp': alert.created_at.isoformat()
                })
        except ImportError:
            logger.debug("WebSocket模块未安装，跳过广播")
        except Exception as e:
            logger.error(f"WebSocket广播失败: {e}")
    
    def acknowledge_alert(self, alert_key: str, user: str) -> bool:
        """确认告警"""
        if alert_key not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_key]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user
        
        logger.info(f"告警已确认: {alert.alert_id} by {user}")
        return True
    
    def resolve_alert(self, alert_key: str) -> bool:
        """解决告警"""
        if alert_key not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_key]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        # 从活动告警中移除
        del self.active_alerts[alert_key]
        
        logger.info(f"告警已解决: {alert.alert_id}")
        return True
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None
                          ) -> List[Alert]:
        """获取活动告警"""
        alerts = list(self.active_alerts.values())
        if level:
            alerts = [a for a in alerts if a.level == level]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def get_alert_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AlertLevel] = None
    ) -> List[Alert]:
        """获取告警历史"""
        alerts = self.alert_history
        
        if start_time:
            alerts = [a for a in alerts if a.created_at >= start_time]
        if end_time:
            alerts = [a for a in alerts if a.created_at <= end_time]
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def get_alert_stats(self) -> dict:
        """获取告警统计"""
        total = len(self.alert_history)
        active = len(self.active_alerts)
        
        by_level = {
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        
        for alert in self.alert_history:
            by_level[alert.level.value] += 1
        
        return {
            'total': total,
            'active': active,
            'by_level': by_level,
            'acknowledged': len([
                a for a in self.alert_history
                if a.status == AlertStatus.ACKNOWLEDGED
            ]),
            'resolved': len([
                a for a in self.alert_history
                if a.status == AlertStatus.RESOLVED
            ])
        }
