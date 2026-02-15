# DAG 模型定义
# 包含 DAG、DAGNode、DAGStatus 等模型

import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4


# 节点名称白名单验证
NODE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


class DAGStatus(str, Enum):
    """DAG 执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DAGNodeStatus(str, Enum):
    """DAG 节点状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DAGNode(BaseModel):
    """DAG 节点模型"""
    id: str
    name: str
    script_name: Optional[str] = None  # 关联的脚本名称
    status: DAGNodeStatus = DAGNodeStatus.PENDING
    depends_on: List[str] = Field(default_factory=list)  # 依赖的节点 ID 列表
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 毫秒
    output: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    @field_validator('name')
    @classmethod
    def validate_node_name(cls, v: str) -> str:
        """验证节点名称：只允许字母、数字、下划线、连字符"""
        if not v:
            raise ValueError("节点名称不能为空")
        if not NODE_NAME_PATTERN.match(v):
            raise ValueError("节点名称只允许字母、数字、下划线、连字符")
        return v

    @field_validator('script_name')
    @classmethod
    def validate_script_name(cls, v: Optional[str]) -> Optional[str]:
        """验证脚本名称"""
        if v is None:
            return v
        if not NODE_NAME_PATTERN.match(v):
            raise ValueError("脚本名称只允许字母、数字、下划线、连字符")
        if '..' in v or v.startswith('/') or v.startswith('\\'):
            raise ValueError("脚本名称包含非法字符")
        return v

    @field_validator('depends_on')
    @classmethod
    def validate_depends_on(cls, v: List[str]) -> List[str]:
        """验证依赖列表"""
        for dep in v:
            if not dep or not NODE_NAME_PATTERN.match(dep):
                raise ValueError(f"依赖节点名称非法: {dep}")
        return v


class DAG(BaseModel):
    """DAG 模型"""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[DAGNode] = Field(default_factory=list)
    status: DAGStatus = DAGStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None  # 毫秒
    progress: float = 0.0  # 0-100

    @field_validator('name')
    @classmethod
    def validate_dag_name(cls, v: str) -> str:
        """验证 DAG 名称"""
        if not v:
            raise ValueError("DAG 名称不能为空")
        if not NODE_NAME_PATTERN.match(v):
            raise ValueError("DAG 名称只允许字母、数字、下划线、连字符")
        return v


class DAGListResponse(BaseModel):
    """DAG 列表响应"""
    dags: List[DAG]
    total: int


class DAGRunRequest(BaseModel):
    """DAG 执行请求"""
    dag_id: str
    params: Dict[str, Any] = {}

    @field_validator('dag_id')
    @classmethod
    def validate_dag_id(cls, v: str) -> str:
        """验证 DAG ID"""
        if not v:
            raise ValueError("DAG ID 不能为空")
        if not NODE_NAME_PATTERN.match(v):
            raise ValueError("DAG ID 只允许字母、数字、下划线、连字符")
        return v


class DAGStatusResponse(BaseModel):
    """DAG 状态响应"""
    dag_id: str
    status: DAGStatus
    progress: float
    nodes: List[DAGNode]


# 兼容旧代码命名（NodeStatus）
NodeStatus = DAGNodeStatus


class DAGExecution(BaseModel):
    """DAG 执行实例（运行态）"""
    id: str = Field(default_factory=lambda: uuid4().hex)
    dag_id: str
    status: DAGStatus = DAGStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0
    nodes: Dict[str, DAGNode] = Field(default_factory=dict)
    error: Optional[str] = None
