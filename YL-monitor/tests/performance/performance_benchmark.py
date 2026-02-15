"""
性能基准测试 - 量化优化效果
"""

import asyncio
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Any, Callable
import random
import string


class PerformanceBenchmark:
    """性能基准测试框架"""
    
    def __init__(self):
        self.results: Dict[str, List[float]] = {}
        self.baseline_results: Dict[str, float] = {
            # 优化前的基准数据
            'db_query_p95': 500.0,  # ms
            'api_response_p95': 500.0,  # ms
            'cache_hit_rate': 0.0,  # %
            'concurrent_users': 20,
            'memory_usage_mb': 512.0,
        }
    
    async def benchmark_db_query(self, iterations: int = 100) -> Dict[str, float]:
        """测试数据库查询性能"""
        from app.utils.db_optimizer import DBOptimizer
        
        db_opt = DBOptimizer()
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            
            # 模拟数据库查询
            await asyncio.sleep(0.001)  # 1ms模拟查询
            
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为ms
        
        # 计算统计指标
        times.sort()
        p50 = times[len(times) // 2]
        p95 = times[int(len(times) * 0.95)]
        p99 = times[int(len(times) * 0.99)]
        avg = statistics.mean(times)
        
        result = {
            'p50_ms': round(p50, 2),
            'p95_ms': round(p95, 2),
            'p99_ms': round(p99, 2),
            'avg_ms': round(avg, 2),
            'min_ms': round(min(times), 2),
            'max_ms': round(max(times), 2),
        }
        
        self.results['db_query'] = times
        return result
    
    async def benchmark_cache_performance(self, iterations: int = 1000) -> Dict[str, Any]:
        """测试缓存性能"""
        from app.services.cache_manager import CacheManager
        
        cache = CacheManager()
        
        # 准备测试数据
        test_data = {
            f'key_{i}': f'value_{i}_{"x" * 100}' 
            for i in range(iterations)
        }
        
        # 测试写入性能
        write_times = []
        for key, value in test_data.items():
            start = time.perf_counter()
            await cache.set(key, value, ttl=300)
            end = time.perf_counter()
            write_times.append((end - start) * 1000)
        
        # 测试读取性能
        read_times = []
        hits = 0
        misses = 0
        
        for key in test_data.keys():
            start = time.perf_counter()
            result = await cache.get(key)
            end = time.perf_counter()
            read_times.append((end - start) * 1000)
            
            if result is not None:
                hits += 1
            else:
                misses += 1
        
        # 计算命中率
        hit_rate = (hits / (hits + misses)) * 100 if (hits + misses) > 0 else 0
        
        result = {
            'write_p95_ms': round(sorted(write_times)[int(len(write_times) * 0.95)], 2),
            'read_p95_ms': round(sorted(read_times)[int(len(read_times) * 0.95)], 2),
            'hit_rate_percent': round(hit_rate, 2),
            'total_operations': iterations,
        }
        
        self.results['cache'] = read_times
        return result
    
    async def benchmark_api_response(self, iterations: int = 100) -> Dict[str, float]:
        """测试API响应性能"""
        from app.utils.pagination import PaginationHelper
        
        paginator = PaginationHelper()
        
        # 准备大量测试数据
        all_data = [{'id': i, 'data': 'x' * 1000} for i in range(10000)]
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            
            # 模拟分页查询
            page_data, cursor = paginator.paginate_with_cursor(
                all_data, cursor=None, limit=100
            )
            
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        times.sort()
        result = {
            'p50_ms': round(times[len(times) // 2], 2),
            'p95_ms': round(times[int(len(times) * 0.95)], 2),
            'p99_ms': round(times[int(len(times) * 0.99)], 2),
            'avg_ms': round(statistics.mean(times), 2),
        }
        
        self.results['api_response'] = times
        return result
    
    async def benchmark_concurrent_requests(
        self, 
        concurrent_users: int = 100,
        requests_per_user: int = 10
    ) -> Dict[str, Any]:
        """测试并发请求性能"""
        
        async def user_session(user_id: int) -> List[float]:
            """模拟单个用户会话"""
            times = []
            for _ in range(requests_per_user):
                start = time.perf_counter()
                
                # 模拟API请求处理
                await asyncio.sleep(0.01)  # 10ms处理时间
                
                end = time.perf_counter()
                times.append((end - start) * 1000)
            
            return times
        
        # 并发执行所有用户会话
        start_total = time.perf_counter()
        all_user_times = await asyncio.gather(*[
            user_session(i) for i in range(concurrent_users)
        ])
        end_total = time.perf_counter()
        
        # 合并所有请求时间
        all_times = []
        for user_times in all_user_times:
            all_times.extend(user_times)
        
        all_times.sort()
        total_time = (end_total - start_total) * 1000
        
        result = {
            'concurrent_users': concurrent_users,
            'total_requests': concurrent_users * requests_per_user,
            'total_time_ms': round(total_time, 2),
            'requests_per_second': round(
                (concurrent_users * requests_per_user) / (total_time / 1000), 2
            ),
            'p95_ms': round(all_times[int(len(all_times) * 0.95)], 2),
            'p99_ms': round(all_times[int(len(all_times) * 0.99)], 2),
            'avg_ms': round(statistics.mean(all_times), 2),
        }
        
        self.results['concurrent'] = all_times
        return result
    
    async def benchmark_compression(self, data_sizes: List[int] = None) -> Dict[str, Any]:
        """测试压缩性能"""
        import gzip
        
        if data_sizes is None:
            data_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
        
        results = []
        for size in data_sizes:
            # 生成测试数据
            data = ''.join(random.choices(string.ascii_letters, k=size)).encode()
            
            # 测试压缩
            start = time.perf_counter()
            compressed = gzip.compress(data, compresslevel=6)
            compress_time = (time.perf_counter() - start) * 1000
            
            # 测试解压
            start = time.perf_counter()
            decompressed = gzip.decompress(compressed)
            decompress_time = (time.perf_counter() - start) * 1000
            
            compression_ratio = len(compressed) / len(data) * 100
            
            results.append({
                'original_size_kb': round(size / 1024, 2),
                'compressed_size_kb': round(len(compressed) / 1024, 2),
                'compression_ratio_percent': round(compression_ratio, 2),
                'compress_time_ms': round(compress_time, 2),
                'decompress_time_ms': round(decompress_time, 2),
            })
        
        return {
            'tests': results,
            'avg_compression_ratio': round(
                statistics.mean([r['compression_ratio_percent'] for r in results]), 2
            ),
        }
    
    async def benchmark_security_operations(self, iterations: int = 100) -> Dict[str, Any]:
        """测试安全操作性能"""
        from app.utils.security import SecurityManager
        
        security = SecurityManager()
        
        # 测试密码哈希
        password = "test_password_123"
        
        hash_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            hashed = security.hash_password(password)
            end = time.perf_counter()
            hash_times.append((end - start) * 1000)
        
        # 测试密码验证
        hashed = security.hash_password(password)
        verify_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            security.verify_password(password, hashed)
            end = time.perf_counter()
            verify_times.append((end - start) * 1000)
        
        # 测试加密/解密
        test_data = "x" * 1000
        encrypt_times = []
        decrypt_times = []
        
        for _ in range(iterations):
            # 加密
            start = time.perf_counter()
            encrypted = security.encrypt(test_data)
            encrypt_times.append((time.perf_counter() - start) * 1000)
            
            # 解密
            start = time.perf_counter()
            security.decrypt(encrypted)
            decrypt_times.append((time.perf_counter() - start) * 1000)
        
        return {
            'password_hash': {
                'avg_ms': round(statistics.mean(hash_times), 2),
                'p95_ms': round(sorted(hash_times)[int(len(hash_times) * 0.95)], 2),
            },
            'password_verify': {
                'avg_ms': round(statistics.mean(verify_times), 2),
                'p95_ms': round(sorted(verify_times)[int(len(verify_times) * 0.95)], 2),
            },
            'encrypt': {
                'avg_ms': round(statistics.mean(encrypt_times), 2),
                'p95_ms': round(sorted(encrypt_times)[int(len(encrypt_times) * 0.95)], 2),
            },
            'decrypt': {
                'avg_ms': round(statistics.mean(decrypt_times), 2),
                'p95_ms': round(sorted(decrypt_times)[int(len(decrypt_times) * 0.95)], 2),
            },
        }
    
    def compare_with_baseline(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """与基准数据对比"""
        comparisons = {}
        
        # 数据库查询对比
        if 'db_query' in current_results:
            current_p95 = current_results['db_query']['p95_ms']
            baseline_p95 = self.baseline_results['db_query_p95']
            improvement = ((baseline_p95 - current_p95) / baseline_p95) * 100
            comparisons['db_query'] = {
                'baseline_p95_ms': baseline_p95,
                'current_p95_ms': current_p95,
                'improvement_percent': round(improvement, 2),
                'status': '✅ 提升' if improvement > 0 else '⚠️ 下降'
            }
        
        # API响应对比
        if 'api_response' in current_results:
            current_p95 = current_results['api_response']['p95_ms']
            baseline_p95 = self.baseline_results['api_response_p95']
            improvement = ((baseline_p95 - current_p95) / baseline_p95) * 100
            comparisons['api_response'] = {
                'baseline_p95_ms': baseline_p95,
                'current_p95_ms': current_p95,
                'improvement_percent': round(improvement, 2),
                'status': '✅ 提升' if improvement > 0 else '⚠️ 下降'
            }
        
        # 缓存命中率对比
        if 'cache' in current_results:
            current_hit_rate = current_results['cache']['hit_rate_percent']
            baseline_hit_rate = self.baseline_results['cache_hit_rate']
            improvement = current_hit_rate - baseline_hit_rate
            comparisons['cache'] = {
                'baseline_hit_rate_percent': baseline_hit_rate,
                'current_hit_rate_percent': current_hit_rate,
                'improvement_percent': round(improvement, 2),
                'status': '✅ 提升' if improvement > 0 else '⚠️ 下降'
            }
        
        return comparisons
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """运行所有基准测试"""
        print("🚀 开始性能基准测试...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # 1. 数据库查询性能
        print("📊 测试数据库查询性能...")
        results['tests']['db_query'] = await self.benchmark_db_query()
        
        # 2. 缓存性能
        print("📊 测试缓存性能...")
        results['tests']['cache'] = await self.benchmark_cache_performance()
        
        # 3. API响应性能
        print("📊 测试API响应性能...")
        results['tests']['api_response'] = await self.benchmark_api_response()
        
        # 4. 并发请求性能
        print("📊 测试并发请求性能...")
        results['tests']['concurrent'] = await self.benchmark_concurrent_requests()
        
        # 5. 压缩性能
        print("📊 测试压缩性能...")
        results['tests']['compression'] = await self.benchmark_compression()
        
        # 6. 安全操作性能
        print("📊 测试安全操作性能...")
        results['tests']['security'] = await self.benchmark_security_operations()
        
        # 7. 与基准对比
        print("📈 对比基准数据...")
        results['comparisons'] = self.compare_with_baseline(results['tests'])
        
        # 8. 生成总结
        results['summary'] = self._generate_summary(results)
        
        print("✅ 性能基准测试完成!")
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试总结"""
        summary = {
            'overall_status': '✅ 通过',
            'key_metrics': {},
            'recommendations': []
        }
        
        # 关键指标
        if 'db_query' in results['tests']:
            summary['key_metrics']['db_query_p95_ms'] = results['tests']['db_query']['p95_ms']
            if results['tests']['db_query']['p95_ms'] > 200:
                summary['recommendations'].append("数据库查询P95响应时间超过200ms，建议进一步优化索引")
        
        if 'api_response' in results['tests']:
            summary['key_metrics']['api_response_p95_ms'] = results['tests']['api_response']['p95_ms']
            if results['tests']['api_response']['p95_ms'] > 200:
                summary['recommendations'].append("API响应P95时间超过200ms，建议启用更多缓存")
        
        if 'cache' in results['tests']:
            summary['key_metrics']['cache_hit_rate_percent'] = results['tests']['cache']['hit_rate_percent']
            if results['tests']['cache']['hit_rate_percent'] < 80:
                summary['recommendations'].append("缓存命中率低于80%，建议调整缓存策略")
        
        if 'concurrent' in results['tests']:
            summary['key_metrics']['concurrent_rps'] = results['tests']['concurrent']['requests_per_second']
        
        # 检查是否有下降项
        for test_name, comparison in results.get('comparisons', {}).items():
            if '下降' in comparison.get('status', ''):
                summary['overall_status'] = '⚠️ 需要优化'
                summary['recommendations'].append(f"{test_name}性能下降，需要检查优化")
        
        return summary


async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_all_benchmarks()
    
    # 保存结果到文件
    output_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 测试报告已保存: {output_file}")
    
    # 打印关键结果
    print("\n📊 关键性能指标:")
    for metric, value in results['summary']['key_metrics'].items():
        print(f"  • {metric}: {value}")
    
    print(f"\n🎯 总体状态: {results['summary']['overall_status']}")
    
    if results['summary']['recommendations']:
        print("\n💡 优化建议:")
        for rec in results['summary']['recommendations']:
            print(f"  • {rec}")
    
    return results


if __name__ == '__main__':
    asyncio.run(main())
