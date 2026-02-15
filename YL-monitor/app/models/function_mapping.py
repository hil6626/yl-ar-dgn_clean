"""
统一接口映射表模型
记录所有功能的前端、后端、脚本、DAG映射关系
"""

from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models import Base


class FunctionMapping(Base):
    """
    统一接口映射表
    
    记录所有功能模块的完整配置信息，包括：
    - 前端路由映射
    - 后端API接口
    - 自动化脚本
    - DAG节点
    - 监控配置
    """
    __tablename__ = "function_mappings"
    
    # 主键
    id = Column(String(50), primary_key=True, comment="功能ID")
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="功能名称")
    description = Column(Text, comment="功能描述")
    
    # 前端映射
    frontend_route = Column(String(200), comment="前端路由路径")
    page_id = Column(String(50), comment="页面ID")
    
    # 后端接口
    api_path = Column(String(200), comment="API路径")
    api_method = Column(String(10), default="GET", comment="HTTP方法")
    
    # 自动化脚本
    script_name = Column(String(100), comment="脚本名称")
    script_path = Column(String(200), comment="脚本路径")
    
    # DAG节点
    dag_node_id = Column(String(50), comment="DAG节点ID")
    dag_layer = Column(Integer, default=0, comment="DAG层级")
    
    # 监控配置
    monitoring_enabled = Column(Boolean, default=False, comment="是否启用监控")
    alert_threshold = Column(Integer, comment="告警阈值")
    
    # 分类和优先级
    category = Column(String(50), comment="功能分类")
    priority = Column(Integer, default=5, comment="优先级(1-10)")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "frontend_route": self.frontend_route,
            "api": {
                "exists": self.api_path is not None,
                "path": self.api_path,
                "method": self.api_method
            },
            "script": {
                "exists": self.script_name is not None,
                "name": self.script_name
            },
            "dag": {
                "registered": self.dag_node_id is not None,
                "node_id": self.dag_node_id
            },
            "monitoring_enabled": self.monitoring_enabled,
            "category": self.category,
            "priority": self.priority,
            "is_active": self.is_active
        }
    
    @classmethod
    async def get_by_id(cls, function_id: str):
        """根据ID获取功能映射"""
        return await cls.get_or_none(id=function_id)
    
    @classmethod
    async def get_active_functions(cls):
        """获取所有启用的功能"""
        return await cls.filter(is_active=True).order_by(cls.priority).all()
