#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一路径管理模块
确保无论AR项目根目录在哪里，所有路径都能正确解析

功能特性：
- 自动检测项目根目录（容器/本地通用）
- 提供所有常用的相对路径
- 支持路径验证和创建
- 单例模式全局访问

生成者: Copilot
最后更新: 2026-02-04
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional


class PathManager:
    """
    统一的路径管理器
    - 自动检测项目根目录（容器/本地通用）
    - 提供所有常用的相对路径
    - 支持路径验证和创建
    
    使用方式：
        from path_manager import get_path_manager
        
        pm = get_path_manager()
        config_file = pm.app_config_file
        log_file = pm.get_log_file('app.log')
    """
    
    _instance: Optional['PathManager'] = None
    _project_root: Optional[Path] = None
    
    def __new__(cls):
        """单例模式确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化路径管理器"""
        if getattr(self, '_initialized', False):
            return
        
        self._project_root = self._detect_project_root()
        if self._project_root is None:
            raise RuntimeError(
                "无法找到AR项目根目录。"
                "请确保在项目目录内运行程序，或设置AR_PROJECT_ROOT环境变量。"
            )
        
        self._initialized = True
    
    @classmethod
    def _detect_project_root(cls) -> Optional[Path]:
        """
        自动检测项目根目录（环境无关）
        
        检测顺序：
        1. 环境变量 AR_PROJECT_ROOT
        2. 当前工作目录
        3. 脚本所在目录及其父目录
        4. 遍历当前目录的父目录
        5. 容器标准路径（兼容容器环境）
        """
        # 方法1：环境变量（最高优先级）
        env_root = os.getenv('AR_PROJECT_ROOT')
        if env_root and cls._is_project_root(Path(env_root)):
            return Path(env_root).resolve()
        
        # 方法2：当前工作目录
        cwd = Path.cwd()
        if cls._is_project_root(cwd):
            return cwd.resolve()
        
        # 方法3：脚本所在目录及其父目录
        script_dir = Path(__file__).parent
        for path in [script_dir, script_dir.parent, script_dir.parent.parent]:
            if cls._is_project_root(path):
                return path.resolve()
        
        # 方法4：遍历当前目录的父目录
        current = cwd
        for _ in range(10):  # 向上最多查找10层
            if cls._is_project_root(current):
                return current.resolve()
            parent = current.parent
            if parent == current:  # 到达文件系统根目录
                break
            current = parent
        
        # 方法5：常见容器路径（兼容容器环境）
        for container_root in ("/workspaces/AR", "/app", "/workspace/AR"):
            container_path = Path(container_root)
            if cls._is_project_root(container_path):
                return container_path.resolve()
        
        return None
    
    @staticmethod
    def _is_project_root(path: Path) -> bool:
        """
        检查目录是否为AR项目根目录
        
        Args:
            path: 要检查的目录路径
            
        Returns:
            bool: 是否为项目根目录
        """
        required_files = [
            'requirements.txt',
            'src/launcher.py',
            'src/backend/monitor_app.py',
            'config/app_config.json',
        ]
        
        return all((path / file).exists() for file in required_files)
    
    @property
    def project_root(self) -> Path:
        """获取项目根目录"""
        return self._project_root
    
    # ==================== 主要目录路径 ====================
    
    @property
    def src_dir(self) -> Path:
        """源代码目录"""
        return self._project_root / 'src'
    
    @property
    def backend_dir(self) -> Path:
        """后端代码目录"""
        return self.src_dir / 'backend'
    
    @property
    def frontend_dir(self) -> Path:
        """前端代码目录"""
        return self.src_dir / 'frontend'
    
    @property
    def config_dir(self) -> Path:
        """配置文件目录"""
        return self._project_root / 'config'
    
    @property
    def logs_dir(self) -> Path:
        """日志文件目录"""
        return self._project_root / 'logs'
    
    @property
    def data_dir(self) -> Path:
        """数据文件目录"""
        return self._project_root / 'data'
    
    @property
    def backups_dir(self) -> Path:
        """备份目录"""
        return self._project_root / 'backups'
    
    @property
    def scripts_dir(self) -> Path:
        """脚本目录"""
        return self._project_root / 'scripts'
    
    @property
    def test_dir(self) -> Path:
        """测试目录"""
        return self._project_root / 'test'
    
    @property
    def docs_dir(self) -> Path:
        """文档目录"""
        return self._project_root / 'docs'
    
    @property
    def rules_dir(self) -> Path:
        """规则目录"""
        return self._project_root / 'rules'
    
    @property
    def reports_dir(self) -> Path:
        """报告目录"""
        return self._project_root / 'reports'
    
    # ==================== 配置文件路径 ====================
    
    @property
    def app_config_file(self) -> Path:
        """应用配置文件"""
        return self.config_dir / 'app_config.json'
    
    @property
    def database_config_file(self) -> Path:
        """数据库配置文件"""
        return self.config_dir / 'database_config.json'
    
    @property
    def logging_config_file(self) -> Path:
        """日志配置文件"""
        return self.config_dir / 'logging_config.yaml'
    
    @property
    def monitoring_config_file(self) -> Path:
        """监控配置文件"""
        return self.config_dir / 'monitoring_config.json'
    
    @property
    def security_config_file(self) -> Path:
        """安全配置文件"""
        return self.config_dir / 'security_config.json'
    
    @property
    def version_file(self) -> Path:
        """版本文件"""
        return self.config_dir / 'version.json'
    
    # ==================== 工具方法 ====================
    
    def ensure_dir_exists(self, path: Optional[Path] = None) -> Path:
        """
        确保目录存在，不存在则创建
        
        Args:
            path: 要检查的路径，None时使用project_root
            
        Returns:
            Path: 已确保存在的目录路径
        """
        target = path or self._project_root
        target.mkdir(parents=True, exist_ok=True)
        return target
    
    def get_log_file(self, name: str) -> Path:
        """
        获取日志文件路径（自动确保目录存在）
        
        Args:
            name: 日志文件名
            
        Returns:
            Path: 日志文件的完整路径
        """
        self.ensure_dir_exists(self.logs_dir)
        return self.logs_dir / name
    
    def get_config(self, config_name: str) -> Dict:
        """
        读取JSON配置文件
        
        Args:
            config_name: 配置文件名（不含.json扩展名）
            
        Returns:
            Dict: 配置内容
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON格式错误
        """
        config_file = self.config_dir / f'{config_name}.json'
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"配置文件格式错误: {config_file}",
                e.doc,
                e.pos
            )
    
    def save_config(self, config_name: str, config_data: Dict) -> None:
        """
        保存JSON配置文件
        
        Args:
            config_name: 配置文件名（不含.json扩展名）
            config_data: 配置内容
        """
        self.ensure_dir_exists(self.config_dir)
        config_file = self.config_dir / f'{config_name}.json'
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    def to_dict(self) -> Dict[str, str]:
        """
        将所有路径导出为字典
        
        Returns:
            Dict: 所有路径的字典表示
        """
        return {
            'project_root': str(self.project_root),
            'src_dir': str(self.src_dir),
            'backend_dir': str(self.backend_dir),
            'frontend_dir': str(self.frontend_dir),
            'config_dir': str(self.config_dir),
            'logs_dir': str(self.logs_dir),
            'data_dir': str(self.data_dir),
            'backups_dir': str(self.backups_dir),
            'scripts_dir': str(self.scripts_dir),
            'test_dir': str(self.test_dir),
            'docs_dir': str(self.docs_dir),
            'rules_dir': str(self.rules_dir),
            'reports_dir': str(self.reports_dir),
        }
    
    def __str__(self) -> str:
        """返回项目根目录字符串"""
        return str(self._project_root)
    
    def __repr__(self) -> str:
        """返回详细表示"""
        return f"PathManager(project_root={self._project_root})"


# ==================== 全局实例快速访问 ====================

def get_path_manager() -> PathManager:
    """
    获取全局路径管理器实例（单例）
    
    Returns:
        PathManager: 全局路径管理器实例
        
    示例：
        pm = get_path_manager()
        log_file = pm.get_log_file('app.log')
    """
    return PathManager()


def get_project_root() -> Path:
    """
    快速获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    return get_path_manager().project_root
