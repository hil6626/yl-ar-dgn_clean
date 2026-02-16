#!/usr/bin/env python3
"""
YL-Monitor 重复文件清理脚本
识别并清理沉积的旧HTML、CSS、JS文件
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
BACKUP_DIR = PROJECT_ROOT / "backups" / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 需要清理的重复/旧文件列表
DUPLICATE_FILES = {
    # 旧的HTML模板（已被新模板替代）
    "templates": [
        "alert_analytics.html",      # 被 alert_center.html 替代
        "alert_rules.html",          # 被 alert_center.html 替代
        "api_test_monitor.html",     # 测试文件，未使用
        "ar_dashboard.html",         # 被 ar.html 替代
        "dashboard_enhanced.html",   # 被 dashboard.html 替代
        "intelligent_alert.html",    # 被 alert_center.html 替代
    ],
    
    # 旧的CSS文件（已被主题系统替代）
    "static/css": [
        "alert-analytics.css",       # 被 alert-center.css 替代
        "alert-rules.css",           # 被 alert-center.css 替代
        "ar_dashboard.css",          # 被 ar.css 替代
        "dashboard_enhanced.css",    # 不存在，但以防万一
        "intelligent-alert.css",     # 被 alert-center.css 替代
        "platform.css",              # 被 platform-modern.css 替代
        "theme-api-doc.css",         # 被 api-doc.css 替代
        "theme-dag.css",             # 被 dag.css 替代
        "theme-dashboard.css",       # 被 dashboard.css 替代
        "theme-scripts.css",         # 被 scripts.css 替代
    ],
    
    # 旧的JS文件（已被模块化系统替代）
    "static/js": [
        "alert-analytics.js",        # 被 alert-center.js 替代
        "dashboard_enhanced.js",     # 被 page-dashboard.js 替代
        "intelligent-alert.js",      # 被 alert-center.js 替代
        "notification-service.js",   # 被 notification-manager.js 替代
        "platform_full.js",          # 被模块化系统替代
        "websocket.js",              # 被 websocket-manager.js 替代
    ],
}

def backup_file(file_path):
    """备份文件到备份目录"""
    if not file_path.exists():
        return False
    
    # 创建备份目录
    relative_path = file_path.relative_to(PROJECT_ROOT)
    backup_path = BACKUP_DIR / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    shutil.copy2(file_path, backup_path)
    return True

def cleanup_files():
    """执行清理操作"""
    print("=" * 60)
    print("YL-Monitor 重复文件清理工具")
    print("=" * 60)
    print(f"备份目录: {BACKUP_DIR}")
    print("-" * 60)
    
    total_removed = 0
    total_backed_up = 0
    
    for subdir, files in DUPLICATE_FILES.items():
        dir_path = PROJECT_ROOT / subdir
        if not dir_path.exists():
            print(f"\n⚠️ 目录不存在: {subdir}")
            continue
        
        print(f"\n📁 检查目录: {subdir}")
        
        for filename in files:
            file_path = dir_path / filename
            
            if file_path.exists():
                # 备份文件
                if backup_file(file_path):
                    total_backed_up += 1
                    print(f"  ✅ 已备份: {filename}")
                
                # 删除文件
                try:
                    file_path.unlink()
                    total_removed += 1
                    print(f"  🗑️  已删除: {filename}")
                except Exception as e:
                    print(f"  ❌ 删除失败 {filename}: {e}")
            else:
                print(f"  ℹ️  文件不存在: {filename}")
    
    print("\n" + "=" * 60)
    print(f"清理完成: 备份 {total_backed_up} 个文件, 删除 {total_removed} 个文件")
    print(f"备份位置: {BACKUP_DIR}")
    print("=" * 60)
    
    return total_removed

def find_orphaned_files():
    """查找可能孤立未被引用的文件"""
    print("\n🔍 扫描孤立文件...")
    
    # 检查templates目录中未被路由引用的HTML
    templates_dir = PROJECT_ROOT / "templates"
    routes_dir = PROJECT_ROOT / "app" / "routes"
    
    # 获取所有HTML模板
    html_files = set(f.stem for f in templates_dir.glob("*.html") if f.name != "README.md")
    
    # 扫描路由文件查找引用
    referenced_templates = set()
    if routes_dir.exists():
        for py_file in routes_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                for template in html_files:
                    if template in content:
                        referenced_templates.add(template)
            except:
                pass
    
    # 找出未被引用的模板
    orphaned = html_files - referenced_templates
    if orphaned:
        print(f"\n⚠️  可能未被引用的模板文件:")
        for template in sorted(orphaned):
            print(f"  - {template}.html")
    else:
        print("\n✅ 所有模板文件似乎都被引用了")

if __name__ == "__main__":
    # 执行清理
    count = cleanup_files()
    
    # 扫描孤立文件
    find_orphaned_files()
    
    print("\n💡 提示: 如果误删了文件，可以从备份目录恢复")
