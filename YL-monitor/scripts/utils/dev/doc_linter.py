#!/usr/bin/env python3
"""
【文件功能】
文档规范检查工具，用于检查Python文件的中文注释规范性和术语一致性

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现基础检查功能

【依赖说明】
- 标准库: argparse, ast, os, re, sys, json, pathlib
- 第三方库: 无
- 内部模块: 无

【使用示例】
```bash
# 检查单个文件
python scripts/tools/doc_linter.py app/services/cleanup_manager.py

# 检查整个目录
python scripts/tools/doc_linter.py app/services/ --recursive

# 生成检查报告
python scripts/tools/doc_linter.py --report docs/lint-report.md app/
```
"""

import argparse
import ast
import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class LintIssue:
    """【检查问题】单个检查问题的详细信息"""
    file_path: str          # 【文件路径】问题所在文件
    line_number: int        # 【行号】问题所在行
    issue_type: str         # 【问题类型】error/warning/info
    category: str           # 【问题分类】file_header/class_doc/method_doc等
    message: str            # 【问题描述】详细说明
    suggestion: str         # 【修复建议】如何修复


@dataclass
class LintResult:
    """【检查结果】单个文件的检查结果"""
    file_path: str
    issues: List[LintIssue] = field(default_factory=list)
    checked: bool = False
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    
    def add_issue(self, issue: LintIssue) -> None:
        """【添加问题】添加检查问题并更新计数"""
        self.issues.append(issue)
        if issue.issue_type == "error":
            self.error_count += 1
        elif issue.issue_type == "warning":
            self.warning_count += 1
        else:
            self.info_count += 1


class DocLinter:
    """
    【类职责】
    文档规范检查器，检查Python文件的中文注释规范性
    
    【主要功能】
    1. 文件头检查: 检查文件头信息完整性
    2. 类注释检查: 检查类文档字符串规范性
    3. 方法注释检查: 检查方法文档字符串规范性
    4. 术语检查: 检查术语使用一致性
    
    【属性说明】
    - required_sections: 文件头必需章节列表
    - forbidden_terms: 禁用术语列表
    - recommended_terms: 推荐术语列表
    
    【使用示例】
    ```python
    linter = DocLinter()
    result = linter.lint_file("app/services/cleanup_manager.py")
    ```
    """
    
    # 【必需章节】文件头必须包含的章节
    REQUIRED_SECTIONS = [
        "【文件功能】",
        "【作者信息】",
        "【版本历史】",
        "【依赖说明】",
        "【使用示例】"
    ]
    
    # 【禁用术语】应避免使用的术语
    FORBIDDEN_TERMS = [
        ("垃圾文件", "沉积内容"),
        ("控制面板", "仪表盘"),
        ("警报", "告警"),
        ("程序", "脚本"),
        ("顶点", "节点"),
        ("临时文件", "沉积内容"),
        ("系统面板", "仪表盘"),
        ("错误提示", "告警"),
        ("后台", "后端"),
        ("前台", "前端"),
    ]
    
    # 【类必需章节】类文档字符串必须包含的章节
    CLASS_REQUIRED_SECTIONS = [
        "【类职责】",
        "【主要功能】",
    ]
    
    # 【方法必需章节】方法文档字符串建议包含的章节
    METHOD_SUGGESTED_SECTIONS = [
        "【方法功能】",
        "【参数说明】",
        "【返回值】",
    ]
    
    def __init__(self):
        """【初始化】创建检查器实例"""
        self.results: List[LintResult] = []
        self.total_files = 0
        self.total_errors = 0
        self.total_warnings = 0
        self.total_infos = 0
    
    def lint_file(self, file_path: str) -> LintResult:
        """
        【检查文件】检查单个Python文件的文档规范
        
        【参数说明】
        - file_path (str): 要检查的文件路径
        
        【返回值】
        - LintResult: 检查结果对象
        
        【使用示例】
        ```python
        result = linter.lint_file("app/services/cleanup_manager.py")
        print(f"发现 {result.error_count} 个错误")
        ```
        """
        result = LintResult(file_path=file_path)
        path = Path(file_path)
        
        # 【文件存在性检查】
        if not path.exists():
            result.add_issue(LintIssue(
                file_path=file_path,
                line_number=0,
                issue_type="error",
                category="file_access",
                message="文件不存在",
                suggestion="检查文件路径是否正确"
            ))
            return result
        
        # 【文件类型检查】
        if not file_path.endswith('.py'):
            result.add_issue(LintIssue(
                file_path=file_path,
                line_number=0,
                issue_type="info",
                category="file_type",
                message="非Python文件，跳过检查",
                suggestion="仅检查.py文件"
            ))
            return result
        
        try:
            # 【读取文件内容】
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # 【文件头检查】
            self._check_file_header(content, lines, result)
            
            # 【术语检查】
            self._check_terminology(content, lines, result)
            
            # 【AST解析检查】
            self._check_ast(content, file_path, result)
            
            result.checked = True
            
        except Exception as e:
            result.add_issue(LintIssue(
                file_path=file_path,
                line_number=0,
                issue_type="error",
                category="parse_error",
                message=f"文件解析失败: {str(e)}",
                suggestion="检查文件编码和语法"
            ))
        
        return result
    
    def _check_file_header(self, content: str, lines: List[str], 
                          result: LintResult) -> None:
        """
        【检查文件头】检查文件头注释的完整性
        
        【参数说明】
        - content (str): 文件完整内容
        - lines (List[str]): 文件行列表
        - result (LintResult): 检查结果对象
        """
        # 【提取文件头】查找开头的三引号注释
        header_match = re.search(r'^("""|\'\'\')([\s\S]*?)\\1', content)
        
        if not header_match:
            result.add_issue(LintIssue(
                file_path=result.file_path,
                line_number=1,
                issue_type="error",
                category="file_header",
                message="缺少文件头注释",
                suggestion="在文件开头添加三引号包裹的文件头注释"
            ))
            return
        
        header_content = header_match.group(2)
        header_lines = header_content.split('\n')
        header_start_line = 1
        
        # 【检查必需章节】
        for section in self.REQUIRED_SECTIONS:
            if section not in header_content:
                result.add_issue(LintIssue(
                    file_path=result.file_path,
                    line_number=header_start_line,
                    issue_type="error",
                    category="file_header",
                    message=f"文件头缺少必需章节: {section}",
                    suggestion=f"在文件头中添加 {section} 章节"
                ))
        
        # 【检查作者信息】
        if "【作者信息】" in header_content:
            author_patterns = [
                r"作者\s*[:：]\s*\S+",
                r"创建时间\s*[:：]\s*\d{4}-\d{2}-\d{2}",
                r"最后更新\s*[:：]\s*\d{4}-\d{2}-\d{2}"
            ]
            for pattern in author_patterns:
                if not re.search(pattern, header_content):
                    result.add_issue(LintIssue(
                        file_path=result.file_path,
                        line_number=header_start_line,
                        issue_type="warning",
                        category="file_header",
                        message=f"作者信息格式不完整，缺少: {pattern}",
                        suggestion="完善作者信息格式"
                    ))
    
    def _check_terminology(self, content: str, lines: List[str],
                          result: LintResult) -> None:
        """
        【检查术语】检查术语使用的一致性
        
        【参数说明】
        - content (str): 文件完整内容
        - lines (List[str]): 文件行列表
        - result (LintResult): 检查结果对象
        """
        for forbidden, recommended in self.FORBIDDEN_TERMS:
            # 【查找禁用术语】使用正则匹配完整单词
            pattern = r'(?<![\w])' + re.escape(forbidden) + r'(?![\w])'
            matches = list(re.finditer(pattern, content))
            
            for match in matches:
                # 【计算行号】
                line_num = content[:match.start()].count('\n') + 1
                
                result.add_issue(LintIssue(
                    file_path=result.file_path,
                    line_number=line_num,
                    issue_type="warning",
                    category="terminology",
                    message=f"发现禁用术语: '{forbidden}'",
                    suggestion=f"建议使用推荐术语: '{recommended}'"
                ))
    
    def _check_ast(self, content: str, file_path: str, 
                   result: LintResult) -> None:
        """
        【AST检查】使用AST解析检查类和函数的文档字符串
        
        【参数说明】
        - content (str): 文件完整内容
        - file_path (str): 文件路径
        - result (LintResult): 检查结果对象
        """
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            result.add_issue(LintIssue(
                file_path=file_path,
                line_number=e.lineno or 1,
                issue_type="error",
                category="syntax_error",
                message=f"语法错误: {e.msg}",
                suggestion="修复语法错误"
            ))
            return
        
        # 【遍历AST节点】
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._check_class_docstring(node, result)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                self._check_function_docstring(node, result)
    
    def _check_class_docstring(self, node: ast.ClassDef, 
                               result: LintResult) -> None:
        """
        【检查类文档】检查类的文档字符串
        
        【参数说明】
        - node (ast.ClassDef): 类定义节点
        - result (LintResult): 检查结果对象
        """
        docstring = ast.get_docstring(node)
        
        if not docstring:
            result.add_issue(LintIssue(
                file_path=result.file_path,
                line_number=node.lineno,
                issue_type="warning",
                category="class_doc",
                message=f"类 '{node.name}' 缺少文档字符串",
                suggestion="为类添加描述性文档字符串"
            ))
            return
        
        # 【检查必需章节】
        for section in self.CLASS_REQUIRED_SECTIONS:
            if section not in docstring:
                result.add_issue(LintIssue(
                    file_path=result.file_path,
                    line_number=node.lineno,
                    issue_type="warning",
                    category="class_doc",
                    message=f"类 '{node.name}' 文档缺少章节: {section}",
                    suggestion=f"在类文档中添加 {section}"
                ))
    
    def _check_function_docstring(self, node: ast.FunctionDef, 
                                   result: LintResult) -> None:
        """
        【检查函数文档】检查函数的文档字符串
        
        【参数说明】
        - node (ast.FunctionDef): 函数定义节点
        - result (LintResult): 检查结果对象
        """
        # 【跳过私有函数】
        if node.name.startswith('_'):
            return
        
        docstring = ast.get_docstring(node)
        
        if not docstring:
            result.add_issue(LintIssue(
                file_path=result.file_path,
                line_number=node.lineno,
                issue_type="info",
                category="method_doc",
                message=f"函数 '{node.name}' 缺少文档字符串",
                suggestion="为公共函数添加文档字符串"
            ))
            return
        
        # 【检查建议章节】
        for section in self.METHOD_SUGGESTED_SECTIONS:
            if section not in docstring:
                result.add_issue(LintIssue(
                    file_path=result.file_path,
                    line_number=node.lineno,
                    issue_type="info",
                    category="method_doc",
                    message=f"函数 '{node.name}' 文档建议添加: {section}",
                    suggestion=f"考虑添加 {section} 以提高文档完整性"
                ))
    
    def lint_directory(self, directory: str, recursive: bool = True) -> List[LintResult]:
        """
        【检查目录】检查目录下所有Python文件
        
        【参数说明】
        - directory (str): 要检查的目录路径
        - recursive (bool): 是否递归检查子目录，默认为True
        
        【返回值】
        - List[LintResult]: 所有文件的检查结果列表
        
        【使用示例】
        ```python
        results = linter.lint_directory("app/services/", recursive=True)
        ```
        """
        results = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"【错误】目录不存在: {directory}")
            return results
        
        # 【查找Python文件】
        if recursive:
            py_files = list(dir_path.rglob("*.py"))
        else:
            py_files = list(dir_path.glob("*.py"))
        
        print(f"【信息】发现 {len(py_files)} 个Python文件")
        
        # 【逐个检查】
        for py_file in py_files:
            # 【跳过特定目录】
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', 'env']):
                continue
            
            print(f"【检查】{py_file}")
            result = self.lint_file(str(py_file))
            results.append(result)
            
            # 【更新统计】
            self.total_files += 1
            self.total_errors += result.error_count
            self.total_warnings += result.warning_count
            self.total_infos += result.info_count
        
        self.results = results
        return results
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        【生成报告】生成检查报告
        
        【参数说明】
        - output_path (str, 可选): 报告输出路径，默认为None（仅返回字符串）
        
        【返回值】
        - str: 报告内容
        
        【使用示例】
        ```python
        report = linter.generate_report("docs/lint-report.md")
        ```
        """
        lines = []
        
        # 【报告头】
        lines.append("# 文档规范检查报告")
        lines.append(f"")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**检查文件数**: {self.total_files}")
        lines.append(f"**错误数**: {self.total_errors}")
        lines.append(f"**警告数**: {self.total_warnings}")
        lines.append(f"**提示数**: {self.total_infos}")
        lines.append(f"")
        
        # 【摘要】
        lines.append("## 检查摘要")
        lines.append(f"")
        lines.append("| 文件路径 | 错误 | 警告 | 提示 | 状态 |")
        lines.append("|----------|------|------|------|------|")
        
        for result in self.results:
            status = "✅ 通过" if result.error_count == 0 else "❌ 失败"
            lines.append(f"| {result.file_path} | {result.error_count} | {result.warning_count} | {result.info_count} | {status} |")
        
        lines.append(f"")
        
        # 【详细问题】
        lines.append("## 详细问题")
        lines.append(f"")
        
        for result in self.results:
            if not result.issues:
                continue
            
            lines.append(f"### {result.file_path}")
            lines.append(f"")
            lines.append("| 行号 | 类型 | 分类 | 问题 | 建议 |")
            lines.append("|------|------|------|------|------|")
            
            for issue in result.issues:
                type_emoji = "🔴" if issue.issue_type == "error" else "🟡" if issue.issue_type == "warning" else "🔵"
                lines.append(f"| {issue.line_number} | {type_emoji} {issue.issue_type} | {issue.category} | {issue.message} | {issue.suggestion} |")
            
            lines.append(f"")
        
        # 【建议】
        lines.append("## 修复建议")
        lines.append(f"")
        lines.append("### 高优先级（错误）")
        lines.append("1. 为所有文件添加完整的文件头注释")
        lines.append("2. 确保文件头包含所有必需章节")
        lines.append("3. 修复术语使用不一致的问题")
        lines.append(f"")
        lines.append("### 中优先级（警告）")
        lines.append("1. 为所有公共类添加文档字符串")
        lines.append("2. 完善类文档的必需章节")
        lines.append("3. 替换禁用术语为推荐术语")
        lines.append(f"")
        lines.append("### 低优先级（提示）")
        lines.append("1. 为公共函数添加文档字符串")
        lines.append("2. 完善函数文档的建议章节")
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
        print("【检查完成】")
        print(f"{'='*60}")
        print(f"检查文件数: {self.total_files}")
        print(f"错误数: {self.total_errors} 🔴")
        print(f"警告数: {self.total_warnings} 🟡")
        print(f"提示数: {self.total_infos} 🔵")
        print(f"{'='*60}")
        
        if self.total_errors == 0:
            print("✅ 所有文件通过检查！")
        else:
            print(f"❌ 发现 {self.total_errors} 个错误，需要修复")
        
        print(f"{'='*60}\n")


def main():
    """
    【主函数】命令行入口
    
    【使用示例】
    ```bash
    python scripts/tools/doc_linter.py app/services/cleanup_manager.py
    python scripts/tools/doc_linter.py app/ --recursive
    python scripts/tools/doc_linter.py --report docs/lint-report.md app/
    ```
    """
    parser = argparse.ArgumentParser(
        description="文档规范检查工具 - 检查Python文件的中文注释规范性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s app/services/cleanup_manager.py
  %(prog)s app/ --recursive
  %(prog)s --report docs/lint-report.md app/
        """
    )
    
    parser.add_argument(
        "path",
        help="要检查的文件或目录路径"
    )
    
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="递归检查子目录"
    )
    
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="生成检查报告到指定路径"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    # 【创建检查器】
    linter = DocLinter()
    
    # 【执行检查】
    path = Path(args.path)
    
    if path.is_file():
        print(f"【检查文件】{path}")
        result = linter.lint_file(str(path))
        linter.results = [result]
        linter.total_files = 1
        linter.total_errors = result.error_count
        linter.total_warnings = result.warning_count
        linter.total_infos = result.info_count
        
        # 【显示详细结果】
        if args.verbose:
            for issue in result.issues:
                emoji = "🔴" if issue.issue_type == "error" else "🟡" if issue.issue_type == "warning" else "🔵"
                print(f"  {emoji} 第{issue.line_number}行 [{issue.category}] {issue.message}")
                print(f"     建议: {issue.suggestion}")
    
    elif path.is_dir():
        print(f"【检查目录】{path}")
        linter.lint_directory(str(path), recursive=args.recursive)
    
    else:
        print(f"【错误】路径不存在: {path}")
        sys.exit(1)
    
    # 【打印摘要】
    linter.print_summary()
    
    # 【生成报告】
    if args.report:
        linter.generate_report(args.report)
    
    # 【返回退出码】
    sys.exit(0 if linter.total_errors == 0 else 1)


if __name__ == "__main__":
    main()
