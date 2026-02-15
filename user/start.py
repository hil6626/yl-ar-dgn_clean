#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR Live Studio 启动脚本 (跨平台)
支持 Windows, Linux, macOS
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """检查依赖包"""
    required = {
        'PyQt5': 'PyQt5',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'psutil': 'psutil',
        'requests': 'requests',
        'flask': 'flask',
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} (未安装)")
    
    if missing:
        print(f"\n缺少以下依赖包: {', '.join(missing)}")
        response = input("是否自动安装? (y/n): ")
        if response.lower() == 'y':
            print("正在安装依赖...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("✓ 依赖安装完成")
        else:
            print("错误: 缺少必要依赖，无法启动")
            return False
    
    return True


def setup_environment():
    """设置环境变量"""
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    # 设置PYTHONPATH
    paths = [
        str(script_dir),
        str(project_root),
        str(project_root / 'AR-backend'),
        str(project_root / 'AR-backend' / 'core'),
    ]
    
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_pythonpath = os.pathsep.join(paths)
    
    if current_pythonpath:
        new_pythonpath = new_pythonpath + os.pathsep + current_pythonpath
    
    os.environ['PYTHONPATH'] = new_pythonpath
    os.environ['PROJECT_ROOT'] = str(project_root)
    
    print(f"✓ 环境变量已设置")
    print(f"  PROJECT_ROOT: {project_root}")
    
    return True


def create_directories():
    """创建必要的目录"""
    dirs = ['logs', 'config', 'cache', 'temp']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print(f"✓ 目录结构已创建")


def check_ar_backend():
    """检查AR-backend目录"""
    script_dir = Path(__file__).parent.resolve()
    ar_backend = script_dir.parent / 'AR-backend'
    
    if not ar_backend.exists():
        print(f"错误: 未找到AR-backend目录")
        print(f"  期望路径: {ar_backend}")
        return False
    
    print(f"✓ AR-backend目录已找到")
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("  AR Live Studio 启动脚本")
    print("=" * 50)
    print()
    
    # 检查Python版本
    print("[*] 检查Python环境...")
    if not check_python_version():
        sys.exit(1)
    
    # 检查依赖
    print("\n[*] 检查依赖...")
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    print("\n[*] 设置环境...")
    if not setup_environment():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 检查AR-backend
    print("\n[*] 检查项目结构...")
    if not check_ar_backend():
        sys.exit(1)
    
    # 启动应用
    print("\n" + "=" * 50)
    print("  启动 AR Live Studio")
    print("=" * 50)
    print()
    
    try:
        import main
        main.main()
    except Exception as e:
        print(f"\n错误: 启动失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
