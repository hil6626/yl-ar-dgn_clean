"""
请求 ID 追踪中间件

功能:
- 为每个请求生成唯一 ID
- 在响应头中返回请求 ID
- 在日志中包含请求 ID

作者: AI Assistant
版本: v1.0
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# 请求 ID 头名称
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求 ID 中间件
    
    为每个请求分配唯一 ID，用于:
    - 请求追踪
    - 日志关联
    - 问题排查
    """
    
    async def dispatch(self, request: Request, call_next):
        # 获取或生成请求 ID
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or request_id
        
        # 存储到 state
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # 添加到响应头
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        
        return response


def get_request_id(request: Request) -> str:
    """获取当前请求的 ID"""
    return getattr(request.state, "request_id", "unknown")


def get_correlation_id(request: Request) -> str:
    """获取当前请求的关联 ID"""
    return getattr(request.state, "correlation_id", "unknown")

