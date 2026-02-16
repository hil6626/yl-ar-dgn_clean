#!/usr/bin/env python3
"""
User GUI 进程监控服务
用于监控 User GUI (PyQt5应用) 的运行状态
通过进程检查而非HTTP接口
"""

import psutil
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import subprocess

logger = logging.getLogger(__name__)


class UserGUIMonitor:
    """User GUI 进程监控器"""
    
    def __init__(self):
        self.process_name = "user/main.py"
        self.process_keywords = ["python", "main.py", "user"]
        self.last_status = None
        self.last_check = None
        
    def check_process_running(self) -> bool:
        """检查 User GUI 进程是否运行"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    # 检查是否包含 user/main.py 或相关关键词
                    if 'user/main.py' in cmdline or (
                        'python' in cmdline and 
                        'user' in cmdline and 
                        'gui' in cmdline
                    ):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"检查进程时出错: {e}")
            return False
    
    def get_process_info(self) -> Optional[Dict]:
        """获取 User GUI 进程详细信息"""
        try:
            for proc in psutil.process_iter([
                'pid', 'name', 'cmdline', 'cpu_percent',
                'memory_info', 'create_time', 'status'
            ]):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'user/main.py' in cmdline or (
                        'python' in cmdline and 
                        'user' in cmdline and 
                        'gui' in cmdline
                    ):
                        mem_info = proc.info['memory_info']
                        mem_mb = mem_info.rss / 1024 / 1024 if mem_info else 0
                        create_time = proc.info['create_time']
                        return {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline[:100],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_mb': mem_mb,
                            'create_time': datetime.fromtimestamp(
                                create_time
                            ).isoformat() if create_time else None,
                            'status': proc.info['status']
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except Exception as e:
            logger.error(f"获取进程信息时出错: {e}")
            return None
    
    def get_status(self) -> Dict:
        """获取 User GUI 完整状态"""
        is_running = self.check_process_running()
        process_info = self.get_process_info() if is_running else None
        
        status = {
            'service': 'user-gui',
            'status': 'running' if is_running else 'stopped',
            'timestamp': datetime.now().isoformat(),
            'process': process_info,
            'uptime': None
        }
        
        # 计算运行时间
        if process_info and process_info.get('create_time'):
            try:
                create_time = datetime.fromisoformat(
                    process_info['create_time']
                )
                uptime_seconds = (
                    datetime.now() - create_time
                ).total_seconds()
                status['uptime'] = uptime_seconds
            except (ValueError, TypeError):
                pass
        
        self.last_status = status
        self.last_check = datetime.now()
        
        return status
    
    def start_gui(self) -> bool:
        """启动 User GUI"""
        try:
            logger.info("正在启动 User GUI...")
            # 使用 subprocess 启动 GUI
            subprocess.Popen(
                ['python3', 'user/main.py'],
                cwd='/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean',
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            # 等待几秒让进程启动
            time.sleep(3)
            return self.check_process_running()
        except Exception as e:
            logger.error(f"启动 User GUI 失败: {e}")
            return False
    
    def stop_gui(self) -> bool:
        """停止 User GUI"""
        try:
            logger.info("正在停止 User GUI...")
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'user/main.py' in cmdline:
                        proc.terminate()
                        proc.wait(timeout=5)
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except psutil.TimeoutExpired:
                    proc.kill()
                    return True
            return False
        except Exception as e:
            logger.error(f"停止 User GUI 失败: {e}")
            return False
    
    def restart_gui(self) -> bool:
        """重启 User GUI"""
        self.stop_gui()
        time.sleep(2)
        return self.start_gui()


# 全局监控实例
user_gui_monitor = UserGUIMonitor()


def get_user_gui_status() -> Dict:
    """获取 User GUI 状态的便捷函数"""
    return user_gui_monitor.get_status()


def is_user_gui_running() -> bool:
    """检查 User GUI 是否运行的便捷函数"""
    return user_gui_monitor.check_process_running()


if __name__ == "__main__":
    # 测试监控功能
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("User GUI 进程监控测试")
    print("=" * 60)
    
    monitor = UserGUIMonitor()
    status = monitor.get_status()
    
    print(f"\n服务状态: {status['status']}")
    print(f"时间戳: {status['timestamp']}")

    if status['process']:
        print(f"\n进程信息:")
        print(f"  PID: {status['process']['pid']}")
        print(f"  CPU: {status['process']['cpu_percent']}%")
        print(f"  内存: {status['process']['memory_mb']:.2f} MB")
        print(f"  运行时间: {status.get('uptime', 'N/A')}")
    else:
        print("\n进程未运行")
    
    print("\n" + "=" * 60)
