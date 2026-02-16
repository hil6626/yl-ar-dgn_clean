#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
统一管理User GUI的配置
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class UserGUIConfig:
    """User GUI配置管理器"""
    
    DEFAULT_CONFIG = {
        "ar_backend_host": "0.0.0.0",
        "ar_backend_port": 5501,
        "yl_monitor_host": "0.0.0.0",
        "yl_monitor_port": 5500,
        "video": {
            "default_resolution": "1280x720",
            "default_fps": 30,
            "auto_start": False
        },
        "audio": {
            "default_device": "default",
            "default_volume": 100,
            "default_pitch": 0
        },
        "gui": {
            "theme": "dark",
            "window_width": 1400,
            "window_height": 900,
            "fullscreen": False
        },
        "monitoring": {
            "status_report_interval": 30,
            "heartbeat_interval": 10,
            "local_http_port": 5502
        }
    }
    
    def __init__(self):
        self.config_path = self._get_config_path()
        self.config = self._load_config()
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 从当前文件位置推导
        current_file = Path(__file__).resolve()
        config_dir = current_file.parent
        return config_dir / "settings.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认配置，确保新字段存在
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(loaded)
                    return merged
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
                return self.DEFAULT_CONFIG.copy()
        else:
            # 首次运行，创建默认配置
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """保存配置"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.config = config
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        
        # 导航到正确的层级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存
        self.save_config()
    
    def get_ar_backend_url(self) -> str:
        """获取AR-backend URL"""
        host = self.get("ar_backend_host", "0.0.0.0")
        port = self.get("ar_backend_port", 5501)
        return f"http://{host}:{port}"
    
    def get_yl_monitor_url(self) -> str:
        """获取YL-monitor URL"""
        host = self.get("yl_monitor_host", "0.0.0.0")
        port = self.get("yl_monitor_port", 5500)
        return f"http://{host}:{port}"
    
    def get_local_http_port(self) -> int:
        """获取本地HTTP服务端口"""
        return self.get("monitoring.local_http_port", 5502)


# 全局配置实例
_config = None


def get_config() -> UserGUIConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = UserGUIConfig()
    return _config
