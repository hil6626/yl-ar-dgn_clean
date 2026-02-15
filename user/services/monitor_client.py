#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 监控服务客户端
负责向YL-monitor上报状态、心跳和性能指标
"""

import threading
import requests
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, Callable

import logging
logger = logging.getLogger('MonitorClient')


class MonitorClient:
    """
    监控服务客户端
    实现与YL-monitor的通信，上报状态和接收命令
    """
    
    def __init__(
        self,
        node_id: str = 'user-gui',
        node_name: str = 'User GUI Application',
        monitor_host: str = 'localhost',
        monitor_port: int = 5500,
        heartbeat_interval: int = 30,
        enabled: bool = True
    ):
        self.node_id = node_id
        self.node_name = node_name
        self.monitor_url = f"http://{monitor_host}:{monitor_port}"
        self.heartbeat_interval = heartbeat_interval
        self.enabled = enabled
        
        # 状态
        self.running = False
        self.last_heartbeat = None
        self.status = 'initializing'
        self.metadata = {}
        
        # 线程
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 回调
        self._status_callbacks: list[Callable] = []
        self._command_callbacks: Dict[str, Callable] = {}
        
        # 本地HTTP服务（用于接收监控命令）
        self._local_server = None
        self._local_port = 5502
        
        logger.info(f"监控客户端初始化: {node_id} -> {self.monitor_url}")
    
    def add_status_callback(self, callback: Callable):
        """添加状态变更回调"""
        self._status_callbacks.append(callback)
    
    def add_command_handler(self, command: str, handler: Callable):
        """添加命令处理器"""
        self._command_callbacks[command] = handler
    
    def _notify_status_change(self, old_status: str, new_status: str):
        """通知状态变更"""
        for callback in self._status_callbacks:
            try:
                callback(old_status, new_status)
            except Exception as e:
                logger.error(f"状态回调执行失败: {e}")
    
    def start(self):
        """启动监控客户端"""
        if not self.enabled:
            logger.info("监控客户端已禁用")
            return
            
        if self.running:
            logger.warning("监控客户端已在运行")
            return
            
        self.running = True
        self._stop_event.clear()
        
        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name='MonitorHeartbeat',
            daemon=True
        )
        self._heartbeat_thread.start()
        
        # 启动本地HTTP服务
        self._start_local_server()
        
        self.status = 'online'
        logger.info("监控客户端已启动")
        
        # 发送初始心跳
        self._send_heartbeat()
    
    def stop(self):
        """停止监控客户端"""
        if not self.running:
            return
            
        self.running = False
        self._stop_event.set()
        
        # 停止心跳线程
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5)
        
        # 停止本地HTTP服务
        self._stop_local_server()
        
        self.status = 'offline'
        logger.info("监控客户端已停止")
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while not self._stop_event.is_set():
            try:
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                
                # 状态降级
                if self.status == 'online':
                    old_status = self.status
                    self.status = 'degraded'
                    self._notify_status_change(old_status, self.status)
            
            # 等待下一次心跳
            self._stop_event.wait(self.heartbeat_interval)
    
    def _send_heartbeat(self):
        """发送心跳"""
        if not self.enabled:
            return
            
        try:
            # 收集状态数据
            data = self._collect_status()
            
            # 发送心跳
            url = f"{self.monitor_url}/api/v1/ar/heartbeat"
            response = requests.post(
                url,
                json=data,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.last_heartbeat = datetime.utcnow()
                
                # 恢复状态
                if self.status in ['degraded', 'error']:
                    old_status = self.status
                    self.status = 'online'
                    self._notify_status_change(old_status, self.status)
                
                logger.debug(f"心跳发送成功: {self.node_id}")
            else:
                logger.warning(f"心跳发送失败: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            logger.warning("无法连接到监控服务")
            raise
        except requests.exceptions.Timeout:
            logger.warning("心跳发送超时")
            raise
        except Exception as e:
            logger.error(f"心跳发送异常: {e}")
            raise
    
    def _collect_status(self) -> Dict[str, Any]:
        """收集状态数据"""
        try:
            # 系统资源
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            resources = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_available': memory.available
            }
            
            # GUI状态
            gui_status = {
                'status': self.status,
                'window_visible': True,  # 由GUI更新
                'camera_active': False,  # 由GUI更新
                'microphone_active': False,  # 由GUI更新
                'current_scene': None,  # 由GUI更新
            }
            
            return {
                'node_id': self.node_id,
                'node_name': self.node_name,
                'node_type': 'user-gui',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'status': self.status,
                'resources': resources,
                'gui': gui_status,
                'metadata': self.metadata
            }
            
        except Exception as e:
            logger.error(f"状态收集失败: {e}")
            return {
                'node_id': self.node_id,
                'node_name': self.node_name,
                'node_type': 'user-gui',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'status': 'error',
                'error': str(e)
            }
    
    def update_gui_status(self, **kwargs):
        """更新GUI状态"""
        if 'gui' not in self.metadata:
            self.metadata['gui'] = {}
        self.metadata['gui'].update(kwargs)
    
    def _start_local_server(self):
        """启动本地HTTP服务接收监控命令"""
        try:
            from flask import Flask, request, jsonify
            
            app = Flask(__name__)
            
            @app.route('/health', methods=['GET'])
            def health():
                """健康检查端点"""
                return jsonify({
                    'status': 'healthy',
                    'service': 'user-gui',
                    'node_id': self.node_id,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
            
            @app.route('/status', methods=['GET'])
            def status():
                """状态查询端点"""
                return jsonify(self._collect_status())
            
            @app.route('/command', methods=['POST'])
            def command():
                """接收监控命令"""
                try:
                    data = request.get_json()
                    cmd = data.get('command')
                    
                    if cmd in self._command_callbacks:
                        callback = self._command_callbacks[cmd]
                        result = callback(data.get('params', {}))
                        return jsonify({
                            'status': 'success',
                            'result': result,
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        })
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': f'未知命令: {cmd}',
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        }), 400
                        
                except Exception as e:
                    logger.error(f"命令处理失败: {e}")
                    return jsonify({
                        'status': 'error',
                        'message': str(e),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }), 500
            
            # 在后台线程启动服务
            def run_server():
                app.run(
                    host='0.0.0.0',
                    port=self._local_port,
                    debug=False,
                    threaded=True,
                    use_reloader=False
                )
            
            server_thread = threading.Thread(
                target=run_server, daemon=True
            )
            server_thread.start()
            
            logger.info(
                f"本地HTTP服务已启动: "
                f"http://localhost:{self._local_port}"
            )
            
        except ImportError:
            logger.warning("Flask未安装，本地HTTP服务未启动")
        except Exception as e:
            logger.error(f"本地HTTP服务启动失败: {e}")
    
    def _stop_local_server(self):
        """停止本地HTTP服务"""
        # Flask服务在守护线程中，会自动停止
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'node_id': self.node_id,
            'status': self.status,
            'running': self.running,
            'last_heartbeat': (
                self.last_heartbeat.isoformat()
                if self.last_heartbeat else None
            ),
            'monitor_url': self.monitor_url
        }


# 全局客户端实例
_monitor_client: Optional[MonitorClient] = None


def get_monitor_client() -> Optional[MonitorClient]:
    """获取全局监控客户端"""
    return _monitor_client


def init_monitor_client(**kwargs) -> MonitorClient:
    """初始化监控客户端"""
    global _monitor_client
    _monitor_client = MonitorClient(**kwargs)
    return _monitor_client


def start_monitoring():
    """启动监控"""
    client = get_monitor_client()
    if client:
        client.start()


def stop_monitoring():
    """停止监控"""
    client = get_monitor_client()
    if client:
        client.stop()


def update_gui_status(**kwargs):
    """更新GUI状态"""
    client = get_monitor_client()
    if client:
        client.update_gui_status(**kwargs)


__all__ = [
    'MonitorClient',
    'get_monitor_client',
    'init_monitor_client',
    'start_monitoring',
    'stop_monitoring',
    'update_gui_status'
]
