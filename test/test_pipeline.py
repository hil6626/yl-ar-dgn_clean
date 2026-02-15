#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试流水线（本地）
AR 综合实时合成与监控系统

功能:
- 本地自动测试执行
- 测试结果报告（本地JSON/HTML）
- 测试失败本地告警
- 测试覆盖率统计

注意: 本流水线专注于本地测试，不涉及GitHub/GitLab等远程仓库CI/CD配置

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import sys
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

from test_utils import find_project_root, add_project_paths

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestAutomationPipeline:
    """
    自动化测试流水线类
    
    功能:
    - 自动执行所有测试
    - 生成测试报告
    - 失败告警通知
    - 测试覆盖率统计
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化测试流水线
        
        Args:
            config: 配置参数
        """
        self.config = {
            'test_dir': 'test',
            'output_dir': 'reports',
            'coverage': True,
            'verbose': True,
            'fail_fast': False,
            'parallel': False,
            'max_workers': 4,
        }
        if config:
            self.config.update(config)
        
        # 测试结果
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'duration': 0,
            'timestamp': None,
            'failures': [],
            'errors_list': [],
        }
        
        # 项目根目录
        self.project_root = find_project_root(Path(__file__).resolve())
        add_project_paths(self.project_root)
        self.test_dir = self.project_root / self.config['test_dir']
        self.output_dir = self.project_root / self.config['output_dir']

        # 覆盖率目标
        self.coverage_targets = [
            str(self.project_root / "AR-backend"),
        ]
        if not any(Path(target).exists() for target in self.coverage_targets):
            self.config['coverage'] = False
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_all_tests(self) -> Dict:
        """
        运行所有测试
        
        Returns:
            Dict: 测试结果
        """
        logger.info("开始自动化测试流水线...")
        start_time = time.time()
        
        # 收集测试套件
        test_suites = self._collect_test_suites()
        
        # 运行测试
        for suite_name, suite_path in test_suites.items():
            logger.info(f"运行测试套件: {suite_name}")
            suite_result = self._run_test_suite(suite_path, suite_name)
            self._merge_results(suite_result)
        
        # 计算总时间
        self.results['duration'] = time.time() - start_time
        self.results['timestamp'] = datetime.now().isoformat()
        
        # 生成报告
        self._generate_report()
        
        logger.info(f"测试流水线完成: {self.results['passed']}/{self.results['total_tests']} 通过")
        
        return self.results
    
    def _collect_test_suites(self) -> Dict[str, Path]:
        """
        收集测试套件
        
        Returns:
            Dict[str, Path]: 测试套件名称和路径
        """
        test_suites = {}
        
        # 单元测试
        unit_test_dir = self.test_dir / 'test_backend'
        if unit_test_dir.exists():
            for f in unit_test_dir.glob('test_*.py'):
                if f.is_file():
                    test_suites[f.stem] = f
        
        # 集成测试
        integration_test = self.test_dir / 'integration' / 'test_modules.py'
        if integration_test.exists():
            test_suites['integration'] = integration_test
        
        # 性能测试
        performance_test = self.test_dir / 'performance' / 'test_performance.py'
        if performance_test.exists():
            test_suites['performance'] = performance_test
        
        # 稳定性测试
        stability_test = self.test_dir / 'stability' / 'test_stability.py'
        if stability_test.exists():
            test_suites['stability'] = stability_test
        
        return test_suites
    
    def _run_test_suite(self, test_path: Path, suite_name: str) -> Dict:
        """
        运行测试套件
        
        Args:
            test_path: 测试文件路径
            suite_name: 测试套件名称
            
        Returns:
            Dict: 测试结果
        """
        result = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'duration': 0,
            'failures': [],
            'errors_list': [],
        }
        
        start_time = time.time()
        
        # 构建pytest命令
        json_report_path = self.output_dir / f'{suite_name}_result.json'

        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_path),
            '-v', '--tb=short',
            '--json-report', '--json-report-file=' + str(json_report_path)
        ]
        
        if self.config['fail_fast']:
            cmd.append('-x')
        
        if self.config['coverage']:
            for target in self.coverage_targets:
                if Path(target).exists():
                    cmd.append(f'--cov={target}')
            cmd.append('--cov-report=term-missing')
        
        try:
            # 执行测试
            process = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 解析JSON报告结果
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    summary = report.get('summary', {})
                    result['total_tests'] = summary.get('total', 0)
                    result['passed'] = summary.get('passed', 0)
                    result['failed'] = summary.get('failed', 0)
                    result['errors'] = summary.get('errors', 0)
                    result['skipped'] = summary.get('skipped', 0)
                except Exception:
                    result['passed'] = self._count_tests(process.stdout, 'passed')
                    result['failed'] = self._count_tests(process.stdout, 'failed')
                    result['errors'] = self._count_tests(process.stdout, 'error')
            else:
                result['passed'] = self._count_tests(process.stdout, 'passed')
                result['failed'] = self._count_tests(process.stdout, 'failed')
                result['errors'] = self._count_tests(process.stdout, 'error')
            
            # 保存输出
            log_file = self.output_dir / f'{suite_name}_output.log'
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(process.stdout)
                f.write(process.stderr)
            
        except subprocess.TimeoutExpired:
            result['errors'] = 1
            result['errors_list'].append(f'{suite_name}: 测试超时')
        except Exception as e:
            result['errors'] = 1
            result['errors_list'].append(f'{suite_name}: {str(e)}')
        
        result['duration'] = time.time() - start_time
        
        return result
    
    def _count_tests(self, output: str, status: str) -> int:
        """
        计算测试数量
        
        Args:
            output: pytest输出
            status: 状态 (passed, failed, error)
            
        Returns:
            int: 测试数量
        """
        try:
            # 尝试解析JSON报告
            # 这里简化处理，实际可以使用pytest的JSON报告
            for line in output.split('\n'):
                if f'{status}' in line.lower():
                    # 提取数字
                    words = line.split()
                    for word in words:
                        if word.isdigit():
                            return int(word)
            return 0
        except Exception:
            return 0
    
    def _merge_results(self, suite_result: Dict) -> None:
        """
        合并测试结果
        
        Args:
            suite_result: 测试套件结果
        """
        self.results['total_tests'] += suite_result['total_tests']
        self.results['passed'] += suite_result['passed']
        self.results['failed'] += suite_result['failed']
        self.results['errors'] += suite_result['errors']
        self.results['skipped'] += suite_result['skipped']
        self.results['duration'] += suite_result['duration']
        self.results['failures'].extend(suite_result.get('failures', []))
        self.results['errors_list'].extend(suite_result.get('errors_list', []))
    
    def _generate_report(self) -> None:
        """
        生成测试报告
        """
        report = {
            'summary': {
                'total_tests': self.results['total_tests'],
                'passed': self.results['passed'],
                'failed': self.results['failed'],
                'errors': self.results['errors'],
                'skipped': self.results['skipped'],
                'pass_rate': self._calculate_pass_rate(),
                'duration_seconds': round(self.results['duration'], 2),
                'timestamp': self.results['timestamp'],
            },
            'failures': self.results['failures'],
            'errors': self.results['errors_list'],
            'config': self.config,
        }
        
        # 保存JSON报告
        report_file = self.output_dir / 'test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成HTML报告
        self._generate_html_report(report)
        
        logger.info(f"测试报告已生成: {report_file}")
    
    def _generate_html_report(self, report: Dict) -> None:
        """
        生成HTML报告
        
        Args:
            report: 测试报告数据
        """
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AR 综合实时合成与监控系统 - 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .error {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
        .duration {{ color: #666; }}
    </style>
</head>
<body>
    <h1>🎯 AR 综合实时合成与监控系统 - 测试报告</h1>
    
    <div class="summary">
        <h2>📊 测试摘要</h2>
        <p>执行时间: {report['summary']['timestamp']}</p>
        <p>总测试数: {report['summary']['total_tests']}</p>
        <p class="pass">✅ 通过: {report['summary']['passed']}</p>
        <p class="fail">❌ 失败: {report['summary']['failed']}</p>
        <p class="error">⚠️ 错误: {report['summary']['errors']}</p>
        <p>通过率: {report['summary']['pass_rate']:.2f}%</p>
        <p class="duration">总耗时: {report['summary']['duration_seconds']}秒</p>
    </div>
    
    <h2>📋 失败详情</h2>
    {self._generate_failure_html(report['failures'])}
    
    <h2>📋 错误详情</h2>
    {self._generate_error_html(report['errors'])}
    
</body>
</html>
        """
        
        html_file = self.output_dir / 'test_report.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _generate_failure_html(self, failures: List) -> str:
        """生成失败详情HTML"""
        if not failures:
            return "<p>无失败记录 ✅</p>"
        
        html = "<table><tr><th>序号</th><th>详情</th></tr>"
        for i, failure in enumerate(failures, 1):
            html += f"<tr><td>{i}</td><td>{failure}</td></tr>"
        html += "</table>"
        return html
    
    def _generate_error_html(self, errors: List) -> str:
        """生成错误详情HTML"""
        if not errors:
            return "<p>无错误记录 ✅</p>"
        
        html = "<table><tr><th>序号</th><th>错误</th></tr>"
        for i, error in enumerate(errors, 1):
            html += f"<tr><td>{i}</td><td>{error}</td></tr>"
        html += "</table>"
        return html
    
    def _calculate_pass_rate(self) -> float:
        """计算通过率"""
        total = self.results['total_tests']
        if total == 0:
            return 0
        return (self.results['passed'] / total) * 100
    
    def check_test_status(self) -> Dict:
        """
        检查测试状态
        
        Returns:
            Dict: 测试状态
        """
        return {
            'status': 'healthy' if self.results['failed'] == 0 and self.results['errors'] == 0 else 'needs_attention',
            'total_tests': self.results['total_tests'],
            'passed': self.results['passed'],
            'failed': self.results['failed'],
            'errors': self.results['errors'],
            'pass_rate': self._calculate_pass_rate(),
        }


# GitHub Actions CI/CD 配置文件
GITHUB_ACTIONS_WORKFLOW = """name: AR System Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-xdist
    
    - name: Run unit tests
      run: |
        pytest test/test_backend/ -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest test/integration/ -v
    
    - name: Run performance tests
      run: |
        pytest test/performance/ -v
    
    - name: Run stability tests
      run: |
        pytest test/stability/ -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
"""

# GitLab CI 配置文件
GITLAB_CI_FILE = """stages:
  - test
  - report

test:
  stage: test
  script:
    - python -m pip install --upgrade pip
    - pip install -r requirements.txt
    - pip install pytest pytest-cov
  artifacts:
    reports:
      junit: test-results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

test:integration:
  stage: test
  script:
    - pip install pytest
    - pytest test/integration/ -v
  artifacts:
    reports:
      junit: test-integration-results.xml

test:performance:
  stage: test
  script:
    - pip install pytest
    - pytest test/performance/ -v

test:stability:
  stage: test
  script:
    - pip install pytest
    - pytest test/stability/ -v

pages:
  stage: report
  script:
    - echo "Generating test report..."
  artifacts:
    paths:
      - public
    expire_in: 1 week
"""


def main():
    """主函数 - 运行测试流水线"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动化测试流水线')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--ci', action='store_true', help='生成CI/CD配置')
    args = parser.parse_args()
    
    # 创建测试流水线
    pipeline = TestAutomationPipeline()
    
    # 运行测试
    results = pipeline.run_all_tests()
    
    # 打印摘要
    print("\n" + "="*50)
    print("🎯 测试流水线执行完成")
    print("="*50)
    print(f"总测试数: {results['total_tests']}")
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")
    print(f"⚠️ 错误: {results['errors']}")
    print(f"通过率: {pipeline._calculate_pass_rate():.2f}%")
    print(f"总耗时: {results['duration']:.2f}秒")
    print("="*50)
    
    # 生成CI/CD配置
    if args.ci:
        # GitHub Actions
        with open('.github/workflows/tests.yml', 'w') as f:
            f.write(GITHUB_ACTIONS_WORKFLOW)
        print("\n✅ GitHub Actions 配置已生成: .github/workflows/tests.yml")
        
        # GitLab CI
        with open('.gitlab-ci.yml', 'w') as f:
            f.write(GITLAB_CI_FILE)
        print("✅ GitLab CI 配置已生成: .gitlab-ci.yml")


if __name__ == '__main__':
    main()
