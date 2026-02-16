#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统资源层监控器 (L2)
提供 CPU、内存、GPU 的详细监控
"""

import os
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class CPUMetrics:
    """CPU 详细指标"""
    overall_percent: float
    per_cpu_percent: List[float]
    cpu_count_logical: int
    cpu_count_physical: int
    cpu_freq_current: Optional[float]
    cpu_freq_min: Optional[float]
    cpu_freq_max: Optional[float]
    ctx_switches: int
    interrupts: int
    soft_interrupts: int
    syscalls: int
    load_avg_1m: float
    load_avg_5m: float
    load_avg_15m: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryMetrics:
    """内存详细指标"""
    total: int
    available: int
    used: int
    free: int
    percent: float
    active: int
    inactive: int
    buffers: int
    cached: int
    shared: int
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessMemoryInfo:
    """进程内存信息"""
    pid: int
    name: str
    memory_rss: int
    memory_vms: int
    memory_percent: float
    cpu_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GPUMetrics:
    """GPU 指标"""
    gpu_id: int
    name: str
    driver_version: str
    utilization_gpu: float
    utilization_memory: float
    memory_total: int
    memory_used: int
    memory_free: int
    temperature: float
    power_draw: Optional[float]
    power_limit: Optional[float]
    fan_speed: Optional[float]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CPUDetailedMonitor:
    """
    CPU 详细监控器
    
    监控指标：
    - 整体和每核 CPU 使用率
    - CPU 频率（当前/最小/最大）
    - 上下文切换次数
    - 中断次数
    - 系统调用次数
    - 系统负载（1/5/15分钟）
    """
    
    def __init__(self, history_size: int = 60):
        self.history_size = history_size
        self._usage_history: deque = deque(maxlen=history_size)
        self._last_cpu_times = None
    
    def collect_metrics(self) -> CPUMetrics:
        """
        采集 CPU 详细指标
        """
        try:
            # 获取 CPU 使用率
            overall_percent = psutil.cpu_percent(interval=0.1)
            per_cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # 获取 CPU 频率
            freq_info = psutil.cpu_freq()
            cpu_freq_current = freq_info.current if freq_info else None
            cpu_freq_min = freq_info.min if freq_info else None
            cpu_freq_max = freq_info.max if freq_info else None
            
            # 获取 CPU 统计信息
            cpu_stats = psutil.cpu_stats()
            
            # 获取系统负载（Linux/Unix）
            try:
                load_avg_1m, load_avg_5m, load_avg_15m = os.getloadavg()
            except (AttributeError, OSError):
                load_avg_1m = load_avg_5m = load_avg_15m = 0.0
            
            metrics = CPUMetrics(
                overall_percent=overall_percent,
                per_cpu_percent=list(per_cpu_percent),
                cpu_count_logical=psutil.cpu_count(logical=True),
                cpu_count_physical=psutil.cpu_count(logical=False),
                cpu_freq_current=cpu_freq_current,
                cpu_freq_min=cpu_freq_min,
                cpu_freq_max=cpu_freq_max,
                ctx_switches=cpu_stats.ctx_switches,
                interrupts=cpu_stats.interrupts,
                soft_interrupts=cpu_stats.soft_interrupts,
                syscalls=cpu_stats.syscalls,
                load_avg_1m=load_avg_1m,
                load_avg_5m=load_avg_5m,
                load_avg_15m=load_avg_15m,
                timestamp=datetime.now().isoformat()
            )
            
            # 保存历史
            self._usage_history.append({
                'timestamp': metrics.timestamp,
                'overall': overall_percent,
                'per_cpu': list(per_cpu_percent)
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"采集 CPU 指标失败: {e}")
            raise
    
    def get_usage_history(self) -> List[Dict[str, Any]]:
        """
        获取 CPU 使用率历史
        """
        return list(self._usage_history)
    
    def get_cpu_pressure(self) -> Dict[str, Any]:
        """
        获取 CPU 压力评估
        """
        if len(self._usage_history) < 3:
            return {"status": "insufficient_data"}
        
        recent = list(self._usage_history)[-3:]
        avg_usage = sum(r['overall'] for r in recent) / len(recent)
        
        if avg_usage > 90:
            status = "critical"
            suggestion = "CPU 严重过载，需要立即扩容或优化"
        elif avg_usage > 70:
            status = "warning"
            suggestion = "CPU 负载较高，建议监控并准备扩容"
        elif avg_usage > 50:
            status = "elevated"
            suggestion = "CPU 负载中等，正常范围内"
        else:
            status = "normal"
            suggestion = "CPU 负载正常"
        
        return {
            "status": status,
            "average_usage": round(avg_usage, 2),
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat()
        }


class MemoryDetailedMonitor:
    """
    内存详细监控器
    
    监控指标：
    - 物理内存总量/可用/已用/空闲
    - 活跃/非活跃内存
    - 缓冲区/缓存
    - 共享内存
    - 交换空间总量/已用/空闲
    - 内存使用趋势
    - Top 内存消耗进程
    """
    
    def __init__(self, history_size: int = 60):
        self.history_size = history_size
        self._usage_history: deque = deque(maxlen=history_size)
    
    def collect_metrics(self) -> MemoryMetrics:
        """
        采集内存详细指标
        """
        try:
            # 虚拟内存
            vm = psutil.virtual_memory()
            
            # 交换空间
            swap = psutil.swap_memory()
            
            metrics = MemoryMetrics(
                total=vm.total,
                available=vm.available,
                used=vm.used,
                free=vm.free,
                percent=vm.percent,
                active=getattr(vm, 'active', 0),
                inactive=getattr(vm, 'inactive', 0),
                buffers=getattr(vm, 'buffers', 0),
                cached=getattr(vm, 'cached', 0),
                shared=getattr(vm, 'shared', 0),
                swap_total=swap.total,
                swap_used=swap.used,
                swap_free=swap.free,
                swap_percent=swap.percent,
                timestamp=datetime.now().isoformat()
            )
            
            # 保存历史
            self._usage_history.append({
                'timestamp': metrics.timestamp,
                'percent': vm.percent,
                'used': vm.used,
                'available': vm.available
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"采集内存指标失败: {e}")
            raise
    
    def get_top_memory_processes(self, n: int = 10) -> List[ProcessMemoryInfo]:
        """
        获取内存消耗最多的进程
        
        Args:
            n: 返回进程数量
            
        Returns:
            进程内存信息列表
        """
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 
                                              'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    mem_info = info.get('memory_info')
                    
                    if mem_info:
                        processes.append(ProcessMemoryInfo(
                            pid=info['pid'],
                            name=info['name'],
                            memory_rss=mem_info.rss,
                            memory_vms=mem_info.vms,
                            memory_percent=info.get('memory_percent', 0.0),
                            cpu_percent=info.get('cpu_percent', 0.0)
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            logger.error(f"获取进程内存信息失败: {e}")
        
        # 按内存使用率排序
        processes.sort(key=lambda x: x.memory_percent, reverse=True)
        return processes[:n]
    
    def get_memory_pressure(self) -> Dict[str, Any]:
        """
        获取内存压力评估
        """
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 评估内存压力
            if vm.percent > 95 or swap.percent > 50:
                status = "critical"
                suggestion = "内存严重不足，可能导致 OOM"
            elif vm.percent > 85:
                status = "warning"
                suggestion = "内存使用率较高，建议优化"
            elif vm.percent > 70:
                status = "elevated"
                suggestion = "内存使用率中等"
            else:
                status = "normal"
                suggestion = "内存使用正常"
            
            return {
                "status": status,
                "memory_percent": vm.percent,
                "swap_percent": swap.percent,
                "available_gb": round(vm.available / (1024**3), 2),
                "suggestion": suggestion,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"评估内存压力失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_usage_history(self) -> List[Dict[str, Any]]:
        """
        获取内存使用历史
        """
        return list(self._usage_history)


class GPUMonitor:
    """
    GPU 监控器
    
    监控指标（需要 pynvml）：
    - GPU 利用率
    - 显存使用（总量/已用/空闲）
    - GPU 温度
    - 功耗（当前/限制）
    - 风扇转速
    """
    
    def __init__(self):
        self._nvml_available = False
        self._pynvml = None
        self._init_nvml()
    
    def _init_nvml(self):
        """
        初始化 NVML（NVIDIA Management Library）
        """
        try:
            import pynvml
            self._pynvml = pynvml
            pynvml.nvmlInit()
            self._nvml_available = True
            logger.info("NVML 初始化成功")
        except ImportError:
            logger.warning("pynvml 未安装，GPU 监控不可用")
        except Exception as e:
            logger.warning(f"NVML 初始化失败: {e}")
    
    def is_available(self) -> bool:
        """
        检查 GPU 监控是否可用
        """
        return self._nvml_available
    
    def collect_metrics(self) -> List[GPUMetrics]:
        """
        采集 GPU 指标
        """
        if not self._nvml_available:
            return []
        
        metrics = []
        
        try:
            device_count = self._pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = self._pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # 基本信息
                name = self._pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                driver_version = self._pynvml.nvmlSystemGetDriverVersion()
                if isinstance(driver_version, bytes):
                    driver_version = driver_version.decode('utf-8')
                
                # 利用率
                utilization = self._pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                # 显存
                mem_info = self._pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # 温度
                temperature = self._pynvml.nvmlDeviceGetTemperature(
                    handle, self._pynvml.NVML_TEMPERATURE_GPU
                )
                
                # 功耗
                try:
                    power_draw = self._pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                    power_limit = (
                        self._pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0
                    )
                except:
                    power_draw = None
                    power_limit = None
                
                # 风扇转速
                try:
                    fan_speed = self._pynvml.nvmlDeviceGetFanSpeed(handle)
                except:
                    fan_speed = None
                
                metrics.append(GPUMetrics(
                    gpu_id=i,
                    name=name,
                    driver_version=driver_version,
                    utilization_gpu=utilization.gpu,
                    utilization_memory=utilization.memory,
                    memory_total=mem_info.total,
                    memory_used=mem_info.used,
                    memory_free=mem_info.free,
                    temperature=temperature,
                    power_draw=power_draw,
                    power_limit=power_limit,
                    fan_speed=fan_speed,
                    timestamp=datetime.now().isoformat()
                ))
        
        except Exception as e:
            logger.error(f"采集 GPU 指标失败: {e}")
        
        return metrics
    
    def get_gpu_summary(self) -> Dict[str, Any]:
        """
        获取 GPU 汇总信息
        """
        if not self._nvml_available:
            return {
                "available": False,
                "message": "GPU 监控不可用（pynvml 未安装或初始化失败）",
                "timestamp": datetime.now().isoformat()
            }
        
        metrics = self.collect_metrics()
        
        if not metrics:
            return {
                "available": True,
                "gpu_count": 0,
                "message": "未检测到 GPU",
                "timestamp": datetime.now().isoformat()
            }
        
        # 计算汇总
        total_memory = sum(g.memory_total for g in metrics)
        used_memory = sum(g.memory_used for g in metrics)
        avg_utilization = sum(g.utilization_gpu for g in metrics) / len(metrics)
        max_temperature = max(g.temperature for g in metrics)
        
        return {
            "available": True,
            "gpu_count": len(metrics),
            "total_memory_gb": round(total_memory / (1024**3), 2),
            "used_memory_gb": round(used_memory / (1024**3), 2),
            "memory_percent": round(used_memory / total_memory * 100, 2),
            "average_utilization": round(avg_utilization, 2),
            "max_temperature": max_temperature,
            "gpus": [g.to_dict() for g in metrics],
            "timestamp": datetime.now().isoformat()
        }


class SystemResourceCollector:
    """
    系统资源指标采集器
    
    整合 CPU、内存、GPU 监控器
    """
    
    def __init__(self):
        self.cpu_monitor = CPUDetailedMonitor()
        self.memory_monitor = MemoryDetailedMonitor()
        self.gpu_monitor = GPUMonitor()
    
    def collect_all(self) -> Dict[str, Any]:
        """
        采集所有系统资源层指标
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "layer": "L2_system_resources"
        }
        
        # CPU 指标
        try:
            result["cpu"] = self.cpu_monitor.collect_metrics().to_dict()
            result["cpu_pressure"] = self.cpu_monitor.get_cpu_pressure()
        except Exception as e:
            result["cpu"] = {"error": str(e)}
            result["cpu_pressure"] = {"status": "error", "error": str(e)}
        
        # 内存指标
        try:
            result["memory"] = self.memory_monitor.collect_metrics().to_dict()
            result["memory_pressure"] = self.memory_monitor.get_memory_pressure()
            result["top_memory_processes"] = [
                p.to_dict() for p in self.memory_monitor.get_top_memory_processes(5)
            ]
        except Exception as e:
            result["memory"] = {"error": str(e)}
            result["memory_pressure"] = {"status": "error", "error": str(e)}
        
        # GPU 指标
        try:
            result["gpu"] = self.gpu_monitor.get_gpu_summary()
        except Exception as e:
            result["gpu"] = {"available": False, "error": str(e)}
        
        return result
    
    def get_resource_pressure(self) -> Dict[str, Any]:
        """
        获取整体资源压力评估
        """
        cpu_pressure = self.cpu_monitor.get_cpu_pressure()
        memory_pressure = self.memory_monitor.get_memory_pressure()
        
        # 综合评估
        critical_count = sum([
            cpu_pressure.get("status") == "critical",
            memory_pressure.get("status") == "critical"
        ])
        warning_count = sum([
            cpu_pressure.get("status") == "warning",
            memory_pressure.get("status") == "warning"
        ])
        
        if critical_count > 0:
            overall_status = "critical"
            overall_suggestion = "系统资源严重不足，需要立即处理"
        elif warning_count > 0:
            overall_status = "warning"
            overall_suggestion = "系统资源紧张，建议优化或扩容"
        else:
            overall_status = "normal"
            overall_suggestion = "系统资源使用正常"
        
        return {
            "overall_status": overall_status,
            "overall_suggestion": overall_suggestion,
            "cpu": cpu_pressure,
            "memory": memory_pressure,
            "timestamp": datetime.now().isoformat()
        }


# 全局采集器实例
system_resource_collector = SystemResourceCollector()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("系统资源层监控测试")
    print("=" * 60)
    
    collector = SystemResourceCollector()
    
    # 测试 CPU 监控
    print("\n1. CPU 监控:")
    try:
        cpu_metrics = collector.cpu_monitor.collect_metrics()
        print(f"  整体使用率: {cpu_metrics.overall_percent:.1f}%")
        print(f"  核心数: {cpu_metrics.cpu_count_logical} 逻辑 / "
              f"{cpu_metrics.cpu_count_physical} 物理")
        print(f"  频率: {cpu_metrics.cpu_freq_current:.0f} MHz")
        print(f"  负载: {cpu_metrics.load_avg_1m:.2f} / "
              f"{cpu_metrics.load_avg_5m:.2f} / "
              f"{cpu_metrics.load_avg_15m:.2f}")
        
        pressure = collector.cpu_monitor.get_cpu_pressure()
        print(f"  压力状态: {pressure['status']}")
    except Exception as e:
        print(f"  ❌ CPU 监控失败: {e}")
    
    # 测试内存监控
    print("\n2. 内存监控:")
    try:
        mem_metrics = collector.memory_monitor.collect_metrics()
        print(f"  总内存: {mem_metrics.total / (1024**3):.1f} GB")
        print(f"  使用率: {mem_metrics.percent:.1f}%")
        print(f"  可用: {mem_metrics.available / (1024**3):.1f} GB")
        print(f"  交换使用率: {mem_metrics.swap_percent:.1f}%")
        
        pressure = collector.memory_monitor.get_memory_pressure()
        print(f"  压力状态: {pressure['status']}")
        
        top_procs = collector.memory_monitor.get_top_memory_processes(3)
        print(f"  Top 3 内存进程:")
        for proc in top_procs:
            print(f"    - {proc.name}: {proc.memory_percent:.1f}% "
                  f"({proc.memory_rss / (1024**2):.1f} MB)")
    except Exception as e:
        print(f"  ❌ 内存监控失败: {e}")
    
    # 测试 GPU 监控
    print("\n3. GPU 监控:")
    try:
        gpu_summary = collector.gpu_monitor.get_gpu_summary()
        if gpu_summary["available"]:
            print(f"  GPU 数量: {gpu_summary['gpu_count']}")
            print(f"  总显存: {gpu_summary['total_memory_gb']:.1f} GB")
            print(f"  显存使用率: {gpu_summary['memory_percent']:.1f}%")
            print(f"  平均利用率: {gpu_summary['average_utilization']:.1f}%")
            print(f"  最高温度: {gpu_summary['max_temperature']}°C")
        else:
            print(f"  ⚠️  {gpu_summary['message']}")
    except Exception as e:
        print(f"  ❌ GPU 监控失败: {e}")
    
    # 整体资源压力
    print("\n4. 整体资源压力:")
    try:
        pressure = collector.get_resource_pressure()
        print(f"  状态: {pressure['overall_status']}")
        print(f"  建议: {pressure['overall_suggestion']}")
    except Exception as e:
        print(f"  ❌ 压力评估失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
