"""
脚本管理路由模块
提供脚本列表查询、执行控制和轮询配置接口
"""

from fastapi import APIRouter, WebSocket, HTTPException, Query
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/v1/scripts", tags=["scripts"])


@router.get("/categories")
async def get_script_categories() -> List[Dict[str, Any]]:
    """
    获取所有脚本分类
    """
    try:
        from app.services.scripts_scanner import get_scripts_scanner
        
        scanner = get_scripts_scanner()
        return scanner.get_categories()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")


@router.get("")
async def get_scripts(
    category: Optional[str] = Query(None, description="按分类筛选")
) -> Dict[str, Any]:
    """
    获取所有脚本列表
    
    参数:
    - category: 可选，按分类筛选
    
    返回脚本卡片数据，包含:
    - scripts: 脚本列表数组
    - total: 总数
    """
    try:
        from app.services.scripts_scanner import get_scripts_scanner
        from app.services.script_metadata import get_script_metadata_manager
        
        scanner = get_scripts_scanner()
        manager = get_script_metadata_manager()
        
        # 扫描所有脚本
        all_scripts = scanner.scan_all()
        
        # 如果指定了分类，进行筛选
        if category:
            all_scripts = [s for s in all_scripts if s.category == category]
        
        # 获取状态信息
        all_status = await manager.get_all_status()
        
        # 组装返回数据
        scripts_list = []
        for script in all_scripts:
            status = all_status.get(script.id)
            scripts_list.append({
                "id": script.id,
                "name": script.name,
                "filename": script.filename,
                "description": script.description,
                "category": script.category,
                "subcategory": script.subcategory,
                "script_type": script.script_type,
                "tags": script.tags,
                "path": script.path,
                "parameters": script.parameters,
                "timeout": script.timeout,
                "enabled": script.enabled,
                "status": {
                    "current_status": status.status if status else "idle",
                    "is_running": status.is_running if status else False,
                    "execution_count": status.execution_count if status else 0,
                    "success_count": status.success_count if status else 0,
                    "fail_count": status.fail_count if status else 0,
                    "last_execution": status.last_execution if status else None,
                    "last_output": status.last_output if status else ""
                }
            })
        
        # 返回前端期望的格式
        return {
            "scripts": scripts_list,
            "total": len(scripts_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取脚本列表失败: {str(e)}")


@router.post("/batch-execute")
async def batch_execute_scripts(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    批量执行多个脚本
    
    参数:
    - script_ids: 要执行的脚本ID列表
    - parallel: 是否并行执行（默认True）
    - parameters: 可选，传递给脚本的参数
    """
    try:
        from app.services.scripts_scanner import get_scripts_scanner
        from app.services.script_metadata import get_script_metadata_manager
        
        scanner = get_scripts_scanner()
        manager = get_script_metadata_manager()
        
        script_ids = request.get("script_ids", [])
        parallel = request.get("parallel", True)
        parameters = request.get("parameters", {})
        
        if not script_ids:
            raise HTTPException(status_code=400, detail="未指定要执行的脚本")
        
        # 验证所有脚本存在
        for script_id in script_ids:
            script = scanner.get_script(script_id)
            if not script:
                raise HTTPException(status_code=404, detail=f"脚本不存在: {script_id}")
        
        # 创建执行记录
        execution_records = []
        for script_id in script_ids:
            record = await manager.create_execution(script_id, parameters)
            execution_records.append({
                "script_id": script_id,
                "execution_id": record.id,
                "status": "pending"
            })
        
        # TODO: 实际执行逻辑（这里简化处理）
        # 实际应该调用脚本执行器来执行
        
        return {
            "success": True,
            "message": f"已创建 {len(script_ids)} 个执行任务",
            "executions": execution_records,
            "parallel": parallel
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量执行失败: {str(e)}")


@router.post("/{script_id}/execute")
async def execute_script(
    script_id: str,
    request: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    执行指定脚本
    
    参数:
    - parameters: 可选，传递给脚本的参数
    """
    try:
        from app.services.scripts_scanner import get_scripts_scanner
        from app.services.script_metadata import get_script_metadata_manager
        
        scanner = get_scripts_scanner()
        manager = get_script_metadata_manager()
        
        # 验证脚本存在
        script = scanner.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail=f"脚本不存在: {script_id}")
        
        # 获取参数
        parameters = (request or {}).get("parameters", {})
        
        # 创建执行记录
        record = await manager.create_execution(script_id, parameters)
        
        # TODO: 实际执行逻辑
        # 这里简化处理，实际应该调用脚本执行器
        
        return {
            "success": True,
            "execution_id": record.id,
            "script_id": script_id,
            "script_name": script.name,
            "status": "pending",
            "message": "执行已创建，请通过WebSocket监控进度"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行脚本失败: {str(e)}")


@router.post("/{script_id}/stop")
async def stop_script(script_id: str) -> Dict[str, Any]:
    """
    停止正在执行的脚本
    """
    try:
        from app.services.scripts_runner import ScriptsRunner
        
        runner = ScriptsRunner()
        success = await runner.stop(script_id)
        
        return {
            "success": success,
            "message": "脚本已停止" if success else "停止失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止脚本失败: {str(e)}")


@router.post("/{script_id}/polling")
async def set_polling_config(
    script_id: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    设置脚本轮询配置
    
    参数:
    - enabled: 是否启用轮询
    - interval: 轮询间隔（秒）
    """
    try:
        from app.services.scripts_runner import ScriptsRunner
        
        runner = ScriptsRunner()
        await runner.set_polling(
            script_id,
            config.get("enabled", False),
            config.get("interval", 300)
        )
        
        return {
            "success": True,
            "message": f"轮询已{'启用' if config.get('enabled') else '禁用'}",
            "script_id": script_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置轮询失败: {str(e)}")


@router.get("/{script_id}/history")
async def get_script_history(
    script_id: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    获取脚本执行历史
    """
    try:
        from app.services.script_metadata import get_script_metadata_manager
        
        manager = get_script_metadata_manager()
        history = await manager.get_script_history(script_id, limit)
        
        return [
            {
                "id": record.id,
                "status": record.status,
                "output": record.output,
                "error": record.error,
                "returncode": record.returncode,
                "duration": record.duration,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "parameters": record.parameters
            }
            for record in history
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.get("/{script_id}/logs")
async def get_script_logs(
    script_id: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    获取脚本执行日志
    """
    try:
        from app.services.scripts_runner import ScriptsRunner
        
        runner = ScriptsRunner()
        return await runner.get_logs(script_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")


@router.get("/statistics")
async def get_scripts_statistics() -> Dict[str, Any]:
    """
    获取脚本执行统计信息
    """
    try:
        from app.services.script_metadata import get_script_metadata_manager
        
        manager = get_script_metadata_manager()
        stats = await manager.get_statistics()
        
        return {
            "total_executions": stats["total_executions"],
            "success_count": stats["success_count"],
            "fail_count": stats["fail_count"],
            "running_count": stats["running_count"],
            "success_rate": round(stats["success_rate"], 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.websocket("/{script_id}/logs")
async def script_logs_websocket(websocket: WebSocket, script_id: str):
    """
    脚本实时日志WebSocket
    """
    await websocket.accept()
    
    try:
        from app.services.scripts_runner import ScriptsRunner
        
        runner = ScriptsRunner()
        
        # 发送历史日志
        history = await runner.get_logs(script_id, limit=50)
        for log in history:
            await websocket.send_json({
                "type": "history",
                "message": log.get("message", ""),
                "timestamp": log.get("timestamp", "")
            })
        
        # 实时推送新日志
        async for log in runner.log_stream(script_id):
            await websocket.send_json({
                "type": "realtime",
                "message": log.get("message", ""),
                "timestamp": log.get("timestamp", "")
            })
            
    except Exception as e:
        print(f"Scripts WebSocket错误: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
