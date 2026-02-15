"""
【API客户端】统一API请求封装

功能:
- 同步/异步HTTP请求封装
- 自动重试机制
- 请求/响应拦截器
- 错误统一处理
- 连接池管理
- 请求签名和认证

作者: AI Assistant
创建时间: 2026-02-10
版本: 1.0.0

依赖:
- requests (同步请求)
- aiohttp (异步请求)
- tenacity (重试机制)

示例:
    # 同步请求
    client = APIClient(base_url="https://api.example.com")
    response = client.get("/users", params={"page": 1})
    
    # 异步请求
    async_client = AsyncAPIClient(base_url="https://api.example.com")
    response = await async_client.get("/users", params={"page": 1})
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, urlencode

logger = logging.getLogger(__name__)

T = TypeVar('T')


class HTTPMethod(Enum):
    """HTTP请求方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class RequestConfig:
    """
    【请求配置】请求配置参数
    
    Attributes:
        base_url: 基础URL
        timeout: 超时时间(秒)
        retries: 重试次数
        retry_delay: 重试延迟(秒)
        headers: 默认请求头
        verify_ssl: 是否验证SSL证书
        proxy: 代理设置
        auth: 认证信息
    """
    base_url: str = ""
    timeout: float = 30.0
    retries: int = 3
    retry_delay: float = 1.0
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    proxy: Optional[Dict[str, str]] = None
    auth: Optional[tuple] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保base_url以/结尾
        if self.base_url and not self.base_url.endswith('/'):
            self.base_url += '/'


@dataclass
class ResponseData:
    """
    【响应数据】统一响应格式
    
    Attributes:
        status_code: HTTP状态码
        data: 响应数据
        headers: 响应头
        text: 原始响应文本
        elapsed: 请求耗时(秒)
        url: 请求URL
    """
    status_code: int
    data: Any
    headers: Dict[str, str]
    text: str
    elapsed: float
    url: str
    
    @property
    def is_success(self) -> bool:
        """是否成功响应(2xx)"""
        return 200 <= self.status_code < 300
    
    @property
    def is_error(self) -> bool:
        """是否错误响应(4xx, 5xx)"""
        return self.status_code >= 400
    
    def raise_for_status(self):
        """根据状态码抛出异常"""
        if self.is_error:
            raise APIError(
                f"HTTP {self.status_code}: {self.text}",
                status_code=self.status_code,
                response=self
            )


class APIError(Exception):
    """
    【API错误】API请求异常
    
    Attributes:
        message: 错误信息
        status_code: HTTP状态码
        response: 响应数据
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[ResponseData] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class RetryStrategy:
    """
    【重试策略】请求重试配置
    
    支持指数退避、固定间隔、线性增长等策略
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_status: Optional[List[int]] = None,
        retry_on_exception: Optional[List[type]] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status = retry_on_status or [500, 502, 503, 504]
        self.retry_on_exception = retry_on_exception or [
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ]
    
    def get_delay(self, attempt: int) -> float:
        """
        获取第attempt次重试的延迟时间
        
        使用指数退避算法
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, status_code: Optional[int] = None, exception: Optional[Exception] = None) -> bool:
        """判断是否应该重试"""
        if status_code is not None:
            return status_code in self.retry_on_status
        
        if exception is not None:
            return type(exception) in self.retry_on_exception
        
        return False


class RequestInterceptor:
    """
    【请求拦截器】请求预处理
    
    可用于:
    - 添加认证头
    - 请求签名
    - 参数格式化
    - 日志记录
    """
    
    def __init__(self):
        self._handlers: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
    
    def add_handler(self, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """添加处理函数"""
        self._handlers.append(handler)
    
    def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求数据"""
        for handler in self._handlers:
            request_data = handler(request_data)
        return request_data


class ResponseInterceptor:
    """
    【响应拦截器】响应后处理
    
    可用于:
    - 数据解析
    - 错误处理
    - 日志记录
    - 数据转换
    """
    
    def __init__(self):
        self._handlers: List[Callable[[ResponseData], ResponseData]] = []
    
    def add_handler(self, handler: Callable[[ResponseData], ResponseData]):
        """添加处理函数"""
        self._handlers.append(handler)
    
    def process(self, response: ResponseData) -> ResponseData:
        """处理响应数据"""
        for handler in self._handlers:
            response = handler(response)
        return response


class APIClient:
    """
    【API客户端】同步HTTP客户端
    
    功能特性:
    - 连接池复用
    - 自动重试
    - 请求/响应拦截器
    - 统一错误处理
    - 请求签名
    
    示例:
        client = APIClient(
            base_url="https://api.example.com",
            timeout=30,
            retries=3
        )
        
        # GET请求
        response = client.get("/users", params={"page": 1})
        
        # POST请求
        response = client.post("/users", json={"name": "张三"})
        
        # 文件上传
        response = client.post("/upload", files={"file": open("data.txt", "rb")})
    """
    
    def __init__(
        self,
        config: Optional[RequestConfig] = None,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.config = config or RequestConfig()
        self.retry_strategy = retry_strategy or RetryStrategy()
        
        # 创建会话
        self.session = requests.Session()
        
        # 配置连接池
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=100,
            max_retries=0  # 我们手动处理重试
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 设置默认头
        self.session.headers.update({
            'User-Agent': 'YL-Monitor-API-Client/1.0',
            'Accept': 'application/json',
            **self.config.headers
        })
        
        # 设置代理
        if self.config.proxy:
            self.session.proxies.update(self.config.proxy)
        
        # 设置认证
        if self.config.auth:
            self.session.auth = self.config.auth
        
        # 设置SSL验证
        self.session.verify = self.config.verify_ssl
        
        # 拦截器
        self.request_interceptor = RequestInterceptor()
        self.response_interceptor = ResponseInterceptor()
        
        # 添加默认拦截器
        self._setup_default_interceptors()
        
        logger.info(f"API客户端已初始化: {self.config.base_url}")
    
    def _setup_default_interceptors(self):
        """设置默认拦截器"""
        # 请求日志拦截器
        def log_request(data: Dict[str, Any]) -> Dict[str, Any]:
            logger.debug(f"API请求: {data.get('method')} {data.get('url')}")
            return data
        
        self.request_interceptor.add_handler(log_request)
        
        # 响应日志拦截器
        def log_response(response: ResponseData) -> ResponseData:
            logger.debug(f"API响应: {response.status_code} {response.url} ({response.elapsed:.3f}s)")
            return response
        
        self.response_interceptor.add_handler(log_response)
    
    def _make_request(
        self,
        method: HTTPMethod,
        path: str,
        **kwargs
    ) -> ResponseData:
        """
        执行HTTP请求
        
        Args:
            method: HTTP方法
            path: 请求路径
            **kwargs: 请求参数(params, json, data, files等)
        
        Returns:
            ResponseData: 统一响应格式
        """
        # 构建完整URL
        url = urljoin(self.config.base_url, path)
        
        # 准备请求数据
        request_data = {
            'method': method.value,
            'url': url,
            'timeout': self.config.timeout,
            **kwargs
        }
        
        # 请求拦截器处理
        request_data = self.request_interceptor.process(request_data)
        
        # 执行请求(带重试)
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.retry_strategy.max_retries + 1):
            try:
                response = self.session.request(**request_data)
                elapsed = time.time() - start_time
                
                # 构建响应数据
                try:
                    data = response.json()
                except ValueError:
                    data = response.text
                
                response_data = ResponseData(
                    status_code=response.status_code,
                    data=data,
                    headers=dict(response.headers),
                    text=response.text,
                    elapsed=elapsed,
                    url=response.url
                )
                
                # 响应拦截器处理
                response_data = self.response_interceptor.process(response_data)
                
                # 检查是否需要重试
                if response_data.is_error and self.retry_strategy.should_retry(status_code=response.status_code):
                    if attempt < self.retry_strategy.max_retries:
                        delay = self.retry_strategy.get_delay(attempt)
                        logger.warning(f"请求失败，{delay:.1f}秒后重试(第{attempt + 1}次)")
                        time.sleep(delay)
                        continue
                
                return response_data
                
            except Exception as e:
                last_exception = e
                elapsed = time.time() - start_time
                
                # 检查是否应该重试
                if self.retry_strategy.should_retry(exception=e):
                    if attempt < self.retry_strategy.max_retries:
                        delay = self.retry_strategy.get_delay(attempt)
                        logger.warning(f"请求异常，{delay:.1f}秒后重试(第{attempt + 1}次): {e}")
                        time.sleep(delay)
                        continue
                
                # 不重试，抛出异常
                raise APIError(f"请求失败: {e}", response=None) from e
        
        # 重试次数用完
        raise APIError(f"请求失败，已重试{self.retry_strategy.max_retries}次: {last_exception}", response=None)
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> ResponseData:
        """GET请求"""
        return self._make_request(HTTPMethod.GET, path, params=params, **kwargs)
    
    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ResponseData:
        """POST请求"""
        return self._make_request(HTTPMethod.POST, path, json=json, data=data, files=files, **kwargs)
    
    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs
    ) -> ResponseData:
        """PUT请求"""
        return self._make_request(HTTPMethod.PUT, path, json=json, data=data, **kwargs)
    
    def delete(self, path: str, **kwargs) -> ResponseData:
        """DELETE请求"""
        return self._make_request(HTTPMethod.DELETE, path, **kwargs)
    
    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs
    ) -> ResponseData:
        """PATCH请求"""
        return self._make_request(HTTPMethod.PATCH, path, json=json, data=data, **kwargs)
    
    def close(self):
        """关闭会话"""
        self.session.close()
        logger.info("API客户端已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False


class AsyncAPIClient:
    """
    【异步API客户端】异步HTTP客户端
    
    功能特性与同步客户端相同，但支持异步操作
    
    示例:
        async with AsyncAPIClient(base_url="https://api.example.com") as client:
            response = await client.get("/users")
            print(response.data)
    """
    
    def __init__(
        self,
        config: Optional[RequestConfig] = None,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.config = config or RequestConfig()
        self.retry_strategy = retry_strategy or RetryStrategy()
        self._session: Optional[Any] = None
        
        # 拦截器
        self.request_interceptor = RequestInterceptor()
        self.response_interceptor = ResponseInterceptor()
        
        # 添加默认拦截器
        self._setup_default_interceptors()
    
    def _setup_default_interceptors(self):
        """设置默认拦截器"""
        def log_request(data: Dict[str, Any]) -> Dict[str, Any]:
            logger.debug(f"异步API请求: {data.get('method')} {data.get('url')}")
            return data
        
        self.request_interceptor.add_handler(log_request)
        
        def log_response(response: ResponseData) -> ResponseData:
            logger.debug(f"异步API响应: {response.status_code} {response.url} ({response.elapsed:.3f}s)")
            return response
        
        self.response_interceptor.add_handler(log_response)
    
    async def _get_session(self):
        """获取或创建aiohttp会话"""
        if self._session is None or self._session.closed:
            import aiohttp
            
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                enable_cleanup_closed=True,
                force_close=False,
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'YL-Monitor-AsyncAPI-Client/1.0',
                    'Accept': 'application/json',
                    **self.config.headers
                }
            )
        
        return self._session
    
    async def _make_request(
        self,
        method: HTTPMethod,
        path: str,
        **kwargs
    ) -> ResponseData:
        """执行异步HTTP请求"""
        import aiohttp
        
        # 构建完整URL
        url = urljoin(self.config.base_url, path)
        
        # 准备请求数据
        request_data = {
            'method': method.value,
            'url': url,
            **kwargs
        }
        
        # 请求拦截器处理
        request_data = self.request_interceptor.process(request_data)
        
        # 执行请求(带重试)
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.retry_strategy.max_retries + 1):
            try:
                session = await self._get_session()
                
                # 准备请求参数
                request_kwargs = {}
                if 'params' in request_data:
                    request_kwargs['params'] = request_data['params']
                if 'json' in request_data:
                    request_kwargs['json'] = request_data['json']
                if 'data' in request_data:
                    request_kwargs['data'] = request_data['data']
                if 'headers' in request_data:
                    request_kwargs['headers'] = request_data['headers']
                
                async with session.request(
                    method.value,
                    url,
                    ssl=self.config.verify_ssl,
                    **request_kwargs
                ) as response:
                    elapsed = time.time() - start_time
                    
                    # 读取响应内容
                    text = await response.text()
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(text)
                    except ValueError:
                        data = text
                    
                    response_data = ResponseData(
                        status_code=response.status,
                        data=data,
                        headers=dict(response.headers),
                        text=text,
                        elapsed=elapsed,
                        url=str(response.url)
                    )
                    
                    # 响应拦截器处理
                    response_data = self.response_interceptor.process(response_data)
                    
                    # 检查是否需要重试
                    if response_data.is_error and self.retry_strategy.should_retry(status_code=response.status):
                        if attempt < self.retry_strategy.max_retries:
                            delay = self.retry_strategy.get_delay(attempt)
                            logger.warning(f"异步请求失败，{delay:.1f}秒后重试(第{attempt + 1}次)")
                            await asyncio.sleep(delay)
                            continue
                    
                    return response_data
                    
            except Exception as e:
                last_exception = e
                elapsed = time.time() - start_time
                
                # 检查是否应该重试
                if self.retry_strategy.should_retry(exception=e):
                    if attempt < self.retry_strategy.max_retries:
                        delay = self.retry_strategy.get_delay(attempt)
                        logger.warning(f"异步请求异常，{delay:.1f}秒后重试(第{attempt + 1}次): {e}")
                        await asyncio.sleep(delay)
                        continue
                
                # 不重试，抛出异常
                raise APIError(f"异步请求失败: {e}", response=None) from e
        
        # 重试次数用完
        raise APIError(f"异步请求失败，已重试{self.retry_strategy.max_retries}次: {last_exception}", response=None)
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> ResponseData:
        """异步GET请求"""
        return await self._make_request(HTTPMethod.GET, path, params=params, **kwargs)
    
    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs
    ) -> ResponseData:
        """异步POST请求"""
        return await self._make_request(HTTPMethod.POST, path, json=json, data=data, **kwargs)
    
    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs
    ) -> ResponseData:
        """异步PUT请求"""
        return await self._make_request(HTTPMethod.PUT, path, json=json, data=data, **kwargs)
    
    async def delete(self, path: str, **kwargs) -> ResponseData:
        """异步DELETE请求"""
        return await self._make_request(HTTPMethod.DELETE, path, **kwargs)
    
    async def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs
    ) -> ResponseData:
        """异步PATCH请求"""
        return await self._make_request(HTTPMethod.PATCH, path, json=json, data=data, **kwargs)
    
    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("异步API客户端已关闭")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


# 便捷函数
def create_client(
    base_url: str,
    timeout: float = 30.0,
    retries: int = 3,
    **kwargs
) -> APIClient:
    """
    快速创建API客户端
    
    Args:
        base_url: 基础URL
        timeout: 超时时间
        retries: 重试次数
        **kwargs: 其他配置参数
    
    Returns:
        APIClient: 配置好的API客户端
    """
    config = RequestConfig(
        base_url=base_url,
        timeout=timeout,
        retries=retries,
        **kwargs
    )
    return APIClient(config)


def create_async_client(
    base_url: str,
    timeout: float = 30.0,
    retries: int = 3,
    **kwargs
) -> AsyncAPIClient:
    """
    快速创建异步API客户端
    
    Args:
        base_url: 基础URL
        timeout: 超时时间
        retries: 重试次数
        **kwargs: 其他配置参数
    
    Returns:
        AsyncAPIClient: 配置好的异步API客户端
    """
    config = RequestConfig(
        base_url=base_url,
        timeout=timeout,
        retries=retries,
        **kwargs
    )
    return AsyncAPIClient(config)


# 导出
__all__ = [
    'APIClient',
    'AsyncAPIClient',
    'RequestConfig',
    'ResponseData',
    'APIError',
    'RetryStrategy',
    'RequestInterceptor',
    'ResponseInterceptor',
    'HTTPMethod',
    'create_client',
    'create_async_client',
]
