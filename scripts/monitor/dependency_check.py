#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查脚本 - Dependency Checker
检查 Python 和系统依赖是否满足要求

功能:
- 检查 Python 包依赖
- 检查系统工具依赖
- 检查 GPU 依赖 (CUDA, cuDNN)
- 自动生成依赖报告

使用方法:
    python dependency_check.py --check            # 检查所有依赖
    python dependency_check.py --python           # 只检查 Python 依赖
    python dependency_check.py --system           # 只检查系统依赖
    python dependency_check.py --gpu              # 只检查 GPU 依赖
    python dependency_check.py --report           # 生成报告

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 配置路径
BASE_DIR = Path(__file__).parent.parent.parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)


class DependencyChecker:
    """依赖检查器"""
    
    # Python 依赖列表
    PYTHON_PACKAGES = {
        'flask': {'min_version': '2.0.0', 'optional': False},
        'flask-socketio': {'min_version': '5.0.0', 'optional': False},
        'flask-cors': {'min_version': '3.0.0', 'optional': False},
        'psutil': {'min_version': '5.8.0', 'optional': False},
        'opencv-python': {'min_version': '4.5.0', 'optional': True},
        'numpy': {'min_version': '1.20.0', 'optional': False},
        'requests': {'min_version': '2.25.0', 'optional': False},
        'pillow': {'min_version': '8.0.0', 'optional': True},
        'torch': {'min_version': '1.9.0', 'optional': True},
        'torchvision': {'min_version': '0.10.0', 'optional': True},
        'tensorflow': {'min_version': '2.5.0', 'optional': True},
        'transformers': {'min_version': '4.0.0', 'optional': True},
    }
    
    # 系统工具依赖
    SYSTEM_TOOLS = {
        'python3': {'min_version': '3.8', 'optional': False},
        'ffmpeg': {'min_version': '4.0', 'optional': False},
        'sox': {'min_version': '14.4', 'optional': False},
        'git': {'min_version': '2.0', 'optional': False},
        'curl': {'min_version': '7.0', 'optional': False},
        'docker': {'min_version': '20.0', 'optional': True},
        'nvidia-smi': {'min_version': None, 'optional': True},
    }
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'python_packages': {},
            'system_tools': {},
            'gpu_info': {},
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def check_python_packages(self) -> Dict[str, Dict]:
        """检查 Python 包依赖"""
        print("🔍 检查 Python 依赖...")
        
        results = {}
        
        for package, info in self.PYTHON_PACKAGES.items():
            check_result = {
                'name': package,
                'installed': False,
                'version': None,
                'meets_requirement': False,
                'optional': info['optional'],
                'error': None
            }
            
            try:
                # 尝试导入包并获取版本
                import importlib
                
                # 特殊处理一些包名和导入名不一致的情况
                import_name = package.replace('-', '_')
                
                # 尝试获取版本
                try:
                    pkg = importlib.import_module(import_name)
                    version = getattr(pkg, '__version__', None)
                    
                    if version is None:
                        # 尝试使用 pkg_resources
                        import pkg_resources
                        version = pkg_resources.get_distribution(package).version
                    
                    check_result['version'] = version
                    check_result['installed'] = True
                    
                    # 检查版本要求
                    if info['min_version']:
                        check_result['meets_requirement'] = self._compare_versions(
                            version, info['min_version']
                        )
                    else:
                        check_result['meets_requirement'] = True
                        
                except ImportError:
                    check_result['installed'] = False
                    check_result['meets_requirement'] = not info['optional']
            
            except Exception as e:
                check_result['error'] = str(e)
                check_result['meets_requirement'] = not info['optional']
            
            results[package] = check_result
            
            # 输出检查结果
            if check_result['installed']:
                status = '✅' if check_result['meets_requirement'] else '⚠️'
                print(f"   {status} {package}: {check_result['version']}")
            else:
                status = '❌' if not check_result['optional'] else '⚠️'
                print(f"   {status} {package}: 未安装")
        
        self.results['python_packages'] = results
        return results
    
    def check_system_tools(self) -> Dict[str, Dict]:
        """检查系统工具依赖"""
        print("\n🔍 检查系统工具...")
        
        results = {}
        
        for tool, info in self.SYSTEM_TOOLS.items():
            check_result = {
                'name': tool,
                'installed': False,
                'version': None,
                'meets_requirement': False,
                'optional': info['optional'],
                'error': None
            }
            
            try:
                # 使用 which 或 whereis 检查命令是否存在
                try:
                    subprocess.run(
                        ['which', tool],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    check_result['installed'] = True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # 尝试 Windows 命令
                    try:
                        subprocess.run(
                            ['where', tool],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        check_result['installed'] = True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        check_result['installed'] = False
                
                # 如果安装了，获取版本
                if check_result['installed']:
                    try:
                        result = subprocess.run(
                            [tool, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        # 解析版本号
                        version_output = result.stdout or result.stderr
                        version = self._extract_version(version_output, tool)
                        check_result['version'] = version
                        
                        # 检查版本要求
                        if info['min_version']:
                            check_result['meets_requirement'] = self._compare_versions(
                                version, info['min_version']
                            )
                        else:
                            check_result['meets_requirement'] = True
                            
                    except Exception as e:
                        check_result['meets_requirement'] = True  # 安装了但无法获取版本
                
            except Exception as e:
                check_result['error'] = str(e)
            
            results[tool] = check_result
            
            # 输出检查结果
            if check_result['installed']:
                status = '✅' if check_result['meets_requirement'] else '⚠️'
                version_str = f" ({check_result['version']})" if check_result['version'] else ""
                print(f"   {status} {tool}: 已安装{version_str}")
            else:
                status = '❌' if not check_result['optional'] else '⚠️'
                print(f"   {status} {tool}: 未安装")
        
        self.results['system_tools'] = results
        return results
    
    def check_gpu(self) -> Dict:
        """检查 GPU 环境"""
        print("\n🔍 检查 GPU 环境...")
        
        gpu_info = {
            'available': False,
            'cuda_available': False,
            'driver_version': None,
            'cuda_version': None,
            'gpus': [],
            'error': None
        }
        
        try:
            # 检查 nvidia-smi
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total,driver_version,cuda_version', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    gpu_info['available'] = True
                    gpu_info['driver_version'] = self._extract_version(result.stdout, 'nvidia')
                    
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 3:
                                gpu_info['gpus'].append({
                                    'name': parts[0],
                                    'memory': parts[1] if len(parts) > 1 else 'Unknown',
                                    'driver': parts[2] if len(parts) > 2 else 'Unknown',
                                    'cuda': parts[3] if len(parts) > 3 else 'Unknown'
                                })
                                gpu_info['cuda_version'] = parts[3] if len(parts) > 3 else None
                    
                    gpu_info['cuda_available'] = True
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # 检查 Python CUDA 库
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info['cuda_available'] = True
                    gpu_info['cuda_version'] = torch.version.cuda
                    
                    for i in range(torch.cuda.device_count()):
                        gpu_info['gpus'].append({
                            'name': torch.cuda.get_device_name(i),
                            'memory': f"{torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB",
                            'index': i
                        })
                    
                    if not gpu_info['available']:
                        gpu_info['available'] = True
                        
            except ImportError:
                pass
            
            # 输出检查结果
            if gpu_info['available']:
                print(f"   ✅ GPU 检测成功:")
                for gpu in gpu_info['gpus']:
                    print(f"      - {gpu['name']} ({gpu.get('memory', 'N/A')})")
                if gpu_info['cuda_version']:
                    print(f"      CUDA 版本: {gpu_info['cuda_version']}")
            else:
                print("   ⚠️  未检测到 GPU (可选)")
            
        except Exception as e:
            gpu_info['error'] = str(e)
            print(f"   ❌ GPU 检查失败: {e}")
        
        self.results['gpu_info'] = gpu_info
        return gpu_info
    
    def check_all(self) -> Dict:
        """执行所有检查"""
        print("=" * 60)
        print("依赖检查")
        print("=" * 60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.check_python_packages()
        self.check_system_tools()
        self.check_gpu()
        
        # 计算统计
        self._calculate_summary()
        
        return self.results
    
    def _calculate_summary(self):
        """计算检查统计"""
        summary = self.results['summary']
        summary['total_checks'] = 0
        summary['passed'] = 0
        summary['failed'] = 0
        summary['warnings'] = 0
        
        # Python 包统计
        for package, result in self.results['python_packages'].items():
            summary['total_checks'] += 1
            if result['installed'] and result['meets_requirement']:
                summary['passed'] += 1
            elif result['installed']:
                summary['warnings'] += 1
            elif result['optional']:
                summary['warnings'] += 1
            else:
                summary['failed'] += 1
        
        # 系统工具统计
        for tool, result in self.results['system_tools'].items():
            summary['total_checks'] += 1
            if result['installed'] and result['meets_requirement']:
                summary['passed'] += 1
            elif result['installed']:
                summary['warnings'] += 1
            elif result['optional']:
                summary['warnings'] += 1
            else:
                summary['failed'] += 1
        
        # GPU 统计
        if self.results['gpu_info']['available']:
            summary['passed'] += 1
        else:
            summary['warnings'] += 1
        
        summary['total_checks'] += 1
    
    def _compare_versions(self, version1: Optional[str], version2: Optional[str]) -> bool:
        """比较版本号"""
        try:
            if not version1 or not version2:
                return True
            
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # 补齐长度
            while len(v1_parts) < len(v2_parts):
                v1_parts.append(0)
            while len(v2_parts) < len(v1_parts):
                v2_parts.append(0)
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 < v2:
                    return False
                elif v1 > v2:
                    return True
            
            return True
        except:
            return True  # 无法比较时默认通过
    
    def _extract_version(self, output: str, tool: str) -> Optional[str]:
        """从命令输出中提取版本号"""
        if not output:
            return None
        
        # 常见版本号模式
        import re
        
        patterns = [
            r'(\d+\.\d+\.\d+)',  # x.y.z
            r'(\d+\.\d+)',        # x.y
            r'(\d+)',             # x
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return None
    
    def format_report_console(self):
        """控制台输出报告"""
        self.check_all()
        
        summary = self.results['summary']
        
        print("\n" + "=" * 60)
        print("依赖检查报告")
        print("=" * 60)
        print(f"检查时间: {self.results['timestamp']}")
        print("-" * 60)
        print(f"总检查项: {summary['total_checks']}")
        print(f"✅ 通过: {summary['passed']}")
        print(f"⚠️  警告: {summary['warnings']}")
        print(f"❌ 失败: {summary['failed']}")
        print("=" * 60)
        
        if summary['failed'] > 0:
            print("\n❌ 未通过的必要依赖:")
            for package, result in self.results['python_packages'].items():
                if not result['optional'] and (not result['installed'] or not result['meets_requirement']):
                    print(f"   - {package}")
            
            for tool, result in self.results['system_tools'].items():
                if not result['optional'] and not result['installed']:
                    print(f"   - {tool}")
        
        if summary['warnings'] > 0:
            print("\n⚠️  可选依赖建议:")
            for package, result in self.results['python_packages'].items():
                if result['optional'] and not result['installed']:
                    print(f"   - {package} (推荐安装以获得完整功能)")
            
            for tool, result in self.results['system_tools'].items():
                if result['optional'] and not result['installed']:
                    print(f"   - {tool} (可选)")
        
        print("\n" + "=" * 60)
    
    def save_report(self, filepath: str = "") -> str:
        """保存报告到文件"""
        if not filepath:
            filepath = str(REPORT_DIR / f"dependency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description='依赖检查脚本 - 检查项目依赖',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--check', '-a', action='store_true',
                        help='检查所有依赖')
    parser.add_argument('--python', '-p', action='store_true',
                        help='只检查 Python 依赖')
    parser.add_argument('--system', '-s', action='store_true',
                        help='只检查系统工具依赖')
    parser.add_argument('--gpu', '-g', action='store_true',
                        help='只检查 GPU 依赖')
    parser.add_argument('--report', '-r', action='store_true',
                        help='生成并保存报告')
    parser.add_argument('--json', '-j', action='store_true',
                        help='JSON 格式输出')
    parser.add_argument('--output', '-o', type=str, default="",
                        help='报告输出路径')
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    try:
        if args.python:
            checker.check_python_packages()
            results = {'python_packages': checker.results['python_packages']}
        
        elif args.system:
            checker.check_system_tools()
            results = {'system_tools': checker.results['system_tools']}
        
        elif args.gpu:
            checker.check_gpu()
            results = {'gpu_info': checker.results['gpu_info']}
        
        elif args.check or args.report:
            checker.check_all()
            results = checker.results
            
            if args.report:
                filepath = checker.save_report(args.output)
                print(f"\n📄 报告已保存到: {filepath}")
        
        else:
            # 默认执行所有检查
            checker.format_report_console()
            results = None
        
        # 输出 JSON 结果
        if args.json and results:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        
        elif not (args.python or args.system or args.gpu or args.check or args.report):
            checker.format_report_console()
    
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查脚本 - Dependency Checker
检查 Python 和系统依赖是否满足要求

功能:
- 检查 Python 包依赖
- 检查系统工具依赖
- 检查 GPU 依赖 (CUDA, cuDNN)
- 自动生成依赖报告

使用方法:
    python dependency_check.py --check            # 检查所有依赖
    python dependency_check.py --python           # 只检查 Python 依赖
    python dependency_check.py --system           # 只检查系统依赖
    python dependency_check.py --gpu              # 只检查 GPU 依赖
    python dependency_check.py --report           # 生成报告

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 配置路径
BASE_DIR = Path(__file__).parent.parent.parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)


class DependencyChecker:
    """依赖检查器"""
    
    # Python 依赖列表
    PYTHON_PACKAGES = {
        'flask': {'min_version': '2.0.0', 'optional': False},
        'flask-socketio': {'min_version': '5.0.0', 'optional': False},
        'flask-cors': {'min_version': '3.0.0', 'optional': False},
        'psutil': {'min_version': '5.8.0', 'optional': False},
        'opencv-python': {'min_version': '4.5.0', 'optional': True},
        'numpy': {'min_version': '1.20.0', 'optional': False},
        'requests': {'min_version': '2.25.0', 'optional': False},
        'pillow': {'min_version': '8.0.0', 'optional': True},
        'torch': {'min_version': '1.9.0', 'optional': True},
        'torchvision': {'min_version': '0.10.0', 'optional': True},
        'tensorflow': {'min_version': '2.5.0', 'optional': True},
        'transformers': {'min_version': '4.0.0', 'optional': True},
    }
    
    # 系统工具依赖
    SYSTEM_TOOLS = {
        'python3': {'min_version': '3.8', 'optional': False},
        'ffmpeg': {'min_version': '4.0', 'optional': False},
        'sox': {'min_version': '14.4', 'optional': False},
        'git': {'min_version': '2.0', 'optional': False},
        'curl': {'min_version': '7.0', 'optional': False},
        'docker': {'min_version': '20.0', 'optional': True},
        'nvidia-smi': {'min_version': None, 'optional': True},
    }
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'python_packages': {},
            'system_tools': {},
            'gpu_info': {},
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def check_python_packages(self) -> Dict[str, Dict]:
        """检查 Python 包依赖"""
        print("🔍 检查 Python 依赖...")
        
        results = {}
        
        for package, info in self.PYTHON_PACKAGES.items():
            check_result = {
                'name': package,
                'installed': False,
                'version': None,
                'meets_requirement': False,
                'optional': info['optional'],
                'error': None
            }
            
            try:
                # 尝试导入包并获取版本
                import importlib
                
                # 特殊处理一些包名和导入名不一致的情况
                import_name = package.replace('-', '_')
                
                # 尝试获取版本
                try:
                    pkg = importlib.import_module(import_name)
                    version = getattr(pkg, '__version__', None)
                    
                    if version is None:
                        # 尝试使用 pkg_resources
                        import pkg_resources
                        version = pkg_resources.get_distribution(package).version
                    
                    check_result['version'] = version
                    check_result['installed'] = True
                    
                    # 检查版本要求
                    if info['min_version']:
                        check_result['meets_requirement'] = self._compare_versions(
                            version, info['min_version']
                        )
                    else:
                        check_result['meets_requirement'] = True
                        
                except ImportError:
                    check_result['installed'] = False
                    check_result['meets_requirement'] = not info['optional']
            
            except Exception as e:
                check_result['error'] = str(e)
                check_result['meets_requirement'] = not info['optional']
            
            results[package] = check_result
            
            # 输出检查结果
            if check_result['installed']:
                status = '✅' if check_result['meets_requirement'] else '⚠️'
                print(f"   {status} {package}: {check_result['version']}")
            else:
                status = '❌' if not check_result['optional'] else '⚠️'
                print(f"   {status} {package}: 未安装")
        
        self.results['python_packages'] = results
        return results
    
    def check_system_tools(self) -> Dict[str, Dict]:
        """检查系统工具依赖"""
        print("\n🔍 检查系统工具...")
        
        results = {}
        
        for tool, info in self.SYSTEM_TOOLS.items():
            check_result = {
                'name': tool,
                'installed': False,
                'version': None,
                'meets_requirement': False,
                'optional': info['optional'],
                'error': None
            }
            
            try:
                # 使用 which 或 whereis 检查命令是否存在
                try:
                    subprocess.run(
                        ['which', tool],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    check_result['installed'] = True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # 尝试 Windows 命令
                    try:
                        subprocess.run(
                            ['where', tool],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        check_result['installed'] = True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        check_result['installed'] = False
                
                # 如果安装了，获取版本
                if check_result['installed']:
                    try:
                        result = subprocess.run(
                            [tool, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        # 解析版本号
                        version_output = result.stdout or result.stderr
                        version = self._extract_version(version_output, tool)
                        check_result['version'] = version
                        
                        # 检查版本要求
                        if info['min_version']:
                            check_result['meets_requirement'] = self._compare_versions(
                                version, info['min_version']
                            )
                        else:
                            check_result['meets_requirement'] = True
                            
                    except Exception as e:
                        check_result['meets_requirement'] = True  # 安装了但无法获取版本
                
            except Exception as e:
                check_result['error'] = str(e)
            
            results[tool] = check_result
            
            # 输出检查结果
            if check_result['installed']:
                status = '✅' if check_result['meets_requirement'] else '⚠️'
                version_str = f" ({check_result['version']})" if check_result['version'] else ""
                print(f"   {status} {tool}: 已安装{version_str}")
            else:
                status = '❌' if not check_result['optional'] else '⚠️'
                print(f"   {status} {tool}: 未安装")
        
        self.results['system_tools'] = results
        return results
    
    def check_gpu(self) -> Dict:
        """检查 GPU 环境"""
        print("\n🔍 检查 GPU 环境...")
        
        gpu_info = {
            'available': False,
            'cuda_available': False,
            'driver_version': None,
            'cuda_version': None,
            'gpus': [],
            'error': None
        }
        
        try:
            # 检查 nvidia-smi
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total,driver_version,cuda_version', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    gpu_info['available'] = True
                    gpu_info['driver_version'] = self._extract_version(result.stdout, 'nvidia')
                    
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 3:
                                gpu_info['gpus'].append({
                                    'name': parts[0],
                                    'memory': parts[1] if len(parts) > 1 else 'Unknown',
                                    'driver': parts[2] if len(parts) > 2 else 'Unknown',
                                    'cuda': parts[3] if len(parts) > 3 else 'Unknown'
                                })
                                gpu_info['cuda_version'] = parts[3] if len(parts) > 3 else None
                    
                    gpu_info['cuda_available'] = True
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # 检查 Python CUDA 库
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info['cuda_available'] = True
                    gpu_info['cuda_version'] = torch.version.cuda
                    
                    for i in range(torch.cuda.device_count()):
                        gpu_info['gpus'].append({
                            'name': torch.cuda.get_device_name(i),
                            'memory': f"{torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB",
                            'index': i
                        })
                    
                    if not gpu_info['available']:
                        gpu_info['available'] = True
                        
            except ImportError:
                pass
            
            # 输出检查结果
            if gpu_info['available']:
                print(f"   ✅ GPU 检测成功:")
                for gpu in gpu_info['gpus']:
                    print(f"      - {gpu['name']} ({gpu.get('memory', 'N/A')})")
                if gpu_info['cuda_version']:
                    print(f"      CUDA 版本: {gpu_info['cuda_version']}")
            else:
                print("   ⚠️  未检测到 GPU (可选)")
        
        except Exception as e:
            gpu_info['error'] = str(e)
            print(f"   ❌ GPU 检查失败: {e}")
        
        self.results['gpu_info'] = gpu_info
        return gpu_info
    
    def check_all(self) -> Dict:
        """执行所有检查"""
        print("=" * 60)
        print("依赖检查")
        print("=" * 60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.check_python_packages()
        self.check_system_tools()
        self.check_gpu()
        
        # 计算统计
        self._calculate_summary()
        
        return self.results
    
    def _calculate_summary(self):
        """计算检查统计"""
        summary = self.results['summary']
        summary['total_checks'] = 0
        summary['passed'] = 0
        summary['failed'] = 0
        summary['warnings'] = 0
        
        # Python 包统计
        for package, result in self.results['python_packages'].items():
            summary['total_checks'] += 1
            if result['installed'] and result['meets_requirement']:
                summary['passed'] += 1
            elif result['installed']:
                summary['warnings'] += 1
            elif result['optional']:
                summary['warnings'] += 1
            else:
                summary['failed'] += 1
        
        # 系统工具统计
        for tool, result in self.results['system_tools'].items():
            summary['total_checks'] += 1
            if result['installed'] and result['meets_requirement']:
                summary['passed'] += 1
            elif result['installed']:
                summary['warnings'] += 1
            elif result['optional']:
                summary['warnings'] += 1
            else:
                summary['failed'] += 1
        
        # GPU 统计
        if self.results['gpu_info']['available']:
            summary['passed'] += 1
        else:
            summary['warnings'] += 1
        
        summary['total_checks'] += 1
    
    def _compare_versions(self, version1: Optional[str], version2: Optional[str]) -> bool:
        """比较版本号"""
        try:
            if not version1 or not version2:
                return True
            
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # 补齐长度
            while len(v1_parts) < len(v2_parts):
                v1_parts.append(0)
            while len(v2_parts) < len(v1_parts):
                v2_parts.append(0)
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 < v2:
                    return False
                elif v1 > v2:
                    return True
            
            return True
        except:
            return True  # 无法比较时默认通过
    
    def _extract_version(self, output: str, tool: str) -> Optional[str]:
        """从命令输出中提取版本号"""
        if not output:
            return None
        
        # 常见版本号模式
        import re
        
        patterns = [
            r'(\d+\.\d+\.\d+)',  # x.y.z
            r'(\d+\.\d+)',        # x.y
            r'(\d+)',             # x
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return None
    
    def format_report_console(self):
        """控制台输出报告"""
        self.check_all()
        
        summary = self.results['summary']
        
        print("\n" + "=" * 60)
        print("依赖检查报告")
        print("=" * 60)
        print(f"检查时间: {self.results['timestamp']}")
        print("-" * 60)
        print(f"总检查项: {summary['total_checks']}")
        print(f"✅ 通过: {summary['passed']}")
        print(f"⚠️  警告: {summary['warnings']}")
        print(f"❌ 失败: {summary['failed']}")
        print("=" * 60)
        
        if summary['failed'] > 0:
            print("\n❌ 未通过的必要依赖:")
            for package, result in self.results['python_packages'].items():
                if not result['optional'] and (not result['installed'] or not result['meets_requirement']):
                    print(f"   - {package}")
            
            for tool, result in self.results['system_tools'].items():
                if not result['optional'] and not result['installed']:
                    print(f"   - {tool}")
        
        if summary['warnings'] > 0:
            print("\n⚠️  可选依赖建议:")
            for package, result in self.results['python_packages'].items():
                if result['optional'] and not result['installed']:
                    print(f"   - {package} (推荐安装以获得完整功能)")
            
            for tool, result in self.results['system_tools'].items():
                if result['optional'] and not result['installed']:
                    print(f"   - {tool} (可选)")
        
        print("\n" + "=" * 60)
    
    def save_report(self, filepath: str = "") -> str:
        """保存报告到文件"""
        if not filepath:
            filepath = str(REPORT_DIR / f"dependency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return str(filepath)


def main():
    parser = argparse.ArgumentParser(
        description='依赖检查脚本 - 检查项目依赖',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--check', '-a', action='store_true',
                        help='检查所有依赖')
    parser.add_argument('--python', '-p', action='store_true',
                        help='只检查 Python 依赖')
    parser.add_argument('--system', '-s', action='store_true',
                        help='只检查系统工具依赖')
    parser.add_argument('--gpu', '-g', action='store_true',
                        help='只检查 GPU 依赖')
    parser.add_argument('--report', '-r', action='store_true',
                        help='生成并保存报告')
    parser.add_argument('--json', '-j', action='store_true',
                        help='JSON 格式输出')
    parser.add_argument('--output', '-o', type=str, default="",
                        help='报告输出路径')
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    try:
        if args.python:
            checker.check_python_packages()
            results = {'python_packages': checker.results['python_packages']}
        
        elif args.system:
            checker.check_system_tools()
            results = {'system_tools': checker.results['system_tools']}
        
        elif args.gpu:
            checker.check_gpu()
            results = {'gpu_info': checker.results['gpu_info']}
        
        elif args.check or args.report:
            checker.check_all()
            results = checker.results
            
            if args.report:
                filepath = checker.save_report(args.output)
                print(f"\n📄 报告已保存到: {filepath}")
        
        else:
            # 默认执行所有检查
            checker.format_report_console()
            results = None
        
        # 输出 JSON 结果
        if args.json and results:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        
        elif not (args.python or args.system or args.gpu or args.check or args.report):
            checker.format_report_console()
    
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

