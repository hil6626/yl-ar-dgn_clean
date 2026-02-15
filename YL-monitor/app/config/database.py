"""
数据库连接池配置模块
提供高性能的数据库连接管理
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.database_url = os.getenv(
            'DATABASE_URL', 
            'sqlite:///data/monitor.db'
        )
        self.pool_size = int(os.getenv('DATABASE_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        self.echo = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
        
    def create_engine(self):
        """创建数据库引擎（带连接池）"""
        try:
            engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,  # 自动检测断开的连接
                echo=self.echo,
                # SQLite特定优化
                connect_args={
                    'check_same_thread': False
                } if 'sqlite' in self.database_url else {}
            )
            
            logger.info(
                f"数据库引擎创建成功: pool_size={self.pool_size}, "
                f"max_overflow={self.max_overflow}"
            )
            return engine
            
        except Exception as e:
            logger.error(f"数据库引擎创建失败: {e}")
            raise

# 全局数据库实例
_db_config = None
_engine = None
_SessionFactory = None

def init_db():
    """初始化数据库"""
    global _db_config, _engine, _SessionFactory
    
    if _engine is None:
        _db_config = DatabaseConfig()
        _engine = _db_config.create_engine()
        _SessionFactory = sessionmaker(bind=_engine)
        
    return _engine

def get_session():
    """获取数据库会话"""
    global _SessionFactory
    
    if _SessionFactory is None:
        init_db()
        
    return scoped_session(_SessionFactory)

@contextmanager
def session_scope():
    """提供事务范围的会话上下文管理器"""
    session = get_session()()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库事务失败: {e}")
        raise
    finally:
        session.close()

def get_engine():
    """获取数据库引擎"""
    global _engine
    
    if _engine is None:
        init_db()
        
    return _engine

def close_db():
    """关闭数据库连接"""
    global _engine
    
    if _engine:
        _engine.dispose()
        _engine = None
        logger.info("数据库连接已关闭")

# 连接池监控
def get_pool_status():
    """获取连接池状态"""
    global _engine
    
    if _engine is None:
        return {"status": "not_initialized"}
        
    pool = _engine.pool
    
    return {
        "status": "active",
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow()
    }
