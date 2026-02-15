#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常用装饰器工具: timeout, retry, circuit_breaker 等
供 monitor 脚本复用
"""

import functools
import signal
import threading
import time
from typing import Callable, Any


class TimeoutException(Exception):
    pass


def timeout(seconds: int):
    """在支持信号的平台上实现的简单超时装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [TimeoutException('function timed out')]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    result[0] = e

            t = threading.Thread(target=target)
            t.daemon = True
            t.start()
            t.join(seconds)
            if t.is_alive():
                raise TimeoutException(f'Function {func.__name__} timed out after {seconds} seconds')
            if isinstance(result[0], Exception):
                raise result[0]
            return result[0]

        return wrapper
    return decorator


def retry(times: int = 3, delay: float = 1.0):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    time.sleep(delay)
            raise last_exc

        return wrapper
    return decorator


def circuit_breaker(max_failures: int = 5, reset_timeout: int = 60):
    state = {'failures': 0, 'opened_at': None}

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if state['failures'] >= max_failures:
                # 检查是否达到重置时间
                if state['opened_at'] and (time.time() - state['opened_at'] < reset_timeout):
                    raise Exception('Circuit open')
                else:
                    state['failures'] = 0
                    state['opened_at'] = None

            try:
                res = func(*args, **kwargs)
                state['failures'] = 0
                return res
            except Exception as e:
                state['failures'] += 1
                if state['failures'] == 1:
                    state['opened_at'] = time.time()
                raise

        return wrapper
    return decorator


def rate_limiter(calls: int = 5, period: int = 1):
    lock = threading.Lock()
    timestamps = []

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timestamps
            with lock:
                now = time.time()
                timestamps = [t for t in timestamps if now - t < period]
                if len(timestamps) >= calls:
                    raise Exception('Rate limit exceeded')
                timestamps.append(now)
            return func(*args, **kwargs)

        return wrapper
    return decorator


def performance_monitor(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        end = time.time()
        print(f"[perf] {func.__name__} took {end - start:.3f}s")
        return res

    return wrapper


def with_cleanup(cleanup_func: Callable):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                try:
                    cleanup_func()
                except Exception:
                    pass

        return wrapper
    return decorator
# -*- coding: utf-8 -*-
"""
装饰器模块 - 提供超时控制、重试机制等通用装饰器

功能:
1. timeout - 函数执行超时控制
2. retry - 失败重试机制
3. circuit_breaker - 熔断器模式
4. rate_limiter - 频率限制器
5. performance_monitor - 性能监控

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月
"""

import signal
import time
import functools
import threading
from enum import Enum
from collections import deque
from typing import Callable, Any, Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ==================== 超时控制 ====================

class TimeoutException(Exception):
    """超时异常"""
    pass


def timeout(seconds: int):
    """
    超时控制装饰器
    
    Args:
        seconds: 超时时间（秒）
    
    Returns:
        装饰器函数
    
    示例:
        @timeout(30)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 使用子线程方式（跨平台）
            result = [None]
            exception = [None]
            
            def worker():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                raise TimeoutException(f"Function {func.__name__} timed out after {seconds} seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator


# ==================== 重试机制 ====================

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: Tuple[type, ...] = (Exception,)
    logger_name: str = 'default'


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[type, ...] = (Exception,)
):
    """
    重试机制装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始重试间隔（秒）
        max_delay: 最大重试间隔
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.warning(
                            f"[Retry] {func.__name__} failed after {attempt} attempts: {e}"
                        )
                        raise
                    
                    # 计算重试间隔
                    current_delay = min(
                        delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # 添加随机抖动
                    if jitter:
                        import random
                        jitter_range = current_delay * 0.2
                        current_delay += random.uniform(-jitter_range, jitter_range)
                    
                    logger.warning(
                        f"[Retry] {func.__name__} failed: {e}, "
                        f"retrying in {current_delay:.2f}s (attempt {attempt}/{max_attempts})"
                    )
                    
                    time.sleep(current_delay)
            
            raise last_exception
        return wrapper
    return decorator


# ==================== 熔断器模式 ====================

class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """熔断器"""
    
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    name: str = "default"
    
    def __post_init__(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.timeout_seconds:
                        self._state = CircuitState.HALF_OPEN
                        self._success_count = 0
            return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = max(0, self._failure_count - 0.5)
    
    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN


def circuit_breaker(
    failure_threshold: int = 5,
    success_threshold: int = 3,
    timeout_seconds: float = 60.0
):
    """熔断器装饰器"""
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds,
            name=func.__name__
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


# ==================== 频率限制器 ====================

class RateLimiter:
    """频率限制器"""
    
    def __init__(self, max_calls: int, time_period: float):
        self.max_calls = max_calls
        self.time_period = time_period
        self._calls = deque()
        self._lock = threading.Lock()
    
    def allow(self) -> bool:
        with self._lock:
            now = time.time()
            
            # 清理过期记录
            while self._calls and now - self._calls[0] > self.time_period:
                self._calls.popleft()
            
            if len(self._calls) >= self.max_calls:
                return False
            
            self._calls.append(now)
            return True
    
    def wait(self, timeout: float = None) -> bool:
        start_time = time.time()
        
        while True:
            if self.allow():
                return True
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.01)
    
    def get_remaining(self) -> int:
        with self._lock:
            now = time.time()
            while self._calls and now - self._calls[0] > self.time_period:
                self._calls.popleft()
            return max(0, self.max_calls - len(self._calls))
    
    def reset(self):
        with self._lock:
            self._calls.clear()


def rate_limiter(max_calls: int, time_period: float, wait: bool = False):
    """频率限制装饰器"""
    limiter = RateLimiter(max_calls, time_period)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if wait:
                if not limiter.wait(timeout=10):  # 最多等10秒
                    raise Exception("Rate limit exceeded")
            else:
                if not limiter.allow():
                    raise Exception("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== 性能监控 ====================

@dataclass
class PerformanceStats:
    """性能统计"""
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    errors: int = 0


def performance_monitor(logger_name: str = 'default'):
    """性能监控装饰器"""
    stats = PerformanceStats()
    lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            error = None
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                
                with lock:
                    stats.call_count += 1
                    stats.total_time += duration
                    stats.min_time = min(stats.min_time, duration)
                    stats.max_time = max(stats.max_time, duration)
                    if error:
                        stats.errors += 1
                
                # 记录日志
                log = logging.getLogger(logger_name)
                log.debug(
                    f"[Performance] {func.__name__} executed in {duration:.3f}s"
                )
        
        wrapper._perf_stats = stats
        return wrapper
    return decorator


# ==================== 资源清理 ====================

def with_cleanup(cleanup_func: Callable):
    """资源清理装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            finally:
                try:
                    cleanup_func()
                except:
                    pass
        return wrapper
    return decorator
