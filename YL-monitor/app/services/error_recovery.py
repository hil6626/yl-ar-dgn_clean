#!/usr/bin/env python3
"""
【文件功能】
错误恢复服务，提供脚本失败和系统错误的恢复策略

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现错误恢复核心功能
- v1.1.0 (2026-02-09): 增强版，集成脚本引擎事件监听、堆栈分析

【依赖说明】
- 标准库: asyncio, json, logging, os, time, traceback, typing, datetime, pathlib, re
- 第三方库: 无
- 内部模块: app.models, app.utils

【使用示例】
```python
from app.services.error_recovery import error_recovery_service

# 处理脚本失败
result = await error_recovery_service.handle_script_failure(
    execution_id="exec-001",
    error=Exception("连接超时"),
    context={"script_id": "script-001", "retry_count": 0}
)

# 处理系统错误
result = await error_recovery_service.handle_system_error(
    error_type="memory_exhaustion",
    context={"service": "dashboard", "memory_usage": 95}
)

# 绑定脚本引擎（增强功能）
await error_recovery_service.register_script_engine(script_engine)
```
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import re
from typing import Dict, Any, List, Optional, Callable, Union, TYPE_CHECKING
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

# 避免循环导入
if TYPE_CHECKING:
    from app.services.script_engine import ScriptExecutionEngine, ScriptExecution


class RecoveryStrategy(Enum):
    """【恢复策略】错误恢复策略类型"""
    RETRY = "retry"                    # 【重试】重新执行
    FALLBACK = "fallback"              # 【回退】使用备用方案
    SKIP = "skip"                      # 【跳过】跳过当前任务
    ROLLBACK = "rollback"              # 【回滚】回滚到之前状态
    ESCALATE = "escalate"              # 【升级】升级处理
    IGNORE = "ignore"                  # 【忽略】忽略错误继续


class ErrorSeverity(Enum):
    """【错误严重级别】错误严重程度分类"""
    CRITICAL = "critical"              # 【紧急】系统级故障
    HIGH = "high"                      # 【高】严重影响功能
    MEDIUM = "medium"                  # 【中】部分功能受影响
    LOW = "low"                        # 【低】轻微影响
    INFO = "info"                      # 【信息】仅记录


class RecoveryLevel(Enum):
    """【恢复级别】错误恢复级别分类"""
    AUTO = "auto"                      # 【自动】自动恢复
    MANUAL = "manual"                  # 【手动】需要人工干预
    ESCALATE = "escalate"              # 【升级】升级到高级别处理
    IGNORE = "ignore"                  # 【忽略】忽略不处理


@dataclass
class ErrorRecord:
    """【错误记录】错误信息记录"""
    error_id: str                      # 【错误ID】唯一标识
    error_type: str                    # 【错误类型】错误分类
    error_message: str                 # 【错误消息】详细描述
    severity: ErrorSeverity            # 【严重级别】错误严重程度
    timestamp: datetime                # 【时间戳】发生时间
    context: Dict[str, Any]            # 【上下文】错误环境信息
    stack_trace: Optional[str]         # 【堆栈跟踪】错误堆栈
    recovery_attempts: int = 0         # 【恢复尝试】已尝试次数
    recovered: bool = False          # 【已恢复】是否已恢复
    recovery_strategy: Optional[str] = None  # 【恢复策略】使用的策略


@dataclass
class RecoveryResult:
    """【恢复结果】错误恢复结果"""
    success: bool                      # 【成功】是否恢复成功
    strategy: RecoveryStrategy         # 【策略】使用的恢复策略
    message: str                       # 【消息】结果描述
    details: Dict[str, Any]            # 【详情】详细信息
    timestamp: datetime                # 【时间戳】恢复时间


@dataclass
class Checkpoint:
    """【检查点】状态检查点"""
    checkpoint_id: str                 # 【检查点ID】唯一标识
    timestamp: datetime                # 【时间戳】创建时间
    state_data: Dict[str, Any]         # 【状态数据】保存的状态
    metadata: Dict[str, Any]           # 【元数据】附加信息


@dataclass
class ErrorContext:
    """错误上下文（增强版）"""
    error_id: str
    error_type: str
    error_message: str
    component: str
    operation: str
    timestamp: datetime
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_attempts: int = 0


class RecoveryStrategyBase:
    """恢复策略基类"""

    def __init__(
        self,
        name: str,
        description: str,
        max_attempts: int = 3,
        backoff_factor: float = 2.0
    ):
        self.name = name
        self.description = description
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor

    def can_handle(self, error_context: ErrorContext) -> bool:
        """判断是否适用此策略（子类实现）"""
        raise NotImplementedError

    async def execute_recovery(
        self,
        error_context: ErrorContext
    ) -> RecoveryResult:
        """执行恢复（子类实现）"""
        raise NotImplementedError


class ScriptTimeoutRecoveryStrategy(RecoveryStrategyBase):
    """脚本超时恢复策略"""

    def __init__(self):
        super().__init__(
            name="script_timeout_recovery",
            description="脚本执行超时自动恢复",
            max_attempts=3,
            backoff_factor=2.0,
        )

    def can_handle(self, error_context: ErrorContext) -> bool:
        """判断是否适用此策略"""
        return (
            error_context.error_type == "TIMEOUT" or
            "timeout" in error_context.error_message.lower()
        )

    async def execute_recovery(
        self,
        error_context: ErrorContext
    ) -> RecoveryResult:
        """执行超时恢复"""
        # 此方法需要在注册引擎后使用
        return RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.RETRY,
            message="超时恢复需要脚本引擎实例",
            details={"requires_engine": True},
            timestamp=datetime.now()
        )


class ResourceExhaustedRecoveryStrategy(RecoveryStrategyBase):
    """资源不足恢复策略"""

    def __init__(self):
        super().__init__(
            name="resource_exhausted_recovery",
            description="资源不足自动恢复",
            max_attempts=3,
        )

    def can_handle(self, error_context: ErrorContext) -> bool:
        """判断是否适用此策略"""
        error_msg = error_context.error_message.lower()
        return any(kw in error_msg for kw in [
            "memory", "cpu", "disk", "resource",
            "quota", "limit", "exhausted"
        ])

    def _analyze_resource_type(
        self,
        error_message: str,
        stack_trace: Optional[str]
    ) -> str:
        """分析错误信息确定资源类型"""
        keywords = {
            "memory": ["memory", "malloc", "oom", "out of memory",
                       "cannot allocate", "MemoryError"],
            "cpu": ["cpu", "throttle", "quota", "CPULimit"],
            "disk": ["disk", "space", "no space left", "write error",
                     "DiskFull", "ENOSPC"],
            "fd": ["file descriptor", "too many open files", "EMFILE"],
        }

        text = (error_message + " " + (stack_trace or "")).lower()

        for resource_type, words in keywords.items():
            if any(word in text for word in words):
                return resource_type

        return "unknown"

    async def execute_recovery(
        self,
        error_context: ErrorContext
    ) -> RecoveryResult:
        """执行资源恢复"""
        resource_type = self._analyze_resource_type(
            error_context.error_message,
            error_context.stack_trace
        )

        suggestions = {
            "memory": [
                "执行 optimize/19_cache_cleanup.py",
                "检查内存泄漏（optimize/35_memory_leak_detect_alert.py）",
            ],
            "disk": [
                "执行 optimize/17_disk_junk_cleanup.py",
                "执行 maintenance/40_history_data_compress_archive.py",
            ],
            "cpu": [
                "检查CPU密集型任务",
                "考虑增加计算资源或优化算法",
            ],
            "fd": [
                "检查文件描述符泄漏",
                "重启服务释放文件句柄",
            ],
        }

        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.FALLBACK,
            message=f"检测到{resource_type}资源不足，建议执行优化操作",
            details={
                "resource_type": resource_type,
                "suggestions": suggestions.get(resource_type,
                    ["查看详细日志，联系管理员"]),
            },
            timestamp=datetime.now()
        )


class StackTraceAnalyzer:
    """堆栈跟踪分析器"""

    # 已知错误模式
    ERROR_PATTERNS = {
        "file_not_found": [
            r"FileNotFoundError",
            r"No such file or directory",
            r"ENOENT",
        ],
        "permission_denied": [
            r"PermissionError",
            r"Permission denied",
            r"EACCES",
            r"EPERM",
        ],
        "network_error": [
            r"ConnectionError",
            r"TimeoutError",
            r"Network is unreachable",
            r"ConnectionRefused",
        ],
        "dependency_missing": [
            r"ModuleNotFoundError",
            r"ImportError",
            r"No module named",
        ],
        "config_error": [
            r"KeyError",
            r"ConfigError",
            r"configuration",
            r"ValidationError",
        ],
        "syntax_error": [
            r"SyntaxError",
            r"IndentationError",
        ],
    }

    def analyze(self, stack_trace: Optional[str]) -> Dict[str, Any]:
        """分析堆栈跟踪"""
        if not stack_trace:
            return {"error": "no_stack_trace"}

        result = {
            "error_type": None,
            "root_cause": None,
            "affected_files": [],
            "suggestions": [],
        }

        # 匹配错误模式
        for error_type, patterns in self.ERROR_PATTERNS.items():
            if any(
                re.search(p, stack_trace, re.IGNORECASE)
                for p in patterns
            ):
                result["error_type"] = error_type
                result["suggestions"] = self._get_suggestions(error_type)
                break

        # 提取文件路径
        file_pattern = r'File "([^"]+)"'
        result["affected_files"] = list(set(re.findall(file_pattern, stack_trace)))

        # 提取最后一行作为根因
        lines = [l.strip() for l in stack_trace.strip().split('\n') if l.strip()]
        if lines:
            result["root_cause"] = lines[-1]

        return result

    def _get_suggestions(self, error_type: str) -> List[str]:
        """根据错误类型获取建议"""
        suggestions = {
            "file_not_found": [
                "检查脚本路径是否正确",
                "验证文件权限",
                "执行 maintenance/30_app_config_check_repair.py",
            ],
            "permission_denied": [
                "检查脚本执行权限",
                "验证运行用户权限",
                "检查 SELinux/AppArmor 配置",
            ],
            "network_error": [
                "检查网络连接",
                "验证防火墙规则",
                "检查 DNS 解析",
            ],
            "dependency_missing": [
                "安装缺失的依赖包",
                "检查 Python 环境",
                "执行 maintenance/22_system_update_patch_check.py",
            ],
            "config_error": [
                "检查配置文件格式",
                "验证配置项完整性",
                "执行 maintenance/52_auto_config_anomaly_fix.py",
            ],
            "syntax_error": [
                "检查脚本语法错误",
                "验证 Python 版本兼容性",
            ],
        }
        return suggestions.get(error_type, ["查看详细日志，联系管理员"])


class ErrorRecoveryService:
    """
    【类职责】
    错误恢复服务，提供全面的错误处理和恢复机制
    
    【主要功能】
    1. 脚本失败恢复: 处理脚本执行失败，支持重试、回退等策略
    2. 系统错误恢复: 处理系统级错误，如内存耗尽、连接丢失等
    3. 状态检查点: 创建和恢复状态检查点
    4. 错误记录管理: 记录和分析错误历史
    
    【属性说明】
    - _error_history: 错误历史记录列表
    - _checkpoints: 检查点存储
    - _recovery_handlers: 恢复处理器映射
    - _max_history_size: 最大历史记录数
    
    【使用示例】
    ```python
    service = ErrorRecoveryService()
    
    # 注册自定义恢复处理器
    service.register_recovery_handler(
        "connection_error",
        custom_recovery_handler
    )
    
    # 处理错误
    result = await service.handle_error(
        error=ConnectionError("超时"),
        context={"operation": "data_sync"}
    )
    ```
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        【初始化】创建错误恢复服务实例

        【参数说明】
        - max_history_size (int): 最大历史记录数，默认1000
        """
        self._error_history: List[ErrorRecord] = []
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._recovery_handlers: Dict[str, Callable] = {}
        self._max_history_size = max_history_size
        self._logger = logging.getLogger(__name__)

        # 【增强功能：脚本引擎集成】
        self._script_engine = None  # 脚本引擎实例
        self._active_recoveries: Dict[str, Any] = {}  # 活跃恢复任务

        # 【增强功能：恢复策略】
        self._recovery_strategies: List[RecoveryStrategyBase] = [
            ScriptTimeoutRecoveryStrategy(),
            ResourceExhaustedRecoveryStrategy(),
        ]

        # 【注册默认处理器】
        self._register_default_handlers()

    async def register_script_engine(self, engine) -> None:
        """
        【注册脚本引擎】建立与脚本引擎的事件监听

        【参数说明】
            engine: 脚本执行引擎实例
        """
        self._script_engine = engine

        # 注册事件回调
        if hasattr(engine, 'register_callback'):
            engine.register_callback('on_fail', self._on_script_failed)
            engine.register_callback('on_complete', self._on_script_completed)

        self._logger.info(
            f"错误恢复服务已绑定到脚本引擎: {id(engine)}"
        )

    async def _on_script_failed(self, execution) -> None:
        """
        【脚本失败回调】脚本执行失败时触发自动恢复流程

        【参数说明】
            execution: ScriptExecution 执行记录对象
        """
        # 构建错误上下文
        error_context = ErrorContext(
            error_id=hashlib.md5(
                f"{execution.id}:{time.time()}".encode()
            ).hexdigest()[:12],
            error_type=execution.status.name if hasattr(execution.status, 'name') else "FAILED",
            error_message=execution.error or "脚本执行失败",
            component="script_engine",
            operation=f"execute:{execution.script_id}",
            timestamp=datetime.now(),
            context={
                "execution_id": execution.id,
                "script_id": execution.script_id,
                "script_name": execution.script_name,
                "script_path": execution.script_path,
                "params": execution.params,
                "duration_ms": execution.duration_ms,
                "retry_count": execution.retry_count,
                "call_chain": execution.call_chain if hasattr(execution, 'call_chain') else [],
            },
            stack_trace=execution.stack_trace if hasattr(execution, 'stack_trace') else None,
            recovery_attempts=execution.retry_count,
        )

        # 触发恢复
        await self.handle_error(error_context)

    async def _on_script_completed(self, execution) -> None:
        """
        【脚本完成回调】脚本执行完成时清理恢复状态

        【参数说明】
            execution: ScriptExecution 执行记录对象
        """
        # 如果之前有恢复记录，标记为已解决
        if execution.id in self._active_recoveries:
            recovery = self._active_recoveries[execution.id]
            recovery["status"] = "resolved"
            recovery["resolved_at"] = datetime.now()
            self._logger.info(
                f"脚本 {execution.script_id} 恢复成功"
            )

    async def handle_error(
        self,
        error_context: ErrorContext
    ) -> RecoveryResult:
        """
        【处理错误】增强版错误处理，集成堆栈分析

        【参数说明】
            error_context: ErrorContext 错误上下文对象

        【返回值】
            RecoveryResult: 恢复结果
        """
        # 【堆栈分析】
        stack_analysis = None
        if error_context.stack_trace:
            analyzer = StackTraceAnalyzer()
            stack_analysis = analyzer.analyze(error_context.stack_trace)
            error_context.context["stack_analysis"] = stack_analysis
            self._logger.info(
                f"堆栈分析结果: {stack_analysis.get('error_type', 'unknown')}"
            )

        # 【查找适用的恢复策略】
        strategy = self._find_strategy(error_context)

        if not strategy:
            # 无适用策略，但提供分析建议
            if stack_analysis:
                return RecoveryResult(
                    success=False,
                    strategy=RecoveryStrategy.ESCALATE,
                    message=f"无法自动恢复，分析建议: {', '.join(stack_analysis.get('suggestions', []))}",
                    details={
                        "error_type": error_context.error_type,
                        "stack_analysis": stack_analysis,
                    },
                    timestamp=datetime.now()
                )

            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ESCALATE,
                message="无适用的恢复策略",
                details={"error_context": error_context.context},
                timestamp=datetime.now()
            )

        # 【执行恢复】
        result = await strategy.execute_recovery(error_context)

        # 【记录恢复尝试】
        self._active_recoveries[error_context.error_id] = {
            "strategy": strategy.name,
            "result": result,
            "status": "pending",
            "created_at": datetime.now(),
        }

        return result

    def _find_strategy(self, error_context: ErrorContext) -> Optional[RecoveryStrategyBase]:
        """查找适用于错误上下文的恢复策略"""
        for strategy in self._recovery_strategies:
            if strategy.can_handle(error_context):
                # 检查是否超过最大尝试次数
                if error_context.recovery_attempts < strategy.max_attempts:
                    return strategy
        return None
    
    def _register_default_handlers(self) -> None:
        """【注册默认处理器】注册内置的错误恢复处理器"""
        self._recovery_handlers.update({
            "timeout_error": self._handle_timeout_error,
            "connection_error": self._handle_connection_error,
            "memory_error": self._handle_memory_error,
            "disk_full_error": self._handle_disk_full_error,
            "permission_error": self._handle_permission_error,
            "script_failure": self._handle_script_failure,
            "system_overload": self._handle_system_overload,
        })
    
    async def handle_script_failure(
        self,
        execution_id: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """
        【处理脚本失败】处理脚本执行失败
        
        【参数说明】
        - execution_id (str): 执行ID
        - error (Exception): 错误异常
        - context (Dict[str, Any]): 执行上下文，包含：
            - script_id: 脚本ID
            - retry_count: 已重试次数
            - params: 执行参数
        
        【返回值】
        - RecoveryResult: 恢复结果
        
        【使用示例】
        ```python
        result = await service.handle_script_failure(
            execution_id="exec-001",
            error=TimeoutError("执行超时"),
            context={"script_id": "script-001", "retry_count": 0}
        )
        ```
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 【记录错误】
        error_record = self._create_error_record(
            error_type="script_failure",
            error_message=error_message,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self._add_error_record(error_record)
        
        # 【确定恢复策略】
        retry_count = context.get("retry_count", 0)
        max_retries = context.get("max_retries", 3)
        
        if retry_count < max_retries:
            # 【策略：重试】
            strategy = RecoveryStrategy.RETRY
            delay = self._calculate_backoff_delay(retry_count)
            
            result = RecoveryResult(
                success=True,
                strategy=strategy,
                message=f"将在{delay}秒后重试（第{retry_count + 1}次）",
                details={
                    "execution_id": execution_id,
                    "retry_delay": delay,
                    "retry_count": retry_count + 1,
                    "max_retries": max_retries
                },
                timestamp=datetime.now()
            )
        else:
            # 【策略：回退或升级】
            if context.get("fallback_available", False):
                strategy = RecoveryStrategy.FALLBACK
                result = RecoveryResult(
                    success=True,
                    strategy=strategy,
                    message="切换到备用方案执行",
                    details={
                        "execution_id": execution_id,
                        "fallback_script": context.get("fallback_script")
                    },
                    timestamp=datetime.now()
                )
            else:
                strategy = RecoveryStrategy.ESCALATE
                result = RecoveryResult(
                    success=False,
                    strategy=strategy,
                    message="超过最大重试次数，需要人工干预",
                    details={
                        "execution_id": execution_id,
                        "error_history": self._get_error_history_for_execution(execution_id)
                    },
                    timestamp=datetime.now()
                )
        
        # 【更新错误记录】
        error_record.recovery_attempts = retry_count + 1
        error_record.recovered = result.success
        error_record.recovery_strategy = strategy.value
        
        self._logger.info(
            f"【脚本失败处理】执行ID: {execution_id}, "
            f"策略: {strategy.value}, 结果: {result.success}"
        )
        
        return result
    
    async def handle_system_error(
        self,
        error_type: str,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """
        【处理系统错误】处理系统级错误
        
        【参数说明】
        - error_type (str): 错误类型，如：
            - memory_exhaustion: 内存耗尽
            - disk_full: 磁盘已满
            - connection_lost: 连接丢失
            - service_unavailable: 服务不可用
        - context (Dict[str, Any]): 错误上下文
        
        【返回值】
        - RecoveryResult: 恢复结果
        
        【使用示例】
        ```python
        result = await service.handle_system_error(
            error_type="memory_exhaustion",
            context={"memory_usage": 95, "service": "dashboard"}
        )
        ```
        """
        # 【记录错误】
        severity = self._determine_severity(error_type, context)
        error_record = self._create_error_record(
            error_type=error_type,
            error_message=f"系统错误: {error_type}",
            severity=severity,
            context=context
        )
        self._add_error_record(error_record)
        
        # 【查找处理器】
        handler = self._recovery_handlers.get(error_type)
        
        if handler:
            # 【使用专用处理器】
            result = await handler(context)
        else:
            # 【使用通用处理】
            result = await self._handle_generic_system_error(error_type, context)
        
        # 【更新错误记录】
        error_record.recovered = result.success
        error_record.recovery_strategy = result.strategy.value
        
        self._logger.info(
            f"【系统错误处理】类型: {error_type}, "
            f"策略: {result.strategy.value}, 结果: {result.success}"
        )
        
        return result
    
    async def create_checkpoint(
        self,
        checkpoint_id: str,
        state_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """
        【创建检查点】保存当前状态
        
        【参数说明】
        - checkpoint_id (str): 检查点ID
        - state_data (Dict[str, Any]): 要保存的状态数据
        - metadata (Dict[str, Any], 可选): 附加元数据
        
        【返回值】
        - Checkpoint: 创建的检查点
        
        【使用示例】
        ```python
        checkpoint = await service.create_checkpoint(
            checkpoint_id="dag-exec-001",
            state_data={"completed_nodes": ["A", "B"], "current_node": "C"},
            metadata={"dag_id": "dag-001", "execution_id": "exec-001"}
        )
        ```
        """
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            state_data=state_data,
            metadata=metadata or {}
        )
        
        self._checkpoints[checkpoint_id] = checkpoint
        
        # 【持久化检查点】
        await self._persist_checkpoint(checkpoint)
        
        self._logger.info(f"【检查点创建】ID: {checkpoint_id}")
        
        return checkpoint
    
    async def restore_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        【从检查点恢复】恢复到之前保存的状态
        
        【参数说明】
        - checkpoint_id (str): 检查点ID
        
        【返回值】
        - Optional[Dict[str, Any]]: 恢复的状态数据，如果不存在返回None
        
        【使用示例】
        ```python
        state = await service.restore_from_checkpoint("dag-exec-001")
        if state:
            print(f"恢复到检查点，已完成节点: {state['completed_nodes']}")
        ```
        """
        # 【从内存获取】
        checkpoint = self._checkpoints.get(checkpoint_id)
        
        if not checkpoint:
            # 【从磁盘加载】
            checkpoint = await self._load_checkpoint(checkpoint_id)
        
        if checkpoint:
            self._logger.info(
                f"【检查点恢复】ID: {checkpoint_id}, "
                f"时间: {checkpoint.timestamp}"
            )
            return checkpoint.state_data
        
        return None
    
    def register_recovery_handler(
        self,
        error_type: str,
        handler: Callable[[Dict[str, Any]], asyncio.Future]
    ) -> None:
        """
        【注册恢复处理器】注册自定义错误恢复处理器
        
        【参数说明】
        - error_type (str): 错误类型
        - handler (Callable): 处理器函数，接收context参数，返回RecoveryResult
        
        【使用示例】
        ```python
        async def custom_handler(context):
            # 自定义恢复逻辑
            return RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.FALLBACK,
                message="已使用自定义恢复",
                details={},
                timestamp=datetime.now()
            )
        
        service.register_recovery_handler("custom_error", custom_handler)
        ```
        """
        self._recovery_handlers[error_type] = handler
        self._logger.info(f"【处理器注册】类型: {error_type}")
    
    def get_error_history(
        self,
        error_type: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        since: Optional[datetime] = None
    ) -> List[ErrorRecord]:
        """
        【获取错误历史】获取错误历史记录
        
        【参数说明】
        - error_type (str, 可选): 错误类型过滤
        - severity (ErrorSeverity, 可选): 严重级别过滤
        - since (datetime, 可选): 起始时间过滤
        
        【返回值】
        - List[ErrorRecord]: 错误记录列表
        
        【使用示例】
        ```python
        # 获取最近24小时的严重错误
        recent_errors = service.get_error_history(
            severity=ErrorSeverity.HIGH,
            since=datetime.now() - timedelta(hours=24)
        )
        ```
        """
        filtered = self._error_history
        
        if error_type:
            filtered = [e for e in filtered if e.error_type == error_type]
        
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        
        if since:
            filtered = [e for e in filtered if e.timestamp >= since]
        
        return filtered
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        【获取恢复统计】获取错误恢复统计信息
        
        【返回值】
        - Dict[str, Any]: 统计信息
        
        【使用示例】
        ```python
        stats = service.get_recovery_statistics()
        print(f"总错误数: {stats['total_errors']}")
        print(f"恢复成功率: {stats['recovery_rate']}%")
        ```
        """
        total = len(self._error_history)
        recovered = len([e for e in self._error_history if e.recovered])
        
        # 【按类型统计】
        by_type: Dict[str, int] = {}
        by_strategy: Dict[str, int] = {}
        
        for error in self._error_history:
            by_type[error.error_type] = by_type.get(error.error_type, 0) + 1
            if error.recovery_strategy:
                by_strategy[error.recovery_strategy] = by_strategy.get(error.recovery_strategy, 0) + 1
        
        return {
            "total_errors": total,
            "recovered_errors": recovered,
            "recovery_rate": round(recovered / total * 100, 2) if total > 0 else 0,
            "by_type": by_type,
            "by_strategy": by_strategy,
            "active_checkpoints": len(self._checkpoints)
        }
    
    # 【内部方法】
    
    def _create_error_record(
        self,
        error_type: str,
        error_message: str,
        severity: ErrorSeverity,
        context: Dict[str, Any]
    ) -> ErrorRecord:
        """【创建错误记录】创建错误记录对象"""
        error_id = hashlib.md5(
            f"{error_type}:{error_message}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        return ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            timestamp=datetime.now(),
            context=context,
            stack_trace=traceback.format_exc() if sys.exc_info()[0] else None
        )
    
    def _add_error_record(self, record: ErrorRecord) -> None:
        """【添加错误记录】添加错误记录到历史"""
        self._error_history.append(record)
        
        # 【限制历史大小】
        if len(self._error_history) > self._max_history_size:
            self._error_history = self._error_history[-self._max_history_size:]
    
    def _determine_severity(
        self,
        error_type: str,
        context: Dict[str, Any]
    ) -> ErrorSeverity:
        """【确定严重级别】根据错误类型和上下文确定严重级别"""
        critical_types = ["memory_exhaustion", "disk_full", "system_crash"]
        high_types = ["service_unavailable", "database_connection_lost"]
        
        if error_type in critical_types:
            return ErrorSeverity.CRITICAL
        elif error_type in high_types:
            return ErrorSeverity.HIGH
        elif context.get("affected_services", 0) > 3:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM
    
    def _calculate_backoff_delay(self, retry_count: int) -> int:
        """【计算退避延迟】计算指数退避延迟"""
        import random
        base_delay = 2 ** retry_count  # 指数退避
        jitter = random.uniform(0, 1)  # 随机抖动
        return int(base_delay + jitter)
    
    def _get_error_history_for_execution(self, execution_id: str) -> List[Dict]:
        """【获取执行错误历史】获取特定执行的错误历史"""
        return [
            asdict(e) for e in self._error_history
            if e.context.get("execution_id") == execution_id
        ]
    
    async def _persist_checkpoint(self, checkpoint: Checkpoint) -> None:
        """【持久化检查点】将检查点保存到磁盘"""
        checkpoint_dir = Path("data/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(checkpoint), f, ensure_ascii=False, indent=2, default=str)
    
    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """【加载检查点】从磁盘加载检查点"""
        file_path = Path(f"data/checkpoints/{checkpoint_id}.json")
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Checkpoint(
                checkpoint_id=data["checkpoint_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                state_data=data["state_data"],
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            self._logger.error(f"【检查点加载失败】{checkpoint_id}: {e}")
            return None
    
    # 【默认错误处理器】
    
    async def _handle_timeout_error(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理超时错误】"""
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.RETRY,
            message="连接超时，将重试",
            details={"delay": 5},
            timestamp=datetime.now()
        )
    
    async def _handle_connection_error(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理连接错误】"""
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.RETRY,
            message="连接错误，将重试连接",
            details={"delay": 10, "max_retries": 5},
            timestamp=datetime.now()
        )
    
    async def _handle_memory_error(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理内存错误】"""
        # 【尝试清理缓存】
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.FALLBACK,
            message="内存不足，将清理缓存并降低负载",
            details={"actions": ["clear_cache", "reduce_batch_size"]},
            timestamp=datetime.now()
        )
    
    async def _handle_disk_full_error(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理磁盘满错误】"""
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.FALLBACK,
            message="磁盘空间不足，将清理沉积内容",
            details={"actions": ["cleanup_temp", "compress_logs"]},
            timestamp=datetime.now()
        )
    
    async def _handle_permission_error(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理权限错误】"""
        return RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.ESCALATE,
            message="权限不足，需要管理员干预",
            details={"required_permissions": context.get("required", [])},
            timestamp=datetime.now()
        )
    
    async def _handle_script_failure(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理脚本失败】"""
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.RETRY,
            message="脚本执行失败，将重试",
            details={"retry_count": context.get("retry_count", 0) + 1},
            timestamp=datetime.now()
        )
    
    async def _handle_system_overload(self, context: Dict[str, Any]) -> RecoveryResult:
        """【处理系统过载】"""
        return RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.FALLBACK,
            message="系统负载过高，将限流并扩容",
            details={"actions": ["throttle_requests", "scale_workers"]},
            timestamp=datetime.now()
        )
    
    async def _handle_generic_system_error(
        self,
        error_type: str,
        context: Dict[str, Any]
    ) -> RecoveryResult:
        """【处理通用系统错误】"""
        return RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.ESCALATE,
            message=f"未知系统错误类型: {error_type}",
            details={"error_type": error_type, "context": context},
            timestamp=datetime.now()
        )


# 【全局服务实例】
error_recovery_service = ErrorRecoveryService()


# 【便捷函数】
async def handle_script_failure(
    execution_id: str,
    error: Exception,
    context: Dict[str, Any]
) -> RecoveryResult:
    """【便捷函数】处理脚本失败"""
    return await error_recovery_service.handle_script_failure(
        execution_id, error, context
    )


async def handle_system_error(
    error_type: str,
    context: Dict[str, Any]
) -> RecoveryResult:
    """【便捷函数】处理系统错误"""
    return await error_recovery_service.handle_system_error(error_type, context)


async def create_checkpoint(
    checkpoint_id: str,
    state_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Checkpoint:
    """【便捷函数】创建检查点"""
    return await error_recovery_service.create_checkpoint(
        checkpoint_id, state_data, metadata
    )


def get_recovery_statistics() -> Dict[str, Any]:
    """【便捷函数】获取恢复统计"""
    return error_recovery_service.get_recovery_statistics()
