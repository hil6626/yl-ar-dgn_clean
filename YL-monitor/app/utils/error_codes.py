"""
【错误码定义】统一错误码管理

功能:
- 定义所有业务错误码
- 错误码分类管理
- 错误信息国际化支持
- 错误码与HTTP状态码映射
- 错误响应格式化

作者: AI Assistant
创建时间: 2026-02-10
版本: 1.0.0

示例:
    # 使用错误码
    raise BusinessError(ErrorCode.USER_NOT_FOUND)
    
    # 自定义错误信息
    raise BusinessError(ErrorCode.USER_NOT_FOUND, message="用户不存在")
    
    # 格式化错误响应
    response = ErrorResponse.from_error(error)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class ErrorCategory(Enum):
    """
    【错误分类】错误码分类
    
    Attributes:
        SYSTEM: 系统级错误 (1xxx)
        AUTH: 认证授权错误 (2xxx)
        USER: 用户相关错误 (3xxx)
        DATA: 数据相关错误 (4xxx)
        BUSINESS: 业务逻辑错误 (5xxx)
        EXTERNAL: 外部服务错误 (6xxx)
        VALIDATION: 参数验证错误 (7xxx)
        RESOURCE: 资源相关错误 (8xxx)
    """
    SYSTEM = auto()      # 系统级错误 (1xxx)
    AUTH = auto()        # 认证授权错误 (2xxx)
    USER = auto()        # 用户相关错误 (3xxx)
    DATA = auto()        # 数据相关错误 (4xxx)
    BUSINESS = auto()    # 业务逻辑错误 (5xxx)
    EXTERNAL = auto()    # 外部服务错误 (6xxx)
    VALIDATION = auto()  # 参数验证错误 (7xxx)
    RESOURCE = auto()    # 资源相关错误 (8xxx)


@dataclass(frozen=True)
class ErrorCode:
    """
    【错误码】错误码定义
    
    Attributes:
        code: 错误码 (4位数字)
        message: 默认错误信息
        category: 错误分类
        http_status: HTTP状态码
        description: 错误描述
    """
    code: str
    message: str
    category: ErrorCategory
    http_status: int = 500
    description: str = ""
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'message': self.message,
            'category': self.category.name,
            'http_status': self.http_status,
            'description': self.description,
        }


class ErrorCodes:
    """
    【错误码集合】预定义错误码
    
    错误码格式: XYYY
    - X: 分类 (1-8)
    - YYY: 具体错误序号 (000-999)
    """
    
    # ==================== 系统级错误 (1xxx) ====================
    SYSTEM_ERROR = ErrorCode(
        code="1000",
        message="系统错误",
        category=ErrorCategory.SYSTEM,
        http_status=500,
        description="系统内部错误"
    )
    
    SERVICE_UNAVAILABLE = ErrorCode(
        code="1001",
        message="服务不可用",
        category=ErrorCategory.SYSTEM,
        http_status=503,
        description="服务暂时不可用，请稍后重试"
    )
    
    DATABASE_ERROR = ErrorCode(
        code="1002",
        message="数据库错误",
        category=ErrorCategory.SYSTEM,
        http_status=500,
        description="数据库操作失败"
    )
    
    CACHE_ERROR = ErrorCode(
        code="1003",
        message="缓存错误",
        category=ErrorCategory.SYSTEM,
        http_status=500,
        description="缓存操作失败"
    )
    
    CONFIG_ERROR = ErrorCode(
        code="1004",
        message="配置错误",
        category=ErrorCategory.SYSTEM,
        http_status=500,
        description="系统配置错误"
    )
    
    RATE_LIMIT_EXCEEDED = ErrorCode(
        code="1005",
        message="请求过于频繁",
        category=ErrorCategory.SYSTEM,
        http_status=429,
        description="请求频率超过限制"
    )
    
    # ==================== 认证授权错误 (2xxx) ====================
    UNAUTHORIZED = ErrorCode(
        code="2000",
        message="未授权",
        category=ErrorCategory.AUTH,
        http_status=401,
        description="请先登录"
    )
    
    TOKEN_EXPIRED = ErrorCode(
        code="2001",
        message="令牌已过期",
        category=ErrorCategory.AUTH,
        http_status=401,
        description="登录令牌已过期，请重新登录"
    )
    
    TOKEN_INVALID = ErrorCode(
        code="2002",
        message="令牌无效",
        category=ErrorCategory.AUTH,
        http_status=401,
        description="登录令牌无效"
    )
    
    PERMISSION_DENIED = ErrorCode(
        code="2003",
        message="权限不足",
        category=ErrorCategory.AUTH,
        http_status=403,
        description="没有权限执行此操作"
    )
    
    ACCOUNT_LOCKED = ErrorCode(
        code="2004",
        message="账户已锁定",
        category=ErrorCategory.AUTH,
        http_status=403,
        description="账户因多次登录失败被锁定"
    )
    
    ACCOUNT_DISABLED = ErrorCode(
        code="2005",
        message="账户已禁用",
        category=ErrorCategory.AUTH,
        http_status=403,
        description="账户已被禁用"
    )
    
    PASSWORD_EXPIRED = ErrorCode(
        code="2006",
        message="密码已过期",
        category=ErrorCategory.AUTH,
        http_status=403,
        description="密码已过期，请修改密码"
    )
    
    # ==================== 用户相关错误 (3xxx) ====================
    USER_NOT_FOUND = ErrorCode(
        code="3000",
        message="用户不存在",
        category=ErrorCategory.USER,
        http_status=404,
        description="找不到指定用户"
    )
    
    USER_ALREADY_EXISTS = ErrorCode(
        code="3001",
        message="用户已存在",
        category=ErrorCategory.USER,
        http_status=409,
        description="用户名或邮箱已被注册"
    )
    
    USERNAME_INVALID = ErrorCode(
        code="3002",
        message="用户名无效",
        category=ErrorCategory.USER,
        http_status=400,
        description="用户名格式不正确"
    )
    
    EMAIL_INVALID = ErrorCode(
        code="3003",
        message="邮箱格式无效",
        category=ErrorCategory.USER,
        http_status=400,
        description="邮箱地址格式不正确"
    )
    
    PHONE_INVALID = ErrorCode(
        code="3004",
        message="手机号格式无效",
        category=ErrorCategory.USER,
        http_status=400,
        description="手机号格式不正确"
    )
    
    PASSWORD_WEAK = ErrorCode(
        code="3005",
        message="密码强度不足",
        category=ErrorCategory.USER,
        http_status=400,
        description="密码不符合安全要求"
    )
    
    PASSWORD_INCORRECT = ErrorCode(
        code="3006",
        message="密码错误",
        category=ErrorCategory.USER,
        http_status=401,
        description="密码不正确"
    )
    
    # ==================== 数据相关错误 (4xxx) ====================
    DATA_NOT_FOUND = ErrorCode(
        code="4000",
        message="数据不存在",
        category=ErrorCategory.DATA,
        http_status=404,
        description="找不到请求的数据"
    )
    
    DATA_ALREADY_EXISTS = ErrorCode(
        code="4001",
        message="数据已存在",
        category=ErrorCategory.DATA,
        http_status=409,
        description="数据已存在，不能重复创建"
    )
    
    DATA_INVALID = ErrorCode(
        code="4002",
        message="数据无效",
        category=ErrorCategory.DATA,
        http_status=400,
        description="数据格式或内容无效"
    )
    
    DATA_TOO_LARGE = ErrorCode(
        code="4003",
        message="数据过大",
        category=ErrorCategory.DATA,
        http_status=413,
        description="请求数据超过大小限制"
    )
    
    DATA_FORMAT_ERROR = ErrorCode(
        code="4004",
        message="数据格式错误",
        category=ErrorCategory.DATA,
        http_status=400,
        description="数据格式不符合要求"
    )
    
    DATA_CONFLICT = ErrorCode(
        code="4005",
        message="数据冲突",
        category=ErrorCategory.DATA,
        http_status=409,
        description="数据状态冲突，无法执行操作"
    )
    
    # ==================== 业务逻辑错误 (5xxx) ====================
    BUSINESS_ERROR = ErrorCode(
        code="5000",
        message="业务错误",
        category=ErrorCategory.BUSINESS,
        http_status=400,
        description="业务逻辑错误"
    )
    
    OPERATION_NOT_ALLOWED = ErrorCode(
        code="5001",
        message="操作不允许",
        category=ErrorCategory.BUSINESS,
        http_status=403,
        description="当前状态不允许执行此操作"
    )
    
    WORKFLOW_ERROR = ErrorCode(
        code="5002",
        message="工作流错误",
        category=ErrorCategory.BUSINESS,
        http_status=400,
        description="工作流执行错误"
    )
    
    DEPENDENCY_ERROR = ErrorCode(
        code="5003",
        message="依赖错误",
        category=ErrorCategory.BUSINESS,
        http_status=400,
        description="依赖项未满足"
    )
    
    TIMEOUT_ERROR = ErrorCode(
        code="5004",
        message="操作超时",
        category=ErrorCategory.BUSINESS,
        http_status=408,
        description="操作执行超时"
    )
    
    CONCURRENT_ERROR = ErrorCode(
        code="5005",
        message="并发冲突",
        category=ErrorCategory.BUSINESS,
        http_status=409,
        description="并发操作冲突"
    )
    
    # ==================== 外部服务错误 (6xxx) ====================
    EXTERNAL_SERVICE_ERROR = ErrorCode(
        code="6000",
        message="外部服务错误",
        category=ErrorCategory.EXTERNAL,
        http_status=502,
        description="调用外部服务失败"
    )
    
    API_CALL_FAILED = ErrorCode(
        code="6001",
        message="API调用失败",
        category=ErrorCategory.EXTERNAL,
        http_status=502,
        description="调用外部API失败"
    )
    
    WEBHOOK_ERROR = ErrorCode(
        code="6002",
        message="Webhook错误",
        category=ErrorCategory.EXTERNAL,
        http_status=502,
        description="Webhook调用失败"
    )
    
    EMAIL_SEND_FAILED = ErrorCode(
        code="6003",
        message="邮件发送失败",
        category=ErrorCategory.EXTERNAL,
        http_status=502,
        description="发送邮件失败"
    )
    
    SMS_SEND_FAILED = ErrorCode(
        code="6004",
        message="短信发送失败",
        category=ErrorCategory.EXTERNAL,
        http_status=502,
        description="发送短信失败"
    )
    
    # ==================== 参数验证错误 (7xxx) ====================
    PARAM_MISSING = ErrorCode(
        code="7000",
        message="参数缺失",
        category=ErrorCategory.VALIDATION,
        http_status=400,
        description="缺少必需参数"
    )
    
    PARAM_INVALID = ErrorCode(
        code="7001",
        message="参数无效",
        category=ErrorCategory.VALIDATION,
        http_status=400,
        description="参数值无效"
    )
    
    PARAM_TYPE_ERROR = ErrorCode(
        code="7002",
        message="参数类型错误",
        category=ErrorCategory.VALIDATION,
        http_status=400,
        description="参数类型不匹配"
    )
    
    PARAM_RANGE_ERROR = ErrorCode(
        code="7003",
        message="参数超出范围",
        category=ErrorCategory.VALIDATION,
        http_status=400,
        description="参数值超出允许范围"
    )
    
    PARAM_FORMAT_ERROR = ErrorCode(
        code="7004",
        message="参数格式错误",
        category=ErrorCategory.VALIDATION,
        http_status=400,
        description="参数格式不正确"
    )
    
    BODY_PARSE_ERROR = ErrorCode(
        code="7005",
        message="请求体解析错误",
        category=ErrorCategory.VALIDATION,
        http_status=400,
        description="无法解析请求体"
    )
    
    # ==================== 资源相关错误 (8xxx) ====================
    RESOURCE_NOT_FOUND = ErrorCode(
        code="8000",
        message="资源不存在",
        category=ErrorCategory.RESOURCE,
        http_status=404,
        description="找不到请求的资源"
    )
    
    RESOURCE_EXHAUSTED = ErrorCode(
        code="8001",
        message="资源耗尽",
        category=ErrorCategory.RESOURCE,
        http_status=503,
        description="系统资源不足"
    )
    
    FILE_NOT_FOUND = ErrorCode(
        code="8002",
        message="文件不存在",
        category=ErrorCategory.RESOURCE,
        http_status=404,
        description="找不到请求的文件"
    )
    
    FILE_TOO_LARGE = ErrorCode(
        code="8003",
        message="文件过大",
        category=ErrorCategory.RESOURCE,
        http_status=413,
        description="上传文件超过大小限制"
    )
    
    FILE_TYPE_INVALID = ErrorCode(
        code="8004",
        message="文件类型无效",
        category=ErrorCategory.RESOURCE,
        http_status=415,
        description="不支持的文件类型"
    )
    
    STORAGE_ERROR = ErrorCode(
        code="8005",
        message="存储错误",
        category=ErrorCategory.RESOURCE,
        http_status=500,
        description="存储操作失败"
    )
    
    @classmethod
    def get_all_codes(cls) -> List[ErrorCode]:
        """获取所有错误码"""
        codes = []
        for attr_name in dir(cls):
            if not attr_name.startswith('_'):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, ErrorCode):
                    codes.append(attr_value)
        return codes
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional[ErrorCode]:
        """根据错误码查找"""
        for error_code in cls.get_all_codes():
            if error_code.code == code:
                return error_code
        return None
    
    @classmethod
    def get_by_category(cls, category: ErrorCategory) -> List[ErrorCode]:
        """根据分类获取错误码"""
        return [
            code for code in cls.get_all_codes()
            if code.category == category
        ]


class BusinessError(Exception):
    """
    【业务异常】业务逻辑异常
    
    Attributes:
        error_code: 错误码
        message: 错误信息
        data: 附加数据
    """
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.data = data or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.error_code.code,
            'message': self.message,
            'category': self.error_code.category.name,
            'data': self.data,
        }


@dataclass
class ErrorResponse:
    """
    【错误响应】统一错误响应格式
    
    Attributes:
        success: 是否成功(始终为False)
        code: 错误码
        message: 错误信息
        category: 错误分类
        data: 附加数据
        timestamp: 时间戳
        request_id: 请求ID
    """
    success: bool = False
    code: str = ""
    message: str = ""
    category: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    request_id: Optional[str] = None
    
    @classmethod
    def from_error(
        cls,
        error: Union[BusinessError, Exception],
        request_id: Optional[str] = None
    ) -> 'ErrorResponse':
        """
        从异常创建错误响应
        
        Args:
            error: 异常对象
            request_id: 请求ID
        
        Returns:
            ErrorResponse: 错误响应对象
        """
        if isinstance(error, BusinessError):
            return cls(
                success=False,
                code=error.error_code.code,
                message=error.message,
                category=error.error_code.category.name,
                data=error.data,
                request_id=request_id
            )
        else:
            # 未知错误
            return cls(
                success=False,
                code=ErrorCodes.SYSTEM_ERROR.code,
                message=str(error) or "未知错误",
                category=ErrorCategory.SYSTEM.name,
                data={'error_type': type(error).__name__},
                request_id=request_id
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'code': self.code,
            'message': self.message,
            'category': self.category,
            'data': self.data,
            'timestamp': self.timestamp,
            'request_id': self.request_id,
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)


# 便捷函数
def raise_if_not_found(obj: Any, error_code: ErrorCode = ErrorCodes.DATA_NOT_FOUND, message: Optional[str] = None):
    """
    如果对象不存在则抛出异常
    
    Args:
        obj: 要检查的对象
        error_code: 错误码
        message: 错误信息
    """
    if obj is None:
        raise BusinessError(error_code, message)


def raise_if_exists(obj: Any, error_code: ErrorCode = ErrorCodes.DATA_ALREADY_EXISTS, message: Optional[str] = None):
    """
    如果对象已存在则抛出异常
    
    Args:
        obj: 要检查的对象
        error_code: 错误码
        message: 错误信息
    """
    if obj is not None:
        raise BusinessError(error_code, message)


def raise_if_true(condition: bool, error_code: ErrorCode, message: Optional[str] = None):
    """
    如果条件为真则抛出异常
    
    Args:
        condition: 条件
        error_code: 错误码
        message: 错误信息
    """
    if condition:
        raise BusinessError(error_code, message)


def raise_if_false(condition: bool, error_code: ErrorCode, message: Optional[str] = None):
    """
    如果条件为假则抛出异常
    
    Args:
        condition: 条件
        error_code: 错误码
        message: 错误信息
    """
    if not condition:
        raise BusinessError(error_code, message)


def get_error_message(code: str) -> str:
    """
    【获取错误信息】根据错误码获取错误信息
    
    Args:
        code: 错误码
    
    Returns:
        str: 错误信息
    """
    error_code = ErrorCodes.get_by_code(code)
    if error_code:
        return error_code.message
    return "未知错误"


# 导出
__all__ = [
    'ErrorCategory',
    'ErrorCode',
    'ErrorCodes',
    'BusinessError',
    'ErrorResponse',
    'raise_if_not_found',
    'raise_if_exists',
    'raise_if_true',
    'raise_if_false',
    'get_error_message',
]
