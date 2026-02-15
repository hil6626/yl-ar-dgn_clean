#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警服务单元测试

【功能描述】
测试告警服务的核心功能，包括规则管理、告警触发、通知发送等

【作者】
AI Assistant

【创建时间】
2026-02-10

【版本】
1.0.0

【测试覆盖】
- 告警规则CRUD操作
- 告警触发逻辑
- 通知发送机制
- 告警历史管理
- 告警确认和恢复
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.alert_service import AlertService, get_alert_service
from app.models.alert import (
    AlertRule, AlertHistory, AlertStatus, AlertLevel, 
    MetricType, NotificationChannel, ComparisonOp
)


@pytest.mark.unit
class TestAlertService:
    """告警服务测试类"""
    
    @pytest.fixture
    def alert_service(self, temp_data_dir):
        """创建告警服务实例"""
        service = AlertService(storage_dir=temp_data_dir)
        return service
    
    @pytest.fixture
    def sample_rule_data(self):
        """示例规则数据"""
        return {
            "name": "CPU高使用率告警",
            "description": "当CPU使用率超过80%时触发",
            "metric": MetricType.CPU,
            "comparison": ComparisonOp.GT,
            "threshold": 80.0,
            "duration": 5,
            "level": AlertLevel.WARNING,
            "channels": [NotificationChannel.BROWSER],
            "enabled": True,
            "silence_duration": 30,
            "email_recipients": [],
            "webhook_url": ""
        }
    
    # ==================== 规则管理测试 ====================
    
    def test_create_rule(self, alert_service, sample_rule_data):
        """
        【测试】创建告警规则
        
        【场景】创建一个新的告警规则
        【预期】规则创建成功，包含正确字段
        """
        # 执行
        rule = alert_service.create_rule(sample_rule_data)
        
        # 验证
        assert rule is not None
        assert rule.id.startswith("rule-")
        assert rule.name == sample_rule_data["name"]
        assert rule.metric == MetricType.CPU
        assert rule.threshold == 80.0
        assert rule.enabled is True
        assert rule.created_at is not None
    
    def test_get_rule(self, alert_service, sample_rule_data):
        """
        【测试】获取单个规则
        
        【场景】根据ID获取已创建的规则
        【预期】返回正确的规则对象
        """
        # 准备
        created_rule = alert_service.create_rule(sample_rule_data)
        rule_id = created_rule.id
        
        # 执行
        rule = alert_service.get_rule(rule_id)
        
        # 验证
        assert rule is not None
        assert rule.id == rule_id
        assert rule.name == sample_rule_data["name"]
    
    def test_get_rule_not_found(self, alert_service):
        """
        【测试】获取不存在的规则
        
        【场景】尝试获取不存在的规则ID
        【预期】返回None
        """
        # 执行
        rule = alert_service.get_rule("non-existent-rule")
        
        # 验证
        assert rule is None
    
    def test_list_rules(self, alert_service, sample_rule_data):
        """
        【测试】列出所有规则
        
        【场景】创建多个规则后列出
        【预期】返回所有规则列表
        """
        # 准备
        rule1 = alert_service.create_rule(sample_rule_data)
        
        data2 = sample_rule_data.copy()
        data2["name"] = "内存告警"
        data2["metric"] = MetricType.MEMORY
        rule2 = alert_service.create_rule(data2)
        
        # 执行
        rules = alert_service.list_rules()
        
        # 验证
        assert len(rules) == 2
        rule_ids = [r.id for r in rules]
        assert rule1.id in rule_ids
        assert rule2.id in rule_ids
    
    def test_list_rules_with_filter(self, alert_service, sample_rule_data):
        """
        【测试】带筛选条件的规则列表
        
        【场景】按启用状态、指标类型、级别筛选
        【预期】返回符合条件的规则
        """
        # 准备
        rule1 = alert_service.create_rule(sample_rule_data)
        
        data2 = sample_rule_data.copy()
        data2["metric"] = MetricType.MEMORY
        data2["enabled"] = False
        rule2 = alert_service.create_rule(data2)
        
        # 执行 - 只查询启用的规则
        enabled_rules = alert_service.list_rules(enabled_only=True)
        
        # 验证
        assert len(enabled_rules) == 1
        assert enabled_rules[0].id == rule1.id
        
        # 执行 - 按指标类型筛选
        cpu_rules = alert_service.list_rules(metric=MetricType.CPU)
        assert len(cpu_rules) == 1
        assert cpu_rules[0].metric == MetricType.CPU
    
    def test_update_rule(self, alert_service, sample_rule_data):
        """
        【测试】更新告警规则
        
        【场景】更新已存在规则的字段
        【预期】规则更新成功
        """
        # 准备
        rule = alert_service.create_rule(sample_rule_data)
        rule_id = rule.id
        
        # 执行
        updated = alert_service.update_rule(
            rule_id, 
            {"name": "更新后的名称", "threshold": 90.0}
        )
        
        # 验证
        assert updated is not None
        assert updated.name == "更新后的名称"
        assert updated.threshold == 90.0
        # 未更新的字段保持不变
        assert updated.metric == MetricType.CPU
    
    def test_update_rule_not_found(self, alert_service):
        """
        【测试】更新不存在的规则
        
        【场景】尝试更新不存在的规则
        【预期】返回None
        """
        # 执行
        result = alert_service.update_rule(
            "non-existent", 
            {"name": "新名称"}
        )
        
        # 验证
        assert result is None
    
    def test_delete_rule(self, alert_service, sample_rule_data):
        """
        【测试】删除告警规则
        
        【场景】删除已存在的规则
        【预期】删除成功，规则不再存在
        """
        # 准备
        rule = alert_service.create_rule(sample_rule_data)
        rule_id = rule.id
        
        # 执行
        success = alert_service.delete_rule(rule_id)
        
        # 验证
        assert success is True
        assert alert_service.get_rule(rule_id) is None
    
    def test_delete_rule_not_found(self, alert_service):
        """
        【测试】删除不存在的规则
        
        【场景】尝试删除不存在的规则
        【预期】返回False
        """
        # 执行
        success = alert_service.delete_rule("non-existent")
        
        # 验证
        assert success is False
    
    # ==================== 告警触发测试 ====================
    
    def test_evaluate_condition_gt(self, alert_service):
        """
        【测试】条件评估 - 大于
        
        【场景】实际值 > 阈值
        【预期】条件满足
        """
        # 执行
        result = alert_service._evaluate_condition(ComparisonOp.GT, 85.0, 80.0)
        
        # 验证
        assert result is True
        
        # 不满足的情况
        result2 = alert_service._evaluate_condition(ComparisonOp.GT, 75.0, 80.0)
        assert result2 is False
    
    def test_evaluate_condition_gte(self, alert_service):
        """
        【测试】条件评估 - 大于等于
        
        【场景】实际值 >= 阈值
        【预期】条件满足
        """
        # 等于的情况
        result = alert_service._evaluate_condition(ComparisonOp.GTE, 80.0, 80.0)
        assert result is True
        
        # 大于的情况
        result2 = alert_service._evaluate_condition(ComparisonOp.GTE, 85.0, 80.0)
        assert result2 is True
    
    def test_evaluate_condition_lt(self, alert_service):
        """
        【测试】条件评估 - 小于
        
        【场景】实际值 < 阈值
        【预期】条件满足
        """
        result = alert_service._evaluate_condition(ComparisonOp.LT, 75.0, 80.0)
        assert result is True
    
    def test_evaluate_condition_lte(self, alert_service):
        """
        【测试】条件评估 - 小于等于
        
        【场景】实际值 <= 阈值
        【预期】条件满足
        """
        result = alert_service._evaluate_condition(ComparisonOp.LTE, 80.0, 80.0)
        assert result is True
    
    def test_generate_alert_message(self, alert_service, sample_rule_data):
        """
        【测试】生成告警消息
        
        【场景】根据规则和实际值生成告警消息
        【预期】消息包含关键信息
        """
        # 准备
        rule = AlertRule(**sample_rule_data)
        
        # 执行
        message = alert_service._generate_alert_message(rule, 85.5)
        
        # 验证
        assert "CPU 使用率" in message
        assert "超过" in message
        assert "80" in message
        assert "85.5" in message
    
    # ==================== 告警历史测试 ====================
    
    def test_get_alert_history_empty(self, alert_service):
        """
        【测试】获取空告警历史
        
        【场景】没有告警记录时查询历史
        【预期】返回空列表
        """
        # 执行
        history = alert_service.get_alert_history()
        
        # 验证
        assert history == []
    
    def test_get_alert_history_with_filters(self, alert_service):
        """
        【测试】带筛选的告警历史查询
        
        【场景】按规则ID、状态、级别、时间筛选
        【预期】返回符合条件的记录
        """
        # 准备 - 创建一些测试告警记录
        now = datetime.utcnow()
        alert1 = AlertHistory(
            id="alert-001",
            rule_id="rule-001",
            rule_name="测试规则1",
            level=AlertLevel.WARNING,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="测试告警1",
            triggered_at=now
        )
        alert2 = AlertHistory(
            id="alert-002",
            rule_id="rule-002",
            rule_name="测试规则2",
            level=AlertLevel.CRITICAL,
            status=AlertStatus.RECOVERED,
            metric=MetricType.MEMORY,
            threshold=90.0,
            actual_value=95.0,
            message="测试告警2",
            triggered_at=now - timedelta(hours=1),
            recovered_at=now
        )
        
        alert_service._history["alert-001"] = alert1
        alert_service._history["alert-002"] = alert2
        
        # 执行 - 按规则ID筛选
        history = alert_service.get_alert_history(rule_id="rule-001")
        assert len(history) == 1
        assert history[0].id == "alert-001"
        
        # 执行 - 按状态筛选
        history = alert_service.get_alert_history(status=AlertStatus.RECOVERED)
        assert len(history) == 1
        assert history[0].status == AlertStatus.RECOVERED
        
        # 执行 - 按级别筛选
        history = alert_service.get_alert_history(level=AlertLevel.CRITICAL)
        assert len(history) == 1
        assert history[0].level == AlertLevel.CRITICAL
    
    def test_get_active_alerts(self, alert_service):
        """
        【测试】获取活动告警
        
        【场景】查询当前未恢复的告警
        【预期】返回活动告警列表
        """
        # 准备
        now = datetime.utcnow()
        active_alert = AlertHistory(
            id="alert-001",
            rule_id="rule-001",
            rule_name="活动告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="活动告警",
            triggered_at=now
        )
        alert_service._active_alerts["rule-001"] = active_alert
        
        # 执行
        active = alert_service.get_active_alerts()
        
        # 验证
        assert len(active) == 1
        assert active[0].id == "alert-001"
        assert active[0].status == AlertStatus.TRIGGERED
    
    def test_acknowledge_alert(self, alert_service):
        """
        【测试】确认告警
        
        【场景】将告警状态改为已确认
        【预期】状态更新成功
        """
        # 准备
        now = datetime.utcnow()
        alert = AlertHistory(
            id="alert-001",
            rule_id="rule-001",
            rule_name="测试告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="测试",
            triggered_at=now
        )
        alert_service._history["alert-001"] = alert
        
        # 执行
        result = alert_service.acknowledge_alert("alert-001", "admin")
        
        # 验证
        assert result is not None
        assert result.status == AlertStatus.ACKNOWLEDGED
        assert result.acknowledged_by == "admin"
        assert result.acknowledged_at is not None
    
    def test_acknowledge_alert_not_found(self, alert_service):
        """
        【测试】确认不存在的告警
        
        【场景】尝试确认不存在的告警
        【预期】返回None
        """
        # 执行
        result = alert_service.acknowledge_alert("non-existent", "admin")
        
        # 验证
        assert result is None
    
    # ==================== 统计测试 ====================
    
    def test_get_stats(self, alert_service):
        """
        【测试】获取告警统计
        
        【场景】获取告警数量统计
        【预期】返回正确的统计信息
        """
        # 准备
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 添加一些测试数据
        alert1 = AlertHistory(
            id="alert-001",
            rule_id="rule-001",
            rule_name="今日告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="测试",
            triggered_at=now
        )
        alert2 = AlertHistory(
            id="alert-002",
            rule_id="rule-002",
            rule_name="昨日告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.RECOVERED,
            metric=MetricType.MEMORY,
            threshold=80.0,
            actual_value=85.0,
            message="测试",
            triggered_at=now - timedelta(days=1),
            recovered_at=now
        )
        
        alert_service._history["alert-001"] = alert1
        alert_service._history["alert-002"] = alert2
        alert_service._active_alerts["rule-001"] = alert1
        
        # 执行
        stats = alert_service.get_stats()
        
        # 验证
        assert stats["total_alerts"] == 2
        assert stats["triggered_today"] == 1
        assert stats["active_alerts"] == 1
        assert stats["recovered_today"] == 0  # 昨天恢复的
    
    # ==================== 通知测试 ====================
    
    @pytest.mark.asyncio
    async def test_send_browser_notification(self, alert_service, sample_rule_data):
        """
        【测试】发送浏览器通知
        
        【场景】通过WebSocket发送浏览器推送
        【预期】通知发送成功
        """
        # 准备
        rule = AlertRule(**sample_rule_data)
        alert = AlertHistory(
            id="alert-001",
            rule_id="rule-001",
            rule_name="测试告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="测试消息",
            triggered_at=datetime.utcnow(),
            notifications_sent=[]
        )
        
        # 模拟EventBus
        with patch('app.services.alert_service.EventBus') as mock_event_bus:
            mock_instance = MagicMock()
            mock_event_bus.return_value = mock_instance
            
            # 执行
            await alert_service._send_browser_notification(rule, alert)
            
            # 验证
            mock_instance.publish.assert_called_once()
            call_args = mock_instance.publish.call_args
            assert call_args[0][0].value == "notification_browser"  # EventType.NOTIFICATION_BROWSER
    
    def test_should_send_notification_no_last_time(self, alert_service, sample_rule_data):
        """
        【测试】通知发送检查 - 无历史记录
        
        【场景】该渠道从未发送过通知
        【预期】应该发送
        """
        # 准备
        rule = alert_service.create_rule(sample_rule_data)
        
        # 执行
        should_send = alert_service._should_send_notification(
            rule.id, 
            NotificationChannel.BROWSER
        )
        
        # 验证
        assert should_send is True
    
    def test_should_send_notification_within_silence(self, alert_service, sample_rule_data):
        """
        【测试】通知发送检查 - 静默期内
        
        【场景】距离上次通知时间小于静默期
        【预期】不应该发送
        """
        # 准备
        rule = alert_service.create_rule(sample_rule_data)
        key = f"{rule.id}:browser"
        alert_service._last_notification[key] = datetime.utcnow() - timedelta(minutes=10)
        
        # 执行
        should_send = alert_service._should_send_notification(
            rule.id, 
            NotificationChannel.BROWSER
        )
        
        # 验证
        assert should_send is False  # 30分钟静默期，只过了10分钟
    
    def test_should_send_notification_after_silence(self, alert_service, sample_rule_data):
        """
        【测试】通知发送检查 - 静默期后
        
        【场景】距离上次通知时间超过静默期
        【预期】应该发送
        """
        # 准备
        rule = alert_service.create_rule(sample_rule_data)
        key = f"{rule.id}:browser"
        alert_service._last_notification[key] = datetime.utcnow() - timedelta(minutes=35)
        
        # 执行
        should_send = alert_service._should_send_notification(
            rule.id, 
            NotificationChannel.BROWSER
        )
        
        # 验证
        assert should_send is True  # 30分钟静默期，已过了35分钟
    
    # ==================== 数据持久化测试 ====================
    
    def test_save_and_load_rules(self, temp_data_dir, sample_rule_data):
        """
        【测试】规则数据持久化
        
        【场景】创建规则后重新加载服务
        【预期】规则数据正确恢复
        """
        # 准备 - 创建服务并添加规则
        service1 = AlertService(storage_dir=temp_data_dir)
        rule = service1.create_rule(sample_rule_data)
        rule_id = rule.id
        
        # 执行 - 创建新服务实例（会触发加载）
        service2 = AlertService(storage_dir=temp_data_dir)
        
        # 验证
        loaded_rule = service2.get_rule(rule_id)
        assert loaded_rule is not None
        assert loaded_rule.name == sample_rule_data["name"]
        assert loaded_rule.threshold == sample_rule_data["threshold"]
    
    def test_save_and_load_history(self, temp_data_dir):
        """
        【测试】历史数据持久化
        
        【场景】添加告警历史后重新加载
        【预期】历史数据正确恢复
        """
        # 准备
        service1 = AlertService(storage_dir=temp_data_dir)
        now = datetime.utcnow()
        alert = AlertHistory(
            id="alert-001",
            rule_id="rule-001",
            rule_name="测试告警",
            level=AlertLevel.WARNING,
            status=AlertStatus.TRIGGERED,
            metric=MetricType.CPU,
            threshold=80.0,
            actual_value=85.0,
            message="测试",
            triggered_at=now
        )
        service1._history["alert-001"] = alert
        service1._save_history()
        
        # 执行
        service2 = AlertService(storage_dir=temp_data_dir)
        
        # 验证
        history = service2.get_alert_history()
        assert len(history) == 1
        assert history[0].id == "alert-001"


@pytest.mark.unit
class TestAlertServiceSingleton:
    """告警服务单例测试"""
    
    def test_get_alert_service_singleton(self):
        """
        【测试】获取单例实例
        
        【场景】多次调用get_alert_service
        【预期】返回同一实例
        """
        # 执行
        service1 = get_alert_service()
        service2 = get_alert_service()
        
        # 验证
        assert service1 is service2
    
    def test_alert_service_is_instance(self):
        """
        【测试】实例类型检查
        
        【场景】获取服务实例
        【预期】是AlertService类型
        """
        # 执行
        service = get_alert_service()
        
        # 验证
        assert isinstance(service, AlertService)
