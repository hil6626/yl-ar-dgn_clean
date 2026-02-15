"""
API v1 - Dashboard 路由

功能:
- 系统健康监控接口
- 统一的响应格式

作者: AI Assistant
版本: v1.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from shutil import disk_usage
from typing import Dict, Tuple

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.middleware import create_success_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_CPU_LAST: Tuple[int, int] | None = None


def _read_cpu_idle_total() -> Tuple[int, int]:
    with open("/proc/stat", "r", encoding="utf-8") as f:
        line = f.readline()
    parts = line.split()
    if not parts or parts[0] != "cpu":
        raise RuntimeError("unexpected /proc/stat format")
    nums = list(map(int, parts[1:]))
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
    total = sum(nums)
    return idle, total


async def _cpu_usage_pct() -> float:
    global _CPU_LAST
    try:
        idle2, total2 = _read_cpu_idle_total()
    except Exception:
        return 0.0

    if _CPU_LAST is None:
        _CPU_LAST = (idle2, total2)
        await asyncio.sleep(0.05)
        try:
            idle2, total2 = _read_cpu_idle_total()
        except Exception:
            return 0.0

    idle1, total1 = _CPU_LAST
    _CPU_LAST = (idle2, total2)

    idle_delta = idle2 - idle1
    total_delta = total2 - total1
    if total_delta <= 0:
        return 0.0
    usage_pct = (1.0 - (idle_delta / total_delta)) * 100.0
    return round(max(0.0, min(100.0, usage_pct)), 2)


def _mem_usage_pct() -> Tuple[float, Dict[str, int]]:
    try:
        mem_total_kb = 0
        mem_avail_kb = 0
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total_kb = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_avail_kb = int(line.split()[1])
                if mem_total_kb and mem_avail_kb:
                    break
        if mem_total_kb <= 0:
            return 0.0, {}
        used_pct = (1.0 - (mem_avail_kb / mem_total_kb)) * 100.0
        details = {
            "mem_total_mb": int(mem_total_kb / 1024),
            "mem_available_mb": int(mem_avail_kb / 1024),
        }
        return round(max(0.0, min(100.0, used_pct)), 2), details
    except Exception:
        return 0.0, {}


def _disk_usage_pct(path: str = "/") -> Tuple[float, Dict[str, int]]:
    try:
        du = disk_usage(path)
        total = int(du.total)
        used = int(du.used)
        if total <= 0:
            return 0.0, {}
        used_pct = (used / total) * 100.0
        details = {
            "disk_total_gb": int(total / (1024**3)),
            "disk_used_gb": int(used / (1024**3)),
        }
        return round(max(0.0, min(100.0, used_pct)), 2), details
    except Exception:
        return 0.0, {}


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    services: list[str]
    details: Dict[str, int]


@router.get("/summary", response_model=HealthResponse)
async def get_summary(request: Request):
    """
    获取系统健康摘要
    
    返回 CPU、内存、磁盘使用率及服务状态
    """
    cpu = await _cpu_usage_pct()
    mem, mem_details = _mem_usage_pct()
    disk, disk_details = _disk_usage_pct("/")
    
    return HealthResponse(
        status="running",
        timestamp=datetime.utcnow().isoformat() + "Z",
        cpu_usage=cpu,
        memory_usage=mem,
        disk_usage=disk,
        services=["FastAPI", "WebSocket", "Scripts Runner", "DAG Engine", "AR Monitor"],
        details={**mem_details, **disk_details}
    )


@router.get("/health")
async def health_check(request: Request):
    """
    健康检查接口
    
    简单返回服务状态和请求 ID
    """
    return create_success_response(
        data={
            "status": "ok",
            "version": "v1.0.0"
        },
        message="Service is healthy"
    )

