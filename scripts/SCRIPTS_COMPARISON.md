# Scripts Comparison Report
# 脚本目录对比报告

**版本:** 1.0.0  
**生成日期:** 2026-02-05  
**对比目录:** 
- `/workspaces/yl-ar-dgn/scripts/` (项目根目录脚本)
- `/workspaces/yl-ar-dgn/YL-monitor/scripts/` (YL-monitor模块脚本)

---

## 📊 目录概览

| 属性 | scripts/ (根目录) | YL-monitor/scripts/ |
|------|-------------------|---------------------|
| **文件数** | 39个脚本 | 59个脚本 |
| **目录结构** | 按功能分类 | 按序号排列 |
| **主要用途** | 部署、清理、工具 | 监控、维护、优化 |
| **运行环境** | 项目全局 | YL-monitor模块专用 |

---

## 📁 目录结构对比

### 根目录 scripts/

```
scripts/
├── deploy/              # 部署脚本 (3个)
├── cleanup/             # 清理脚本 (5个)
├── docs/                # 文档脚本 (2个)
├── utilities/           # 工具脚本 (8个)
├── monitor/             # 监控脚本 (13个)
├── security/            # 安全脚本 (2个)
├── validation/          # 验证脚本 (5个)
├── README.md
└── reorganize_scripts.sh
```

### YL-monitor/scripts/

```
YL-monitor/scripts/
├── 01-54_*.py          # 54个功能脚本 (按序号)
├── _common.py          # 公共模块
├── docker_build.sh     # Docker构建
├── docker_start.sh     # Docker启动
├── docker_stop.sh      # Docker停止
├── verify_api.sh       # API验证
├── verify_start.sh     # 启动验证
└── README.md
```

---

## 🔍 功能分类对比

### 1. 部署相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| `deploy/deploy.sh` | `docker_build.sh` |
| `deploy/rollback.sh` | `docker_start.sh` |
| `deploy/notify_deployment.py` | `docker_stop.sh` |

**对比说明:**
- 根目录: 完整的部署流程控制
- YL-monitor: 仅Docker容器管理

---

### 2. 清理相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| `cleanup/cleanup_project.sh` | `17_disk_junk_cleanup.py` |
| `cleanup/cleanup_tasks_docs.sh` | `18_duplicate_file_dedup.py` |
| `cleanup/final_cleanup.sh` | `19_cache_cleanup.py` |
| `cleanup/refactor_directories.sh` | `20_temp_file_cleanup.py` |
| `cleanup/clean_cache.sh` | `21_log_rotate_compress.py` |
| | `23_db_redundant_data_cleanup.py` |
| | `24_cache_db_maintenance.py` |
| | `27_app_temp_data_cleanup.py` |
| | `28_browser_history_management.py` |
| | `31_combo_cleanup_optimize.py` |

**对比说明:**
- 根目录: 项目级清理、文档归档
- YL-monitor: 系统级清理、专项清理

---

### 3. 监控相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| `monitor/monitor.py` | `01_cpu_usage_monitor.py` |
| `monitor/health_check.py` | `02_memory_usage_monitor.py` |
| `monitor/log_analyzer.py` | `03_disk_space_io_monitor.py` |
| `monitor/resource_monitor.py` | `04_system_load_process_monitor.py` |
| `monitor/api_health_check.py` | `05_port_service_availability_check.py` |
| `monitor/auto_log_monitor.py` | `06_network_latency_bandwidth_monitor.py` |
| `monitor/dependency_check.py` | `07_external_api_health_check.py` |
| `monitor/deployment_progress.py` | `08_web_app_availability_check.py` |
| `monitor/env_check.py` | `09_database_connection_query_monitor.py` |
| `monitor/monitor_app.py` | `10_log_anomaly_scan.py` |
| `monitor/monitor_router.py` | `13_ar_node_resource_monitor.py` |
| `monitor/monitor_server.py` | `42_service_dependency_detect.py` |
| `monitor/service_repair.py` | `43_traffic_anomaly_detect.py` |
| | `44_api_load_test.py` |

**对比说明:**
- 根目录: 综合监控框架
- YL-monitor: 专项监控脚本（更细粒度）

---

### 4. 验证相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| `validation/validate_backend_services.py` | `verify_api.sh` |
| `validation/validate_frontend_architecture.py` | `verify_start.sh` |
| `validation/check_scripts_integrity.py` | |
| `validation/validate_entrypoints.py` | |
| `validation/validate_rules_engine.py` | |

---

### 5. 工具相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| `utilities/build_gui_components.py` | `_common.py` (公共模块) |
| `utilities/refactor_rules.py` | |
| `utilities/check_dependencies.py` | |
| `utilities/env.sh` | |
| `utilities/fix_paths_to_local.sh` | |
| `utilities/scripts_manager.py` | |
| `utilities/scripts_manager_enhanced.py` | |
| `utilities/verify_start.sh` | |

---

### 6. 优化相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| (无) | `16_resource_trend_analysis.py` |
| | `34_process_priority_auto_adjust.py` |
| | `35_memory_leak_detect_alert.py` |
| | `36_boot_acceleration_optimize.py` |
| | `37_cpu_core_load_balance.py` |
| | `38_db_index_optimize.py` |
| | `45_load_balancer_tune.py` |
| | `46_task_dependency_auto_fix.py` |
| | `47_ar_render_node_schedule.py` |
| | `50_performance_trend_predict.py` |
| | `51_smart_cleanup_policy_generate.py` |

---

### 7. 维护相关

| 根目录 scripts/ | YL-monitor/scripts/ |
|-----------------|---------------------|
| `docs/docs_generator.py` | `15_scheduled_inspection_report.py` |
| `docs/verify_yl-monitor_docs.sh` | `22_system_update_patch_check.py` |
| | `25_file_backup_archive.py` |
| | `26_log_anomaly_archive.py` |
| | `29_service_cache_refresh.py` |
| | `30_app_config_check_repair.py` |
| | `32_smart_maintenance.py` |
| | `33_auto_archive_rollback.py` |
| | `39_log_classify_tagging.py` |
| | `40_history_data_compress_archive.py` |
| | `41_auto_data_summary.py` |
| | `48_script_failure_auto_rollback.py` |
| | `49_script_priority_scheduler.py` |
| | `52_auto_config_anomaly_fix.py` |
| | `53_multi_env_script_sync.py` |
| | `54_security_policy_validate.py` |

---

## 📋 功能重叠分析

### 存在重叠的功能

| 功能 | 根目录脚本 | YL-monitor脚本 | 处理建议 |
|------|-----------|----------------|----------|
| 缓存清理 | `clean_cache.sh` | `19_cache_cleanup.py` | 保留各自实现 |
| 临时文件清理 | `cleanup_project.sh` | `20_temp_file_cleanup.py` | 保留各自实现 |
| 日志轮转 | 无 | `21_log_rotate_compress.py` | YL-monitor专用 |
| 数据库清理 | 无 | `23_db_redundant_data_cleanup.py` | YL-monitor专用 |
| 服务验证 | `validate_backend_services.py` | `verify_api.sh` | 保留各自实现 |
| 启动验证 | `verify_start.sh` | `verify_start.sh` | **冲突!** 同名文件 |

### 冲突解决

| 冲突项 | 位置 | 解决方案 |
|--------|------|----------|
| `verify_start.sh` | 根目录 & YL-monitor | 根目录: `utilities/verify_start.sh`<br>YL-monitor: `YL-monitor/scripts/verify_start.sh` |

---

## 🎯 脚本调用关系

### 根目录脚本调用YL-monitor脚本

```bash
# 根目录脚本可以调用YL-monitor脚本
./scripts/cleanup/cleanup_project.sh
  → 可能调用: YL-monitor/scripts/17_disk_junk_cleanup.py
  → 可能调用: YL-monitor/scripts/20_temp_file_cleanup.py

./scripts/monitor/monitor.py
  → 可能调用: YL-monitor/scripts/01-10_*.py
```

### YL-monitor脚本依赖

```python
# YL-monitor脚本使用_common.py
from _common import output_json, get_metrics
```

---

## 📈 建议整合方案

### 1. 统一监控接口
- 根目录 `monitor/monitor.py` 作为统一入口
- YL-monitor脚本作为具体实现

### 2. 共享公共模块
- 将 `_common.py` 移动到项目根目录
- 供所有脚本使用

### 3. 避免重复开发
- 清理功能: 根目录负责项目级，YL-monitor负责系统级
- 监控功能: 根目录做聚合，YL-monitor做采集

---

## 📊 统计总结

| 分类 | 根目录 | YL-monitor | 重叠 |
|------|--------|------------|------|
| 部署 | 3 | 3 | 0 |
| 清理 | 5 | 10 | 0 |
| 监控 | 13 | 14 | 5 |
| 验证 | 5 | 2 | 1 |
| 工具 | 8 | 1 | 0 |
| 优化 | 0 | 11 | 0 |
| 维护 | 2 | 16 | 0 |
| **总计** | **36** | **57** | **6** |

---

## 🔗 关联文档

| 文档 | 描述 |
|------|------|
| [scripts/README.md](../scripts/README.md) | 根目录脚本说明 |
| [YL-monitor/scripts/README.md](./README.md) | YL-monitor脚本说明 |
| [docs/DEPLOYMENT_SUMMARY.md](../docs/DEPLOYMENT_SUMMARY.md) | 部署总结 |

---

**版本:** 1.0.0  
**最后更新:** 2026-02-05
