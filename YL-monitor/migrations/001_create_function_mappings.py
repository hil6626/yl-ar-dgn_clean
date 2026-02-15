"""
数据库迁移脚本 - 创建统一接口映射表
"""

from sqlalchemy import create_engine, Column, String, Text, Boolean, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

Base = declarative_base()


class FunctionMapping(Base):
    __tablename__ = "function_mappings"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    frontend_route = Column(String(200))
    page_id = Column(String(50))
    api_path = Column(String(200))
    api_method = Column(String(10), default="GET")
    script_name = Column(String(100))
    script_path = Column(String(200))
    dag_node_id = Column(String(50))
    dag_layer = Column(Integer, default=0)
    monitoring_enabled = Column(Boolean, default=False)
    alert_threshold = Column(Integer)
    category = Column(String(50))
    priority = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def to_dict(self):
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


def run_migration():
    """执行迁移"""
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/monitor.db")
    print(f"🔄 使用数据库: {db_url}")
    
    engine = create_engine(db_url, echo=False)
    
    # 创建表
    Base.metadata.create_all(engine)
    print("✅ 统一接口映射表创建成功")
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 检查是否已有数据
    existing = session.query(FunctionMapping).first()
    if existing:
        print("ℹ️ 表中已有数据，跳过示例数据插入")
        session.close()
        return
    
    # 插入示例数据
    sample_data = [
        FunctionMapping(
            id="alert-management",
            name="告警管理",
            description="告警规则配置、触发与通知管理",
            frontend_route="/alerts",
            page_id="alerts",
            api_path="/api/v1/alerts",
            api_method="GET",
            script_name="alert_monitor.py",
            script_path="scripts/alert/alert_monitor.py",
            dag_node_id="alert-check",
            dag_layer=1,
            monitoring_enabled=True,
            alert_threshold=80,
            category="monitor",
            priority=1
        ),
        FunctionMapping(
            id="metrics-collection",
            name="指标采集",
            description="系统性能指标自动采集与存储",
            frontend_route="/metrics",
            page_id="metrics",
            api_path="/api/v1/metrics",
            api_method="POST",
            script_name="metrics_collector.py",
            script_path="scripts/monitor/metrics_collector.py",
            monitoring_enabled=True,
            alert_threshold=90,
            category="monitor",
            priority=2
        ),
        FunctionMapping(
            id="dag-orchestration",
            name="DAG编排",
            description="可视化流程编排与执行",
            frontend_route="/dag",
            page_id="dag",
            api_path="/api/v1/dag",
            api_method="GET",
            dag_node_id="dag-engine",
            dag_layer=0,
            monitoring_enabled=True,
            category="orchestration",
            priority=3
        ),
        FunctionMapping(
            id="script-execution",
            name="脚本执行",
            description="自动化脚本管理与执行",
            frontend_route="/scripts",
            page_id="scripts",
            script_name="script_runner.py",
            script_path="scripts/tools/script_runner.py",
            monitoring_enabled=False,
            category="automation",
            priority=4
        ),
        FunctionMapping(
            id="dashboard-monitor",
            name="仪表盘监控",
            description="全局监控控制台",
            frontend_route="/dashboard",
            page_id="dashboard",
            api_path="/api/v1/dashboard",
            api_method="GET",
            monitoring_enabled=True,
            category="monitor",
            priority=1
        ),
        FunctionMapping(
            id="api-documentation",
            name="API文档",
            description="API接口文档与验收矩阵",
            frontend_route="/api-doc",
            page_id="api-doc",
            api_path="/api/v1/api-doc",
            api_method="GET",
            monitoring_enabled=False,
            category="documentation",
            priority=5
        ),
        FunctionMapping(
            id="ar-monitoring",
            name="AR监控",
            description="AR设备实时监控",
            frontend_route="/ar",
            page_id="ar",
            api_path="/api/v1/ar",
            api_method="GET",
            script_name="ar_monitor.py",
            dag_node_id="ar-check",
            monitoring_enabled=True,
            category="monitor",
            priority=2
        ),
        FunctionMapping(
            id="intelligent-alert",
            name="智能告警",
            description="基于AI的智能告警分析",
            frontend_route="/intelligent-alert",
            page_id="intelligent-alert",
            api_path="/api/v1/intelligent-alert",
            api_method="GET",
            script_name="intelligent_alert.py",
            monitoring_enabled=True,
            category="ai",
            priority=3
        )
    ]
    
    session.add_all(sample_data)
    session.commit()
    print(f"✅ 已插入 {len(sample_data)} 条示例数据")
    
    # 显示插入的数据
    print("\n📋 已创建的功能映射:")
    for func in sample_data:
        completion = 0
        if func.api_path:
            completion += 25
        if func.script_name:
            completion += 25
        if func.dag_node_id:
            completion += 25
        if func.monitoring_enabled:
            completion += 25
        
        status = "✅" if completion == 100 else "⚠️"
        print(f"  {status} {func.name} ({func.id}) - 完成度: {completion}%")
    
    session.close()
    print("\n🎉 迁移完成！")


if __name__ == "__main__":
    run_migration()
