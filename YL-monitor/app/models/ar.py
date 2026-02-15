# AR 模型定义
# 包含 ARNode、ARStatus 等模型
# 注意：AR 模块为占位符实现，后续根据实际需求完善

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class ARStatus(str, Enum):
    """AR 状态枚举"""
    IDLE = "idle"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ERROR = "error"


class ARNodeStatus(str, Enum):
    """AR 节点状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class ARNode(BaseModel):
    """AR 节点模型"""
    id: str
    name: str
    type: str = "render"
    status: ARNodeStatus = ARNodeStatus.OFFLINE
    ip_address: Optional[str] = None
    port: Optional[int] = None
    resources: Dict[str, Any] = Field(default_factory=dict)  # CPU、内存、GPU 等
    current_task: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    uptime: Optional[float] = None  # 秒
    created_at: datetime = Field(default_factory=datetime.now)


class ARScene(BaseModel):
    """AR 场景模型"""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[ARNode] = Field(default_factory=list)
    status: ARStatus = ARStatus.IDLE
    progress: float = 0.0  # 0-100
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ARNodesResponse(BaseModel):
    """AR 节点列表响应"""
    nodes: List[ARNode]
    total: int
    online_count: int
    offline_count: int


class ARStatusResponse(BaseModel):
    """AR 状态响应"""
    scene_id: str
    status: ARStatus
    progress: float
    nodes: List[ARNode]
    total_nodes: int
    online_nodes: int
