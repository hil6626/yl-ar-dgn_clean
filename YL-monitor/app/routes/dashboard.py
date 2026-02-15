"""
Dashboard API路由模块
提供仪表盘数据查询接口
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.services.dashboard_monitor import DashboardMonitor
from app.auth.deps import get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview")
async def get_overview(
    monitor: DashboardMonitor = Depends(),
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取仪表盘概览数据
    
    返回:
    - api: API接口统计 {total, healthy, trend}
    - nodes: DAG节点统计 {total, running, active%}
    - scripts: 脚本执行统计 {total, active, trend}
    - completion: 整体完成度百分比
    """
    try:
        return await monitor.get_overview_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概览数据失败: {str(e)}")


@router.get("/function-matrix")
async def get_function_matrix(
    monitor: DashboardMonitor = Depends()
) -> List[Dict[str, Any]]:
    """
    获取功能完成度矩阵
    
    返回功能列表，每项包含:
    - id: 功能ID
    - name: 功能名称
    - description: 功能描述
    - api: {exists, path, method}
    - script: {exists, name}
    - dag: {registered, node_id}
    - monitor: {enabled}
    - completion: 完成度百分比
    """
    try:
        return await monitor.get_function_matrix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能矩阵失败: {str(e)}")




@router.get("/test-monitor")
async def get_api_test_monitor():
    """
    获取API测试监控页面
    """
    from fastapi.responses import HTMLResponse
    from pathlib import Path
    
    template_path = (
        Path(__file__).parent.parent.parent /
        "templates" / "api_test_monitor.html"
    )
    
    if not template_path.exists():
        raise HTTPException(
            status_code=404, detail="测试监控页面模板不存在"
        )
    
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return HTMLResponse(content=content)
