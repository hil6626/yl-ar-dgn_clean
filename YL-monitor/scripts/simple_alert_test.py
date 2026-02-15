#!/usr/bin/env python3
"""
简单的告警系统测试脚本

功能:
- 测试告警服务是否正常工作
- 测试 WebSocket 连接
- 验证基本的 API 路由

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

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
logger = logging.getLogger("simple_alert_test")


async def test_alert_service():
    """测试告警服务基础功能"""
    host = os.getenv("YL_MONITOR_HOST", "localhost")
    port = int(os.getenv("YL_MONITOR_PORT", "5500"))
    base_url = f"http://{host}:{port}"
    
    logger.info("开始测试告警服务...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 测试健康检查端点
            logger.info("1. 测试健康检查端点...")
            async with session.get(f"{base_url}/api/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✓ 健康检查通过: {health_data}")
                else:
                    logger.error(f"✗ 健康检查失败: {response.status}")
                    return False
            
            # 2. 测试告警规则列表
            logger.info("2. 测试告警规则列表...")
            async with session.get(f"{base_url}/api/v1/alerts/rules") as response:
                if response.status == 200:
                    rules_data = await response.json()
                    logger.info(f"✓ 告警规则列表获取成功，共有 {len(rules_data.get('items', []))} 条规则")
                else:
                    logger.warning(f"⚠ 告警规则列表获取失败: {response.status}")
            
            # 3. 测试告警历史
            logger.info("3. 测试告警历史...")
            async with session.get(f"{base_url}/api/v1/alerts/history") as response:
                if response.status == 200:
                    history_data = await response.json()
                    logger.info(f"✓ 告警历史获取成功，共有 {len(history_data.get('items', []))} 条记录")
                else:
                    logger.warning(f"⚠ 告警历史获取失败: {response.status}")
            
            # 4. 测试活动告警
            logger.info("4. 测试活动告警...")
            async with session.get(f"{base_url}/api/v1/alerts/active") as response:
                if response.status == 200:
                    active_data = await response.json()
                    logger.info(f"✓ 活动告警获取成功，共有 {len(active_data.get('items', []))} 条记录")
                else:
                    logger.warning(f"⚠ 活动告警获取失败: {response.status}")
            
            logger.info("告警服务基础功能测试完成")
            return True
            
        except Exception as e:
            logger.error(f"✗ 测试过程中发生异常: {e}")
            return False


async def test_websocket_connection():
    """测试 WebSocket 连接"""
    host = os.getenv("YL_MONITOR_HOST", "localhost")
    port = int(os.getenv("YL_MONITOR_PORT", "5500"))
    ws_url = f"ws://{host}:{port}"
    
    logger.info("开始测试 WebSocket 连接...")
    
    try:
        uri = f"{ws_url}/ws/alerts"
        async with websockets.connect(uri) as websocket:
            logger.info("✓ WebSocket 连接成功")
            
            # 等待初始化消息
            init_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
            init_data = json.loads(init_msg)
            logger.info(f"✓ 收到初始化消息: {init_data.get('type', 'unknown')}")
            
            logger.info("WebSocket 连接测试完成")
            return True
            
    except asyncio.TimeoutError:
        logger.error("✗ WebSocket 连接超时")
        return False
    except Exception as e:
        logger.error(f"✗ WebSocket 连接测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("简单告警系统测试")
    logger.info("=" * 60)
    
    # 测试告警服务
    service_ok = await test_alert_service()
    
    # 测试 WebSocket
    websocket_ok = await test_websocket_connection()
    
    logger.info("=" * 60)
    logger.info("测试结果:")
    logger.info("=" * 60)
    logger.info(f"{'✓' if service_ok else '✗'} 告警服务: {'通过' if service_ok else '失败'}")
    logger.info(f"{'✓' if websocket_ok else '✗'} WebSocket 连接: {'通过' if websocket_ok else '失败'}")
    
    overall_ok = service_ok and websocket_ok
    logger.info("=" * 60)
    logger.info(f"{'✓' if overall_ok else '✗'} 总体测试结果: {'通过' if overall_ok else '失败'}")
    logger.info("=" * 60)
    
    return overall_ok


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
