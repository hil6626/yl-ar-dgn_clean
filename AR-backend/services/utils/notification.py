#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化通知服务 - 多渠道通知机制
AR 综合实时合成与监控系统

功能:
- 邮件通知
- Webhook通知
- 短信通知 (扩展)
- 通知模板管理
- 通知历史记录

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-09
"""

import time
import json
import logging
import smtplib
import requests
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union
from pathlib import Path
import uuid

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道枚举"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"
    CONSOLE = "console"


class NotificationTemplate:
    """通知模板类"""

    def __init__(self, template_id: str, name: str, channel: NotificationChannel,
                 subject_template: str, body_template: str, description: str = ""):
        """
        初始化通知模板

        Args:
            template_id: 模板ID
            name: 模板名称
            channel: 通知渠道
            subject_template: 主题模板
            body_template: 正文模板
            description: 模板描述
        """
        self.template_id = template_id
        self.name = name
        self.channel = channel
        self.subject_template = subject_template
        self.body_template = body_template
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def render_subject(self, context: Dict[str, Any]) -> str:
        """
        渲染主题

        Args:
            context: 上下文数据

        Returns:
            str: 渲染后的主题
        """
        try:
            return self.subject_template.format(**context)
        except (KeyError, ValueError) as e:
            logger.error(f"主题模板渲染失败: {e}")
            return self.subject_template

    def render_body(self, context: Dict[str, Any]) -> str:
        """
        渲染正文

        Args:
            context: 上下文数据

        Returns:
            str: 渲染后的正文
        """
        try:
            return self.body_template.format(**context)
        except (KeyError, ValueError) as e:
            logger.error(f"正文模板渲染失败: {e}")
            return self.body_template

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "channel": self.channel.value,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class Notification:
    """通知类"""

    def __init__(self, notification_id: str, channel: NotificationChannel,
                 recipient: str, subject: str, body: str,
                 template_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        初始化通知

        Args:
            notification_id: 通知ID
            channel: 通知渠道
            recipient: 接收者
            subject: 主题
            body: 正文
            template_id: 模板ID
            metadata: 额外元数据
        """
        self.notification_id = notification_id
        self.channel = channel
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.template_id = template_id
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.sent_at = None
        self.delivered_at = None
        self.failed_at = None
        self.error_message = None
        self.retry_count = 0
        self.max_retries = 3

    def mark_sent(self) -> None:
        """标记为已发送"""
        self.sent_at = datetime.now()

    def mark_delivered(self) -> None:
        """标记为已送达"""
        self.delivered_at = datetime.now()

    def mark_failed(self, error_message: str) -> None:
        """
        标记为发送失败

        Args:
            error_message: 错误消息
        """
        self.failed_at = datetime.now()
        self.error_message = error_message
        self.retry_count += 1

    def can_retry(self) -> bool:
        """
        是否可以重试

        Returns:
            bool: 是否可以重试
        """
        return self.retry_count < self.max_retries and self.failed_at is not None

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "notification_id": self.notification_id,
            "channel": self.channel.value,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "template_id": self.template_id,
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config: Dict):
        """
        初始化邮件通知器

        Args:
            config: 邮件配置
                - smtp_server: SMTP服务器
                - smtp_port: SMTP端口
                - username: 用户名
                - password: 密码
                - from_email: 发件人邮箱
                - use_tls: 是否使用TLS
        """
        self.config = config
        self.server = None

    def connect(self) -> bool:
        """
        连接到SMTP服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            self.server = smtplib.SMTP(
                self.config['smtp_server'],
                self.config['smtp_port']
            )

            if self.config.get('use_tls', True):
                self.server.starttls()

            if self.config.get('username') and self.config.get('password'):
                self.server.login(
                    self.config['username'],
                    self.config['password']
                )

            logger.info("邮件服务器连接成功")
            return True

        except Exception as e:
            logger.error(f"邮件服务器连接失败: {e}")
            return False

    def disconnect(self) -> None:
        """断开连接"""
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass
            self.server = None

    def send(self, notification: Notification) -> bool:
        """
        发送邮件通知

        Args:
            notification: 通知对象

        Returns:
            bool: 发送是否成功
        """
        try:
            if not self.server:
                if not self.connect():
                    return False

            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.config['from_email']
            msg['To'] = notification.recipient
            msg['Subject'] = notification.subject

            # 添加正文
            body_part = MIMEText(notification.body, 'html', 'utf-8')
            msg.attach(body_part)

            # 发送邮件
            self.server.sendmail(
                self.config['from_email'],
                notification.recipient,
                msg.as_string()
            )

            logger.info(f"邮件发送成功: {notification.recipient}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False


class WebhookNotifier:
    """Webhook通知器"""

    def __init__(self, config: Dict):
        """
        初始化Webhook通知器

        Args:
            config: Webhook配置
                - url: Webhook URL
                - method: HTTP方法 (POST, GET等)
                - headers: 请求头
                - timeout: 超时时间
        """
        self.config = config

    def send(self, notification: Notification) -> bool:
        """
        发送Webhook通知

        Args:
            notification: 通知对象

        Returns:
            bool: 发送是否成功
        """
        try:
            url = self.config['url']
            method = self.config.get('method', 'POST')
            headers = self.config.get('headers', {'Content-Type': 'application/json'})
            timeout = self.config.get('timeout', 10)

            # 构建请求数据
            data = {
                "notification_id": notification.notification_id,
                "channel": notification.channel.value,
                "subject": notification.subject,
                "body": notification.body,
                "recipient": notification.recipient,
                "timestamp": notification.created_at.isoformat(),
                "metadata": notification.metadata
            }

            # 发送请求
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=timeout
            )

            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook发送成功: {url}")
                return True
            else:
                logger.error(f"Webhook发送失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Webhook发送异常: {e}")
            return False


class ConsoleNotifier:
    """控制台通知器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化控制台通知器

        Args:
            config: 配置参数
        """
        self.config = config or {}

    def send(self, notification: Notification) -> bool:
        """
        发送控制台通知

        Args:
            notification: 通知对象

        Returns:
            bool: 发送是否成功
        """
        try:
            print(f"\n=== 通知 ({notification.channel.value.upper()}) ===")
            print(f"收件人: {notification.recipient}")
            print(f"主题: {notification.subject}")
            print(f"内容: {notification.body}")
            print(f"时间: {notification.created_at}")
            print("=" * 50)

            return True

        except Exception as e:
            logger.error(f"控制台通知失败: {e}")
            return False


class NotificationService:
    """
    自动化通知服务主类

    提供完整的通知功能:
    - 多渠道通知支持
    - 通知模板管理
    - 通知历史记录
    - 异步发送支持
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化通知服务

        Args:
            config: 配置参数
                - max_history: 最大历史记录数
                - enable_persistence: 是否启用持久化
                - history_file: 历史记录文件路径
                - channels: 各渠道配置
        """
        self.config = {
            'max_history': 1000,
            'enable_persistence': True,
            'history_file': str(Path(__file__).parent.parent.parent / 'logs' / 'notification_history.log'),
            'channels': {
                'email': {},
                'webhook': {},
                'sms': {},
                'console': {}
            }
        }
        if config:
            self._merge_config(config)

        # 模板管理
        self.templates: Dict[str, NotificationTemplate] = {}
        self.template_lock = threading.Lock()

        # 通知器管理
        self.notifiers: Dict[NotificationChannel, Any] = {}
        self.notifier_lock = threading.Lock()

        # 通知历史
        self.notification_history: List[Notification] = []
        self.history_lock = threading.Lock()

        # 发送队列
        self.send_queue: List[Notification] = []
        self.queue_lock = threading.Lock()

        # 发送线程
        self.send_thread: Optional[threading.Thread] = None
        self.sending = False

        # 统计信息
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'by_channel': {channel.value: 0 for channel in NotificationChannel}
        }

        # 初始化默认模板
        self._init_default_templates()

        # 初始化通知器
        self._init_notifiers()

        # 加载历史记录
        self._load_history()

    def _merge_config(self, config: Dict) -> None:
        """合并配置"""
        for key, value in config.items():
            if isinstance(value, dict) and key in self.config:
                self.config[key].update(value)
            else:
                self.config[key] = value

    def _init_default_templates(self) -> None:
        """初始化默认通知模板"""
        default_templates = [
            # 告警通知模板
            NotificationTemplate(
                "alert_email",
                "告警邮件通知",
                NotificationChannel.EMAIL,
                "AR系统告警: {alert_level} - {alert_name}",
                """
                <html>
                <body>
                    <h2>AR系统告警通知</h2>
                    <p><strong>告警级别:</strong> {alert_level}</p>
                    <p><strong>告警名称:</strong> {alert_name}</p>
                    <p><strong>告警消息:</strong> {alert_message}</p>
                    <p><strong>触发时间:</strong> {alert_time}</p>
                    <p><strong>当前值:</strong> {current_value}</p>
                    <hr>
                    <p>此邮件由AR系统自动发送，请勿回复。</p>
                </body>
                </html>
                """,
                "系统告警邮件通知模板"
            ),

            NotificationTemplate(
                "alert_webhook",
                "告警Webhook通知",
                NotificationChannel.WEBHOOK,
                "",
                "",
                "系统告警Webhook通知模板"
            ),

            # 部署进度通知模板
            NotificationTemplate(
                "progress_email",
                "部署进度邮件通知",
                NotificationChannel.EMAIL,
                "AR系统部署进度: {task_name}",
                """
                <html>
                <body>
                    <h2>AR系统部署进度通知</h2>
                    <p><strong>任务名称:</strong> {task_name}</p>
                    <p><strong>当前进度:</strong> {progress}%</p>
                    <p><strong>状态:</strong> {status}</p>
                    <p><strong>消息:</strong> {message}</p>
                    <p><strong>更新时间:</strong> {update_time}</p>
                    <hr>
                    <p>此邮件由AR系统自动发送，请勿回复。</p>
                </body>
                </html>
                """,
                "部署进度邮件通知模板"
            ),

            # 系统状态通知模板
            NotificationTemplate(
                "system_status",
                "系统状态通知",
                NotificationChannel.EMAIL,
                "AR系统状态报告",
                """
                <html>
                <body>
                    <h2>AR系统状态报告</h2>
                    <p><strong>报告时间:</strong> {report_time}</p>
                    <p><strong>系统状态:</strong> {system_status}</p>
                    <p><strong>活跃任务:</strong> {active_tasks}</p>
                    <p><strong>CPU使用率:</strong> {cpu_usage}%</p>
                    <p><strong>内存使用率:</strong> {memory_usage}%</p>
                    <hr>
                    <p>此邮件由AR系统自动发送，请勿回复。</p>
                </body>
                </html>
                """,
                "系统状态报告模板"
            )
        ]

        for template in default_templates:
            self.add_template(template)

    def _init_notifiers(self) -> None:
        """初始化通知器"""
        channel_configs = self.config.get('channels', {})

        # 邮件通知器
        if channel_configs.get('email'):
            self.notifiers[NotificationChannel.EMAIL] = EmailNotifier(
                channel_configs['email']
            )

        # Webhook通知器
        if channel_configs.get('webhook'):
            self.notifiers[NotificationChannel.WEBHOOK] = WebhookNotifier(
                channel_configs['webhook']
            )

        # 控制台通知器 (默认启用)
        self.notifiers[NotificationChannel.CONSOLE] = ConsoleNotifier()

    def add_template(self, template: NotificationTemplate) -> None:
        """
        添加通知模板

        Args:
            template: 通知模板
        """
        with self.template_lock:
            self.templates[template.template_id] = template
            logger.info(f"通知模板已添加: {template.name}")

    def remove_template(self, template_id: str) -> bool:
        """
        移除通知模板

        Args:
            template_id: 模板ID

        Returns:
            bool: 是否成功移除
        """
        with self.template_lock:
            if template_id in self.templates:
                del self.templates[template_id]
                logger.info(f"通知模板已移除: {template_id}")
                return True
            return False

    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """
        获取通知模板

        Args:
            template_id: 模板ID

        Returns:
            Optional[NotificationTemplate]: 通知模板
        """
        with self.template_lock:
            return self.templates.get(template_id)

    def send_notification(self, channel: NotificationChannel, recipient: str,
                         subject: str, body: str, template_id: Optional[str] = None,
                         metadata: Optional[Dict] = None) -> str:
        """
        发送通知

        Args:
            channel: 通知渠道
            recipient: 接收者
            subject: 主题
            body: 正文
            template_id: 模板ID
            metadata: 额外元数据

        Returns:
            str: 通知ID
        """
        notification_id = str(uuid.uuid4())
        notification = Notification(
            notification_id, channel, recipient, subject, body,
            template_id, metadata
        )

        # 添加到发送队列
        with self.queue_lock:
            self.send_queue.append(notification)

        logger.info(f"通知已添加到发送队列: {notification_id}")

        # 启动发送线程（如果未启动）
        if not self.sending:
            self.start_sending()

        return notification_id

    def send_notification_from_template(self, template_id: str, recipient: str,
                                      context: Dict[str, Any]) -> Optional[str]:
        """
        使用模板发送通知

        Args:
            template_id: 模板ID
            recipient: 接收者
            context: 模板上下文

        Returns:
            Optional[str]: 通知ID，失败返回None
        """
        template = self.get_template(template_id)
        if not template:
            logger.error(f"通知模板不存在: {template_id}")
            return None

        subject = template.render_subject(context)
        body = template.render_body(context)

        return self.send_notification(
            template.channel, recipient, subject, body, template_id, context
        )

    def start_sending(self) -> None:
        """启动发送线程"""
        if self.sending:
            return

        self.sending = True
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        logger.info("通知发送服务已启动")

    def stop_sending(self) -> None:
        """停止发送线程"""
        self.sending = False
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=5)
        logger.info("通知发送服务已停止")

    def _send_loop(self) -> None:
        """发送主循环"""
        while self.sending:
            try:
                notification = None

                # 获取待发送通知
                with self.queue_lock:
                    if self.send_queue:
                        notification = self.send_queue.pop(0)

                if notification:
                    self._send_single_notification(notification)
                else:
                    time.sleep(1)  # 队列为空时等待

            except Exception as e:
                logger.error(f"发送循环错误: {e}")
                time.sleep(5)

    def _send_single_notification(self, notification: Notification) -> None:
        """
        发送单个通知

        Args:
            notification: 通知对象
        """
        try:
            # 获取对应的通知器
            notifier = self.notifiers.get(notification.channel)
            if not notifier:
                logger.error(f"未找到通知器: {notification.channel.value}")
                notification.mark_failed("未找到通知器")
                return

            # 发送通知
            notification.mark_sent()

            if notifier.send(notification):
                notification.mark_delivered()
                self.stats['total_sent'] += 1
                self.stats['by_channel'][notification.channel.value] += 1
                logger.info(f"通知发送成功: {notification.notification_id}")
            else:
                notification.mark_failed("发送失败")
                self.stats['total_failed'] += 1

                # 如果可以重试，重新加入队列
                if notification.can_retry():
                    with self.queue_lock:
                        self.send_queue.insert(0, notification)
                    logger.info(f"通知将重试: {notification.notification_id}")

        except Exception as e:
            logger.error(f"发送通知异常: {e}")
            notification.mark_failed(str(e))
            self.stats['total_failed'] += 1

        finally:
            # 添加到历史记录
            with self.history_lock:
                self.notification_history.append(notification)

                # 限制历史记录数量
                max_history = self.config['max_history']
                if len(self.notification_history) > max_history:
                    self.notification_history = self.notification_history[-max_history:]

            # 持久化存储
            if self.config['enable_persistence']:
                self._persist_notification(notification)

    def get_notification_history(self, limit: int = 100) -> List[Notification]:
        """
        获取通知历史

        Args:
            limit: 最大返回数量

        Returns:
            List[Notification]: 通知历史列表
        """
        with self.history_lock:
            return self.notification_history[-limit:] if self.notification_history else []

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计数据
        """
        with self.queue_lock:
            stats = self.stats.copy()
            stats['queue_size'] = len(self.send_queue)
        return stats

    def _persist_notification(self, notification: Notification) -> None:
        """
        持久化存储通知

        Args:
            notification: 要存储的通知
        """
        try:
            history_file = self.config['history_file']

            # 确保目录存在
            Path(history_file).parent.mkdir(parents=True, exist_ok=True)

            # 追加写入
            with open(history_file, 'a', encoding='utf-8') as f:
                json.dump(notification.to_dict(), f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            logger.error(f"通知持久化失败: {e}")

    def _load_history(self) -> None:
        """加载历史记录"""
        try:
            history_file = self.config['history_file']
            if not Path(history_file).exists():
                return

            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            # 重建通知对象
                            channel = NotificationChannel(data['channel'])
                            notification = Notification(
                                data['notification_id'],
                                channel,
                                data['recipient'],
                                data['subject'],
                                data['body'],
                                data.get('template_id')
                            )
                            notification.metadata = data.get('metadata', {})
                            notification.created_at = datetime.fromisoformat(data['created_at'])

                            if data.get('sent_at'):
                                notification.sent_at = datetime.fromisoformat(data['sent_at'])
                            if data.get('delivered_at'):
                                notification.delivered_at = datetime.fromisoformat(data['delivered_at'])
                            if data.get('failed_at'):
                                notification.failed_at = datetime.fromisoformat(data['failed_at'])

                            notification.error_message = data.get('error_message')
                            notification.retry_count = data.get('retry_count', 0)

                            self.notification_history.append(notification)

                        except (json.JSONDecodeError, KeyError):
                            continue

            logger.info(f"已加载 {len(self.notification_history)} 条通知历史记录")

        except Exception as e:
            logger.error(f"加载通知历史失败: {e}")

    def cleanup(self) -> None:
        """清理资源"""
        self.stop_sending()

        with self.queue_lock:
            self.send_queue.clear()

        with self.history_lock:
            self.notification_history.clear()

        # 断开通知器连接
        for notifier in self.notifiers.values():
            if hasattr(notifier, 'disconnect'):
                notifier.disconnect()

        logger.info("通知服务已清理")


# 全局实例
_notification_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """获取全局通知服务实例"""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    return _notification_service_instance


def send_alert_notification(recipient: str, alert_data: Dict) -> Optional[str]:
    """
    发送告警通知

    Args:
        recipient: 接收者
        alert_data: 告警数据

    Returns:
        Optional[str]: 通知ID
    """
    service = get_notification_service()

    # 构建上下文
    context = {
        'alert_level': alert_data.get('level', 'UNKNOWN'),
        'alert_name': alert_data.get('name', '未知告警'),
        'alert_message': alert_data.get('message', ''),
        'alert_time': alert_data.get('time', datetime.now().isoformat()),
        'current_value': alert_data.get('value', 'N/A')
    }

    # 尝试使用邮件模板
    email_template = service.get_template('alert_email')
    if email_template:
        return service.send_notification_from_template('alert_email', recipient, context)

    # 回退到Webhook
    webhook_template = service.get_template('alert_webhook')
    if webhook_template:
        return service.send_notification_from_template('alert_webhook', recipient, context)

    # 最后回退到控制台
    return service.send_notification(
        NotificationChannel.CONSOLE,
        recipient,
        f"告警通知: {context['alert_name']}",
        context['alert_message'],
        metadata=context
    )


def send_progress_notification(recipient: str, progress_data: Dict) -> Optional[str]:
    """
    发送进度通知

    Args:
        recipient: 接收者
        progress_data: 进度数据

    Returns:
        Optional[str]: 通知ID
    """
    service = get_notification_service()

    context = {
        'task_name': progress_data.get('task_name', '未知任务'),
        'progress': progress_data.get('progress', 0),
        'status': progress_data.get('status', 'unknown'),
        'message': progress_data.get('message', ''),
        'update_time': progress_data.get('time', datetime.now().isoformat())
    }

    # 使用邮件模板
    template = service.get_template('progress_email')
    if template:
        return service.send_notification_from_template('progress_email', recipient, context)

    # 回退到控制台
    return service.send_notification(
        NotificationChannel.CONSOLE,
        recipient,
        f"进度通知: {context['task_name']}",
        f"进度: {context['progress']}%, 状态: {context['status']}, 消息: {context['message']}",
        metadata=context
    )


def main():
    """主函数 - 测试通知服务"""
    import argparse

    parser = argparse.ArgumentParser(description='通知服务测试')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--email', type=str, help='测试邮件发送')
    parser.add_argument('--webhook', type=str, help='测试Webhook发送')
    args = parser.parse_args()

    # 创建通知服务
    service = NotificationService()

    if args.test:
        print("开始测试通知服务...")

        # 测试控制台通知
        notification_id = service.send_notification(
            NotificationChannel.CONSOLE,
            "console",
            "测试通知",
            "这是一个测试通知消息",
            metadata={"test": True}
        )
        print(f"控制台通知已发送: {notification_id}")

        # 测试模板通知
        template = service.get_template('alert_email')
        if template:
            context = {
                'alert_level': 'WARNING',
                'alert_name': '测试告警',
                'alert_message': '这是一个测试告警消息',
                'alert_time': datetime.now().isoformat(),
                'current_value': '85.5'
            }

            template_id = service.send_notification_from_template(
                'alert_email', 'test@example.com', context
            )
            print(f"模板通知已发送: {template_id}")

        time.sleep(2)

        # 显示统计信息
        stats = service.get_statistics()
        print(f"\n统计信息: {stats}")

        # 显示历史记录
        history = service.get_notification_history(5)
        print(f"\n最近通知:")
        for notification in history:
            status = "成功" if notification.delivered_at else ("失败" if notification.failed_at else "发送中")
            print(f"  {notification.subject}: {status}")

    if args.email:
        print(f"测试邮件发送到: {args.email}")

        notification_id = service.send_notification(
            NotificationChannel.EMAIL,
            args.email,
            "测试邮件",
            "<h1>这是一封测试邮件</h1><p>来自AR系统的通知服务。</p>",
            metadata={"test": True}
        )
        print(f"邮件通知已发送: {notification_id}")

    if args.webhook:
        print(f"测试Webhook发送到: {args.webhook}")

        # 配置Webhook
        service.config['channels']['webhook'] = {
            'url': args.webhook,
            'method': 'POST'
        }
        service._init_notifiers()

        notification_id = service.send_notification(
            NotificationChannel.WEBHOOK,
            args.webhook,
            "测试Webhook",
            "这是一条测试Webhook消息",
            metadata={"test": True}
        )
        print(f"Webhook通知已发送: {notification_id}")

    service.cleanup()


if __name__ == '__main__':
    main()
