# 监控类脚本 (Monitor)

> 系统与服务实时监控脚本

## 脚本列表

| ID | 名称 | 文件 | 描述 |
|----|------|------|------|
| 01 | CPU使用率监控 | `01_cpu_usage_monitor.py` | 实时监控CPU使用率 |
| 02 | 内存使用率监控 | `02_memory_usage_monitor.py` | 监控系统内存使用情况 |
| 03 | 磁盘空间与I/O监控 | `03_disk_space_io_monitor.py` | 监控磁盘空间和读写IOPS |
| 04 | 系统负载与进程监控 | `04_system_load_process_monitor.py` | 监控load average和进程状态 |
| 05 | 端口服务可用性检查 | `05_port_service_availability_check.py` | 检查指定端口和服务是否可达 |
| 06 | 网络延迟与带宽监控 | `06_network_latency_bandwidth_monitor.py` | 测量网络延迟和带宽 |
| 07 | 外部API健康检查 | `07_external_api_health_check.py` | 检查外部API接口健康状态 |
| 08 | Web应用可用性检测 | `08_web_app_availability_check.py` | 检测Web应用页面可用性 |
| 09 | 数据库连接与查询监控 | `09_database_connection_query_monitor.py` | 监控数据库连接和查询性能 |
| 10 | 日志异常扫描 | `10_log_anomaly_scan.py` | 扫描日志文件检测异常模式 |
| 13 | AR节点资源监控 | `13_ar_node_resource_monitor.py` | 监控AR渲染节点资源 |

## 使用方式

```bash
# 直接运行脚本
python3 scripts/monitor/01_cpu_usage_monitor.py --pretty

# 通过API调用
POST /api/scripts/run
{"script_id": "01"}
```

## 输出格式

所有脚本返回标准 JSON 格式：

```json
{
  "id": "01",
  "name": "CPU使用率监控",
  "type": "monitor",
  "status": "ok",
  "metrics": {
    "cpu_percent": 45.2,
    "load_average": [1.2, 1.5, 1.8]
  },
  "message": "CPU使用率正常"
}
```

## 返回顶部

[返回 scripts 目录](../README.md)

