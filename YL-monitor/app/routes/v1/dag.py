"""
API v1 - DAG 路由

功能:
- DAG 流水线管理接口
- 统一的响应格式

作者: AI Assistant
版本: v1.0.0
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, Query, HTTPException
from pydantic import BaseModel

from app.models.dag import DAGRunRequest
from app.middleware import create_success_response

router = APIRouter(prefix="/dag", tags=["DAG"])


class DAGListItem(BaseModel):
    """DAG 列表项"""
    id: str
    name: str
    description: Optional[str] = None
    nodes: int
    edges: int


class DAGListResponse(BaseModel):
    """DAG 列表响应"""
    dags: list[DAGListItem]


class DAGRunResponse(BaseModel):
    """DAG 执行响应"""
    status: str
    execution_id: str
    dag_id: str


class DAGNodeStatus(BaseModel):
    """DAG 节点状态"""
    id: str
    name: str
    status: str
    progress: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None


class DAGExecutionStatus(BaseModel):
    """DAG 执行状态响应"""
    dag_id: str
    execution_id: str
    status: str
    progress: float
    nodes: list[Dict[str, Any]]
    error: Optional[str] = None


def _get_engine(request: Request):
    engine = getattr(request.app.state, "dag_engine", None)
    if engine is None:
        raise RuntimeError("dag engine not initialized")
    return engine


@router.get("/list", response_model=DAGListResponse)
async def list_dags(request: Request):
    """
    获取 DAG 列表
    """
    engine = _get_engine(request)
    dag_list = engine.list_dags()
    
    # 转换为 DAGListItem 格式
    items = []
    for dag_data in dag_list:
        nodes = dag_data.get("nodes", [])
        # 计算 edges 数量（从节点的 depends_on 推导）
        edge_count = sum(len(n.get("depends_on", [])) for n in nodes)
        
        items.append(DAGListItem(
            id=dag_data.get("id", ""),
            name=dag_data.get("name", ""),
            description=dag_data.get("description", ""),
            nodes=len(nodes),
            edges=edge_count
        ))
    
    return DAGListResponse(dags=items)


@router.get("/detail")
async def get_dag_detail(request: Request, dag_id: str):
    """
    获取 DAG 详细定义
    """
    engine = _get_engine(request)
    dag = engine.get_dag(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="dag not found")
    return create_success_response(
        data=dag.model_dump(),
        message="DAG detail retrieved"
    )


@router.post("/run", response_model=DAGRunResponse)
async def run_dag(request: Request, body: DAGRunRequest):
    """
    执行 DAG 流水线
    """
    engine = _get_engine(request)
    execution = await engine.run_dag(body.dag_id, body.params)
    if not execution:
        raise HTTPException(status_code=404, detail="dag not found")
    
    return DAGRunResponse(
        status="running",
        execution_id=execution.id,
        dag_id=execution.dag_id
    )


@router.get("/status", response_model=DAGExecutionStatus)
async def get_status(request: Request, execution_id: str):
    """
    获取 DAG 执行状态
    """
    engine = _get_engine(request)
    execution = engine.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="execution not found")
    
    return DAGExecutionStatus(
        dag_id=execution.dag_id,
        execution_id=execution.id,
        status=execution.status.value,
        progress=execution.progress,
        nodes=[n.model_dump() for n in execution.nodes.values()],
        error=execution.error
    )


@router.post("/stop")
async def stop_dag(request: Request, execution_id: str):
    """
    停止 DAG 执行
    """
    engine = _get_engine(request)
    ok = engine.stop_execution(execution_id)
    if ok:
        return create_success_response(message=f"Execution {execution_id} stopped")
    raise HTTPException(status_code=404, detail="execution not found or already completed")
