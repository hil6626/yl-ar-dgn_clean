"""
脚本元数据管理服务
管理脚本的元数据、执行历史和状态
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ScriptExecutionRecord:
    """脚本执行记录"""
    id: str
    script_id: str
    status: str  # pending, running, completed, failed, timeout, stopped
    output: str = ""
    error: str = ""
    returncode: int = -1
    duration: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScriptStatus:
    """脚本实时状态"""
    script_id: str
    status: str  # idle, running, success, error, stopped
    last_execution: Optional[str] = None
    last_output: str = ""
    execution_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    is_running: bool = False
    current_execution_id: Optional[str] = None


class ScriptMetadataManager:
    """
    脚本元数据管理器
    
    管理脚本的元数据、执行历史和实时状态
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.execution_history: Dict[str, List[ScriptExecutionRecord]] = {}
        self.script_status: Dict[str, ScriptStatus] = {}
        self._running_executions: Dict[str, ScriptExecutionRecord] = {}
        self._lock = asyncio.Lock()
        
        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载历史数据
        self._load_data()
    
    def _get_history_file(self) -> Path:
        """获取历史记录文件路径"""
        return self.data_dir / "script_execution_history.json"
    
    def _get_status_file(self) -> Path:
        """获取状态文件路径"""
        return self.data_dir / "script_status.json"
    
    def _load_data(self):
        """加载历史数据"""
        try:
            # 加载执行历史
            history_file = self._get_history_file()
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for script_id, records in data.items():
                        self.execution_history[script_id] = [
                            ScriptExecutionRecord(**r) for r in records
                        ]
            
            # 加载状态
            status_file = self._get_status_file()
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for script_id, status_data in data.items():
                        self.script_status[script_id] = ScriptStatus(**status_data)
                        
        except Exception as e:
            print(f"加载脚本数据失败: {e}")
    
    async def _save_data(self):
        """保存数据到文件"""
        async with self._lock:
            try:
                # 保存执行历史
                history_data = {
                    k: [asdict(r) for r in v]
                    for k, v in self.execution_history.items()
                }
                with open(self._get_history_file(), 'w', encoding='utf-8') as f:
                    json.dump(history_data, f, ensure_ascii=False, indent=2)
                
                # 保存状态
                status_data = {
                    k: asdict(v) for k, v in self.script_status.items()
                }
                with open(self._get_status_file(), 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                print(f"保存脚本数据失败: {e}")
    
    async def create_execution(
        self,
        script_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ScriptExecutionRecord:
        """
        创建新的执行记录
        """
        execution_id = f"{script_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        record = ScriptExecutionRecord(
            id=execution_id,
            script_id=script_id,
            status="pending",
            started_at=datetime.utcnow().isoformat(),
            parameters=parameters or {}
        )
        
        async with self._lock:
            self._running_executions[execution_id] = record
            
            # 更新脚本状态
            if script_id not in self.script_status:
                self.script_status[script_id] = ScriptStatus(
                    script_id=script_id,
                    status="idle",
                    execution_count=0
                )
            
            status = self.script_status[script_id]
            status.status = "running"
            status.is_running = True
            status.current_execution_id = execution_id
        
        await self._save_data()
        return record
    
    async def update_execution_status(
        self,
        execution_id: str,
        status: str,
        output: Optional[str] = None,
        error: Optional[str] = None,
        returncode: Optional[int] = None,
        duration: Optional[float] = None
    ):
        """
        更新执行状态
        """
        async with self._lock:
            if execution_id not in self._running_executions:
                return
            
            record = self._running_executions[execution_id]
            record.status = status
            
            if output is not None:
                record.output = output
            if error is not None:
                record.error = error
            if returncode is not None:
                record.returncode = returncode
            if duration is not None:
                record.duration = duration
            
            if status in ["completed", "failed", "timeout", "stopped"]:
                record.completed_at = datetime.utcnow().isoformat()
                
                # 移动到历史记录
                script_id = record.script_id
                if script_id not in self.execution_history:
                    self.execution_history[script_id] = []
                
                self.execution_history[script_id].append(record)
                
                # 只保留最近50条记录
                self.execution_history[script_id] = \
                    self.execution_history[script_id][-50:]
                
                # 从运行中移除
                del self._running_executions[execution_id]
                
                # 更新脚本状态
                if script_id in self.script_status:
                    status_obj = self.script_status[script_id]
                    status_obj.is_running = False
                    status_obj.current_execution_id = None
                    status_obj.last_execution = record.completed_at
                    status_obj.last_output = record.output[:500]
                    status_obj.execution_count += 1
                    
                    if status == "completed" and returncode == 0:
                        status_obj.status = "success"
                        status_obj.success_count += 1
                    else:
                        status_obj.status = "error"
                        status_obj.fail_count += 1
        
        await self._save_data()
    
    async def get_execution(self, execution_id: str) -> Optional[ScriptExecutionRecord]:
        """
        获取执行记录
        """
        # 先在运行中查找
        if execution_id in self._running_executions:
            return self._running_executions[execution_id]
        
        # 在历史记录中查找
        for records in self.execution_history.values():
            for record in records:
                if record.id == execution_id:
                    return record
        
        return None
    
    async def get_script_history(
        self,
        script_id: str,
        limit: int = 20
    ) -> List[ScriptExecutionRecord]:
        """
        获取脚本的执行历史
        """
        records = self.execution_history.get(script_id, [])
        return records[-limit:]
    
    async def get_script_status(self, script_id: str) -> Optional[ScriptStatus]:
        """
        获取脚本状态
        """
        return self.script_status.get(script_id)
    
    async def get_all_status(self) -> Dict[str, ScriptStatus]:
        """
        获取所有脚本状态
        """
        return self.script_status.copy()
    
    async def get_running_executions(self) -> List[ScriptExecutionRecord]:
        """
        获取正在执行的脚本列表
        """
        return list(self._running_executions.values())
    
    async def stop_execution(self, execution_id: str) -> bool:
        """
        停止执行
        """
        if execution_id not in self._running_executions:
            return False
        
        await self.update_execution_status(
            execution_id,
            "stopped",
            error="用户手动停止"
        )
        return True
    
    async def get_execution_logs(
        self,
        execution_id: str,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取执行日志
        """
        record = await self.get_execution(execution_id)
        if not record:
            return []
        
        logs = []
        if record.output:
            logs.append({
                "timestamp": record.started_at or datetime.utcnow().isoformat(),
                "level": "info",
                "message": record.output
            })
        
        if record.error:
            logs.append({
                "timestamp": record.completed_at or datetime.utcnow().isoformat(),
                "level": "error",
                "message": record.error
            })
        
        return logs
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取执行统计信息
        """
        total_executions = 0
        success_count = 0
        fail_count = 0
        running_count = len(self._running_executions)
        
        for status in self.script_status.values():
            total_executions += status.execution_count
            success_count += status.success_count
            fail_count += status.fail_count
        
        return {
            "total_executions": total_executions,
            "success_count": success_count,
            "fail_count": fail_count,
            "running_count": running_count,
            "success_rate": (
                (success_count / total_executions * 100)
                if total_executions > 0 else 0
            )
        }


# 全局管理器实例
_metadata_manager: Optional[ScriptMetadataManager] = None


def get_script_metadata_manager(data_dir: str = "data") -> ScriptMetadataManager:
    """
    获取脚本元数据管理器实例（单例）
    """
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = ScriptMetadataManager(data_dir)
    return _metadata_manager
