# YL-AR-DGN 项目脚本清单 V2

**版本:** 2.0.0  
**创建日期:** 2026-02-16  
**状态:** 阶段4执行中

---

## 📊 脚本统计

| 目录 | 脚本数量 | 类别 |
|------|----------|------|
| scripts/ (根目录) | 11 | 核心脚本 |
| scripts/cleanup/ | 5 | 清理脚本 |
| scripts/deploy/ | 3 | 部署脚本 |
| scripts/docs/ | 2 | 文档脚本 |
| scripts/lib/ | 2 | 库函数 |
| scripts/monitor/ | 12 | 监控脚本 |
| scripts/security/ | 2 | 安全脚本 |
| scripts/utilities/ | 7 | 工具脚本 |
| scripts/validation/ | 5 | 验证脚本 |
| **scripts/ 总计** | **49** | - |
| **YL-monitor/scripts/ 总计** | **80+** | - |
| **重复/可合并** | **约15** | - |

---

## 📁 scripts/ 目录详细清单

### 核心脚本 (根目录)

| 脚本 | 功能描述 | 状态 | 建议 |
|------|----------|------|------|
| yl-ar-dgn.sh | 统一入口脚本 | ✅ 核心 | 保留并增强 |
| verify-monitoring.sh | 监控验证工具 | ✅ 核心 | 保留 |
| test-rules-engine.sh | 规则引擎测试 | ✅ 核心 | 保留 |
| verify_all.sh | 全面验证v1 | 🟡 审查 | 与v2合并 |
| verify_all_v2.sh | 全面验证v2 | 🟡 审查 | 合并为统一验证 |
| verify_infrastructure.sh | 基础设施验证 | 🟡 审查 | 整合到统一验证 |
| verify_phase7_deployment.sh | 阶段7验证 | 🟡 审查 | 整合到统一验证 |
| ar-backend-verify.sh | AR后端验证 | 🟡 审查 | 整合到统一验证 |
| cleanup-services-structure.sh | 服务结构清理 | 🟡 审查 | 整合到cleanup/ |
| reorganize_scripts.sh | 脚本重组 | 🟡 审查 | 执行后删除 |
| restructure-services.sh | 服务重构 | 🟡 审查 | 执行后删除 |

### cleanup/ 目录

| 脚本 | 功能描述 | 状态 | 建议 |
|------|----------|------|------|
| clean_cache.sh | 清理缓存 | ✅ 保留 | 保留 |
| cleanup_project.sh | 项目清理 | ✅ 保留 | 保留 |
| cleanup_tasks_docs.sh | 任务文档清理 | ✅ 保留 | 保留 |
| final_cleanup.sh | 最终清理 | ✅ 保留 | 保留 |
| refactor_directories.sh | 目录重构 | 🟡 审查 | 执行后删除 |

### deploy/ 目录

| 脚本 | 功能描述 | 状态 | 建议 |
|------|----------|------|------|
| deploy.sh | 部署脚本 | ✅ 保留 | 保留 |
| notify_deployment.py | 部署通知 | ✅ 保留 | 保留 |
| rollback.sh | 回滚脚本 | ✅ 保留 | 保留 |

### monitor/ 目录

| 脚本 | 功能描述 | 状态 | 建议 |
|------|----------|------|------|
| api_health_check.py | API健康检查 | ✅ 保留 | 保留 |
| auto_log_monitor.py | 日志监控 | ✅ 保留 | 保留 |
| dependency_check.py | 依赖检查 | ✅ 保留 | 保留 |
| deployment_progress.py | 部署进度 | ✅ 保留 | 保留 |
| env_check.py | 环境检查 | ✅ 保留 | 保留 |
| health_check.py | 健康检查 | ✅ 保留 | 保留 |
| log_analyzer.py | 日志分析 | ✅ 保留 | 保留 |
| monitor_app.py | 应用监控 | ✅ 保留 | 保留 |
| monitor.py | 监控主程序 | ✅ 保留 | 保留 |
| monitor_router.py | 监控路由 | ✅ 保留 | 保留 |
| resource_monitor.py | 资源监控 | ✅ 保留 | 保留 |
| service_repair.py | 服务修复 | ✅ 保留 | 保留 |

---

## 📁 YL-monitor/scripts/ 目录详细清单

### 核心脚本 (根目录)

| 脚本 | 功能描述 | 类别 | 建议 |
|------|----------|------|------|
| backup.sh | 备份脚本 | 维护 | 🔀 迁移到 scripts/maintenance/ |
| docker_build.sh | Docker构建 | 部署 | 🔀 迁移到 scripts/deploy/ |
| docker_start.sh | Docker启动 | 部署 | 🔀 迁移到 scripts/deploy/ |
| docker_stop.sh | Docker停止 | 部署 | 🔀 迁移到 scripts/deploy/ |
| run_all_monitors.sh | 运行所有监控 | 监控 | 🔀 功能合并到 verify-monitoring.sh |
| setup_vscode_testing.sh | VSCode测试配置 | 开发 | 🔀 迁移到 scripts/utilities/ |
| test_alert_system.py | 告警系统测试 | 测试 | 🔀 迁移到 scripts/monitor/ |
| simple_alert_test.py | 简单告警测试 | 测试 | 🔀 迁移到 scripts/monitor/ |
| optimize_project_structure.py | 项目结构优化 | 维护 | 🔀 迁移到 scripts/utilities/ |
| cleanup_duplicate_files.py | 重复文件清理 | 清理 | 🔀 迁移到 scripts/cleanup/ |
| cleanup_old_files.sh | 旧文件清理 | 清理 | 🔀 迁移到 scripts/cleanup/ |

### monitors/ 目录 (系统监控脚本)

| 脚本 | 功能描述 | 类别 | 建议 |
|------|----------|------|------|
| system/01_cpu_usage_monitor.py | CPU监控 | 系统 | 🔀 整合到 resource_monitor.py |
| system/02_memory_usage_monitor.py | 内存监控 | 系统 | 🔀 整合到 resource_monitor.py |
| system/03_disk_space_io_monitor.py | 磁盘监控 | 系统 | 🔀 整合到 resource_monitor.py |
| system/04_system_load_process_monitor.py | 负载监控 | 系统 | 🔀 整合到 resource_monitor.py |
| service/05_port_service_availability_check.py | 端口检查 | 服务 | 🔀 整合到 health_check.py |
| service/06_network_latency_bandwidth_monitor.py | 网络监控 | 服务 | 🔀 整合到 health_check.py |
| service/07_external_api_health_check.py | API健康检查 | 服务 | 🔀 整合到 api_health_check.py |
| service/08_web_app_availability_check.py | Web应用检查 | 服务 | 🔀 整合到 health_check.py |
| service/09_database_connection_query_monitor.py | 数据库监控 | 服务 | 🔀 保留独立 |
| service/10_log_anomaly_scan.py | 日志异常扫描 | 服务 | 🔀 整合到 log_analyzer.py |
| ar/13_ar_node_resource_monitor.py | AR节点监控 | AR | 🔀 整合到 monitor_app.py |

### maintenance/ 目录 (维护脚本)

| 脚本 | 功能描述 | 建议 |
|------|----------|------|
| health/11_script_execution_status_monitor.py | 脚本执行监控 | 🔀 保留在 YL-monitor |
| health/12_dag_node_status_monitor.py | DAG节点监控 | 🔀 保留在 YL-monitor |
| health/15_scheduled_inspection_report.py | 定时检查报告 | 🔀 保留在 YL-monitor |
| health/22_system_update_patch_check.py | 系统更新检查 | 🔀 保留在 YL-monitor |
| ... (共15个健康检查脚本) | 各种健康检查 | 🔀 保留在 YL-monitor |

### optimizers/ 目录 (优化脚本)

| 脚本 | 功能描述 | 建议 |
|------|----------|------|
| resource/16_resource_trend_analysis.py | 资源趋势分析 | 🔀 保留在 YL-monitor |
| resource/17_disk_junk_cleanup.py | 磁盘清理 | 🔀 保留在 YL-monitor |
| ... (共13个资源优化脚本) | 各种优化 | 🔀 保留在 YL-monitor |
| service/34_process_priority_auto_adjust.py | 进程优先级调整 | 🔀 保留在 YL-monitor |
| ... (共10个服务优化脚本) | 各种优化 | 🔀 保留在 YL-monitor |

---

## 🔀 整合计划

### 需要迁移的脚本 (从 YL-monitor/scripts/ 到 scripts/)

| 源文件 | 目标位置 | 操作 |
|--------|----------|------|
| backup.sh | scripts/maintenance/backup.sh | 迁移 |
| docker_build.sh | scripts/deploy/docker_build.sh | 迁移 |
| docker_start.sh | scripts/deploy/docker_start.sh | 迁移 |
| docker_stop.sh | scripts/deploy/docker_stop.sh | 迁移 |
| setup_vscode_testing.sh | scripts/utilities/setup_vscode.sh | 迁移 |
| test_alert_system.py | scripts/monitor/alert_system_test.py | 迁移 |
| simple_alert_test.py | scripts/monitor/alert_simple_test.py | 迁移 |
| optimize_project_structure.py | scripts/utilities/optimize_structure.py | 迁移 |
| cleanup_duplicate_files.py | scripts/cleanup/duplicate_files.py | 迁移 |
| cleanup_old_files.sh | scripts/cleanup/old_files.sh | 迁移 |

### 需要合并的脚本

| 功能 | 现有脚本 | 合并方案 |
|------|----------|----------|
| 全面验证 | verify_all.sh, verify_all_v2.sh, verify_infrastructure.sh, verify_phase7_deployment.sh, ar-backend-verify.sh | 合并为 scripts/verify_all.sh |
| 服务结构清理 | cleanup-services-structure.sh, reorganize_scripts.sh, restructure-services.sh, refactor_directories.sh | 合并为 scripts/cleanup/service_structure.sh |
| 监控运行 | run_all_monitors.sh | 功能合并到 verify-monitoring.sh |

### 需要删除的脚本 (执行整合后)

- reorganize_scripts.sh
- restructure-services.sh
- refactor_directories.sh
- verify_all_v2.sh (合并后)
- verify_infrastructure.sh (合并后)
- verify_phase7_deployment.sh (合并后)
- ar-backend-verify.sh (合并后)

---

## 📋 执行检查清单

- [ ] 创建 scripts/maintenance/ 目录
- [ ] 迁移备份脚本
- [ ] 迁移Docker脚本
- [ ] 合并验证脚本
- [ ] 合并清理脚本
- [ ] 更新 yl-ar-dgn.sh 添加新命令
- [ ] 创建统一配置
- [ ] 统一日志格式
- [ ] 测试所有脚本
- [ ] 更新文档

---

**下一步:** 开始执行脚本迁移和合并
