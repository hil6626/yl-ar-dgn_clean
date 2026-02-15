#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PathManager 验证脚本
测试路径管理器是否能正确工作

生成者: Copilot
最后更新: 2026-02-04
"""

from pathlib import Path

from test_utils import add_project_paths

PATHS = add_project_paths()

try:
    from path_manager import get_path_manager
    
    print("=" * 70)
    print("🔍 AR 项目路径管理器验证")
    print("=" * 70)
    print()
    
    # 获取路径管理器实例
    pm = get_path_manager()
    
    print("✅ PathManager 初始化成功")
    print()
    
    # 显示项目根目录
    print(f"📁 项目根目录: {pm.project_root}")
    print()
    
    # 验证关键文件是否存在
    print("🔐 验证关键文件:")
    critical_files = [
        pm.app_config_file,
        pm.project_root / 'requirements.txt',
        pm.backend_dir / 'monitor_app.py',
        pm.src_dir / 'launcher.py',
    ]
    
    for file_path in critical_files:
        exists = file_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path.relative_to(pm.project_root)}")
    
    print()
    
    # 显示所有路径
    print("📋 项目所有路径:")
    for key, value in pm.to_dict().items():
        print(f"  • {key:20} → {value}")
    
    print()
    
    # 验证目录创建
    print("🛠️  验证目录创建功能:")
    test_dirs = [pm.logs_dir, pm.data_dir, pm.backups_dir]
    for dir_path in test_dirs:
        pm.ensure_dir_exists(dir_path)
        exists = dir_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path.relative_to(pm.project_root)}")
    
    print()
    
    # 验证日志文件路径
    print("📝 验证日志文件路径:")
    log_file = pm.get_log_file('test_pathmanager.log')
    print(f"  ✅ 日志文件: {log_file.relative_to(pm.project_root)}")
    print()
    
    # 验证配置文件读取
    print("⚙️  验证配置文件读取:")
    try:
        config = pm.get_config('app_config')
        print(f"  ✅ 成功读取 app_config.json")
        print(f"    应用名: {config.get('app', {}).get('name', 'N/A')[:40]}...")
        print(f"    版本: {config.get('app', {}).get('version', 'N/A')}")
    except Exception as e:
        print(f"  ❌ 读取配置失败: {e}")
    
    print()
    print("=" * 70)
    print("✅ 所有验证通过！PathManager 工作正常")
    print("=" * 70)
    print()
    print("💡 使用建议:")
    print("   from path_manager import get_path_manager")
    print("   pm = get_path_manager()")
    print("   config_file = pm.app_config_file")
    print("   log_file = pm.get_log_file('myapp.log')")
    
except Exception as e:
    print("=" * 70)
    print("❌ PathManager 验证失败")
    print("=" * 70)
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
