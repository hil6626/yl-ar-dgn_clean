#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理模块
解决User GUI的模块导入路径问题
"""

import sys
from pathlib import Path


class PathManager:
    """路径管理器 - 统一管理项目路径和模块导入"""
    
    def __init__(self):
        self.project_root = self._find_project_root()
        self.ar_backend_path = self.project_root / "AR-backend"
        self.user_path = self.project_root / "user"
        
    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        # 从当前文件开始向上查找
        current = Path(__file__).resolve()
        
        # 尝试找到包含AR-backend和user目录的根目录
        for parent in [current, *current.parents]:
            if (parent / "AR-backend").exists() and (parent / "user").exists():
                return parent
        
        # 如果找不到，使用当前文件的父目录的父目录
        return current.parent.parent
    
    def setup_python_path(self):
        """设置Python导入路径"""
        # 添加AR-backend到路径
        if str(self.ar_backend_path) not in sys.path:
            sys.path.insert(0, str(self.ar_backend_path))
        
        # 添加AR-backend/core到路径
        core_path = self.ar_backend_path / "core"
        if str(core_path) not in sys.path:
            sys.path.insert(0, str(core_path))
        
        # 添加AR-backend/integrations到路径
        integrations_path = self.ar_backend_path / "integrations"
        if str(integrations_path) not in sys.path:
            sys.path.insert(0, str(integrations_path))
        
        # 添加AR-backend/app到路径
        app_path = self.ar_backend_path / "app"
        if str(app_path) not in sys.path:
            sys.path.insert(0, str(app_path))
        
        # 添加AR-backend/services到路径
        services_path = self.ar_backend_path / "services"
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))
    
    def get_ar_backend_path(self) -> Path:
        """获取AR-backend路径"""
        return self.ar_backend_path
    
    def get_user_path(self) -> Path:
        """获取user路径"""
        return self.user_path
    
    def get_config_path(self) -> Path:
        """获取配置文件路径"""
        return self.user_path / "config"
    
    def get_logs_path(self) -> Path:
        """获取日志目录路径"""
        return self.user_path / "logs"
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.get_config_path(),
            self.get_logs_path(),
            self.user_path / "assets",
            self.user_path / "manuals",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# 全局路径管理器实例
_path_manager = None


def get_path_manager() -> PathManager:
    """获取全局路径管理器实例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
        _path_manager.setup_python_path()
        _path_manager.ensure_directories()
    return _path_manager


def setup_paths():
    """快捷函数：设置所有路径"""
    manager = get_path_manager()
    return manager
