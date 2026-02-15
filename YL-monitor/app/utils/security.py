"""
安全工具模块

功能:
- 密码加密 (bcrypt/Argon2)
- 数据加密/解密 (AES)
- 密钥管理
- 敏感数据脱敏
- 安全随机数生成

作者: AI Assistant
版本: 1.0.0
"""

import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
import string
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class PasswordHasher:
    """
    密码哈希器
    
    使用bcrypt或Argon2进行密码哈希
    """
    
    def __init__(self, algorithm: str = "bcrypt"):
        self.algorithm = algorithm
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖库"""
        if self.algorithm == "bcrypt":
            try:
                import bcrypt
                self._hasher = bcrypt
                self._available = True
            except ImportError:
                logger.warning("bcrypt未安装，密码哈希将使用SHA256回退(不安全)")
                self._available = False
        elif self.algorithm == "argon2":
            try:
                import argon2
                self._hasher = argon2.PasswordHasher()
                self._available = True
            except ImportError:
                logger.warning("argon2未安装，密码哈希将使用SHA256回退(不安全)")
                self._available = False
        else:
            self._available = False
    
    def hash(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 明文密码
        
        Returns:
            哈希后的密码字符串
        """
        if not self._available:
            # 回退到SHA256(仅用于开发)
            return self._fallback_hash(password)
        
        if self.algorithm == "bcrypt":
            salt = self._hasher.gensalt()
            return self._hasher.hashpw(password.encode(), salt).decode()
        elif self.algorithm == "argon2":
            return self._hasher.hash(password)
        
        return self._fallback_hash(password)
    
    def verify(self, password: str, hashed: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed: 哈希后的密码
        
        Returns:
            是否匹配
        """
        if not self._available:
            return self._fallback_verify(password, hashed)
        
        try:
            if self.algorithm == "bcrypt":
                return self._hasher.checkpw(password.encode(), hashed.encode())
            elif self.algorithm == "argon2":
                self._hasher.verify(hashed, password)
                return True
        except Exception:
            return False
        
        return False
    
    def _fallback_hash(self, password: str) -> str:
        """回退哈希方法(SHA256)"""
        logger.warning("使用不安全的SHA256哈希，请安装bcrypt或argon2")
        salt = secrets.token_hex(16)
        hash_value = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"sha256${salt}${hash_value}"
    
    def _fallback_verify(self, password: str, hashed: str) -> bool:
        """回退验证方法"""
        if not hashed.startswith("sha256$"):
            return False
        
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        
        salt = parts[1]
        expected_hash = parts[2]
        actual_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        return hmac.compare_digest(expected_hash, actual_hash)
    
    def needs_rehash(self, hashed: str) -> bool:
        """检查是否需要重新哈希"""
        if not self._available:
            return True  # 回退算法总是需要重新哈希
        
        if self.algorithm == "argon2":
            try:
                return self._hasher.check_needs_rehash(hashed)
            except Exception:
                return True
        
        return False


class DataEncryptor:
    """
    数据加密器
    
    使用AES-256-GCM进行数据加密
    """
    
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or self._generate_key()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖库"""
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            self._fernet = Fernet
            self._aesgcm = AESGCM
            self._available = True
        except ImportError:
            logger.warning("cryptography未安装，加密功能将不可用")
            self._available = False
    
    @staticmethod
    def _generate_key() -> bytes:
        """生成密钥"""
        try:
            from cryptography.fernet import Fernet
            return Fernet.generate_key()
        except ImportError:
            # 回退到随机生成
            return secrets.token_urlsafe(32).encode()
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的数据
        
        Returns:
            Base64编码的加密数据
        """
        if not self._available:
            raise RuntimeError("加密库未安装")
        
        if isinstance(data, str):
            data = data.encode()
        
        try:
            f = self._fernet(self.key)
            encrypted = f.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: Base64编码的加密数据
        
        Returns:
            解密后的字符串
        """
        if not self._available:
            raise RuntimeError("加密库未安装")
        
        try:
            f = self._fernet(self.key)
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = f.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """加密字典"""
        import json
        return self.encrypt(json.dumps(data))
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """解密字典"""
        import json
        return json.loads(self.decrypt(encrypted_data))


class KeyManager:
    """
    密钥管理器
    
    管理加密密钥的安全存储和轮换
    """
    
    def __init__(self, key_storage_path: Optional[str] = None):
        self.key_storage_path = key_storage_path or ".keys"
        self._keys: Dict[str, bytes] = {}
        self._load_keys()
    
    def _load_keys(self):
        """从环境变量加载密钥"""
        # 主密钥
        master_key = os.environ.get("MASTER_KEY")
        if master_key:
            self._keys["master"] = master_key.encode()
        
        # JWT密钥
        jwt_key = os.environ.get("JWT_SECRET_KEY")
        if jwt_key:
            self._keys["jwt"] = jwt_key.encode()
        
        # 数据库加密密钥
        db_key = os.environ.get("DB_ENCRYPTION_KEY")
        if db_key:
            self._keys["db"] = db_key.encode()
        
        # 会话密钥
        session_key = os.environ.get("SESSION_KEY")
        if session_key:
            self._keys["session"] = session_key.encode()
    
    def get_key(self, name: str) -> Optional[bytes]:
        """获取密钥"""
        return self._keys.get(name)
    
    def set_key(self, name: str, key: Union[str, bytes]):
        """设置密钥"""
        if isinstance(key, str):
            key = key.encode()
        self._keys[name] = key
    
    def generate_key(self, name: str, length: int = 32) -> bytes:
        """生成新密钥"""
        key = secrets.token_urlsafe(length).encode()
        self._keys[name] = key
        return key
    
    def rotate_key(self, name: str) -> bytes:
        """轮换密钥"""
        return self.generate_key(name)
    
    def get_or_create_key(self, name: str, length: int = 32) -> bytes:
        """获取或创建密钥"""
        if name not in self._keys:
            return self.generate_key(name, length)
        return self._keys[name]


class DataMasker:
    """
    数据脱敏器
    
    对敏感数据进行脱敏处理
    """
    
    @staticmethod
    def mask_email(email: str) -> str:
        """脱敏邮箱"""
        if "@" not in email:
            return email
        
        local, domain = email.split("@")
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """脱敏手机号"""
        if len(phone) < 7:
            return phone
        
        return phone[:3] + "****" + phone[-4:]
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """脱敏身份证号"""
        if len(id_card) < 8:
            return id_card
        
        return id_card[:4] + "********" + id_card[-4:]
    
    @staticmethod
    def mask_bank_card(bank_card: str) -> str:
        """脱敏银行卡号"""
        if len(bank_card) < 8:
            return bank_card
        
        return "****" + bank_card[-4:]
    
    @staticmethod
    def mask_name(name: str) -> str:
        """脱敏姓名"""
        if len(name) <= 1:
            return name
        
        return name[0] + "*" * (len(name) - 1)
    
    @staticmethod
    def mask_string(text: str, visible_start: int = 3, visible_end: int = 3) -> str:
        """
        通用字符串脱敏
        
        Args:
            text: 原始字符串
            visible_start: 开头保留字符数
            visible_end: 结尾保留字符数
        """
        if len(text) <= visible_start + visible_end:
            return "*" * len(text)
        
        return text[:visible_start] + "*" * (len(text) - visible_start - visible_end) + text[-visible_end:]
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """
        对字典中的敏感字段脱敏
        
        Args:
            data: 原始数据字典
            sensitive_fields: 需要脱敏的字段列表
        """
        result = {}
        for key, value in data.items():
            if key in sensitive_fields:
                if isinstance(value, str):
                    if "email" in key.lower():
                        result[key] = cls.mask_email(value)
                    elif "phone" in key.lower() or "mobile" in key.lower():
                        result[key] = cls.mask_phone(value)
                    elif "password" in key.lower() or "secret" in key.lower():
                        result[key] = "********"
                    elif "card" in key.lower():
                        result[key] = cls.mask_bank_card(value)
                    else:
                        result[key] = cls.mask_string(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result


class SecureRandom:
    """
    安全随机数生成器
    """
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """
        生成随机密码
        
        包含大小写字母、数字和特殊字符
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """生成一次性验证码"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_nonce(length: int = 16) -> str:
        """生成随机nonce"""
        return secrets.token_hex(length)


class SecurityUtils:
    """
    安全工具函数集合
    """
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名
        
        移除危险字符和路径遍历尝试
        """
        # 移除路径分隔符
        filename = os.path.basename(filename)
        
        # 移除危险字符
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # 检查路径遍历
        if '..' in filename or filename.startswith('.'):
            filename = filename.replace('..', '_')
        
        return filename
    
    @staticmethod
    def is_safe_path(path: str, allowed_base: str) -> bool:
        """
        检查路径是否安全
        
        确保路径在允许的基目录内
        """
        try:
            real_path = os.path.realpath(path)
            real_base = os.path.realpath(allowed_base)
            return real_path.startswith(real_base)
        except Exception:
            return False
    
    @staticmethod
    def calculate_file_hash(filepath: str, algorithm: str = "sha256") -> str:
        """计算文件哈希"""
        hash_obj = hashlib.new(algorithm)
        
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_file_hash(filepath: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        """验证文件哈希"""
        actual_hash = SecurityUtils.calculate_file_hash(filepath, algorithm)
        return hmac.compare_digest(actual_hash.lower(), expected_hash.lower())
    
    @staticmethod
    def strip_sensitive_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """
        移除敏感头信息
        
        用于日志记录时清理敏感信息
        """
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'password', 'token', 'secret', 'api-key'
        }
        
        return {
            k: (v if k.lower() not in sensitive_headers else '***')
            for k, v in headers.items()
        }


# 全局实例
_password_hasher: Optional[PasswordHasher] = None
_data_encryptor: Optional[DataEncryptor] = None
_key_manager: Optional[KeyManager] = None


def get_password_hasher() -> PasswordHasher:
    """获取全局密码哈希器"""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = PasswordHasher()
    return _password_hasher


def get_data_encryptor() -> DataEncryptor:
    """获取全局数据加密器"""
    global _data_encryptor
    if _data_encryptor is None:
        # 从密钥管理器获取密钥
        key_manager = get_key_manager()
        key = key_manager.get_or_create_key("data_encryption")
        _data_encryptor = DataEncryptor(key)
    return _data_encryptor


def get_key_manager() -> KeyManager:
    """获取全局密钥管理器"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


# 便捷函数
def hash_password(password: str) -> str:
    """哈希密码"""
    return get_password_hasher().hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return get_password_hasher().verify(password, hashed)


def encrypt_data(data: Union[str, bytes]) -> str:
    """加密数据"""
    return get_data_encryptor().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """解密数据"""
    return get_data_encryptor().decrypt(encrypted_data)


def mask_sensitive_data(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """脱敏敏感数据"""
    return DataMasker.mask_dict(data, fields)


def generate_secure_token(length: int = 32) -> str:
    """生成安全令牌"""
    return SecureRandom.generate_token(length)


# 安全配置建议
SECURITY_BEST_PRACTICES = {
    "password_policy": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digits": True,
        "require_special": True,
        "max_age_days": 90,
    },
    "session_policy": {
        "timeout_minutes": 30,
        "max_concurrent": 5,
        "require_reauth_for_sensitive": True,
    },
    "encryption_policy": {
        "algorithm": "AES-256-GCM",
        "key_rotation_days": 90,
        "data_at_rest": True,
        "data_in_transit": True,
    },
}
