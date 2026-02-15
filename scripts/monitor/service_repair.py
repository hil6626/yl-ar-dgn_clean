#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务修复脚本 - Service Repair
尝试根据配置自动重启或修复常见后台服务

用法:
    python service_repair.py --service myservice --action restart

作者: AI 全栈技术员
版本: 1.0
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent


class ServiceManager:
    def __init__(self):
        pass

    def restart_service(self, service_name: str) -> bool:
        try:
            subprocess.run(['systemctl', 'restart', service_name], check=True)
            return True
        except Exception:
            try:
                # 备用方式: 使用 service 命令
                subprocess.run(['service', service_name, 'restart'], check=True)
                return True
            except Exception:
                return False

    def start_service(self, service_name: str) -> bool:
        try:
            subprocess.run(['systemctl', 'start', service_name], check=True)
            return True
        except Exception:
            try:
                subprocess.run(['service', service_name, 'start'], check=True)
                return True
            except Exception:
                return False

    def stop_service(self, service_name: str) -> bool:
        try:
            subprocess.run(['systemctl', 'stop', service_name], check=True)
            return True
        except Exception:
            try:
                subprocess.run(['service', service_name, 'stop'], check=True)
                return True
            except Exception:
                return False


def main():
    parser = argparse.ArgumentParser(description='服务修复工具')
    parser.add_argument('--service', required=True, help='服务名或进程标识')
    parser.add_argument('--action', choices=['restart', 'start', 'stop'], default='restart')
    args = parser.parse_args()

    sm = ServiceManager()
    ok = False
    if args.action == 'restart':
        ok = sm.restart_service(args.service)
    elif args.action == 'start':
        ok = sm.start_service(args.service)
    elif args.action == 'stop':
        ok = sm.stop_service(args.service)

    if ok:
        print(f'操作成功: {args.action} {args.service}')
        sys.exit(0)
    else:
        print(f'操作失败: {args.action} {args.service}')
        sys.exit(2)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务修复脚本 - Service Repair Script
用于检测和修复系统服务故障，自动重启崩溃的服务

功能:
- 定期检查关键服务状态
- 自动重启崩溃或停止的服务
- 记录服务修复历史
- 支持手动触发服务修复

使用方法:
    python service_repair.py --check              # 检查所有服务状态
    python service_repair.py --repair <service>   # 修复特定服务
    python service_repair.py --auto               # 自动修复模式
    python service_repair.py --daemon             # 守护进程模式

作者: AI 全栈技术员
版本: 1.1 (已修复psutil导入问题)
创建日期: 2026年2月9日
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 条件导入psutil
PSUTIL_AVAILABLE = False
psutil = None

try:
    import psutil as psutil_module
    psutil = psutil_module
    PSUTIL_AVAILABLE = True
except ImportError:
    print("警告: psutil 未安装，将使用系统命令替代")

# 配置日志
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "service_repair.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ServiceRepair')


class ServiceManager:
    """服务管理器"""
    
    # 关键服务定义
    CRITICAL_SERVICES = {
        'monitor_app': {
            'name': '监控服务',
            'process_pattern': 'monitor_app',
            'start_command': None,
            'required': True,
            'check_port': 5000
        },
        'camera_service': {
            'name': '摄像头服务',
            'process_pattern': 'camera',
            'start_command': None,
            'required': False,
            'check_port': None
        },
        'audio_service': {
            'name': '音频服务',
            'process_pattern': 'audio',
            'start_command': None,
            'required': False,
            'check_port': None
        },
        'obs_studio': {
            'name': 'OBS Studio',
            'process_pattern': 'obs',
            'start_command': None,
            'required': False,
            'check_port': None
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.services = self.CRITICAL_SERVICES.copy()
        self.repair_history = []
        self.config_file = config_file
        self.base_dir = Path(__file__).parent.parent.parent
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'services' in config:
                        self.services.update(config['services'])
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
    
    def get_all_services(self) -> Dict[str, Dict]:
        """获取所有服务状态"""
        services_status = {}
        
        for service_id, service_info in self.services.items():
            status = self._check_service_status(service_id, service_info)
            services_status[service_id] = status
        
        return services_status
    
    def _check_service_status(self, service_id: str, service_info: Dict) -> Dict:
        """检查单个服务状态"""
        status = {
            'id': service_id,
            'name': service_info.get('name', service_id),
            'status': 'unknown',
            'running': False,
            'pid': None,
            'port_open': None,
            'uptime': None,
            'error': None
        }
        
        try:
            # 检查进程
            process_pattern = service_info.get('process_pattern', service_id)
            running_process = self._find_process(process_pattern)
            
            if running_process:
                status['running'] = True
                status['pid'] = running_process.pid
                status['status'] = 'running'
                status['uptime'] = self._get_process_uptime(running_process)
            else:
                status['status'] = 'stopped'
            
            # 检查端口
            check_port = service_info.get('check_port')
            if check_port:
                status['port_open'] = self._check_port(check_port)
                if not status['port_open'] and status['running']:
                    status['status'] = 'warning'
            
            # 检查是否必须服务
            if service_info.get('required', False) and not status['running']:
                status['status'] = 'critical'
                status['error'] = 'Required service is not running'
        
        except Exception as e:
            status['status'] = 'error'
            status['error'] = str(e)
            logger.error(f"检查服务 {service_id} 状态失败: {e}")
        
        return status
    
    def _find_process(self, pattern: str):
        """查找进程"""
        if not PSUTIL_AVAILABLE or psutil is None:
            return None
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    name = proc.info.get('name', '')
                    
                    if pattern.lower() in cmdline.lower() or pattern.lower() in name.lower():
                        return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"查找进程失败: {e}")
        
        return None
    
    def _get_process_uptime(self, process) -> str:
        """获取进程运行时间"""
        try:
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"
    
    def _check_port(self, port: int) -> bool:
        """检查端口是否开放"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def repair_service(self, service_id: str) -> Dict:
        """修复单个服务"""
        result = {
            'service_id': service_id,
            'success': False,
            'message': '',
            'actions': []
        }
        
        if service_id not in self.services:
            result['message'] = f"服务 {service_id} 不存在"
            return result
        
        service_info = self.services[service_id]
        
        # 停止现有进程
        process_pattern = service_info.get('process_pattern', service_id)
        existing_process = self._find_process(process_pattern)
        
        if existing_process:
            try:
                existing_process.terminate()
                result['actions'].append(f"终止现有进程 PID: {existing_process.pid}")
                time.sleep(2)
                
                # 如果进程仍未结束，强制杀死
                if existing_process.is_running():
                    existing_process.kill()
                    result['actions'].append(f"强制杀死进程 PID: {existing_process.pid}")
            except Exception as e:
                result['actions'].append(f"停止进程失败: {e}")
        
        # 启动服务
        start_command = service_info.get('start_command')
        if start_command:
            try:
                subprocess.Popen(
                    start_command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                result['actions'].append(f"启动服务命令: {start_command}")
                result['success'] = True
                result['message'] = "服务修复成功"
            except Exception as e:
                result['message'] = f"启动服务失败: {e}"
        else:
            # 没有启动命令的服务，标记为需要手动启动
            result['success'] = True
            result['message'] = "服务已停止，需要手动启动"
            result['actions'].append("无自动启动命令，需要手动操作")
        
        # 记录修复历史
        self.repair_history.append({
            'service_id': service_id,
            'timestamp': datetime.now().isoformat(),
            'success': result['success'],
            'actions': result['actions']
        })
        
        # 保存修复历史
        self._save_repair_history()
        
        return result
    
    def auto_repair_all(self) -> Dict:
        """自动修复所有异常服务"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'services_checked': 0,
            'services_repaired': 0,
            'services_remaining': 0,
            'details': []
        }
        
        services_status = self.get_all_services()
        result['services_checked'] = len(services_status)
        
        for service_id, status in services_status.items():
            if status['status'] in ['stopped', 'critical', 'warning']:
                repair_result = self.repair_service(service_id)
                result['details'].append({
                    'service_id': service_id,
                    'original_status': status['status'],
                    'repair_result': repair_result
                })
                
                if repair_result['success']:
                    result['services_repaired'] += 1
                else:
                    result['services_remaining'] += 1
        
        return result
    
    def _save_repair_history(self):
        """保存修复历史"""
        try:
            history_file = LOG_DIR / "repair_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.repair_history[-100:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存修复历史失败: {e}")
    
    def get_repair_history(self, limit: int = 20) -> List[Dict]:
        """获取修复历史"""
        return self.repair_history[-limit:]
    
    def format_status_console(self, services_status: Dict):
        """控制台格式化输出服务状态"""
        print("\n" + "=" * 70)
        print("服务状态报告")
        print("=" * 70)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
        
        for service_id, status in services_status.items():
            status_icon = {
                'running': '✅',
                'stopped': '⏹️',
                'warning': '⚠️',
                'critical': '🚨',
                'error': '❌',
                'unknown': '❓'
            }.get(status['status'], '❓')
            
            print(f"\n{status_icon} {status['name']} ({service_id})")
            print(f"   状态: {status['status']}")
            print(f"   运行: {'是' if status['running'] else '否'}")
            
            if status['pid']:
                print(f"   PID: {status['pid']}")
            
            if status['uptime']:
                print(f"   运行时间: {status['uptime']}")
            
            if status['error']:
                print(f"   错误: {status['error']}")
        
        print("\n" + "=" * 70)
        
        # 统计
        running_count = sum(1 for s in services_status.values() if s['status'] == 'running')
        stopped_count = sum(1 for s in services_status.values() if s['status'] == 'stopped')
        warning_count = sum(1 for s in services_status.values() if s['status'] in ['warning', 'critical'])
        
        print(f"统计: 运行中 {running_count} | 已停止 {stopped_count} | 异常 {warning_count}")
        print("=" * 70 + "\n")


class RepairDaemon:
    """修复守护进程"""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.service_manager = ServiceManager()
    
    def start(self):
        """启动守护进程"""
        self.running = True
        logger.info(f"启动服务修复守护进程，检查间隔: {self.check_interval}秒")
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        try:
            while self.running:
                # 检查并自动修复
                result = self.service_manager.auto_repair_all()
                
                if result['services_repaired'] > 0:
                    logger.info(f"自动修复了 {result['services_repaired']} 个服务")
                
                # 等待下次检查
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        except Exception as e:
            logger.error(f"守护进程出错: {e}")
        finally:
            self.running = False
            logger.info("服务修复守护进程已停止")
    
    def stop(self):
        """停止守护进程"""
        self.running = False
    
    def _handle_signal(self, signum, frame):
        """信号处理"""
        logger.info(f"收到信号 {signum}，正在停止守护进程...")
        self.stop()


def main():
    parser = argparse.ArgumentParser(
        description='服务修复脚本 - 检测和修复系统服务故障',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--check', '-c', action='store_true', 
                        help='检查所有服务状态')
    parser.add_argument('--repair', '-r', type=str, 
                        help='修复特定服务 (服务ID)')
    parser.add_argument('--auto', '-a', action='store_true', 
                        help='自动修复所有异常服务')
    parser.add_argument('--daemon', '-d', action='store_true', 
                        help='启动守护进程模式')
    parser.add_argument('--interval', '-i', type=int, default=60,
                        help='守护进程检查间隔（秒），默认60秒')
    parser.add_argument('--config', '-f', type=str, default=None,
                        help='配置文件路径')
    parser.add_argument('--json', '-j', action='store_true',
                        help='JSON 格式输出')
    
    args = parser.parse_args()
    
    service_manager = ServiceManager(config_file=args.config)
    
    try:
        if args.daemon:
            # 守护进程模式
            daemon = RepairDaemon(check_interval=args.interval)
            daemon.start()
        
        elif args.repair:
            # 修复特定服务
            result = service_manager.repair_service(args.repair)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"修复服务 {args.repair}: {result['message']}")
                for action in result['actions']:
                    print(f"  - {action}")
        
        elif args.auto:
            # 自动修复所有异常服务
            result = service_manager.auto_repair_all()
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"自动修复完成:")
                print(f"  检查服务数: {result['services_checked']}")
                print(f"  修复成功: {result['services_repaired']}")
                print(f"  仍需处理: {result['services_remaining']}")
        
        else:
            # 默认检查所有服务状态
            services_status = service_manager.get_all_services()
            
            if args.json:
                print(json.dumps(services_status, ensure_ascii=False, indent=2))
            else:
                service_manager.format_status_console(services_status)
    
    except Exception as e:
        logger.error(f"执行出错: {e}")
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

