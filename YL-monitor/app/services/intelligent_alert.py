"""
【文件功能】智能告警服务
实现告警去重、合并、升级和自动恢复通知功能

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现智能告警核心功能

【依赖说明】
- 标准库: asyncio, time, typing, dataclasses, datetime, collections
- 第三方库: 无
- 内部模块: app.models.alert, app.services.alert_service

【使用示例】
```python
from app.services.intelligent_alert import intelligent_alert_service

# 启动服务
await intelligent_alert_service.start()

# 处理告警（自动去重、合并）
await intelligent_alert_service.process_alert(alert_data)

# 检查告警升级
await intelligent_alert_service.check_escalation()

# 检查告警恢复
await intelligent_alert_service.check_recovery()
```
"""

import asyncio
import time
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from app.models.alert import AlertRule, AlertHistory, AlertLevel, AlertStatus, MetricType


class AlertDedupStrategy(Enum):
    """【告警去重策略】"""
    RULE_BASED = "rule_based"      # 基于规则去重
    METRIC_BASED = "metric_based"   # 基于指标去重
    HOST_BASED = "host_based"       # 基于主机去重


class AlertMergeStrategy(Enum):
    """【告警合并策略】"""
    BY_TYPE = "by_type"             # 按类型合并
    BY_LEVEL = "by_level"           # 按级别合并
    BY_RULE = "by_rule"             # 按规则合并


@dataclass
class IntelligentAlertPolicy:
    """【智能告警策略】"""
    policy_id: str                  # 【策略ID】唯一标识
    name: str                       # 【名称】策略名称
    description: str = ""           # 【描述】策略描述
    rule_ids: List[str] = field(default_factory=list)  # 【关联规则】
    
    # 去重配置
    dedup_enabled: bool = True      # 【去重启用】
    dedup_strategy: str = "rule_based"  # 【去重策略】
    dedup_window: int = 300         # 【去重窗口】秒（默认5分钟）
    
    # 合并配置
    merge_enabled: bool = True      # 【合并启用】
    merge_strategy: str = "by_type"  # 【合并策略】
    merge_window: int = 60          # 【合并窗口】秒（默认1分钟）
    
    # 升级配置
    escalate_enabled: bool = True   # 【升级启用】
    escalate_time: int = 300        # 【升级时间】秒（默认5分钟）
    escalate_levels: List[str] = field(default_factory=lambda: ["warning", "error", "critical"])  # 【升级路径】
    
    # 恢复通知配置
    recover_enabled: bool = True    # 【恢复通知启用】
    recover_check_interval: int = 30  # 【恢复检测间隔】秒
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "rule_ids": self.rule_ids,
            "dedup_enabled": self.dedup_enabled,
            "dedup_strategy": self.dedup_strategy,
            "dedup_window": self.dedup_window,
            "merge_enabled": self.merge_enabled,
            "merge_strategy": self.merge_strategy,
            "merge_window": self.merge_window,
            "escalate_enabled": self.escalate_enabled,
            "escalate_time": self.escalate_time,
            "escalate_levels": self.escalate_levels,
            "recover_enabled": self.recover_enabled,
            "recover_check_interval": self.recover_check_interval,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class DedupRecord:
    """【去重记录】"""
    rule_id: str
    metric_type: str
    timestamp: datetime
    alert_hash: str


@dataclass
class MergeGroup:
    """【合并组】"""
    group_key: str
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    first_alert_time: datetime = field(default_factory=datetime.utcnow)
    last_alert_time: datetime = field(default_factory=datetime.utcnow)
    
    def add_alert(self, alert: Dict[str, Any]):
        """添加告警到组"""
        self.alerts.append(alert)
        self.last_alert_time = datetime.utcnow()
    
    def get_merged_alert(self) -> Dict[str, Any]:
        """获取合并后的告警"""
        if not self.alerts:
            return {}
        
        first_alert = self.alerts[0]
        return {
            "alert_id": f"merged_{self.group_key}_{int(time.time())}",
            "type": "merged_alert",
            "group_key": self.group_key,
            "alert_count": len(self.alerts),
            "first_alert_time": self.first_alert_time.isoformat(),
            "last_alert_time": self.last_alert_time.isoformat(),
            "rule_name": first_alert.get("rule_name", "Unknown"),
            "level": first_alert.get("level", "warning"),
            "message": f"{first_alert.get('rule_name', '告警')} 等 {len(self.alerts)} 个相关告警",
            "details": self.alerts
        }


class IntelligentAlertService:
    """
    【智能告警服务】
    
    【主要职责】
    1. 告警去重: 防止相同告警频繁触发
    2. 告警合并: 将相关告警合并为一条通知
    3. 告警升级: 未处理告警自动升级级别
    4. 恢复通知: 指标恢复后自动通知
    
    【核心机制】
    - 去重缓存: 记录最近触发的告警，避免重复
    - 合并窗口: 时间窗口内相同类型告警合并
    - 升级检查: 定时检查未确认告警并升级
    - 恢复检测: 监控指标值，低于阈值后触发恢复
    """
    
    def __init__(self):
        """【初始化】"""
        # 策略存储
        self._policies: Dict[str, IntelligentAlertPolicy] = {}
        
        # 去重缓存: {dedup_key: last_alert_time}
        self._dedup_cache: Dict[str, datetime] = {}
        
        # 合并缓存: {group_key: MergeGroup}
        self._merge_cache: Dict[str, MergeGroup] = {}
        
        # 活跃告警: {alert_id: alert_data}
        self._active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # 已升级告警: {alert_id: current_level}
        self._escalated_alerts: Dict[str, str] = {}
        
        # 运行状态
        self._running = False
        self._escalation_task: Optional[asyncio.Task] = None
        self._merge_flush_task: Optional[asyncio.Task] = None
        
        # 回调函数
        self._alert_handlers: List[Callable] = []
        self._recover_handlers: List[Callable] = []
        
        # 统计
        self._stats = {
            "dedup_count": 0,
            "merged_count": 0,
            "escalated_count": 0,
            "recovered_count": 0,
            "total_processed": 0
        }
        
        # 日志前缀
        self._log_prefix = "[智能告警]"
        
        # 加载默认策略
        self._load_default_policies()
    
    def _load_default_policies(self):
        """【加载默认策略】"""
        default_policy = IntelligentAlertPolicy(
            policy_id="default",
            name="默认智能策略",
            description="系统默认智能告警策略",
            rule_ids=[],  # 应用于所有规则
            dedup_enabled=True,
            dedup_window=300,  # 5分钟
            merge_enabled=True,
            merge_window=60,   # 1分钟
            escalate_enabled=True,
            escalate_time=300,  # 5分钟
            recover_enabled=True
        )
        self._policies[default_policy.policy_id] = default_policy
    
    async def start(self):
        """【启动服务】"""
        if self._running:
            return
        
        self._running = True
        
        # 启动升级检查任务
        self._escalation_task = asyncio.create_task(self._escalation_loop())
        
        # 启动合并刷新任务
        self._merge_flush_task = asyncio.create_task(self._merge_flush_loop())
        
        print(f"{self._log_prefix} 服务已启动")
    
    async def stop(self):
        """【停止服务】"""
        self._running = False
        
        if self._escalation_task:
            self._escalation_task.cancel()
            try:
                await self._escalation_task
            except asyncio.CancelledError:
                pass
        
        if self._merge_flush_task:
            self._merge_flush_task.cancel()
            try:
                await self._merge_flush_task
            except asyncio.CancelledError:
                pass
        
        print(f"{self._log_prefix} 服务已停止")
    
    async def process_alert(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        【处理告警】处理新告警（去重、合并）
        
        【参数说明】
        - alert: 告警数据字典
        
        【返回值】
        - 处理后的告警（去重返回None，合并返回合并后告警）
        """
        self._stats["total_processed"] += 1
        
        rule_id = alert.get("rule_id", "unknown")
        metric_type = alert.get("metric_type", "custom")
        
        # 获取适用的策略
        policy = self._get_policy_for_rule(rule_id)
        if not policy:
            return alert
        
        # 【去重检查】
        if policy.dedup_enabled:
            if self._should_dedup(alert, policy):
                self._stats["dedup_count"] += 1
                print(f"{self._log_prefix} 告警已去重: {rule_id}")
                return None
        
        # 【合并检查】
        if policy.merge_enabled:
            merged_alert = self._try_merge(alert, policy)
            if merged_alert:
                # 如果是合并后的告警，返回合并结果
                if merged_alert.get("type") == "merged_alert":
                    self._stats["merged_count"] += 1
                    return merged_alert
                # 否则继续处理（已加入合并组）
                return None
        
        # 记录活跃告警
        alert_id = alert.get("alert_id", f"alert_{int(time.time())}")
        self._active_alerts[alert_id] = alert
        
        # 更新去重缓存
        self._update_dedup_cache(alert, policy)
        
        return alert
    
    def _get_policy_for_rule(self, rule_id: str) -> Optional[IntelligentAlertPolicy]:
        """【获取策略】获取适用于指定规则的策略"""
        # 查找明确关联该规则的策略
        for policy in self._policies.values():
            if rule_id in policy.rule_ids:
                return policy
        
        # 返回默认策略
        return self._policies.get("default")
    
    def _should_dedup(self, alert: Dict[str, Any], policy: IntelligentAlertPolicy) -> bool:
        """【检查去重】检查是否应该去重"""
        # 生成去重键
        dedup_key = self._generate_dedup_key(alert, policy)
        
        # 检查缓存
        last_time = self._dedup_cache.get(dedup_key)
        if not last_time:
            return False
        
        # 检查是否在去重窗口内
        window = timedelta(seconds=policy.dedup_window)
        if datetime.utcnow() - last_time < window:
            return True
        
        return False
    
    def _generate_dedup_key(self, alert: Dict[str, Any], 
                           policy: IntelligentAlertPolicy) -> str:
        """【生成去重键】"""
        rule_id = alert.get("rule_id", "unknown")
        metric_type = alert.get("metric_type", "custom")
        host = alert.get("labels", {}).get("host", "default")
        
        if policy.dedup_strategy == "rule_based":
            return f"rule:{rule_id}"
        elif policy.dedup_strategy == "metric_based":
            return f"metric:{metric_type}:{host}"
        elif policy.dedup_strategy == "host_based":
            return f"host:{host}"
        else:
            return f"rule:{rule_id}"
    
    def _update_dedup_cache(self, alert: Dict[str, Any], 
                           policy: IntelligentAlertPolicy):
        """【更新去重缓存】"""
        dedup_key = self._generate_dedup_key(alert, policy)
        self._dedup_cache[dedup_key] = datetime.utcnow()
    
    def _try_merge(self, alert: Dict[str, Any], 
                  policy: IntelligentAlertPolicy) -> Optional[Dict[str, Any]]:
        """【尝试合并】尝试将告警加入合并组"""
        group_key = self._generate_merge_key(alert, policy)
        
        # 检查是否已有合并组
        if group_key in self._merge_cache:
            merge_group = self._merge_cache[group_key]
            merge_group.add_alert(alert)
            print(f"{self._log_prefix} 告警已加入合并组: {group_key}")
            return None  # 已加入合并组，暂不发送
        
        # 创建新合并组
        merge_group = MergeGroup(group_key=group_key)
        merge_group.add_alert(alert)
        self._merge_cache[group_key] = merge_group
        
        # 返回原始告警（等待合并窗口结束）
        return alert
    
    def _generate_merge_key(self, alert: Dict[str, Any], 
                           policy: IntelligentAlertPolicy) -> str:
        """【生成合并键】"""
        metric_type = alert.get("metric_type", "custom")
        level = alert.get("level", "warning")
        rule_id = alert.get("rule_id", "unknown")
        
        if policy.merge_strategy == "by_type":
            return f"type:{metric_type}"
        elif policy.merge_strategy == "by_level":
            return f"level:{level}"
        elif policy.merge_strategy == "by_rule":
            return f"rule:{rule_id}"
        else:
            return f"type:{metric_type}"
    
    async def _merge_flush_loop(self):
        """【合并刷新循环】定期刷新合并缓存"""
        while self._running:
            try:
                await self._flush_merge_groups()
            except Exception as e:
                print(f"{self._log_prefix} 合并刷新错误: {e}")
            
            await asyncio.sleep(30)  # 每30秒检查一次
    
    async def _flush_merge_groups(self):
        """【刷新合并组】发送超时的合并告警"""
        now = datetime.utcnow()
        expired_groups = []
        
        for group_key, merge_group in self._merge_cache.items():
            # 检查合并窗口是否结束
            policy = self._policies.get("default")
            window = timedelta(seconds=policy.merge_window if policy else 60)
            
            if now - merge_group.first_alert_time >= window:
                # 生成合并告警
                if len(merge_group.alerts) > 1:
                    merged_alert = merge_group.get_merged_alert()
                    
                    # 通知处理器
                    for handler in self._alert_handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(merged_alert)
                            else:
                                handler(merged_alert)
                        except Exception as e:
                            print(f"{self._log_prefix} 合并告警通知失败: {e}")
                
                expired_groups.append(group_key)
        
        # 清理过期组
        for key in expired_groups:
            del self._merge_cache[key]
    
    async def _escalation_loop(self):
        """【升级检查循环】定期检查告警升级"""
        while self._running:
            try:
                await self._check_escalation()
            except Exception as e:
                print(f"{self._log_prefix} 升级检查错误: {e}")
            
            await asyncio.sleep(60)  # 每分钟检查一次
    
    async def _check_escalation(self):
        """【检查升级】检查并升级未确认的告警"""
        now = datetime.utcnow()
        
        for alert_id, alert in list(self._active_alerts.items()):
            # 跳过已确认或已解决的告警
            if alert.get("acknowledged") or alert.get("resolved"):
                continue
            
            # 获取策略
            rule_id = alert.get("rule_id", "unknown")
            policy = self._get_policy_for_rule(rule_id)
            if not policy or not policy.escalate_enabled:
                continue
            
            # 检查是否需要升级
            alert_time = datetime.fromisoformat(alert.get("timestamp", "2000-01-01"))
            escalate_threshold = timedelta(seconds=policy.escalate_time)
            
            if now - alert_time >= escalate_threshold:
                # 检查是否已经升级过
                current_level = self._escalated_alerts.get(alert_id, alert.get("level", "warning"))
                
                # 升级到下一级别
                next_level = self._get_next_level(current_level, policy.escalate_levels)
                if next_level and next_level != current_level:
                    # 更新告警级别
                    alert["level"] = next_level
                    alert["escalated"] = True
                    alert["escalated_at"] = now.isoformat()
                    self._escalated_alerts[alert_id] = next_level
                    
                    self._stats["escalated_count"] += 1
                    
                    print(f"{self._log_prefix} 告警已升级: {alert_id} -> {next_level}")
                    
                    # 通知升级
                    for handler in self._alert_handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(alert)
                            else:
                                handler(alert)
                        except Exception as e:
                            print(f"{self._log_prefix} 升级通知失败: {e}")
    
    def _get_next_level(self, current_level: str, escalate_levels: List[str]) -> Optional[str]:
        """【获取下一级别】"""
        if current_level not in escalate_levels:
            return escalate_levels[0] if escalate_levels else None
        
        current_index = escalate_levels.index(current_level)
        if current_index < len(escalate_levels) - 1:
            return escalate_levels[current_index + 1]
        
        return None  # 已经是最高级别
    
    async def check_recovery(self, metric_data: Dict[str, Any]):
        """
        【检查恢复】检查指标是否恢复正常
        
        【参数说明】
        - metric_data: 当前指标数据
        """
        metric_type = metric_data.get("metric_type", "custom")
        current_value = metric_data.get("value", 0)
        
        # 查找相关告警
        for alert_id, alert in list(self._active_alerts.items()):
            if alert.get("metric_type") != metric_type:
                continue
            
            if alert.get("resolved"):
                continue
            
            # 获取规则阈值
            threshold = alert.get("threshold")
            condition = alert.get("condition", ">")
            
            if threshold is None:
                continue
            
            # 检查是否恢复（条件反转）
            recovered = False
            if condition == ">" and current_value <= threshold:
                recovered = True
            elif condition == "<" and current_value >= threshold:
                recovered = True
            elif condition == "=" and current_value != threshold:
                recovered = True
            
            if recovered:
                # 标记为已解决
                alert["resolved"] = True
                alert["resolved_at"] = datetime.utcnow().isoformat()
                alert["recovery_value"] = current_value
                
                self._stats["recovered_count"] += 1
                
                print(f"{self._log_prefix} 告警已恢复: {alert_id}")
                
                # 发送恢复通知
                recovery_notification = {
                    "type": "recovery",
                    "alert_id": alert_id,
                    "rule_name": alert.get("rule_name", "Unknown"),
                    "metric_type": metric_type,
                    "recovery_value": current_value,
                    "threshold": threshold,
                    "resolved_at": alert["resolved_at"],
                    "message": f"{alert.get('rule_name', '告警')}已恢复 "
                              f"(当前值: {current_value:.2f}, 阈值: {threshold})"
                }
                
                for handler in self._recover_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(recovery_notification)
                        else:
                            handler(recovery_notification)
                    except Exception as e:
                        print(f"{self._log_prefix} 恢复通知失败: {e}")
    
    def add_policy(self, policy: IntelligentAlertPolicy) -> None:
        """【添加策略】"""
        self._policies[policy.policy_id] = policy
    
    def remove_policy(self, policy_id: str) -> bool:
        """【移除策略】"""
        if policy_id in self._policies and policy_id != "default":
            del self._policies[policy_id]
            return True
        return False
    
    def get_policy(self, policy_id: str) -> Optional[IntelligentAlertPolicy]:
        """【获取策略】"""
        return self._policies.get(policy_id)
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """【列出所有策略】"""
        return [p.to_dict() for p in self._policies.values()]
    
    def on_alert(self, handler: Callable[[Dict[str, Any]], None]):
        """【注册告警处理器】"""
        self._alert_handlers.append(handler)
    
    def on_recovery(self, handler: Callable[[Dict[str, Any]], None]):
        """【注册恢复处理器】"""
        self._recover_handlers.append(handler)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """【确认告警】"""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id]["acknowledged"] = True
            self._active_alerts[alert_id]["acknowledged_at"] = datetime.utcnow().isoformat()
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """【解决告警】"""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id]["resolved"] = True
            self._active_alerts[alert_id]["resolved_at"] = datetime.utcnow().isoformat()
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """【获取统计】"""
        return {
            **self._stats,
            "active_alerts": len(self._active_alerts),
            "dedup_cache_size": len(self._dedup_cache),
            "merge_groups": len(self._merge_cache),
            "policies": len(self._policies)
        }
    
    def cleanup_cache(self):
        """【清理缓存】清理过期的去重缓存"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, last_time in self._dedup_cache.items():
            # 清理超过1小时的记录
            if now - last_time > timedelta(hours=1):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._dedup_cache[key]
        
        return len(expired_keys)


# 【全局智能告警服务实例】
intelligent_alert_service = IntelligentAlertService()


# 【便捷函数】
async def start_intelligent_alert_service():
    """【便捷函数】启动智能告警服务"""
    await intelligent_alert_service.start()


async def stop_intelligent_alert_service():
    """【便捷函数】停止智能告警服务"""
    await intelligent_alert_service.stop()


async def process_alert(alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """【便捷函数】处理告警"""
    return await intelligent_alert_service.process_alert(alert)


def add_intelligent_policy(policy: IntelligentAlertPolicy):
    """【便捷函数】添加策略"""
    intelligent_alert_service.add_policy(policy)


def get_intelligent_stats() -> Dict[str, Any]:
    """【便捷函数】获取统计"""
    return intelligent_alert_service.get_stats()
