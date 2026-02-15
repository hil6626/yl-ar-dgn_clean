#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 状态上报服务
定时向 YL-monitor 上报应用状态
"""

import os
import sys
import time
import json
import logging
import requests
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StatusReporter')


class StatusReporter:
    """
    状态上报器
    负责收集User GUI状态并上报到YL-monitor
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_report_time: Optional[datetime] = None
        self.report_count = 0
        self.error_count = 0
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'UserGUI-StatusReporter/1.0'
        })
        
        # 状态缓存
        self._status_cache: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置"""
        default_config = {
            'monitor_url': 'http://localhost:5500',
            'node_id': 'user-gui',
            'node_name': 'User GUI',
            'report_interval': 30,  # 秒
            'timeout': 5,  # 秒
            'max_retries': 3,
            'retry_delay': 2,  # 秒
            'enabled': True
        }
        
        if config_path and Path(config_path).exists():
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        default_config.update(user_config)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                
        # 环境变量覆盖
        if os.getenv('YL_MONITOR_URL'):
            default_config['monitor_url'] = os.getenv('YL_MONITOR_URL')
        if os.getenv('USER_GUI_NODE_ID'):
            default_config['node_id'] = os.getenv('USER_GUI_NODE_ID')
            
        return default_config
    
    def _collect_status(self) -> Dict[str, Any]:
        """收集当前状态"""
        try:
            import psutil
            
            # 获取进程信息
            process = psutil.Process()
            
            status = {
                'node_id': self.config['node_id'],
                'node_name': self.config['node_name'],
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'status': 'running',
                'version': '2.0.0',
                'uptime': time.time() - process.create_time(),
                'resources': {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'threads': process.num_threads()
                },
                'gui': {
                    'window_active': True,  # 由GUI更新
                    'video_running': False,  # 由GUI更新
                    'audio_running': False,  # 由GUI更新
                    'face_loaded': False  # 由GUI更新
                }
            }
            
            # 合并GUI更新的状态
            with self._lock:
                status['gui'].update(self._status_cache)
                
            return status
            
        except Exception as e:
            logger.error(f"收集状态失败: {e}")
            return {
                'node_id': self.config['node_id'],
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'status': 'error',
                'error': str(e)
            }
    
    def update_gui_status(self, **kwargs):
        """更新GUI状态（由GUI调用）"""
        with self._lock:
            self._status_cache.update(kwargs)
            logger.debug(f"GUI状态更新: {kwargs}")
    
    def _send_report(self, status: Dict[str, Any]) -> bool:
        """发送状态报告"""
        url = f"{self.config['monitor_url']}/api/ar/nodes/{self.config['node_id']}/heartbeat"
        
        for attempt in range(self.config['max_retries']):
            try:
                response = self.session.post(
                    url,
                    json=status,
                    timeout=self.config['timeout']
                )
                
                if response.status_code == 200:
                    logger.debug(f"状态上报成功: {response.json()}")
                    return True
                else:
                    logger.warning(f"状态上报失败: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"连接失败 (尝试 {attempt + 1}/{self.config['max_retries']})")
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.config['max_retries']})")
            except Exception as e:
                logger.error(f"上报异常: {e}")
                
            if attempt < self.config['max_retries'] - 1:
                time.sleep(self.config['retry_delay'])
                
        return False
    
    def _report_loop(self):
        """上报循环"""
        logger.info(f"状态上报线程启动，间隔: {self.config['report_interval']}秒")
        
        while self.running:
            try:
                status = self._collect_status()
                success = self._send_report(status)
                
                if success:
                    self.last_report_time = datetime.utcnow()
                    self.report_count += 1
                    logger.info(f"状态上报成功 [#{self.report_count}]")
                else:
                    self.error_count += 1
                    logger.error(f"状态上报失败 [#{self.error_count}]")
                    
            except Exception as e:
                logger.error(f"上报循环异常: {e}")
                
            # 等待下一次上报
            for _ in range(self.config['report_interval']):
                if not self.running:
                    break
                time.sleep(1)
                
        logger.info("状态上报线程停止")
    
    def start(self) -> bool:
        """启动状态上报"""
        if not self.config['enabled']:
            logger.info("状态上报已禁用")
            return False
            
        if self.running:
            logger.warning("状态上报已在运行")
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._report_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"状态上报服务启动: {self.config['node_id']} -> {self.config['monitor_url']}")
        return True
    
    def stop(self):
        """停止状态上报"""
        if not self.running:
            return
            
        logger.info("正在停止状态上报服务...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
            
        logger.info("状态上报服务已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取上报统计"""
        return {
            'running': self.running,
            'report_count': self.report_count,
            'error_count': self.error_count,
            'last_report_time': self.last_report_time.isoformat() if self.last_report_time else None,
            'config': {
                'node_id': self.config['node_id'],
                'monitor_url': self.config['monitor_url'],
                'interval': self.config['report_interval']
            }
        }


# 全局实例
_status_reporter: Optional[StatusReporter] = None

def get_reporter() -> StatusReporter:
    """获取状态上报器实例（单例）"""
    global _status_reporter
    if _status_reporter is None:
        # 查找配置文件
        config_paths = [
            Path(__file__).parent.parent / 'config' / 'monitor_config.yaml',
            Path.cwd() / 'config' / 'monitor_config.yaml',
        ]
        
        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = str(path)
                break
                
        _status_reporter = StatusReporter(config_path)
        
    return _status_reporter


if __name__ == '__main__':
    # 测试运行
    reporter = StatusReporter()
    reporter.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        reporter.stop()
