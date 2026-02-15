#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本优化测试验证脚本
用于验证脚本部署优化的所有组件是否正常工作
"""

print("🚀 开始脚本优化验证测试...")

# 测试1: 检查关键文件是否存在
from pathlib import Path

from test_utils import add_project_paths

PATHS = add_project_paths()

print("\n🧪 测试文件完整性...")

files_to_check = [
    PATHS.monitor_root / "monitor" / "monitor-js" / "core" / "app" / "script-execution-config.js",
    PATHS.monitor_root / "monitor" / "monitor-js" / "api-config.js",
    PATHS.root / "scripts" / "scripts_manager_enhanced.py",
    PATHS.monitor_root / "monitor" / "monitor-js" / "modules" / "scripts-module.js",
]

for file_path in files_to_check:
    if file_path.exists():
        print(f"✅ {file_path.relative_to(PATHS.root)}")
    else:
        print(f"❌ {file_path.relative_to(PATHS.root)}")

print("\n✅ 脚本优化验证测试完成!")
