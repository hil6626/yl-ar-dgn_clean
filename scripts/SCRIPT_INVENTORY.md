# YL-AR-DGN 项目脚本清单

**创建日期:** 2026-02-11  
**版本:** 1.0.0

---

## 一、脚本目录结构

```
scripts/                    # 项目级通用脚本
├── ar-backend-verify.sh    # AR-backend验证
├── cleanup/                # 清理脚本
├── config/                 # 配置管理
├── deploy/                 # 部署脚本
├── docs/                   # 文档脚本
├── lib/                    # 公共库
├── monitor/                # 监控脚本
├── security/               # 安全脚本
├── utilities/              # 工具脚本
├── validation/             # 验证脚本
└── yl-ar-dgn.sh            # 统一入口

YL-monitor/scripts/         # YL-monitor专用脚本
├── alerts/                 # 告警处理
├── core/                   # 核心功能
├── maintenance/            # 维护任务
├── monitors/               # 监控任务
├── optimizers/             # 优化任务
└── utils/                  # 工具函数
```

---

## 二、脚本分类对照表

### 2.1 部署相关

| 功能 | scripts/ | YL-monitor/scripts/ | 建议 |
|------|----------|---------------------|------|
| 部署脚本 | `deploy/deploy.sh` | - | 保留在scripts/ |
| 回滚脚本 | `deploy/rollback.sh` | - | 保留在scripts/ |
| 部署通知 | `deploy/notify_deployment.py` | - | 保留在scripts/ |
| Docker构建 | - | `docker_build.sh` | 保留在YL-monitor/ |
| Docker启动 | - | `docker_start.sh` | 保留在YL-monitor/ |

### 2.2 监控相关

| 功能 | scripts/ | YL-monitor/scripts/ | 建议 |
|------|----------|---------------------|------|
| 健康检查 | `monitor/health_check.py` | `monitors/` (多个) | 合并到scripts/ |
| 资源监控 | `monitor/resource_monitor.py` | `monitors/system/` | 合并到scripts/ |
| API健康检查 | `monitor/api_health_check.py` | `monitors/service/` | 合并到scripts/ |
| AR节点监控 | - | `monitors/ar/` | 保留在YL-monitor/ |
| 日志监控 | `monitor/log_analyzer.py` | `monitors/service/10_log_anomaly_scan.py` | 合并到scripts/ |

### 2.3 清理相关

| 功能 | scripts/ | YL-monitor/scripts/ | 建议 |
|------|----------|---------------------|------|
| 缓存清理 | `cleanup/clean_cache.sh` | `optimizers/resource/19_cache_cleanup.py` | 合并到scripts/ |
| 项目清理 | `cleanup/cleanup_project.sh` | - | 保留在scripts/ |
| 临时文件清理 | - | `optimizers/resource/20_temp_file_cleanup.py` | 迁移到scripts/ |
| 日志轮转 | - | `optimizers/resource/21_log_rotate_compress.py` | 迁移到scripts/ |

### 2.4 验证相关

| 功能 | scripts/ | YL-monitor/scripts/ | 建议 |
|------|----------|---------------------|------|
| 入口验证 | `validation/validate_entrypoints.py` | - | 保留在scripts/ |
| 规则验证 | `validation/validate_rules_engine.py` | - | 保留在scripts/ |
| 后端验证 | `validation/validate_backend_services.py` | - | 保留在scripts/ |
| 部署验证 | `utilities/verify_start.sh` | `utils/verify/verify_deployment.py` | 合并到scripts/ |

### 2.5 安全相关

| 功能 | scripts/ | YL-monitor/scripts/ | 建议 |
|------|----------|---------------------|------|
| 安全扫描 | `security/security_scan.py` | `maintenance/health/54_security_policy_validate.py` | 合并到scripts/ |
| 漏洞检查 | `security/vulnerability_check.py` | - | 保留在scripts/ |

---

## 三、脚本整合策略

### 3.1 保留双目录，明确边界

**scripts/ (项目级通用脚本)**
- 负责整个项目的部署、验证、清理
- 包含跨组件的协调脚本
- 统一入口 `yl-ar-dgn.sh`

**YL-monitor/scripts/ (YL-monitor专用)**
- 负责YL-monitor平台自身的维护
- 包含特定监控任务和优化任务
- 编号脚本（01-54）保持不动

### 3.2 需要迁移的脚本

从 `YL-monitor/scripts/` 迁移到 `scripts/`：
- `utils/verify/verify_deployment.py` → `validation/`
- `utils/dev/test_api_functionality.py` → `utilities/`
- `utils/dev/start_and_verify.sh` → `utilities/`

### 3.3 需要合并的功能

| 功能 | 合并方案 |
|------|----------|
| 健康检查 | 以 `scripts/monitor/health_check.py` 为主，吸收YL-monitor的功能 |
| 资源监控 | 以 `scripts/monitor/resource_monitor.py` 为主，吸收YL-monitor的系统监控 |
| 日志分析 | 以 `scripts/monitor/log_analyzer.py` 为主，吸收YL-monitor的日志扫描 |

---

## 四、统一入口设计

### 4.1 命令结构

```bash
./scripts/yl-ar-dgn.sh <command> [options]

Commands:
  deploy     # 部署所有组件
  cleanup    # 清理临时文件和缓存
  monitor    # 启动监控
  validate   # 验证项目完整性
  status     # 显示所有组件状态
  logs       # 查看组件日志
  restart    # 重启组件
  help       # 显示帮助
```

### 4.2 配置管理

配置文件: `scripts/config/script_config.yaml`
- 定义组件配置（YL-monitor, AR-backend, User GUI）
- 定义端口、路径、依赖关系

### 4.3 日志格式

统一日志格式: `scripts/lib/logging.sh`
- 时间戳、级别、消息
- 支持JSON格式输出

---

## 五、执行计划

### 阶段4.1: 脚本审查 ✅
- [x] 列出 scripts/ 所有脚本
- [x] 列出 YL-monitor/scripts/ 所有脚本
- [x] 创建功能对照表

### 阶段4.2: 迁移脚本
- [ ] 迁移 verify_deployment.py
- [ ] 迁移 test_api_functionality.py
- [ ] 迁移 start_and_verify.sh

### 阶段4.3: 合并功能
- [ ] 合并健康检查脚本
- [ ] 合并资源监控脚本
- [ ] 合并日志分析脚本

### 阶段4.4: 创建统一入口
- [ ] 创建 yl-ar-dgn.sh
- [ ] 实现所有命令

### 阶段4.5-4.7: 统一标准
- [ ] 统一配置管理
- [ ] 统一日志格式
- [ ] 统一错误处理

---

## 六、脚本统计

| 目录 | 脚本数量 | 主要功能 |
|------|----------|----------|
| scripts/ | 39个 | 部署、验证、监控、清理、安全 |
| YL-monitor/scripts/ | 54+个 | 系统监控、维护、优化、告警 |

**总计:** 90+ 个脚本

---

## 七、关联文档

- [部署/6.脚本整合方案.md](../部署/6.脚本整合方案.md)
- [scripts/README.md](./README.md)
- [YL-monitor/scripts/README.md](../YL-monitor/scripts/README.md)
