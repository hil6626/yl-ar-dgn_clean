#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 监控服务启动脚本
启动本地HTTP服务和状态上报
"""

import sys
import time
import signal
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.local_http_server import LocalHTTPServer
from services.status_reporter import StatusReporter


def main():
    """主函数"""
    print("=" * 60)
    print("User GUI 监控服务启动")
    print("=" * 60)
    
    # 创建状态上报器
    config_path = project_root / 'config' / 'monitor_config.yaml'
    reporter = StatusReporter(str(config_path) if config_path.exists() else None)
    
    # 启动本地HTTP服务
    server = LocalHTTPServer(port=5502, status_reporter=reporter)
    if not server.start():
        print("❌ HTTP服务启动失败")
        return 1
    
    print(f"✅ HTTP服务已启动: http://0.0.0.0:5502")
    print("   - GET /health - 健康检查")
    print("   - GET /status - 详细状态")
    print("   - GET /stats  - 统计信息")
    
    # 启动状态上报（可选）
    reporter.config['enabled'] = True
    if reporter.start():
        print(f"✅ 状态上报已启动 -> {reporter.config['monitor_url']}")
    else:
        print("⚠️ 状态上报未启动（已禁用或已在运行）")
    
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 等待中断信号
    def signal_handler(sig, frame):
        print("\n\n正在停止服务...")
        reporter.stop()
        server.stop()
        print("✅ 服务已停止")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 保持运行
    while True:
        time.sleep(1)


if __name__ == '__main__':
    sys.exit(main())
