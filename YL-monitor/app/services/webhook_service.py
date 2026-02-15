"""
Webhook 通知服务

功能:
- 发送 Webhook 通知到第三方平台
- 支持企业微信、钉钉等平台
- 异步发送和重试机制

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WebhookService:
    """Webhook 服务"""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def send_alert_webhook(
        self,
        webhook_url: str,
        alert_data: Dict[str, Any]
    ) -> bool:
        """发送告警 Webhook"""
        # 检测平台类型
        platform = self._detect_platform(webhook_url)

        # 格式化消息
        message_data = self._format_message(platform, alert_data)

        # 发送 Webhook
        return await self._send_webhook(webhook_url, message_data)

    def _detect_platform(self, webhook_url: str) -> str:
        """检测 Webhook 平台类型"""
        if "qyapi.weixin.qq.com" in webhook_url:
            return "wechat"
        elif "dingtalk.com" in webhook_url:
            return "dingtalk"
        elif "feishu.cn" in webhook_url:
            return "feishu"
        else:
            return "generic"

    def _format_message(self, platform: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化消息内容"""
        level_emoji = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵"
        }

        level_text = {
            "critical": "严重",
            "warning": "警告",
            "info": "信息"
        }

        emoji = level_emoji.get(alert_data.get("level", "info"), "🔵")
        level_display = level_text.get(alert_data.get("level", "info"), "信息")

        title = f"{emoji} YL-Monitor 告警通知"
        content = f"""
**告警规则**: {alert_data.get('rule_name', '')}
**级别**: {level_display}
**状态**: {alert_data.get('status', '').title()}
**监控指标**: {alert_data.get('metric', '')}
**当前值**: {alert_data.get('actual_value', 0)}%
**阈值**: {alert_data.get('threshold', 0)}%
**消息**: {alert_data.get('message', '')}
**触发时间**: {alert_data.get('triggered_at', '')}
**告警ID**: {alert_data.get('alert_id', '')}
"""

        if platform == "wechat":
            return {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"{title}\n{content}"
                }
            }
        elif platform == "dingtalk":
            return {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"## {title}\n{content}"
                }
            }
        elif platform == "feishu":
            return {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [
                                [
                                    {
                                        "tag": "text",
                                        "text": content.replace("**", "").replace("\n", "\n\n")
                                    }
                                ]
                            ]
                        }
                    }
                }
            }
        else:
            # 通用 JSON 格式
            return {
                "title": title,
                "content": content.strip(),
                "alert_data": alert_data,
                "timestamp": alert_data.get("timestamp", "")
            }

    async def _send_webhook(
        self,
        webhook_url: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """发送 Webhook 请求"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "YL-Monitor/1.0.0"
        }

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url,
                        json=message_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status in [200, 201, 202]:
                            logger.info(f"Webhook 发送成功: {webhook_url}")
                            return True
                        else:
                            response_text = await response.text()
                            logger.warning(
                                f"Webhook 发送失败 (尝试 {attempt + 1}/{self.max_retries}): "
                                f"HTTP {response.status} - {response_text}"
                            )

            except asyncio.TimeoutError:
                logger.warning(f"Webhook 超时 (尝试 {attempt + 1}/{self.max_retries}): {webhook_url}")
            except Exception as e:
                logger.error(f"Webhook 发送异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")

            # 等待重试
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避

        logger.error(f"Webhook 发送失败，已重试 {self.max_retries} 次: {webhook_url}")
        return False

    async def test_webhook(self, webhook_url: str) -> bool:
        """测试 Webhook 连接"""
        test_data = {
            "alert_id": "test-001",
            "rule_id": "test-rule",
            "rule_name": "测试告警规则",
            "level": "info",
            "status": "triggered",
            "metric": "cpu",
            "threshold": 80.0,
            "actual_value": 85.0,
            "message": "这是一条测试告警消息",
            "triggered_at": "2025-02-08T10:30:00Z",
            "timestamp": "2025-02-08T10:30:00Z"
        }

        return await self.send_alert_webhook(webhook_url, test_data)


# 全局实例
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """获取 Webhook 服务实例"""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
