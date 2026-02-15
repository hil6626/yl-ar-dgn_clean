"""
API文档路由模块
提供6栏验收矩阵和冒泡检测接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1/api-doc", tags=["api-doc"])


@router.get("/validation-matrix")
async def get_validation_matrix() -> List[Dict[str, Any]]:
    """
    获取API文档验证矩阵（6栏结构）
    
    返回统一接口映射表，包含:
    - 前端映射
    - 功能说明
    - 后端接口
    - 自动化脚本
    - DAG节点
    - 冒泡检测状态
    - 完成度
    """
    try:
        from app.services.api_doc_service import APIDocService
        
        service = APIDocService()
        return await service.get_validation_matrix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验证矩阵失败: {str(e)}")


@router.get("/bubble-check/{function_id}")
async def check_bubble_status(function_id: str) -> Dict[str, Any]:
    """
    检查指定功能的冒泡状态
    
    返回:
    - status: danger/warning/success
    - message: 状态说明
    - issues: 问题列表
    - priority: 优先级
    """
    try:
        from app.services.api_doc_service import APIDocService
        
        service = APIDocService()
        return await service.check_bubble_status(function_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"冒泡检测失败: {str(e)}")


@router.get("/stats")
async def get_api_doc_stats() -> Dict[str, Any]:
    """
    获取API文档统计信息
    
    返回:
    - total: 总功能数
    - completed: 已完成数
    - incomplete: 未完成数
    - rate: 完成率
    - api_completed: API配置完成数
    - script_completed: 脚本配置完成数
    - dag_completed: DAG接入完成数
    """
    try:
        from app.services.api_doc_service import APIDocService
        
        service = APIDocService()
        return await service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/functions/{function_id}")
async def get_function_detail(function_id: str) -> Dict[str, Any]:
    """
    获取指定功能的详细信息
    
    返回完整的功能配置和依赖关系
    """
    try:
        from app.services.api_doc_service import APIDocService
        
        service = APIDocService()
        detail = await service.get_function_detail(function_id)
        
        if not detail:
            raise HTTPException(status_code=404, detail="功能不存在")
        
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能详情失败: {str(e)}")


@router.post("/functions/{function_id}/validate")
async def validate_function(function_id: str) -> Dict[str, Any]:
    """
    验证指定功能的配置完整性
    
    返回验证结果和建议
    """
    try:
        from app.services.api_doc_service import APIDocService
        
        service = APIDocService()
        return await service.validate_function(function_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/scripts")
async def get_scripts_for_api_doc() -> Dict[str, Any]:
    """
    获取脚本管理信息（用于API文档页面展示）
    
    返回:
    - scripts: 脚本列表（按分类组织）
    - categories: 分类信息
    - total: 脚本总数
    """
    try:
        from app.services.scripts_scanner import get_scripts_scanner
        
        scanner = get_scripts_scanner()
        all_scripts = scanner.scan_all()
        categories = scanner.get_categories()
        
        # 按分类组织脚本
        scripts_by_category = {}
        for script in all_scripts:
            cat = script.category
            if cat not in scripts_by_category:
                scripts_by_category[cat] = []
            scripts_by_category[cat].append({
                "id": script.id,
                "name": script.name,
                "filename": script.filename,
                "description": script.description,
                "script_type": script.script_type,
                "tags": script.tags,
                "enabled": script.enabled
            })
        
        return {
            "scripts": scripts_by_category,
            "categories": categories,
            "total": len(all_scripts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取脚本信息失败: {str(e)}")


@router.get("/endpoints")
async def get_api_endpoints() -> List[Dict[str, Any]]:
    """
    获取API端点列表（用于API文档页面展示）
    
    返回所有可用的API端点信息，按模块组织
    """
    return [
        {
            "module": "脚本管理",
            "icon": "📜",
            "expanded": True,
            "endpoints": [
                {
                    "id": "scripts-list",
                    "method": "GET",
                    "path": "/api/v1/scripts",
                    "name": "获取脚本列表",
                    "description": "获取所有自动化脚本列表，支持按分类筛选",
                    "params": [
                        {"name": "category", "type": "string", "required": False, "description": "按分类筛选脚本"}
                    ],
                    "response": {
                        "status": 200,
                        "example": {
                            "scripts": [{"id": "script-001", "name": "系统监控脚本", "category": "system-monitor"}],
                            "total": 95
                        }
                    }
                },
                {
                    "id": "scripts-categories",
                    "method": "GET",
                    "path": "/api/v1/scripts/categories",
                    "name": "获取脚本分类",
                    "description": "获取所有脚本分类信息",
                    "params": [],
                    "response": {
                        "status": 200,
                        "example": {
                            "categories": [
                                {"id": "system-monitor", "name": "系统监控", "count": 5}
                            ]
                        }
                    }
                },
                {
                    "id": "script-execute",
                    "method": "POST",
                    "path": "/api/v1/scripts/{script_id}/execute",
                    "name": "执行脚本",
                    "description": "执行指定的自动化脚本",
                    "params": [
                        {"name": "script_id", "type": "string", "required": True, "description": "脚本ID", "in": "path"}
                    ],
                    "body": {"parameters": {}},
                    "response": {
                        "status": 200,
                        "example": {
                            "success": True,
                            "execution_id": "exec-001",
                            "status": "pending"
                        }
                    }
                }
            ]
        },
        {
            "module": "API文档",
            "icon": "📚",
            "expanded": False,
            "endpoints": [
                {
                    "id": "api-validation-matrix",
                    "method": "GET",
                    "path": "/api/v1/api-doc/validation-matrix",
                    "name": "获取验证矩阵",
                    "description": "获取API文档验证矩阵（6栏结构）",
                    "params": [],
                    "response": {"status": 200}
                },
                {
                    "id": "api-scripts",
                    "method": "GET",
                    "path": "/api/v1/api-doc/scripts",
                    "name": "获取脚本信息",
                    "description": "获取API文档页面用的脚本信息",
                    "params": [],
                    "response": {"status": 200}
                }
            ]
        },
        {
            "module": "系统监控",
            "icon": "📊",
            "expanded": False,
            "endpoints": [
                {
                    "id": "health-check",
                    "method": "GET",
                    "path": "/api/health",
                    "name": "健康检查",
                    "description": "系统健康状态检查",
                    "params": [],
                    "response": {
                        "status": 200,
                        "example": {"status": "healthy", "version": "1.0.6"}
                    }
                },
                {
                    "id": "system-summary",
                    "method": "GET",
                    "path": "/api/summary",
                    "name": "系统摘要",
                    "description": "获取系统整体状态摘要",
                    "params": [],
                    "response": {
                        "status": 200,
                        "example": {
                            "status": "running",
                            "services": {"fastapi": "running", "scripts_runner": "running"}
                        }
                    }
                }
            ]
        }
    ]
