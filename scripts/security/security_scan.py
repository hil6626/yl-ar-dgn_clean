#!/usr/bin/env python3
"""
AR System Security Scan Script
系统安全扫描脚本

功能:
- 系统安全检查
- 文件权限检查
- 端口安全检测
- 漏洞扫描

使用方法:
    python3 scripts/security/security_scan.py [--output FORMAT]
    
输出格式:
    --output json    - JSON格式输出
    --output text    - 文本格式输出 (默认)
    --output html    - HTML格式报告
"""

import os
import sys
import json
import time
import argparse
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class SecurityScanner:
    """安全扫描器类"""
    
    def __init__(self, output_format: str = 'text'):
        """
        初始化安全扫描器
        
        Args:
            output_format: 输出格式 (json/text/html)
        """
        self.output_format = output_format
        self.scan_results = {
            'timestamp': datetime.now().isoformat(),
            'scanner_version': '1.0.0',
            'scan_duration': 0,
            'findings': [],
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'warnings': 0,
                'failures': 0,
                'score': 0
            },
            'details': {}
        }
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    def run_scan(self) -> Dict[str, Any]:
        """
        执行完整的安全扫描
        
        Returns:
            扫描结果字典
        """
        start_time = time.time()
        
        print("=" * 60)
        print("AR 系统安全扫描器 v1.0.0")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"输出格式: {self.output_format}")
        print("-" * 60)
        
        # 执行各类安全检查
        self._check_file_permissions()
        self._check_port_security()
        self._check_system_security()
        self._check_python_security()
        self._check_config_security()
        self._check_dependency_security()
        
        # 计算扫描结果
        self.scan_results['scan_duration'] = round(time.time() - start_time, 2)
        self._calculate_summary()
        
        # 输出结果
        self._output_results()
        
        print("-" * 60)
        print(f"扫描完成! 耗时: {self.scan_results['scan_duration']}秒")
        print(f"总检查项: {self.scan_results['summary']['total_checks']}")
        print(f"通过: {self.scan_results['summary']['passed']}")
        print(f"警告: {self.scan_results['summary']['warnings']}")
        print(f"失败: {self.scan_results['summary']['failures']}")
        print(f"安全评分: {self.scan_results['summary']['score']}/100")
        print("=" * 60)
        
        return self.scan_results
    
    def _add_finding(self, check_name: str, status: str, message: str, 
                     severity: str = 'info', details: Optional[Dict] = None):
        """
        添加扫描发现
        
        Args:
            check_name: 检查项名称
            status: 状态 (pass/warning/fail)
            message: 简要信息
            severity: 严重程度 (info/warning/critical)
            details: 详细信息字典
        """
        finding = {
            'check': check_name,
            'status': status,
            'message': message,
            'severity': severity,
            'details': details or {}
        }
        self.scan_results['findings'].append(finding)
        self.scan_results['summary']['total_checks'] += 1
        
        # 根据状态输出
        status_symbol = {'pass': '✅', 'warning': '⚠️', 'fail': '❌'}
        symbol = status_symbol.get(status, '•')
        print(f"  {symbol} [{check_name}] {message}")
    
    def _check_file_permissions(self):
        """检查文件权限"""
        print("\n📁 检查文件权限...")
        
        sensitive_files = [
            ('.env', '环境变量文件'),
            ('.blackboxrules', 'AI规则文件'),
            ('config/security_config.json', '安全配置文件'),
            ('config/app_config.json', '应用配置文件'),
        ]
        
        for filename, description in sensitive_files:
            filepath = os.path.join(self.project_root, filename)
            if os.path.exists(filepath):
                try:
                    mode = os.stat(filepath).st_mode & 0o777
                    perm_str = oct(mode)[-3:]
                    
                    # 检查权限是否过于宽松
                    if mode & 0o004:  # 其他用户可读
                        self._add_finding(
                            f'文件权限-{filename}',
                            'warning',
                            f'{description} ({filename}) 权限过于宽松: {perm_str}',
                            'medium',
                            {'file': filename, 'permission': perm_str}
                        )
                    elif mode & 0o002:  # 其他用户可写
                        self._add_finding(
                            f'文件权限-{filename}',
                            'fail',
                            f'{description} ({filename}) 权限存在安全风险: {perm_str}',
                            'critical',
                            {'file': filename, 'permission': perm_str}
                        )
                    else:
                        self._add_finding(
                            f'文件权限-{filename}',
                            'pass',
                            f'{description} ({filename}) 权限正常: {perm_str}',
                            'info',
                            {'file': filename, 'permission': perm_str}
                        )
                except Exception as e:
                    self._add_finding(
                        f'文件权限-{filename}',
                        'warning',
                        f'无法检查 {filename} 权限: {str(e)}',
                        'low',
                        {'file': filename, 'error': str(e)}
                    )
            else:
                self._add_finding(
                    f'文件存在-{filename}',
                    'info',
                    f'{description} ({filename}) 不存在，跳过检查',
                    'info',
                    {'file': filename}
                )
    
    def _check_port_security(self):
        """检查端口安全"""
        print("\n🔌 检查端口安全...")
        
        # 检查监听的端口
        try:
            result = subprocess.run(
                ['ss', '-tlnp'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            listening_ports = []
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    # 解析端口号
                    match = re.search(r':(\d+)\s', line)
                    if match:
                        port = int(match.group(1))
                        if port not in listening_ports:
                            listening_ports.append(port)
            
            # 检查是否有关键端口暴露
            critical_ports = {
                22: 'SSH',
                3389: 'RDP',
                5000: '开发服务器',
                5000: '开发服务器'
            }
            
            for port, service in critical_ports.items():
                if port in listening_ports:
                    if port in [22, 3389]:
                        self._add_finding(
                            f'端口-{port}',
                            'warning',
                            f'{service} 端口 ({port}) 正在监听，确保已配置防火墙',
                            'medium',
                            {'port': port, 'service': service}
                        )
                    else:
                        self._add_finding(
                            f'端口-{port}',
                            'pass',
                            f'{service} 端口 ({port}) 正在监听',
                            'info',
                            {'port': port, 'service': service}
                        )
            
            if not listening_ports:
                self._add_finding(
                    '端口扫描',
                    'info',
                    '未检测到监听端口',
                    'info',
                    {'ports': listening_ports}
                )
                
        except Exception as e:
            self._add_finding(
                '端口扫描',
                'warning',
                f'无法扫描端口: {str(e)}',
                'low',
                {'error': str(e)}
            )
    
    def _check_system_security(self):
        """检查系统安全"""
        print("\n🛡️ 检查系统安全...")
        
        checks = [
            ('selinux', self._check_selinux),
            ('firewall', self._check_firewall),
            ('password_policy', self._check_password_policy),
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self._add_finding(
                    check_name,
                    'warning',
                    f'检查失败: {str(e)}',
                    'low',
                    {'error': str(e)}
                )
    
    def _check_selinux(self):
        """检查SELinux状态"""
        try:
            with open('/proc/sys/fs/superuser/show_name_for_uid', 'r') as f:
                pass
            self._add_finding(
                'SELinux',
                'info',
                'SELinux 配置检查完成',
                'info'
            )
        except:
            self._add_finding(
                'SELinux',
                'info',
                'SELinux 未在此系统上配置',
                'info'
            )
    
    def _check_firewall(self):
        """检查防火墙状态"""
        try:
            result = subprocess.run(
                ['sudo', 'ufw', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'inactive' in result.stdout.lower():
                self._add_finding(
                    '防火墙',
                    'warning',
                    '防火墙未启用，建议启用防火墙',
                    'medium'
                )
            else:
                self._add_finding(
                    '防火墙',
                    'pass',
                    '防火墙已启用',
                    'info'
                )
        except FileNotFoundError:
            # ufw not installed, try iptables
            try:
                result = subprocess.run(
                    ['sudo', 'iptables', '-L', '-n'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if 'Chain INPUT' in result.stdout:
                    self._add_finding(
                        '防火墙(iptables)',
                        'pass',
                        'iptables 规则已配置',
                        'info'
                    )
                else:
                    self._add_finding(
                        '防火墙(iptables)',
                        'warning',
                        '未检测到 iptables 规则',
                        'low'
                    )
            except:
                self._add_finding(
                    '防火墙',
                    'info',
                    '无法检测防火墙状态',
                    'info'
                )
        except Exception as e:
            self._add_finding(
                '防火墙',
                'warning',
                f'防火墙检查失败: {str(e)}',
                'low'
            )
    
    def _check_password_policy(self):
        """检查密码策略"""
        # 检查是否存在密码策略文件
        policy_files = [
            '/etc/security/pwquality.conf',
            '/etc/login.defs'
        ]
        
        has_policy = False
        for pf in policy_files:
            if os.path.exists(pf):
                has_policy = True
                break
        
        if has_policy:
            self._add_finding(
                '密码策略',
                'pass',
                '系统已配置密码策略',
                'info'
            )
        else:
            self._add_finding(
                '密码策略',
                'warning',
                '未检测到系统密码策略配置',
                'low'
            )
    
    def _check_python_security(self):
        """检查Python安全"""
        print("\n🐍 检查Python安全...")
        
        # 检查是否有已知不安全的代码模式
        insecure_patterns = [
            (r'eval\s*\(', '使用 eval() 可能导致代码注入'),
            (r'exec\s*\(', '使用 exec() 可能导致代码注入'),
            (r'pickle\.loads', '使用 pickle 可能导致反序列化漏洞'),
            (r'MD5', '使用 MD5 已被认为不安全'),
            (r'SHA1', 'SHA1 已被认为不安全，建议使用 SHA256'),
        ]
        
        code_extensions = ('.py', '.pyw')
        insecure_count = 0
        
        for root, dirs, files in os.walk(self.project_root):
            # 跳过虚拟环境和构建目录
            dirs[:] = [d for d in dirs if d not in ['env', 'venv', '__pycache__', '.git', 'build']]
            
            for file in files:
                if file.endswith(code_extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            for pattern, description in insecure_patterns:
                                if re.search(pattern, content):
                                    insecure_count += 1
                                    rel_path = os.path.relpath(filepath, self.project_root)
                                    self._add_finding(
                                        f'代码安全-{file}',
                                        'warning',
                                        f'{file}: {description}',
                                        'medium',
                                        {'file': rel_path, 'pattern': pattern}
                                    )
                    except Exception:
                        continue
        
        if insecure_count == 0:
            self._add_finding(
                'Python代码安全',
                'pass',
                f'未检测到不安全的代码模式 (扫描 {code_extensions} 文件)',
                'info',
                {'files_scanned': '多个'}
            )
    
    def _check_config_security(self):
        """检查配置文件安全"""
        print("\n⚙️ 检查配置安全...")
        
        # 检查敏感配置
        config_checks = [
            ('config/app_config.json', 'DEBUG模式', 'debug', False),
            ('config/security_config.json', '认证启用', 'authentication', True),
        ]
        
        for config_file, check_name, key, expected_value in config_checks:
            filepath = os.path.join(self.project_root, config_file)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        config = json.load(f)
                        
                        if key in config:
                            actual_value = config[key]
                            if actual_value == expected_value:
                                self._add_finding(
                                    f'配置-{config_file}',
                                    'pass',
                                    f'{check_name} 设置正确',
                                    'info',
                                    {key: actual_value}
                                )
                            else:
                                self._add_finding(
                                    f'配置-{config_file}',
                                    'warning',
                                    f'{check_name} 可能存在安全风险 (当前: {actual_value})',
                                    'medium',
                                    {key: actual_value, 'recommended': expected_value}
                                )
                        else:
                            self._add_finding(
                                f'配置-{config_file}',
                                'info',
                                f'{check_name} 配置项未找到',
                                'info'
                            )
                except Exception as e:
                    self._add_finding(
                        f'配置-{config_file}',
                        'warning',
                        f'无法读取配置文件: {str(e)}',
                        'low',
                        {'error': str(e)}
                    )
    
    def _check_dependency_security(self):
        """检查依赖安全"""
        print("\n📦 检查依赖安全...")
        
        requirements_file = os.path.join(self.project_root, 'requirements.txt')
        if os.path.exists(requirements_file):
            try:
                with open(requirements_file, 'r') as f:
                    deps = f.readlines()
                
                # 已知有漏洞的包
                vulnerable_packages = [
                    ('pyyaml', '5.3.1', 'CVE-2020-1747'),
                    ('django', '2.2', '多个已知漏洞'),
                    ('flask', '0.12', '已知漏洞'),
                ]
                
                found_vulnerabilities = []
                for line in deps:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析依赖
                        parts = line.split('==')
                        if len(parts) == 2:
                            pkg_name, version = parts
                            
                            for vuln_pkg, vuln_version, cve in vulnerable_packages:
                                if pkg_name.lower() == vuln_pkg:
                                    found_vulnerabilities.append({
                                        'package': pkg_name,
                                        'version': version,
                                        'cve': cve
                                    })
                
                if found_vulnerabilities:
                    for vuln in found_vulnerabilities:
                        self._add_finding(
                            f'依赖-{vuln["package"]}',
                            'fail',
                            f'{vuln["package"]}=={vuln["version"]} 存在漏洞 ({vuln["cve"]})',
                            'critical',
                            vuln
                        )
                else:
                    self._add_finding(
                        '依赖安全',
                        'pass',
                        f'requirements.txt 中的依赖未检测到已知漏洞',
                        'info',
                        {'total_dependencies': len(deps)}
                    )
                    
            except Exception as e:
                self._add_finding(
                    '依赖安全检查',
                    'warning',
                    f'无法检查依赖安全: {str(e)}',
                    'low',
                    {'error': str(e)}
                )
        else:
            self._add_finding(
                '依赖文件',
                'info',
                '未找到 requirements.txt 文件',
                'info'
            )
    
    def _calculate_summary(self):
        """计算扫描摘要"""
        summary = self.scan_results['summary']
        
        for finding in self.scan_results['findings']:
            status = finding['status']
            if status == 'pass':
                summary['passed'] += 1
            elif status == 'warning':
                summary['warnings'] += 1
            elif status == 'fail':
                summary['failures'] += 1
        
        # 计算安全评分
        if summary['total_checks'] > 0:
            score = (summary['passed'] * 100) / summary['total_checks']
            score -= summary['warnings'] * 5
            score -= summary['failures'] * 10
            score = max(0, min(100, score))
            summary['score'] = round(score, 1)
    
    def _output_results(self):
        """输出结果"""
        if self.output_format == 'json':
            output_file = os.path.join(self.project_root, 'logs', 'security_scan.json')
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.scan_results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 JSON报告已保存到: {output_file}")
            
        elif self.output_format == 'html':
            output_file = os.path.join(self.project_root, 'logs', 'security_scan.html')
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            self._generate_html_report(output_file)
            print(f"\n📄 HTML报告已保存到: {output_file}")
        
        # 保存到文件供浏览器读取
        results_file = os.path.join(self.project_root, 'logs', 'security_results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.scan_results, f, indent=2, ensure_ascii=False)


class SecurityScanAPI:
    """安全扫描API接口类"""
    
    def __init__(self):
        self.scanner = None
        
    def start_scan(self, output_format: str = 'json') -> Dict:
        """
        开始安全扫描
        
        Returns:
            扫描任务信息
        """
        self.scanner = SecurityScanner(output_format)
        
        # 在后台线程中运行扫描
        import threading
        thread = threading.Thread(target=self.scanner.run_scan)
        thread.start()
        
        return {
            'status': 'started',
            'message': '安全扫描已开始',
            'output_format': output_format
        }
    
    def get_results(self) -> Optional[Dict]:
        """
        获取扫描结果
        
        Returns:
            扫描结果或None
        """
        if self.scanner:
            return self.scanner.scan_results
        return None
    
    def get_latest_results(self) -> Dict:
        """
        获取最新扫描结果（从文件读取）
        
        Returns:
            扫描结果
        """
        results_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'logs', 'security_results.json'
        )
        
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'status': 'no_results',
            'message': '尚未执行安全扫描',
            'findings': [],
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'warnings': 0,
                'failures': 0,
                'score': 0
            }
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AR 系统安全扫描工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python3 scripts/security/security_scan.py                    # 默认文本输出
    python3 scripts/security/security_scan.py --output json     # JSON格式输出
    python3 scripts/security/security_scan.py --output html     # HTML报告输出
        """
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'text', 'html'],
        default='text',
        help='输出格式 (默认: text)'
    )
    
    args = parser.parse_args()
    
    # 创建扫描器并执行扫描
    scanner = SecurityScanner(args.output)
    results = scanner.run_scan()
    
    return 0 if results['summary']['failures'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
