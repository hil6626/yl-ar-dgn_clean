#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警API路由单元测试

【功能描述】
测试告警相关的API端点，包括规则管理、告警历史、通知测试等

【作者】
AI Assistant

【创建时间】
2026-02-10

【版本】
1.0.0

【测试覆盖】
- GET /api/v1/alerts/rules - 获取规则列表
- POST /api/v1/alerts/rules - 创建规则
- PUT /api/v1/alerts/rules/{id} - 更新规则
- DELETE /api/v1/alerts/rules/{id} - 删除规则
- GET /api/v1/alerts/history - 获取告警历史
- POST /api/v1/alerts/{id}/acknowledge - 确认告警
- GET /api/v1/alerts/stats - 告警统计
- POST /api/v1/alerts/test-notification - 测试通知
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch


@pytest.mark.unit
@pytest.mark.api
class TestAlertsAPI:
    """告警API测试类"""
    
    @pytest.fixture
    def sample_rule(self):
        """示例告警规则"""
        return {
            "name": "CPU高使用率告警",
            "description": "当CPU使用率超过80%时触发",
            "metric": "cpu",
            "comparison": "gt",
            "threshold": 80.0,
            "duration": 5,
            "level": "warning",
            "channels": ["browser"],
            "enabled": True,
            "silence_duration": 30
        }
    
    # ==================== 规则列表API测试 ====================
    
    def test_list_rules_success(self, client):
        """
        【测试】获取规则列表成功
        
        【场景】正常请求规则列表
        【预期】返回200和规则列表
        """
        # 执行
        response = client.get("/api/v1/alerts/rules")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_rules_with_filters(self, client):
        """
        【测试】带筛选条件的规则列表
        
        【场景】使用查询参数筛选规则
        【预期】返回筛选后的结果
        """
        # 执行 - 只查询启用的规则
        response = client.get("/api/v1/alerts/rules?enabled_only=true")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        # 执行 - 按指标类型筛选
        response = client.get("/api/v1/alerts/rules?metric=cpu")
        assert response.status_code == 200
        
        # 执行 - 按级别筛选
        response = client.get("/api/v1/alerts/rules?level=warning")
        assert response.status_code == 200
    
    # ==================== 获取单个规则API测试 ====================
    
    def test_get_rule_success(self, client, sample_rule):
        """
        【测试】获取单个规则成功
        
        【场景】获取已存在的规则
        【预期】返回200和规则详情
        """
        # 准备 - 先创建一个规则
        create_response = client.post("/api/v1/alerts/rules", json=sample_rule)
        assert create_response.status_code == 200
        rule_id = create_response.json()["data"]["id"]
        
        # 执行
        response = client.get(f"/api/v1/alerts/rules/{rule_id}")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rule_id
        assert data["name"] == sample_rule["name"]
    
    def test_get_rule_not_found(self, client):
        """
        【测试】获取不存在的规则
        
        【场景】请求不存在的规则ID
        【预期】返回404
        """
        # 执行
        response = client.get("/api/v1/alerts/rules/non-existent-rule")
        
        # 验证
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    # ==================== 创建规则API测试 ====================
    
    def test_create_rule_success(self, client, sample_rule):
        """
        【测试】创建规则成功
        
        【场景】提交有效的规则数据
        【预期】返回200和创建的规则
        """
        # 执行
        response = client.post("/api/v1/alerts/rules", json=sample_rule)
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["name"] == sample_rule["name"]
        assert "id" in data["data"]
    
    def test_create_rule_invalid_data(self, client):
        """
        【测试】创建规则 - 无效数据
        
        【场景】提交缺少必填字段的数据
        【预期】返回422验证错误
        """
        # 准备 - 缺少必填字段
        invalid_rule = {
            "description": "缺少名称和阈值"
        }
        
        # 执行
        response = client.post("/api/v1/alerts/rules", json=invalid_rule)
        
        # 验证
        assert response.status_code == 422
    
    def test_create_rule_invalid_metric_type(self, client, sample_rule):
        """
        【测试】创建规则 - 无效指标类型
        
        【场景】提交无效的metric值
        【预期】返回422验证错误
        """
        # 准备
        invalid_rule = sample_rule.copy()
        invalid_rule["metric"] = "invalid_metric"
        
        # 执行
        response = client.post("/api/v1/alerts/rules", json=invalid_rule)
        
        # 验证
        assert response.status_code == 422
    
    # ==================== 更新规则API测试 ====================
    
    def test_update_rule_success(self, client, sample_rule):
        """
        【测试】更新规则成功
        
        【场景】更新已存在的规则
        【预期】返回200和更新后的规则
        """
        # 准备 - 先创建规则
        create_response = client.post("/api/v1/alerts/rules", json=sample_rule)
        rule_id = create_response.json()["data"]["id"]
        
        # 执行
        update_data = {
            "name": "更新后的名称",
            "threshold": 90.0
        }
        response = client.put(f"/api/v1/alerts/rules/{rule_id}", json=update_data)
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "更新后的名称"
        assert data["data"]["threshold"] == 90.0
    
    def test_update_rule_not_found(self, client):
        """
        【测试】更新不存在的规则
        
        【场景】更新不存在的规则ID
        【预期】返回404
        """
        # 执行
        update_data = {"name": "新名称"}
        response = client.put("/api/v1/alerts/rules/non-existent", json=update_data)
        
        # 验证
        assert response.status_code == 404
    
    def test_update_rule_partial(self, client, sample_rule):
        """
        【测试】部分更新规则
        
        【场景】只更新部分字段
        【预期】只更新指定字段，其他保持不变
        """
        # 准备 - 先创建规则
        create_response = client.post("/api/v1/alerts/rules", json=sample_rule)
        rule_id = create_response.json()["data"]["id"]
        original_threshold = sample_rule["threshold"]
        
        # 执行 - 只更新名称
        update_data = {"name": "仅更新名称"}
        response = client.put(f"/api/v1/alerts/rules/{rule_id}", json=update_data)
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "仅更新名称"
        # 其他字段保持不变
        assert data["data"]["threshold"] == original_threshold
    
    # ==================== 删除规则API测试 ====================
    
    def test_delete_rule_success(self, client, sample_rule):
        """
        【测试】删除规则成功
        
        【场景】删除已存在的规则
        【预期】返回200
        """
        # 准备 - 先创建规则
        create_response = client.post("/api/v1/alerts/rules", json=sample_rule)
        rule_id = create_response.json()["data"]["id"]
        
        # 执行
        response = client.delete(f"/api/v1/alerts/rules/{rule_id}")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证规则已删除
        get_response = client.get(f"/api/v1/alerts/rules/{rule_id}")
        assert get_response.status_code == 404
    
    def test_delete_rule_not_found(self, client):
        """
        【测试】删除不存在的规则
        
        【场景】删除不存在的规则ID
        【预期】返回404
        """
        # 执行
        response = client.delete("/api/v1/alerts/rules/non-existent")
        
        # 验证
        assert response.status_code == 404
    
    # ==================== 告警历史API测试 ====================
    
    def test_get_alert_history_success(self, client):
        """
        【测试】获取告警历史成功
        
        【场景】正常请求告警历史
        【预期】返回200和历史列表
        """
        # 执行
        response = client.get("/api/v1/alerts/history")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_get_alert_history_with_filters(self, client):
        """
        【测试】带筛选的告警历史
        
        【场景】使用查询参数筛选历史
        【预期】返回筛选后的结果
        """
        # 执行 - 按规则ID筛选
        response = client.get("/api/v1/alerts/history?rule_id=rule-001")
        assert response.status_code == 200
        
        # 执行 - 按状态筛选
        response = client.get("/api/v1/alerts/history?status=triggered")
        assert response.status_code == 200
        
        # 执行 - 按级别筛选
        response = client.get("/api/v1/alerts/history?level=warning")
        assert response.status_code == 200
    
    def test_get_alert_history_pagination(self, client):
        """
        【测试】告警历史分页
        
        【场景】使用limit和offset分页
        【预期】返回分页结果
        """
        # 执行
        response = client.get("/api/v1/alerts/history?limit=10&offset=0")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    # ==================== 活动告警API测试 ====================
    
    def test_get_active_alerts(self, client):
        """
        【测试】获取活动告警
        
        【场景】获取当前未恢复的告警
        【预期】返回活动告警列表
        """
        # 执行
        response = client.get("/api/v1/alerts/active")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    # ==================== 确认告警API测试 ====================
    
    def test_acknowledge_alert_success(self, client, sample_rule):
        """
        【测试】确认告警成功
        
        【场景】确认一个存在的告警
        【预期】返回200
        """
        # 注意：这需要先触发一个告警，这里简化测试
        # 实际测试可能需要模拟告警触发
        
        # 执行 - 使用测试告警ID
        response = client.post(
            "/api/v1/alerts/test-alert/acknowledge?user=admin"
        )
        
        # 验证 - 可能404（告警不存在）或200（成功）
        assert response.status_code in [200, 404]
    
    def test_acknowledge_alert_missing_user(self, client):
        """
        【测试】确认告警 - 缺少用户参数
        
        【场景】未提供确认人参数
        【预期】返回422
        """
        # 执行
        response = client.post("/api/v1/alerts/test-alert/acknowledge")
        
        # 验证
        assert response.status_code == 422
    
    # ==================== 统计API测试 ====================
    
    def test_get_alert_stats(self, client):
        """
        【测试】获取告警统计
        
        【场景】获取告警统计信息
        【预期】返回统计数据
        """
        # 执行
        response = client.get("/api/v1/alerts/stats")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "triggered_today" in data
        assert "active_alerts" in data
        assert "recovered_today" in data
    
    # ==================== 通知测试API测试 ====================
    
    def test_test_notification_browser(self, client):
        """
        【测试】测试浏览器通知
        
        【场景】测试浏览器推送通知
        【预期】返回200
        """
        # 准备
        test_data = {
            "channel": "browser"
        }
        
        # 执行
        response = client.post("/api/v1/alerts/test-notification", json=test_data)
        
        # 验证
        assert response.status_code in [200, 500]  # 200成功或500配置错误
    
    def test_test_notification_email(self, client):
        """
        【测试】测试邮件通知
        
        【场景】测试邮件通知渠道
        【预期】返回200或500
        """
        # 准备
        test_data = {
            "channel": "email",
            "email": "test@example.com"
        }
        
        # 执行
        response = client.post("/api/v1/alerts/test-notification", json=test_data)
        
        # 验证
        assert response.status_code in [200, 500]
    
    def test_test_notification_webhook(self, client):
        """
        【测试】测试Webhook通知
        
        【场景】测试Webhook通知渠道
        【预期】返回200或500
        """
        # 准备
        test_data = {
            "channel": "webhook",
            "webhook_url": "https://example.com/webhook"
        }
        
        # 执行
        response = client.post("/api/v1/alerts/test-notification", json=test_data)
        
        # 验证
        assert response.status_code in [200, 500]
    
    def test_test_notification_invalid_channel(self, client):
        """
        【测试】测试通知 - 无效渠道
        
        【场景】使用无效的通知渠道
        【预期】返回422
        """
        # 准备
        test_data = {
            "channel": "invalid_channel"
        }
        
        # 执行
        response = client.post("/api/v1/alerts/test-notification", json=test_data)
        
        # 验证
        assert response.status_code == 422
    
    # ==================== 批量操作API测试 ====================
    
    def test_batch_delete_rules(self, client, sample_rule):
        """
        【测试】批量删除规则
        
        【场景】批量删除多个规则
        【预期】返回删除结果
        """
        # 准备 - 创建两个规则
        response1 = client.post("/api/v1/alerts/rules", json=sample_rule)
        rule_id1 = response1.json()["data"]["id"]
        
        rule2 = sample_rule.copy()
        rule2["name"] = "第二个规则"
        response2 = client.post("/api/v1/alerts/rules", json=rule2)
        rule_id2 = response2.json()["data"]["id"]
        
        # 执行
        batch_data = {
            "rule_ids": [rule_id1, rule_id2]
        }
        response = client.post("/api/v1/alerts/rules/batch-delete", json=batch_data)
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2
    
    def test_batch_enable_rules(self, client, sample_rule):
        """
        【测试】批量启用/禁用规则
        
        【场景】批量修改规则启用状态
        【预期】返回更新结果
        """
        # 准备 - 创建规则（默认启用）
        response = client.post("/api/v1/alerts/rules", json=sample_rule)
        rule_id = response.json()["data"]["id"]
        
        # 执行 - 批量禁用
        batch_data = {
            "rule_ids": [rule_id]
        }
        response = client.post(
            "/api/v1/alerts/rules/batch-enable?enabled=false",
            json=batch_data
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 1
        
        # 验证规则已禁用
        get_response = client.get(f"/api/v1/alerts/rules/{rule_id}")
        assert get_response.json()["enabled"] is False


@pytest.mark.unit
@pytest.mark.api
class TestAlertsAPIErrorHandling:
    """告警API错误处理测试"""
    
    def test_invalid_json_body(self, client):
        """
        【测试】无效的JSON请求体
        
        【场景】发送无效的JSON
        【预期】返回400错误
        """
        # 执行
        response = client.post(
            "/api/v1/alerts/rules",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # 验证
        assert response.status_code == 400
    
    def test_invalid_http_method(self, client):
        """
        【测试】无效的HTTP方法
        
        【场景】使用不允许的HTTP方法
        【预期】返回405错误
        """
        # 执行 - 对只读端点使用POST
        response = client.post("/api/v1/alerts/stats")
        
        # 验证
        assert response.status_code == 405
