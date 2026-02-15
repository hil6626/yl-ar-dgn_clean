#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理模块
统一处理项目路径，解决导入问题
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Union

# 项目根目录缓存
_project_root: Optional[Path] = None


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    """
    global _project_root
    
    if _project_root is not None:
        return _project_root
    
    # 尝试多种方式定位项目根目录
    possible_roots = [
        # 从当前文件向上查找
        Path(__file__).parent.parent.parent,
        # 从当前工作目录
        Path.cwd(),
        # 从已知的项目结构
        Path('/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean'),
    ]
    
    # 查找包含关键目录的路径
    for path in possible_roots:
        if (path / 'AR-backend').exists() and (path / 'YL-monitor').exists():
            _project_root = path
            return path
    
    # 如果找不到，使用第一个可能的路径
    _project_root = possible_roots[0]
    return _project_root


def get_ar_backend_path() -> Path:
    """获取AR-backend目录路径"""
    return get_project_root() / 'AR-backend'


def get_yl_monitor_path() -> Path:
    """获取YL-monitor目录路径"""
    return get_project_root() / 'YL-monitor'


def get_user_path() -> Path:
    """获取user目录路径"""
    return get_project_root() / 'user'


def setup_python_path() -> None:
    """
    设置Python导入路径
    将项目关键目录添加到sys.path
    """
    root = get_project_root()
    
    paths_to_add = [
        str(root),
        str(root / 'AR-backend'),
        str(root / 'AR-backend' / 'core'),
        str(root / 'AR-backend' / 'app'),
        str(root / 'YL-monitor'),
        str(root / 'user'),
    ]
    
    # 逆序添加，确保优先级正确
    for path in reversed(paths_to_add):
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置环境变量
    os.environ['PROJECT_ROOT'] = str(root)
    os.environ['AR_BACKEND_PATH'] = str(root / 'AR-backend')
    os.environ['YL_MONITOR_PATH'] = str(root / 'YL-monitor')


def ensure_directories() -> None:
    """确保必要的目录存在"""
    user_path = get_user_path()
    
    directories = [
        user_path / 'logs',
        user_path / 'config',
        user_path / 'cache',
        user_path / 'temp',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_config_path(filename: Optional[str] = None) -> Path:
    """
    获取配置文件路径
    
    Args:
        filename: 配置文件名，为None则返回配置目录
        
    Returns:
        Path: 配置路径
    """
    config_dir = get_user_path() / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    if filename:
        return config_dir / filename
    return config_dir


def get_log_path(filename: Optional[str] = None) -> Path:
    """
    获取日志文件路径
    
    Args:
        filename: 日志文件名，为None则返回日志目录
        
    Returns:
        Path: 日志路径
    """
    log_dir = get_user_path() / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if filename:
        return log_dir / filename
    return log_dir


def get_cache_path(filename: Optional[str] = None) -> Path:
    """
    获取缓存文件路径
    
    Args:
        filename: 缓存文件名，为None则返回缓存目录
        
    Returns:
        Path: 缓存路径
    """
    cache_dir = get_user_path() / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    if filename:
        return cache_dir / filename
    return cache_dir


def find_file(
    filename: str,
    search_paths: Optional[List[Path]] = None
) -> Optional[Path]:
    """
    在多个路径中查找文件
    
    Args:
        filename: 要查找的文件名
        search_paths: 搜索路径列表，为None则使用默认路径
        
    Returns:
        Optional[Path]: 找到的文件路径，未找到返回None
    """
    if search_paths is None:
        search_paths = [
            get_user_path(),
            get_ar_backend_path(),
            get_yl_monitor_path(),
            get_project_root(),
        ]
    
    for path in search_paths:
        file_path = path / filename
        if file_path.exists():
            return file_path
    
    return None


def resolve_path(path: Union[str, Path]) -> Path:
    """
    解析路径，支持相对路径和绝对路径
    
    Args:
        path: 路径字符串或Path对象
        
    Returns:
        Path: 解析后的绝对路径
    """
    path = Path(path)
    
    if path.is_absolute():
        return path
    
    # 尝试相对于项目根目录解析
    root_relative = get_project_root() / path
    if root_relative.exists():
        return root_relative.resolve()
    
    # 尝试相对于当前工作目录解析
    cwd_relative = Path.cwd() / path
    if cwd_relative.exists():
        return cwd_relative.resolve()
    
    # 返回相对于项目根目录的路径（即使不存在）
    return root_relative


# 初始化
setup_python_path()
ensure_directories()


__all__ = [
    'get_project_root',
    'get_ar_backend_path',
    'get_yl_monitor_path',
    'get_user_path',
    'setup_python_path',
    'ensure_directories',
    'get_config_path',
    'get_log_path',
    'get_cache_path',
    'find_file',
    'resolve_path',
]
