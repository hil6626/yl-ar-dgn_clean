# 脚本模型定义
# 包含 Script 实体和 ScriptStatus 枚举

import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Any, List


# 脚本名称白名单验证
SCRIPT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


class ScriptStatus(str, Enum):
    """脚本执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Script(BaseModel):
    """脚本模型"""
    id: str
    name: str
    description: Optional[str] = None
    file_path: str
    priority: int = 1000
    status: ScriptStatus = ScriptStatus.PENDING
    last_run_time: Optional[datetime] = None
    last_run_duration: Optional[float] = None  # 毫秒
    last_run_output: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    parameters: dict = Field(default_factory=dict)
    declared_params: List[str] = Field(default_factory=list)
    # 内存级最近执行聚合（按时间降序），条数受环境变量控制
    recent_runs: List[dict] = Field(default_factory=list)
    schedule: Optional[str] = None  # Cron 表达式
    enabled: bool = True


class ScriptRunRequest(BaseModel):
    """脚本执行请求"""
    script_name: str
    params: dict = {}

    @field_validator('script_name')
    @classmethod
    def validate_script_name(cls, v: str) -> str:
        """验证脚本名称：只允许字母、数字、下划线、连字符"""
        if not v:
            raise ValueError("脚本名称不能为空")
        if not SCRIPT_NAME_PATTERN.match(v):
            raise ValueError("脚本名称只允许字母、数字、下划线、连字符")
        # 防止路径遍历
        if '..' in v or v.startswith('/') or v.startswith('\\'):
            raise ValueError("脚本名称包含非法字符")
        return v


class ScriptRunResponse(BaseModel):
    """脚本执行响应"""
    status: str  # "success" | "fail"
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
