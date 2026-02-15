#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 健康检查脚本 - API Health Check (优化版)
用于检查系统 API 接口的健康状态和响应时间

使用方法:
    python api_health_check.py                      # 检查所有端点
    python api_health_check.py --endpoint /health   # 检查单个端点
    python api_health_check.py --report             # 生成报告
    python api_health_check.py --url http://0.0.0.0:5500  # 指定服务地址
    python api_health_check.py --timeout 30         # 设置超时30秒

版本: 2.1
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import socket

# 配置日志
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "api_health.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """超时异常"""
    pass


class APIHealthChecker:
    """API 健康检查器类"""
    
    # 默认 API 端点列表
    DEFAULT_ENDPOINTS = {
        '/api/health': '健康检查端点',
        '/api/summary': '系统整体状态摘要',
        '/dashboard': '仪表盘页面',
        '/alerts': '告警中心页面',
        '/ar': 'AR监控页面',
        '/dag': 'DAG流水线页面',
        '/scripts': '脚本管理页面',
        '/api-doc': 'API文档页面'
    }
    
    def __init__(self, base_url='http://0.0.0.0:5500', timeout=10, verbose=False,
                 max_retries=3, retry_delay=2, global_timeout=60):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verbose = verbose
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.global_timeout = global_timeout
        self.results = {}
        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0
    
    def check_endpoint(self, endpoint, method='GET', data=None, headers=None):
        """检查单个 API 端点"""
        url = f"{self.base_url}{endpoint}"
        result = {
            'endpoint': endpoint,
            'url': url,
            'method': method,
            'status': 'unknown',
            'response_time': None,
            'status_code': None,
            'error': None,
            'data': None
        }
        
        start_time = time.time()
        self._request_count += 1
        
        try:
            req_headers = {
                'User-Agent': 'AR Health Checker/2.1',
                'Accept': 'application/json, text/html'
            }
            if headers:
                req_headers.update(headers)
            
            if data:
                if isinstance(data, dict):
                    data = json.dumps(data)
                req_headers['Content-Type'] = 'application/json'
            
            req = Request(url, data=data, headers=req_headers)
            req.get_method = lambda: method
            
            with urlopen(req, timeout=self.timeout) as response:
                end_time = time.time()
                result['response_time'] = round(end_time - start_time, 3)
                result['status_code'] = response.status
                result['status'] = 'healthy' if response.status == 200 else 'degraded'
                self._success_count += 1
                
                try:
                    result['data'] = json.loads(response.read().decode('utf-8'))
                except Exception:
                    result['data'] = {'raw': response.read().decode('utf-8')[:100]}
            
            logger.debug(f"端点检查成功: {endpoint} ({result['response_time']:.3f}s)")
                    
        except HTTPError as e:
            end_time = time.time()
            result['response_time'] = round(end_time - start_time, 3)
            result['status_code'] = e.code
            result['status'] = 'error'
            result['error'] = f'HTTP Error: {e.code} {e.reason}'
            self._failure_count += 1
            logger.warning(f"端点 HTTP 错误: {endpoint} - {e.code}")
            
        except URLError as e:
            end_time = time.time()
            result['response_time'] = round(end_time - start_time, 3)
            result['status'] = 'unreachable'
            result['error'] = f'URL Error: {e.reason}'
            self._failure_count += 1
            logger.warning(f"端点无法访问: {endpoint} - {e.reason}")
            
        except socket.timeout:
            end_time = time.time()
            result['response_time'] = round(end_time - start_time, 3)
            result['status'] = 'timeout'
            result['error'] = 'Request timeout'
            self._failure_count += 1
            logger.warning(f"端点超时: {endpoint}")
            
        except Exception as e:
            end_time = time.time()
            result['response_time'] = round(end_time - start_time, 3)
            result['status'] = 'error'
            result['error'] = str(e)
            self._failure_count += 1
            logger.error(f"端点检查异常: {endpoint} - {e}")
        
        return result
    
    def check_all_endpoints(self, endpoints=None):
        """检查所有 API 端点"""
        if endpoints is None:
            endpoints = self.DEFAULT_ENDPOINTS
        
        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0
        
        results = {}
        total_time = 0
        healthy_count = 0
        error_count = 0
        timeout_count = 0
        
        start_time = time.time()
        
        for endpoint in endpoints:
            if self.verbose:
                print(f"检查端点: {endpoint}")
            
            result = self.check_endpoint(endpoint)
            results[endpoint] = result
            
            total_time += result.get('response_time', 0) or 0
            
            status = result.get('status', 'unknown')
            if status == 'healthy':
                healthy_count += 1
            elif status in ['error', 'unreachable']:
                error_count += 1
            elif status == 'timeout':
                timeout_count += 1
        
        total_duration = time.time() - start_time
        avg_response_time = total_time / len(results) if results else 0
        
        if timeout_count == len(results) or error_count == len(results):
            overall_status = 'critical'
        elif error_count > 0 or timeout_count > 0:
            overall_status = 'degraded'
        elif healthy_count == len(results):
            overall_status = 'healthy'
        else:
            overall_status = 'unknown'
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'overall_status': overall_status,
            'total_endpoints': len(results),
            'healthy_count': healthy_count,
            'error_count': error_count,
            'timeout_count': timeout_count,
            'average_response_time': round(avg_response_time, 3),
            'total_duration': round(total_duration, 3),
            'request_stats': {
                'total': self._request_count,
                'success': self._success_count,
                'failed': self._failure_count,
                'success_rate': round(
                    self._success_count / max(self._request_count, 1) * 100, 1
                )
            },
            'results': results
        }
        
        logger.info(
            f"API 健康检查完成: {overall_status}, "
            f"健康: {healthy_count}, 错误: {error_count}, 超时: {timeout_count}, "
            f"成功率: {summary['request_stats']['success_rate']}%"
        )
        
        return summary
    
    def print_results(self, summary):
        """控制台输出检查结果"""
        print("\n" + "=" * 70)
        print("API 健康检查报告")
        print("=" * 70)
        
        print(f"\n检查时间: {summary['timestamp']}")
        print(f"服务地址: {summary['base_url']}")
        print(f"总耗时: {summary['total_duration']:.3f}s")
        
        status_icons = {
            'healthy': '✅',
            'degraded': '⚠️',
            'critical': '❌',
            'unknown': '❓'
        }
        status_icon = status_icons.get(summary['overall_status'], '❓')
        print(f"\n整体状态: {status_icon} {summary['overall_status'].upper()}")
        print(f"   健康端点: {summary['healthy_count']}/{summary['total_endpoints']}")
        print(f"   错误端点: {summary['error_count']}")
        print(f"   超时端点: {summary['timeout_count']}")
        print(f"   平均响应时间: {summary['average_response_time']:.3f}s")
        print(f"   成功率: {summary['request_stats']['success_rate']}%")
        
        print("\n端点检查结果:")
        print("-" * 70)
        print(f"{'端点':<30} {'状态':<12} {'响应时间':<12} {'状态码'}")
        print("-" * 70)
        
        for endpoint, result in summary['results'].items():
            status_icon = status_icons.get(result.get('status', 'unknown'), '❓')
            response_time = f"{result.get('response_time', 0):.3f}s" \
                if result.get('response_time') else 'N/A'
            status_code = str(result.get('status_code', 'N/A'))
            
            print(f"{endpoint:<30} {status_icon} {result.get('status', 'unknown'):<10} "
                  f"{response_time:<12} {status_code}")
        
        print("-" * 70)
        
        errors = [
            (ep, r) for ep, r in summary['results'].items()
            if r.get('status') in ['error', 'unreachable', 'timeout']
        ]
        if errors:
            print("\n错误端点:")
            for endpoint, result in errors:
                print(f"   - {endpoint}: {result.get('error', 'Unknown error')}")
        
        print("=" * 70 + "\n")
    
    def generate_report(self, output_path=None):
        """生成健康检查报告"""
        summary = self.check_all_endpoints()
        
        base_dir = Path(__file__).parent.parent.parent
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = logs_dir / f"api_health_report_{timestamp}.json"
        
        report = {
            'report_type': 'API Health Check Report',
            'generated_at': datetime.now().isoformat(),
            'checker_version': '2.1',
            'base_url': self.base_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'global_timeout': self.global_timeout,
            'summary': summary
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"API 健康报告已生成: {output_path}")
            print(f"✅ 健康报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            print(f"❌ 生成报告失败: {e}")
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='API 健康检查工具（优化版）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python api_health_check.py                          # 检查所有端点
    python api_health_check.py --endpoint /health       # 检查单个端点
    python api_health_check.py --report                 # 生成报告
    python api_health_check.py --url http://0.0.0.0:5500  # 指定地址
    python api_health_check.py --timeout 30             # 设置超时30秒
        """
    )
    
    parser.add_argument(
        '--url', '-u', type=str, default='http://0.0.0.0:5500',
        help='API 服务基础 URL (默认: http://0.0.0.0:5500)'
    )
    parser.add_argument('--endpoint', '-e', type=str, default=None,
                        help='检查单个端点')
    parser.add_argument('--report', '-r', action='store_true',
                        help='生成报告')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='报告输出路径')
    parser.add_argument('--timeout', '-t', type=int, default=10,
                        help='单次请求超时时间（秒），默认10秒')
    parser.add_argument('--retries', '-R', type=int, default=3,
                        help='最大重试次数，默认3次')
    parser.add_argument('--retry-delay', type=int, default=2,
                        help='重试间隔（秒），默认2秒')
    parser.add_argument('--global-timeout', '-g', type=int, default=60,
                        help='全局超时时间（秒），默认60秒')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='详细输出模式')
    
    args = parser.parse_args()
    
    checker = APIHealthChecker(
        base_url=args.url,
        timeout=args.timeout,
        verbose=args.verbose,
        max_retries=args.retries,
        retry_delay=args.retry_delay,
        global_timeout=args.global_timeout
    )
    
    try:
        if args.endpoint:
            result = checker.check_endpoint(args.endpoint)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.report:
            checker.generate_report(args.output)
        else:
            summary = checker.check_all_endpoints()
            checker.print_results(summary)
    
    except TimeoutException as e:
        logger.error(f"API 健康检查超时: {e}")
        print(f"❌ 错误: 检查超时 - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"API 健康检查出错: {e}")
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
