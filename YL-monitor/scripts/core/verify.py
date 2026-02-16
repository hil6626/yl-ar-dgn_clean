#!/usr/bin/env python3
"""
YL-Monitor 统一验证脚本
整合功能：verify_api.sh + verify_pages.py + verify_references.py + 
         verify_start.sh + verify_static_resources.sh + verify_templates.py + 
         verify_alert_center.py
"""

import os
import sys
import json
import re
import subprocess
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class VerifyResult:
    """验证结果"""
    name: str
    status: str  # 'pass', 'fail', 'warning', 'skip'
    message: str
    details: Optional[Dict] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details or {},
            'duration': f"{self.duration:.2f}s"
        }


class BaseVerifier:
    """验证器基类"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[VerifyResult] = []
    
    def log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def success(self, msg: str):
        print(f"  ✅ {msg}")
    
    def warning(self, msg: str):
        print(f"  ⚠️  {msg}")
    
    def error(self, msg: str):
        print(f"  ❌ {msg}")
    
    def add_result(self, name: str, status: str, message: str, 
                   details: Optional[Dict] = None, duration: float = 0.0):
        self.results.append(VerifyResult(
            name=name, status=status, message=message,
            details=details, duration=duration
        ))
    
    def get_summary(self) -> Dict[str, int]:
        summary = {'pass': 0, 'fail': 0, 'warning': 0, 'skip': 0}
        for result in self.results:
            summary[result.status] = summary.get(result.status, 0) + 1
        return summary


class APIVerifier(BaseVerifier):
    """API接口验证器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5500, **kwargs):
        super().__init__(**kwargs)
        self.base_url = f"http://{host}:{port}"
        self.endpoints = {
            'health': '/api/health',
            'summary': '/api/summary',
            'dashboard': '/api/v1/dashboard/overview',
            'scripts': '/api/v1/scripts',
            'alerts': '/api/v1/alerts',
            'dag': '/api/v1/dag'
        }
    
    def verify(self) -> List[VerifyResult]:
        """验证所有API端点"""
        print("\n🔍 验证API接口...")
        
        import time
        
        # 1. 验证服务是否运行
        start = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=5
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    '服务健康检查', 'pass',
                    f"服务运行正常 (版本: {data.get('version', 'unknown')})",
                    {'version': data.get('version'), 'status': data.get('status')},
                    duration
                )
                self.success(f"服务健康检查通过 ({duration:.2f}s)")
            else:
                self.add_result(
                    '服务健康检查', 'fail',
                    f"服务返回异常状态码: {response.status_code}",
                    {'status_code': response.status_code},
                    duration
                )
                self.error(f"服务健康检查失败: HTTP {response.status_code}")
                return self.results
                
        except requests.exceptions.ConnectionError:
            self.add_result(
                '服务健康检查', 'fail',
                f"无法连接到服务: {self.base_url}",
                {'url': self.base_url}
            )
            self.error(f"无法连接到服务: {self.base_url}")
            return self.results
        except Exception as e:
            self.add_result(
                '服务健康检查', 'fail',
                f"检查异常: {str(e)}"
            )
            self.error(f"服务健康检查异常: {e}")
            return self.results
        
        # 2. 验证其他端点
        for name, endpoint in self.endpoints.items():
            if name == 'health':
                continue  # 已检查
            
            start = time.time()
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    timeout=10
                )
                duration = time.time() - start
                
                if response.status_code == 200:
                    self.add_result(
                        f'API端点: {name}', 'pass',
                        f"端点正常 ({duration:.2f}s)",
                        {'endpoint': endpoint, 'status_code': 200},
                        duration
                    )
                    self.success(f"{name} API正常")
                else:
                    self.add_result(
                        f'API端点: {name}', 'warning',
                        f"端点返回非200状态码: {response.status_code}",
                        {'endpoint': endpoint, 'status_code': response.status_code},
                        duration
                    )
                    self.warning(f"{name} API返回 HTTP {response.status_code}")
                    
            except Exception as e:
                duration = time.time() - start
                self.add_result(
                    f'API端点: {name}', 'fail',
                    f"请求失败: {str(e)}",
                    {'endpoint': endpoint, 'error': str(e)},
                    duration
                )
                self.error(f"{name} API请求失败: {e}")
        
        return self.results


class PageVerifier(BaseVerifier):
    """页面验证器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5500, **kwargs):
        super().__init__(**kwargs)
        self.base_url = f"http://{host}:{port}"
        self.pages = [
            ('/', '首页'),
            ('/dashboard', '仪表盘'),
            ('/api-doc', 'API文档'),
            ('/dag', 'DAG流水线'),
            ('/scripts', '脚本管理'),
            ('/ar', 'AR监控'),
            ('/alerts', '告警中心')
        ]
    
    def verify(self) -> List[VerifyResult]:
        """验证所有页面"""
        print("\n🔍 验证页面可访问性...")
        
        import time
        
        for path, name in self.pages:
            start = time.time()
            try:
                response = requests.get(
                    f"{self.base_url}{path}",
                    timeout=10,
                    allow_redirects=True
                )
                duration = time.time() - start
                
                if response.status_code == 200:
                    # 检查内容
                    content_length = len(response.text)
                    has_doctype = '<!DOCTYPE' in response.text.upper() or '<!doctype' in response.text
                    
                    self.add_result(
                        f'页面: {name}', 'pass',
                        f"页面正常 ({content_length} bytes)",
                        {
                            'path': path,
                            'content_length': content_length,
                            'has_doctype': has_doctype
                        },
                        duration
                    )
                    self.success(f"{name} 页面正常 ({content_length} bytes)")
                else:
                    self.add_result(
                        f'页面: {name}', 'warning',
                        f"页面返回 HTTP {response.status_code}",
                        {'path': path, 'status_code': response.status_code},
                        duration
                    )
                    self.warning(f"{name} 页面返回 HTTP {response.status_code}")
                    
            except Exception as e:
                duration = time.time() - start
                self.add_result(
                    f'页面: {name}', 'fail',
                    f"访问失败: {str(e)}",
                    {'path': path, 'error': str(e)},
                    duration
                )
                self.error(f"{name} 页面访问失败: {e}")
        
        return self.results


class StaticResourceVerifier(BaseVerifier):
    """静态资源验证器"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.static_dir = PROJECT_ROOT / 'static'
        self.required_files = {
            'css': ['style.css', 'platform-modern.css', 'theme-enhancements.css'],
            'js': ['app-loader.js', 'config.js', 'api-utils.js']
        }
    
    def verify(self) -> List[VerifyResult]:
        """验证静态资源"""
        print("\n🔍 验证静态资源...")
        
        import time
        
        # 1. 检查目录结构
        start = time.time()
        if not self.static_dir.exists():
            self.add_result(
                '静态资源目录', 'fail',
                f"目录不存在: {self.static_dir}"
            )
            self.error("静态资源目录不存在")
            return self.results
        
        duration = time.time() - start
        self.add_result(
            '静态资源目录', 'pass',
            f"目录存在",
            {'path': str(self.static_dir)},
            duration
        )
        
        # 2. 检查必需文件
        for subdir, files in self.required_files.items():
            dir_path = self.static_dir / subdir
            if not dir_path.exists():
                self.add_result(
                    f'静态资源/{subdir}', 'warning',
                    f"子目录不存在: {subdir}"
                )
                self.warning(f"{subdir} 目录不存在")
                continue
            
            for filename in files:
                file_path = dir_path / filename
                start = time.time()
                
                if file_path.exists():
                    size = file_path.stat().st_size
                    self.add_result(
                        f'静态文件: {subdir}/{filename}', 'pass',
                        f"文件存在 ({size} bytes)",
                        {'path': str(file_path), 'size': size},
                        time.time() - start
                    )
                    self.success(f"{subdir}/{filename} 存在 ({size} bytes)")
                else:
                    self.add_result(
                        f'静态文件: {subdir}/{filename}', 'warning',
                        f"文件不存在: {filename}",
                        {'path': str(file_path)},
                        time.time() - start
                    )
                    self.warning(f"{subdir}/{filename} 不存在")
        
        # 3. 检查CSS重复
        start = time.time()
        css_dir = self.static_dir / 'css'
        if css_dir.exists():
            css_files = list(css_dir.glob('*.css'))
            duplicates = self._find_duplicates(css_files)
            
            if duplicates:
                self.add_result(
                    'CSS重复检查', 'warning',
                    f"发现 {len(duplicates)} 个可能重复的文件",
                    {'duplicates': duplicates},
                    time.time() - start
                )
                self.warning(f"发现 {len(duplicates)} 个可能重复的CSS文件")
            else:
                self.add_result(
                    'CSS重复检查', 'pass',
                    "未发现明显重复",
                    {'css_count': len(css_files)},
                    time.time() - start
                )
                self.success("CSS文件无重复")
        
        return self.results
    
    def _find_duplicates(self, files: List[Path]) -> List[Dict]:
        """查找重复文件"""
        duplicates = []
        seen = {}
        
        for f in files:
            key = f.stem.replace('-', '_').replace('.', '_')
            if key in seen:
                duplicates.append({
                    'file1': str(seen[key]),
                    'file2': str(f),
                    'name': f.name
                })
            else:
                seen[key] = f
        
        return duplicates


class TemplateVerifier(BaseVerifier):
    """模板验证器"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.templates_dir = PROJECT_ROOT / 'templates'
        self.required_templates = [
            'base.html',
            'platform.html',
            'dashboard.html',
            'api_doc.html',
            'dag.html',
            'scripts.html',
            'ar.html',
            'alerts.html'
        ]
    
    def verify(self) -> List[VerifyResult]:
        """验证模板文件"""
        print("\n🔍 验证模板文件...")
        
        import time
        
        if not self.templates_dir.exists():
            self.add_result(
                '模板目录', 'fail',
                f"目录不存在: {self.templates_dir}"
            )
            self.error("模板目录不存在")
            return self.results
        
        # 检查必需模板
        for template_name in self.required_templates:
            start = time.time()
            template_path = self.templates_dir / template_name
            
            if template_path.exists():
                content = template_path.read_text(encoding='utf-8')
                has_extends = '{% extends' in content
                has_blocks = '{% block' in content
                
                self.add_result(
                    f'模板: {template_name}', 'pass',
                    f"模板存在 (extends: {has_extends}, blocks: {has_blocks})",
                    {
                        'path': str(template_path),
                        'has_extends': has_extends,
                        'has_blocks': has_blocks,
                        'size': len(content)
                    },
                    time.time() - start
                )
                self.success(f"{template_name} 模板正常")
            else:
                self.add_result(
                    f'模板: {template_name}', 'warning',
                    f"模板不存在: {template_name}",
                    {'path': str(template_path)},
                    time.time() - start
                )
                self.warning(f"{template_name} 模板不存在")
        
        # 检查重复模板
        start = time.time()
        all_templates = list(self.templates_dir.glob('*.html'))
        names = [t.stem for t in all_templates]
        duplicates = [name for name in set(names) if names.count(name) > 1]
        
        if duplicates:
            self.add_result(
                '模板重复检查', 'warning',
                f"发现重复模板名: {', '.join(duplicates)}",
                {'duplicates': duplicates},
                time.time() - start
            )
            self.warning(f"发现重复模板: {', '.join(duplicates)}")
        else:
            self.add_result(
                '模板重复检查', 'pass',
                f"未发现重复模板 ({len(all_templates)} 个模板)",
                {'template_count': len(all_templates)},
                time.time() - start
            )
            self.success(f"模板无重复 ({len(all_templates)} 个)")
        
        return self.results


class ReferenceVerifier(BaseVerifier):
    """引用验证器"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def verify(self) -> List[VerifyResult]:
        """验证代码引用"""
        print("\n🔍 验证代码引用...")
        
        import time
        
        # 1. 检查Python导入
        start = time.time()
        app_dir = PROJECT_ROOT / 'app'
        if app_dir.exists():
            py_files = list(app_dir.rglob('*.py'))
            import_errors = []
            
            for py_file in py_files:
                try:
                    # 简单的语法检查
                    compile(py_file.read_text(encoding='utf-8'), str(py_file), 'exec')
                except SyntaxError as e:
                    import_errors.append({
                        'file': str(py_file),
                        'error': str(e)
                    })
            
            if import_errors:
                self.add_result(
                    'Python语法检查', 'fail',
                    f"发现 {len(import_errors)} 个语法错误",
                    {'errors': import_errors[:5]},  # 只显示前5个
                    time.time() - start
                )
                self.error(f"发现 {len(import_errors)} 个Python语法错误")
            else:
                self.add_result(
                    'Python语法检查', 'pass',
                    f"检查了 {len(py_files)} 个文件，无语法错误",
                    {'file_count': len(py_files)},
                    time.time() - start
                )
                self.success(f"Python语法检查通过 ({len(py_files)} 个文件)")
        
        # 2. 检查模板引用
        start = time.time()
        templates_dir = PROJECT_ROOT / 'templates'
        if templates_dir.exists():
            base_template = templates_dir / 'base.html'
            if base_template.exists():
                base_content = base_template.read_text(encoding='utf-8')
                
                # 检查其他模板是否继承base.html
                templates = list(templates_dir.glob('*.html'))
                missing_extends = []
                
                for template in templates:
                    if template.name == 'base.html':
                        continue
                    
                    content = template.read_text(encoding='utf-8')
                    if '{% extends' not in content:
                        missing_extends.append(template.name)
                
                if missing_extends:
                    self.add_result(
                        '模板继承检查', 'warning',
                        f"{len(missing_extends)} 个模板未继承base.html",
                        {'templates': missing_extends},
                        time.time() - start
                    )
                    self.warning(f"{len(missing_extends)} 个模板未继承base.html")
                else:
                    self.add_result(
                        '模板继承检查', 'pass',
                        f"所有模板正确继承base.html",
                        {'template_count': len(templates) - 1},
                        time.time() - start
                    )
                    self.success("模板继承检查通过")
        
        return self.results


class AlertCenterVerifier(BaseVerifier):
    """告警中心验证器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5500, **kwargs):
        super().__init__(**kwargs)
        self.base_url = f"http://{host}:{port}"
    
    def verify(self) -> List[VerifyResult]:
        """验证告警中心"""
        print("\n🔍 验证告警中心...")
        
        import time
        
        # 1. 检查告警API
        start = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/alerts",
                timeout=10
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                alert_count = len(data) if isinstance(data, list) else 0
                
                self.add_result(
                    '告警API', 'pass',
                    f"API正常，当前 {alert_count} 条告警",
                    {'alert_count': alert_count},
                    duration
                )
                self.success(f"告警API正常 ({alert_count} 条告警)")
            else:
                self.add_result(
                    '告警API', 'warning',
                    f"API返回 HTTP {response.status_code}",
                    {'status_code': response.status_code},
                    duration
                )
                self.warning(f"告警API返回 HTTP {response.status_code}")
                
        except Exception as e:
            self.add_result(
                '告警API', 'fail',
                f"API请求失败: {str(e)}",
                {'error': str(e)}
            )
            self.error(f"告警API请求失败: {e}")
        
        # 2. 检查告警规则API
        start = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/alert-rules",
                timeout=10
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                self.add_result(
                    '告警规则API', 'pass',
                    "告警规则API正常",
                    {},
                    duration
                )
                self.success("告警规则API正常")
            else:
                self.add_result(
                    '告警规则API', 'warning',
                    f"API返回 HTTP {response.status_code}",
                    {'status_code': response.status_code},
                    duration
                )
                
        except Exception as e:
            self.add_result(
                '告警规则API', 'fail',
                f"API请求失败: {str(e)}",
                {'error': str(e)}
            )
        
        return self.results


class ProjectVerifier:
    """统一项目验证器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5500, verbose: bool = False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.results: List[VerifyResult] = []
        
        # 初始化各个验证器
        self.verifiers = {
            'api': APIVerifier(host=host, port=port, verbose=verbose),
            'pages': PageVerifier(host=host, port=port, verbose=verbose),
            'static': StaticResourceVerifier(verbose=verbose),
            'templates': TemplateVerifier(verbose=verbose),
            'references': ReferenceVerifier(verbose=verbose),
            'alerts': AlertCenterVerifier(host=host, port=port, verbose=verbose)
        }
    
    def verify_all(self) -> Dict[str, Any]:
        """执行所有验证"""
        print("=" * 60)
        print("YL-Monitor 项目验证工具")
        print("=" * 60)
        print(f"目标: http://{self.host}:{self.port}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 执行各个验证器
        for name, verifier in self.verifiers.items():
            try:
                verifier.verify()
                self.results.extend(verifier.results)
            except Exception as e:
                print(f"\n❌ {name} 验证器异常: {e}")
        
        # 生成报告
        return self._generate_report()
    
    def verify_single(self, name: str) -> Dict[str, Any]:
        """执行单个验证"""
        if name not in self.verifiers:
            return {'error': f'未知的验证类型: {name}'}
        
        verifier = self.verifiers[name]
        verifier.verify()
        self.results = verifier.results
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        summary = {'pass': 0, 'fail': 0, 'warning': 0, 'skip': 0}
        for result in self.results:
            summary[result.status] = summary.get(result.status, 0) + 1
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("验证结果摘要")
        print("=" * 60)
        print(f"  ✅ 通过:   {summary.get('pass', 0)}")
        print(f"  ❌ 失败:   {summary.get('fail', 0)}")
        print(f"  ⚠️  警告:   {summary.get('warning', 0)}")
        print(f"  ⏭️  跳过:   {summary.get('skip', 0)}")
        print(f"  📊 总计:   {len(self.results)}")
        print("=" * 60)
        
        # 显示失败项
        failures = [r for r in self.results if r.status == 'fail']
        if failures:
            print("\n❌ 失败的检查项:")
            for f in failures:
                print(f"  - {f.name}: {f.message}")
        
        # 显示警告项
        warnings = [r for r in self.results if r.status == 'warning']
        if warnings:
            print("\n⚠️  警告项:")
            for w in warnings:
                print(f"  - {w.name}: {w.message}")
        
        # 返回详细报告
        return {
            'summary': summary,
            'total': len(self.results),
            'results': [r.to_dict() for r in self.results],
            'timestamp': datetime.now().isoformat(),
            'target': f"http://{self.host}:{self.port}"
        }
    
    def save_report(self, output_file: Optional[str] = None):
        """保存报告到文件"""
        if not output_file:
            output_file = PROJECT_ROOT / 'logs' / 'verify_report.json'
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report = self._generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 报告已保存: {output_file}")
        return str(output_file)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='YL-Monitor 统一验证脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 验证所有项目
  %(prog)s --api              # 仅验证API
  %(prog)s --pages            # 仅验证页面
  %(prog)s --host 0.0.0.0 --port 5500  # 指定目标
  %(prog)s --output report.json        # 保存报告
        """
    )
    
    # 验证类型
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='验证所有项目（默认）'
    )
    parser.add_argument(
        '--api',
        action='store_true',
        help='仅验证API接口'
    )
    parser.add_argument(
        '--pages',
        action='store_true',
        help='仅验证页面'
    )
    parser.add_argument(
        '--static',
        action='store_true',
        help='仅验证静态资源'
    )
    parser.add_argument(
        '--templates',
        action='store_true',
        help='仅验证模板'
    )
    parser.add_argument(
        '--references',
        action='store_true',
        help='仅验证代码引用'
    )
    parser.add_argument(
        '--alerts',
        action='store_true',
        help='仅验证告警中心'
    )
    
    # 连接配置
    parser.add_argument(
        '--host', '-H',
        default='0.0.0.0',
        help='目标主机 (默认:0.0.0.0)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5500,
        help='目标端口 (默认: 5500)'
    )
    
    # 输出选项
    parser.add_argument(
        '--output', '-o',
        help='保存报告到文件'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定具体验证类型，默认验证所有
    if not any([args.api, args.pages, args.static, args.templates, args.references, args.alerts]):
        args.all = True
    
    # 创建验证器
    verifier = ProjectVerifier(
        host=args.host,
        port=args.port,
        verbose=args.verbose
    )
    
    # 执行验证
    if args.all:
        report = verifier.verify_all()
    else:
        # 找到第一个指定的验证类型
        verify_type = None
        for t in ['api', 'pages', 'static', 'templates', 'references', 'alerts']:
            if getattr(args, t):
                verify_type = t
                break
        
        if verify_type:
            report = verifier.verify_single(verify_type)
        else:
            report = verifier.verify_all()
    
    # 保存报告
    if args.output:
        verifier.save_report(args.output)
    
    # 返回退出码
    failed = report['summary'].get('fail', 0)
    return 1 if failed > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
