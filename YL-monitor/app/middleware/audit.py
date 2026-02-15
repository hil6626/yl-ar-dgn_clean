"""
审计日志中间件

功能:
- 操作日志记录
- 异常访问监控
- 敏感操作标记
- 审计数据存储

作者: AI Assistant
版本: 1.0.0
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AuditLevel(str, Enum):
    """审计级别"""
    DEBUG = "debug"       # 调试信息
    INFO = "info"         # 一般信息
    WARNING = "warning"   # 警告
    ERROR = "error"       # 错误
    CRITICAL = "critical" # 严重
    SECURITY = "security" # 安全相关


class ActionType(str, Enum):
    """操作类型"""
    CREATE = "create"      # 创建
    READ = "read"         # 读取
    UPDATE = "update"     # 更新
    DELETE = "delete"     # 删除
    LOGIN = "login"       # 登录
    LOGOUT = "logout"     # 注销
    EXPORT = "export"     # 导出
    IMPORT = "import"     # 导入
    EXECUTE = "execute"   # 执行
    CONFIG = "config"     # 配置变更
    ACCESS = "access"     # 访问


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    level: AuditLevel = AuditLevel.INFO
    action: ActionType = ActionType.ACCESS
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_size: Optional[int] = None
    execution_time: Optional[float] = None  # 毫秒
    error_message: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


class AuditStorage:
    """
    审计存储基类
    
    定义审计日志存储接口
    """
    
    async def store(self, entry: AuditLogEntry) -> bool:
        """存储审计日志"""
        raise NotImplementedError
    
    async def query(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        user_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """查询审计日志"""
        raise NotImplementedError
    
    async def count(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        user_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        level: Optional[AuditLevel] = None
    ) -> int:
        """统计审计日志数量"""
        raise NotImplementedError


class MemoryAuditStorage(AuditStorage):
    """
    内存审计存储
    
    用于开发和测试环境
    """
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self._entries: List[AuditLogEntry] = []
    
    async def store(self, entry: AuditLogEntry) -> bool:
        """存储审计日志"""
        self._entries.append(entry)
        
        # 限制大小
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        
        return True
    
    async def query(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        user_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """查询审计日志"""
        results = self._entries
        
        # 过滤
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if action:
            results = [e for e in results if e.action == action]
        if level:
            results = [e for e in results if e.level == level]
        
        # 排序(时间倒序)
        results.sort(key=lambda e: e.timestamp, reverse=True)
        
        # 分页
        return results[offset:offset + limit]
    
    async def count(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        user_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        level: Optional[AuditLevel] = None
    ) -> int:
        """统计数量"""
        entries = await self.query(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            action=action,
            level=level,
            limit=999999999
        )
        return len(entries)
    
    def clear(self):
        """清空存储"""
        self._entries = []


class FileAuditStorage(AuditStorage):
    """
    文件审计存储
    
    将审计日志写入文件
    """
    
    def __init__(self, filepath: str = "logs/audit.log"):
        self.filepath = filepath
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    async def store(self, entry: AuditLogEntry) -> bool:
        """存储审计日志"""
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
            return True
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")
            return False
    
    async def query(self, **kwargs) -> List[AuditLogEntry]:
        """查询(文件存储不支持高效查询)"""
        # 简化实现，实际应使用数据库
        return []
    
    async def count(self, **kwargs) -> int:
        """统计(文件存储不支持高效统计)"""
        return 0


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计中间件
    
    自动记录所有请求和响应
    """
    
    # 敏感字段，需要脱敏
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'apikey',
        'authorization', 'cookie', 'credit_card', 'ssn'
    }
    
    # 敏感路径模式
    SENSITIVE_PATHS = [
        r'/auth/login',
        r'/auth/register',
        r'/auth/reset-password',
        r'/api/users/\w+/password',
    ]
    
    def __init__(
        self,
        app: ASGIApp,
        storage: Optional[AuditStorage] = None,
        exclude_paths: Optional[Set[str]] = None,
        log_request_body: bool = False,
        log_response_body: bool = False
    ):
        super().__init__(app)
        self.storage = storage or MemoryAuditStorage()
        self.exclude_paths = exclude_paths or {"/health", "/metrics", "/static"}
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        
        import re
        self.sensitive_patterns = [re.compile(p) for p in self.SENSITIVE_PATHS]
        
        logger.info("审计中间件已初始化")
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        start_time = time.time()
        
        # 检查是否排除
        if self._is_excluded(request.url.path):
            return await call_next(request)
        
        # 创建审计条目
        entry = AuditLogEntry(
            request_method=request.method,
            request_path=str(request.url),
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        
        # 获取用户信息(如果已认证)
        user = getattr(request.state, "user", None)
        if user:
            entry.user_id = getattr(user, "user_id", None)
            entry.username = getattr(user, "username", None)
        
        # 记录请求参数
        entry.request_params = dict(request.query_params)
        
        # 记录请求体(如果启用)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    entry.request_body = self._sanitize_body(body.decode())
            except:
                pass
        
        # 执行请求
        try:
            response = await call_next(request)
            
            # 记录响应
            entry.response_status = response.status_code
            entry.response_size = int(response.headers.get("content-length", 0))
            entry.success = 200 <= response.status_code < 400
            
            # 确定操作类型
            entry.action = self._determine_action(request.method, request.url.path)
            
            # 检查是否为敏感操作
            if self._is_sensitive_path(request.url.path):
                entry.level = AuditLevel.SECURITY
            
            # 检查是否为错误
            if response.status_code >= 400:
                entry.level = AuditLevel.ERROR if response.status_code < 500 else AuditLevel.CRITICAL
                entry.success = False
            
        except Exception as e:
            entry.level = AuditLevel.ERROR
            entry.error_message = str(e)
            entry.success = False
            raise
        finally:
            # 计算执行时间
            entry.execution_time = (time.time() - start_time) * 1000
            
            # 存储审计日志
            await self.storage.store(entry)
            
            # 记录到日志
            self._log_entry(entry)
        
        return response
    
    def _is_excluded(self, path: str) -> bool:
        """检查路径是否排除"""
        for excluded in self.exclude_paths:
            if path.startswith(excluded):
                return True
        return False
    
    def _is_sensitive_path(self, path: str) -> bool:
        """检查是否为敏感路径"""
        for pattern in self.sensitive_patterns:
            if pattern.match(path):
                return True
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 直接连接
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _sanitize_body(self, body: str) -> str:
        """清理请求体中的敏感信息"""
        try:
            data = json.loads(body)
            sanitized = self._sanitize_dict(data)
            return json.dumps(sanitized)
        except:
            # 不是JSON，返回截断的文本
            if len(body) > 1000:
                return body[:1000] + "... [truncated]"
            return body
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理字典中的敏感字段"""
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELDS):
                result[key] = "***"
            elif isinstance(value, dict):
                result[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        return result
    
    def _determine_action(self, method: str, path: str) -> ActionType:
        """确定操作类型"""
        method_actions = {
            "GET": ActionType.READ,
            "POST": ActionType.CREATE,
            "PUT": ActionType.UPDATE,
            "PATCH": ActionType.UPDATE,
            "DELETE": ActionType.DELETE,
        }
        
        # 特殊路径判断
        if "login" in path.lower():
            return ActionType.LOGIN
        if "logout" in path.lower():
            return ActionType.LOGOUT
        if "export" in path.lower():
            return ActionType.EXPORT
        if "import" in path.lower():
            return ActionType.IMPORT
        if "execute" in path.lower() or "run" in path.lower():
            return ActionType.EXECUTE
        
        return method_actions.get(method, ActionType.ACCESS)
    
    def _log_entry(self, entry: AuditLogEntry):
        """记录审计日志到日志系统"""
        message = (
            f"[AUDIT] {entry.action.value} {entry.request_method} {entry.request_path} "
            f"user={entry.username} status={entry.response_status} "
            f"time={entry.execution_time:.2f}ms"
        )
        
        if entry.level == AuditLevel.ERROR:
            logger.error(message)
        elif entry.level == AuditLevel.WARNING:
            logger.warning(message)
        elif entry.level == AuditLevel.SECURITY:
            logger.info(f"{message} [SECURITY]")
        else:
            logger.debug(message)


class AuditAnalyzer:
    """
    审计分析器
    
    分析审计日志，检测异常行为
    """
    
    def __init__(self, storage: AuditStorage):
        self.storage = storage
    
    async def detect_anomalies(
        self,
        time_window: float = 3600,  # 1小时
        threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        检测异常行为
        
        检测指标:
        - 频繁登录失败
        - 大量数据导出
        - 异常时间访问
        - 敏感操作集中
        """
        anomalies = []
        current_time = time.time()
        start_time = current_time - time_window
        
        # 1. 检测频繁登录失败
        failed_logins = await self.storage.query(
            start_time=start_time,
            action=ActionType.LOGIN,
            level=AuditLevel.ERROR,
            limit=999999
        )
        
        # 按IP分组统计
        ip_failures: Dict[str, int] = {}
        for entry in failed_logins:
            ip = entry.ip_address or "unknown"
            ip_failures[ip] = ip_failures.get(ip, 0) + 1
        
        for ip, count in ip_failures.items():
            if count >= threshold:
                anomalies.append({
                    "type": "brute_force",
                    "severity": "high",
                    "description": f"IP {ip} 在1小时内登录失败 {count} 次",
                    "ip": ip,
                    "count": count,
                    "recommendation": "建议封禁该IP或启用验证码"
                })
        
        # 2. 检测大量数据导出
        exports = await self.storage.query(
            start_time=start_time,
            action=ActionType.EXPORT,
            limit=999999
        )
        
        if len(exports) > threshold * 2:
            anomalies.append({
                "type": "mass_export",
                "severity": "medium",
                "description": f"1小时内发生 {len(exports)} 次数据导出操作",
                "count": len(exports),
                "recommendation": "建议审查导出操作是否合规"
            })
        
        # 3. 检测异常时间访问(凌晨2-5点)
        night_access = []
        for entry in await self.storage.query(start_time=start_time, limit=999999):
            hour = datetime.fromtimestamp(entry.timestamp).hour
            if 2 <= hour <= 5:
                night_access.append(entry)
        
        if len(night_access) > threshold:
            anomalies.append({
                "type": "night_access",
                "severity": "low",
                "description": f"凌晨时段(2-5点)发生 {len(night_access)} 次访问",
                "count": len(night_access),
                "recommendation": "建议关注夜间操作"
            })
        
        return anomalies
    
    async def generate_report(
        self,
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """
        生成审计报告
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
        """
        # 统计总数
        total_count = await self.storage.count(start_time=start_time, end_time=end_time)
        
        # 按操作类型统计
        action_stats = {}
        for action in ActionType:
            count = await self.storage.count(
                start_time=start_time,
                end_time=end_time,
                action=action
            )
            if count > 0:
                action_stats[action.value] = count
        
        # 按级别统计
        level_stats = {}
        for level in AuditLevel:
            count = await self.storage.count(
                start_time=start_time,
                end_time=end_time,
                level=level
            )
            if count > 0:
                level_stats[level.value] = count
        
        # 活跃用户
        entries = await self.storage.query(
            start_time=start_time,
            end_time=end_time,
            limit=999999
        )
        
        active_users = set()
        for entry in entries:
            if entry.user_id:
                active_users.add(entry.user_id)
        
        # 异常检测
        anomalies = await self.detect_anomalies(end_time - start_time)
        
        return {
            "period": {
                "start": datetime.fromtimestamp(start_time).isoformat(),
                "end": datetime.fromtimestamp(end_time).isoformat(),
            },
            "summary": {
                "total_operations": total_count,
                "active_users": len(active_users),
                "success_rate": self._calculate_success_rate(entries),
            },
            "action_statistics": action_stats,
            "level_statistics": level_stats,
            "anomalies": anomalies,
            "recommendations": self._generate_recommendations(anomalies)
        }
    
    def _calculate_success_rate(self, entries: List[AuditLogEntry]) -> float:
        """计算成功率"""
        if not entries:
            return 100.0
        
        success_count = sum(1 for e in entries if e.success)
        return (success_count / len(entries)) * 100
    
    def _generate_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for anomaly in anomalies:
            recommendations.append(anomaly["recommendation"])
        
        if not recommendations:
            recommendations.append("当前未发现明显安全问题，继续保持监控")
        
        return recommendations


# 全局审计存储实例
_audit_storage: Optional[AuditStorage] = None


def get_audit_storage() -> AuditStorage:
    """获取全局审计存储"""
    global _audit_storage
    if _audit_storage is None:
        _audit_storage = MemoryAuditStorage()
    return _audit_storage


def set_audit_storage(storage: AuditStorage):
    """设置全局审计存储"""
    global _audit_storage
    _audit_storage = storage


# 便捷函数
async def log_security_event(
    action: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """记录安全事件"""
    storage = get_audit_storage()
    
    entry = AuditLogEntry(
        level=AuditLevel.SECURITY,
        action=ActionType(action) if action in [a.value for a in ActionType] else ActionType.ACCESS,
        user_id=user_id,
        metadata=details or {}
    )
    
    await storage.store(entry)
    logger.warning(f"[SECURITY] {action} user={user_id} details={details}")


# 审计配置建议
AUDIT_BEST_PRACTICES = {
    "retention_policy": {
        "debug_logs": "7_days",
        "info_logs": "30_days",
        "security_logs": "1_year",
        "compliance_logs": "7_years"
    },
    "monitoring_rules": [
        {"name": "brute_force", "condition": "5_failed_logins_in_10_minutes", "action": "alert_and_block"},
        {"name": "privilege_escalation", "condition": "permission_change_by_non_admin", "action": "alert"},
        {"name": "data_exfiltration", "condition": "large_export_by_non_regular_user", "action": "alert"},
        {"name": "off_hours_access", "condition": "admin_access_between_2am_5am", "action": "log_and_review"},
    ],
    "compliance_requirements": {
        "gdpr": ["data_access_logging", "right_to_be_forgotten"],
        "sox": ["financial_data_change_logging", "admin_action_logging"],
        "hipaa": ["phi_access_logging", "failed_access_alerting"],
    }
}
