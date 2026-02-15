# Scripts Directory
# 脚本目录

**版本:** 2.1.0  
**最后更新:** 2026-02-05

本目录包含项目所有的脚本文件，按功能分类组织。

## 📁 目录结构

```
scripts/
├── deploy/                    # 部署脚本
│   ├── deploy.sh              # 主部署脚本
│   ├── rollback.sh            # 回滚脚本
│   ├── notify_deployment.py   # 部署通知
│   └── README.md              # 部署脚本说明
│
├── cleanup/                   # 清理脚本
│   ├── cleanup_project.sh     # 项目清理
│   ├── cleanup_tasks_docs.sh  # 任务文档清理
│   ├── final_cleanup.sh       # 最终清理
│   ├── refactor_directories.sh # 目录重构
│   ├── clean_cache.sh         # 缓存清理
│   └── README.md              # 清理脚本说明
│
├── docs/                      # 文档脚本
│   ├── docs_generator.py      # 文档生成器
│   ├── verify_yl-monitor_docs.sh # 文档验证
│   └── README.md              # 文档脚本说明
│
├── utilities/                 # 工具脚本
│   ├── build_gui_components.py # GUI组件构建
│   ├── refactor_rules.py      # 规则重构
│   ├── check_dependencies.py  # 依赖检查
│   ├── env.sh                 # 环境变量
│   ├── fix_paths_to_local.sh # 路径修复
│   ├── scripts_manager.py     # 脚本管理
│   ├── scripts_manager_enhanced.py # 增强管理
│   ├── verify_start.sh        # 启动验证
│   └── README.md              # 工具脚本说明
│
├── monitor/                   # 监控脚本
│   ├── monitor.py              # 主监控
│   ├── health_check.py         # 健康检查
│   ├── log_analyzer.py        # 日志分析
│   ├── resource_monitor.py    # 资源监控
│   ├── api_health_check.py   # API健康
│   ├── auto_log_monitor.py    # 自动日志
│   ├── dependency_check.py    # 依赖检查
│   ├── deployment_progress.py # 部署进度
│   ├── env_check.py           # 环境检查
│   ├── monitor_app.py         # 监控应用
│   ├── monitor_router.py      # 监控路由
│   ├── monitor_server.py      # 监控服务
│   ├── service_repair.py      # 服务修复
│   ├── utils/                 # 工具目录
│   └── README.md              # 监控脚本说明
│
├── security/                  # 安全脚本
│   ├── security_scan.py       # 安全扫描
│   ├── vulnerability_check.py # 漏洞检查
│   └── README.md              # 安全脚本说明
│
├── validation/                # 验证脚本
│   ├── validate_backend_services.py # 后端验证
│   ├── validate_frontend_architecture.py # 前端验证
│   ├── check_scripts_integrity.py # 脚本完整性
│   ├── validate_entrypoints.py   # 入口验证
│   ├── validate_rules_engine.py  # 规则验证
│   └── README.md              # 验证脚本说明
│
├── reorganize_scripts.sh       # 目录重构脚本
├── verify_infrastructure.sh    # 基础设施验证
└── README.md                  # 本文档
```

## 📊 脚本统计

| 分类 | 数量 | 描述 |
|------|------|------|
| deploy | 3 | 部署相关脚本 |
| cleanup | 5 | 清理相关脚本 |
| docs | 2 | 文档相关脚本 |
| utilities | 8 | 工具类脚本 |
| monitor | 14 | 监控相关脚本 |
| security | 2 | 安全相关脚本 |
| validation | 5 | 验证相关脚本 |
| **总计** | **39** | |

## 🚀 快速使用

### 部署
```bash
# 部署到生产环境
./scripts/deploy/deploy.sh production

# 回滚到上一版本
./scripts/deploy/rollback.sh production
```

### 清理
```bash
# 执行项目清理（清理临时文件）
./scripts/cleanup/cleanup_project.sh

# 清理任务文档
./scripts/cleanup/cleanup_tasks_docs.sh

# 最终清理（归档任务文档）
./scripts/cleanup/final_cleanup.sh

# 目录重构
./scripts/cleanup/refactor_directories.sh

# 清理缓存
./scripts/cleanup/clean_cache.sh
```

### 文档
```bash
# 生成文档
python scripts/docs/docs_generator.py

# 验证文档
./scripts/docs/verify_yl-monitor_docs.sh
```

### 工具
```bash
# 检查依赖
python scripts/utilities/check_dependencies.py

# 验证启动
./scripts/utilities/verify_start.sh

# 环境变量
source scripts/utilities/env.sh
```

### 验证
```bash
# 验证后端服务
python scripts/validation/validate_backend_services.py

# 验证前端架构
python scripts/validation/validate_frontend_architecture.py

# 验证基础设施
./scripts/verify_infrastructure.sh
```

## 📖 脚本说明

### deploy/ - 部署脚本
| 脚本 | 功能 |
|------|------|
| `deploy.sh` | 主部署脚本，执行完整部署流程 |
| `rollback.sh` | 回滚脚本，恢复到上一版本 |
| `notify_deployment.py` | 部署通知，发送通知到Slack/钉钉 |

### cleanup/ - 清理脚本
| 脚本 | 功能 | 特点 |
|------|------|------|
| `cleanup_project.sh` | 项目清理，清理临时文件、缓存、日志 | 交互式，询问是否清理Docker |
| `cleanup_tasks_docs.sh` | 任务文档清理，移动已完成的文档到归档 | 移动到cleanup-archive目录 |
| `final_cleanup.sh` | 最终清理，移除所有已完成的任务文档 | 归档所有任务文档 |
| `refactor_directories.sh` | 目录重构，重组项目目录结构 | 重构目录 |
| `clean_cache.sh` | 缓存清理，清理各种缓存文件 | 轻量级清理 |

### docs/ - 文档脚本
| 脚本 | 功能 |
|------|------|
| `docs_generator.py` | 自动生成项目文档，输出JSON |
| `verify_yl-monitor_docs.sh` | 验证YL-monitor文档完整性 |

### utilities/ - 工具脚本
| 脚本 | 功能 |
|------|------|
| `build_gui_components.py` | 自动生成GUI组件代码 |
| `refactor_rules.py` | 重构和优化项目规则 |
| `check_dependencies.py` | 检查项目依赖完整性 |
| `env.sh` | 加载环境变量 |
| `fix_paths_to_local.sh` | 修复路径引用 |
| `scripts_manager.py` | 脚本管理器 |
| `scripts_manager_enhanced.py` | 增强版脚本管理器 |
| `verify_start.sh` | 验证项目启动环境 |

### monitor/ - 监控脚本
| 脚本 | 功能 |
|------|------|
| `monitor.py` | 主监控脚本 |
| `health_check.py` | 健康检查 |
| `log_analyzer.py` | 日志分析 |
| `resource_monitor.py` | 资源监控 |
| `api_health_check.py` | API健康检查 |
| `auto_log_monitor.py` | 自动日志监控 |
| `dependency_check.py` | 依赖检查 |
| `deployment_progress.py` | 部署进度 |
| `env_check.py` | 环境检查 |
| `monitor_app.py` | 监控应用 |
| `monitor_router.py` | 监控路由 |
| `monitor_server.py` | 监控服务 |
| `service_repair.py` | 服务修复 |

### security/ - 安全脚本
| 脚本 | 功能 |
|------|------|
| `security_scan.py` | 安全扫描 |
| `vulnerability_check.py` | 漏洞检查 |

### validation/ - 验证脚本
| 脚本 | 功能 |
|------|------|
| `validate_backend_services.py` | 后端服务验证 |
| `validate_frontend_architecture.py` | 前端架构验证 |
| `check_scripts_integrity.py` | 脚本完整性检查 |
| `validate_entrypoints.py` | 入口验证 |
| `validate_rules_engine.py` | 规则引擎验证 |

## 🔗 关联文档

| 文档 | 描述 |
|------|------|
| [Makefile](../Makefile) | Make命令入口 |
| [docker-compose.yml](../docker-compose.yml) | Docker编排配置 |
| [config/](../config/) | 环境配置 |
| [AR-backend/](../AR-backend/) | 后端模块 |

---

**版本:** 2.1.0  
**最后更新:** 2026-02-05
