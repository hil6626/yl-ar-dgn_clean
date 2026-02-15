"""
YL-Monitor FastAPI 应用主入口

- 应用初始化与配置
- 路由注册
- 中间件配置
- 启动/关闭钩子
- 全局异常处理
"""

from __future__ import annotations

# 修复模块导入路径问题 - 必须在其他导入之前执行
# 当从 app/ 目录直接运行时，将父目录加入 sys.path 使 'app' 模块可被找到
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yl_monitor")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("YL-Monitor 启动中...")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # 初始化脚本执行器
    try:
        from app.services.scripts_runner import ScriptsRunner
        scripts_runner = ScriptsRunner(
            scripts_dir=os.getenv("YL_MONITOR_SCRIPTS_DIR", "scripts"),
            logs_dir=os.getenv("YL_MONITOR_LOGS_DIR", "logs")
        )
        await scripts_runner.load_scripts()
        app.state.scripts_runner = scripts_runner
        logger.info(f"✓ 脚本执行器已初始化，加载了 {len(scripts_runner.scripts)} 个脚本")
    except Exception as e:
        logger.error(f"✗ 脚本执行器初始化失败: {e}")
        app.state.scripts_runner = None
    
    # 初始化 DAG 引擎
    try:
        from app.services.dag_engine import DAGEngine
        dag_engine = DAGEngine(
            dags_dir=os.getenv("YL_MONITOR_DAGS_DIR", "dags"),
            scripts_runner=getattr(app.state, "scripts_runner", None),
            concurrency=int(os.getenv("YL_MONITOR_DAG_CONCURRENCY", "6"))
        )
        await dag_engine.load_dags()
        app.state.dag_engine = dag_engine
        logger.info(f"✓ DAG 引擎已初始化，加载了 {len(dag_engine.dags)} 个 DAG")
    except Exception as e:
        logger.error(f"✗ DAG 引擎初始化失败: {e}")
        app.state.dag_engine = None
    
    # 初始化 AR 监控器
    try:
        from app.services.ar_monitor import ARMonitor
        ar_monitor = ARMonitor()
        app.state.ar_monitor = ar_monitor
        await ar_monitor.start_monitoring()
        logger.info("✓ AR 监控器已启动")
    except Exception as e:
        logger.error(f"✗ AR 监控器启动失败: {e}")
        app.state.ar_monitor = None
    
    # 初始化告警服务
    try:
        from app.services.alert_service import AlertService
        alert_service = AlertService()
        app.state.alert_service = alert_service
        logger.info("✓ 告警服务已启动")
    except Exception as e:
        logger.warning(f"⚠ 告警服务启动失败（非关键）: {e}")
        app.state.alert_service = None
    
    # 初始化指标服务
    try:
        from app.services.metrics_service import MetricsService
        metrics_service = MetricsService()
        app.state.metrics_service = metrics_service
        logger.info("✓ 指标服务已启动")
    except Exception as e:
        logger.warning(f"⚠ 指标服务启动失败（非关键）: {e}")
        app.state.metrics_service = None
    
    # 初始化告警监控服务
    try:
        from app.services.alert_monitor import AlertMonitor
        alert_monitor = AlertMonitor()
        app.state.alert_monitor = alert_monitor
        await alert_monitor.start()
        logger.info("✓ 告警监控服务已启动")
    except Exception as e:
        logger.warning(f"⚠ 告警监控服务启动失败（非关键）: {e}")
        app.state.alert_monitor = None
    
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"YL-Monitor 启动完成！耗时 {elapsed:.2f} 秒")
    logger.info(f"访问地址: http://0.0.0.0:{os.getenv('YL_MONITOR_PORT', '5500')}")
    logger.info("=" * 60)
    
    yield
    
    # 关闭时执行
    logger.info("YL-Monitor 正在关闭...")
    
    # 停止 AR 监控器
    if hasattr(app.state, "ar_monitor") and app.state.ar_monitor:
        logger.info("正在停止 AR 监控器...")
    
    # 停止 DAG 引擎中的运行任务
    if hasattr(app.state, "dag_engine") and app.state.dag_engine:
        logger.info("正在停止 DAG 引擎...")
        for task in list(app.state.dag_engine._tasks.values()):
            task.cancel()
    
    # 停止脚本执行器
    if hasattr(app.state, "scripts_runner") and app.state.scripts_runner:
        logger.info("正在停止脚本执行器...")
        for proc in list(app.state.scripts_runner._running_procs.values()):
            try:
                proc.terminate()
            except Exception:
                pass
    
    # 停止告警监控服务
    if hasattr(app.state, "alert_monitor") and app.state.alert_monitor:
        logger.info("正在停止告警监控服务...")
        await app.state.alert_monitor.stop()
    
    logger.info("YL-Monitor 已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="YL-Monitor",
    description="夜灵多功能统一监控平台 - 系统监控、脚本管理、DAG编排、AR监控",
    version="1.0.6",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS
cors_origins = os.getenv("YL_MONITOR_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 GZip 压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求"""
    start_time = time.time()
    
    # 生成请求 ID
    request_id = f"{int(start_time * 1000)}-{id(request)}"
    request.state.request_id = request_id
    
    # 记录请求
    logger.debug(f"[{request_id}] {request.method} {request.url.path}")
    
    # 执行请求
    response = await call_next(request)
    
    # 计算耗时
    elapsed = time.time() - start_time
    
    # 记录响应
    status_code = response.status_code
    log_level = logging.INFO if status_code < 400 else logging.WARNING
    logger.log(log_level, f"[{request_id}] {request.method} {request.url.path} - {status_code} ({elapsed:.3f}s)")
    
    # 添加响应头
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed:.3f}"
    
    return response


# 挂载静态文件
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"✓ 静态文件目录已挂载: {static_dir}")

# 配置模板引擎
templates_dir = PROJECT_ROOT / "templates"
if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
    logger.info(f"✓ 模板目录已配置: {templates_dir}")
else:
    templates = None
    logger.warning(f"⚠ 模板目录不存在: {templates_dir}")


# 注册路由
def register_routers():
    """注册所有 API 路由"""
    
    # Dashboard 路由
    try:
        from app.routes import dashboard
        app.include_router(dashboard.router)
        logger.info("✓ Dashboard 路由已注册")
    except Exception as e:
        logger.error(f"✗ Dashboard 路由注册失败: {e}")
    
    # Scripts 路由
    try:
        from app.routes import scripts
        app.include_router(scripts.router)
        logger.info("✓ Scripts 路由已注册")
    except Exception as e:
        logger.error(f"✗ Scripts 路由注册失败: {e}")
    
    # DAG 路由
    try:
        from app.routes import dag
        app.include_router(dag.router)
        logger.info("✓ DAG 路由已注册")
    except Exception as e:
        logger.error(f"✗ DAG 路由注册失败: {e}")
    
    # AR 路由
    try:
        from app.routes import ar
        app.include_router(ar.router)
        logger.info("✓ AR 路由已注册")
    except Exception as e:
        logger.error(f"✗ AR 路由注册失败: {e}")
    
    # API Doc 路由
    try:
        from app.routes import api_doc
        app.include_router(api_doc.router)
        logger.info("✓ API Doc 路由已注册")
    except Exception as e:
        logger.error(f"✗ API Doc 路由注册失败: {e}")
    
    # Alerts 路由
    try:
        from app.routes import alerts
        app.include_router(alerts.router)
        logger.info("✓ Alerts 路由已注册")
    except Exception as e:
        logger.error(f"✗ Alerts 路由注册失败: {e}")
    
    # V1 API 路由（新版 API）
    try:
        from app.routes.v1 import dashboard as v1_dashboard
        from app.routes.v1 import scripts as v1_scripts
        from app.routes.v1 import dag as v1_dag
        from app.routes.v1 import ar as v1_ar
        from app.routes.v1 import alerts as v1_alerts
        from app.routes.v1 import metrics_history as v1_metrics
        from app.routes.v1 import alert_rules as v1_alert_rules
        from app.routes.v1 import alerts_history as v1_alerts_history
        from app.routes.v1 import intelligent_alert as v1_intelligent
        from app.routes.v1 import monitor as v1_monitor
        
        app.include_router(v1_dashboard.router, prefix="/api/v1")
        app.include_router(v1_scripts.router, prefix="/api/v1")
        app.include_router(v1_dag.router, prefix="/api/v1")
        app.include_router(v1_ar.router, prefix="/api/v1")
        app.include_router(v1_alerts.router, prefix="/api/v1")
        app.include_router(v1_metrics.router, prefix="/api/v1")
        app.include_router(v1_alert_rules.router, prefix="/api/v1")
        app.include_router(v1_alerts_history.router, prefix="/api/v1")
        app.include_router(v1_intelligent.router, prefix="/api/v1")
        app.include_router(v1_monitor.router, prefix="/api/v1")
        logger.info("✓ V1 API 路由已注册")
    except Exception as e:
        logger.warning(f"⚠ V1 API 路由注册失败（非关键）: {e}")


# 注册 WebSocket 路由
def register_websocket_routes():
    """注册所有 WebSocket 路由（使用 APIRouter）"""
    
    # Dashboard WebSocket
    try:
        from app.ws import dashboard_ws
        app.include_router(dashboard_ws.router)
        logger.info("✓ Dashboard WebSocket 已注册")
    except Exception as e:
        logger.warning(f"⚠ Dashboard WebSocket 注册失败: {e}")
    
    # DAG WebSocket
    try:
        from app.ws import dag_ws
        app.include_router(dag_ws.router)
        logger.info("✓ DAG WebSocket 已注册")
    except Exception as e:
        logger.warning(f"⚠ DAG WebSocket 注册失败: {e}")
    
    # Scripts WebSocket
    try:
        from app.ws import scripts_ws
        app.include_router(scripts_ws.router)
        logger.info("✓ Scripts WebSocket 已注册")
    except Exception as e:
        logger.warning(f"⚠ Scripts WebSocket 注册失败: {e}")
    
    # AR WebSocket
    try:
        from app.ws import ar_ws
        app.include_router(ar_ws.router)
        logger.info("✓ AR WebSocket 已注册")
    except Exception as e:
        logger.warning(f"⚠ AR WebSocket 注册失败: {e}")
    
    # Alerts WebSocket
    try:
        from app.ws import alerts_ws
        app.include_router(alerts_ws.router)
        logger.info("✓ Alerts WebSocket 已注册")
    except Exception as e:
        logger.warning(f"⚠ Alerts WebSocket 注册失败: {e}")
    
    # Scripts WebSocket
    try:
        from app.ws import scripts_ws
        app.include_router(scripts_ws.router)
        logger.info("✓ Scripts WebSocket 已注册")
    except Exception as e:
        logger.warning(f"⚠ Scripts WebSocket 注册失败: {e}")


# 页面路由
@app.get("/")
async def root(request: Request):
    """平台主入口（SPA）"""
    if templates:
        return templates.TemplateResponse("platform.html", {"request": request})
    return {"message": "YL-Monitor API", "version": "1.0.6", "docs": "/docs"}


@app.get("/dashboard")
async def dashboard_page(request: Request):
    """仪表盘页面"""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    return {"error": "Template not available"}


@app.get("/scripts")
async def scripts_page(request: Request):
    """脚本管理页面"""
    if templates:
        return templates.TemplateResponse("scripts.html", {"request": request})
    return {"error": "Template not available"}


@app.get("/dag")
async def dag_page(request: Request):
    """DAG 流水线页面"""
    if templates:
        return templates.TemplateResponse("dag.html", {"request": request})
    return {"error": "Template not available"}


@app.get("/ar")
async def ar_page(request: Request):
    """AR 监控页面"""
    if templates:
        return templates.TemplateResponse("ar.html", {"request": request})
    return {"error": "Template not available"}


@app.get("/alerts")
async def alerts_page(request: Request):
    """告警中心页面（统一入口）"""
    if templates:
        return templates.TemplateResponse("alert_center.html", {"request": request})
    return {"error": "Template not available"}


@app.get("/alert-rules")
async def alert_rules_redirect(request: Request):
    """告警规则页面 - 重定向到告警中心"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/alerts#rules", status_code=301)


@app.get("/alert-analytics")
async def alert_analytics_redirect(request: Request):
    """告警分析页面 - 重定向到告警中心"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/alerts#analytics", status_code=301)


@app.get("/intelligent-alert")
async def intelligent_alert_redirect(request: Request):
    """智能告警页面 - 重定向到告警中心"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/alerts#intelligent", status_code=301)


@app.get("/api-doc")
async def api_doc_page(request: Request):
    """API 文档页面"""
    if templates:
        return templates.TemplateResponse("api_doc.html", {"request": request})
    return {"error": "Template not available"}


# API 端点
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "1.0.6",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/summary")
async def api_summary():
    """系统整体状态摘要"""
    summary = {
        "status": "running",
        "version": "1.0.6",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "fastapi": "running",
            "websocket": "running",
        }
    }
    
    # 添加各服务状态
    if hasattr(app.state, "scripts_runner") and app.state.scripts_runner:
        summary["services"]["scripts_runner"] = "running"
        summary["scripts_count"] = len(app.state.scripts_runner.scripts)
    
    if hasattr(app.state, "dag_engine") and app.state.dag_engine:
        summary["services"]["dag_engine"] = "running"
        summary["dags_count"] = len(app.state.dag_engine.dags)
    
    if hasattr(app.state, "ar_monitor") and app.state.ar_monitor:
        summary["services"]["ar_monitor"] = "running"
        nodes = app.state.ar_monitor.get_nodes()
        summary["ar_nodes"] = {
            "total": nodes.total,
            "online": nodes.online_count,
            "offline": nodes.offline_count
        }
    
    return summary


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未捕获的异常: {exc}", exc_info=True)
    import json
    return Response(
        content=json.dumps({"error": "Internal Server Error", "detail": str(exc)}),
        status_code=500,
        media_type="application/json"
    )


# 启动时注册路由
register_routers()
register_websocket_routes()

logger.info("FastAPI 应用初始化完成")
