#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用服务监控 API
提供 API、数据库、缓存的详细监控数据
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.application_monitor import application_collector

router = APIRouter()


@router.get("/application")
async def get_application_metrics() -> Dict[str, Any]:
    """
    获取完整的应用服务层监控数据
    
    包括：
    - API服务指标（响应时间、错误率、可用性）
    - 数据库指标（连接池、查询性能、事务）
    - 缓存指标（命中率、内存使用、淘汰率）
    """
    try:
        return application_collector.collect_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/services")
async def get_api_services() -> Dict[str, Any]:
    """
    获取所有API服务的监控数据
    """
    try:
        result = application_collector.collect_all()
        return {
            "services": result.get("api_services", {}),
            "timestamp": result.get("timestamp")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/services/{service_name}")
async def get_service_metrics(service_name: str) -> Dict[str, Any]:
    """
    获取指定API服务的详细指标
    
    Args:
        service_name: 服务名称（yl-monitor, ar-backend, user-gui）
    """
    if service_name not in application_collector.services:
        raise HTTPException(
            status_code=404,
            detail=f"未知服务: {service_name}"
        )
    
    try:
        config = application_collector.services[service_name]
        metrics = application_collector.api_monitor.get_service_metrics(
            service_name=service_name,
            base_url=config['base_url'],
            endpoints=config['endpoints']
        )
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/services/{service_name}/health")
async def get_service_health(service_name: str) -> Dict[str, Any]:
    """
    获取指定服务的健康状态
    """
    try:
        return application_collector.get_service_health(service_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/database")
async def get_database_metrics() -> Dict[str, Any]:
    """
    获取数据库监控指标
    """
    try:
        db_path = "YL-monitor/data/monitor.db"
        metrics = application_collector.db_monitor.get_metrics(db_path)
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/cache")
async def get_cache_metrics() -> Dict[str, Any]:
    """
    获取缓存监控指标
    """
    try:
        metrics = application_collector.cache_monitor.get_metrics()
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
