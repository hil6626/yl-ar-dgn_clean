#!/usr/bin/env python3
"""检查YL-monitor所有页面的渲染情况"""

import urllib.request
import urllib.error
import re
from html.parser import HTMLParser


class HTMLChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
        self.warnings = []
        self.scripts = []
        self.links = []
        self.stylesheets = []
        self.title = None
        self.in_title = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # 检查script标签
        if tag == 'script':
            src = attrs_dict.get('src', '')
            self.scripts.append(src)
            if src and not src.startswith(('http://', 'https://', '/')):
                self.warnings.append(f"Script路径可能错误: {src}")
                
        # 检查link标签
        elif tag == 'link':
            rel = attrs_dict.get('rel', '')
            href = attrs_dict.get('href', '')
            if rel == 'stylesheet':
                self.stylesheets.append(href)
                if href and not href.startswith(('http://', 'https://', '/')):
                    self.warnings.append(f"CSS路径可能错误: {href}")
                    
        # 检查title
        elif tag == 'title':
            self.in_title = True
            
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
            
    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()
            
    def check_common_issues(self, html, url):
        """检查常见问题"""
        issues = []
        
        # 检查未闭合标签
        unclosed = ['<div', '<span', '<p', '<a', '<li', '<td', '<tr']
        for tag in unclosed:
            open_count = html.count(tag)
            close_count = html.count(tag.replace('<', '</'))
            if open_count != close_count:
                issues.append(f"标签不平衡: {tag} (开:{open_count}, 闭:{close_count})")
                
        # 检查重复ID
        ids = re.findall(r'id=["\']([^"\']+)["\']', html)
        duplicates = set([x for x in ids if ids.count(x) > 1])
        if duplicates:
            issues.append(f"重复ID: {duplicates}")
            
        # 检查console.error
        if 'console.error' in html:
            issues.append("页面包含console.error调用")
            
        # 检查404资源
        if '404' in html and 'not found' in html.lower():
            issues.append("页面可能包含404错误信息")
            
        return issues


def check_page(url, name):
    """检查单个页面"""
    print(f"\n{'='*60}")
    print(f"检查页面: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # 解析HTML
            checker = HTMLChecker()
            try:
                checker.feed(html)
            except Exception as e:
                print(f"⚠️ HTML解析错误: {e}")
                
            # 检查常见问题
            issues = checker.check_common_issues(html, url)
            
            # 输出结果
            print(f"\n📄 页面标题: {checker.title or '未找到'}")
            print(f"📊 页面大小: {len(html)} 字节")
            print(f"📜 Scripts: {len(checker.scripts)} 个")
            print(f"🎨 Stylesheets: {len(checker.stylesheets)} 个")
            
            # 检查资源加载
            print(f"\n🔍 资源检查:")
            base_url = url.rsplit('/', 1)[0] if '/' in url else url
            
            # 检查CSS文件
            for css in checker.stylesheets:
                if css.startswith('http'):
                    css_url = css
                elif css.startswith('/'):
                    css_url = f"http://localhost:5500{css}"
                else:
                    css_url = f"{base_url}/{css}"
                    
                try:
                    css_req = urllib.request.Request(css_url)
                    with urllib.request.urlopen(css_req, timeout=5) as css_resp:
                        print(f"  ✅ CSS: {css} ({css_resp.status})")
                except Exception as e:
                    print(f"  ❌ CSS加载失败: {css} - {e}")
                    
            # 检查JS文件
            for js in checker.scripts:
                if not js:
                    continue
                if js.startswith('http'):
                    js_url = js
                elif js.startswith('/'):
                    js_url = f"http://localhost:5500{js}"
                else:
                    js_url = f"{base_url}/{js}"
                    
                try:
                    js_req = urllib.request.Request(js_url)
                    with urllib.request.urlopen(js_req, timeout=5) as js_resp:
                        print(f"  ✅ JS: {js} ({js_resp.status})")
                except Exception as e:
                    print(f"  ❌ JS加载失败: {js} - {e}")
            
            # 报告问题
            if issues:
                print(f"\n⚠️ 发现的问题:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print(f"\n✅ 未发现明显渲染问题")
                
            # 检查特定错误模式
            error_patterns = [
                (r'error|exception|fail', "包含错误关键词"),
                (r'undefined|NaN|null', "包含未定义值"),
                (r'class=["\'][^"\']*error', "包含错误样式类"),
                (r'style=["\'][^"\']*display:\s*none', "包含隐藏元素"),
            ]
            
            found_patterns = []
            for pattern, desc in error_patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    found_patterns.append(desc)
                    
            if found_patterns:
                print(f"\n🔍 内容模式检查:")
                for pattern in found_patterns:
                    print(f"  ⚠️ {pattern}")
                    
            return {
                'name': name,
                'url': url,
                'status': response.status,
                'title': checker.title,
                'size': len(html),
                'issues': issues,
                'patterns': found_patterns
            }
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP错误: {e.code} - {e.reason}")
        return {'name': name, 'url': url, 'error': f"HTTP {e.code}"}
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return {'name': name, 'url': url, 'error': str(e)}


def main():
    base = 'http://localhost:5500'
    
    pages = [
        ('/', '首页'),
        ('/dashboard', '仪表盘'),
        ('/scripts', '脚本管理'),
        ('/dag', 'DAG工作流'),
        ('/ar', 'AR监控'),
        ('/alert-rules', '告警规则'),
        ('/alert-analytics', '告警分析'),
        ('/intelligent-alert', '智能告警'),
        ('/api-doc', 'API文档'),
        ('/alerts', '告警列表'),
    ]
    
    results = []
    
    print("="*60)
    print("YL-monitor 页面渲染检查")
    print("="*60)
    
    for path, name in pages:
        url = f"{base}{path}"
        result = check_page(url, name)
        results.append(result)
        
    # 汇总报告
    print(f"\n{'='*60}")
    print("汇总报告")
    print('='*60)
    
    success = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    with_issues = [r for r in success if r.get('issues') or r.get('patterns')]
    
    print(f"\n✅ 正常页面: {len(success)}/{len(results)}")
    print(f"❌ 失败页面: {len(failed)}/{len(results)}")
    print(f"⚠️ 有问题页面: {len(with_issues)}/{len(results)}")
    
    if failed:
        print(f"\n❌ 失败页面详情:")
        for r in failed:
            print(f"  - {r['name']}: {r['error']}")
            
    if with_issues:
        print(f"\n⚠️ 需关注页面:")
        for r in with_issues:
            issues = r.get('issues', []) + r.get('patterns', [])
            print(f"  - {r['name']}: {len(issues)} 个问题")
            
    print(f"\n{'='*60}")
    print("检查完成")
    print('='*60)


if __name__ == '__main__':
    main()
