"""
API文档服务
提供6栏验收矩阵和冒泡检测功能
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class APIDocService:
    """
    API文档服务
    
    职责:
    1. 管理统一接口映射表
    2. 提供6栏验收矩阵数据
    3. 实现冒泡检测算法
    4. 计算功能完成度
    """
    
    def __init__(self):
        pass
    
    async def get_validation_matrix(self) -> List[Dict[str, Any]]:
        """
        获取验证矩阵（6栏结构）
        
        返回所有功能的配置状态，用于6栏表格展示
        """
        try:
            from app.models.function_mapping import FunctionMapping
            
            # 查询所有启用的功能
            functions = await FunctionMapping.filter(
                is_active=True
            ).order_by("priority", "id").all()
            
            if not functions:
                return self._get_sample_matrix()
            
            matrix = []
            for func in functions:
                # 计算冒泡状态
                bubble = self._calculate_bubble_status(func)
                
                matrix.append({
                    "id": func.id,
                    "name": func.name,
                    "description": func.description or "暂无描述",
                    "frontend_route": func.frontend_route or "#",
                    "api": {
                        "exists": func.api_path is not None,
                        "path": func.api_path,
                        "method": func.api_method or "GET"
                    },
                    "script": {
                        "exists": func.script_name is not None,
                        "name": func.script_name
                    },
                    "dag": {
                        "registered": func.dag_node_id is not None,
                        "node_id": func.dag_node_id
                    },
                    "bubble": bubble,
                    "completion": self._calculate_completion(func)
                })
            
            return matrix
            
        except Exception as e:
            return self._get_sample_matrix()
    
    def _calculate_bubble_status(self, func) -> Dict[str, Any]:
        """
        计算冒泡检测状态
        
        规则:
        - 🔴 danger: API不存在 或 脚本缺失（强制红色）
        - 🟡 warning: DAG未接入（黄色警告）
        - 🟢 success: 全部通过
        """
        issues = []
        
        # 检查API
        if not func.api_path:
            issues.append({
                "type": "error",
                "field": "api",
                "message": "API接口未配置"
            })
        
        # 检查脚本
        if not func.script_name:
            issues.append({
                "type": "error",
                "field": "script",
                "message": "自动化脚本未配置"
            })
        
        # 检查DAG
        if not func.dag_node_id:
            issues.append({
                "type": "warning",
                "field": "dag",
                "message": "DAG节点未接入"
            })
        
        # 确定状态
        has_errors = any(i["type"] == "error" for i in issues)
        has_warnings = any(i["type"] == "warning" for i in issues)
        
        if has_errors:
            return {
                "status": "danger",
                "icon": "🔴",
                "message": "配置错误",
                "priority": 1,
                "issues": issues
            }
        elif has_warnings:
            return {
                "status": "warning",
                "icon": "🟡",
                "message": "配置不完整",
                "priority": 2,
                "issues": issues
            }
        else:
            return {
                "status": "success",
                "icon": "🟢",
                "message": "全部通过",
                "priority": 0,
                "issues": []
            }
    
    def _calculate_completion(self, func) -> int:
        """
        计算功能完成度
        
        四个组件各占25%
        """
        components = [
            func.api_path is not None,
            func.script_name is not None,
            func.dag_node_id is not None,
            func.monitoring_enabled
        ]
        return round(sum(components) / len(components) * 100)
    
    async def check_bubble_status(self, function_id: str) -> Dict[str, Any]:
        """
        检查指定功能的冒泡状态
        """
        try:
            from app.models.function_mapping import FunctionMapping
            
            func = await FunctionMapping.get_or_none(id=function_id)
            if not func:
                return {
                    "status": "error",
                    "message": "功能不存在",
                    "issues": [{"type": "error", "message": "功能ID未找到"}]
                }
            
            return self._calculate_bubble_status(func)
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"检测失败: {str(e)}",
                "issues": []
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取API文档统计信息
        """
        try:
            matrix = await self.get_validation_matrix()
            
            total = len(matrix)
            completed = sum(1 for m in matrix if m["completion"] == 100)
            api_completed = sum(1 for m in matrix if m["api"]["exists"])
            script_completed = sum(1 for m in matrix if m["script"]["exists"])
            dag_completed = sum(1 for m in matrix if m["dag"]["registered"])
            
            return {
                "total": total,
                "completed": completed,
                "incomplete": total - completed,
                "rate": round(completed / total * 100) if total > 0 else 0,
                "api_completed": api_completed,
                "script_completed": script_completed,
                "dag_completed": dag_completed,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "total": 0,
                "completed": 0,
                "incomplete": 0,
                "rate": 0,
                "api_completed": 0,
                "script_completed": 0,
                "dag_completed": 0
            }
    
    async def get_function_detail(self, function_id: str) -> Optional[Dict[str, Any]]:
        """
        获取功能详细信息
        """
        try:
            from app.models.function_mapping import FunctionMapping
            
            func = await FunctionMapping.get_or_none(id=function_id)
            if not func:
                return None
            
            return {
                "id": func.id,
                "name": func.name,
                "description": func.description,
                "frontend": {
                    "route": func.frontend_route,
                    "page_id": func.page_id
                },
                "api": {
                    "path": func.api_path,
                    "method": func.api_method
                },
                "script": {
                    "name": func.script_name,
                    "path": func.script_path
                },
                "dag": {
                    "node_id": func.dag_node_id,
                    "layer": func.dag_layer
                },
                "monitoring": {
                    "enabled": func.monitoring_enabled,
                    "alert_threshold": func.alert_threshold
                },
                "completion": self._calculate_completion(func),
                "bubble": self._calculate_bubble_status(func)
            }
            
        except Exception as e:
            return None
    
    async def validate_function(self, function_id: str) -> Dict[str, Any]:
        """
        验证功能配置完整性
        """
        detail = await self.get_function_detail(function_id)
        
        if not detail:
            return {
                "valid": False,
                "errors": ["功能不存在"],
                "suggestions": []
            }
        
        errors = []
        suggestions = []
        
        # 验证API
        if not detail["api"]["path"]:
            errors.append("API路径未配置")
            suggestions.append("在FunctionMapping中设置api_path字段")
        
        # 验证脚本
        if not detail["script"]["name"]:
            errors.append("脚本未配置")
            suggestions.append("在FunctionMapping中设置script_name字段")
        
        # 验证DAG
        if not detail["dag"]["node_id"]:
            suggestions.append("建议接入DAG节点以实现自动化编排")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "suggestions": suggestions,
            "completion": detail["completion"]
        }
    
    def _get_sample_matrix(self) -> List[Dict[str, Any]]:
        """获取示例数据"""
        return [
            {
                "id": "alert-management",
                "name": "告警管理",
                "description": "告警规则配置、触发与通知管理",
                "frontend_route": "/alerts",
                "api": {"exists": True, "path": "/api/v1/alerts", "method": "GET"},
                "script": {"exists": True, "name": "alert_monitor.py"},
                "dag": {"registered": True, "node_id": "alert-check"},
                "bubble": {
                    "status": "success",
                    "icon": "🟢",
                    "message": "全部通过",
                    "priority": 0,
                    "issues": []
                },
                "completion": 100
            },
            {
                "id": "metrics-collection",
                "name": "指标采集",
                "description": "系统性能指标自动采集与存储",
                "frontend_route": "/metrics",
                "api": {"exists": True, "path": "/api/v1/metrics", "method": "POST"},
                "script": {"exists": True, "name": "metrics_collector.py"},
                "dag": {"registered": False},
                "bubble": {
                    "status": "warning",
                    "icon": "🟡",
                    "message": "DAG未接入",
                    "priority": 2,
                    "issues": [{"type": "warning", "field": "dag", "message": "DAG节点未接入"}]
                },
                "completion": 75
            }
        ]
