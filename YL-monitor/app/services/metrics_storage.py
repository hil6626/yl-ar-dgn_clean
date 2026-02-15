"""
【文件功能】监控数据存储服务
实现监控数据的持久化存储、归档和查询

【作者信息】
作者: AI Assistant
创建时间: 2026-02-08
最后更新: 2026-02-08

【版本历史】
- v1.0.0 (2026-02-08): 初始版本，实现监控数据存储核心功能

【依赖说明】
- 标准库: json, os, gzip, shutil, datetime, pathlib, typing
- 第三方库: 无
- 内部模块: app.models.alert

【使用示例】
```python
from app.services.metrics_storage import metrics_storage

# 存储指标数据
await metrics_storage.store_metric(metric_data)

# 查询历史数据
history = await metrics_storage.query_history(
    metric_type="cpu",
    start_time=start,
    end_time=end
)

# 获取存储统计
stats = metrics_storage.get_storage_stats()
```
"""

import json
import gzip
import shutil
import asyncio
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from app.models.alert import MetricType


@dataclass
class StoredMetric:
    """【存储的指标数据】"""
    timestamp: str
    metric_type: str
    name: str
    value: float
    unit: str
    labels: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredMetric":
        """从字典创建"""
        return cls(**data)


class MetricsStorage:
    """
    【监控数据存储器】监控数据存储类
    
    【主要职责】
    1. 接收和存储实时指标数据
    2. 按时间组织数据文件
    3. 自动归档旧数据
    4. 提供历史数据查询
    5. 管理存储空间
    """
    
    def __init__(
        self,
        data_dir: str = "data/metrics",
        hot_days: int = 7,
        warm_days: int = 30,
        archive_format: str = "gzip"
    ):
        """
        【初始化】
        
        【参数说明】
        - data_dir: 数据存储目录
        - hot_days: 热数据保留天数（最近N天，原始格式）
        - warm_days: 温数据保留天数（N天后压缩）
        - archive_format: 归档格式（gzip/none）
        """
        self._data_dir = Path(data_dir)
        self._hot_days = hot_days
        self._warm_days = warm_days
        self._archive_format = archive_format
        
        # 子目录
        self._raw_dir = self._data_dir / "raw"
        self._archive_dir = self._data_dir / "archive"
        self._index_file = self._data_dir / "index.json"
        
        # 内存缓存（热数据）
        self._cache: Dict[str, List[StoredMetric]] = {}
        self._cache_lock = asyncio.Lock()
        
        # 统计信息
        self._stats = {
            "total_stored": 0,
            "total_archived": 0,
            "storage_size_bytes": 0,
            "last_cleanup": None
        }
        
        # 日志前缀
        self._log_prefix = "[监控数据存储]"
        
        # 初始化
        self._ensure_directories()
        self._load_index()
    
    def _ensure_directories(self):
        """【确保目录存在】创建必要的目录结构"""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._raw_dir.mkdir(parents=True, exist_ok=True)
        self._archive_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """【加载索引】加载数据索引文件"""
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                    self._stats["total_stored"] = index.get("total_stored", 0)
                    self._stats["total_archived"] = index.get("total_archived", 0)
            except Exception as e:
                print(f"{self._log_prefix} 加载索引失败: {e}")
    
    async def _save_index(self):
        """【保存索引】保存数据索引"""
        try:
            index = {
                "total_stored": self._stats["total_stored"],
                "total_archived": self._stats["total_archived"],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            async with aiofiles.open(self._index_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(index, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"{self._log_prefix} 保存索引失败: {e}")
    
    async def store_metric(self, metric_data: Dict[str, Any]) -> bool:
        """
        【存储指标】存储单个指标数据
        
        【参数说明】
        - metric_data: 指标数据字典
        
        【返回值】
        - bool: 是否成功
        """
        try:
            # 创建存储对象
            metric = StoredMetric(
                timestamp=metric_data.get("timestamp", datetime.utcnow().isoformat()),
                metric_type=metric_data.get("metric_type", "custom"),
                name=metric_data.get("name", "unknown"),
                value=float(metric_data.get("value", 0)),
                unit=metric_data.get("unit", ""),
                labels=metric_data.get("labels", {})
            )
            
            # 确定存储文件（按天）
            date_str = metric.timestamp[:10]  # YYYY-MM-DD
            file_path = self._raw_dir / f"{date_str}.jsonl"
            
            # 追加写入
            async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
                await f.write(json.dumps(metric.to_dict(), ensure_ascii=False) + '\n')
            
            # 更新统计
            self._stats["total_stored"] += 1
            
            # 更新缓存
            async with self._cache_lock:
                if date_str not in self._cache:
                    self._cache[date_str] = []
                self._cache[date_str].append(metric)
            
            return True
            
        except Exception as e:
            print(f"{self._log_prefix} 存储指标失败: {e}")
            return False
    
    async def store_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """
        【批量存储】批量存储指标数据
        
        【参数说明】
        - metrics: 指标数据列表
        
        【返回值】
        - int: 成功存储的数量
        """
        success_count = 0
        for metric in metrics:
            if await self.store_metric(metric):
                success_count += 1
        
        # 批量保存后更新索引
        if success_count > 0:
            await self._save_index()
        
        return success_count
    
    async def query_history(
        self,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        【查询历史】查询历史指标数据
        
        【参数说明】
        - metric_type: 指标类型筛选
        - start_time: 开始时间
        - end_time: 结束时间
        - labels: 标签筛选
        - limit: 返回数量限制
        
        【返回值】
        - List[Dict]: 指标数据列表
        """
        results = []
        
        # 确定查询的日期范围
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=self._hot_days)
        if not end_time:
            end_time = datetime.utcnow()
        
        # 生成日期列表
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 尝试从缓存读取
            cache_data = await self._get_from_cache(date_str)
            if cache_data:
                results.extend(cache_data)
            else:
                # 从文件读取
                file_data = await self._read_day_data(date_str)
                results.extend(file_data)
            
            current_date += timedelta(days=1)
        
        # 应用筛选
        filtered_results = []
        for metric in results:
            # 时间筛选
            metric_time = datetime.fromisoformat(metric["timestamp"].replace('Z', '+00:00'))
            if metric_time < start_time or metric_time > end_time:
                continue
            
            # 类型筛选
            if metric_type and metric["metric_type"] != metric_type:
                continue
            
            # 标签筛选
            if labels:
                metric_labels = metric.get("labels", {})
                if not all(metric_labels.get(k) == v for k, v in labels.items()):
                    continue
            
            filtered_results.append(metric)
            
            if len(filtered_results) >= limit:
                break
        
        # 按时间排序
        filtered_results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return filtered_results
    
    async def _get_from_cache(self, date_str: str) -> Optional[List[Dict[str, Any]]]:
        """【从缓存获取】"""
        async with self._cache_lock:
            if date_str in self._cache:
                return [m.to_dict() for m in self._cache[date_str]]
        return None
    
    async def _read_day_data(self, date_str: str) -> List[Dict[str, Any]]:
        """【读取单日数据】"""
        file_path = self._raw_dir / f"{date_str}.jsonl"
        
        if not file_path.exists():
            return []
        
        try:
            metrics = []
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            metrics.append(data)
                        except json.JSONDecodeError:
                            continue
            
            # 加载到缓存
            async with self._cache_lock:
                self._cache[date_str] = [StoredMetric.from_dict(m) for m in metrics]
            
            return metrics
            
        except Exception as e:
            print(f"{self._log_prefix} 读取数据失败 {date_str}: {e}")
            return []
    
    async def aggregate(
        self,
        metric_type: str,
        aggregation: str = "avg",  # avg, max, min, sum, count
        interval: str = "hour",    # hour, day
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        【聚合查询】按时间间隔聚合指标数据
        
        【参数说明】
        - metric_type: 指标类型
        - aggregation: 聚合方式
        - interval: 时间间隔
        - start_time: 开始时间
        - end_time: 结束时间
        
        【返回值】
        - List[Dict]: 聚合结果
        """
        # 获取原始数据
        raw_data = await self.query_history(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if not raw_data:
            return []
        
        # 按时间间隔分组
        from collections import defaultdict
        groups = defaultdict(list)
        
        for metric in raw_data:
            timestamp = datetime.fromisoformat(metric["timestamp"].replace('Z', '+00:00'))
            
            if interval == "hour":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            elif interval == "day":
                key = timestamp.strftime("%Y-%m-%d")
            else:
                key = timestamp.strftime("%Y-%m-%d %H:00")
            
            groups[key].append(metric["value"])
        
        # 计算聚合值
        results = []
        for time_key, values in sorted(groups.items()):
            if aggregation == "avg":
                agg_value = sum(values) / len(values) if values else 0
            elif aggregation == "max":
                agg_value = max(values) if values else 0
            elif aggregation == "min":
                agg_value = min(values) if values else 0
            elif aggregation == "sum":
                agg_value = sum(values)
            elif aggregation == "count":
                agg_value = len(values)
            else:
                agg_value = sum(values) / len(values) if values else 0
            
            results.append({
                "timestamp": time_key,
                "value": round(agg_value, 2),
                "count": len(values),
                "metric_type": metric_type,
                "aggregation": aggregation
            })
        
        return results
    
    async def cleanup_old_data(self) -> Dict[str, Any]:
        """
        【清理旧数据】清理过期数据并归档
        
        【返回值】
        - Dict: 清理结果统计
        """
        now = datetime.utcnow()
        hot_cutoff = now - timedelta(days=self._hot_days)
        warm_cutoff = now - timedelta(days=self._warm_days)
        
        cleanup_stats = {
            "archived_files": 0,
            "deleted_files": 0,
            "errors": []
        }
        
        # 遍历原始数据文件
        for file_path in self._raw_dir.glob("*.jsonl"):
            try:
                # 解析日期
                date_str = file_path.stem  # YYYY-MM-DD
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # 归档温数据（7-30天）
                if file_date < hot_cutoff and file_date >= warm_cutoff:
                    if self._archive_format == "gzip":
                        await self._gzip_file(file_path)
                        cleanup_stats["archived_files"] += 1
                
                # 删除冷数据（30天以上）
                elif file_date < warm_cutoff:
                    # 可以选择删除或迁移到长期存储
                    # 这里先保留，只记录
                    pass
                    
            except Exception as e:
                cleanup_stats["errors"].append(str(e))
        
        # 更新统计
        self._stats["last_cleanup"] = now.isoformat()
        await self._save_index()
        
        return cleanup_stats
    
    async def _gzip_file(self, file_path: Path):
        """【压缩文件】"""
        try:
            archive_path = self._archive_dir / f"{file_path.stem}.jsonl.gz"
            
            # 压缩
            with open(file_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            file_path.unlink()
            
            self._stats["total_archived"] += 1
            
        except Exception as e:
            print(f"{self._log_prefix} 压缩文件失败 {file_path}: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        【获取存储统计】
        
        【返回值】
        - Dict: 存储统计信息
        """
        # 计算存储大小
        total_size = 0
        file_count = 0
        
        for file_path in self._raw_dir.glob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        for file_path in self._archive_dir.glob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        self._stats["storage_size_bytes"] = total_size
        self._stats["storage_size_mb"] = round(total_size / (1024 * 1024), 2)
        self._stats["file_count"] = file_count
        
        # 计算日期范围
        dates = []
        for file_path in self._raw_dir.glob("*.jsonl"):
            try:
                date_str = file_path.stem
                dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
            except:
                continue
        
        for file_path in self._archive_dir.glob("*.jsonl.gz"):
            try:
                date_str = file_path.stem
                dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
            except:
                continue
        
        if dates:
            self._stats["earliest_date"] = min(dates).strftime("%Y-%m-%d")
            self._stats["latest_date"] = max(dates).strftime("%Y-%m-%d")
        else:
            self._stats["earliest_date"] = None
            self._stats["latest_date"] = None
        
        return self._stats.copy()
    
    async def export_data(
        self,
        start_time: datetime,
        end_time: datetime,
        format: str = "json",
        metric_type: Optional[str] = None
    ) -> Tuple[str, bytes]:
        """
        【导出数据】导出指定时间范围的数据
        
        【参数说明】
        - start_time: 开始时间
        - end_time: 结束时间
        - format: 导出格式（json/csv）
        - metric_type: 指标类型筛选
        
        【返回值】
        - Tuple[str, bytes]: (文件名, 数据内容)
        """
        # 查询数据
        data = await self.query_history(
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=100000
        )
        
        if format == "json":
            # JSON格式
            content = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            filename = f"metrics_export_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.json"
            
        elif format == "csv":
            # CSV格式
            import csv
            import io
            
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            content = output.getvalue().encode('utf-8')
            filename = f"metrics_export_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.csv"
            
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        return filename, content


# 【全局存储实例】
metrics_storage = MetricsStorage()


# 【便捷函数】
async def store_metric(metric_data: Dict[str, Any]) -> bool:
    """【便捷函数】存储单个指标"""
    return await metrics_storage.store_metric(metric_data)


async def query_metrics_history(**kwargs) -> List[Dict[str, Any]]:
    """【便捷函数】查询历史数据"""
    return await metrics_storage.query_history(**kwargs)


async def aggregate_metrics(**kwargs) -> List[Dict[str, Any]]:
    """【便捷函数】聚合查询"""
    return await metrics_storage.aggregate(**kwargs)


def get_storage_stats() -> Dict[str, Any]:
    """【便捷函数】获取存储统计"""
    return metrics_storage.get_storage_stats()
