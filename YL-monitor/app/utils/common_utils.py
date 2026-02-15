"""
公共工具函数库
实现统一工具函数、API封装标准化和错误处理统一
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re


T = TypeVar('T')


class ErrorCode(Enum):
    """统一错误码"""
    SUCCESS = "0"
    UNKNOWN_ERROR = "E0001"
    VALIDATION_ERROR = "E0002"
    NOT_FOUND = "E0003"
    PERMISSION_DENIED = "E0004"
    RATE_LIMITED = "E0005"
    TIMEOUT = "E0006"
    SERVICE_UNAVAILABLE = "E0007"
    DATABASE_ERROR = "E0008"
    EXTERNAL_API_ERROR = "E0009"
    CONFIG_ERROR = "E0010"
    BUSINESS_LOGIC_ERROR = "E0100"


@dataclass
class APIResponse:
    """统一API响应格式"""
    code: str
    message: str
    data: Any = None
    timestamp: str = None
    request_id: str = None
    pagination: Optional[Dict] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        result = {
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp
        }
        if self.request_id:
            result["request_id"] = self.request_id
        if self.pagination:
            result["pagination"] = self.pagination
        return result
    
    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功") -> "APIResponse":
        """成功响应"""
        return cls(
            code=ErrorCode.SUCCESS.value,
            message=message,
            data=data
        )
    
    @classmethod
    def error(cls, code: ErrorCode, message: str, 
              data: Any = None) -> "APIResponse":
        """错误响应"""
        return cls(
            code=code.value,
            message=message,
            data=data
        )


class APIError(Exception):
    """API错误基类"""
    def __init__(self, code: ErrorCode, message: str, 
                 data: Any = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.data = data
        self.status_code = status_code
        super().__init__(message)
    
    def to_response(self) -> APIResponse:
        """转换为API响应"""
        return APIResponse.error(self.code, self.message, self.data)


class ValidationError(APIError):
    """验证错误"""
    def __init__(self, message: str = "参数验证失败", data: Any = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, data, 422)


class NotFoundError(APIError):
    """资源未找到错误"""
    def __init__(self, message: str = "资源不存在", data: Any = None):
        super().__init__(ErrorCode.NOT_FOUND, message, data, 404)


class PermissionError(APIError):
    """权限错误"""
    def __init__(self, message: str = "权限不足", data: Any = None):
        super().__init__(ErrorCode.PERMISSION_DENIED, message, data, 403)


class TimeoutError(APIError):
    """超时错误"""
    def __init__(self, message: str = "操作超时", data: Any = None):
        super().__init__(ErrorCode.TIMEOUT, message, data, 408)


def api_handler(func: Callable) -> Callable:
    """
    API处理装饰器
    
    统一处理：
    1. 异常捕获和转换
    2. 响应格式统一
    3. 日志记录
    4. 性能监控
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        try:
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 如果已经是APIResponse，直接返回
            if isinstance(result, APIResponse):
                result.request_id = request_id
                return result.to_dict()
            
            # 包装为成功响应
            response = APIResponse.success(data=result)
            response.request_id = request_id
            return response.to_dict()
            
        except APIError as e:
            # 已知API错误
            logging.warning(f"API错误 [{request_id}]: {e.code} - {e.message}")
            response = e.to_response()
            response.request_id = request_id
            return response.to_dict()
            
        except Exception as e:
            # 未知错误
            logging.error(f"未处理错误 [{request_id}]: {str(e)}")
            logging.error(traceback.format_exc())
            
            response = APIResponse.error(
                ErrorCode.UNKNOWN_ERROR,
                f"服务器内部错误: {str(e)}",
                {"error_type": type(e).__name__}
            )
            response.request_id = request_id
            return response.to_dict()
        
        finally:
            # 记录性能
            elapsed = time.time() - start_time
            logging.info(f"API请求 [{request_id}] 耗时: {elapsed:.3f}s")
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # 同步版本包装为异步
        return async_wrapper(*args, **kwargs)
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, 
          exceptions: tuple = (Exception,)) -> Callable:
    """
    重试装饰器
    
    参数：
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(
                            f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，"
                            f"{delay}秒后重试: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logging.error(
                            f"函数 {func.__name__} 重试 {max_attempts} 次后仍然失败"
                        )
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    结果缓存装饰器
    
    参数：
        ttl: 缓存时间（秒）
        key_func: 自定义缓存键生成函数
    """
    cache = {}
    timestamps = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 检查缓存
            now = time.time()
            if cache_key in cache:
                if now - timestamps[cache_key] < ttl:
                    return cache[cache_key]
            
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 存储缓存
            cache[cache_key] = result
            timestamps[cache_key] = now
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            now = time.time()
            if cache_key in cache:
                if now - timestamps[cache_key] < ttl:
                    return cache[cache_key]
            
            result = func(*args, **kwargs)
            cache[cache_key] = result
            timestamps[cache_key] = now
            
            return result
        
        # 添加清除缓存的方法
        def clear_cache():
            cache.clear()
            timestamps.clear()
        
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.clear_cache = clear_cache
        
        return wrapper
    
    return decorator


def validate_params(**validators) -> Callable:
    """
    参数验证装饰器
    
    使用示例：
    @validate_params(
        name=str,
        age=int,
        email=lambda x: re.match(r'[^@]+@[^@]+\\.[^@]+', x)
    )
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            errors = {}
            
            for param_name, validator in validators.items():
                if param_name not in kwargs:
                    errors[param_name] = "缺少必需参数"
                    continue
                
                value = kwargs[param_name]
                
                # 类型验证
                if isinstance(validator, type):
                    if not isinstance(value, validator):
                        errors[param_name] = f"类型错误，期望 {validator.__name__}"
                
                # 函数验证
                elif callable(validator):
                    try:
                        if not validator(value):
                            errors[param_name] = "验证失败"
                    except Exception as e:
                        errors[param_name] = f"验证错误: {str(e)}"
            
            if errors:
                raise ValidationError("参数验证失败", errors)
            
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本
            errors = {}
            
            for param_name, validator in validators.items():
                if param_name not in kwargs:
                    errors[param_name] = "缺少必需参数"
                    continue
                
                value = kwargs[param_name]
                
                if isinstance(validator, type):
                    if not isinstance(value, validator):
                        errors[param_name] = f"类型错误，期望 {validator.__name__}"
                elif callable(validator):
                    try:
                        if not validator(value):
                            errors[param_name] = "验证失败"
                    except Exception as e:
                        errors[param_name] = f"验证错误: {str(e)}"
            
            if errors:
                raise ValidationError("参数验证失败", errors)
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 工具函数
def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    timestamp = int(time.time() * 1000)
    random_part = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
    return f"{prefix}{timestamp}{random_part}"


def hash_string(input_string: str, algorithm: str = "md5") -> str:
    """字符串哈希"""
    if algorithm == "md5":
        return hashlib.md5(input_string.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(input_string.encode()).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def format_datetime(dt: Union[datetime, str], 
                  format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(format)


def parse_datetime(date_string: str, 
                   format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析日期时间"""
    return datetime.strptime(date_string, format)


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """安全JSON解析"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_string(s: str, max_length: int, 
                    suffix: str = "...") -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    # 移除非法字符
    filename = re.sub(r'[<>:\"/\\\\|?*]', '', filename)
    # 限制长度
    return truncate_string(filename, 255)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """分块列表"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List[List[T]]) -> List[T]:
    """扁平化列表"""
    return [item for sublist in nested_list for item in sublist]


def dict_get_nested(d: Dict, path: str, default: Any = None) -> Any:
    """获取嵌套字典值"""
    keys = path.split(".")
    current = d
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def dict_merge(*dicts: Dict) -> Dict:
    """合并多个字典"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def measure_time(func: Callable) -> Callable:
    """测量函数执行时间"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logging.info(f"函数 {func.__name__} 执行时间: {elapsed:.3f}s")
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logging.info(f"函数 {func.__name__} 执行时间: {elapsed:.3f}s")
        return result
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# 导出常用工具
__all__ = [
    # 响应和错误
    "APIResponse",
    "APIError",
    "ValidationError",
    "NotFoundError",
    "PermissionError",
    "TimeoutError",
    "ErrorCode",
    
    # 装饰器
    "api_handler",
    "retry",
    "cache_result",
    "validate_params",
    "measure_time",
    
    # 工具函数
    "generate_id",
    "hash_string",
    "format_datetime",
    "parse_datetime",
    "safe_json_loads",
    "truncate_string",
    "sanitize_filename",
    "chunk_list",
    "flatten_list",
    "dict_get_nested",
    "dict_merge",
]
