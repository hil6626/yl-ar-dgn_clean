"""
后端API监控路由
监控 AR-backend 服务状态
"""

from fastapi import APIRouter, Request
from typing import Dict, Any, List
from datetime import datetime
import aiohttp

router = APIRouter(tags=["API Monitor"])

AR_BACKEND_URL = "http://0.0.0.0:5501"


@router.get("/status")
async def get_api_status(request: Request) -> Dict[str, Any]:
    """
    获取 AR-backend 整体状态
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{AR_BACKEND_URL}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "ok",
                        "timestamp": datetime.utcnow().isoformat(),
                        "component": "api",
                        "data": {
                            "service_health": "healthy",
                            "details": data
                        }
                    }
                else:
                    return {
                        "status": "warning",
                        "timestamp": datetime.utcnow().isoformat(),
                        "component": "api",
                        "data": {
                            "service_health": "degraded",
                            "http_status": response.status
                        }
                    }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "component": "api",
            "message": str(e),
            "data": {
                "service_health": "unhealthy"
            }
        }


@router.get("/endpoints")
async def get_api_endpoints(request: Request) -> Dict[str, Any]:
    """
    获取 API 端点状态
    """
    endpoints = [
        {"path": "/health", "method": "GET", "description": "健康检查"},
        {"path": "/status", "method": "GET", "description": "服务状态"},
        {"path": "/metrics", "method": "GET", "description": "性能指标"}
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{AR_BACKEND_URL}{endpoint['path']}"
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    results.append({
                        **endpoint,
                        "status": "ok" if response.status == 200 else "error",
                        "http_status": response.status,
                        "response_time_ms": 0  # 简化处理
                    })
        except Exception as e:
            results.append({
                **endpoint,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "api",
        "data": {
            "endpoints": results
        }
    }


@router.get("/performance")
async def get_api_performance(request: Request) -> Dict[str, Any]:
    """
    获取 API 性能指标
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{AR_BACKEND_URL}/metrics",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    metrics = await response.json()
                    return {
                        "status": "ok",
                        "timestamp": datetime.utcnow().isoformat(),
                        "component": "api",
                        "data": {
                            "performance": metrics
                        }
                    }
                else:
                    return {
                        "status": "warning",
                        "timestamp": datetime.utcnow().isoformat(),
                        "component": "api",
                        "data": {
                            "performance": {}
                        }
                    }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "component": "api",
            "message": str(e),
            "data": {
                "performance": {}
            }
        }


@router.get("/modules")
async def get_api_modules(request: Request) -> Dict[str, Any]:
    """
    获取 AR-backend 模块状态
    """
    modules = [
        {"id": "video", "name": "视频处理", "icon": "🎥"},
        {"id": "audio", "name": "音频处理", "icon": "🔊"},
        {"id": "face", "name": "人脸合成", "icon": "👤"},
        {"id": "virtual_cam", "name": "虚拟摄像头", "icon": "📹"}
    ]
    
    # 从状态端点获取模块状态
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{AR_BACKEND_URL}/status",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    status_data = await response.json()
                    # 根据实际返回更新模块状态
                    for module in modules:
                        module["status"] = "ok"  # 简化处理
                else:
                    for module in modules:
                        module["status"] = "unknown"
    except Exception:
        for module in modules:
            module["status"] = "error"
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "component": "api",
        "data": {
            "modules": modules
        }
    }
