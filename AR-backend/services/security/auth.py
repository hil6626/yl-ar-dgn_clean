#!/usr/bin/env python3
"""
JWT Authentication Service
YL-AR-DGN API Security Module
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets


class TokenType(Enum):
    """Token类型枚举"""
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenPayload:
    """Token载荷数据类"""
    user_id: str
    role: str
    permissions: List[str]
    exp: datetime
    iat: datetime
    token_type: TokenType = TokenType.ACCESS


class JWTAuth:
    """
    JWT认证服务类
    
    提供JWT令牌的创建、验证和刷新功能。
    
    Attributes:
        secret_key: JWT签名密钥
        algorithm: 加密算法
        access_token_expire_minutes: 访问令牌过期时间(分钟)
        refresh_token_expire_days: 刷新令牌过期时间(天)
    """
    
    # 默认配置
    DEFAULT_ALGORITHM = "HS256"
    DEFAULT_ACCESS_EXPIRE_MINUTES = 30
    DEFAULT_REFRESH_EXPIRE_DAYS = 7
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None
    ):
        """
        初始化JWT认证服务
        
        Args:
            secret_key: JWT签名密钥
            algorithm: 加密算法
            access_token_expire_minutes: 访问令牌过期时间
            refresh_token_expire_days: 刷新令牌过期时间
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.algorithm = algorithm or self.DEFAULT_ALGORITHM
        self.access_token_expire_minutes = (
            access_token_expire_minutes or self.DEFAULT_ACCESS_EXPIRE_MINUTES
        )
        self.refresh_token_expire_days = (
            refresh_token_expire_days or self.DEFAULT_REFRESH_EXPIRE_DAYS
        )
    
    def create_access_token(
        self,
        user_id: str,
        role: str,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Dict[str, Any] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            role: 用户角色
            permissions: 权限列表
            expires_delta: 自定义过期时间
            additional_claims: 额外的声明
            
        Returns:
            str: JWT访问令牌
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "role": role,
            "permissions": permissions or [],
            "type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        # 添加额外声明
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        additional_claims: Dict[str, Any] = None
    ) -> str:
        """
        创建刷新令牌
        
        Args:
            user_id: 用户ID
            additional_claims: 额外的声明
            
        Returns:
            str: JWT刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(
        self,
        token: str,
        expected_type: TokenType = TokenType.ACCESS
    ) -> Optional[TokenPayload]:
        """
        验证Token并返回载荷
        
        Args:
            token: JWT令牌
            expected_type: 期望的令牌类型
            
        Returns:
            Optional[TokenPayload]: 令牌载荷，验证失败返回None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 验证令牌类型
            if payload.get("type") != expected_type.value:
                return None
            
            return TokenPayload(
                user_id=payload["sub"],
                role=payload["role"],
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                token_type=expected_type
            )
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError as e:
            return None
    
    def refresh_access_token(
        self,
        refresh_token: str,
        role: str = None,
        permissions: List[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            role: 可选的新角色
            permissions: 可选的新权限列表
            
        Returns:
            Optional[Dict]: 包含新访问令牌和刷新令牌的字典
        """
        payload = self.verify_token(refresh_token, TokenType.REFRESH)
        
        if not payload:
            return None
        
        # 使用原令牌的用户ID，创建新令牌
        new_access_token = self.create_access_token(
            user_id=payload.user_id,
            role=role or payload.role,
            permissions=permissions or payload.permissions
        )
        
        new_refresh_token = self.create_refresh_token(payload.user_id)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码令牌但不验证签名
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict]: 解码后的载荷
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except jwt.InvalidTokenError:
            return None


class APIKeyAuth:
    """
    API密钥认证服务类
    
    提供API密钥的创建、验证和管理功能。
    """
    
    KEY_PREFIX = "ak_"
    KEY_LENGTH = 32
    SIGNATURE_LENGTH = 64
    
    def __init__(self, secret_salt: str = None):
        """
        初始化API密钥认证服务
        
        Args:
            secret_salt: 密钥盐值
        """
        self.secret_salt = secret_salt or secrets.token_hex(16)
        self.keys: Dict[str, Dict] = {}
    
    @dataclass
    class APIKeyInfo:
        """API密钥信息"""
        key_id: str
        user_id: str
        permissions: List[str]
        created_at: datetime
        expires_at: datetime
        last_used_at: Optional[datetime]
        is_active: bool
    
    def create_key(
        self,
        user_id: str,
        permissions: List[str] = None,
        expires_days: int = 365,
        metadata: Dict[str, Any] = None
    ) -> tuple:
        """
        创建API密钥
        
        Args:
            user_id: 用户ID
            permissions: 权限列表
            expires_days: 过期天数
            metadata: 元数据
            
        Returns:
            tuple: (key_id, full_key)
        """
        key_id = f"{self.KEY_PREFIX}{secrets.token_hex(8)}"
        secret = secrets.token_urlsafe(self.KEY_LENGTH)
        key_hash = self._hash_key(secret)
        
        key_info = {
            "key_id": key_id,
            "key_hash": key_hash,
            "user_id": user_id,
            "permissions": permissions or [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=expires_days),
            "last_used_at": None,
            "is_active": True
        }
        
        self.keys[key_id] = key_info
        
        # 返回完整密钥（只返回一次）
        full_key = f"{key_id}.{secret}"
        return key_id, full_key
    
    def verify_key(
        self,
        key_id: str,
        signature: str = None
    ) -> Optional[Dict]:
        """
        验证API密钥
        
        Args:
            key_id: 密钥ID
            signature: 签名（可选）
            
        Returns:
            Optional[Dict]: 密钥信息，验证失败返回None
        """
        if key_id not in self.keys:
            return None
        
        key_info = self.keys[key_id]
        
        # 检查是否激活
        if not key_info["is_active"]:
            return None
        
        # 检查是否过期
        if datetime.utcnow() > key_info["expires_at"]:
            return None
        
        # 更新最后使用时间
        key_info["last_used_at"] = datetime.utcnow()
        
        return key_info
    
    def revoke_key(self, key_id: str) -> bool:
        """
        撤销API密钥
        
        Args:
            key_id: 密钥ID
            
        Returns:
            bool: 是否成功撤销
        """
        if key_id in self.keys:
            self.keys[key_id]["is_active"] = False
            return True
        return False
    
    def list_keys(self, user_id: str = None) -> List[Dict]:
        """
        列出API密钥
        
        Args:
            user_id: 可选的用户ID过滤
            
        Returns:
            List[Dict]: 密钥信息列表
        """
        keys = []
        for key_id, info in self.keys.items():
            if user_id is None or info["user_id"] == user_id:
                keys.append({
                    "key_id": key_id,
                    "user_id": info["user_id"],
                    "permissions": info["permissions"],
                    "created_at": info["created_at"].isoformat(),
                    "expires_at": info["expires_at"].isoformat(),
                    "last_used_at": (
                        info["last_used_at"].isoformat() 
                        if info["last_used_at"] else None
                    ),
                    "is_active": info["is_active"]
                })
        return keys
    
    def _hash_key(self, key: str) -> str:
        """哈希密钥"""
        return hashlib.sha256(
            f"{key}:{self.secret_salt}".encode()
        ).hexdigest()


# 便捷函数
def create_jwt_auth(secret_key: str = None) -> JWTAuth:
    """创建JWT认证服务实例"""
    return JWTAuth(secret_key=secret_key)


def create_api_key_auth(secret_salt: str = None) -> APIKeyAuth:
    """创建API密钥认证服务实例"""
    return APIKeyAuth(secret_salt=secret_salt)
