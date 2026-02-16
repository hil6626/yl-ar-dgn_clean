"""
统一监控路由模块
提供用户界面、后端API、DAG流水线的统一监控
"""

from fastapi import APIRouter

from . import ui, api, dag

router = APIRouter(prefix="/monitor", tags=["Monitor"])

# 包含子路由 - 统一监控路由
# 用户界面监控: /api/v1/monitor/ui/*
router.include_router(ui.router, prefix="/ui")

# 后端API监控: /api/v1/monitor/api/*
router.include_router(api.router, prefix="/api")

# DAG流水线监控: /api/v1/monitor/dag/*
router.include_router(dag.router, prefix="/dag")

__all__ = ["router"]
