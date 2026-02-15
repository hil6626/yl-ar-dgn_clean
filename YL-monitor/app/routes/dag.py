"""
DAG流水线路由模块
提供DAG定义查询和执行控制接口
"""

from fastapi import APIRouter, WebSocket, HTTPException
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1/dag", tags=["dag"])


@router.get("/definition")
async def get_dag_definition() -> Dict[str, Any]:
    """
    获取DAG定义（节点和连线）
    
    返回:
    - nodes: 节点列表 {id, name, type, x, y, status}
    - edges: 连线列表 {from, to}
    """
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        return await engine.get_definition()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取DAG定义失败: {str(e)}")


@router.post("/execute")
async def execute_dag() -> Dict[str, Any]:
    """
    执行整个DAG
    """
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        execution_id = await engine.execute_all()
        
        return {
            "success": True,
            "execution_id": execution_id,
            "message": "DAG执行已启动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行DAG失败: {str(e)}")


@router.post("/nodes/{node_id}/execute")
async def execute_node(node_id: str) -> Dict[str, Any]:
    """
    执行单个节点
    """
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        result = await engine.execute_node(node_id)
        
        return {
            "success": result.get("success", False),
            "output": result.get("output", ""),
            "duration": result.get("duration", 0),
            "node_id": node_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行节点失败: {str(e)}")


@router.get("/executions")
async def get_executions(limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取最近的DAG执行记录
    """
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        return await engine.get_recent_executions(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行记录失败: {str(e)}")


@router.get("/executions/{execution_id}")
async def get_execution_detail(execution_id: str) -> Dict[str, Any]:
    """
    获取指定执行的详细信息
    """
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        detail = await engine.get_execution_detail(execution_id)
        
        if not detail:
            raise HTTPException(status_code=404, detail="执行记录不存在")
        
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行详情失败: {str(e)}")


@router.websocket("/ws")
async def dag_websocket(websocket: WebSocket):
    """
    DAG实时状态WebSocket
    
    推送节点状态变更、执行进度等实时事件
    """
    await websocket.accept()
    
    try:
        from app.services.dag_engine import DAGEngine
        
        engine = DAGEngine()
        
        # 订阅DAG事件流
        async for event in engine.event_stream():
            await websocket.send_json({
                "type": event.get("type"),
                "data": event.get("data"),
                "timestamp": event.get("timestamp")
            })
            
    except Exception as e:
        print(f"DAG WebSocket错误: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
