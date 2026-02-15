"""
【文件功能】智能告警配置API
实现智能告警策略的CRUD和配置管理

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现智能告警配置API

【依赖说明】
- 标准库: datetime, typing
- 第三方库: fastapi, pydantic
- 内部模块: app.services.intelligent_alert

【使用示例】
```python
from app.routes.v1.intelligent_alert import router

# 在FastAPI应用中注册
app.include_router(router, prefix="/api/v1")
```
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.services.intelligent_alert import (
    intelligent_alert_service,
    IntelligentAlertPolicy,
    add_intelligent_policy
)

router = APIRouter(prefix="/intelligent-alert", tags=["智能告警"])


class PolicyCreateRequest(BaseModel):
    """【策略创建请求】"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: str = Field(default="", max_length=500, description="策略描述")
    rule_ids: List[str] = Field(default_factory=list, description="关联的告警规则ID")
    
    # 去重配置
    dedup_enabled: bool = Field(default=True, description="启用去重")
    dedup_strategy: str = Field(default="rule_based", description="去重策略")
    dedup_window: int = Field(default=300, ge=60, le=3600, description="去重窗口（秒）")
    
    # 合并配置
    merge_enabled: bool = Field(default=True, description="启用合并")
    merge_strategy: str = Field(default="by_type", description="合并策略")
    merge_window: int = Field(default=60, ge=10, le=600, description="合并窗口（秒）")
    
    # 升级配置
    escalate_enabled: bool = Field(default=True, description="启用升级")
    escalate_time: int = Field(default=300, ge=60, le=3600, description="升级时间（秒）")
    escalate_levels: List[str] = Field(
        default_factory=lambda: ["warning", "error", "critical"],
        description="升级路径"
    )
    
    # 恢复通知配置
    recover_enabled: bool = Field(default=True, description="启用恢复通知")
    recover_check_interval: int = Field(default=30, ge=10, le=300, description="恢复检测间隔（秒）")


class PolicyUpdateRequest(BaseModel):
    """【策略更新请求】"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rule_ids: Optional[List[str]] = Field(None)
    dedup_enabled: Optional[bool] = Field(None)
    dedup_strategy: Optional[str] = Field(None)
    dedup_window: Optional[int] = Field(None, ge=60, le=3600)
    merge_enabled: Optional[bool] = Field(None)
    merge_strategy: Optional[str] = Field(None)
    merge_window: Optional[int] = Field(None, ge=10, le=600)
    escalate_enabled: Optional[bool] = Field(None)
    escalate_time: Optional[int] = Field(None, ge=60, le=3600)
    escalate_levels: Optional[List[str]] = Field(None)
    recover_enabled: Optional[bool] = Field(None)
    recover_check_interval: Optional[int] = Field(None, ge=10, le=300)


class PolicyResponse(BaseModel):
    """【策略响应】"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="策略数据")
    message: str = Field(default="操作成功", description="响应消息")


class PolicyListResponse(BaseModel):
    """【策略列表响应】"""
    success: bool = Field(..., description="是否成功")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="策略列表")
    total: int = Field(default=0, description="总数")
    message: str = Field(default="查询成功", description="响应消息")


class StatsResponse(BaseModel):
    """【统计响应】"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="统计数据")
    message: str = Field(default="获取成功", description="响应消息")


@router.get("/policies", response_model=PolicyListResponse)
async def list_policies():
    """
    【获取策略列表】获取所有智能告警策略
    
    【返回值】
    - success: 是否成功
    - data: 策略列表
    - total: 总数
    """
    try:
        policies = intelligent_alert_service.list_policies()
        
        return PolicyListResponse(
            success=True,
            data=policies,
            total=len(policies),
            message=f"成功获取 {len(policies)} 个策略"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str = Path(..., description="策略ID")):
    """
    【获取策略详情】获取指定策略的详细信息
    
    【参数说明】
    - policy_id: 策略ID
    
    【返回值】
    - 策略详细信息
    """
    try:
        policy = intelligent_alert_service.get_policy(policy_id)
        
        if not policy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {policy_id}")
        
        return PolicyResponse(
            success=True,
            data=policy.to_dict(),
            message="获取策略成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.post("/policies", response_model=PolicyResponse)
async def create_policy(request: PolicyCreateRequest):
    """
    【创建策略】创建新的智能告警策略
    
    【请求体】
    - name: 策略名称（必填）
    - description: 策略描述
    - rule_ids: 关联的告警规则ID列表
    - dedup_enabled: 是否启用去重
    - dedup_strategy: 去重策略（rule_based/metric_based/host_based）
    - dedup_window: 去重窗口（秒，60-3600）
    - merge_enabled: 是否启用合并
    - merge_strategy: 合并策略（by_type/by_level/by_rule）
    - merge_window: 合并窗口（秒，10-600）
    - escalate_enabled: 是否启用升级
    - escalate_time: 升级时间（秒，60-3600）
    - escalate_levels: 升级路径列表
    - recover_enabled: 是否启用恢复通知
    - recover_check_interval: 恢复检测间隔（秒，10-300）
    
    【返回值】
    - 创建成功的策略信息
    """
    try:
        # 生成策略ID
        import uuid
        policy_id = f"policy_{uuid.uuid4().hex[:8]}"
        
        # 创建策略对象
        policy = IntelligentAlertPolicy(
            policy_id=policy_id,
            name=request.name,
            description=request.description,
            rule_ids=request.rule_ids,
            dedup_enabled=request.dedup_enabled,
            dedup_strategy=request.dedup_strategy,
            dedup_window=request.dedup_window,
            merge_enabled=request.merge_enabled,
            merge_strategy=request.merge_strategy,
            merge_window=request.merge_window,
            escalate_enabled=request.escalate_enabled,
            escalate_time=request.escalate_time,
            escalate_levels=request.escalate_levels,
            recover_enabled=request.recover_enabled,
            recover_check_interval=request.recover_check_interval,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 添加到服务
        intelligent_alert_service.add_policy(policy)
        
        return PolicyResponse(
            success=True,
            data=policy.to_dict(),
            message="策略创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略失败: {str(e)}")


@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str = Path(..., description="策略ID"),
    request: PolicyUpdateRequest = ...
):
    """
    【更新策略】更新智能告警策略
    
    【参数说明】
    - policy_id: 策略ID（路径参数）
    - 请求体: 需要更新的字段
    
    【返回值】
    - 更新后的策略信息
    """
    try:
        # 获取现有策略
        existing_policy = intelligent_alert_service.get_policy(policy_id)
        
        if not existing_policy:
            raise HTTPException(status_code=404, detail=f"策略不存在: {policy_id}")
        
        # 不允许修改默认策略的关键字段
        if policy_id == "default":
            if request.rule_ids is not None:
                raise HTTPException(status_code=400, detail="不能修改默认策略的规则关联")
        
        # 更新字段
        if request.name is not None:
            existing_policy.name = request.name
        if request.description is not None:
            existing_policy.description = request.description
        if request.rule_ids is not None:
            existing_policy.rule_ids = request.rule_ids
        if request.dedup_enabled is not None:
            existing_policy.dedup_enabled = request.dedup_enabled
        if request.dedup_strategy is not None:
            existing_policy.dedup_strategy = request.dedup_strategy
        if request.dedup_window is not None:
            existing_policy.dedup_window = request.dedup_window
        if request.merge_enabled is not None:
            existing_policy.merge_enabled = request.merge_enabled
        if request.merge_strategy is not None:
            existing_policy.merge_strategy = request.merge_strategy
        if request.merge_window is not None:
            existing_policy.merge_window = request.merge_window
        if request.escalate_enabled is not None:
            existing_policy.escalate_enabled = request.escalate_enabled
        if request.escalate_time is not None:
            existing_policy.escalate_time = request.escalate_time
        if request.escalate_levels is not None:
            existing_policy.escalate_levels = request.escalate_levels
        if request.recover_enabled is not None:
            existing_policy.recover_enabled = request.recover_enabled
        if request.recover_check_interval is not None:
            existing_policy.recover_check_interval = request.recover_check_interval
        
        existing_policy.updated_at = datetime.utcnow()
        
        return PolicyResponse(
            success=True,
            data=existing_policy.to_dict(),
            message="策略更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略失败: {str(e)}")


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str = Path(..., description="策略ID")):
    """
    【删除策略】删除智能告警策略
    
    【参数说明】
    - policy_id: 策略ID
    
    【返回值】
    - 删除结果
    """
    try:
        # 不能删除默认策略
        if policy_id == "default":
            raise HTTPException(status_code=400, detail="不能删除默认策略")
        
        # 删除策略
        success = intelligent_alert_service.remove_policy(policy_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"策略不存在: {policy_id}")
        
        return {
            "success": True,
            "message": "策略删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除策略失败: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_intelligent_alert_stats():
    """
    【获取统计】获取智能告警服务统计
    
    【返回值】
    - 去重次数
    - 合并次数
    - 升级次数
    - 恢复次数
    - 活跃告警数
    - 缓存大小等
    """
    try:
        stats = intelligent_alert_service.get_stats()
        
        return StatsResponse(
            success=True,
            data=stats,
            message="获取统计成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/cache/cleanup")
async def cleanup_cache():
    """
    【清理缓存】清理过期的去重缓存
    
    【返回值】
    - 清理的缓存条目数
    """
    try:
        cleaned_count = intelligent_alert_service.cleanup_cache()
        
        return {
            "success": True,
            "data": {
                "cleaned_count": cleaned_count
            },
            "message": f"清理了 {cleaned_count} 条过期缓存"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.get("/strategies")
async def get_strategies():
    """
    【获取策略选项】获取可用的策略选项
    
    【返回值】
    - 去重策略选项
    - 合并策略选项
    - 升级级别选项
    """
    return {
        "success": True,
        "data": {
            "dedup_strategies": [
                {"value": "rule_based", "name": "基于规则", "description": "相同规则ID的告警去重"},
                {"value": "metric_based", "name": "基于指标", "description": "相同指标类型的告警去重"},
                {"value": "host_based", "name": "基于主机", "description": "相同主机的告警去重"}
            ],
            "merge_strategies": [
                {"value": "by_type", "name": "按类型合并", "description": "相同指标类型的告警合并"},
                {"value": "by_level", "name": "按级别合并", "description": "相同告警级别的告警合并"},
                {"value": "by_rule", "name": "按规则合并", "description": "相同规则的告警合并"}
            ],
            "escalate_levels": [
                {"value": "info", "name": "信息", "description": "信息级别"},
                {"value": "warning", "name": "警告", "description": "警告级别"},
                {"value": "error", "name": "错误", "description": "错误级别"},
                {"value": "critical", "name": "紧急", "description": "紧急级别"}
            ]
        },
        "message": "获取策略选项成功"
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str = Path(..., description="告警ID")):
    """
    【确认告警】手动确认告警
    
    【参数说明】
    - alert_id: 告警ID
    
    【返回值】
    - 确认结果
    """
    try:
        success = intelligent_alert_service.acknowledge_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"告警不存在: {alert_id}")
        
        return {
            "success": True,
            "message": "告警已确认"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str = Path(..., description="告警ID")):
    """
    【解决告警】手动解决告警
    
    【参数说明】
    - alert_id: 告警ID
    
    【返回值】
    - 解决结果
    """
    try:
        success = intelligent_alert_service.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"告警不存在: {alert_id}")
        
        return {
            "success": True,
            "message": "告警已解决"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")
