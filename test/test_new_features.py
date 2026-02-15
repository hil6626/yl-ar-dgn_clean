#!/usr/bin/env python3
"""
测试新功能集成验证脚本
验证实时监控图表、WebSocket连接、日志查看等功能
"""

import os
import sys
import time
from typing import Tuple, List

from test_utils import (
    get_base_url,
    get_requests_session,
    resolve_monitor_api_prefix,
    require_server,
)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _build_url(base_url: str, prefix: str, path: str) -> str:
    prefix = prefix.rstrip("/")
    path = path if path.startswith("/") else f"/{path}"
    if prefix:
        return f"{base_url}{prefix}{path}"
    return f"{base_url}{path}"


def test_api_endpoints(base_url: str, api_prefix: str, session) -> Tuple[bool, int]:
    """测试新的API端点"""
    print("🔍 测试API端点...")
    passed = 0
    total = 0

    # 测试健康检查
    try:
        total += 1
        response = session.get(_build_url(base_url, api_prefix, "/health"))
        if response.status_code == 200:
            print("✅ 健康检查API正常")
            passed += 1
        else:
            print(f"❌ 健康检查API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查API错误: {e}")

    # 测试日志API
    try:
        total += 1
        response = session.get(_build_url(base_url, api_prefix, "/logs"))
        if response.status_code == 200:
            print("✅ 日志API正常")
            passed += 1
        else:
            print(f"❌ 日志API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 日志API错误: {e}")

    # 测试指标API
    try:
        total += 1
        response = session.get(_build_url(base_url, api_prefix, "/resources"))
        if response.status_code == 200:
            print("✅ 指标API正常")
            passed += 1
        else:
            print(f"❌ 指标API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 指标API错误: {e}")

    # 测试诊断API
    try:
        total += 1
        response = session.get(_build_url(base_url, api_prefix, "/overview"))
        if response.status_code == 200:
            print("✅ 诊断API正常")
            passed += 1
        else:
            print(f"❌ 诊断API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 诊断API错误: {e}")
    return passed == total, passed

def test_websocket_connection(base_url: str, session) -> bool:
    """测试WebSocket连接"""
    print("🔌 测试WebSocket连接...")

    # 注意：这里只是检查SocketIO端点是否可访问
    try:
        response = session.get(f"{base_url}/socket.io/?EIO=4&transport=polling")
        if response.status_code == 200:
            print("✅ WebSocket端点可访问")
            return True
        print(f"❌ WebSocket端点不可访问: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ WebSocket连接测试失败: {e}")
        return False

def test_frontend_loading(base_url: str, session) -> bool:
    """测试前端页面加载"""
    print("🌐 测试前端页面加载...")

    try:
        response = session.get(f"{base_url}/monitor/monitor.html")
        if response.status_code == 200:
            content = response.text

            # 检查新的模块是否在HTML中
            checks = [
                ("监控API配置", "monitor-js/api-config.js"),
                ("核心模块", "monitor-js/monitor-core.js"),
                ("视图模块", "monitor-js/monitor-view.js"),
                ("动作模块", "monitor-js/monitor-actions.js"),
                ("导航菜单", "系统概览"),
                ("导航菜单", "日志管理"),
            ]

            all_ok = True
            for name, check in checks:
                if check in content:
                    print(f"✅ {name} 已加载")
                else:
                    print(f"❌ {name} 未找到")
                    all_ok = False

            return all_ok
        else:
            print(f"❌ 前端页面加载失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试新功能集成...")
    print("=" * 50)

    base_url = get_base_url()
    session = get_requests_session()
    api_prefix = resolve_monitor_api_prefix(base_url)

    if not require_server(base_url, api_prefix):
        print(f"⚠️ 服务不可用: {base_url}{api_prefix}/health")
        return

    # 等待服务完全启动
    print("⏳ 等待服务启动...")
    time.sleep(3)

    # 运行测试
    api_ok, _ = test_api_endpoints(base_url, api_prefix, session)
    print()
    ws_ok = test_websocket_connection(base_url, session)
    print()
    ui_ok = test_frontend_loading(base_url, session)

    print()
    print("=" * 50)
    if api_ok and ui_ok and ws_ok:
        print(f"✅ 测试完成！请在浏览器中访问 {base_url}/monitor/monitor.html 查看新功能")
    else:
        print(f"⚠️ 测试完成但存在失败项，请检查服务状态: {base_url}")

if __name__ == "__main__":
    main()
