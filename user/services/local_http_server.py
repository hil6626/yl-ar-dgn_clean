#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 本地HTTP服务
提供本地状态查询接口
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Optional

logger = logging.getLogger('LocalHTTPServer')


class StatusHandler(BaseHTTPRequestHandler):
    """状态请求处理器"""
    
    status_reporter = None  # 由外部设置
    
    def log_message(self, format, *args):
        """自定义日志"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/health':
            self._send_health()
        elif self.path == '/status':
            self._send_status()
        elif self.path == '/stats':
            self._send_stats()
        else:
            self._send_error(404, "Not Found")
    
    def _send_health(self):
        """发送健康状态"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'healthy',
            'service': 'user-gui',
            'version': '2.0.0',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z'
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def _send_status(self):
        """发送详细状态"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.status_reporter:
            status = self.status_reporter._collect_status()
        else:
            status = {'status': 'unknown', 'error': 'Status reporter not initialized'}
        
        self.wfile.write(json.dumps(status).encode())
    
    def _send_stats(self):
        """发送统计信息"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.status_reporter:
            stats = self.status_reporter.get_stats()
        else:
            stats = {'error': 'Status reporter not initialized'}
        
        self.wfile.write(json.dumps(stats).encode())
    
    def _send_error(self, code: int, message: str):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            'error': message,
            'code': code
        }
        
        self.wfile.write(json.dumps(response).encode())


class LocalHTTPServer:
    """
    本地HTTP服务
    """
    
    def __init__(self, port: int = 5502, status_reporter=None):
        self.port = port
        self.status_reporter = status_reporter
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
        self.running = False
        
    def start(self) -> bool:
        """启动服务"""
        try:
            StatusHandler.status_reporter = self.status_reporter
            
            self.server = HTTPServer(('0.0.0.0', self.port), StatusHandler)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self.running = True
            
            logger.info(f"本地HTTP服务启动: http://0.0.0.0:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"启动HTTP服务失败: {e}")
            return False
    
    def stop(self):
        """停止服务"""
        if self.server:
            self.server.shutdown()
            self.running = False
            logger.info("本地HTTP服务已停止")
