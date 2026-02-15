"""
请求限流中间件

功能:
- 防止 API 滥用
- 支持 IP 级别的限流
- 可配置的限流规则

作者: AI Assistant
版本: v1.0
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests: int = 100  # 允许的请求数
    seconds: int = 60    # 时间窗口（秒）


@dataclass
class RateLimitEntry:
    """限流条目"""
    count: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求限流中间件
    
    基于滑动窗口算法的限流实现:
    - 按 IP 地址限流
    - 可配置限流规则
    - 返回剩余请求数和重试时间
    
    响应头:
    - X-RateLimit-Limit: 允许的最大请求数
    - X-RateLimit-Remaining: 剩余请求数
    - X-RateLimit-Reset: 窗口重置时间戳
    """
    
    # 默认限流配置
    DEFAULT_CONFIG = RateLimitConfig(requests=100, seconds=60)
    
    # 不同路径的限流配置
    PATH_CONFIGS: Dict[str, RateLimitConfig] = {
        "/api/": RateLimitConfig(requests=100, seconds=60),      # 普通 API
        "/api/scripts/run": RateLimitConfig(requests=10, seconds=60),  # 脚本执行
        "/api/dag/run": RateLimitConfig(requests=5, seconds=60),      # DAG 执行
    }
    
    def __init__(self, app, default_config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.default_config = default_config or self.DEFAULT_CONFIG
        self.windows: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端 IP
        client_ip = self._get_client_ip(request)
        key = f"{client_ip}:{request.url.path}"
        
        # 获取限流配置
        config = self._get_config(request.url.path)
        
        # 检查限流
        remaining, reset_at = self._check_rate_limit(key, config)
        
        # 获取响应
        response = await call_next(request)
        
        # 添加限流头
        response.headers["X-RateLimit-Limit"] = str(config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))
        
        # 如果超过限流，返回 429
        if remaining < 0:
            response = JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁，请稍后再试",
                    "details": {
                        "retry_after": int(reset_at - time.time()) + 1
                    },
                    "timestamp": self._get_timestamp()
                }
            )
            response.headers["Retry-After"] = str(int(reset_at - time.time()) + 1)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 优先使用 X-Forwarded-For（反向代理场景）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # 直接连接
        return request.client.host if request.client else "unknown"
    
    def _get_config(self, path: str) -> RateLimitConfig:
        """获取路径对应的限流配置"""
        # 精确匹配
        if path in self.PATH_CONFIGS:
            return self.PATH_CONFIGS[path]
        
        # 前缀匹配
        for prefix, config in self.PATH_CONFIGS.items():
            if path.startswith(prefix):
                return config
        
        return self.default_config
    
    def _check_rate_limit(self, key: str, config: RateLimitConfig) -> Tuple[int, float]:
        """
        检查限流
        
        返回:
            remaining: 剩余请求数
            reset_at: 窗口重置时间戳
        """
        now = time.time()
        entry = self.windows[key]
        
        # 如果窗口已过期，重置
        if now - entry.window_start >= config.seconds:
            entry.count = 0
            entry.window_start = now
        
        # 计算剩余请求数
        remaining = config.requests - entry.count - 1
        
        # 增加计数
        entry.count += 1
        
        return remaining, entry.window_start + config.seconds
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳（ISO 格式）"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def reset(self, key: Optional[str] = None):
        """重置限流计数"""
        if key:
            self.windows.pop(key, None)
        else:
            self.windows.clear()

