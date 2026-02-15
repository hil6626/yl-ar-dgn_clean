# Documentation Center
# 文档中心

**版本:** 2.0.0  
**最后更新:** 2026-02-04

YL-AR-DGN 项目的文档中心，汇集所有项目文档。

---

## 📁 文档目录

```
docs/
├── README.md                    # 本文档
├── PROJECT_STRUCTURE.md         # 项目结构
├── DEPLOYMENT_SUMMARY.md        # 部署总结
├── TODO.md                      # 项目待办
│
├── archive/                     # 归档文档
│   ├── README.md               # 归档索引
│   └── *.md                    # 归档文档(12个)
│
├── project/                     # 模块文档
│   ├── README.md               # 模块文档说明
│   ├── optimization-analysis.md # 优化分析
│   └── rules-docs/             # 规则文档
│       └── frontend-interaction-spec.md
│
├── tasks/                      # 任务文档
│   ├── README.md               # 任务文档中心
│   ├── TASK_EXECUTION_SUMMARY.md # 任务执行总览
│   ├── IMPLEMENTATION_SUMMARY.md # 实施总结
│   ├── TODO.md                 # 任务进度
│   ├── *-task.md               # 任务文档(8个)
│   ├── task-*-deploy-*.md      # 部署跟踪(4个)
│   └── *-execution-report.md   # 执行报告(8个)
│
├── cleanup-archive/             # 清理归档
└── workflows/                   # 工作流文档
```

---

## 📚 文档统计

| 目录 | 文档数 | 状态 |
|------|--------|------|
| **根目录** | 4 | ✅ 有效 |
| **archive/** | 12 | 📦 已归档 |
| **project/** | 2 | ✅ 有效 |
| **tasks/** | 24 | ✅ 有效 |
| **cleanup-archive/** | - | 📦 已归档 |
| **合计** | **42+** | |

---

## 🚀 快速导航

### 开始使用

| 主题 | 文档 |
|------|------|
| 项目介绍 | [README.md](../README.md) |
| 项目结构 | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| 快速开始 | [README.md](../README.md#快速开始) |

### 开发文档

| 主题 | 文档 |
|------|------|
| 前端规范 | [project/rules-docs/frontend-interaction-spec.md](project/rules-docs/frontend-interaction-spec.md) |
| 后端文档 | [AR-backend/README.md](../AR-backend/README.md) |
| 监控文档 | [YL-monitor/README.md](../YL-monitor/README.md) |
| 脚本文档 | [scripts/README.md](../scripts/README.md) |

### 任务管理

| 主题 | 文档 |
|------|------|
| 任务列表 | [tasks/README.md](tasks/README.md) |
| 执行进度 | [tasks/TASK_EXECUTION_SUMMARY.md](tasks/TASK_EXECUTION_SUMMARY.md) |
| 实施总结 | [tasks/IMPLEMENTATION_SUMMARY.md](tasks/IMPLEMENTATION_SUMMARY.md) |

### 部署运维

| 主题 | 文档 |
|------|------|
| 部署总结 | [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) |
| 基础设施 | [infrastructure/README.md](../infrastructure/README.md) |
| 安全模块 | [AR-backend/services/security/README.md](../AR-backend/services/security/README.md) |

---

## 📋 任务完成状态

### 总览

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅ 已完成 | 12 | 所有任务已完成 |
| 🔄 进行中 | 0 | 无进行中任务 |
| 📋 规划中 | 0 | 无规划中任务 |

### 按优先级

| 优先级 | 总数 | 已完成 | 完成率 |
|--------|------|--------|--------|
| 高 | 3 | 3 | 100% |
| 中 | 4 | 4 | 100% |
| 低 | 4 | 4 | 100% |

---

## 🛠️ 工具与脚本

### 文档工具

| 脚本 | 用途 |
|------|------|
| `scripts/docs_generator.py` | 文档生成器 |
| `scripts/refactor_rules.py` | 规则重构 |
| `scripts/build_gui_components.py` | GUI组件构建 |

### 清理工具

| 脚本 | 用途 |
|------|------|
| `scripts/cleanup_project.sh` | 项目清理 |

### 验证工具

| 脚本 | 用途 |
|------|------|
| `scripts/verify_infrastructure.sh` | 基础设施验证 |
| `AR-backend/verify_deployment.py` | 部署验证 |

---

## 📊 项目状态

### 核心模块

| 模块 | 状态 | 说明 |
|------|------|------|
| AR-backend | ✅ 完成 | FastAPI后端服务 |
| YL-monitor | ✅ 完成 | Flask监控前端 |
| Infrastructure | ✅ 完成 | Prometheus/Grafana |
| CI/CD | ✅ 完成 | GitHub Actions |
| Security | ✅ 完成 | JWT/RBAC/Audit |

### 质量指标

| 指标 | 目标 | 状态 |
|------|------|------|
| 测试覆盖率 | >80% | ✅ |
| 文档完整度 | 100% | ✅ |
| 任务完成率 | 100% | ✅ |

---

## 🔗 外部链接

- [GitHub Repository](https://github.com)
- [CI/CD Pipeline](../.github/workflows/)
- [Docker Hub](https://hub.docker.com)

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0.0 | 2026-02-04 | 整理归档所有文档 |
| 1.0.0 | 2026-02-01 | 初始文档结构 |

---

**版本:** 2.0.0  
**最后更新:** 2026-02-04
