#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本 - Environment Checker
执行基础的运行环境检查 (目录、权限、配置文件、端口等)

用法:
    python env_check.py --quick
    python env_check.py --full --report

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import argparse
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).parent.parent.parent
REQUIRED_DIRS = ['logs', 'data', 'config', 'src']
REQUIRED_PORTS = [5000]


def check_directories() -> Dict:
    results = {}
    for d in REQUIRED_DIRS:
        p = BASE_DIR / d
        results[d] = {
            'exists': p.exists(),
            'is_dir': p.is_dir() if p.exists() else False,
            'writable': os.access(p, os.W_OK) if p.exists() else False
        }
    return results


def check_ports() -> Dict:
    results = {}
    for port in REQUIRED_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('0.0.0.0', port))
            s.close()
            results[port] = {'available': True}
        except OSError:
            results[port] = {'available': False}
    return results


def check_config_files() -> Dict:
    cfg_dir = BASE_DIR / 'config'
    results = {}
    if cfg_dir.exists():
        for f in cfg_dir.glob('*.json'):
            try:
                import json as _json
                with open(f, 'r', encoding='utf-8') as fh:
                    _json.load(fh)
                results[f.name] = {'valid_json': True}
            except Exception as e:
                results[f.name] = {'valid_json': False, 'error': str(e)}
    return results


def quick_check() -> Dict:
    return {
        'time': datetime.now().isoformat(),
        'dirs': check_directories(),
        'ports': check_ports()
    }


def full_check() -> Dict:
    return {
        'time': datetime.now().isoformat(),
        'dirs': check_directories(),
        'ports': check_ports(),
        'configs': check_config_files()
    }


def main():
    parser = argparse.ArgumentParser(description='环境检查工具')
    parser.add_argument('--quick', action='store_true', help='快速检查目录和端口')
    parser.add_argument('--full', action='store_true', help='完整检查，包括配置文件')
    parser.add_argument('--report', action='store_true', help='输出 JSON 报告')
    args = parser.parse_args()

    if args.full:
        result = full_check()
    else:
        result = quick_check()

    if args.report:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本 - Environment Check Script
检查系统运行环境和依赖

功能:
- 检查Python版本和依赖包
- 检查系统工具和命令
- 检查文件权限和目录结构
- 生成环境报告

使用方法:
    python env_check.py --json             # JSON 输出模式
    python env_check.py --report           # 生成详细报告
    python env_check.py --check-permissions # 检查权限

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月10日
"""

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "env_check.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EnvironmentChecker:
    """环境检查器"""

    def __init__(self, verbose=False):
        self.base_dir = Path(__file__).parent.parent.parent
        self.verbose = verbose
        self.results = {
            'python': {},
            'system': {},
            'dependencies': {},
            'permissions': {},
            'directories': {},
            'overall_status': 'unknown'
        }

    def check_python_version(self):
        """检查Python版本"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        # 检查是否为推荐版本
        recommended = (3, 8, 0)
        is_recommended = version >= recommended

        result = {
            'version': version_str,
            'major': version.major,
            'minor': version.minor,
            'micro': version.micro,
            'is_recommended': is_recommended,
            'status': 'pass' if is_recommended else 'warning'
        }

        self.results['python'] = result
        if self.verbose:
            logger.info(f"Python版本检查完成: {version_str}")
        return result

    def check_system_info(self):
        """检查系统信息"""
        result = {
            'platform': platform.system(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'status': 'pass'
        }

        self.results['system'] = result
        if self.verbose:
            logger.info(f"系统信息检查完成: {result['platform']} {result['architecture']}")
        return result

    def check_dependencies(self):
        """检查Python依赖"""
        required_packages = [
            'flask', 'flask-socketio', 'flask-cors',
            'psutil', 'python-socketio', 'opencv-python',
            'numpy', 'pillow', 'requests'
        ]

        installed_packages = {}
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                installed_packages[package] = 'installed'
            except ImportError:
                installed_packages[package] = 'missing'
                missing_packages.append(package)

        result = {
            'required': required_packages,
            'installed': installed_packages,
            'missing': missing_packages,
            'status': 'pass' if not missing_packages else 'fail'
        }

        self.results['dependencies'] = result
        if self.verbose:
            logger.info(f"依赖检查完成: {len(missing_packages)} 个缺失")
        return result

    def check_system_tools(self):
        """检查系统工具"""
        tools = ['python3', 'pip3', 'git', 'curl', 'wget']
        tool_status = {}

        for tool in tools:
            try:
                result = subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                tool_status[tool] = 'available' if result.returncode == 0 else 'unavailable'
            except (subprocess.TimeoutExpired, FileNotFoundError):
                tool_status[tool] = 'unavailable'

        result = {
            'tools': tool_status,
            'status': 'pass' if all(s == 'available' for s in tool_status.values()) else 'warning'
        }

        self.results['system_tools'] = result
        if self.verbose:
            unavailable = [t for t, s in tool_status.items() if s == 'unavailable']
            if unavailable:
                logger.warning(f"不可用的工具: {', '.join(unavailable)}")
        return result

    def check_permissions(self):
        """检查文件权限"""
        critical_paths = [
            self.base_dir / 'logs',
            self.base_dir / 'data',
            self.base_dir / 'config',
            self.base_dir / 'scripts'
        ]

        permissions = {}
        issues = []

        for path in critical_paths:
            if path.exists():
                # 检查写入权限
                try:
                    test_file = path / '.permission_test'
                    test_file.write_text('test')
                    test_file.unlink()
                    permissions[str(path)] = 'writable'
                except (OSError, PermissionError):
                    permissions[str(path)] = 'read-only'
                    issues.append(f"无写入权限: {path}")
            else:
                permissions[str(path)] = 'not_exists'
                issues.append(f"目录不存在: {path}")

        result = {
            'permissions': permissions,
            'issues': issues,
            'status': 'pass' if not issues else 'fail'
        }

        self.results['permissions'] = result
        if self.verbose:
            if issues:
                logger.error(f"权限问题: {', '.join(issues)}")
        return result

    def check_directories(self):
        """检查目录结构"""
        required_dirs = [
            'logs', 'data', 'config', 'scripts',
            'src', 'src/backend', 'src/frontend',
            'test', 'docs'
        ]

        dir_status = {}
        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                dir_status[dir_name] = 'exists'
            else:
                dir_status[dir_name] = 'missing'
                missing_dirs.append(dir_name)

        result = {
            'directories': dir_status,
            'missing': missing_dirs,
            'status': 'pass' if not missing_dirs else 'warning'
        }

        self.results['directories'] = result
        if self.verbose:
            if missing_dirs:
                logger.warning(f"缺失的目录: {', '.join(missing_dirs)}")
        return result

    def run_all_checks(self):
        """运行所有检查"""
        if self.verbose:
            logger.info("开始环境检查...")

        self.check_python_version()
        if self.verbose:
            logger.info("✓ Python版本检查完成")

        self.check_system_info()
        if self.verbose:
            logger.info("✓ 系统信息检查完成")

        self.check_dependencies()
        if self.verbose:
            logger.info("✓ 依赖包检查完成")

        self.check_system_tools()
        if self.verbose:
            logger.info("✓ 系统工具检查完成")

        self.check_permissions()
        if self.verbose:
            logger.info("✓ 权限检查完成")

        self.check_directories()
        if self.verbose:
            logger.info("✓ 目录结构检查完成")

        # 计算总体状态
        statuses = [check['status'] for check in self.results.values() if isinstance(check, dict) and 'status' in check]
        if 'fail' in statuses:
            overall_status = 'fail'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'pass'

        self.results['overall_status'] = overall_status
        self.results['timestamp'] = datetime.now().isoformat()

        if self.verbose:
            logger.info(f"环境检查完成，总体状态: {overall_status}")
        return self.results

    def print_report(self):
        """打印检查报告"""
        print("\n" + "="*50)
        print("环境检查报告")
        print("="*50)

        print(f"总体状态: {self.results['overall_status'].upper()}")

        print("\nPython版本:")
        py = self.results['python']
        print(f"  版本: {py['version']}")
        print(f"  推荐版本: {'是' if py['is_recommended'] else '否'}")

        print("\n系统信息:")
        sys_info = self.results['system']
        print(f"  平台: {sys_info['platform']}")
        print(f"  架构: {sys_info['architecture']}")

        print("\n依赖包:")
        deps = self.results['dependencies']
        print(f"  缺失包: {', '.join(deps['missing']) if deps['missing'] else '无'}")

        print("\n权限检查:")
        perm = self.results['permissions']
        if perm['issues']:
            for issue in perm['issues']:
                print(f"  ⚠ {issue}")
        else:
            print("  ✓ 所有权限正常")

        print("\n目录结构:")
        dirs = self.results['directories']
        if dirs['missing']:
            for missing in dirs['missing']:
                print(f"  ⚠ 缺失目录: {missing}")
        else:
            print("  ✓ 目录结构完整")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='环境检查脚本')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    parser.add_argument('--report', action='store_true', help='生成详细报告')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--check-permissions', action='store_true', help='仅检查权限')

    args = parser.parse_args()

    checker = EnvironmentChecker(verbose=args.verbose)
    
    if args.check_permissions:
        result = checker.check_permissions()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            status_icon = {'pass': '✓', 'fail': '✗', 'warning': '⚠'}.get(result['status'], '?')
            print(f"{status_icon} 权限检查完成 - 状态: {result['status']}")
    else:
        results = checker.run_all_checks()
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        elif args.report:
            checker.print_report()
        else:
            # 默认输出简要信息
            status = results['overall_status']
            status_icon = {'pass': '✓', 'warning': '⚠', 'fail': '✗'}.get(status, '?')
            print(f"{status_icon} 环境检查完成 - 状态: {status}")


if __name__ == '__main__':
    main()
