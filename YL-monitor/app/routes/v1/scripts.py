"""
API v1 - Scripts 路由

功能:
- 脚本管理与执行接口
- 统一的响应格式

作者: AI Assistant
版本: v1.0.0
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Request, HTTPException
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ValidationError as CoreValidationError

from app.models.script import ScriptRunRequest
from app.middleware import create_success_response

router = APIRouter(prefix="/scripts", tags=["Scripts"])


class ScriptListResponse(BaseModel):
    """脚本列表响应"""
    scripts: list[Dict[str, Any]]
    page: int
    per_page: int
    total: int
    total_pages: int


class ScriptRunRequestV1(BaseModel):
    """脚本执行请求"""
    script_name: str
    params: Dict[str, Any] = {}


class ScriptStatusResponse(BaseModel):
    """脚本状态响应"""
    script_name: str
    status: str
    priority: int
    description: Optional[str] = None


def _get_runner(request: Request):
    runner = getattr(request.app.state, "scripts_runner", None)
    if runner is None:
        raise RuntimeError("scripts runner not initialized")
    return runner


def _sanitize_errors(errors):
    sanitized = []
    for err in errors:
        if isinstance(err, dict) and "ctx" in err and isinstance(err["ctx"], dict):
            ctx = {k: str(v) for k, v in err["ctx"].items()}
            err = {**err, "ctx": ctx}
        sanitized.append(err)
    return sanitized


@router.get("/list", response_model=ScriptListResponse)
async def list_scripts(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=100),
    sort_by: str = Query("priority", pattern="^(priority|name)$"),
):
    """
    获取脚本列表
    
    支持分页和排序
    """
    runner = _get_runner(request)
    items = runner.list_scripts(sort_by=sort_by)
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page

    scripts = []
    for s in items[start:end]:
        d = s.model_dump()
        d.pop("file_path", None)
        scripts.append(d)

    return ScriptListResponse(
        scripts=scripts,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages
    )


@router.post("/run")
async def run_script(request: Request, body: ScriptRunRequestV1):
    """
    执行脚本
    
    触发脚本执行并返回执行 ID
    """
    runner = _get_runner(request)
    try:
        req = ScriptRunRequest(script_name=body.script_name, params=body.params)
    except (PydanticValidationError, CoreValidationError) as e:
        raise HTTPException(status_code=422, detail=_sanitize_errors(e.errors()))
    
    result = await runner.run_script(req)
    return create_success_response(
        data=result.model_dump(),
        message="Script execution started"
    )


@router.get("/status", response_model=ScriptStatusResponse)
async def get_status(request: Request, script_name: str):
    """
    获取脚本状态
    """
    runner = _get_runner(request)
    s = runner.get_script(script_name)
    if not s:
        raise HTTPException(status_code=404, detail="script not found")
    
    d = s.model_dump()
    d.pop("file_path", None)
    return ScriptStatusResponse(**d)


@router.get("/logs")
async def get_logs(request: Request, script_name: str, max_lines: int = Query(100, ge=1, le=1000)):
    """
    获取脚本执行日志
    """
    runner = _get_runner(request)
    logs = runner.get_logs(script_name, max_lines=max_lines)
    return create_success_response(
        data={"logs": logs},
        message="Logs retrieved successfully"
    )


@router.post("/reload")
async def reload_scripts(request: Request):
    """
    重新加载脚本
    """
    runner = _get_runner(request)
    count = await runner.load_scripts()
    return create_success_response(
        data={"count": count},
        message="Scripts reloaded successfully"
    )


@router.post("/stop")
async def stop_script(request: Request, script_name: str):
    """
    停止运行中的脚本
    """
    runner = _get_runner(request)
    ok = await runner.stop_script(script_name)
    if ok:
        return create_success_response(message=f"Script {script_name} stopped")
    raise HTTPException(status_code=404, detail=f"script '{script_name}' is not running")
