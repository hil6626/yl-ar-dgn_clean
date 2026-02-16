#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务功能监控 API
提供视频处理、人脸合成、音频处理的详细监控数据
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.business_monitor import business_collector

router = APIRouter()


@router.get("/business")
async def get_business_metrics() -> Dict[str, Any]:
    """
    获取完整的业务功能层监控数据
    
    包括：
    - 视频处理指标（FPS、丢帧率、处理时间）
    - 人脸合成指标（推理时间、质量评分、GPU利用率）
    - 音频处理指标（延迟、实时因子、音效状态）
    - 整体健康状态
    """
    try:
        return business_collector.collect_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/video")
async def get_video_metrics() -> Dict[str, Any]:
    """
    获取视频处理监控指标
    """
    try:
        metrics = business_collector.video_monitor.get_metrics()
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/face-swap")
async def get_face_swap_metrics() -> Dict[str, Any]:
    """
    获取人脸合成监控指标
    """
    try:
        metrics = business_collector.face_monitor.get_metrics()
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/audio")
async def get_audio_metrics() -> Dict[str, Any]:
    """
    获取音频处理监控指标
    """
    try:
        metrics = business_collector.audio_monitor.get_metrics()
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/health")
async def get_business_health() -> Dict[str, Any]:
    """
    获取业务功能健康状态摘要
    """
    try:
        return business_collector.get_health_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/session/start")
async def start_session() -> Dict[str, Any]:
    """
    开始业务会话（用于测试）
    """
    try:
        business_collector.start_session()
        return {
            "status": "started",
            "active_sessions": business_collector._active_sessions,
            "timestamp": business_collector.video_monitor.get_metrics().timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/session/stop")
async def stop_session() -> Dict[str, Any]:
    """
    停止业务会话（用于测试）
    """
    try:
        business_collector.stop_session()
        return {
            "status": "stopped",
            "active_sessions": business_collector._active_sessions,
            "timestamp": business_collector.video_monitor.get_metrics().timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
