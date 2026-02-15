# 优化类脚本 (Optimize)

> 性能优化、清理与资源调度

## 脚本列表

| ID | 名称 | 文件 | 描述 |
|----|------|------|------|
| 16 | 资源趋势分析 | `16_resource_trend_analysis.py` | 分析CPU/内存/磁盘使用趋势 |
| 17 | 磁盘垃圾清理 | `17_disk_junk_cleanup.py` | 清理系统临时文件 |
| 18 | 重复文件去重 | `18_duplicate_file_dedup.py` | 检测并清理重复文件 |
| 19 | 缓存清理 | `19_cache_cleanup.py` | 清理系统/浏览器/应用缓存 |
| 20 | 临时文件清理 | `20_temp_file_cleanup.py` | 清理临时目录文件 |
| 21 | 日志轮转压缩 | `21_log_rotate_compress.py` | 轮转并压缩历史日志 |
| 23 | 数据库冗余清理 | `23_db_redundant_data_cleanup.py` | 清理数据库冗余数据 |
| 24 | 缓存数据库维护 | `24_cache_db_maintenance.py` | 维护缓存数据库性能 |
| 27 | 应用临时数据清理 | `27_app_temp_data_cleanup.py` | 清理应用产生的临时数据 |
| 28 | 浏览器历史管理 | `28_browser_history_management.py` | 管理浏览器历史记录 |
| 29 | 服务缓存刷新 | `29_service_cache_refresh.py` | 刷新各服务的缓存数据 |
| 31 | 清理优化组合任务 | `31_combo_cleanup_optimize.py` | 组合多种清理优化任务 |
| 32 | 智能维护脚本 | `32_smart_maintenance.py` | 智能分析并执行维护任务 |
| 34 | 进程优先级调整 | `34_process_priority_auto_adjust.py` | 自动调整进程优先级 |
| 35 | 内存泄漏检测告警 | `35_memory_leak_detect_alert.py` | 检测内存泄漏并发送告警 |
| 37 | CPU核心负载均衡 | `37_cpu_core_load_balance.py` | 均衡CPU核心负载 |
| 43 | 流量异常识别 | `43_traffic_anomaly_detect.py` | 智能识别网络流量异常 |
| 45 | 负载均衡调优 | `45_load_balancer_tune.py` | 调优负载均衡配置 |
| 46 | 任务依赖自动修复 | `46_task_dependency_auto_fix.py` | 自动修复DAG任务依赖问题 |
| 47 | AR渲染节点调度 | `47_ar_render_node_schedule.py` | 调度AR渲染节点负载 |
| 48 | 脚本异常回滚 | `48_script_failure_auto_rollback.py` | 脚本执行异常时自动回滚 |
| 49 | 脚本优先级调度 | `49_script_priority_scheduler.py` | 智能调度脚本执行优先级 |
| 50 | 性能趋势预测 | `50_performance_trend_predict.py` | 预测系统性能趋势 |
| 51 | 智能清理策略生成 | `51_smart_cleanup_policy_generate.py` | 生成智能资源清理策略 |

## 使用方式

```bash
# 直接运行脚本（dry-run模式）
python3 scripts/optimize/17_disk_junk_cleanup.py --pretty

# 执行真实清理（需要 --apply 参数）
python3 scripts/optimize/17_disk_junk_cleanup.py --apply --pretty

# 通过API调用
POST /api/scripts/run
{"script_id": "17"}
```

## 安全模式

大部分清理类脚本默认使用 **dry-run** 模式，仅显示将执行的操作而不实际执行。

如需执行真实清理，需要：
1. 命令行添加 `--apply` 参数
2. 或通过前端界面确认执行

## 输出格式

所有脚本返回标准 JSON 格式：

```json
{
  "id": "17",
  "name": "磁盘垃圾清理",
  "type": "optimize",
  "status": "ok",
  "metrics": {
    "files_scanned": 1250,
    "junk_files_found": 45,
    "space_recoverable_mb": 128.5
  },
  "message": "扫描完成，可清理45个文件"
}
```

## 返回顶部

[返回 scripts 目录](../README.md)

