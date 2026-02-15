#!/usr/bin/env python3
"""
YL-Monitor 项目结构优化脚本
自动执行目录重构和文件合并
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
BACKUP_DIR = PROJECT_ROOT / "backups" / f"structure_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 优化配置
OPTIMIZATION_CONFIG = {
    "create_directories": [
        "scripts/core",
        "scripts/monitors/system",
        "scripts/monitors/service", 
        "scripts/monitors/ar",
        "scripts/maintenance/cleanup",
        "scripts/maintenance/backup",
        "scripts/maintenance/health",
        "scripts/optimizers/resource",
        "scripts/optimizers/service",
        "scripts/alerts/handlers",
        "scripts/alerts/notifiers",
        "scripts/alerts/rules",
        "scripts/utils/css",
        "scripts/utils/verify",
        "scripts/utils/dev"
    ],
    
    "merge_scripts": {
        # 验证脚本合并
        "scripts/core/verify.py": {
            "sources": [
                "verify_api.sh",
                "verify_pages.py",
                "verify_references.py",
                "verify_start.sh",
                "verify_static_resources.sh",
                "verify_templates.py",
                "verify_alert_center.py"
            ],
            "description": "统一项目验证工具"
        },
        
        # CSS工具合并
        "scripts/utils/css/manager.py": {
            "sources": [
                "tools/analyze_unused_css.py",
                "tools/check_css_compliance.py",
                "tools/cleanup_unused_css.py",
                "tools/duplicate_detector.py"
            ],
            "description": "CSS统一管理器"
        },
        
        # 启动脚本合并
        "scripts/core/start.py": {
            "sources": [
                "start_app_simple.sh",
                "debug_launch.sh",
                "deploy.sh"
            ],
            "description": "统一应用启动器"
        }
    },
    
    "move_scripts": {
        # 监控脚本分类
        "scripts/monitors/system/cpu_monitor.py": [
            "monitor/01_cpu_usage_monitor.py",
            "monitor/04_system_load_process_monitor.py"
        ],
        "scripts/monitors/system/memory_monitor.py": [
            "monitor/02_memory_usage_monitor.py"
        ],
        "scripts/monitors/system/disk_monitor.py": [
            "monitor/03_disk_space_io_monitor.py"
        ],
        "scripts/monitors/service/api_monitor.py": [
            "monitor/07_external_api_health_check.py",
            "monitor/08_web_app_availability_check.py"
        ],
        "scripts/monitors/service/port_monitor.py": [
            "monitor/05_port_service_availability_check.py"
        ],
        
        # 维护脚本分类
        "scripts/maintenance/cleanup/disk_cleanup.py": [
            "optimize/17_disk_junk_cleanup.py",
            "optimize/18_duplicate_file_dedup.py",
            "optimize/20_temp_file_cleanup.py"
        ],
        "scripts/maintenance/cleanup/cache_cleanup.py": [
            "optimize/19_cache_cleanup.py",
            "optimize/24_cache_db_maintenance.py",
            "optimize/29_service_cache_refresh.py"
        ],
        
        # 优化脚本分类
        "scripts/optimizers/resource/cpu_optimizer.py": [
            "optimize/34_process_priority_auto_adjust.py",
            "optimize/37_cpu_core_load_balance.py"
        ],
        "scripts/optimizers/resource/memory_optimizer.py": [
            "optimize/35_memory_leak_detect_alert.py"
        ]
    },
    
    "delete_empty": [
        "scripts/tools",  # 合并后删除
        "scripts/monitor",  # 移动后删除
        "scripts/optimize"  # 移动后删除
    ]
}


def backup_project():
    """创建项目备份"""
    print("=" * 60)
    print("创建项目备份...")
    print("=" * 60)
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 备份关键目录
    dirs_to_backup = ["scripts", "static", "templates"]
    for dir_name in dirs_to_backup:
        src = PROJECT_ROOT / dir_name
        if src.exists():
            dst = BACKUP_DIR / dir_name
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"✅ 已备份: {dir_name}")
    
    print(f"\n📦 备份位置: {BACKUP_DIR}")
    return True


def create_directory_structure():
    """创建新的目录结构"""
    print("\n" + "=" * 60)
    print("创建新的目录结构...")
    print("=" * 60)
    
    created = 0
    for dir_path in OPTIMIZATION_CONFIG["create_directories"]:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        # 创建__init__.py
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        
        created += 1
        print(f"📁 创建: {dir_path}")
    
    print(f"\n✅ 创建了 {created} 个目录")
    return True


def generate_merge_script(target, sources, description):
    """生成合并后的脚本框架"""
    template = f'''#!/usr/bin/env python3
"""
{description}
合并来源: {', '.join(sources)}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class {target.stem.replace('_', ' ').title().replace(' ', '')}:
    """
    {description}
    """
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.verbose = False
    
    def run(self, **kwargs):
        """
        主入口方法
        """
        raise NotImplementedError("请实现具体的run方法")
    
    def validate(self):
        """
        验证环境
        """
        return True


def main():
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--dry-run", "-d", action="store_true", help="模拟运行")
    
    args = parser.parse_args()
    
    tool = {target.stem.replace('_', ' ').title().replace(' ', '')}()
    tool.verbose = args.verbose
    
    if args.dry_run:
        print("🔍 模拟运行模式")
    
    # 执行主逻辑
    try:
        result = tool.run(dry_run=args.dry_run)
        if result:
            print("✅ 执行成功")
            return 0
        else:
            print("❌ 执行失败")
            return 1
    except Exception as e:
        print(f"❌ 错误: {{e}}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''
    return template


def create_merged_scripts():
    """创建合并后的脚本框架"""
    print("\n" + "=" * 60)
    print("创建合并后的脚本框架...")
    print("=" * 60)
    
    created = 0
    for target_path, config in OPTIMIZATION_CONFIG["merge_scripts"].items():
        target = PROJECT_ROOT / target_path
        
        # 确保目录存在
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成脚本内容
        content = generate_merge_script(
            target,
            config["sources"],
            config["description"]
        )
        
        # 写入文件
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 添加执行权限
        os.chmod(target, 0o755)
        
        created += 1
        print(f"📝 创建: {target_path}")
        print(f"   来源: {', '.join(config['sources'])}")
    
    print(f"\n✅ 创建了 {created} 个合并脚本框架")
    return True


def generate_migration_report():
    """生成迁移报告"""
    report_path = PROJECT_ROOT / "docs" / "MIGRATION_REPORT.md"
    
    report = f"""# YL-Monitor 项目结构迁移报告

**迁移时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 目录结构变更

### 新增目录
"""
    
    for dir_path in OPTIMIZATION_CONFIG["create_directories"]:
        report += f"- `{dir_path}/`\n"
    
    report += "\n## 脚本合并计划\n\n"
    
    for target, config in OPTIMIZATION_CONFIG["merge_scripts"].items():
        report += f"### {target}\n"
        report += f"- **描述:** {config['description']}\n"
        report += f"- **合并来源:**\n"
        for src in config["sources"]:
            report += f"  - `{src}`\n"
        report += "\n"
    
    report += """## 后续步骤

1. **实现合并脚本逻辑**
   - 将原脚本的功能迁移到新的合并脚本中
   - 保持向后兼容性

2. **更新调用入口**
   - 修改文档中的使用说明
   - 更新CI/CD配置

3. **测试验证**
   - 运行所有合并后的脚本
   - 确保功能正常

4. **删除旧脚本**
   - 确认新脚本工作正常后
   - 删除已合并的旧脚本

## 备份位置

所有原始文件已备份到:
```
{BACKUP_DIR}
```
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 迁移报告已生成: {report_path}")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("YL-Monitor 项目结构优化工具")
    print("=" * 60)
    
    # 1. 备份项目
    backup_project()
    
    # 2. 创建新目录结构
    create_directory_structure()
    
    # 3. 创建合并脚本框架
    create_merged_scripts()
    
    # 4. 生成迁移报告
    generate_migration_report()
    
    print("\n" + "=" * 60)
    print("优化准备完成！")
    print("=" * 60)
    print(f"\n📦 备份位置: {BACKUP_DIR}")
    print("📄 迁移报告: docs/MIGRATION_REPORT.md")
    print("\n下一步:")
    print("1. 查看迁移报告了解变更详情")
    print("2. 实现合并脚本的具体逻辑")
    print("3. 测试新脚本功能")
    print("4. 删除旧脚本")


if __name__ == "__main__":
    main()
