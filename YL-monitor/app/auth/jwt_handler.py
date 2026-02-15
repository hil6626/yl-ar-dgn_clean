"""
JWT认证处理器

功能:
- JWT Token生成和验证
- Token刷新机制
- 黑名单管理
- 权限声明处理

作者: AI Assistant
版本: 1.0.0
"""

import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Token类型"""
    ACCESS = "access"    # 访问令牌
    REFRESH = "refresh"  # 刷新令牌


class TokenError(Exception):
    """Token错误"""
    pass


class TokenExpiredError(TokenError):
    """Token过期错误"""
    pass


class TokenInvalidError(TokenError):
    """Token无效错误"""
    pass


@dataclass
class TokenPayload:
    """Token载荷"""
    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    token_type: TokenType
    issued_at: float
    expires_at: float
    jti: str  # JWT ID，用于唯一标识token
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sub": self.user_id,
            "username": self.username,
            "roles": self.roles,
            "permissions": self.permissions,
            "type": self.token_type.value,
            "iat": self.issued_at,
            "exp": self.expires_at,
            "jti": self.jti,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """从字典创建"""
        return cls(
            user_id=data.get("sub", ""),
            username=data.get("username", ""),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            token_type=TokenType(data.get("type", "access")),
            issued_at=data.get("iat", 0),
            expires_at=data.get("exp", 0),
            jti=data.get("jti", ""),
        )


class JWTHandler:
    """
    JWT处理器
    
    处理JWT Token的生成、验证和刷新
    """
    
    # 默认配置
    DEFAULT_ACCESS_TOKEN_EXPIRE = 30  # 分钟
    DEFAULT_REFRESH_TOKEN_EXPIRE = 7  # 天
    ALGORITHM = "HS256"
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        access_token_expire: int = DEFAULT_ACCESS_TOKEN_EXPIRE,
        refresh_token_expire: int = DEFAULT_REFRESH_TOKEN_EXPIRE,
        algorithm: str = ALGORITHM
    ):
        # 如果没有提供密钥，生成一个随机密钥(仅用于开发)
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.access_token_expire = access_token_expire
        self.refresh_token_expire = refresh_token_expire
        self.algorithm = algorithm
        
        # Token黑名单(用于注销)
        self._blacklist: Set[str] = set()
        
        # 刷新令牌存储(用于验证刷新令牌)
        self._refresh_tokens: Dict[str, str] = {}  # jti -> user_id
        
        logger.info("JWT处理器已初始化")
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            roles: 用户角色列表
            permissions: 用户权限列表
            extra_claims: 额外声明
        
        Returns:
            JWT Token字符串
        """
        now = time.time()
        expires = now + (self.access_token_expire * 60)
        
        payload = TokenPayload(
            user_id=user_id,
            username=username,
            roles=roles or [],
            permissions=permissions or [],
            token_type=TokenType.ACCESS,
            issued_at=now,
            expires_at=expires,
            jti=secrets.token_urlsafe(16)
        )
        
        token_data = payload.to_dict()
        
        # 添加额外声明
        if extra_claims:
            token_data.update(extra_claims)
        
        token = jwt.encode(
            token_data,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        logger.debug(f"访问令牌已创建: user={username}, jti={payload.jti}")
        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        创建刷新令牌
        
        Args:
            user_id: 用户ID
        
        Returns:
            刷新令牌字符串
        """
        now = time.time()
        expires = now + (self.refresh_token_expire * 86400)  # 转换为秒
        
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": user_id,
            "type": TokenType.REFRESH.value,
            "iat": now,
            "exp": expires,
            "jti": jti,
        }
        
        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # 存储刷新令牌
        self._refresh_tokens[jti] = user_id
        
        logger.debug(f"刷新令牌已创建: user={user_id}, jti={jti}")
        return token
    
    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> TokenPayload:
        """
        验证Token
        
        Args:
            token: JWT Token字符串
            token_type: 期望的Token类型
        
        Returns:
            TokenPayload对象
        
        Raises:
            TokenExpiredError: Token已过期
            TokenInvalidError: Token无效
        """
        try:
            # 解码token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 检查token类型
            if payload.get("type") != token_type.value:
                raise TokenInvalidError(f"Token类型不匹配: 期望{token_type.value}")
            
            # 检查黑名单
            jti = payload.get("jti")
            if jti and jti in self._blacklist:
                raise TokenInvalidError("Token已被注销")
            
            # 验证刷新令牌
            if token_type == TokenType.REFRESH:
                if jti not in self._refresh_tokens:
                    raise TokenInvalidError("刷新令牌无效或已过期")
            
            return TokenPayload.from_dict(payload)
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token已过期")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Token无效: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的访问令牌，如果刷新失败则返回None
        """
        try:
            # 验证刷新令牌
            payload = self.verify_token(refresh_token, TokenType.REFRESH)
            
            # 获取用户信息(这里简化处理，实际应从数据库获取)
            user_id = payload.user_id
            
            # 创建新的访问令牌
            # 注意：实际应用中应从数据库获取用户详细信息
            access_token = self.create_access_token(
                user_id=user_id,
                username=f"user_{user_id}",  # 简化处理
                roles=[],  # 应从数据库获取
                permissions=[]  # 应从数据库获取
            )
            
            logger.info(f"访问令牌已刷新: user={user_id}")
            return access_token
            
        except TokenError as e:
            logger.warning(f"刷新令牌失败: {e}")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        注销Token(加入黑名单)
        
        Args:
            token: 要注销的Token
        
        Returns:
            是否成功注销
        """
        try:
            # 解码token(不验证过期时间)
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            if jti:
                self._blacklist.add(jti)
                logger.info(f"Token已注销: jti={jti}")
                return True
            
            return False
            
        except jwt.InvalidTokenError:
            return False
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        注销刷新令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            是否成功注销
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get("jti")
            if jti and jti in self._refresh_tokens:
                del self._refresh_tokens[jti]
                self._blacklist.add(jti)
                logger.info(f"刷新令牌已注销: jti={jti}")
                return True
            
            return False
            
        except jwt.InvalidTokenError:
            return False
    
    def cleanup_expired_tokens(self):
        """清理过期的刷新令牌"""
        current_time = time.time()
        expired_jtis = []
        
        for jti, token in self._refresh_tokens.items():
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm]
                )
                exp = payload.get("exp", 0)
                if exp < current_time:
                    expired_jtis.append(jti)
            except jwt.ExpiredSignatureError:
                expired_jtis.append(jti)
            except jwt.InvalidTokenError:
                expired_jtis.append(jti)
        
        for jti in expired_jtis:
            del self._refresh_tokens[jti]
            self._blacklist.discard(jti)  # 从黑名单中移除(已过期不需要黑名单)
        
        if expired_jtis:
            logger.info(f"已清理 {len(expired_jtis)} 个过期刷新令牌")
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取Token信息(不验证)
        
        Args:
            token: JWT Token
        
        Returns:
            Token信息字典
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            return payload
        except jwt.InvalidTokenError:
            return None


# HTTP Bearer安全方案
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = security_bearer
) -> Optional[TokenPayload]:
    """
    获取当前用户(依赖函数)
    
    用于FastAPI依赖注入
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # 从应用状态获取JWT处理器
    jwt_handler: Optional[JWTHandler] = getattr(request.app.state, "jwt_handler", None)
    if not jwt_handler:
        logger.error("JWT处理器未初始化")
        return None
    
    try:
        payload = jwt_handler.verify_token(token, TokenType.ACCESS)
        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token无效: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = security_bearer
) -> TokenPayload:
    """
    要求认证(依赖函数)
    
    用于需要强制认证的端点
    """
    user = await get_current_user(request, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_permissions(required_permissions: List[str]):
    """
    权限要求装饰器工厂
    
    用于检查用户是否具有所需权限
    """
    async def permission_checker(
        user: TokenPayload = require_auth
    ) -> TokenPayload:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证"
            )
        
        # 检查权限
        user_perms = set(user.permissions)
        required_perms = set(required_permissions)
        
        if not required_perms.issubset(user_perms):
            missing = required_perms - user_perms
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {', '.join(missing)}"
            )
        
        return user
    
    return permission_checker


def require_roles(required_roles: List[str]):
    """
    角色要求装饰器工厂
    
    用于检查用户是否具有所需角色
    """
    async def role_checker(
        user: TokenPayload = require_auth
    ) -> TokenPayload:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证"
            )
        
        # 检查角色
        user_roles = set(user.roles)
        required_roles_set = set(required_roles)
        
        if not required_roles_set.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(required_roles)}"
            )
        
        return user
    
    return role_checker


# 全局JWT处理器实例
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """获取全局JWT处理器"""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler


def set_jwt_handler(handler: JWTHandler):
    """设置全局JWT处理器"""
    global _jwt_handler
    _jwt_handler = handler


# Token工具函数
def extract_token_from_header(header: str) -> Optional[str]:
    """从Authorization头提取Token"""
    if not header:
        return None
    
    parts = header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    
    return None


def is_token_expired(token: str, secret_key: str) -> bool:
    """检查Token是否过期"""
    try:
        jwt.decode(token, secret_key, algorithms=["HS256"])
        return False
    except jwt.ExpiredSignatureError:
        return True
    except jwt.InvalidTokenError:
        return True
