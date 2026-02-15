#!/usr/bin/env python3
"""
YL-Monitor CSS 统一管理器
整合功能：analyze_unused_css.py + check_css_compliance.py + cleanup_unused_css.py + 
         duplicate_detector.py + css_version_manager.py
"""

import os
import re
import sys
import json
import shutil
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CSSIssue:
    """CSS问题记录"""
    type: str
    file: str
    message: str
    severity: str  # 'error', 'warning', 'info'
    details: Optional[Dict] = None


class CSSAnalyzer:
    """CSS分析器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.css_dir = project_root / "static" / "css"
        self.template_dir = project_root / "templates"
        self.js_dir = project_root / "static" / "js"
        
        self.css_selectors: Dict[str, Set[str]] = {}
        self.html_classes: Set[str] = set()
        self.js_classes: Set[str] = set()
        self.dynamic_classes: Set[str] = set()
    
    def extract_css_selectors(self) -> Dict[str, Set[str]]:
        """提取所有CSS选择器"""
        print("🔍 分析CSS选择器...")
        
        for css_file in self.css_dir.glob("*.css"):
            content = css_file.read_text(encoding='utf-8')
            selectors = set()
            
            # 提取类选择器
            class_selectors = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', content)
            selectors.update(class_selectors)
            
            # 提取ID选择器
            id_selectors = re.findall(r'#([a-zA-Z][a-zA-Z0-9_-]*)', content)
            selectors.update(id_selectors)
            
            self.css_selectors[css_file.name] = selectors
            print(f"   {css_file.name}: {len(selectors)} 个选择器")
        
        return self.css_selectors
    
    def extract_html_classes(self) -> Set[str]:
        """提取HTML中使用的类名"""
        print("\n🔍 分析HTML类名...")
        
        for html_file in self.template_dir.glob("*.html"):
            content = html_file.read_text(encoding='utf-8')
            
            # 提取class属性
            classes = re.findall(r'class="([^"]*)"', content)
            for class_str in classes:
                self.html_classes.update(class_str.split())
            
            # 提取id属性
            ids = re.findall(r'id="([^"]*)"', content)
            self.html_classes.update(ids)
        
        print(f"   找到 {len(self.html_classes)} 个唯一类名/ID")
        return self.html_classes
    
    def extract_js_classes(self) -> Set[str]:
        """提取JS中使用的类名"""
        print("\n🔍 分析JavaScript类名...")
        
        for js_file in self.js_dir.glob("*.js"):
            content = js_file.read_text(encoding='utf-8')
            
            # 提取classList操作
            classlist_ops = re.findall(r'classList\.(?:add|remove|toggle)\([\'"]([^\'"]+)[\'"]\)', content)
            self.js_classes.update(classlist_ops)
            
            # 提取className赋值
            classnames = re.findall(r'className\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            for cn in classnames:
                self.js_classes.update(cn.split())
            
            # 提取querySelector
            query_selectors = re.findall(r'querySelector\([\'"]\.([a-zA-Z][a-zA-Z0-9_-]*)[\'"]\)', content)
            self.js_classes.update(query_selectors)
            
            # 提取动态类名
            dynamic = re.findall(r'[\'"]([a-zA-Z-]+)-\$\{[^}]+\}[\'"]', content)
            self.dynamic_classes.update(dynamic)
        
        print(f"   找到 {len(self.js_classes)} 个JS中使用的类名")
        print(f"   找到 {len(self.dynamic_classes)} 个动态类名前缀")
        return self.js_classes
    
    def find_unused_selectors(self) -> Dict[str, List[str]]:
        """查找未使用的选择器"""
        self.extract_css_selectors()
        self.extract_html_classes()
        self.extract_js_classes()
        
        print("\n🔍 查找未使用的选择器...")
        
        all_used = self.html_classes | self.js_classes
        
        # 添加动态类名的可能组合
        for prefix in self.dynamic_classes:
            for file, selectors in self.css_selectors.items():
                for selector in selectors:
                    if selector.startswith(prefix):
                        all_used.add(selector)
        
        unused_by_file: Dict[str, List[str]] = {}
        
        for file, selectors in self.css_selectors.items():
            unused = []
            for selector in selectors:
                if self._is_generic_class(selector):
                    continue
                
                if selector not in all_used:
                    unused.append(selector)
            
            if unused:
                unused_by_file[file] = unused
        
        return unused_by_file
    
    def _is_generic_class(self, selector: str) -> bool:
        """检查是否为通用类名"""
        generic_prefixes = [
            'btn', 'card', 'modal', 'alert', 'badge', 'container',
            'row', 'col', 'form', 'input', 'table', 'nav', 'sidebar',
            'header', 'footer', 'main', 'content', 'page', 'grid',
            'list', 'item', 'active', 'disabled', 'show', 'hide',
            'open', 'close', 'primary', 'secondary', 'success',
            'danger', 'warning', 'info', 'light', 'dark'
        ]
        
        for prefix in generic_prefixes:
            if selector.startswith(prefix):
                return True
        
        if 'status-' in selector or 'state-' in selector:
            return True
        
        if ':' in selector:
            return True
        
        return False
    
    def find_duplicates(self) -> List[Dict]:
        """查找重复的选择器"""
        print("\n🔍 查找重复的选择器...")
        
        all_selectors: Dict[str, List[str]] = {}
        
        for css_file in self.css_dir.glob("*.css"):
            content = css_file.read_text(encoding='utf-8')
            selectors = re.findall(r'^([a-zA-Z.#][^{]+)\s*\{', content, re.MULTILINE)
            
            for selector in selectors:
                selector = selector.strip()
                if selector not in all_selectors:
                    all_selectors[selector] = []
                all_selectors[selector].append(css_file.name)
        
        duplicates = []
        for selector, files in all_selectors.items():
            if len(files) > 1:
                # 排除允许的重复
                if not any(media in selector for media in ['@media', ':hover', ':focus']):
                    duplicates.append({
                        'selector': selector,
                        'files': files
                    })
        
        print(f"   发现 {len(duplicates)} 个重复选择器")
        return duplicates


class CSSComplianceChecker:
    """CSS合规性检查器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.css_dir = project_root / "static" / "css"
        self.template_dir = project_root / "templates"
        self.issues: List[CSSIssue] = []
    
    def check_all(self) -> List[CSSIssue]:
        """执行所有合规性检查"""
        print("\n🔍 执行CSS合规性检查...")
        
        self._check_naming_convention()
        self._check_css_variables()
        self._check_responsive_breakpoints()
        self._check_spacing_consistency()
        
        return self.issues
    
    def _check_naming_convention(self):
        """检查命名规范"""
        print("   检查命名规范...")
        
        for html_file in self.template_dir.glob("*.html"):
            if html_file.name == "base.html":
                continue
            
            content = html_file.read_text(encoding='utf-8')
            page_match = re.search(r'class="([a-z-]+-page)"', content)
            
            if page_match:
                page_class = page_match.group(1)
                if not page_class.endswith('-page'):
                    self.issues.append(CSSIssue(
                        type='naming',
                        file=html_file.name,
                        message=f'页面容器类名 "{page_class}" 不符合规范，应使用 "-page" 后缀',
                        severity='error'
                    ))
    
    def _check_css_variables(self):
        """检查CSS变量使用"""
        print("   检查CSS变量...")
        
        required_variables = [
            '--primary-color',
            '--success-color',
            '--danger-color',
            '--warning-color'
        ]
        
        for css_file in self.css_dir.glob("*.css"):
            if css_file.name == "style.css":
                continue
            
            content = css_file.read_text(encoding='utf-8')
            
            # 检查硬编码颜色
            hardcoded_colors = re.findall(r'#[a-fA-F0-9]{3,6}\b', content)
            if hardcoded_colors:
                self.issues.append(CSSIssue(
                    type='hardcoded_color',
                    file=css_file.name,
                    message=f'使用了硬编码颜色值，建议使用CSS变量',
                    severity='warning',
                    details={'colors': list(set(hardcoded_colors))[:5]}
                ))
    
    def _check_responsive_breakpoints(self):
        """检查响应式断点"""
        print("   检查响应式断点...")
        
        standard_breakpoints = [480, 768, 1024]
        
        for css_file in self.css_dir.glob("*.css"):
            content = css_file.read_text(encoding='utf-8')
            breakpoints = re.findall(r'@media[^{]*?\(\s*(?:max-width|min-width)\s*:\s*(\d+)px', content, re.IGNORECASE)
            
            non_standard = [int(b) for b in breakpoints if int(b) not in standard_breakpoints]
            if non_standard:
                self.issues.append(CSSIssue(
                    type='non_standard_breakpoint',
                    file=css_file.name,
                    message=f'使用了非标准断点: {set(non_standard)}',
                    severity='warning',
                    details={'breakpoints': list(set(non_standard))}
                ))
    
    def _check_spacing_consistency(self):
        """检查间距一致性"""
        print("   检查间距一致性...")
        
        standard_values = [4, 8, 12, 16, 20, 24, 32]
        
        for css_file in self.css_dir.glob("*.css"):
            content = css_file.read_text(encoding='utf-8')
            
            paddings = re.findall(r'padding[:\s]+(\d+)px', content)
            non_standard = [int(p) for p in paddings if int(p) not in standard_values]
            
            if non_standard:
                self.issues.append(CSSIssue(
                    type='non_standard_spacing',
                    file=css_file.name,
                    message=f'使用了非标准padding值: {set(non_standard)}',
                    severity='info',
                    details={'values': list(set(non_standard))}
                ))


class CSSCleaner:
    """CSS清理器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.css_dir = project_root / "static" / "css"
        self.backup_dir = project_root / "backups" / "css_cleanups"
    
    def create_backup(self) -> Path:
        """创建CSS备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"css_backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for css_file in self.css_dir.glob("*.css"):
            shutil.copy2(css_file, backup_path / css_file.name)
        
        print(f"   📦 CSS备份已创建: {backup_path}")
        return backup_path
    
    def cleanup_unused(self, unused_selectors: Dict[str, List[str]], dry_run: bool = True) -> int:
        """清理未使用的CSS"""
        if dry_run:
            print("\n🔍 [试运行] 以下CSS将被清理:")
        else:
            print("\n🧹 清理未使用的CSS...")
            self.create_backup()
        
        total_removed = 0
        
        for file, selectors in unused_selectors.items():
            css_file = self.css_dir / file
            if not css_file.exists():
                continue
            
            content = css_file.read_text(encoding='utf-8')
            original_length = len(content)
            
            for selector in selectors:
                # 构建正则表达式匹配选择器及其规则
                pattern = rf'\.{re.escape(selector)}\s*\{{[^}}]*\}}\s*'
                matches = len(re.findall(pattern, content))
                
                if matches > 0:
                    if dry_run:
                        print(f"   将删除: {file} 中的 .{selector}")
                    else:
                        content = re.sub(pattern, '', content)
                    total_removed += matches
            
            if not dry_run:
                css_file.write_text(content, encoding='utf-8')
                new_length = len(content)
                saved = original_length - new_length
                print(f"   ✅ {file}: 清理完成，节省 {saved} 字节")
        
        return total_removed


class CSSManager:
    """CSS统一管理器"""
    
    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.parent.absolute()
        else:
            self.project_root = Path(project_root)
        
        self.analyzer = CSSAnalyzer(self.project_root)
        self.checker = CSSComplianceChecker(self.project_root)
        self.cleaner = CSSCleaner(self.project_root)
        
        self.report_data: Dict = {}
    
    def analyze(self) -> Dict:
        """执行完整分析"""
        print("=" * 60)
        print("YL-Monitor CSS 分析")
        print("=" * 60)
        
        # 分析未使用的选择器
        unused = self.analyzer.find_unused_selectors()
        total_unused = sum(len(s) for s in unused.values())
        
        # 查找重复
        duplicates = self.analyzer.find_duplicates()
        
        # 合规性检查
        issues = self.checker.check_all()
        
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'unused_selectors': unused,
            'total_unused': total_unused,
            'duplicates': duplicates,
            'issues': [asdict(issue) for issue in issues],
            'summary': {
                'unused': total_unused,
                'duplicates': len(duplicates),
                'errors': len([i for i in issues if i.severity == 'error']),
                'warnings': len([i for i in issues if i.severity == 'warning']),
                'infos': len([i for i in issues if i.severity == 'info'])
            }
        }
        
        return self.report_data
    
    def cleanup(self, dry_run: bool = True) -> int:
        """执行清理"""
        if 'unused_selectors' not in self.report_data:
            self.analyze()
        
        removed = self.cleaner.cleanup_unused(
            self.report_data['unused_selectors'],
            dry_run=dry_run
        )
        
        if dry_run:
            print(f"\n🔍 [试运行] 将清理 {removed} 个选择器")
            print("   使用 --apply 参数执行实际清理")
        else:
            print(f"\n✅ 已清理 {removed} 个选择器")
        
        return removed
    
    def generate_report(self) -> str:
        """生成文本报告"""
        if not self.report_data:
            self.analyze()
        
        lines = []
        lines.append("=" * 60)
        lines.append("YL-Monitor CSS 分析报告")
        lines.append("=" * 60)
        lines.append(f"时间: {self.report_data['timestamp']}")
        lines.append("")
        
        # 摘要
        summary = self.report_data['summary']
        lines.append("📊 摘要")
        lines.append("-" * 40)
        lines.append(f"未使用选择器: {summary['unused']}")
        lines.append(f"重复选择器: {summary['duplicates']}")
        lines.append(f"错误: {summary['errors']}")
        lines.append(f"警告: {summary['warnings']}")
        lines.append(f"建议: {summary['infos']}")
        lines.append("")
        
        # 未使用的选择器
        if self.report_data['unused_selectors']:
            lines.append("🗑️  未使用的选择器")
            lines.append("-" * 40)
            for file, selectors in self.report_data['unused_selectors'].items():
                lines.append(f"\n{file}:")
                for selector in selectors[:10]:  # 只显示前10个
                    lines.append(f"  • .{selector}")
                if len(selectors) > 10:
                    lines.append(f"  ... 还有 {len(selectors) - 10} 个")
            lines.append("")
        
        # 重复的选择器
        if self.report_data['duplicates']:
            lines.append("🔁 重复的选择器")
            lines.append("-" * 40)
            for dup in self.report_data['duplicates'][:10]:
                lines.append(f"\n  {dup['selector']}")
                lines.append(f"    出现在: {', '.join(dup['files'])}")
            if len(self.report_data['duplicates']) > 10:
                lines.append(f"\n  ... 还有 {len(self.report_data['duplicates']) - 10} 个")
            lines.append("")
        
        # 问题列表
        issues = self.report_data['issues']
        if issues:
            lines.append("⚠️  合规性问题")
            lines.append("-" * 40)
            for issue in issues:
                icon = "❌" if issue['severity'] == 'error' else "⚠️" if issue['severity'] == 'warning' else "ℹ️"
                lines.append(f"{icon} [{issue['type']}] {issue['file']}")
                lines.append(f"   {issue['message']}")
                lines.append("")
        
        lines.append("=" * 60)
        lines.append("分析完成")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_report(self, output_file: Optional[str] = None) -> str:
        """保存报告"""
        if output_file is None:
            output_file = self.project_root / "logs" / "css_manager_report.json"
        else:
            output_file = Path(output_file)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
        
        # 同时保存文本报告
        text_file = output_file.with_suffix('.txt')
        text_file.write_text(self.generate_report(), encoding='utf-8')
        
        print(f"\n📄 报告已保存:")
        print(f"   JSON: {output_file}")
        print(f"   文本: {text_file}")
        
        return str(output_file)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='YL-Monitor CSS 统一管理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s analyze                    # 分析CSS
  %(prog)s cleanup                    # 试运行清理
  %(prog)s cleanup --apply            # 实际执行清理
  %(prog)s report                     # 生成报告
        """
    )
    
    parser.add_argument(
        'command',
        choices=['analyze', 'cleanup', 'report', 'check'],
        help='要执行的命令'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='实际执行清理（默认试运行）'
    )
    parser.add_argument(
        '--output', '-o',
        help='报告输出文件'
    )
    parser.add_argument(
        '--project-root', '-p',
        help='项目根目录（默认自动检测）'
    )
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = CSSManager(project_root=args.project_root)
    
    # 执行命令
    if args.command == 'analyze':
        manager.analyze()
        print(manager.generate_report())
        
    elif args.command == 'check':
        # 仅合规性检查
        issues = manager.checker.check_all()
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']
        
        print(f"\n合规性检查完成:")
        print(f"  错误: {len(errors)}")
        print(f"  警告: {len(warnings)}")
        
        if errors:
            sys.exit(1)
            
    elif args.command == 'cleanup':
        manager.analyze()
        removed = manager.cleanup(dry_run=not args.apply)
        
        if not args.apply:
            print(f"\n🔍 试运行完成，发现 {removed} 个可清理的选择器")
            print("   使用 --apply 参数执行实际清理")
        else:
            print(f"\n✅ 清理完成，已删除 {removed} 个选择器")
            
    elif args.command == 'report':
        manager.analyze()
        manager.save_report(args.output)
        print(manager.generate_report())
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
