"""
中间件模块

提供以下中间件:
- request_id: 请求 ID 追踪
- error_handler: 统一错误响应
- rate_limit: 请求限流

作者: AI Assistant
版本: v1.0
"""

from app.middleware.request_id import (
    RequestIDMiddleware,
    get_request_id,
    get_correlation_id,
    REQUEST_ID_HEADER,
    CORRELATION_ID_HEADER,
)

from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    ErrorResponse,
    ErrorCode,
    APIException,
    create_success_response,
    create_error_response,
)

from app.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitConfig,
    RateLimitEntry,
)

__all__ = [
    # Request ID
    "RequestIDMiddleware",
    "get_request_id",
    "get_correlation_id",
    "REQUEST_ID_HEADER",
    "CORRELATION_ID_HEADER",
    
    # Error Handler
    "ErrorHandlerMiddleware",
    "ErrorResponse",
    "ErrorCode",
    "APIException",
    "create_success_response",
    "create_error_response",
    
    # Rate Limit
    "RateLimitMiddleware",
    "RateLimitConfig",
    "RateLimitEntry",
]

