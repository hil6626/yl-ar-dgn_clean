#!/usr/bin/env python3
"""
模块加载测试脚本
检查关键JS模块是否存在和可访问
"""

import os
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    full_path = Path('/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean') / filepath
    exists = full_path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def main():
    print("=" * 60)
    print("YL-Monitor 模块加载测试")
    print("=" * 60)
    
    # 检查Alerts模块
    print("\n📋 Alerts页面模块:")
    alerts_modules = [
        ("YL-monitor/static/js/pages/alerts/index.js", "Alerts页面入口"),
        ("YL-monitor/static/js/pages/alerts/components/index.js", "Alerts组件入口"),
        ("YL-monitor/static/js/pages/alerts/components/AlertDetailDrawer.js", "告警详情抽屉"),
        ("YL-monitor/static/js/pages/alerts/managers/index.js", "Alerts管理器入口"),
        ("YL-monitor/static/js/pages/alerts/managers/AlertsWebSocketManager.js", "WebSocket管理器"),
    ]
    
    alerts_ok = all(check_file_exists(path, desc) for path, desc in alerts_modules)
    
    # 检查Scripts模块
    print("\n📜 Scripts页面模块:")
    scripts_modules = [
        ("YL-monitor/static/js/pages/scripts/index.js", "Scripts页面入口"),
        ("YL-monitor/static/js/pages/scripts/components/index.js", "Scripts组件入口"),
        ("YL-monitor/static/js/pages/scripts/components/ScriptList.js", "脚本列表"),
        ("YL-monitor/static/js/pages/scripts/components/ScriptCard.js", "脚本卡片"),
        ("YL-monitor/static/js/pages/scripts/managers/index.js", "Scripts管理器入口"),
        ("YL-monitor/static/js/pages/scripts/managers/ScriptRunner.js", "脚本运行器"),
        ("YL-monitor/static/js/pages/scripts/managers/LogViewer.js", "日志查看器"),
    ]
    
    scripts_ok = all(check_file_exists(path, desc) for path, desc in scripts_modules)
    
    # 检查DAG模块
    print("\n🔄 DAG页面模块:")
    dag_modules = [
        ("YL-monitor/static/js/pages/dag/index.js", "DAG页面入口"),
        ("YL-monitor/static/js/pages/dag/components/index.js", "DAG组件入口"),
        ("YL-monitor/static/js/pages/dag/managers/index.js", "DAG管理器入口"),
    ]
    
    dag_ok = all(check_file_exists(path, desc) for path, desc in dag_modules)
    
    # 检查共享模块
    print("\n🔧 共享模块:")
    shared_modules = [
        ("YL-monitor/static/js/app-loader.js", "应用加载器"),
        ("YL-monitor/static/js/theme-manager.js", "主题管理器"),
        ("YL-monitor/static/js/ui-components.js", "UI组件"),
    ]
    
    shared_ok = all(check_file_exists(path, desc) for path, desc in shared_modules)
    
    # 检查模板文件
    print("\n📄 模板文件:")
    templates = [
        ("YL-monitor/templates/alert_center.html", "Alerts模板"),
        ("YL-monitor/templates/scripts.html", "Scripts模板"),
        ("YL-monitor/templates/dag.html", "DAG模板"),
    ]
    
    templates_ok = all(check_file_exists(path, desc) for path, desc in templates)
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)
    print(f"Alerts模块: {'✅ 正常' if alerts_ok else '❌ 有问题'}")
    print(f"Scripts模块: {'✅ 正常' if scripts_ok else '❌ 有问题'}")
    print(f"DAG模块: {'✅ 正常' if dag_ok else '❌ 有问题'}")
    print(f"共享模块: {'✅ 正常' if shared_ok else '❌ 有问题'}")
    print(f"模板文件: {'✅ 正常' if templates_ok else '❌ 有问题'}")
    
    all_ok = alerts_ok and scripts_ok and dag_ok and shared_ok and templates_ok
    print(f"\n总体状态: {'✅ 所有模块正常' if all_ok else '❌ 存在缺失模块'}")
    
    return all_ok

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
