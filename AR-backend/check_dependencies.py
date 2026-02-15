#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR-backend 依赖检查和自动安装脚本
检查所有必要的依赖项，并提供自动安装功能

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import sys
import subprocess
import importlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DependencyChecker:
    """依赖检查器类"""
    
    def __init__(self):
        self.checks = []
        self.missing = []
        self.installed = []
        
    def check_python_package(self, package_name: str, import_name: Optional[str] = None, 
                           min_version: Optional[str] = None) -> bool:
        """
        检查Python包是否已安装
        
        Args:
            package_name: pip包名
            import_name: 导入名（如果与包名不同）
            min_version: 最低版本要求
            
        Returns:
            bool: 是否已安装且满足版本要求
        """
        import_name = import_name or package_name
        
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            
            if min_version and version != 'unknown':
                # 简单版本比较
                if self._version_compare(version, min_version) < 0:
                    logger.warning(f"⚠️  {package_name} 版本过低: {version} < {min_version}")
                    self.missing.append({
                        'name': package_name,
                        'type': 'python',
                        'reason': f'版本过低: {version} < {min_version}',
                        'current_version': version,
                        'required_version': min_version
                    })
                    return False
            
            logger.info(f"✅ {package_name} ({version})")
            self.installed.append({
                'name': package_name,
                'type': 'python',
                'version': version
            })
            return True
            
        except ImportError:
            logger.error(f"❌ {package_name} 未安装")
            self.missing.append({
                'name': package_name,
                'type': 'python',
                'reason': '未安装'
            })
            return False
    
    def check_system_command(self, command: str, args: List[str] = None,
                           check_string: Optional[str] = None) -> bool:
        """
        检查系统命令是否可用
        
        Args:
            command: 命令名
            args: 检查时使用的参数
            check_string: 输出中应包含的字符串
            
        Returns:
            bool: 命令是否可用
        """
        args = args or ['--version']
        
        try:
            result = subprocess.run(
                [command] + args,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                if check_string and check_string not in output:
                    logger.warning(f"⚠️  {command} 输出异常")
                    return False
                
                # 提取版本信息
                version = self._extract_version(output)
                logger.info(f"✅ {command} ({version})")
                self.installed.append({
                    'name': command,
                    'type': 'system',
                    'version': version
                })
                return True
            else:
                logger.error(f"❌ {command} 返回错误码: {result.returncode}")
                self.missing.append({
                    'name': command,
                    'type': 'system',
                    'reason': f'返回错误码: {result.returncode}'
                })
                return False
                
        except FileNotFoundError:
            logger.error(f"❌ {command} 未找到")
            self.missing.append({
                'name': command,
                'type': 'system',
                'reason': '命令未找到'
            })
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {command} 检查超时")
            self.missing.append({
                'name': command,
                'type': 'system',
                'reason': '检查超时'
            })
            return False
    
    def check_file_exists(self, file_path: str, description: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            description: 文件描述
            
        Returns:
            bool: 文件是否存在
        """
        path = Path(file_path)
        if path.exists():
            logger.info(f"✅ {description}: {file_path}")
            self.installed.append({
                'name': description,
                'type': 'file',
                'path': str(path)
            })
            return True
        else:
            logger.error(f"❌ {description} 不存在: {file_path}")
            self.missing.append({
                'name': description,
                'type': 'file',
                'reason': f'文件不存在: {file_path}'
            })
            return False
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """比较两个版本号"""
        def normalize(v):
            return [int(x) for x in v.split('.') if x.isdigit()]
        
        try:
            n1 = normalize(v1)
            n2 = normalize(v2)
            
            if n1 > n2:
                return 1
            elif n1 < n2:
                return -1
            else:
                return 0
        except:
            return 0
    
    def _extract_version(self, output: str) -> str:
        """从命令输出中提取版本号"""
        import re
        # 常见版本格式: x.x.x, x.x, vx.x.x
        patterns = [
            r'(\d+\.\d+\.\d+)',
            r'(\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return 'unknown'
    
    def install_python_package(self, package_name: str) -> bool:
        """
        安装Python包
        
        Args:
            package_name: 包名
            
        Returns:
            bool: 安装是否成功
        """
        logger.info(f"📦 正在安装 {package_name}...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {package_name} 安装成功")
                return True
            else:
                logger.error(f"❌ {package_name} 安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {package_name} 安装异常: {e}")
            return False
    
    def get_install_command(self, item: Dict) -> Optional[str]:
        """
        获取安装命令建议
        
        Args:
            item: 缺失的依赖项
            
        Returns:
            Optional[str]: 安装命令
        """
        install_commands = {
            'opencv-python': 'pip install opencv-python',
            'numpy': 'pip install numpy',
            'PyQt5': 'pip install PyQt5',
            'psutil': 'pip install psutil',
            'dlib': 'pip install dlib (需要cmake)',
            'sox': 'sudo apt-get install sox (Ubuntu/Debian)',
            'v4l2loopback': 'sudo apt-get install v4l2loopback-dkms',
            'arecord': 'sudo apt-get install alsa-utils',
            'aplay': 'sudo apt-get install alsa-utils',
        }
        
        return install_commands.get(item['name'])


def check_all_dependencies(auto_install: bool = False) -> bool:
    """
    检查所有依赖
    
    Args:
        auto_install: 是否自动安装缺失的Python包
        
    Returns:
        bool: 所有依赖是否满足
    """
    checker = DependencyChecker()
    
    logger.info("=" * 60)
    logger.info("AR-backend 依赖检查")
    logger.info("=" * 60)
    
    # 1. 检查核心Python包
    logger.info("\n📦 检查核心Python包...")
    core_packages = [
        ('opencv-python', 'cv2', '4.5.0'),
        ('numpy', 'numpy', '1.20.0'),
        ('PyQt5', 'PyQt5', '5.15.0'),
        ('psutil', 'psutil', '5.8.0'),
    ]
    
    for package, import_name, min_version in core_packages:
        checker.check_python_package(package, import_name, min_version)
    
    # 2. 检查可选Python包
    logger.info("\n📦 检查可选Python包...")
    optional_packages = [
        ('dlib', 'dlib', None),  # 用于关键点检测
    ]
    
    for package, import_name, min_version in optional_packages:
        checker.check_python_package(package, import_name, min_version)
    
    # 3. 检查系统命令
    logger.info("\n🔧 检查系统命令...")
    system_commands = [
        ('sox', ['--version'], 'SoX'),
        ('arecord', ['-l'], None),
        ('aplay', ['-l'], None),
    ]
    
    for command, args, check_string in system_commands:
        checker.check_system_command(command, args, check_string)
    
    # 4. 检查模型文件
    logger.info("\n📁 检查模型文件...")
    model_files = [
        ('AR-backend/models/deploy.prototxt', 'DNN人脸检测配置'),
        ('AR-backend/models/res10_300x300_ssd_iter_140000.caffemodel', 'DNN人脸检测模型'),
        ('AR-backend/models/shape_predictor_68_face_landmarks.dat', 'Dlib关键点模型(可选)'),
    ]
    
    for file_path, description in model_files:
        checker.check_file_exists(file_path, description)
    
    # 5. 检查硬件
    logger.info("\n🎥 检查视频设备...")
    try:
        import cv2
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                logger.info(f"✅ 摄像头设备 /dev/video{i} 可用")
                cap.release()
            else:
                logger.warning(f"⚠️  摄像头设备 /dev/video{i} 不可用")
    except Exception as e:
        logger.error(f"❌ 摄像头检查失败: {e}")
    
    # 6. 检查虚拟摄像头模块
    logger.info("\n📹 检查虚拟摄像头...")
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        if 'v4l2loopback' in result.stdout:
            logger.info("✅ v4l2loopback 模块已加载")
        else:
            logger.warning("⚠️  v4l2loopback 模块未加载")
            checker.missing.append({
                'name': 'v4l2loopback',
                'type': 'kernel_module',
                'reason': '内核模块未加载'
            })
    except Exception as e:
        logger.error(f"❌ 无法检查v4l2loopback: {e}")
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("检查总结")
    logger.info("=" * 60)
    
    total = len(checker.installed) + len(checker.missing)
    logger.info(f"总计: {total} 项检查")
    logger.info(f"✅ 通过: {len(checker.installed)} 项")
    logger.info(f"❌ 缺失: {len(checker.missing)} 项")
    
    if checker.missing:
        logger.info("\n缺失的依赖:")
        for item in checker.missing:
            logger.info(f"  - {item['name']}: {item['reason']}")
            install_cmd = checker.get_install_command(item)
            if install_cmd:
                logger.info(f"    安装命令: {install_cmd}")
        
        # 自动安装
        if auto_install:
            logger.info("\n🔄 尝试自动安装...")
            python_packages = [item['name'] for item in checker.missing 
                            if item['type'] == 'python']
            
            for package in python_packages:
                checker.install_python_package(package)
            
            # 重新检查
            logger.info("\n🔄 重新检查...")
            return check_all_dependencies(auto_install=False)
        
        return False
    else:
        logger.info("\n🎉 所有依赖已满足！")
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AR-backend 依赖检查')
    parser.add_argument('--auto-install', action='store_true',
                       help='自动安装缺失的Python包')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='静默模式，只输出结果')
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    success = check_all_dependencies(auto_install=args.auto_install)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
