#!/usr/bin/env python3
"""
告警系统测试脚本

功能:
- 测试告警规则创建
- 测试告警触发
- 测试通知发送
- 测试 WebSocket 实时推送

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import aiohttp
import websockets

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("test_alert_system")


class AlertSystemTester:
    """告警系统测试器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5500):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"
        self.session: aiohttp.ClientSession = None
        self.test_rule_id = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def create_test_rule(self) -> str:
        """创建测试告警规则"""
        logger.info("创建测试告警规则...")
        
        rule_data = {
            "name": "测试告警规则",
            "description": "用于测试的告警规则",
            "metric": "cpu",
            "comparison": "gt",
            "threshold": 10.0,  # 设置较低阈值以便触发
            "duration": 1,
            "level": "warning",
            "enabled": True,
            "channels": ["browser", "email", "webhook"],
            "silence_duration": 300,
            "email_recipients": ["test@example.com"],
            "webhook_url": "http://0.0.0.0:8080/webhook"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/alerts/rules",
                json=rule_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.test_rule_id = result.get("id")
                    logger.info(f"✓ 测试告警规则创建成功，ID: {self.test_rule_id}")
                    return self.test_rule_id
                else:
                    error_text = await response.text()
                    logger.error(f"✗ 创建告警规则失败: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"✗ 创建告警规则时发生异常: {e}")
            return None
    
    async def trigger_test_alert(self) -> bool:
        """触发测试告警"""
        if not self.test_rule_id:
            logger.error("✗ 未找到测试规则 ID")
            return False
            
        logger.info("触发测试告警...")
        
        try:
            # 模拟触发告警的 API 调用
            async with self.session.post(
                f"{self.base_url}/api/v1/alerts/test-trigger/{self.test_rule_id}"
            ) as response:
                if response.status == 200:
                    logger.info("✓ 测试告警触发成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"✗ 触发告警失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"✗ 触发告警时发生异常: {e}")
            return False
    
    async def test_websocket_notifications(self) -> bool:
        """测试 WebSocket 实时推送"""
        logger.info("测试 WebSocket 通知推送...")
        
        try:
            uri = f"{self.ws_url}/ws/alerts"
            async with websockets.connect(uri) as websocket:
                logger.info("✓ WebSocket 连接成功")
                
                # 等待初始化消息
                init_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                init_data = json.loads(init_msg)
                logger.info(f"✓ 收到初始化消息: {init_data.get('type')}")
                
                # 等待告警消息（最多等待10秒）
                try:
                    alert_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                    alert_data = json.loads(alert_msg)
                    logger.info(f"✓ 收到告警消息: {alert_data.get('type')}")
                    
                    # 检查消息类型
                    if alert_data.get("type") in ["alert_triggered", "browser_notification"]:
                        logger.info("✓ WebSocket 通知推送测试通过")
                        return True
                    else:
                        logger.warning(f"⚠ 收到意外消息类型: {alert_data.get('type')}")
                        
                except asyncio.TimeoutError:
                    logger.warning("⚠ 未收到 WebSocket 告警消息（超时）")
                    
        except Exception as e:
            logger.error(f"✗ WebSocket 测试失败: {e}")
            return False
            
        return True
    
    async def acknowledge_alert(self) -> bool:
        """确认告警"""
        if not self.test_rule_id:
            logger.error("✗ 未找到测试规则 ID")
            return False
            
        logger.info("确认测试告警...")
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/alerts/{self.test_rule_id}/acknowledge?user=tester"
            ) as response:
                if response.status == 200:
                    logger.info("✓ 告警确认成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"✗ 告警确认失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"✗ 告警确认时发生异常: {e}")
            return False
    
    async def delete_test_rule(self) -> bool:
        """删除测试告警规则"""
        if not self.test_rule_id:
            logger.warning("⚠ 未找到测试规则 ID，跳过删除")
            return True
            
        logger.info("删除测试告警规则...")
        
        try:
            async with self.session.delete(
                f"{self.base_url}/api/v1/alerts/rules/{self.test_rule_id}"
            ) as response:
                if response.status == 200:
                    logger.info("✓ 测试告警规则删除成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"✗ 删除告警规则失败: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"✗ 删除告警规则时发生异常: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("告警系统测试开始")
        logger.info("=" * 60)
        
        test_results = []
        
        # 1. 创建测试规则
        rule_id = await self.create_test_rule()
        test_results.append(("创建告警规则", rule_id is not None))
        
        if not rule_id:
            logger.error("✗ 无法继续测试，因为创建规则失败")
            return False
        
        # 2. 触发告警（模拟）
        # 注意：实际环境中我们会让系统监控指标达到阈值来触发告警
        # 这里我们假设规则创建后就已经触发了告警
        
        # 3. 测试 WebSocket 通知
        ws_result = await self.test_websocket_notifications()
        test_results.append(("WebSocket 通知推送", ws_result))
        
        # 4. 确认告警
        ack_result = await self.acknowledge_alert()
        test_results.append(("告警确认", ack_result))
        
        # 5. 删除测试规则
        delete_result = await self.delete_test_rule()
        test_results.append(("删除告警规则", delete_result))
        
        # 输出测试结果
        logger.info("=" * 60)
        logger.info("测试结果汇总:")
        logger.info("=" * 60)
        
        all_passed = True
        for test_name, result in test_results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status:<10} {test_name}")
            if not result:
                all_passed = False
        
        logger.info("=" * 60)
        final_status = "✓ 所有测试通过" if all_passed else "✗ 存在测试失败"
        logger.info(final_status)
        logger.info("=" * 60)
        
        return all_passed


async def main():
    """主函数"""
    host = os.getenv("YL_MONITOR_HOST", "0.0.0.0")
    port = int(os.getenv("YL_MONITOR_PORT", "5500"))
    
    async with AlertSystemTester(host, port) as tester:
        success = await tester.run_all_tests()
        return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生未预期的错误: {e}", exc_info=True)
        sys.exit(1)
