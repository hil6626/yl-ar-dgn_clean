"""
清理管理器
实现沉积内容清理、重复内容检测、错误恢复和队列监控
"""

import asyncio
import hashlib
import json
import os
import time
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import shutil


@dataclass
class CleanupRule:
    """清理规则"""
    name: str
    path_pattern: str          # 文件路径模式
    max_age_days: int          # 最大保留天数
    max_size_mb: Optional[int] = None  # 最大大小限制(MB)
    exclude_patterns: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class DuplicateFile:
    """重复文件信息"""
    file_path: str
    file_hash: str
    file_size: int
    modified_time: datetime
    duplicates: List[str] = field(default_factory=list)


@dataclass
class QueueStatus:
    """队列状态"""
    queue_name: str
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int
    avg_wait_time: float       # 平均等待时间(秒)
    avg_process_time: float    # 平均处理时间(秒)


class CleanupManager:
    """
    清理管理器
    
    功能：
    1. 沉积内容清理（临时文件、日志、缓存）
    2. 重复内容检测和去重
    3. 错误恢复策略
    4. 队列监控
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).absolute()
        self._cleanup_rules: List[CleanupRule] = []
        self._queue_monitors: Dict[str, Callable] = {}
        self._error_handlers: Dict[str, Callable] = {}
        self._cleanup_history: List[Dict] = []
        
        # 加载默认清理规则
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """加载默认清理规则"""
        default_rules = [
            CleanupRule(
                name="temp_files",
                path_pattern="**/*.tmp",
                max_age_days=1,
                exclude_patterns=["*.important.tmp"]
            ),
            CleanupRule(
                name="python_cache",
                path_pattern="**/__pycache__",
                max_age_days=7
            ),
            CleanupRule(
                name="pyc_files",
                path_pattern="**/*.pyc",
                max_age_days=7
            ),
            CleanupRule(
                name="log_files",
                path_pattern="logs/**/*.log",
                max_age_days=30,
                max_size_mb=100
            ),
            CleanupRule(
                name="old_logs",
                path_pattern="logs/**/*.log.*",
                max_age_days=7
            ),
            CleanupRule(
                name="backup_files",
                path_pattern="**/*.bak",
                max_age_days=14
            ),
        ]
        
        for rule in default_rules:
            self._cleanup_rules.append(rule)
    
    def add_cleanup_rule(self, rule: CleanupRule) -> None:
        """添加清理规则"""
        self._cleanup_rules.append(rule)
    
    def remove_cleanup_rule(self, rule_name: str) -> bool:
        """移除清理规则"""
        for i, rule in enumerate(self._cleanup_rules):
            if rule.name == rule_name:
                self._cleanup_rules.pop(i)
                return True
        return False
    
    async def run_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        执行清理任务
        
        参数：
            dry_run: 是否为模拟运行（不实际删除文件）
        
        返回：
            清理结果统计
        """
        results = {
            "start_time": datetime.now().isoformat(),
            "dry_run": dry_run,
            "rules_processed": 0,
            "files_found": 0,
            "files_deleted": 0,
            "space_reclaimed_mb": 0.0,
            "errors": [],
            "details": []
        }
        
        for rule in self._cleanup_rules:
            if not rule.enabled:
                continue
            
            try:
                rule_result = await self._process_rule(rule, dry_run)
                results["rules_processed"] += 1
                results["files_found"] += rule_result["files_found"]
                results["files_deleted"] += rule_result["files_deleted"]
                results["space_reclaimed_mb"] += rule_result["space_reclaimed_mb"]
                results["details"].append({
                    "rule": rule.name,
                    **rule_result
                })
            except Exception as e:
                results["errors"].append(f"规则 {rule.name} 执行失败: {str(e)}")
        
        results["end_time"] = datetime.now().isoformat()
        
        # 记录清理历史
        self._cleanup_history.append({
            "timestamp": results["start_time"],
            "dry_run": dry_run,
            "files_deleted": results["files_deleted"],
            "space_reclaimed_mb": results["space_reclaimed_mb"]
        })
        
        return results
    
    async def _process_rule(self, rule: CleanupRule, dry_run: bool) -> Dict[str, Any]:
        """处理单个清理规则"""
        result = {
            "files_found": 0,
            "files_deleted": 0,
            "space_reclaimed_mb": 0.0,
            "files": []
        }
        
        # 查找匹配的文件
        pattern_path = self.project_root / rule.path_pattern
        
        if "**" in rule.path_pattern:
            # 递归查找
            base_path = self.project_root
            relative_pattern = rule.path_pattern.replace("**/", "")
            
            for file_path in base_path.rglob(relative_pattern):
                if self._should_delete(file_path, rule):
                    result["files_found"] += 1
                    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                    
                    if not dry_run:
                        try:
                            if file_path.is_dir():
                                shutil.rmtree(file_path)
                            else:
                                file_path.unlink()
                            result["files_deleted"] += 1
                            result["space_reclaimed_mb"] += file_size
                            result["files"].append(str(file_path))
                        except Exception as e:
                            result["files"].append(f"{file_path} (删除失败: {e})")
                    else:
                        result["files"].append(f"{file_path} (模拟删除)")
        else:
            # 直接匹配
            if pattern_path.exists():
                for file_path in pattern_path.parent.glob(pattern_path.name):
                    if self._should_delete(file_path, rule):
                        result["files_found"] += 1
                        file_size = file_path.stat().st_size / (1024 * 1024)
                        
                        if not dry_run:
                            try:
                                if file_path.is_dir():
                                    shutil.rmtree(file_path)
                                else:
                                    file_path.unlink()
                                result["files_deleted"] += 1
                                result["space_reclaimed_mb"] += file_size
                                result["files"].append(str(file_path))
                            except Exception as e:
                                result["files"].append(f"{file_path} (删除失败: {e})")
                        else:
                            result["files"].append(f"{file_path} (模拟删除)")
        
        return result
    
    def _should_delete(self, file_path: Path, rule: CleanupRule) -> bool:
        """判断是否应该删除文件"""
        # 检查排除模式
        for exclude in rule.exclude_patterns:
            if exclude in str(file_path):
                return False
        
        try:
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            age_days = (datetime.now() - modified_time).days
            
            # 检查年龄
            if age_days > rule.max_age_days:
                return True
            
            # 检查大小
            if rule.max_size_mb:
                file_size_mb = stat.st_size / (1024 * 1024)
                if file_size_mb > rule.max_size_mb:
                    return True
            
        except Exception:
            return False
        
        return False
    
    async def find_duplicates(self, directories: List[str], 
                            min_size_kb: int = 1) -> List[DuplicateFile]:
        """
        查找重复文件
        
        参数：
            directories: 要扫描的目录列表
            min_size_kb: 最小文件大小(KB)
        
        返回：
            重复文件列表
        """
        file_hashes: Dict[str, List[Path]] = {}
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size
                    
                    # 跳过小文件
                    if file_size < min_size_kb * 1024:
                        continue
                    
                    # 计算文件哈希
                    file_hash = await self._calculate_hash(file_path)
                    
                    if file_hash in file_hashes:
                        file_hashes[file_hash].append(file_path)
                    else:
                        file_hashes[file_hash] = [file_path]
                        
                except Exception:
                    continue
        
        # 构建重复文件列表
        duplicates = []
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                # 保留第一个，其余标记为重复
                original = paths[0]
                stat = original.stat()
                
                dup = DuplicateFile(
                    file_path=str(original),
                    file_hash=file_hash,
                    file_size=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime),
                    duplicates=[str(p) for p in paths[1:]]
                )
                duplicates.append(dup)
        
        return duplicates
    
    async def _calculate_hash(self, file_path: Path, 
                            chunk_size: int = 8192) -> str:
        """计算文件哈希"""
        hasher = hashlib.md5()
        
        def read_chunks():
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        
        # 在线程池中执行文件读取
        loop = asyncio.get_event_loop()
        for chunk in await loop.run_in_executor(None, 
                                               lambda: list(read_chunks())):
            hasher.update(chunk)
        
        return hasher.hexdigest()
    
    async def remove_duplicates(self, duplicates: List[DuplicateFile],
                               keep_strategy: str = "first",
                               dry_run: bool = False) -> Dict[str, Any]:
        """
        删除重复文件
        
        参数：
            duplicates: 重复文件列表
            keep_strategy: 保留策略（first/last/newest/largest）
            dry_run: 是否为模拟运行
        
        返回：
            删除结果统计
        """
        results = {
            "files_removed": 0,
            "space_reclaimed_mb": 0.0,
            "errors": []
        }
        
        for dup in duplicates:
            files_to_remove = dup.duplicates
            
            for file_path in files_to_remove:
                try:
                    path = Path(file_path)
                    if path.exists():
                        file_size = path.stat().st_size / (1024 * 1024)
                        
                        if not dry_run:
                            path.unlink()
                        
                        results["files_removed"] += 1
                        results["space_reclaimed_mb"] += file_size
                        
                except Exception as e:
                    results["errors"].append(f"删除 {file_path} 失败: {e}")
        
        return results
    
    def register_queue_monitor(self, queue_name: str, 
                              monitor_func: Callable[[], QueueStatus]) -> None:
        """注册队列监控函数"""
        self._queue_monitors[queue_name] = monitor_func
    
    async def monitor_queues(self) -> Dict[str, QueueStatus]:
        """监控所有队列状态"""
        statuses = {}
        
        for queue_name, monitor_func in self._queue_monitors.items():
            try:
                status = await asyncio.get_event_loop().run_in_executor(
                    None, monitor_func
                )
                statuses[queue_name] = status
            except Exception as e:
                statuses[queue_name] = QueueStatus(
                    queue_name=queue_name,
                    pending_count=-1,
                    processing_count=-1,
                    completed_count=-1,
                    failed_count=-1,
                    avg_wait_time=0.0,
                    avg_process_time=0.0
                )
        
        return statuses
    
    def register_error_handler(self, error_type: str, 
                              handler: Callable[[Exception], bool]) -> None:
        """注册错误处理器"""
        self._error_handlers[error_type] = handler
    
    async def handle_error(self, error: Exception, 
                          context: Dict[str, Any]) -> bool:
        """
        处理错误
        
        返回：
            bool: 是否成功处理
        """
        error_type = type(error).__name__
        
        # 查找对应的处理器
        handler = self._error_handlers.get(error_type)
        if handler:
            try:
                return await asyncio.get_event_loop().run_in_executor(
                    None, lambda: handler(error)
                )
            except Exception as e:
                print(f"错误处理器执行失败: {e}")
        
        # 默认处理：记录错误
        print(f"未处理的错误 [{error_type}]: {error}")
        print(f"上下文: {context}")
        
        return False
    
    def get_cleanup_history(self, days: int = 30) -> List[Dict]:
        """获取清理历史"""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            h for h in self._cleanup_history
            if datetime.fromisoformat(h["timestamp"]) > cutoff
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        history = self._cleanup_history
        
        if not history:
            return {
                "total_cleanups": 0,
                "total_files_deleted": 0,
                "total_space_reclaimed_mb": 0.0,
                "avg_files_per_cleanup": 0.0,
                "avg_space_per_cleanup_mb": 0.0
            }
        
        total_files = sum(h["files_deleted"] for h in history)
        total_space = sum(h["space_reclaimed_mb"] for h in history)
        
        return {
            "total_cleanups": len(history),
            "total_files_deleted": total_files,
            "total_space_reclaimed_mb": round(total_space, 2),
            "avg_files_per_cleanup": round(total_files / len(history), 2),
            "avg_space_per_cleanup_mb": round(total_space / len(history), 2)
        }


# 全局清理管理器实例
cleanup_manager = CleanupManager()


# 便捷函数
async def run_cleanup(dry_run: bool = False) -> Dict[str, Any]:
    """运行清理任务"""
    return await cleanup_manager.run_cleanup(dry_run)


async def find_and_remove_duplicates(directories: List[str],
                                     dry_run: bool = False) -> Dict[str, Any]:
    """查找并删除重复文件"""
    duplicates = await cleanup_manager.find_duplicates(directories)
    return await cleanup_manager.remove_duplicates(duplicates, dry_run=dry_run)
