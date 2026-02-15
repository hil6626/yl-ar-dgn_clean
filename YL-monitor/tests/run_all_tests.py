#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试执行入口

【功能描述】
提供统一的测试执行入口，支持运行所有测试或特定类型的测试

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0

【依赖】
pytest>=7.0.0

【使用方法】
    # 运行所有测试
    python tests/run_all_tests.py
    
    # 运行集成测试
    python tests/run_all_tests.py --type integration
    
    # 运行性能测试
    python tests/run_all_tests.py --type performance
    
    # 运行UAT测试
    python tests/run_all_tests.py --type uat
    
    # 生成测试报告
    python tests/run_all_tests.py --report

【命令行参数】
    --type: 测试类型 (all|integration|performance|uat)
    --report: 生成HTML测试报告
    --verbose: 详细输出
    --coverage: 生成覆盖率报告
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


def run_tests(test_type: str = "all", verbose: bool = False, coverage: bool = False, report: bool = False):
    """
    【函数】运行测试
    
    【功能】根据类型运行相应的测试
    
    【参数】
        test_type: 测试类型 (all|integration|performance|uat)
        verbose: 是否详细输出
        coverage: 是否生成覆盖率报告
        report: 是否生成HTML报告
    
    【返回】
        int: 退出码 (0=成功, 1=失败)
    """
    # 【构建】pytest命令
    cmd = ["pytest"]
    
    # 【添加】测试路径
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "performance":
        cmd.append("tests/performance/")
    elif test_type == "uat":
        cmd.append("tests/uat/")
    else:
        print(f"错误: 未知的测试类型 '{test_type}'")
        return 1
    
    # 【添加】输出选项
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    else:
        cmd.append("-v")
    
    # 【添加】覆盖率
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    # 【添加】HTML报告
    if report:
        report_dir = Path("tests/reports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"test_report_{timestamp}.html"
        cmd.extend([f"--html={report_file}", "--self-contained-html"])
        print(f"测试报告将保存至: {report_file}")
    
    # 【添加】其他选项
    cmd.extend([
        "--strict-markers",
        "--disable-warnings",
        "-x",  # 遇到第一个失败时停止
    ])
    
    # 【执行】测试
    print(f"\n{'='*60}")
    print(f"【开始执行测试】")
    print(f"测试类型: {test_type}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"执行测试时出错: {e}")
        return 1


def print_test_summary():
    """
    【函数】打印测试摘要
    
    【功能】打印测试类型说明
    """
    print("""
【YL-Monitor 测试体系】

测试类型说明:
  1. 集成测试 (integration)
     - 验证模块间的联动性
     - 测试数据流转和接口兼容性
     - 文件: tests/integration/

  2. 性能测试 (performance)
     - 验证前端性能指标 (FCP, LCP, FPS)
     - 验证API性能 (响应时间, 吞吐量)
     - 文件: tests/performance/

  3. 用户验收测试 (uat)
     - 验证功能完整性
     - 验证用户体验
     - 文件: tests/uat/

使用示例:
  python tests/run_all_tests.py                    # 运行所有测试
  python tests/run_all_tests.py --type integration # 运行集成测试
  python tests/run_all_tests.py --type performance # 运行性能测试
  python tests/run_all_tests.py --type uat         # 运行UAT测试
  python tests/run_all_tests.py --report           # 生成HTML报告
  python tests/run_all_tests.py --coverage         # 生成覆盖率报告
""")


def main():
    """
    【主函数】命令行入口
    
    【功能】解析命令行参数并执行测试
    """
    parser = argparse.ArgumentParser(
        description="YL-Monitor 统一测试执行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/run_all_tests.py --type integration --verbose
  python tests/run_all_tests.py --type performance --report
  python tests/run_all_tests.py --coverage
        """
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "integration", "performance", "uat"],
        default="all",
        help="测试类型 (默认: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="生成HTML测试报告"
    )
    
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="显示测试体系信息"
    )
    
    args = parser.parse_args()
    
    # 【显示】测试信息
    if args.info:
        print_test_summary()
        return 0
    
    # 【运行】测试
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        report=args.report
    )
    
    # 【输出】结果
    print(f"\n{'='*60}")
    if exit_code == 0:
        print("【测试结果】✓ 所有测试通过")
    else:
        print("【测试结果】✗ 部分测试失败")
    print(f"{'='*60}\n")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
