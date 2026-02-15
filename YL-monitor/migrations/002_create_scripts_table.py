"""
数据库迁移脚本 - 创建脚本表
"""

from sqlalchemy import create_engine, Column, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

Base = declarative_base()


class Script(Base):
    __tablename__ = "scripts"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(JSON, default={})
    category = Column(String(50), default="tools")
    path = Column(String(200))
    status = Column(String(20), default="idle")
    polling = Column(JSON, default={"enabled": False, "interval": 300})
    lastLog = Column(Text, default="等待执行...")
    last_execution = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


def run_migration():
    """执行迁移"""
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/monitor.db")
    print(f"🔄 使用数据库: {db_url}")
    
    engine = create_engine(db_url, echo=False)
    
    # 创建表
    Base.metadata.create_all(engine)
    print("✅ 脚本表创建成功")
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 检查是否已有数据
    existing = session.query(Script).first()
    if existing:
        print("ℹ️ 表中已有数据，跳过示例数据插入")
        session.close()
        return
    
    # 插入示例脚本数据
    sample_scripts = [
        Script(
            id="cpu-monitor",
            name="CPU监控",
            description={
                "summary": "实时监控系统CPU使用率",
                "detail": "采集CPU使用率、负载平均值、进程数等指标",
                "business_value": "及时发现CPU资源瓶颈，预防系统过载",
                "tags": ["监控", "系统", "CPU"]
            },
            category="monitor",
            path="scripts/monitor/cpu_monitor.py",
            status="idle",
            polling={"enabled": True, "interval": 60},
            lastLog="上次执行: CPU使用率 45%"
        ),
        Script(
            id="disk-check",
            name="磁盘检查",
            description={
                "summary": "检查磁盘空间和inode使用情况",
                "detail": "监控磁盘使用率，预警磁盘空间不足",
                "business_value": "防止磁盘满导致系统故障",
                "tags": ["监控", "磁盘", "存储"]
            },
            category="maintenance",
            path="scripts/maintenance/disk_check.py",
            status="idle",
            polling={"enabled": True, "interval": 300},
            lastLog="上次执行: 磁盘使用率 67%"
        ),
        Script(
            id="alert-notify",
            name="告警通知",
            description={
                "summary": "发送告警通知到多渠道",
                "detail": "支持邮件、短信、Webhook等多种通知方式",
                "business_value": "确保告警及时送达，快速响应故障",
                "tags": ["告警", "通知", "运维"]
            },
            category="alert",
            path="scripts/alert/alert_notify.py",
            status="idle",
            polling={"enabled": False, "interval": 300},
            lastLog="等待执行..."
        ),
        Script(
            id="log-cleanup",
            name="日志清理",
            description={
                "summary": "自动清理过期日志文件",
                "detail": "按配置保留期清理日志，释放磁盘空间",
                "business_value": "自动化运维，减少人工干预",
                "tags": ["维护", "日志", "清理"]
            },
            category="maintenance",
            path="scripts/maintenance/log_cleanup.py",
            status="idle",
            polling={"enabled": True, "interval": 3600},
            lastLog="上次执行: 清理了 12 个日志文件"
        ),
        Script(
            id="metrics-collector",
            name="指标采集",
            description={
                "summary": "采集系统性能指标",
                "detail": "采集CPU、内存、磁盘、网络等指标并存储",
                "business_value": "为监控和告警提供数据基础",
                "tags": ["监控", "指标", "采集"]
            },
            category="monitor",
            path="scripts/monitor/metrics_collector.py",
            status="idle",
            polling={"enabled": True, "interval": 60},
            lastLog="上次执行: 采集了 24 个指标"
        ),
        Script(
            id="backup-archive",
            name="备份归档",
            description={
                "summary": "自动备份和归档数据",
                "detail": "定期备份数据库和配置文件到远程存储",
                "business_value": "保障数据安全，支持灾难恢复",
                "tags": ["备份", "归档", "数据安全"]
            },
            category="maintenance",
            path="scripts/maintenance/backup_archive.py",
            status="idle",
            polling={"enabled": True, "interval": 86400},
            lastLog="上次执行: 备份完成，大小 1.2GB"
        )
    ]
    
    session.add_all(sample_scripts)
    session.commit()
    print(f"✅ 已插入 {len(sample_scripts)} 条示例脚本数据")
    
    # 显示插入的数据
    print("\n📋 已创建的脚本:")
    for script in sample_scripts:
        polling_status = "🔄" if script.polling.get("enabled") else "⏸️"
        print(f"  {polling_status} {script.name} ({script.id}) - 分类: {script.category}")
    
    session.close()
    print("\n🎉 迁移完成！")


if __name__ == "__main__":
    run_migration()
