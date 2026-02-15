"""
AR监控路由模块
提供AR节点管理和状态查询接口
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/ar-legacy", tags=["ar"])


def _get_ar_monitor(request: Request):
    """获取AR监控器实例"""
    monitor = getattr(request.app.state, "ar_monitor", None)
    if monitor is None:
        raise RuntimeError("AR monitor not initialized")
    return monitor


@router.get("/nodes")
async def get_nodes(request: Request) -> Dict[str, Any]:
    """
    获取所有AR节点列表
    
    返回:
    - nodes: 节点列表
    - total: 节点总数
    - online_count: 在线节点数
    - offline_count: 离线节点数
    """
    try:
        monitor = _get_ar_monitor(request)
        nodes = monitor.get_nodes()
        
        return {
            "nodes": [node.model_dump() for node in nodes],
            "total": len(nodes),
            "online_count": sum(1 for n in nodes if n.status == "online"),
            "offline_count": sum(1 for n in nodes if n.status == "offline")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取节点列表失败: {str(e)}")


@router.get("/nodes/{node_id}")
async def get_node_detail(request: Request, node_id: str) -> Dict[str, Any]:
    """
    获取指定节点的详细信息
    
    参数:
    - node_id: 节点ID
    
    返回:
    - 节点详细信息
    """
    try:
        monitor = _get_ar_monitor(request)
        node = monitor.get_node(node_id)
        
        if node is None:
            raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
        
        return node.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取节点详情失败: {str(e)}")


@router.post("/nodes/{node_id}/heartbeat")
async def heartbeat(request: Request, node_id: str) -> Dict[str, str]:
    """
    接收节点心跳
    
    参数:
    - node_id: 节点ID
    
    返回:
    - status: 状态
    """
    try:
        monitor = _get_ar_monitor(request)
        monitor.update_heartbeat(node_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"心跳更新失败: {str(e)}")


@router.get("/status")
async def get_ar_status(request: Request) -> Dict[str, Any]:
    """
    获取AR系统整体状态
    
    返回:
    - status: 系统状态
    - active_nodes: 活跃节点数
    - total_nodes: 总节点数
    """
    try:
        monitor = _get_ar_monitor(request)
        nodes = monitor.get_nodes()
        
        return {
            "status": "healthy" if any(
                n.status == "online" for n in nodes
            ) else "degraded",
            "active_nodes": sum(1 for n in nodes if n.status == "online"),
            "total_nodes": len(nodes),
            "timestamp": __import__(
                'datetime'
            ).datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/nodes/{node_id}/restart")
async def restart_node(request: Request, node_id: str) -> Dict[str, str]:
    """
    重启指定节点
    
    参数:
    - node_id: 节点ID
    
    返回:
    - status: 操作状态
    - message: 操作结果消息
    """
    try:
        monitor = _get_ar_monitor(request)
        success = monitor.restart_node(node_id)
        
        if success:
            return {"status": "success", "message": f"节点 {node_id} 重启命令已发送"}
        else:
            raise HTTPException(status_code=400, detail=f"节点 {node_id} 重启失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重启节点失败: {str(e)}")
