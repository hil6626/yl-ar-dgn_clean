"""
脚本执行器服务
提供脚本管理、执行控制和轮询调度功能
"""

import asyncio
import uuid
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class ScriptConfig:
    """脚本配置"""
    id: str
    name: str
    description: Dict[str, Any] = field(default_factory=dict)
    category: str = "tools"
    path: str = ""
    status: str = "idle"
    polling: Dict[str, Any] = field(default_factory=lambda: {"enabled": False, "interval": 300})
    last_execution: Optional[datetime] = None
    lastLog: str = "等待执行..."


@dataclass
class ScriptExecution:
    """脚本执行记录"""
    id: str
    script_id: str
    status: str = "pending"
    output: str = ""
    error: str = ""
    returncode: int = -1
    duration: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ScriptsRunner:
    """
    脚本执行器
    
    职责:
    1. 管理脚本配置和元数据
    2. 执行脚本并捕获输出
    3. 管理轮询调度
    4. 提供实时日志流
    """
    
    def __init__(self):
        self.scripts: Dict[str, ScriptConfig] = {}
        self.running_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.execution_history: Dict[str, List[ScriptExecution]] = {}
        self._log_queues: Dict[str, asyncio.Queue] = {}
        self._polling_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
    
    async def _initialize(self):
        """初始化，加载脚本配置"""
        if self._initialized:
            return
        
        await self._load_scripts()
        self._initialized = True
    
    async def _load_scripts(self):
        """从数据库或文件系统加载脚本"""
        try:
            # 尝试从数据库加载
            from app.models.script import Script
            
            db_scripts = await Script.all()
            
            for script in db_scripts:
                self.scripts[script.id] = ScriptConfig(
                    id=script.id,
                    name=script.name,
                    description=script.description or {},
                    category=script.category or "tools",
                    path=script.path or f"scripts/{script.name}.py",
                    status=script.status or "idle",
                    polling=script.polling or {"enabled": False, "interval": 300},
                    last_execution=script.last_execution,
                    lastLog=script.lastLog or "等待执行..."
                )
            
            # 如果没有脚本，使用示例数据
            if not self.scripts:
                self._load_sample_scripts()
                
        except Exception as e:
            # 使用示例数据
            self._load_sample_scripts()
    
    def _load_sample_scripts(self):
        """加载示例脚本"""
        sample_scripts = [
            {
                "id": "cpu-monitor",
                "name": "CPU监控",
                "description": {
                    "summary": "实时监控系统CPU使用率",
                    "detail": "采集CPU使用率、负载平均值、进程数等指标",
                    "business_value": "及时发现CPU资源瓶颈，预防系统过载",
                    "tags": ["监控", "系统", "CPU"]
                },
                "category": "monitor",
                "path": "scripts/monitor/cpu_monitor.py"
            },
            {
                "id": "disk-check",
                "name": "磁盘检查",
                "description": {
                    "summary": "检查磁盘空间和inode使用情况",
                    "detail": "监控磁盘使用率，预警磁盘空间不足",
                    "business_value": "防止磁盘满导致系统故障",
                    "tags": ["监控", "磁盘", "存储"]
                },
                "category": "maintenance",
                "path": "scripts/maintenance/disk_check.py"
            },
            {
                "id": "alert-notify",
                "name": "告警通知",
                "description": {
                    "summary": "发送告警通知到多渠道",
                    "detail": "支持邮件、短信、Webhook等多种通知方式",
                    "business_value": "确保告警及时送达，快速响应故障",
                    "tags": ["告警", "通知", "运维"]
                },
                "category": "alert",
                "path": "scripts/alert/alert_notify.py"
            },
            {
                "id": "log-cleanup",
                "name": "日志清理",
                "description": {
                    "summary": "自动清理过期日志文件",
                    "detail": "按配置保留期清理日志，释放磁盘空间",
                    "business_value": "自动化运维，减少人工干预",
                    "tags": ["维护", "日志", "清理"]
                },
                "category": "maintenance",
                "path": "scripts/maintenance/log_cleanup.py"
            }
        ]
        
        for script_data in sample_scripts:
            self.scripts[script_data["id"]] = ScriptConfig(
                id=script_data["id"],
                name=script_data["name"],
                description=script_data["description"],
                category=script_data["category"],
                path=script_data["path"]
            )
    
    async def get_all_scripts(self) -> List[Dict[str, Any]]:
        """
        获取所有脚本列表
        """
        await self._initialize()
        
        return [
            {
                "id": script.id,
                "name": script.name,
                "description": script.description,
                "category": script.category,
                "status": script.status,
                "polling": script.polling,
                "lastLog": script.lastLog,
                "last_execution": script.last_execution.isoformat() if script.last_execution else None
            }
            for script in self.scripts.values()
        ]
    
    async def execute(self, script_id: str) -> Dict[str, Any]:
        """
        执行指定脚本
        """
        await self._initialize()
        
        script = self.scripts.get(script_id)
        if not script:
            return {
                "success": False,
                "error": f"脚本 {script_id} 不存在",
                "output": "",
                "duration": 0,
                "returncode": -1
            }
        
        # 检查是否已在运行
        if script_id in self.running_processes:
            return {
                "success": False,
                "error": "脚本正在执行中",
                "output": "",
                "duration": 0,
                "returncode": -1
            }
        
        # 创建执行记录
        execution_id = str(uuid.uuid4())[:8]
        execution = ScriptExecution(
            id=execution_id,
            script_id=script_id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        # 更新脚本状态
        script.status = "running"
        
        # 创建日志队列
        self._log_queues[script_id] = asyncio.Queue()
        
        # 执行脚本
        start_time = datetime.utcnow()
        
        try:
            # 模拟脚本执行（实际应调用真实脚本）
            proc = await asyncio.create_subprocess_exec(
                "python3", "-c",
                f"import time; print('开始执行: {script.name}'); time.sleep(2); print('执行完成')",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            self.running_processes[script_id] = proc
            
            # 读取输出
            stdout, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=60
            )
            
            output = stdout.decode("utf-8", errors="replace")
            returncode = proc.returncode
            
            # 更新执行记录
            execution.output = output
            execution.returncode = returncode
            execution.status = "completed" if returncode == 0 else "failed"
            execution.completed_at = datetime.utcnow()
            execution.duration = (execution.completed_at - start_time).total_seconds()
            
            # 更新脚本状态
            script.status = "success" if returncode == 0 else "error"
            script.lastLog = output[-500:] if len(output) > 500 else output  # 保留最后500字符
            script.last_execution = datetime.utcnow()
            
            # 推送日志
            await self._push_log(script_id, output)
            
            return {
                "success": returncode == 0,
                "output": output,
                "duration": execution.duration,
                "returncode": returncode
            }
            
        except asyncio.TimeoutError:
            # 超时处理
            if script_id in self.running_processes:
                proc = self.running_processes[script_id]
                proc.kill()
            
            execution.status = "timeout"
            execution.error = "执行超时(>60s)"
            execution.completed_at = datetime.utcnow()
            script.status = "error"
            
            return {
                "success": False,
                "error": "执行超时",
                "output": "脚本执行超过60秒，已强制终止",
                "duration": 60,
                "returncode": -1
            }
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            script.status = "error"
            
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "duration": 0,
                "returncode": -1
            }
            
        finally:
            # 清理
            self.running_processes.pop(script_id, None)
            
            # 保存执行历史
            if script_id not in self.execution_history:
                self.execution_history[script_id] = []
            self.execution_history[script_id].append(execution)
            
            # 只保留最近20条记录
            self.execution_history[script_id] = self.execution_history[script_id][-20:]
    
    async def stop(self, script_id: str) -> bool:
        """
        停止正在执行的脚本
        """
        if script_id not in self.running_processes:
            return False
        
        try:
            proc = self.running_processes[script_id]
            proc.kill()
            
            # 等待进程结束
            await proc.wait()
            
            # 更新状态
            script = self.scripts.get(script_id)
            if script:
                script.status = "stopped"
            
            self.running_processes.pop(script_id, None)
            
            return True
            
        except Exception as e:
            print(f"停止脚本失败: {e}")
            return False
    
    async def set_polling(self, script_id: str, enabled: bool, interval: int):
        """
        设置脚本轮询配置
        """
        await self._initialize()
        
        script = self.scripts.get(script_id)
        if not script:
            return
        
        # 更新配置
        script.polling = {
            "enabled": enabled,
            "interval": interval
        }
        
        # 如果启用轮询，创建调度任务
        if enabled:
            if script_id in self._polling_tasks:
                self._polling_tasks[script_id].cancel()
            
            self._polling_tasks[script_id] = asyncio.create_task(
                self._polling_loop(script_id, interval)
            )
        else:
            # 禁用轮询，取消任务
            if script_id in self._polling_tasks:
                self._polling_tasks[script_id].cancel()
                del self._polling_tasks[script_id]
    
    async def _polling_loop(self, script_id: str, interval: int):
        """
        轮询执行循环
        """
        while True:
            try:
                # 执行脚本
                await self.execute(script_id)
                
                # 等待下一次执行
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"轮询执行错误: {e}")
                await asyncio.sleep(interval)
    
    async def get_logs(self, script_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取脚本执行日志
        """
        await self._initialize()
        
        # 从历史记录中获取日志
        history = self.execution_history.get(script_id, [])
        
        logs = []
        for execution in history[-limit:]:
            logs.append({
                "message": execution.output or execution.error or "无输出",
                "timestamp": execution.completed_at.isoformat() if execution.completed_at else datetime.utcnow().isoformat(),
                "status": execution.status
            })
        
        return logs
    
    async def log_stream(self, script_id: str):
        """
        日志流生成器（用于WebSocket）
        """
        # 创建队列
        if script_id not in self._log_queues:
            self._log_queues[script_id] = asyncio.Queue()
        
        queue = self._log_queues[script_id]
        
        while True:
            try:
                # 等待日志（超时1秒发送心跳）
                log = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield log
            except asyncio.TimeoutError:
                # 发送心跳
                yield {
                    "message": "",
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "heartbeat"
                }
    
    async def _push_log(self, script_id: str, message: str):
        """
        推送日志到队列
        """
        if script_id in self._log_queues:
            await self._log_queues[script_id].put({
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
