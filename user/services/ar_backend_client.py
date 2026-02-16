#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR-backend 服务客户端
用于User GUI与AR-backend通信
"""

import requests
import json
import socket
from typing import Optional, Dict, Any


class ARBackendClient:
    """AR-backend HTTP客户端"""
    
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORTS = [5501, 5503, 5504, 5505]
    TIMEOUT = 5
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or self._discover_host()
        self.port = port or self._discover_port()
        self.base_url = f"http://{self.host}:{self.port}"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _discover_host(self) -> str:
        """自动发现服务主机"""
        # 1. 检查环境变量
        host = __import__('os').getenv("AR_BACKEND_HOST")
        if host:
            return host
        
        # 2. 检查配置文件
        try:
            config_path = (
                __import__('pathlib').Path(__file__).parent.parent /
                "config" / "settings.json"
            )
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if config.get("ar_backend_host"):
                        return config["ar_backend_host"]
        except Exception:
            pass
        
        # 3. 默认本地
        return self.DEFAULT_HOST
    
    def _discover_port(self) -> int:
        """自动发现服务端口"""
        # 1. 检查环境变量
        import os
        port = os.getenv("AR_BACKEND_PORT")
        if port:
            return int(port)
        
        # 2. 检查配置文件
        try:
            config_path = (
                __import__('pathlib').Path(__file__).parent.parent /
                "config" / "settings.json"
            )
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if config.get("ar_backend_port"):
                        return config["ar_backend_port"]
        except Exception:
            pass
        
        # 3. 尝试默认端口
        for port in self.DEFAULT_PORTS:
            if self._check_port(self.host, port):
                return port
        
        # 4. 返回默认端口
        return self.DEFAULT_PORTS[0]
    
    def _check_port(self, host: str, port: int) -> bool:
        """检查端口是否开放"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/status",
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/metrics",
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def start_video(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """启动视频处理"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/video/start",
                json=params or {},
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def stop_video(self) -> Dict[str, Any]:
        """停止视频处理"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/video/stop",
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def start_audio(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """启动音频处理"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/audio/start",
                json=params or {},
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def stop_audio(self) -> Dict[str, Any]:
        """停止音频处理"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/audio/stop",
                timeout=self.TIMEOUT
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        health = self.health_check()
        return health.get("status") == "healthy"


# 全局客户端实例
_client = None


def get_client() -> ARBackendClient:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = ARBackendClient()
    return _client


def check_backend() -> bool:
    """快捷函数：检查后端是否可用"""
    return get_client().is_available()
