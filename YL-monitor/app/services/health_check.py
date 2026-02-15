"""
健康检查系统
提供系统健康状态监控、依赖检查、自动修复建议
"""

import asyncio
import psutil
import time
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"       # 健康
    WARNING = "warning"     # 警告
    CRITICAL = "critical"   # 严重
    UNKNOWN = "unknown"     # 未知


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str          # 组件名称
    status: HealthStatus    # 状态
    message: str            # 状态消息
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: float = 0.0
    suggestion: str = ""    # 修复建议
    
    def to_dict(self):
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'response_time_ms': self.response_time_ms,
            'suggestion': self.suggestion
        }


class HealthCheck:
    """健康检查基类"""
    
    def __init__(self, name: str, interval: int = 60):
        self.name = name
        self.interval = interval  # 检查间隔（秒）
        self.last_result: Optional[HealthCheckResult] = None
        self.last_check_time: Optional[datetime] = None
    
    async def check(self) -> HealthCheckResult:
        """执行健康检查"""
        start_time = time.time()
        
        try:
            result = await self._do_check()
            result.response_time_ms = (time.time() - start_time) * 1000
            self.last_result = result
            self.last_check_time = datetime.now()
            return result
        except Exception as e:
            result = HealthCheckResult(
                component=self.name,
                status=HealthStatus.CRITICAL,
                message=f"检查异常: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
            self.last_result = result
            self.last_check_time = datetime.now()
            return result
    
    async def _do_check(self) -> HealthCheckResult:
        """子类实现具体的检查逻辑"""
        raise NotImplementedError


class SystemResourceCheck(HealthCheck):
    """系统资源检查"""
    
    def __init__(self, 
                 cpu_threshold: float = 80.0,
                 memory_threshold: float = 85.0,
                 disk_threshold: float = 90.0):
        super().__init__("system_resources", interval=30)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def _do_check(self) -> HealthCheckResult:
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # 确定状态
        status = HealthStatus.HEALTHY
        messages = []
        suggestions = []
        
        if cpu_percent > self.cpu_threshold:
            status = HealthStatus.WARNING if status == HealthStatus.HEALTHY else HealthStatus.CRITICAL
            messages.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            suggestions.append("建议：检查高CPU进程，考虑优化脚本执行时间")
        
        if memory_percent > self.memory_threshold:
            status = HealthStatus.WARNING if status == HealthStatus.HEALTHY else HealthStatus.CRITICAL
            messages.append(f"内存使用率过高: {memory_percent:.1f}%")
            suggestions.append("建议：清理内存缓存，重启不必要的服务")
        
        if disk_percent > self.disk_threshold:
            status = HealthStatus.CRITICAL
            messages.append(f"磁盘使用率过高: {disk_percent:.1f}%")
            suggestions.append("建议：清理日志文件，删除临时文件，扩展磁盘空间")
        
        if status == HealthStatus.HEALTHY:
            message = "系统资源正常"
            suggestion = "继续保持"
        else:
            message = "; ".join(messages)
            suggestion = "; ".join(suggestions)
        
        return HealthCheckResult(
            component=self.name,
            status=status,
            message=message,
            details={
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'cpu_threshold': self.cpu_threshold,
                'memory_threshold': self.memory_threshold,
                'disk_threshold': self.disk_threshold
            },
            suggestion=suggestion
        )


class DiskSpaceCheck(HealthCheck):
    """磁盘空间检查"""
    
    def __init__(self, 
                 warning_threshold: float = 80.0,
                 critical_threshold: float = 90.0,
                 paths: List[str] = None):
        super().__init__("disk_space", interval=300)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.paths = paths or ['/']
    
    async def _do_check(self) -> HealthCheckResult:
        issues = []
        details = {}
        
        for path in self.paths:
            try:
                usage = psutil.disk_usage(path)
                percent = (usage.used / usage.total) * 100
                
                details[path] = {
                    'total_gb': usage.total / (1024**3),
                    'used_gb': usage.used / (1024**3),
                    'free_gb': usage.free / (1024**3),
                    'percent': percent
                }
                
                if percent > self.critical_threshold:
                    issues.append(f"{path} 磁盘严重不足: {percent:.1f}%")
                elif percent > self.warning_threshold:
                    issues.append(f"{path} 磁盘空间警告: {percent:.1f}%")
                    
            except Exception as e:
                issues.append(f"{path} 检查失败: {e}")
        
        if issues:
            status = HealthStatus.CRITICAL if any("严重不足" in i for i in issues) else HealthStatus.WARNING
            message = "; ".join(issues)
            suggestion = "建议：运行磁盘清理脚本，删除旧日志和临时文件"
        else:
            status = HealthStatus.HEALTHY
            message = "磁盘空间充足"
            suggestion = "继续保持"
        
        return HealthCheckResult(
            component=self.name,
            status=status,
            message=message,
            details=details,
            suggestion=suggestion
        )


class LogFileCheck(HealthCheck):
    """日志文件检查"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 max_size_mb: float = 100.0,
                 max_files: int = 50):
        super().__init__("log_files", interval=600)
        self.log_dir = Path(log_dir)
        self.max_size_mb = max_size_mb
        self.max_files = max_files
    
    async def _do_check(self) -> HealthCheckResult:
        if not self.log_dir.exists():
            return HealthCheckResult(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="日志目录不存在",
                suggestion="无需处理"
            )
        
        log_files = list(self.log_dir.glob("*.log*"))
        total_size = sum(f.stat().st_size for f in log_files if f.exists())
        total_size_mb = total_size / (1024 * 1024)
        
        details = {
            'file_count': len(log_files),
            'total_size_mb': total_size_mb,
            'max_size_mb': self.max_size_mb,
            'max_files': self.max_files
        }
        
        if total_size_mb > self.max_size_mb:
            status = HealthStatus.WARNING
            message = f"日志文件过大: {total_size_mb:.1f}MB ({len(log_files)}个文件)"
            suggestion = f"建议：运行日志轮转脚本，压缩或删除旧日志"
        elif len(log_files) > self.max_files:
            status = HealthStatus.WARNING
            message = f"日志文件过多: {len(log_files)}个"
            suggestion = "建议：清理旧日志文件，保留最近的日志"
        else:
            status = HealthStatus.HEALTHY
            message = f"日志文件正常: {total_size_mb:.1f}MB ({len(log_files)}个文件)"
            suggestion = "继续保持"
        
        return HealthCheckResult(
            component=self.name,
            status=status,
            message=message,
            details=details,
            suggestion=suggestion
        )


class HealthCheckManager:
    """
    健康检查管理器
    
    统一管理所有健康检查，提供：
    1. 定期检查调度
    2. 结果聚合
    3. 告警通知
    4. 历史记录
    """
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self._running = False
        self._check_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[HealthCheckResult], None]] = []
        self._history: List[Dict] = []
        self._max_history = 1000
    
    def register_check(self, check: HealthCheck):
        """注册健康检查"""
        self.checks[check.name] = check
        logger.info(f"注册健康检查: {check.name}")
    
    def unregister_check(self, name: str):
        """注销健康检查"""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"注销健康检查: {name}")
    
    def register_callback(self, callback: Callable[[HealthCheckResult], None]):
        """注册状态变更回调"""
        self._callbacks.append(callback)
    
    async def start(self):
        """启动健康检查管理器"""
        if self._running:
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("健康检查管理器已启动")
    
    async def stop(self):
        """停止健康检查管理器"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("健康检查管理器已停止")
    
    async def _check_loop(self):
        """检查循环"""
        while self._running:
            try:
                # 执行所有检查
                for name, check in self.checks.items():
                    # 检查是否需要执行（根据间隔）
                    if check.last_check_time:
                        elapsed = (datetime.now() - check.last_check_time).total_seconds()
                        if elapsed < check.interval:
                            continue
                    
                    # 执行检查
                    result = await check.check()
                    
                    # 记录历史
                    self._history.append({
                        'timestamp': datetime.now().isoformat(),
                        'result': result.to_dict()
                    })
                    if len(self._history) > self._max_history:
                        self._history.pop(0)
                    
                    # 通知回调
                    for callback in self._callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(result)
                            else:
                                callback(result)
                        except Exception as e:
                            logger.error(f"健康检查回调错误: {e}")
                
                # 等待下一次检查
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(10)
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """立即执行所有检查"""
        results = {}
        for name, check in self.checks.items():
            results[name] = await check.check()
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """获取整体健康状态"""
        statuses = [check.last_result.status for check in self.checks.values() if check.last_result]
        
        if any(s == HealthStatus.CRITICAL for s in statuses):
            return HealthStatus.CRITICAL
        elif any(s == HealthStatus.WARNING for s in statuses):
            return HealthStatus.WARNING
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        return {
            'overall_status': self.get_overall_status().value,
            'timestamp': datetime.now().isoformat(),
            'checks': {
                name: check.last_result.to_dict() if check.last_result else None
                for name, check in self.checks.items()
            },
            'history': self._history[-100:]  # 最近100条记录
        }
    
    def save_report(self, path: str = "logs/health_report.json"):
        """保存健康报告"""
        report = self.get_health_report()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)


# 全局健康检查管理器
health_manager = HealthCheckManager()


# 初始化默认检查
def init_default_checks():
    """初始化默认健康检查"""
    health_manager.register_check(SystemResourceCheck())
    health_manager.register_check(DiskSpaceCheck())
    health_manager.register_check(LogFileCheck())


# 使用示例
if __name__ == "__main__":
    async def main():
        # 初始化
        init_default_checks()
        
        # 注册回调
        def on_health_change(result: HealthCheckResult):
            print(f"[{result.status.value.upper()}] {result.component}: {result.message}")
            if result.suggestion:
                print(f"  建议: {result.suggestion}")
        
        health_manager.register_callback(on_health_change)
        
        # 启动
        await health_manager.start()
        
        # 运行一段时间
        await asyncio.sleep(60)
        
        # 获取报告
        report = health_manager.get_health_report()
        print("\n健康报告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
        # 停止
        await health_manager.stop()
    
    asyncio.run(main())
