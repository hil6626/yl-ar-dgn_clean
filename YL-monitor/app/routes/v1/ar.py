"""
API v1 - AR 路由

功能:
- AR 节点监控接口
- 统一的响应格式

作者: AI Assistant
版本: v1.0.0
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, HTTPException

from app.middleware import create_success_response

router = APIRouter(prefix="/ar", tags=["AR"])


def _get_monitor(request: Request):
    monitor = getattr(request.app.state, "ar_monitor", None)
    if monitor is None:
        raise RuntimeError("ar monitor not initialized")
    return monitor


@router.get("/nodes")
async def get_nodes(request: Request):
    """
    获取所有 AR 节点
    """
    monitor = _get_monitor(request)
    nodes = monitor.get_nodes()
    
    # Convert ARNode objects to dictionaries
    node_dicts = []
    for n in nodes.nodes:
        node_dict = {
            "id": n.id,
            "name": n.name,
            "type": n.type,
            "status": n.status.value if hasattr(n.status, "value") else str(n.status),
            "ip_address": n.ip_address,
            "port": n.port,
            "resources": n.resources,
            "current_task": n.current_task,
            "last_heartbeat": n.last_heartbeat.isoformat() if n.last_heartbeat else None,
            "uptime": n.uptime
        }
        node_dicts.append(node_dict)
    
    return {
        "status": "ok",
        "total": nodes.total,
        "online": nodes.online_count,
        "offline": nodes.offline_count,
        "nodes": node_dicts
    }


@router.get("/status")
async def get_status(request: Request, node_id: str):
    """
    获取特定节点状态
    """
    monitor = _get_monitor(request)
    nodes = monitor.get_nodes()
    
    # Find node by id in the nodes list
    node = None
    for n in nodes.nodes:
        if n.id == node_id:
            node = n
            break
    
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    
    return {
        "id": node.id,
        "name": node.name,
        "type": node.type,
        "status": node.status.value if hasattr(node.status, 'value') else str(node.status),
        "ip_address": node.ip_address,
        "port": node.port,
        "resources": node.resources,
        "current_task": node.current_task,
        "last_heartbeat": node.last_heartbeat.isoformat() + "Z" if node.last_heartbeat else None,
        "uptime": node.uptime
    }


@router.get("/performance")
async def get_performance(request: Request):
    """
    获取渲染性能数据
    """
    monitor = _get_monitor(request)
    nodes = monitor.get_nodes()
    
    # Calculate totals from resources
    total_cpu = sum(n.resources.get("cpu", 0) for n in nodes.nodes)
    total_memory = sum(n.resources.get("memory", 0) for n in nodes.nodes)
    total_gpu = sum(n.resources.get("gpu", 0) for n in nodes.nodes)
    
    return create_success_response(
        data={
            "total_cpu": total_cpu,
            "total_memory": total_memory,
            "total_gpu": total_gpu,
            "node_count": len(nodes.nodes)
        },
        message="Performance data retrieved"
    )


@router.post("/heartbeat")
async def heartbeat(request: Request, node_id: str):
    """
    更新节点心跳
    """
    monitor = _get_monitor(request)
    monitor.update_node_heartbeat(node_id)
    return create_success_response(message="Heartbeat updated")


@router.get("/scenes")
async def get_scenes(request: Request):
    """
    获取场景列表
    """
    monitor = _get_monitor(request)
    scenes = monitor.get_scenes()
    return create_success_response(
        data={"scenes": scenes},
        message="Scenes retrieved"
    )
