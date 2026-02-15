"""
邮件通知服务

功能:
- SMTP 邮件发送
- 邮件模板渲染
- 异步发送支持

作者: AI Assistant
版本: 1.0.0
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务"""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        from_email: Optional[str] = None,
        from_name: Optional[str] = "YL-Monitor 告警系统"
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.from_email = from_email or smtp_username
        self.from_name = from_name

        # 模板目录
        self.templates_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # 创建默认模板
        self._create_default_templates()

    def _create_default_templates(self):
        """创建默认邮件模板"""
        # HTML 模板
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 2px solid #667eea; padding-bottom: 20px; margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #667eea; }
        .alert-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; text-transform: uppercase; font-size: 12px; }
        .alert-critical { background: #fee2e2; color: #dc2626; }
        .alert-warning { background: #fef3c7; color: #d97706; }
        .alert-info { background: #dbeafe; color: #2563eb; }
        .content { line-height: 1.6; color: #374151; }
        .details { background: #f9fafb; padding: 20px; border-radius: 6px; margin: 20px 0; }
        .detail-row { margin-bottom: 10px; }
        .detail-label { font-weight: bold; color: #6b7280; }
        .detail-value { color: #111827; }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px; }
        .timestamp { color: #9ca3af; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">YL-Monitor 监控告警</div>
            <div class="timestamp">{{ timestamp }}</div>
        </div>

        <h2>{{ title }}</h2>

        <div class="alert-badge alert-{{ level }}">
            {{ level_display }}
        </div>

        <div class="content">
            <p>{{ message }}</p>

            <div class="details">
                <div class="detail-row">
                    <span class="detail-label">告警规则：</span>
                    <span class="detail-value">{{ rule_name }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">监控指标：</span>
                    <span class="detail-value">{{ metric_display }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">当前值：</span>
                    <span class="detail-value">{{ actual_value }}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">阈值：</span>
                    <span class="detail-value">{{ threshold }}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">触发时间：</span>
                    <span class="detail-value">{{ triggered_at }}</span>
                </div>
            </div>

            <p>请及时处理此告警。如有疑问，请联系系统管理员。</p>
        </div>

        <div class="footer">
            <p>此邮件由 YL-Monitor 系统自动发送，请勿回复。</p>
        </div>
    </div>
</body>
</html>
"""

        # 纯文本模板
        text_template = """
YL-Monitor 监控告警

{{ title }}

级别: {{ level_display }}
时间: {{ timestamp }}

{{ message }}

告警详情:
- 规则名称: {{ rule_name }}
- 监控指标: {{ metric_display }}
- 当前值: {{ actual_value }}%
- 阈值: {{ threshold }}%
- 触发时间: {{ triggered_at }}

请及时处理此告警。如有疑问，请联系系统管理员。

此邮件由 YL-Monitor 系统自动发送，请勿回复。
"""

        # 保存模板
        html_path = self.templates_dir / "alert.html"
        text_path = self.templates_dir / "alert.txt"

        if not html_path.exists():
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_template)

        if not text_path.exists():
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text_template)

    async def send_alert_email(
        self,
        recipients: List[str],
        subject: str,
        alert_data: Dict[str, Any]
    ) -> bool:
        """发送告警邮件"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP 未配置，跳过邮件发送")
            return False

        try:
            # 准备邮件数据
            email_data = self._prepare_email_data(alert_data)

            # 渲染模板
            html_content = self._render_template("alert.html", email_data)
            text_content = self._render_template("alert.txt", email_data)

            # 发送邮件
            await self._send_email_async(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            logger.info(f"告警邮件发送成功: {subject} -> {recipients}")
            return True

        except Exception as e:
            logger.error(f"告警邮件发送失败: {e}")
            return False

    def _prepare_email_data(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备邮件数据"""
        level_map = {
            "critical": "严重",
            "warning": "警告",
            "info": "信息"
        }

        metric_map = {
            "cpu": "CPU 使用率",
            "memory": "内存使用率",
            "disk": "磁盘使用率",
            "network": "网络流量",
            "process": "进程数",
            "load": "系统负载"
        }

        return {
            "title": alert_data.get("title", "系统告警通知"),
            "level": alert_data.get("level", "warning"),
            "level_display": level_map.get(alert_data.get("level", "warning"), "警告"),
            "message": alert_data.get("message", ""),
            "rule_name": alert_data.get("rule_name", ""),
            "metric_display": metric_map.get(alert_data.get("metric", ""), alert_data.get("metric", "")),
            "actual_value": alert_data.get("actual_value", 0),
            "threshold": alert_data.get("threshold", 0),
            "triggered_at": alert_data.get("triggered_at", ""),
            "timestamp": alert_data.get("timestamp", "")
        }

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            # 返回简单文本
            return f"""
系统告警通知

{data.get('title', '')}

级别: {data.get('level_display', '')}
消息: {data.get('message', '')}

详情:
- 规则: {data.get('rule_name', '')}
- 指标: {data.get('metric_display', '')}
- 当前值: {data.get('actual_value', '')}%
- 阈值: {data.get('threshold', '')}%

时间: {data.get('timestamp', '')}
"""

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)
        return template.render(**data)

    async def _send_email_async(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: str
    ):
        """异步发送邮件"""
        # 在线程池中执行同步发送
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._send_email_sync,
            recipients,
            subject,
            html_content,
            text_content
        )

    def _send_email_sync(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: str
    ):
        """同步发送邮件"""
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = ', '.join(recipients)

        # 添加纯文本版本
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)

        # 添加 HTML 版本
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # 创建 SSL 上下文
        context = ssl.create_default_context()

        # 发送邮件
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)

            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()

        except Exception as e:
            raise Exception(f"邮件发送失败: {e}")

    async def test_connection(self) -> bool:
        """测试邮件服务器连接"""
        if not self.smtp_username or not self.smtp_password:
            return False

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._test_connection_sync)
        except Exception as e:
            logger.error(f"邮件连接测试失败: {e}")
            return False

    def _test_connection_sync(self) -> bool:
        """同步测试连接"""
        try:
            context = ssl.create_default_context()

            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)

            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            return True

        except Exception:
            return False


# 全局实例
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """获取邮件服务实例"""
    global _email_service
    if _email_service is None:
        # 从环境变量获取配置
        smtp_server = "smtp.gmail.com"  # 默认 Gmail
        smtp_port = 587
        smtp_username = None  # 需要配置
        smtp_password = None  # 需要配置
        from_email = None
        from_name = "YL-Monitor 告警系统"

        _email_service = EmailService(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=from_name
        )
    return _email_service
