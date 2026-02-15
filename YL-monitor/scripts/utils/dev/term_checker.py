#!/usr/bin/env python3
"""
【文件功能】
术语一致性检查工具，用于检查项目中术语使用的统一性

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现术语检查功能

【依赖说明】
- 标准库: argparse, os, re, sys, json, pathlib, collections
- 第三方库: 无
- 内部模块: 无

【使用示例】
```bash
# 检查术语一致性
python scripts/tools/term_checker.py app/

# 生成术语使用报告
python scripts/tools/term_checker.py --report docs/term-report.md app/

# 自动修复术语问题
python scripts/tools/term_checker.py --fix app/
```
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class TermIssue:
    """【术语问题】术语使用问题详情"""
    file_path: str          # 【文件路径】问题所在文件
    line_number: int        # 【行号】问题所在行
    line_content: str       # 【行内容】问题所在行的内容
    forbidden_term: str     # 【禁用术语】发现的禁用术语
    recommended_term: str   # 【推荐术语】建议使用的术语
    context: str            # 【上下文】术语出现的上下文


@dataclass
class TermStats:
    """【术语统计】术语使用统计信息"""
    term: str               # 【术语】术语名称
    count: int = 0          # 【计数】使用次数
    files: Set[str] = field(default_factory=set)  # 【文件】出现的文件集合
    lines: List[Tuple[str, int]] = field(default_factory=list)  # 【位置】文件和行号


class TermChecker:
    """
    【类职责】
    术语一致性检查器，检查项目中术语使用的统一性
    
    【主要功能】
    1. 禁用术语检测: 检测并报告禁用术语的使用
    2. 术语使用统计: 统计推荐术语的使用情况
    3. 自动修复建议: 提供术语替换建议
    4. 术语一致性报告: 生成术语使用报告
    
    【属性说明】
    - forbidden_terms: 禁用术语映射表
    - recommended_terms: 推荐术语列表
    - term_stats: 术语使用统计
    
    【使用示例】
    ```python
    checker = TermChecker()
    issues = checker.check_file("app/services/cleanup_manager.py")
    ```
    """
    
    # 【禁用术语映射】禁用术语到推荐术语的映射
    FORBIDDEN_TERMS = {
        "垃圾文件": "沉积内容",
        "垃圾": "沉积",
        "控制面板": "仪表盘",
        "面板": "仪表盘",
        "警报": "告警",
        "程序": "脚本",
        "顶点": "节点",
        "临时文件": "沉积内容",
        "系统面板": "仪表盘",
        "错误提示": "告警",
        "后台": "后端",
        "前台": "前端",
        "监视器": "监控",
        "监视": "监控",
        "配置项": "配置",
        "参数项": "参数",
        "函数库": "工具库",
        "类库": "工具库",
        "子程序": "子脚本",
        "主程序": "主脚本",
    }
    
    # 【推荐术语列表】项目中推荐使用的标准术语
    RECOMMENDED_TERMS = [
        "监控", "仪表盘", "告警", "脚本", "DAG", "节点", "边",
        "沉积内容", "重复内容", "事件", "队列", "工作流",
        "前端", "后端", "服务", "路由", "中间件", "模型", "模板",
        "静态资源", "WebSocket", "API", "配置中心", "事件总线",
        "CPU使用率", "内存使用率", "磁盘使用率", "网络延迟",
        "阈值", "告警级别", "紧急", "警告", "提示",
        "任务", "作业", "调度", "并发", "并行", "异步", "同步",
        "数据库", "缓存", "日志", "索引", "事务", "备份", "归档",
        "认证", "授权", "鉴权", "令牌", "会话", "加密", "哈希",
        "优化", "瓶颈", "延迟", "吞吐量", "并发数", "连接池",
        "部署", "发布", "回滚", "灰度", "健康检查", "服务发现",
        "AR", "渲染节点", "渲染任务", "渲染队列", "帧率",
    ]
    
    # 【文件类型】要检查的文件类型
    CHECK_EXTENSIONS = {'.py', '.md', '.html', '.js', '.css', '.json', '.yml', '.yaml'}
    
    def __init__(self):
        """【初始化】创建检查器实例"""
        self.issues: List[TermIssue] = []
        self.term_stats: Dict[str, TermStats] = {
            term: TermStats(term=term) for term in self.RECOMMENDED_TERMS
        }
        self.forbidden_stats: Dict[str, int] = defaultdict(int)
        self.total_files = 0
        self.total_issues = 0
    
    def check_file(self, file_path: str) -> List[TermIssue]:
        """
        【检查文件】检查单个文件的术语使用
        
        【参数说明】
        - file_path (str): 要检查的文件路径
        
        【返回值】
        - List[TermIssue]: 发现的术语问题列表
        
        【使用示例】
        ```python
        issues = checker.check_file("app/services/cleanup_manager.py")
        for issue in issues:
            print(f"{issue.file_path}:{issue.line_number} - {issue.forbidden_term}")
        ```
        """
        issues = []
        path = Path(file_path)
        
        # 【文件存在性检查】
        if not path.exists():
            return issues
        
        # 【文件类型检查】
        if path.suffix not in self.CHECK_EXTENSIONS:
            return issues
        
        try:
            # 【读取文件内容】
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # 【逐行检查】
            for line_num, line in enumerate(lines, 1):
                # 【检查禁用术语】
                for forbidden, recommended in self.FORBIDDEN_TERMS.items():
                    # 【使用正则匹配完整单词】
                    pattern = r'(?<![\w])' + re.escape(forbidden) + r'(?![\w])'
                    matches = list(re.finditer(pattern, line))
                    
                    for match in matches:
                        # 【提取上下文】
                        start = max(0, match.start() - 20)
                        end = min(len(line), match.end() + 20)
                        context = line[start:end]
                        
                        issue = TermIssue(
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line.strip(),
                            forbidden_term=forbidden,
                            recommended_term=recommended,
                            context=context
                        )
                        issues.append(issue)
                        self.forbidden_stats[forbidden] += 1
                
                # 【统计推荐术语】
                for term in self.RECOMMENDED_TERMS:
                    # 【使用正则匹配完整单词】
                    pattern = r'(?<![\w])' + re.escape(term) + r'(?![\w])'
                    matches = re.findall(pattern, line)
                    
                    if matches:
                        self.term_stats[term].count += len(matches)
                        self.term_stats[term].files.add(file_path)
                        self.term_stats[term].lines.append((file_path, line_num))
            
            self.total_files += 1
            
        except Exception as e:
            print(f"【警告】无法读取文件 {file_path}: {e}")
        
        self.issues.extend(issues)
        self.total_issues += len(issues)
        
        return issues
    
    def check_directory(self, directory: str, 
                        recursive: bool = True,
                        exclude_patterns: List[str] = None) -> List[TermIssue]:
        """
        【检查目录】检查目录下所有文件
        
        【参数说明】
        - directory (str): 要检查的目录路径
        - recursive (bool): 是否递归检查子目录，默认为True
        - exclude_patterns (List[str]): 排除的文件模式列表
        
        【返回值】
        - List[TermIssue]: 所有发现的术语问题列表
        
        【使用示例】
        ```python
        issues = checker.check_directory("app/", recursive=True)
        ```
        """
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '.git', 'venv', 'env', 'node_modules', '.pytest_cache']
        
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"【错误】目录不存在: {directory}")
            return []
        
        all_issues = []
        
        # 【查找文件】
        if recursive:
            files = list(dir_path.rglob("*"))
        else:
            files = list(dir_path.glob("*"))
        
        # 【过滤文件】
        check_files = []
        for f in files:
            if f.is_file() and f.suffix in self.CHECK_EXTENSIONS:
                # 【检查排除模式】
                if any(pattern in str(f) for pattern in exclude_patterns):
                    continue
                check_files.append(f)
        
        print(f"【信息】发现 {len(check_files)} 个待检查文件")
        
        # 【逐个检查】
        for i, file_path in enumerate(check_files, 1):
            if i % 50 == 0:
                print(f"【进度】已检查 {i}/{len(check_files)} 个文件...")
            
            issues = self.check_file(str(file_path))
            if issues:
                all_issues.extend(issues)
        
        return all_issues
    
    def generate_fix_suggestions(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        【生成修复建议】生成文件级别的修复建议
        
        【返回值】
        - Dict[str, List[Tuple[str, str]]]: 文件路径到替换建议的映射
        
        【使用示例】
        ```python
        suggestions = checker.generate_fix_suggestions()
        for file_path, replacements in suggestions.items():
            for old, new in replacements:
                print(f"{file_path}: '{old}' -> '{new}'")
        ```
        """
        suggestions = defaultdict(list)
        
        for issue in self.issues:
            suggestions[issue.file_path].append(
                (issue.forbidden_term, issue.recommended_term)
            )
        
        return dict(suggestions)
    
    def apply_fixes(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        【应用修复】自动修复术语问题
        
        【参数说明】
        - dry_run (bool): 是否为模拟运行，默认为True
        
        【返回值】
        - Dict[str, Any]: 修复结果统计
        
        【使用示例】
        ```python
        # 先模拟运行
        result = checker.apply_fixes(dry_run=True)
        print(f"将修复 {result['total_replacements']} 处问题")
        
        # 确认后实际修复
        result = checker.apply_fixes(dry_run=False)
        ```
        """
        results = {
            "dry_run": dry_run,
            "files_modified": 0,
            "total_replacements": 0,
            "details": []
        }
        
        # 【按文件分组】
        file_issues = defaultdict(list)
        for issue in self.issues:
            file_issues[issue.file_path].append(issue)
        
        # 【逐个文件修复】
        for file_path, issues in file_issues.items():
            try:
                path = Path(file_path)
                content = path.read_text(encoding='utf-8')
                original_content = content
                
                # 【执行替换】
                replacements = 0
                for issue in issues:
                    # 【从后向前替换，避免位置变化】
                    forbidden = issue.forbidden_term
                    recommended = issue.recommended_term
                    
                    # 【使用正则替换】
                    pattern = r'(?<![\w])' + re.escape(forbidden) + r'(?![\w])'
                    new_content, count = re.subn(pattern, recommended, content)
                    
                    if count > 0:
                        content = new_content
                        replacements += count
                
                # 【保存文件】
                if not dry_run and content != original_content:
                    path.write_text(content, encoding='utf-8')
                    results["files_modified"] += 1
                
                results["total_replacements"] += replacements
                results["details"].append({
                    "file": file_path,
                    "replacements": replacements
                })
                
            except Exception as e:
                results["details"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        return results
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        【生成报告】生成术语检查报告
        
        【参数说明】
        - output_path (str, 可选): 报告输出路径
        
        【返回值】
        - str: 报告内容
        
        【使用示例】
        ```python
        report = checker.generate_report("docs/term-report.md")
        ```
        """
        lines = []
        
        # 【报告头】
        lines.append("# 术语一致性检查报告")
        lines.append(f"")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**检查文件数**: {self.total_files}")
        lines.append(f"**发现问题数**: {self.total_issues}")
        lines.append(f"")
        
        # 【摘要】
        lines.append("## 检查摘要")
        lines.append(f"")
        
        if self.total_issues == 0:
            lines.append("✅ 未发现术语使用问题！")
        else:
            lines.append(f"⚠️ 发现 {self.total_issues} 处术语使用问题，需要修复")
        
        lines.append(f"")
        
        # 【禁用术语统计】
        lines.append("## 禁用术语使用情况")
        lines.append(f"")
        
        if self.forbidden_stats:
            lines.append("| 禁用术语 | 使用次数 | 推荐替换 |")
            lines.append("|----------|----------|----------|")
            
            # 【按使用次数排序】
            sorted_terms = sorted(
                self.forbidden_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for term, count in sorted_terms:
                recommended = self.FORBIDDEN_TERMS.get(term, "未知")
                lines.append(f"| {term} | {count} | {recommended} |")
        else:
            lines.append("未发现禁用术语使用")
        
        lines.append(f"")
        
        # 【推荐术语统计】
        lines.append("## 推荐术语使用情况")
        lines.append(f"")
        lines.append("| 推荐术语 | 使用次数 | 出现文件数 |")
        lines.append("|----------|----------|------------|")
        
        # 【按使用次数排序】
        sorted_stats = sorted(
            self.term_stats.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        for term, stats in sorted_stats[:30]:  # 【只显示前30个】
            if stats.count > 0:
                lines.append(f"| {term} | {stats.count} | {len(stats.files)} |")
        
        lines.append(f"")
        
        # 【详细问题】
        if self.issues:
            lines.append("## 详细问题列表")
            lines.append(f"")
            lines.append("| 文件 | 行号 | 禁用术语 | 推荐术语 | 上下文 |")
            lines.append("|------|------|----------|----------|--------|")
            
            # 【按文件排序】
            sorted_issues = sorted(self.issues, key=lambda x: (x.file_path, x.line_number))
            
            for issue in sorted_issues[:100]:  # 【只显示前100个】
                # 【截断上下文】
                context = issue.context[:50] + "..." if len(issue.context) > 50 else issue.context
                context = context.replace("|", "\\|")  # 【转义表格字符】
                
                lines.append(f"| {issue.file_path} | {issue.line_number} | {issue.forbidden_term} | {issue.recommended_term} | {context} |")
            
            if len(self.issues) > 100:
                lines.append(f"| ... | ... | ... | ... | 还有 {len(self.issues) - 100} 个问题未显示 |")
            
            lines.append(f"")
        
        # 【修复建议】
        lines.append("## 修复建议")
        lines.append(f"")
        lines.append("### 手动修复")
        lines.append("1. 根据上表中的'详细问题列表'逐个文件修复")
        lines.append("2. 将'禁用术语'替换为'推荐术语'")
        lines.append(f"")
        lines.append("### 自动修复")
        lines.append("运行以下命令自动修复术语问题：")
        lines.append(f"```bash")
        lines.append(f"python scripts/tools/term_checker.py --fix app/")
        lines.append(f"```")
        lines.append(f"")
        lines.append("⚠️ **注意**: 自动修复前建议先备份代码或提交到版本控制")
        lines.append(f"")
        
        # 【术语表参考】
        lines.append("## 术语表参考")
        lines.append(f"")
        lines.append("完整的术语定义请参考：[术语表](../../docs/terminology-glossary.md)")
        lines.append(f"")
        
        report = '\n'.join(lines)
        
        # 【保存报告】
        if output_path:
            Path(output_path).write_text(report, encoding='utf-8')
            print(f"【信息】报告已保存: {output_path}")
        
        return report
    
    def print_summary(self) -> None:
        """【打印摘要】打印检查摘要到控制台"""
        print(f"\n{'='*60}")
        print("【术语检查完成】")
        print(f"{'='*60}")
        print(f"检查文件数: {self.total_files}")
        print(f"发现问题数: {self.total_issues}")
        
        if self.forbidden_stats:
            print(f"\n【禁用术语使用统计】")
            sorted_terms = sorted(
                self.forbidden_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for term, count in sorted_terms[:10]:
                recommended = self.FORBIDDEN_TERMS.get(term, "未知")
                print(f"  {term} -> {recommended}: {count}次")
        
        print(f"{'='*60}")
        
        if self.total_issues == 0:
            print("✅ 术语使用规范！")
        else:
            print(f"⚠️ 发现 {self.total_issues} 处术语问题")
        
        print(f"{'='*60}\n")


def main():
    """
    【主函数】命令行入口
    
    【使用示例】
    ```bash
    # 检查术语一致性
    python scripts/tools/term_checker.py app/
    
    # 生成报告
    python scripts/tools/term_checker.py --report docs/term-report.md app/
    
    # 自动修复（模拟运行）
    python scripts/tools/term_checker.py --fix --dry-run app/
    
    # 自动修复（实际执行）
    python scripts/tools/term_checker.py --fix app/
    ```
    """
    parser = argparse.ArgumentParser(
        description="术语一致性检查工具 - 检查项目中术语使用的统一性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s app/
  %(prog)s --report docs/term-report.md app/
  %(prog)s --fix --dry-run app/
  %(prog)s --fix app/
        """
    )
    
    parser.add_argument(
        "path",
        help="要检查的文件或目录路径"
    )
    
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=True,
        help="递归检查子目录（默认启用）"
    )
    
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="生成检查报告到指定路径"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复术语问题"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行（不实际修改文件）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    # 【创建检查器】
    checker = TermChecker()
    
    # 【执行检查】
    path = Path(args.path)
    
    if path.is_file():
        print(f"【检查文件】{path}")
        checker.check_file(str(path))
    
    elif path.is_dir():
        print(f"【检查目录】{path}")
        checker.check_directory(str(path), recursive=args.recursive)
    
    else:
        print(f"【错误】路径不存在: {path}")
        sys.exit(1)
    
    # 【自动修复】
    if args.fix:
        print(f"\n【自动修复】{'模拟运行' if args.dry_run else '实际执行'}")
        fix_results = checker.apply_fixes(dry_run=args.dry_run)
        
        print(f"文件修改: {fix_results['files_modified']}")
        print(f"替换次数: {fix_results['total_replacements']}")
        
        if args.dry_run:
            print("\n⚠️ 这是模拟运行，未实际修改文件")
            print("确认无误后，去掉 --dry-run 参数执行实际修复")
    
    # 【打印摘要】
    checker.print_summary()
    
    # 【生成报告】
    if args.report:
        checker.generate_report(args.report)
    
    # 【返回退出码】
    sys.exit(0 if checker.total_issues == 0 else 1)


if __name__ == "__main__":
    main()
