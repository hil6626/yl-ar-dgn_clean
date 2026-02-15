# 维护类脚本 (Maintenance)

> 系统巡检、备份、配置管理与运维工具

## 脚本列表

| ID | 名称 | 文件 | 描述 |
|----|------|------|------|
| 11 | 脚本执行状态监控 | `11_script_execution_status_monitor.py` | 监控所有脚本的历史执行状态 |
| 12 | DAG节点状态监控 | `12_dag_node_status_monitor.py` | 监控DAG流水线各节点执行状态 |
| 15 | 定时巡检报告生成 | `15_scheduled_inspection_report.py` | 生成系统健康巡检报告 |
| 22 | 系统更新补丁检查 | `22_system_update_patch_check.py` | 检查系统和软件更新 |
| 25 | 文件备份归档 | `25_file_backup_archive.py` | 备份重要文件和配置 |
| 26 | 日志异常归档 | `26_log_anomaly_archive.py` | 归档异常日志便于分析 |
| 30 | 应用配置检查修复 | `30_app_config_check_repair.py` | 检测并修复应用配置问题 |
| 33 | 自动归档回滚 | `33_auto_archive_rollback.py` | 自动化归档与回滚机制 |
| 36 | 系统启动加速优化 | `36_boot_acceleration_optimize.py` | 优化系统启动速度 |
| 38 | 数据库索引优化 | `38_db_index_optimize.py` | 优化数据库索引提升性能 |
| 39 | 日志智能归类标签 | `39_log_classify_tagging.py` | 智能归类日志并添加标签 |
| 40 | 历史数据压缩归档 | `40_history_data_compress_archive.py` | 压缩归档历史数据 |
| 41 | 自动数据摘要 | `41_auto_data_summary.py` | 自动生成数据统计摘要 |
| 42 | 服务依赖检测 | `42_service_dependency_detect.py` | 检测服务间依赖关系 |
| 44 | API负载测试 | `44_api_load_test.py` | 对API进行压力测试 |
| 52 | 自动配置异常修复 | `52_auto_config_anomaly_fix.py` | 自动检测并修复配置异常 |
| 53 | 多环境脚本同步 | `53_multi_env_script_sync.py` | 同步不同环境的脚本配置 |
| 54 | 安全策略校验 | `54_security_policy_validate.py` | 校验系统安全策略合规性 |

## 使用方式

```bash
# 直接运行脚本
python3 scripts/maintenance/15_scheduled_inspection_report.py --pretty

# 通过API调用
POST /api/scripts/run
{"script_id": "15"}
```

## 输出格式

所有脚本返回标准 JSON 格式：

```json
{
  "id": "15",
  "name": "定时巡检报告生成",
  "type": "maintenance",
  "status": "ok",
  "metrics": {
    "checks_performed": 12,
    "issues_found": 2,
    "report_path": "/app/logs/inspection_20260205.json"
  },
  "message": "巡检完成，发现2个问题"
}
```

## 返回顶部

[返回 scripts 目录](../README.md)

