# AR项目集成指南

**版本**: 1.0.0  
**创建时间**: 2026-02-08  
**适用范围**: AR项目监控扩展

---

## 一、概述

### 1.1 集成目标

本文档指导如何将AR（增强现实）项目接入YL-Monitor监控系统，实现：
- **实时监控**: 监控AR渲染节点状态
- **性能指标**: 采集渲染性能数据
- **任务管理**: 管理AR渲染任务
- **资源监控**: 监控存储和缓存使用

### 1.2 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    YL-Monitor 系统                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   仪表盘    │  │   告警系统   │  │   事件总线   │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │             │
│  ┌──────┴────────────────┴────────────────┴──────┐      │
│  │           AR监控扩展 (ARMonitorExtension)      │      │
│  │  ┌─────────────┐  ┌─────────────┐             │      │
│  │  │  项目注册   │  │  指标采集   │             │      │
│  │  └─────────────┘  └─────────────┘             │      │
│  └──────────────────┬────────────────────────────┘      │
└──────────────────────┼──────────────────────────────────┘
                       │
                       │ HTTP/WebSocket
                       │
┌──────────────────────┼──────────────────────────────────┐
│                      ▼                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │              AR项目系统                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐        │   │
│  │  │ 渲染节点 │  │ 协调节点 │  │ 存储节点 │        │   │
│  │  └─────────┘  └─────────┘  └─────────┘        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 二、快速接入

### 2.1 接入步骤

**步骤1: 注册AR项目**

```python
from app.ar.ar_monitor_extension import ar_monitor_extension

# 注册项目
await ar_monitor_extension.register_project("my_ar_project", {
    "name": "我的AR项目",
    "description": "AR演示应用",
    "render_nodes": 5,
    "scenes": ["main_scene", "loading_scene"]
})
```

**步骤2: 添加渲染节点**

```python
from app.ar.ar_monitor_extension import ARNodeConfig, ARNodeType

# 添加渲染节点
ar_monitor_extension.add_node("my_ar_project", ARNodeConfig(
    node_id="render_node_1",
    node_type=ARNodeType.RENDER,
    host="192.168.1.100",
    port=8080,
    gpu_memory=16384,  # 16GB显存
    cpu_cores=16,
    capabilities=["ray_tracing", "4k_rendering"]
))
```

**步骤3: 采集指标**

```python
# 采集项目指标
metrics = await ar_monitor_extension.collect_metrics("my_ar_project")

print(f"活跃节点: {metrics.active_nodes}")
print(f"平均FPS: {metrics.avg_fps}")
print(f"渲染任务: {metrics.active_tasks}")
```

**步骤4: 渲染仪表盘**

```python
# 获取仪表盘数据
dashboard = await ar_monitor_extension.render_dashboard("my_ar_project")

# 返回JSON数据，可直接用于前端渲染
```

### 2.2 接入时间

- **基础接入**: < 1小时
- **完整集成**: < 1天
- **自定义扩展**: 1-3天

---

## 三、接口说明

### 3.1 项目注册接口

```python
async def register_project(
    project_id: str,           # 项目唯一标识
    config: Dict[str, Any]    # 项目配置
) -> bool
```

**配置参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | str | 是 | 项目名称 |
| description | str | 否 | 项目描述 |
| render_nodes | int | 否 | 渲染节点数 |
| scenes | List[str] | 否 | 场景列表 |

**示例**:

```python
config = {
    "name": "AR演示项目",
    "description": "用于展示AR功能的演示项目",
    "render_nodes": 3,
    "scenes": ["scene1", "scene2", "scene3"]
}
```

### 3.2 节点管理接口

```python
def add_node(
    project_id: str,           # 项目标识
    node_config: ARNodeConfig  # 节点配置
) -> bool
```

**节点配置**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| node_id | str | 是 | 节点唯一标识 |
| node_type | ARNodeType | 是 | 节点类型 |
| host | str | 是 | 主机地址 |
| port | int | 是 | 服务端口 |
| gpu_memory | int | 否 | GPU显存（MB） |
| cpu_cores | int | 否 | CPU核心数 |
| capabilities | List[str] | 否 | 处理能力列表 |

**节点类型**:

- `RENDER`: 渲染节点
- `COORDINATOR`: 协调节点
- `STORAGE`: 存储节点
- `CACHE`: 缓存节点
- `PROXY`: 代理节点

### 3.3 指标采集接口

```python
async def collect_metrics(
    project_id: str           # 项目标识
) -> ARMetrics
```

**返回指标**:

| 指标 | 类型 | 说明 |
|------|------|------|
| active_nodes | int | 活跃节点数 |
| total_nodes | int | 总节点数 |
| node_cpu_usage | float | 平均CPU使用率 |
| node_memory_usage | float | 平均内存使用率 |
| node_gpu_usage | float | 平均GPU使用率 |
| active_tasks | int | 活跃任务数 |
| queued_tasks | int | 排队任务数 |
| avg_render_time_ms | float | 平均渲染时间（毫秒） |
| avg_fps | float | 平均帧率 |
| storage_usage_gb | float | 存储使用量（GB） |
| cache_hit_rate | float | 缓存命中率 |

### 3.4 仪表盘接口

```python
async def render_dashboard(
    project_id: str           # 项目标识
) -> Dict[str, Any]
```

**返回结构**:

```json
{
    "project": {
        "id": "project_id",
        "name": "项目名称",
        "status": "active",
        "scene_count": 3
    },
    "nodes": {
        "total": 5,
        "active": 4,
        "by_type": {"render": 3, "coordinator": 1, "storage": 1},
        "list": [...]
    },
    "metrics": {
        "current": {...},
        "history": [...]
    },
    "tasks": {
        "active": 5,
        "queued": 10,
        "completed": 100,
        "failed": 2
    }
}
```

---

## 四、扩展开发

### 4.1 自定义指标采集

```python
from app.ar.ar_monitor_extension import ar_monitor_extension

# 注册自定义指标采集钩子
async def custom_metrics_collector(project_id: str):
    # 自定义指标采集逻辑
    return {
        "custom_metric_1": 100,
        "custom_metric_2": 200
    }

# 注册扩展钩子
ar_monitor_extension.register_extension_hook(
    "metrics_collected", 
    custom_metrics_collector
)
```

### 4.2 自定义事件处理

```python
# 注册项目注册事件钩子
async def on_project_registered(project):
    print(f"项目已注册: {project.name}")
    # 执行自定义初始化逻辑

ar_monitor_extension.register_extension_hook(
    "project_registered",
    on_project_registered
)
```

### 4.3 支持的事件类型

| 事件 | 触发时机 | 参数 |
|------|----------|------|
| project_registered | 项目注册完成 | ARProject |
| node_added | 节点添加完成 | ARNodeConfig |
| metrics_collected | 指标采集完成 | ARMetrics |
| task_created | 任务创建 | ARTask |
| task_completed | 任务完成 | ARTask |

---

## 五、配置示例

### 5.1 基础配置

```python
# config/ar_project.py

AR_PROJECTS = {
    "ar_demo": {
        "name": "AR演示项目",
        "description": "基础AR功能演示",
        "render_nodes": 3,
        "scenes": ["main", "loading", "result"]
    }
}

AR_NODES = [
    {
        "node_id": "render_1",
        "project_id": "ar_demo",
        "node_type": "render",
        "host": "192.168.1.101",
        "port": 8080,
        "gpu_memory": 8192,
        "cpu_cores": 8
    },
    {
        "node_id": "render_2",
        "project_id": "ar_demo",
        "node_type": "render",
        "host": "192.168.1.102",
        "port": 8080,
        "gpu_memory": 16384,
        "cpu_cores": 16
    }
]
```

### 5.2 高级配置

```python
# 自动注册所有项目
async def auto_register_projects():
    for project_id, config in AR_PROJECTS.items():
        await ar_monitor_extension.register_project(project_id, config)
    
    for node in AR_NODES:
        project_id = node.pop("project_id")
        node_config = ARNodeConfig(**node)
        ar_monitor_extension.add_node(project_id, node_config)

# 启动时执行
await auto_register_projects()
```

---

## 六、前端集成

### 6.1 WebSocket实时推送

```javascript
// 连接AR监控WebSocket
const ws = new WebSocket('ws://0.0.0.0:8000/ws/ar');

// 订阅项目
ws.send(JSON.stringify({
    action: 'subscribe',
    project_id: 'ar_demo'
}));

// 接收实时数据
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('AR指标:', data.metrics);
    updateDashboard(data);
};
```

### 6.2 仪表盘组件

```javascript
// AR仪表盘组件
class ARDashboard {
    constructor(projectId) {
        this.projectId = projectId;
        this.metrics = {};
    }
    
    async load() {
        const response = await fetch(`/api/ar/dashboard/${this.projectId}`);
        this.data = await response.json();
        this.render();
    }
    
    render() {
        // 渲染项目信息
        this.renderProjectInfo();
        // 渲染节点状态
        this.renderNodeStatus();
        // 渲染性能图表
        this.renderPerformanceCharts();
    }
}
```

---

## 七、最佳实践

### 7.1 性能优化

- **批量采集**: 合并多个指标采集请求
- **缓存策略**: 缓存不频繁变化的指标
- **增量更新**: 只推送变化的指标数据
- **采样率**: 高频指标降低采样率

### 7.2 可靠性保障

- **重试机制**: 指标采集失败自动重试
- **降级策略**: 服务不可用时提供模拟数据
- **健康检查**: 定期检查AR节点健康状态
- **告警配置**: 关键指标异常时触发告警

### 7.3 安全建议

- **认证授权**: 所有API请求需要认证
- **数据加密**: 敏感指标数据加密传输
- **访问控制**: 基于角色的仪表盘访问控制
- **审计日志**: 记录所有管理操作

---

## 八、故障排查

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 项目注册失败 | 项目ID已存在 | 使用唯一项目ID |
| 节点添加失败 | 项目不存在 | 先注册项目 |
| 指标采集失败 | 节点不可达 | 检查网络连接 |
| 仪表盘无数据 | 未采集指标 | 先执行指标采集 |

### 8.2 调试方法

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查项目状态
projects = ar_monitor_extension.get_project_list()
print(f"已注册项目: {projects}")

# 检查节点状态
project = ar_monitor_extension._projects.get("my_project")
print(f"项目节点: {project.nodes}")
```

---

## 九、附录

### 9.1 参考文档

- [AR监控扩展API文档](../app/ar/ar_monitor_extension.py)
- [AR数据模型](../app/models/ar.py)
- [WebSocket接口](../app/ws/ar_ws.py)

### 9.2 更新记录

| 版本 | 时间 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-02-08 | 初始版本 |

---

**维护者**: AI Assistant  
**技术支持**: AI Assistant
