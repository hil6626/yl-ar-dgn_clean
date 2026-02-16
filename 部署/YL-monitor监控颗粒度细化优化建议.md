# YL-Monitor 监控颗粒度细化优化建议

**版本:** 1.0.0  
**创建日期:** 2026-02-16  
**状态:** 优化建议文档

---

## 一、当前监控现状分析

### 1.1 现有监控架构

```
┌─────────────────────────────────────────────────────────────┐
│                    YL-Monitor (端口5500)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Dashboard   │  │  AR Monitor  │  │  DAG Engine  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  AR-backend  │   │  User GUI    │   │  Scripts     │
    │  (端口5501)  │   │  (端口5502)  │   │  (统一入口)   │
    └──────────────┘   └──────────────┘   └──────────────┘
```

### 1.2 现有监控指标

| 层级 | 监控器 | 指标数量 | 采集频率 | 当前状态 |
|------|--------|----------|----------|----------|
| L1 基础设施 | ProcessMonitor, PortMonitor | 15+ | 30-60秒 | ✅ 已部署 |
| L2 系统资源 | CPUDetailedMonitor, MemoryDetailedMonitor, GPUMonitor | 20+ | 30-60秒 | ✅ 已部署 |
| L3 应用服务 | APIDetailedMonitor, DatabaseMonitor | 10+ | 30-60秒 | ✅ 已部署 |
| L4 业务功能 | VideoProcessingMonitor, FaceSwapMonitor, AudioProcessingMonitor | 15+ | 实时 | ✅ 已部署 |
| L5 用户体验 | GUIExperienceMonitor | 10+ | 实时 | ✅ 已部署 |

### 1.3 现有问题识别

| 问题 | 影响 | 优先级 |
|------|------|--------|
| 监控粒度较粗 | 只能发现服务级问题，无法定位到具体模块 | 高 |
| 监控维度较少 | 缺少业务指标、用户体验指标 | 中 |
| 采集频率较低 | 30-60秒间隔，无法捕捉瞬时异常 | 中 |
| 缺少指标关联 | 无法分析指标间的因果关系 | 中 |
| 告警滞后 | 事后告警，无法提前预警 | 高 |

---

## 二、监控颗粒度细化方案

### 2.1 五层监控架构增强

```
┌─────────────────────────────────────────────────────────────────────┐
│                         五层监控架构 (增强版)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  L5: 用户体验层 (User Experience)                                    │
│  ├── GUI响应时间监控 (100ms级)                                      │
│  ├── 用户操作流畅度监控                                              │
│  ├── 页面加载时间监控                                                │
│  └── 用户满意度指标                                                  │
│                                                                     │
│  L4: 业务功能层 (Business Function)                                  │
│  ├── 视频处理FPS监控 (实时)                                          │
│  ├── 人脸合成质量监控                                                │
│  ├── 音频处理延迟监控                                                │
│  ├── 模型加载时间监控                                                │
│  └── 虚拟摄像头输出监控                                              │
│                                                                     │
│  L3: 应用服务层 (Application Service)                                │
│  ├── API响应时间监控 (P50/P95/P99)                                   │
│  ├── 错误率监控                                                      │
│  ├── 吞吐量监控 (QPS/TPS)                                            │
│  ├── 数据库连接池监控                                                │
│  └── 缓存命中率监控                                                  │
│                                                                     │
│  L2: 系统资源层 (System Resources)                                   │
│  ├── CPU详细监控 (每核使用率、频率、温度)                            │
│  ├── 内存详细监控 (分段使用、交换、缓存)                             │
│  ├── GPU监控 (利用率、显存、温度、功耗)                              │
│  ├── 磁盘I/O监控 (读写速率、IOPS、延迟)                             │
│  └── 网络监控 (带宽、延迟、丢包率)                                   │
│                                                                     │
│  L1: 基础设施层 (Infrastructure)                                     │
│  ├── 进程级监控 (PID、线程数、文件描述符)                            │
│  ├── 端口级监控 (连接时间、响应时间)                                 │
│  ├── 文件系统监控 (磁盘使用、inode、文件统计)                        │
│  └── 日志监控 (错误率、关键字匹配)                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 监控指标细化设计

#### L1 基础设施层 - 进程级监控

```python
# 增强版进程监控指标
PROCESS_DETAILED_METRICS = {
    "process_id": "进程ID",
    "process_name": "进程名称",
    "status": "运行状态 (running/sleeping/zombie)",
    "cpu_percent": "CPU使用率 (%)",
    "memory_rss": "实际使用内存 (bytes)",
    "memory_vms": "虚拟内存 (bytes)",
    "memory_percent": "内存使用占比 (%)",
    "num_threads": "线程数",
    "num_fds": "文件描述符数",
    "open_files": "打开文件数",
    "connections": "网络连接数",
    "io_read_bytes": "IO读取字节数",
    "io_write_bytes": "IO写入字节数",
    "context_switches": "上下文切换次数",
    "cpu_times_user": "用户态CPU时间",
    "cpu_times_system": "系统态CPU时间",
    "create_time": "进程创建时间",
    "runtime_seconds": "运行时长 (秒)"
}
```

#### L2 系统资源层 - 详细监控

```python
# CPU详细监控
CPU_DETAILED_METRICS = {
    "overall_percent": "整体使用率 (%)",
    "per_cpu_percent": "每核使用率 [%]",
    "cpu_freq_current": "当前频率 (MHz)",
    "cpu_freq_min": "最小频率 (MHz)",
    "cpu_freq_max": "最大频率 (MHz)",
    "ctx_switches": "上下文切换次数",
    "interrupts": "中断次数",
    "soft_interrupts": "软中断次数",
    "syscalls": "系统调用次数",
    "load_avg_1m": "1分钟负载",
    "load_avg_5m": "5分钟负载",
    "load_avg_15m": "15分钟负载",
    "cpu_temperature": "CPU温度 (°C)"
}

# 内存详细监控
MEMORY_DETAILED_METRICS = {
    "total": "总内存 (bytes)",
    "available": "可用内存 (bytes)",
    "used": "已用内存 (bytes)",
    "free": "空闲内存 (bytes)",
    "percent": "使用百分比 (%)",
    "active": "活跃内存 (bytes)",
    "inactive": "非活跃内存 (bytes)",
    "buffers": "缓冲区 (bytes)",
    "cached": "缓存 (bytes)",
    "shared": "共享内存 (bytes)",
    "swap_total": "交换区总量 (bytes)",
    "swap_used": "交换区已用 (bytes)",
    "swap_free": "交换区空闲 (bytes)",
    "swap_percent": "交换区使用 (%)"
}
```

#### L3 应用服务层 - API详细监控

```python
# API详细监控
API_DETAILED_METRICS = {
    "endpoint": "API端点",
    "method": "HTTP方法",
    "request_count": "请求总数",
    "response_time_p50": "P50响应时间 (ms)",
    "response_time_p95": "P95响应时间 (ms)",
    "response_time_p99": "P99响应时间 (ms)",
    "error_rate": "错误率 (%)",
    "success_rate": "成功率 (%)",
    "qps": "每秒查询数",
    "active_connections": "活跃连接数",
    "queue_size": "请求队列大小",
    "timeout_count": "超时次数"
}
```

#### L4 业务功能层 - 实时业务监控

```python
# 视频处理监控
VIDEO_PROCESSING_METRICS = {
    "fps": "当前帧率",
    "target_fps": "目标帧率",
    "frame_drop_rate": "丢帧率 (%)",
    "processing_time_ms": "单帧处理时间 (ms)",
    "buffer_size": "缓冲区大小",
    "latency_ms": "延迟 (ms)",
    "resolution": "分辨率",
    "codec": "编码格式"
}

# 人脸合成监控
FACE_SWAP_METRICS = {
    "model_loaded": "模型是否加载",
    "model_name": "当前模型名称",
    "model_load_time_ms": "模型加载时间 (ms)",
    "inference_time_ms": "推理时间 (ms)",
    "faces_detected": "检测到的人脸数",
    "faces_swapped": "成功合成的人脸数",
    "quality_score": "合成质量评分 (0-100)",
    "gpu_utilization": "GPU利用率 (%)"
}

# 音频处理监控
AUDIO_PROCESSING_METRICS = {
    "sample_rate": "采样率 (Hz)",
    "channels": "声道数",
    "buffer_size": "缓冲区大小",
    "processing_delay_ms": "处理延迟 (ms)",
    "realtime_factor": "实时因子 (处理时间/音频时长)",
    "effects_active": "活跃音效列表",
    "volume_level": "音量级别 (dB)"
}
```

#### L5 用户体验层 - 交互监控

```python
# GUI体验监控
GUI_EXPERIENCE_METRICS = {
    "ui_response_time_ms": "UI响应时间 (ms)",
    "button_click_latency_ms": "按钮点击延迟 (ms)",
    "page_load_time_ms": "页面加载时间 (ms)",
    "animation_fps": "动画帧率",
    "memory_leak_detected": "内存泄漏检测",
    "ui_freeze_count": "UI卡顿次数",
    "user_action_count": "用户操作次数",
    "error_dialog_count": "错误弹窗次数"
}
```

---

## 三、高频采集方案

### 3.1 采集频率设计

| 监控层级 | 指标类型 | 采集频率 | 存储策略 |
|----------|----------|----------|----------|
| L1 基础设施 | 进程状态 | 5秒 | 保留7天 |
| L1 基础设施 | 端口状态 | 10秒 | 保留7天 |
| L2 系统资源 | CPU/内存 | 5秒 | 保留7天 |
| L2 系统资源 | GPU/磁盘 | 10秒 | 保留7天 |
| L3 应用服务 | API指标 | 实时 (每次请求) | 保留3天 |
| L3 应用服务 | 数据库 | 30秒 | 保留7天 |
| L4 业务功能 | 视频/音频 | 实时 (每帧) | 保留1天 |
| L4 业务功能 | 人脸合成 | 实时 (每次推理) | 保留1天 |
| L5 用户体验 | UI交互 | 实时 (每次操作) | 保留3天 |

### 3.2 高频采集实现

```python
# 高频采集器实现
class HighFrequencyCollector:
    def __init__(self):
        self.collectors = {
            "process": ProcessCollector(interval=5),
            "cpu": CPUCollector(interval=5),
            "memory": MemoryCollector(interval=5),
            "api": APICollector(realtime=True),
            "video": VideoCollector(realtime=True),
            "gui": GUICollector(realtime=True)
        }
        
    async def start(self):
        """启动所有高频采集器"""
        for name, collector in self.collectors.items():
            if collector.realtime:
                asyncio.create_task(collector.collect_realtime())
            else:
                asyncio.create_task(collector.collect_periodic())
```

---

## 四、监控面板增强

### 4.1 实时性能监控视图

```javascript
// 实时性能监控组件
class RealtimePerformanceMonitor {
    constructor() {
        this.charts = {
            cpu: new RealtimeChart('cpu-chart', {interval: 1000}),
            memory: new RealtimeChart('memory-chart', {interval: 1000}),
            fps: new RealtimeChart('fps-chart', {interval: 100}),
            api_latency: new RealtimeChart('api-latency-chart', {interval: 1000})
        };
    }
    
    updateMetrics(data) {
        // 更新CPU图表
        this.charts.cpu.addPoint({
            timestamp: data.timestamp,
            value: data.cpu.overall_percent,
            per_core: data.cpu.per_cpu_percent
        });
        
        // 更新内存图表
        this.charts.memory.addPoint({
            timestamp: data.timestamp,
            value: data.memory.percent,
            available: data.memory.available_gb
        });
        
        // 更新FPS图表
        this.charts.fps.addPoint({
            timestamp: data.timestamp,
            value: data.video.fps,
            target: data.video.target_fps,
            drop_rate: data.video.frame_drop_rate
        });
    }
}
```

### 4.2 告警规则增强

```python
# 高级告警规则
ADVANCED_ALERT_RULES = {
    # 性能劣化预警
    "performance_degradation": {
        "condition": "cpu_percent > 80% for 3 minutes",
        "severity": "warning",
        "action": "notify_admin"
    },
    
    # 内存泄漏检测
    "memory_leak": {
        "condition": "memory_percent increases > 5% per hour",
        "severity": "critical",
        "action": "restart_service"
    },
    
    # 视频处理异常
    "video_processing_anomaly": {
        "condition": "fps < 15 or frame_drop_rate > 10%",
        "severity": "warning",
        "action": "notify_user"
    },
    
    # 人脸合成质量下降
    "face_swap_quality_drop": {
        "condition": "quality_score < 70 for 1 minute",
        "severity": "warning",
        "action": "notify_user"
    },
    
    # API响应时间异常
    "api_latency_anomaly": {
        "condition": "p95_response_time > 500ms",
        "severity": "critical",
        "action": "scale_up"
    },
    
    # 用户体验下降
    "ux_degradation": {
        "condition": "ui_response_time > 200ms or ui_freeze_count > 5 per minute",
        "severity": "warning",
        "action": "optimize_ui"
    }
}
```

---

## 五、实施路线图

### 5.1 阶段划分

| 阶段 | 目标 | 预计工时 | 优先级 |
|------|------|----------|--------|
| **阶段1** | L1+L2层增强（基础设施+系统资源） | 2-3天 | 高 |
| **阶段2** | L3层增强（应用服务） | 2-3天 | 高 |
| **阶段3** | L4层增强（业务功能） | 2-3天 | 中 |
| **阶段4** | L5层增强（用户体验） | 1-2天 | 中 |
| **阶段5** | 监控面板优化 | 2-3天 | 中 |
| **阶段6** | 告警规则完善 | 1-2天 | 高 |

### 5.2 详细任务

#### 阶段1: 基础设施+系统资源监控增强
- [ ] 增强ProcessMonitor，添加详细进程指标
- [ ] 创建CPUDetailedMonitor，支持每核监控
- [ ] 创建MemoryDetailedMonitor，支持分段监控
- [ ] 创建GPUMonitor，支持GPU详细监控
- [ ] 实现5秒高频采集

#### 阶段2: 应用服务监控增强
- [ ] 创建APIDetailedMonitor，支持P50/P95/P99
- [ ] 创建DatabaseMonitor，监控连接池和慢查询
- [ ] 实现API实时采集
- [ ] 添加API性能趋势分析

#### 阶段3: 业务功能监控增强
- [ ] 创建VideoProcessingMonitor，实时监控FPS
- [ ] 创建FaceSwapMonitor，监控合成质量
- [ ] 创建AudioProcessingMonitor，监控音频延迟
- [ ] 实现业务指标实时采集

#### 阶段4: 用户体验监控增强
- [ ] 创建GUIExperienceMonitor，监控UI响应
- [ ] 实现用户操作追踪
- [ ] 添加用户体验评分

#### 阶段5: 监控面板优化
- [ ] 设计实时性能监控视图
- [ ] 实现多维度图表展示
- [ ] 添加指标关联分析
- [ ] 优化移动端适配

#### 阶段6: 告警规则完善
- [ ] 定义15+高级告警规则
- [ ] 实现智能告警抑制
- [ ] 添加告警趋势预测
- [ ] 实现自动恢复机制

---

## 六、预期收益

### 6.1 监控能力提升

| 能力 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| 监控粒度 | 服务级 (30-60秒) | 进程级+模块级 (5秒) | 10倍 |
| 指标维度 | 10+ | 100+ | 10倍 |
| 采集频率 | 30-60秒 | 5秒-实时 | 6-12倍 |
| 告警精度 | 事后告警 | 劣化预警+趋势预测 | 质的飞跃 |

### 6.2 运维效率提升

| 场景 | 当前 | 优化后 | 效率提升 |
|------|------|--------|----------|
| 故障发现时间 | 1-5分钟 | 5-30秒 | 10倍 |
| 故障定位时间 | 10-30分钟 | 1-3分钟 | 10倍 |
| 性能优化周期 | 1-2周 | 2-3天 | 5倍 |
| 用户投诉响应 | 小时级 | 分钟级 | 60倍 |

---

## 七、风险控制

### 7.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 高频采集增加系统负载 | 中 | 1. 动态调整采集频率<br>2. 采样而非全量采集<br>3. 异步采集避免阻塞 |
| 大量指标存储成本 | 中 | 1. 分级存储策略<br>2. 自动清理过期数据<br>3. 指标聚合压缩 |
| 复杂告警规则误报 | 中 | 1. 告警规则逐步调优<br>2. 智能告警抑制<br>3. 告警分级处理 |

### 7.2 实施建议

1. **渐进式实施**: 先实施L1+L2层，验证效果后再推进上层
2. **灰度发布**: 先在测试环境验证，再逐步推广到生产
3. **监控回滚**: 保留原有监控作为备份，新监控并行运行
4. **持续优化**: 根据实际运行情况持续调优采集频率和告警阈值

---

## 八、关联文档

- [监控整合方案](./3.监控整合方案.md)
- [统一监控面板架构方案](./统一监控面板架构方案.md)
- [监控颗粒度细化优化方案](./监控颗粒度细化优化方案.md)
- [YL-monitor README](../YL-monitor/README.md)

---

**建议下一步**: 根据实施路线图，开始阶段1开发（L1+L2层增强）

**优先级**: 高（建议立即实施）
