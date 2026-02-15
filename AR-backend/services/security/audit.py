#!/usr/bin/env python3
"""
Audit Logging Service
YL-AR-DGN API Security Module
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Iterator
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict
import os


class AuditAction(Enum):
    """审计动作枚举"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    PERMISSION_CHANGE = "permission_change"
    CONFIG_CHANGE = "config_change"
    API_ACCESS = "api_access"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    SESSION_TIMEOUT = "session_timeout"


class AuditStatus(Enum):
    """审计状态枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


@dataclass
class AuditLog:
    """审计日志数据类"""
    timestamp: datetime
    action: AuditAction
    user_id: str
    user_role: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: AuditStatus = AuditStatus.SUCCESS
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status.value,
            "error_message": self.error_message,
            "request_id": self.request_id,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLog':
        """从字典创建"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=AuditAction(data["action"]),
            user_id=data["user_id"],
            user_role=data["user_role"],
            resource_type=data["resource_type"],
            resource_id=data["resource_id"],
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            status=AuditStatus(data["status"]),
            error_message=data.get("error_message"),
            request_id=data.get("request_id"),
            session_id=data.get("session_id")
        )


class AuditLogger:
    """
    审计日志记录器
    
    提供完整的审计日志记录、查询和分析功能。
    
    Attributes:
        log_dir: 日志目录
        max_log_days: 日志保留天数
        current_file: 当前日志文件
    """
    
    def __init__(
        self,
        log_dir: str = "logs/audit",
        max_log_days: int = 30,
        file_prefix: str = "audit"
    ):
        """
        初始化审计日志记录器
        
        Args:
            log_dir: 日志目录
            max_log_days: 日志保留天数
            file_prefix: 日志文件前缀
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_log_days = max_log_days
        self.file_prefix = file_prefix
        
        # 配置日志
        self._setup_logger()
    
    def _setup_logger(self):
        """配置Python日志"""
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复处理器
        if not self.logger.handlers:
            # 文件处理器
            fh = logging.FileHandler(self.log_dir / f"{self.file_prefix}.log")
            fh.setLevel(logging.INFO)
            fh.setFormatter(
                logging.Formatter('%(asctime)s - %(message)s')
            )
            self.logger.addHandler(fh)
    
    def _get_log_file(self, date: datetime = None) -> Path:
        """获取日志文件路径"""
        if date is None:
            date = datetime.utcnow()
        return self.log_dir / f"{self.file_prefix}_{date.strftime('%Y-%m-%d')}.log"
    
    def log(
        self,
        action: AuditAction,
        user_id: str,
        user_role: str,
        resource_type: str,
        resource_id: str,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        status: AuditStatus = AuditStatus.SUCCESS,
        error_message: str = None,
        request_id: str = None,
        session_id: str = None
    ) -> AuditLog:
        """
        记录审计日志
        
        Args:
            action: 审计动作
            user_id: 用户ID
            user_role: 用户角色
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            status: 状态
            error_message: 错误消息
            request_id: 请求ID
            session_id: 会话ID
            
        Returns:
            AuditLog: 创建的审计日志
        """
        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            action=action,
            user_id=user_id,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            request_id=request_id,
            session_id=session_id
        )
        
        # 写入日志文件
        self._write_log(audit_log)
        
        # 发送日志消息
        self.logger.info(json.dumps(audit_log.to_dict(), ensure_ascii=False))
        
        return audit_log
    
    def _write_log(self, audit_log: AuditLog):
        """写入日志文件"""
        log_file = self._get_log_file(audit_log.timestamp)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_log.to_dict(), ensure_ascii=False) + '\n')
    
    def query_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: str = None,
        action: AuditAction = None,
        resource_type: str = None,
        status: AuditStatus = None,
        ip_address: str = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        查询审计日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID过滤
            action: 动作过滤
            resource_type: 资源类型过滤
            status: 状态过滤
            ip_address: IP地址过滤
            limit: 结果数量限制
            offset: 结果偏移量
            
        Returns:
            List[AuditLog]: 审计日志列表
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=1)
        if end_date is None:
            end_date = datetime.utcnow()
        
        logs = []
        current_date = start_date
        
        while current_date <= end_date and len(logs) < limit + offset:
            log_file = self._get_log_file(current_date)
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(logs) >= limit + offset:
                            break
                        
                        try:
                            log_entry = json.loads(line)
                            log_obj = AuditLog.from_dict(log_entry)
                            
                            # 应用过滤器
                            if user_id and log_obj.user_id != user_id:
                                continue
                            if action and log_obj.action != action:
                                continue
                            if resource_type and log_obj.resource_type != resource_type:
                                continue
                            if status and log_obj.status != status:
                                continue
                            if ip_address and log_obj.ip_address != ip_address:
                                continue
                            
                            logs.append(log_obj)
                        except (json.JSONDecodeError, KeyError):
                            continue
            
            current_date += timedelta(days=1)
        
        return logs[offset:limit + offset]
    
    def get_log_stats(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Args:
            hours: 统计时间范围（小时）
            
        Returns:
            Dict: 统计信息
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        logs = self.query_logs(start_date=start_time)
        
        # 统计各动作数量
        action_counts = defaultdict(int)
        status_counts = defaultdict(int)
        user_counts = defaultdict(int)
        ip_counts = defaultdict(int)
        
        for log in logs:
            action_counts[log.action.value] += 1
            status_counts[log.status.value] += 1
            user_counts[log.user_id] += 1
            if log.ip_address:
                ip_counts[log.ip_address] += 1
        
        return {
            "period_hours": hours,
            "total_logs": len(logs),
            "action_distribution": dict(action_counts),
            "status_distribution": dict(status_counts),
            "top_users": dict(sorted(user_counts.items(), key=lambda x: -x[1])[:10]),
            "top_ips": dict(sorted(ip_counts.items(), key=lambda x: -x[1])[:10]),
            "success_rate": (
                status_counts[AuditStatus.SUCCESS.value] / len(logs) * 100 
                if logs else 100
            )
        }
    
    def cleanup_old_logs(self):
        """清理旧的日志文件"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_log_days)
        
        for log_file in self.log_dir.glob(f"{self.file_prefix}_*.log"):
            try:
                file_date = datetime.strptime(
                    log_file.stem.split('_')[-1],
                    '%Y-%m-%d'
                )
                
                if file_date < cutoff_date:
                    log_file.unlink()
            except (ValueError, OSError):
                continue
    
    def export_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """
        导出日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            format: 导出格式 (json, csv)
            
        Returns:
            str: 导出的日志内容
        """
        logs = self.query_logs(start_date=start_date, end_date=end_date)
        
        if format == "csv":
            lines = ["timestamp,action,user_id,user_role,resource_type,resource_id,status,ip_address"]
            for log in logs:
                lines.append(
                    f"{log.timestamp.isoformat()},"
                    f"{log.action.value},"
                    f"{log.user_id},"
                    f"{log.user_role},"
                    f"{log.resource_type},"
                    f"{log.resource_id},"
                    f"{log.status.value},"
                    f"{log.ip_address or ''}"
                )
            return '\n'.join(lines)
        else:
            return json.dumps(
                [log.to_dict() for log in logs],
                indent=2,
                ensure_ascii=False
            )


# 便捷函数
def create_audit_logger(
    log_dir: str = "logs/audit",
    max_log_days: int = 30
) -> AuditLogger:
    """创建审计日志记录器实例"""
    return AuditLogger(log_dir=log_dir, max_log_days=max_log_days)


# 装饰器辅助函数
def audit_decorator(
    resource_type: str,
    action: AuditAction
):
    """
    审计装饰器工厂
    
    Args:
        resource_type: 资源类型
        action: 审计动作
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从kwargs或上下文中获取user_id和user_role
            user_id = kwargs.get('user_id', 'system')
            user_role = kwargs.get('user_role', 'system')
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录审计日志
            logger = create_audit_logger()
            logger.log(
                action=action,
                user_id=user_id,
                user_role=user_role,
                resource_type=resource_type,
                resource_id=str(result.get('id', 'unknown')) if isinstance(result, dict) else 'unknown',
                details={"args": str(args), "kwargs": str(kwargs)},
                status=AuditStatus.SUCCESS
            )
            
            return result
        return wrapper
    return decorator
