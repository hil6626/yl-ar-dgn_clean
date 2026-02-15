"""
API v1 版本路由

功能:
- 提供标准化的 API v1 版本路由
- 统一的响应格式
- 请求 ID 和限流支持

作者: AI Assistant
版本: 1.0.0
"""

from fastapi import APIRouter

# 创建 v1 主路由
router = APIRouter(prefix="/api/v1", tags=["API v1"])

# 导入子路由
from app.routes.v1 import dashboard, scripts, dag, ar, alerts, metrics, alert_rules, alerts_history, metrics_history, intelligent_alert

# 注册子路由
router.include_router(dashboard.router)
router.include_router(scripts.router)
router.include_router(dag.router)
router.include_router(ar.router)
router.include_router(alerts.router)
router.include_router(metrics.router)
router.include_router(alert_rules.router)
router.include_router(alerts_history.router)
router.include_router(metrics_history.router)
router.include_router(intelligent_alert.router)

__all__ = ["router"]
