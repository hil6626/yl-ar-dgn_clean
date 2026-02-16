#!/usr/bin/env python3
"""
YL-Monitor 统一启动脚本
整合功能：start_app_simple.sh + debug_launch.sh + deploy.sh
支持模式：development | production | debug | docker
"""

import os
import sys
import time
import signal
import socket
import subprocess
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 配置
DEFAULT_CONFIG = {
    'port': 5500,
    'host': '0.0.0.0',
    'workers': 4,
    'log_level': 'info',
    'reload': False,
    'browser': False,
    'monitor_scripts': False
}

# 颜色输出
COLORS = {
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[0;34m',
    'nc': '\033[0m'
}


class Logger:
    """统一日志输出"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log_file = PROJECT_ROOT / 'logs' / 'start.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('YL-Monitor')
    
    def info(self, msg: str):
        print(f"{COLORS['blue']}[INFO]{COLORS['nc']} {msg}")
        self.logger.info(msg)
    
    def success(self, msg: str):
        print(f"{COLORS['green']}[SUCCESS]{COLORS['nc']} {msg}")
        self.logger.info(f"SUCCESS: {msg}")
    
    def warning(self, msg: str):
        print(f"{COLORS['yellow']}[WARN]{COLORS['nc']} {msg}")
        self.logger.warning(msg)
    
    def error(self, msg: str):
        print(f"{COLORS['red']}[ERROR]{COLORS['nc']} {msg}")
        self.logger.error(msg)
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"{COLORS['blue']}[DEBUG]{COLORS['nc']} {msg}")
        self.logger.debug(msg)


class ProcessManager:
    """进程管理器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.pid_file = PROJECT_ROOT / '.yl-monitor.pid'
        self.process: Optional[subprocess.Popen] = None
    
    def is_running(self) -> bool:
        """检查服务是否已在运行"""
        if not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, 0)  # 检查进程是否存在
            return True
        except (ValueError, OSError, ProcessLookupError):
            # PID文件存在但进程不存在，清理文件
            self.pid_file.unlink(missing_ok=True)
            return False
    
    def get_pid(self) -> Optional[int]:
        """获取当前运行的PID"""
        if not self.pid_file.exists():
            return None
        
        try:
            return int(self.pid_file.read_text().strip())
        except ValueError:
            return None
    
    def save_pid(self, pid: int):
        """保存PID到文件"""
        self.pid_file.write_text(str(pid))
    
    def remove_pid(self):
        """删除PID文件"""
        self.pid_file.unlink(missing_ok=True)
    
    def stop(self, force: bool = False) -> bool:
        """停止服务"""
        pid = self.get_pid()
        if not pid:
            self.logger.warning("服务未运行")
            return False
        
        try:
            if force:
                self.logger.info(f"强制停止服务 (PID: {pid})...")
                os.kill(pid, signal.SIGKILL)
            else:
                self.logger.info(f"优雅停止服务 (PID: {pid})...")
                os.kill(pid, signal.SIGTERM)
                
                # 等待进程结束
                for i in range(10):
                    try:
                        os.kill(pid, 0)
                        time.sleep(1)
                    except OSError:
                        break
            
            self.remove_pid()
            self.logger.success("服务已停止")
            return True
            
        except ProcessLookupError:
            self.logger.warning("进程不存在")
            self.remove_pid()
            return False
        except Exception as e:
            self.logger.error(f"停止服务失败: {e}")
            return False


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, host: str, port: int, logger: Logger):
        self.host = host if host != '0.0.0.0' else '0.0.0.0'
        self.port = port
        self.logger = logger
    
    def check(self, max_retries: int = 30, interval: int = 2) -> bool:
        """执行健康检查"""
        self.logger.info("执行健康检查...")
        
        for i in range(max_retries):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.host, self.port))
                sock.close()
                
                if result == 0:
                    # 尝试HTTP请求
                    import urllib.request
                    url = f"http://{self.host}:{self.port}/api/health"
                    try:
                        with urllib.request.urlopen(url, timeout=2) as response:
                            if response.status == 200:
                                self.logger.success("健康检查通过")
                                return True
                    except:
                        pass
                
                self.logger.debug(f"等待服务启动... ({i+1}/{max_retries})")
                time.sleep(interval)
                
            except Exception as e:
                self.logger.debug(f"检查失败: {e}")
                time.sleep(interval)
        
        self.logger.error("健康检查失败，服务可能未正常启动")
        return False


class ApplicationStarter:
    """统一应用启动器"""
    
    def __init__(self, config: Dict[str, Any], logger: Logger):
        self.config = config
        self.logger = logger
        self.process_manager = ProcessManager(logger)
        self.health_checker = None
    
    def start(self) -> bool:
        """启动应用"""
        mode = self.config.get('mode', 'production')
        
        self.logger.info(f"启动YL-Monitor (模式: {mode})...")
        self.logger.info(f"配置: host={self.config['host']}, port={self.config['port']}")
        
        # 检查是否已在运行
        if self.process_manager.is_running():
            pid = self.process_manager.get_pid()
            self.logger.warning(f"服务已在运行 (PID: {pid})")
            self.logger.info("使用 --restart 重启服务")
            return False
        
        # 根据模式选择启动方式
        starters = {
            'development': self._start_development,
            'production': self._start_production,
            'debug': self._start_debug,
            'docker': self._start_docker
        }
        
        starter = starters.get(mode, self._start_production)
        return starter()
    
    def _start_development(self) -> bool:
        """开发模式：热重载 + 详细日志"""
        self.logger.info("启动开发模式...")
        
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', self.config['host'],
            '--port', str(self.config['port']),
            '--reload',
            '--log-level', 'debug'
        ]
        
        return self._run_command(cmd, wait=False)
    
    def _start_production(self) -> bool:
        """生产模式：多进程 + 守护进程"""
        self.logger.info("启动生产模式...")
        
        # 设置环境变量
        env = os.environ.copy()
        env['YL_MONITOR_PORT'] = str(self.config['port'])
        env['YL_MONITOR_HOST'] = self.config['host']
        
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', self.config['host'],
            '--port', str(self.config['port']),
            '--workers', str(self.config.get('workers', 4)),
            '--log-level', self.config.get('log_level', 'info')
        ]
        
        return self._run_command(cmd, wait=False, env=env, daemon=True)
    
    def _start_debug(self) -> bool:
        """调试模式：详细日志 + 自动打开浏览器"""
        self.logger.info("启动调试模式...")
        
        # 先启动服务
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', self.config['host'],
            '--port', str(self.config['port']),
            '--reload',
            '--log-level', 'debug'
        ]
        
        if not self._run_command(cmd, wait=False):
            return False
        
        # 等待服务就绪
        if not self._wait_for_ready():
            return False
        
        # 打开浏览器
        if self.config.get('browser', False):
            self._open_browser()
        
        # 运行监控脚本
        if self.config.get('monitor_scripts', False):
            self._run_monitor_scripts()
        
        return True
    
    def _start_docker(self) -> bool:
        """Docker模式：容器启动"""
        self.logger.info("启动Docker模式...")
        
        # 检查docker-compose.yml
        compose_file = PROJECT_ROOT / 'docker-compose.yml'
        if not compose_file.exists():
            self.logger.error("未找到docker-compose.yml")
            return False
        
        # 构建并启动
        cmd = ['docker-compose', 'up', '--build', '-d']
        
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.success("Docker容器已启动")
                return True
            else:
                self.logger.error(f"Docker启动失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Docker命令执行失败: {e}")
            return False
    
    def _run_command(self, cmd: List[str], wait: bool = True, 
                     env: Optional[Dict] = None, daemon: bool = False) -> bool:
        """运行命令"""
        try:
            if wait:
                # 前台运行
                result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)
                return result.returncode == 0
            else:
                # 后台运行
                if daemon:
                    # 使用nohup方式
                    log_file = PROJECT_ROOT / 'logs' / 'server.log'
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(log_file, 'a') as f:
                        process = subprocess.Popen(
                            cmd,
                            cwd=PROJECT_ROOT,
                            env=env,
                            stdout=f,
                            stderr=subprocess.STDOUT,
                            start_new_session=True
                        )
                else:
                    process = subprocess.Popen(
                        cmd,
                        cwd=PROJECT_ROOT,
                        env=env,
                        start_new_session=True
                    )
                
                # 保存PID
                self.process_manager.save_pid(process.pid)
                self.logger.info(f"服务已启动 (PID: {process.pid})")
                
                return True
                
        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            return False
    
    def _wait_for_ready(self, timeout: int = 60) -> bool:
        """等待服务就绪"""
        self.health_checker = HealthChecker(
            self.config['host'], 
            self.config['port'], 
            self.logger
        )
        return self.health_checker.check(max_retries=timeout // 2)
    
    def _open_browser(self):
        """打开浏览器"""
        import webbrowser
        
        url = f"http://0.0.0.0:{self.config['port']}"
        self.logger.info(f"打开浏览器: {url}")
        
        try:
            webbrowser.open(url)
        except Exception as e:
            self.logger.warning(f"打开浏览器失败: {e}")
    
    def _run_monitor_scripts(self):
        """运行监控脚本"""
        monitor_dir = PROJECT_ROOT / 'scripts' / 'monitor'
        if not monitor_dir.exists():
            self.logger.warning("监控脚本目录不存在")
            return
        
        self.logger.info("运行监控脚本...")
        
        for script_file in sorted(monitor_dir.glob('*.py')):
            self.logger.info(f"执行: {script_file.name}")
            try:
                result = subprocess.run(
                    [sys.executable, str(script_file)],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.logger.success(f"{script_file.name} 执行成功")
                else:
                    self.logger.warning(f"{script_file.name} 执行失败")
                    
            except Exception as e:
                self.logger.error(f"{script_file.name} 执行异常: {e}")


def check_dependencies(logger: Logger) -> bool:
    """检查依赖"""
    logger.info("检查系统依赖...")
    
    # 检查Python
    try:
        version = sys.version_info
        logger.info(f"Python版本: {version.major}.{version.minor}.{version.micro}")
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error("需要Python 3.8或更高版本")
            return False
    except Exception as e:
        logger.error(f"检查Python版本失败: {e}")
        return False
    
    # 检查关键依赖
    required_modules = ['fastapi', 'uvicorn', 'pydantic']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        logger.error(f"缺少依赖: {', '.join(missing)}")
        logger.info("请运行: pip install -r requirements.txt")
        return False
    
    logger.success("依赖检查通过")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='YL-Monitor 统一启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --mode development          # 开发模式（热重载）
  %(prog)s --mode production           # 生产模式（多进程）
  %(prog)s --mode debug --browser      # 调试模式（自动打开浏览器）
  %(prog)s --restart                   # 重启服务
  %(prog)s --stop                      # 停止服务
  %(prog)s --status                    # 查看状态
        """
    )
    
    # 模式选择
    parser.add_argument(
        '--mode', '-m',
        choices=['development', 'production', 'debug', 'docker'],
        default='production',
        help='启动模式 (默认: production)'
    )
    
    # 网络配置
    parser.add_argument(
        '--host', '-H',
        default='0.0.0.0',
        help='绑定主机 (默认: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5500,
        help='绑定端口 (默认: 5500)'
    )
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='工作进程数 (默认: 4)'
    )
    
    # 调试选项
    parser.add_argument(
        '--browser', '-b',
        action='store_true',
        help='自动打开浏览器（仅debug模式）'
    )
    parser.add_argument(
        '--monitor-scripts', '-M',
        action='store_true',
        help='运行监控脚本（仅debug模式）'
    )
    
    # 控制命令
    parser.add_argument(
        '--restart', '-r',
        action='store_true',
        help='重启服务'
    )
    parser.add_argument(
        '--stop', '-s',
        action='store_true',
        help='停止服务'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='查看服务状态'
    )
    
    # 其他选项
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='强制操作'
    )
    
    args = parser.parse_args()
    
    # 初始化日志
    logger = Logger(verbose=args.verbose)
    
    # 打印欢迎信息
    print(f"\n{COLORS['blue']}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║           YL-Monitor 统一启动脚本 v1.0.0                  ║")
    print("║           浏览器监控平台 - 一键启动工具                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{COLORS['nc']}\n")
    
    # 处理控制命令
    process_manager = ProcessManager(logger)
    
    if args.stop:
        return 0 if process_manager.stop(force=args.force) else 1
    
    if args.status:
        if process_manager.is_running():
            pid = process_manager.get_pid()
            logger.success(f"服务运行中 (PID: {pid})")
            logger.info(f"访问地址: http://{args.host}:{args.port}")
        else:
            logger.info("服务未运行")
        return 0
    
    if args.restart:
        logger.info("重启服务...")
        process_manager.stop()
        time.sleep(2)
    
    # 检查依赖
    if not check_dependencies(logger):
        return 1
    
    # 构建配置
    config = {
        'mode': args.mode,
        'host': args.host,
        'port': args.port,
        'workers': args.workers,
        'browser': args.browser,
        'monitor_scripts': args.monitor_scripts,
        'log_level': 'debug' if args.verbose else 'info'
    }
    
    # 启动应用
    starter = ApplicationStarter(config, logger)
    success = starter.start()
    
    if success and args.mode in ['production', 'docker']:
        # 生产模式执行健康检查
        time.sleep(3)
        health_checker = HealthChecker(args.host, args.port, logger)
        if not health_checker.check(max_retries=15):
            return 1
        
        logger.success("🎉 服务启动成功！")
        logger.info(f"访问地址: http://{args.host}:{args.port}")
        logger.info(f"API文档: http://{args.host}:{args.port}/docs")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
