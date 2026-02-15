"""
安全中间件

功能:
- SQL注入防护
- XSS攻击防护
- CSRF防护
- 输入验证
- 安全头设置

作者: AI Assistant
版本: 1.0.0
"""

import html
import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SecurityConfig:
    """安全配置"""
    
    def __init__(
        self,
        enable_sql_injection_protection: bool = True,
        enable_xss_protection: bool = True,
        enable_csrf_protection: bool = True,
        enable_security_headers: bool = True,
        csrf_token_length: int = 32,
        csrf_token_header: str = "X-CSRF-Token",
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_content_types: Optional[Set[str]] = None,
        blocked_extensions: Optional[Set[str]] = None
    ):
        self.enable_sql_injection_protection = enable_sql_injection_protection
        self.enable_xss_protection = enable_xss_protection
        self.enable_csrf_protection = enable_csrf_protection
        self.enable_security_headers = enable_security_headers
        self.csrf_token_length = csrf_token_length
        self.csrf_token_header = csrf_token_header
        self.max_request_size = max_request_size
        self.allowed_content_types = allowed_content_types or {
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
            "text/html",
        }
        self.blocked_extensions = blocked_extensions or {
            ".exe", ".dll", ".bat", ".cmd", ".sh", ".php",
            ".jsp", ".asp", ".aspx", ".py", ".rb", ".pl"
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件
    
    提供全面的安全防护
    """
    
    # SQL注入检测模式
    SQL_INJECTION_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",  # 基本SQL注入
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",  # 等号注入
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",  # OR注入
        r"((\%27)|(\'))union",  # UNION注入
        r"exec(\s|\+)+(s|x)p\w+",  # 存储过程
        r"UNION\s+SELECT",  # UNION SELECT
        r"INSERT\s+INTO",  # INSERT注入
        r"DELETE\s+FROM",  # DELETE注入
        r"DROP\s+TABLE",  # DROP注入
    ]
    
    # XSS检测模式
    XSS_PATTERNS = [
        r"<script[^>]*>[\s\S]*?</script>",  # script标签
        r"javascript:",  # javascript协议
        r"on\w+\s*=",  # 事件处理器
        r"<iframe",  # iframe
        r"<object",  # object
        r"<embed",  # embed
    ]
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[SecurityConfig] = None
    ):
        super().__init__(app)
        self.config = config or SecurityConfig()
        
        # 编译正则表达式
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        
        # CSRF Token存储
        self._csrf_tokens: Dict[str, str] = {}
        
        logger.info("安全中间件已初始化")
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        try:
            # 请求大小检查
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.config.max_request_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="请求体过大"
                )
            
            # 内容类型检查
            content_type = request.headers.get("content-type", "").lower()
            if content_type and not self._is_allowed_content_type(content_type):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"不支持的内容类型: {content_type}"
                )
            
            # SQL注入检测
            if self.config.enable_sql_injection_protection:
                await self._check_sql_injection(request)
            
            # XSS检测
            if self.config.enable_xss_protection:
                await self._check_xss(request)
            
            # CSRF检查
            if self.config.enable_csrf_protection:
                await self._check_csrf(request)
            
            # 继续处理请求
            response = await call_next(request)
            
            # 添加安全头
            if self.config.enable_security_headers:
                response = self._add_security_headers(response)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"安全中间件错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="安全检查失败"
            )
    
    def _is_allowed_content_type(self, content_type: str) -> bool:
        """检查内容类型是否允许"""
        # 提取主类型
        if ";" in content_type:
            content_type = content_type.split(";")[0].strip()
        
        return content_type in self.config.allowed_content_types
    
    async def _check_sql_injection(self, request: Request):
        """检查SQL注入"""
        # 检查查询参数
        for key, value in request.query_params.items():
            if self._contains_sql_injection(f"{key}={value}"):
                logger.warning(f"SQL注入检测: {key}={value[:50]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="检测到非法输入"
                )
        
        # 检查路径
        if self._contains_sql_injection(request.url.path):
            logger.warning(f"SQL注入检测(路径): {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="检测到非法路径"
            )
    
    def _contains_sql_injection(self, text: str) -> bool:
        """检查文本是否包含SQL注入"""
        for pattern in self.sql_patterns:
            if pattern.search(text):
                return True
        return False
    
    async def _check_xss(self, request: Request):
        """检查XSS攻击"""
        # 检查查询参数
        for key, value in request.query_params.items():
            if self._contains_xss(value):
                logger.warning(f"XSS检测: {key}={value[:50]}")
                # 不阻止，但记录日志
                # 实际应用中可以选择阻止或清理
    
    def _contains_xss(self, text: str) -> bool:
        """检查文本是否包含XSS"""
        for pattern in self.xss_patterns:
            if pattern.search(text):
                return True
        return False
    
    async def _check_csrf(self, request: Request):
        """检查CSRF"""
        # 只检查修改操作的请求
        if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
            return
        
        # 检查CSRF Token
        csrf_token = request.headers.get(self.config.csrf_token_header)
        if not csrf_token:
            # 尝试从表单数据获取
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    csrf_token = data.get("csrf_token")
            except:
                pass
        
        if not csrf_token or not self._validate_csrf_token(csrf_token):
            logger.warning(f"CSRF验证失败: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF验证失败"
            )
    
    def _validate_csrf_token(self, token: str) -> bool:
        """验证CSRF Token"""
        # 简化实现，实际应使用更复杂的验证
        return token in self._csrf_tokens
    
    def _add_security_headers(self, response: Response) -> Response:
        """添加安全头"""
        headers = {
            # 防止MIME类型嗅探
            "X-Content-Type-Options": "nosniff",
            # XSS保护
            "X-XSS-Protection": "1; mode=block",
            # 点击劫持保护
            "X-Frame-Options": "DENY",
            # 内容安全策略
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            # 严格传输安全(HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            # 引用来源策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 权限策略
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


class InputValidator:
    """
    输入验证器
    
    提供各种输入验证功能
    """
    
    # 邮箱正则
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # 手机号正则(中国)
    PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
    
    # 用户名正则
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
    
    # 密码强度正则(至少8位，包含大小写字母和数字)
    STRONG_PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$')
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """验证邮箱"""
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """验证手机号"""
        return bool(cls.PHONE_PATTERN.match(phone))
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """验证用户名"""
        return bool(cls.USERNAME_PATTERN.match(username))
    
    @classmethod
    def validate_password_strength(cls, password: str) -> bool:
        """验证密码强度"""
        return bool(cls.STRONG_PASSWORD_PATTERN.match(password))
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """
        清理HTML
        
        转义HTML特殊字符
        """
        return html.escape(text)
    
    @classmethod
    def sanitize_sql(cls, text: str) -> str:
        """
        清理SQL输入
        
        移除或转义SQL特殊字符
        """
        # 转义单引号
        return text.replace("'", "''")
    
    @classmethod
    def validate_file_extension(cls, filename: str, allowed_extensions: Set[str]) -> bool:
        """验证文件扩展名"""
        if "." not in filename:
            return False
        
        ext = filename.lower().split(".")[-1]
        return f".{ext}" in allowed_extensions
    
    @classmethod
    def validate_file_size(cls, size: int, max_size: int) -> bool:
        """验证文件大小"""
        return size <= max_size


class RateLimiter:
    """
    速率限制器
    
    简单的内存速率限制实现
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        current_time = time.time()
        
        # 清理过期记录
        if key in self._requests:
            self._requests[key] = [
                t for t in self._requests[key]
                if current_time - t < self.window_seconds
            ]
        else:
            self._requests[key] = []
        
        # 检查限制
        if len(self._requests[key]) >= self.max_requests:
            return False
        
        # 记录请求
        self._requests[key].append(current_time)
        return True
    
    def get_remaining(self, key: str) -> int:
        """获取剩余请求数"""
        current_time = time.time()
        
        if key not in self._requests:
            return self.max_requests
        
        # 清理过期记录
        valid_requests = [
            t for t in self._requests[key]
            if current_time - t < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(valid_requests))


import time

# 全局速率限制器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局速率限制器"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter):
    """设置全局速率限制器"""
    global _rate_limiter
    _rate_limiter = limiter


# 安全工具函数
def generate_csrf_token() -> str:
    """生成CSRF Token"""
    import secrets
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """
    哈希密码
    
    使用bcrypt(如果可用)或回退到简单哈希
    """
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    except ImportError:
        # 回退到SHA256(仅用于开发，生产环境应使用bcrypt)
        import hashlib
        logger.warning("bcrypt未安装，使用SHA256回退(不推荐用于生产)")
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ImportError:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed


# 安全建议
SECURITY_TIPS = {
    "use_https": "生产环境必须使用HTTPS",
    "validate_input": "所有用户输入都必须验证",
    "parameterize_queries": "使用参数化查询防止SQL注入",
    "escape_output": "输出到HTML时进行转义",
    "csrf_protection": "所有修改操作都需要CSRF保护",
    "rate_limiting": "实施速率限制防止暴力攻击",
    "secure_headers": "添加安全相关的HTTP头",
    "password_hashing": "使用bcrypt或Argon2哈希密码",
    "session_security": "使用安全的会话管理",
    "principle_of_least_privilege": "遵循最小权限原则",
}
