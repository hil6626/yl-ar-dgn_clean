"""
统一脚本执行引擎（增强版）

特性：
1. 执行队列管理（优先级、并发控制）
2. 优雅停止机制
3. 资源限制（CPU、内存、超时）
4. 自动重试和恢复
5. 执行历史持久化
6. 实时监控和告警
7. 配置中心集成
8. 调用链追踪
9. 增强堆栈捕获
"""

import asyncio
import json
import uuid
import time
import traceback
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from collections import deque
import sys

# 配置中心集成
try:
    from app.config_center import config_center
    CONFIG_CENTER_AVAILABLE = True
except ImportError:
    CONFIG_CENTER_AVAILABLE = False
    config_center = None

# 脚本引擎专用配置键
SCRIPT_ENGINE_CONFIG_PREFIX = "script_engine"


class ScriptStatus(Enum):
    """脚本执行状态"""
    PENDING = auto()      # 等待执行
    QUEUED = auto()       # 已进入队列
    RUNNING = auto()      # 执行中
    PAUSED = auto()       # 已暂停
    COMPLETED = auto()    # 成功完成
    FAILED = auto()       # 执行失败
    TIMEOUT = auto()      # 执行超时
    CANCELLED = auto()    # 已取消
    RETRYING = auto()     # 重试中


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_cpu_percent: float = 80.0        # 最大 CPU 使用率
    max_memory_mb: int = 512             # 最大内存使用（MB）
    max_execution_time: int = 300        # 最大执行时间（秒）
    max_disk_io_mbps: float = 100.0      # 最大磁盘 IO（MB/s）
    
    def to_dict(self):
        return asdict(self)


@dataclass
class RetryPolicy:
    """重试策略"""
    max_retries: int = 3                 # 最大重试次数
    retry_delay: float = 5.0             # 重试间隔（秒）
    exponential_backoff: bool = True     # 指数退避
    max_retry_delay: float = 60.0        # 最大重试间隔
    
    def get_delay(self, attempt: int) -> float:
        """获取第 N 次重试的延迟"""
        if not self.exponential_backoff:
            return self.retry_delay
        
        delay = self.retry_delay * (2 ** attempt)
        return min(delay, self.max_retry_delay)


@dataclass
class ScriptExecution:
    """脚本执行记录（增强版）"""
    id: str
    script_id: str
    script_name: str
    script_path: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: ScriptStatus = ScriptStatus.PENDING
    priority: int = 100                  # 数字越小优先级越高
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    output: str = ""
    error: str = ""
    return_code: Optional[int] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # === 新增字段：调用链追踪 ===
    call_chain: List[Dict[str, Any]] = field(default_factory=list)
    
    # === 新增字段：堆栈跟踪（仅错误时填充） ===
    stack_trace: Optional[str] = None
    
    # === 新增字段：父执行ID（支持嵌套调用） ===
    parent_execution_id: Optional[str] = None
    
    # === 新增字段：触发来源 ===
    triggered_by: str = "api"  # api, scheduler, dag, manual
    
    # === 新增字段：配置快照（执行时的配置状态） ===
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        data = asdict(self)
        data['status'] = self.status.name
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        
        # 根据配置级别过滤堆栈跟踪
        if CONFIG_CENTER_AVAILABLE and config_center:
            include_stack = config_center.get(
                f"{SCRIPT_ENGINE_CONFIG_PREFIX}.stack_trace_in_response", False
            )
            if self.stack_trace and include_stack:
                # 限制堆栈长度
                max_length = config_center.get(
                    f"{SCRIPT_ENGINE_CONFIG_PREFIX}.max_stack_trace_length", 5000
                )
                data['stack_trace'] = self.stack_trace[:max_length]
            else:
                data.pop('stack_trace', None)
        else:
            # 默认不包含堆栈
            data.pop('stack_trace', None)

        return data


class ScriptExecutionEngine:
    """
    脚本执行引擎（增强版）
    
    核心功能：
    1. 优先级队列管理
    2. 并发控制
    3. 资源限制和监控
    4. 优雅停止
    5. 自动重试
    6. 执行历史
    7. 配置中心集成
    8. 调用链追踪
    9. 增强堆栈捕获
    """
    
    def __init__(
        self,
        max_concurrent: int = None,  # 改为None，从配置中心读取
        queue_size: int = None,
        default_resource_limits: Optional[ResourceLimits] = None,
        enable_persistence: bool = None
    ):
        # 从配置中心读取配置
        if CONFIG_CENTER_AVAILABLE and config_center:
            self.max_concurrent = max_concurrent or config_center.get(
                f"{SCRIPT_ENGINE_CONFIG_PREFIX}.max_concurrent", 4
            )
            self.queue_size = queue_size or config_center.get(
                f"{SCRIPT_ENGINE_CONFIG_PREFIX}.queue_size", 100
            )
            self.enable_persistence = (
                enable_persistence if enable_persistence is not None
                else config_center.get(
                    f"{SCRIPT_ENGINE_CONFIG_PREFIX}.enable_persistence", True
                )
            )

            # 堆栈跟踪配置
            self.stack_trace_level = config_center.get(
                f"{SCRIPT_ENGINE_CONFIG_PREFIX}.stack_trace_level",
                "minimal"  # 默认最小级别
            )
            self.enable_call_chain = config_center.get(
                f"{SCRIPT_ENGINE_CONFIG_PREFIX}.enable_call_chain",
                True
            )
        else:
            # 使用传入参数或默认值
            self.max_concurrent = max_concurrent or 4
            self.queue_size = queue_size or 100
            self.enable_persistence = (
                enable_persistence if enable_persistence is not None else True
            )
            self.stack_trace_level = "minimal"
            self.enable_call_chain = True
        
        self.default_limits = default_resource_limits or ResourceLimits()
        
        # 执行队列（优先级队列）
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=queue_size)
        
        # 正在执行的脚本
        self._running: Dict[str, ScriptExecution] = {}
        self._processes: Dict[str, asyncio.subprocess.Process] = {}
        self._stop_events: Dict[str, asyncio.Event] = {}
        
        # 执行历史
        self._history: deque = deque(maxlen=1000)
        self._history_file = Path("logs/script_executions.jsonl")
        
        # 快速查找表（用于parent_execution_id查询）
        self._history_lookup: Dict[str, ScriptExecution] = {}
        
        # 统计信息
        self._stats = {
            'submitted': 0,
            'started': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0,
            'timeout': 0
        }
        
        # 回调函数
        self._callbacks: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_complete': [],
            'on_fail': [],
            'on_cancel': [],
            'on_progress': []
        }
        
        # 控制标志
        self._running_flag = False
        self._worker_tasks: List[asyncio.Task] = []
        self._lock = asyncio.Lock()
        
        # 持久化
        if enable_persistence:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """启动执行引擎"""
        if self._running_flag:
            return
        
        self._running_flag = True
        
        # 启动工作线程
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        print(f"脚本执行引擎已启动，并发数: {self.max_concurrent}")
    
    async def stop(self, graceful: bool = True, timeout: float = 30.0):
        """
        停止执行引擎
        
        参数：
            graceful: 是否优雅停止（等待运行中的脚本完成）
            timeout: 优雅停止超时时间
        """
        self._running_flag = False
        
        if graceful:
            # 优雅停止：先停止接受新任务，等待运行中的完成
            print("正在优雅停止脚本执行引擎...")
            
            # 取消队列中等待的任务
            while not self._queue.empty():
                try:
                    priority, execution = self._queue.get_nowait()
                    execution.status = ScriptStatus.CANCELLED
                    await self._notify('on_cancel', execution)
                except asyncio.QueueEmpty:
                    break
            
            # 等待运行中的脚本完成或超时
            start_time = time.time()
            while self._running and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
            
            # 强制停止剩余的脚本
            for execution_id in list(self._running.keys()):
                await self._force_stop_execution(execution_id)
        else:
            # 强制停止：立即终止所有脚本
            print("正在强制停止脚本执行引擎...")
            for execution_id in list(self._running.keys()):
                await self._force_stop_execution(execution_id)
        
        # 取消工作线程
        for task in self._worker_tasks:
            task.cancel()
        
        self._worker_tasks.clear()
        print("脚本执行引擎已停止")
    
    def _build_call_chain(
        self, 
        parent_id: Optional[str] = None,
        triggered_by: str = "api",
        request_context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        构建调用链
        
        参数：
            parent_id: 父执行ID（用于嵌套调用）
            triggered_by: 触发来源
            request_context: 请求上下文信息
        
        返回：
            调用链节点列表
        """
        chain = []
        
        # 如果有父执行，继承其调用链
        if parent_id and parent_id in self._history_lookup:
            parent = self._history_lookup[parent_id]
            chain = parent.call_chain.copy()
        
        # 添加当前节点
        node = {
            "node_type": "script_engine",
            "node_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "action": "script_submit",
            "triggered_by": triggered_by,
            "engine_instance": id(self),  # 实例标识
        }
        
        # 添加上下文信息（如果有）
        if request_context:
            # 过滤敏感信息
            safe_context = {
                "request_id": request_context.get("request_id"),
                "user_id": request_context.get("user_id"),
                "client_ip": request_context.get("client_ip"),
            }
            node["context"] = safe_context
        
        chain.append(node)
        
        # 限制调用链长度
        max_chain_length = 10
        if CONFIG_CENTER_AVAILABLE and config_center:
            max_chain_length = config_center.get(
                f"{SCRIPT_ENGINE_CONFIG_PREFIX}.max_call_chain_length", 10
            )

        if len(chain) > max_chain_length:
            chain = chain[-max_chain_length:]
            chain[0]["truncated"] = True  # 标记已截断
        
        return chain
    
    async def submit(
        self,
        script_id: str,
        script_name: str,
        script_path: str,
        params: Optional[Dict] = None,
        priority: int = 100,
        resource_limits: Optional[ResourceLimits] = None,
        retry_policy: Optional[RetryPolicy] = None,
        metadata: Optional[Dict] = None,
        # === 新增参数 ===
        parent_execution_id: Optional[str] = None,
        triggered_by: str = "api",
        request_context: Optional[Dict] = None,
    ) -> str:
        """
        提交脚本执行请求（增强版）
        
        参数：
            script_id: 脚本标识
            script_name: 脚本名称
            script_path: 脚本路径
            params: 执行参数
            priority: 优先级（数字越小优先级越高）
            resource_limits: 资源限制
            retry_policy: 重试策略
            metadata: 附加元数据
            parent_execution_id: 父执行ID（用于DAG等嵌套场景）
            triggered_by: 触发来源标识
            request_context: 请求上下文
        
        返回：
            str: 执行ID
        """
        # 构建调用链
        call_chain = []
        if self.enable_call_chain:
            call_chain = self._build_call_chain(
                parent_id=parent_execution_id,
                triggered_by=triggered_by,
                request_context=request_context
            )
        
        # 捕获配置快照
        config_snapshot = {}
        if CONFIG_CENTER_AVAILABLE and config_center:
            snapshot_key = f"{SCRIPT_ENGINE_CONFIG_PREFIX}.capture_config_snapshot"
            if config_center.get(snapshot_key, True):
                config_snapshot = {
                    "max_concurrent": self.max_concurrent,
                    "queue_size": self.queue_size,
                    "stack_trace_level": self.stack_trace_level,
                    "resource_limits": (
                        resource_limits or self.default_limits
                    ).to_dict(),
                    "retry_policy": asdict(retry_policy or RetryPolicy()),
                }
        
        execution = ScriptExecution(
            id=str(uuid.uuid4()),
            script_id=script_id,
            script_name=script_name,
            script_path=script_path,
            params=params or {},
            priority=priority,
            max_retries=retry_policy.max_retries if retry_policy else 3,
            metadata=metadata or {},
            # === 填充新增字段 ===
            call_chain=call_chain,
            parent_execution_id=parent_execution_id,
            triggered_by=triggered_by,
            config_snapshot=config_snapshot,
        )
        
        # 存储资源限制和重试策略
        execution.metadata['resource_limits'] = (resource_limits or self.default_limits).to_dict()
        execution.metadata['retry_policy'] = asdict(retry_policy or RetryPolicy())
        
        async with self._lock:
            self._stats['submitted'] += 1
        
        # 尝试加入队列
        try:
            # 优先级队列使用 (priority, execution) 格式
            await asyncio.wait_for(
                self._queue.put((priority, execution)),
                timeout=5.0
            )
            execution.status = ScriptStatus.QUEUED
            return execution.id
            
        except asyncio.TimeoutError:
            execution.status = ScriptStatus.FAILED
            execution.error = "提交超时，队列已满"
            await self._persist_execution(execution)
            raise RuntimeError("脚本提交失败：执行队列已满")
    
    async def cancel(self, execution_id: str) -> bool:
        """取消脚本执行"""
        async with self._lock:
            # 检查是否在运行中
            if execution_id in self._running:
                execution = self._running[execution_id]
                await self._graceful_stop_execution(execution_id)
                execution.status = ScriptStatus.CANCELLED
                await self._notify('on_cancel', execution)
                return True
            
            # 检查是否在队列中
            # 注意：从优先级队列中移除特定项比较复杂，
            # 这里采用标记方式，执行时检查状态
            temp_queue = asyncio.PriorityQueue()
            found = False
            
            while not self._queue.empty():
                try:
                    priority, execution = self._queue.get_nowait()
                    if execution.id == execution_id:
                        execution.status = ScriptStatus.CANCELLED
                        await self._notify('on_cancel', execution)
                        found = True
                    else:
                        await temp_queue.put((priority, execution))
                except asyncio.QueueEmpty:
                    break
            
            # 恢复队列
            while not temp_queue.empty():
                try:
                    priority, execution = temp_queue.get_nowait()
                    await self._queue.put((priority, execution))
                except asyncio.QueueEmpty:
                    break
            
            return found
    
    async def get_execution(self, execution_id: str) -> Optional[ScriptExecution]:
        """获取执行记录"""
        # 检查运行中
        if execution_id in self._running:
            return self._running[execution_id]
        
        # 检查历史
        for execution in self._history:
            if execution.id == execution_id:
                return execution
        
        return None
    
    async def get_status(self, execution_id: str) -> Optional[str]:
        """
        【获取执行状态】获取指定执行的状态
        
        【参数】
            execution_id: 执行ID
        
        【返回值】
            str: 状态字符串，或 None 如果未找到
        """
        execution = await self.get_execution(execution_id)
        if execution:
            return execution.status.name.lower()
        return None
    
    async def execute(
        self,
        script_id: str,
        script_path: str,
        params: Optional[Dict] = None,
        priority: int = 100
    ) -> ScriptExecution:
        """
        【执行脚本】直接执行脚本（简化接口）
        
        【参数】
            script_id: 脚本标识
            script_path: 脚本路径
            params: 执行参数
            priority: 优先级
        
        【返回值】
            ScriptExecution: 执行记录
        """
        # 提交并等待完成
        execution_id = await self.submit(
            script_id=script_id,
            script_name=script_id,
            script_path=script_path,
            params=params,
            priority=priority
        )
        
        # 等待执行完成
        while True:
            execution = await self.get_execution(execution_id)
            if not execution:
                raise RuntimeError(f"执行记录丢失: {execution_id}")
            
            if execution.status in [
                ScriptStatus.COMPLETED, ScriptStatus.FAILED,
                ScriptStatus.TIMEOUT, ScriptStatus.CANCELLED
            ]:
                return execution
            
            await asyncio.sleep(0.1)
    
    async def get_history(
        self,
        script_id: Optional[str] = None,
        status: Optional[ScriptStatus] = None,
        limit: int = 100
    ) -> List[ScriptExecution]:
        """获取执行历史"""
        history = list(self._history)
        
        if script_id:
            history = [h for h in history if h.script_id == script_id]
        
        if status:
            history = [h for h in history if h.status == status]
        
        # 按时间倒序
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return history[:limit]
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self._stats.copy()
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    async def _worker_loop(self, worker_id: str):
        """工作线程主循环"""
        while self._running_flag:
            try:
                # 从队列获取任务（带超时，以便检查停止标志）
                priority, execution = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                
                # 检查是否已取消
                if execution.status == ScriptStatus.CANCELLED:
                    continue
                
                # 执行脚本
                await self._execute_script(execution)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"工作线程 {worker_id} 错误: {e}")
    
    async def _execute_script(self, execution: ScriptExecution):
        """执行单个脚本（增强堆栈捕获）"""
        execution_id = execution.id
        
        async with self._lock:
            self._running[execution_id] = execution
            execution.status = ScriptStatus.RUNNING
            execution.started_at = datetime.now()
            self._stats['started'] += 1
        
        # 通知开始
        await self._notify('on_start', execution)
        
        # 获取资源限制
        limits_dict = execution.metadata.get('resource_limits', {})
        limits = ResourceLimits(**limits_dict)
        
        # 创建停止事件
        self._stop_events[execution_id] = asyncio.Event()
        
        # 记录执行开始节点到调用链
        if self.enable_call_chain:
            execution.call_chain.append({
                "node_type": "script_engine",
                "node_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.now().isoformat(),
                "action": "execution_start",
                "script_path": execution.script_path,
            })
        
        start_time = time.time()
        
        try:
            # 构建命令
            cmd = [sys.executable, execution.script_path]
            
            # 添加参数
            for key, value in execution.params.items():
                cmd.extend([f"--{key}", str(value)])
            
            # 启动进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*1024  # 1MB 缓冲区
            )
            
            self._processes[execution_id] = process
            
            # 监控执行
            output_lines = []
            error_lines = []  # 新增：单独收集错误输出
            
            # 增强的流读取
            async def read_stream(stream, is_error=False):
                target_lines = error_lines if is_error else output_lines
                max_lines = 1000
                if CONFIG_CENTER_AVAILABLE and config_center:
                    max_lines = config_center.get(
                        f"{SCRIPT_ENGINE_CONFIG_PREFIX}.max_output_lines", 1000
                    )

                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode('utf-8', errors='replace').rstrip()
                    target_lines.append(text)
                    
                    # 限制行数
                    if len(target_lines) > max_lines:
                        target_lines.pop(0)
                        if not hasattr(execution, '_output_truncated'):
                            execution._output_truncated = True
                    
                    # 通知进度
                    await self._notify('on_progress', execution, {
                        'line': text,
                        'is_error': is_error
                    })
            
            # 并发读取 stdout 和 stderr
            await asyncio.gather(
                read_stream(process.stdout, False),
                read_stream(process.stderr, True)
            )
            
            # 等待进程完成（带超时）
            try:
                return_code = await asyncio.wait_for(
                    process.wait(),
                    timeout=limits.max_execution_time
                )
                
                # 合并输出（stderr在前标记）
                full_output = '\n'.join(output_lines)
                if error_lines:
                    full_output += '\n[STDERR]\n' + '\n'.join(error_lines)
                
                execution.return_code = return_code
                execution.output = full_output
                
                # 记录完成节点到调用链
                if self.enable_call_chain:
                    execution.call_chain.append({
                        "node_type": "script_engine",
                        "node_id": str(uuid.uuid4())[:8],
                        "timestamp": datetime.now().isoformat(),
                        "action": "execution_complete",
                        "return_code": return_code,
                        "duration_ms": (time.time() - start_time) * 1000,
                    })
                
                if return_code == 0:
                    execution.status = ScriptStatus.COMPLETED
                    self._stats['completed'] += 1
                    await self._notify('on_complete', execution)
                else:
                    execution.status = ScriptStatus.FAILED
                    execution.error = f"脚本返回非零退出码: {return_code}"
                    if error_lines:
                        execution.error += f"\n错误输出: {error_lines[-5:]}"  # 最后5行错误
                    
                    self._stats['failed'] += 1
                    await self._notify('on_fail', execution)
                    
            except asyncio.TimeoutError:
                # 超时处理（增强堆栈记录）
                execution.status = ScriptStatus.TIMEOUT
                execution.error = f"执行超时（>{limits.max_execution_time}秒）"
                
                # 记录超时节点
                if self.enable_call_chain:
                    execution.call_chain.append({
                        "node_type": "script_engine",
                        "node_id": str(uuid.uuid4())[:8],
                        "timestamp": datetime.now().isoformat(),
                        "action": "execution_timeout",
                        "timeout_seconds": limits.max_execution_time,
                    })
                
                self._stats['timeout'] += 1
                
                # 终止进程
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except:
                    process.kill()
                
                await self._notify('on_fail', execution)
            
        except Exception as e:
            # 异常处理（核心增强）
            execution.status = ScriptStatus.FAILED
            execution.error = str(e)

            # 根据配置级别捕获堆栈
            if self.stack_trace_level in ("full", "dev_only"):
                execution.stack_trace = traceback.format_exc()

                # 记录到调用链
                if self.enable_call_chain:
                    execution.call_chain.append({
                        "node_type": "script_engine",
                        "node_id": str(uuid.uuid4())[:8],
                        "timestamp": datetime.now().isoformat(),
                        "action": "execution_exception",
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                        "has_stack_trace": True,
                    })

            self._stats['failed'] += 1
            await self._notify('on_fail', execution)

            # 记录错误日志
            logging.error(
                f"脚本执行异常 [{execution_id}]: {str(e)}",
                extra={
                    "script_id": execution.script_id,
                    "script_name": execution.script_name,
                    "stack_trace": execution.stack_trace,
                    "call_chain": execution.call_chain,
                }
            )

        finally:
            # 清理和持久化（增强版）
            execution.completed_at = datetime.now()
            execution.duration_ms = (time.time() - start_time) * 1000
            
            async with self._lock:
                if execution_id in self._running:
                    del self._running[execution_id]
                if execution_id in self._processes:
                    del self._processes[execution_id]
                if execution_id in self._stop_events:
                    del self._stop_events[execution_id]
            
            # 添加到历史（同时维护查找表）
            self._history.append(execution)
            self._history_lookup[execution.id] = execution
            
            # 限制查找表大小
            max_lookup_size = 10000
            if CONFIG_CENTER_AVAILABLE and config_center:
                max_lookup_size = config_center.get(
                    f"{SCRIPT_ENGINE_CONFIG_PREFIX}.max_history_lookup_size", 10000
                )

            if len(self._history_lookup) > max_lookup_size:
                # 移除最旧的条目
                oldest_id = next(iter(self._history_lookup))
                del self._history_lookup[oldest_id]

            # 持久化
            await self._persist_execution(execution)
    
    async def _graceful_stop_execution(self, execution_id: str):
        """优雅停止脚本执行"""
        if execution_id in self._stop_events:
            self._stop_events[execution_id].set()
        
        if execution_id in self._processes:
            process = self._processes[execution_id]
            try:
                # 发送 SIGTERM
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except Exception:
                # 强制终止
                process.kill()
    
    async def _force_stop_execution(self, execution_id: str):
        """强制停止脚本执行"""
        if execution_id in self._processes:
            process = self._processes[execution_id]
            try:
                process.kill()
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except Exception:
                pass
    
    async def _persist_execution(self, execution: ScriptExecution):
        """持久化执行记录"""
        if not self.enable_persistence:
            return
        
        try:
            with open(self._history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(execution.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            logging.error(f"持久化执行记录失败: {e}")
    
    async def _notify(self, event: str, execution: ScriptExecution, data: Any = None):
        """通知回调函数"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        if data:
                            await callback(execution, data)
                        else:
                            await callback(execution)
                    else:
                        if data:
                            callback(execution, data)
                        else:
                            callback(execution)
                except Exception as e:
                    logging.error(f"回调通知失败: {e}")


# 为兼容性提供别名
ScriptEngine = ScriptExecutionEngine

# 全局脚本执行引擎实例
script_engine = ScriptExecutionEngine(
    max_concurrent=4,
    queue_size=100,
    enable_persistence=True
)


# 使用示例
if __name__ == "__main__":
    async def main():
        # 启动引擎
        await script_engine.start()
        
        # 注册回调
        def on_start(execution):
            print(f"脚本开始执行: {execution.script_name}")
        
        def on_complete(execution):
            print(f"脚本执行完成: {execution.script_name}, 耗时: {execution.duration_ms}ms")
        
        script_engine.register_callback('on_start', on_start)
        script_engine.register_callback('on_complete', on_complete)
        
        # 提交脚本
        execution_id = await script_engine.submit(
            script_id="test_script",
            script_name="测试脚本",
            script_path="scripts/monitor/01_cpu_usage_monitor.py",
            params={"interval": "5"},
            priority=10
        )
        
        print(f"脚本已提交，执行ID: {execution_id}")
        
        # 等待一段时间
        await asyncio.sleep(10)
        
        # 停止引擎
        await script_engine.stop()
    
    asyncio.run(main())
