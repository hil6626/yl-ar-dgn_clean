"""
标准化错误响应中间件

功能:
- 统一 API 错误响应格式
- 支持多种错误类型
- 详细的错误信息

作者: AI Assistant
版本: v1.0
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import os
import uuid

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError


# 环境配置
ENV = os.getenv("APP_ENV", "development")
IS_PRODUCTION = ENV in ("production", "prod", "staging")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")


class StackTraceLevel:
    """堆栈跟踪级别"""
    NONE = "none"           # 不记录堆栈
    MINIMAL = "minimal"     # 仅记录异常类型和消息
    FULL = "full"           # 完整堆栈跟踪
    DEV_ONLY = "dev_only"   # 仅开发环境显示


# 当前环境适用的堆栈级别
CURRENT_STACK_LEVEL = os.getenv("STACK_TRACE_LEVEL",
    StackTraceLevel.NONE if IS_PRODUCTION else StackTraceLevel.FULL)


class ErrorCode(str, Enum):
    """错误码枚举"""
    SUCCESS = "SUCCESS"
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class APIException(Exception):
    """自定义 API 异常"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class ErrorResponse:
    """标准错误响应格式"""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        stack_trace: Optional[str] = None,  # 新增
        call_chain: Optional[List[str]] = None  # 新增：调用链
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.request_id = request_id
        self.stack_trace = stack_trace  # 新增
        self.call_chain = call_chain or []  # 新增
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（根据环境过滤敏感信息）"""
        result = {
            "code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp
        }
        if self.details:
            result["details"] = self.details
        if self.request_id:
            result["request_id"] = self.request_id
        if self.call_chain:
            result["call_chain"] = self.call_chain

        # 生产环境不返回堆栈跟踪
        if self.stack_trace and not IS_PRODUCTION:
            result["stack_trace"] = self.stack_trace

        return result


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    统一错误处理中间件
    
    标准化所有 API 响应的错误格式:
    {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": {...},  // 可选
        "request_id": "uuid",
        "timestamp": "ISO8601"
    }
    """
    
    async def dispatch(self, request: Request, call_next):
        # 生成或获取调用链ID
        call_chain_id = request.headers.get("X-Call-Chain-ID") or str(uuid.uuid4())
        request.state.call_chain_id = call_chain_id

        # 构建调用链
        call_chain = request.headers.get("X-Call-Chain", "").split(",")
        if call_chain == [""]:  # 处理空字符串情况
            call_chain = []
        call_chain.append(f"error_handler:{datetime.utcnow().isoformat()}")
        # 限制调用链长度（最大10个节点）
        if len(call_chain) > 10:
            call_chain = call_chain[-10:]
        request.state.call_chain = call_chain

        try:
            response = await call_next(request)
            # 将调用链ID传递到响应头
            response.headers["X-Call-Chain-ID"] = call_chain_id
            return response
            
        except HTTPException as exc:
            # HTTP 异常处理
            error_code = self._map_status_code(exc.status_code)
            error_response = ErrorResponse(
                error_code=error_code,
                message=exc.detail,
                request_id=getattr(request.state, "request_id", None),
                call_chain=getattr(request.state, "call_chain", [])
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.to_dict()
            )
            
        except RequestValidationError as exc:
            # 请求验证错误
            error_response = ErrorResponse(
                error_code=ErrorCode.VALIDATION_ERROR.value,
                message="请求参数验证失败",
                details={"errors": self._format_validation_errors(exc)},
                request_id=getattr(request.state, "request_id", None),
                call_chain=getattr(request.state, "call_chain", [])
            )
            return await request_validation_exception_handler(request, exc)
            
        except ValidationError as exc:
            # Pydantic 验证错误
            error_response = ErrorResponse(
                error_code=ErrorCode.VALIDATION_ERROR.value,
                message="数据模型验证失败",
                details={"errors": exc.errors()},
                request_id=getattr(request.state, "request_id", None),
                call_chain=getattr(request.state, "call_chain", [])
            )
            return JSONResponse(
                status_code=422,
                content=error_response.to_dict()
            )
            
        except APIException as exc:
            # 自定义 API 异常
            error_response = ErrorResponse(
                error_code=exc.error_code.value if isinstance(exc.error_code, ErrorCode) else exc.error_code,
                message=exc.message,
                details=exc.details,
                request_id=getattr(request.state, "request_id", None)
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.to_dict()
            )
            
        except Exception as exc:
            # 其他未知异常
            stack_trace = format_stack_trace(exc, CURRENT_STACK_LEVEL)

            # 生产环境：记录日志但不返回客户端
            if IS_PRODUCTION:
                import logging
                logging.error(f"未处理异常 [{getattr(request.state, 'request_id', 'unknown')}]: {str(exc)}",
                             extra={"stack_trace": stack_trace})
                error_details = None
            else:
                # 开发环境：返回详细错误信息
                error_details = {
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "stack_trace": stack_trace
                }

            error_response = ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                message="内部服务器错误",
                details=error_details,
                request_id=getattr(request.state, "request_id", None),
                stack_trace=stack_trace if not IS_PRODUCTION else None,
                call_chain=getattr(request.state, "call_chain", [])
            )

            return JSONResponse(
                status_code=500,
                content=error_response.to_dict()
            )
    
    def _map_status_code(self, status_code: int) -> str:
        """映射 HTTP 状态码到错误码"""
        mapping = {
            400: ErrorCode.BAD_REQUEST.value,
            401: ErrorCode.UNAUTHORIZED.value,
            403: ErrorCode.FORBIDDEN.value,
            404: ErrorCode.NOT_FOUND.value,
        }
        return mapping.get(status_code, ErrorCode.BAD_REQUEST.value)
    
    def _format_validation_errors(self, exc: RequestValidationError) -> list:
        """格式化验证错误"""
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error["loc"])
            errors.append({
                "field": loc,
                "message": error["msg"],
                "type": error["type"]
            })
        return errors


def create_success_response(data: Any = None, message: str = "OK") -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "code": ErrorCode.SUCCESS.value,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def format_stack_trace(exc: Exception, level: str = StackTraceLevel.FULL) -> Optional[str]:
    """
    格式化堆栈跟踪信息

    参数：
        exc: 异常对象
        level: 堆栈级别

    返回：
        格式化后的堆栈字符串，或None（如果级别为NONE）
    """
    if level == StackTraceLevel.NONE:
        return None

    if level == StackTraceLevel.MINIMAL:
        return f"{type(exc).__name__}: {str(exc)}"

    # FULL or DEV_ONLY
    import traceback
    stack_str = traceback.format_exc()
    # 限制堆栈字符串长度（最大5000字符）
    if len(stack_str) > 5000:
        stack_str = stack_str[:5000] + "... (truncated)"
    return stack_str


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """创建错误响应"""
    return ErrorResponse(
        error_code=error_code.value,
        message=message,
        details=details
    ).to_dict()

