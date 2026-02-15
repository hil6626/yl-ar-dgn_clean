# 📚 文档导航

文档中心的完整索引。快速定位你需要的信息。

---

## 🎯 快速入门

## ⚠️ 强制规则（必读）

**任何操作前必读：[EXECUTION_RULES.md](EXECUTION_RULES.md) - 9 步强制执行规则**

这是项目的绝对执行标准，所有任务都必须严格遵循。

---

### 我是新手

1. [EXECUTION_RULES.md](EXECUTION_RULES.md) - **⭐ 强制执行规则** - 必须理解 9 步法则
2. [../README.md](../README.md) - **项目概览** - 了解整体架构与快速启动
3. [../rules/README.md](../rules/README.md) - **规则体系** - 理解项目的规则框架
4. [README.md](README.md) - **文档中心说明** - 浏览文档目录
5. [project/rules-docs/frontend-interaction-spec.md](project/rules-docs/frontend-interaction-spec.md) - **前端规范** - 如果要开发前端

### 我要开发

| 目标 | 文档 | 说明 |
|------|------|------|
| **前端页面** | [project/rules-docs/frontend-interaction-spec.md](project/rules-docs/frontend-interaction-spec.md) | 交互规范与约定 |
| **后端服务** | [../AR-backend/README.md](../AR-backend/README.md) | 后端模块说明 |
| **运维脚本** | [../scripts/README.md](../scripts/README.md) | 脚本使用指南 |
| **系统集成** | [../api-map/README.md](../api-map/README.md) | API 映射与接口 |
| **规则修改** | [../rules/README.md](../rules/README.md) | 规则系统说明 |

### 我要追踪任务

→ 查看 [TODO.md](TODO.md) 了解当前进度

---

## 📂 完整目录

### 核心文档

| 文件 | 用途 | 位置 |
|------|------|------|
| **README.md** | 本文档中心说明 | [README.md](README.md) |
| **INDEX.md** | 本快速导航 | [INDEX.md](INDEX.md) |
| **TODO.md** | 任务与进度跟踪 | [TODO.md](TODO.md) |
| **docs.json** | 机器可读的目录索引 | [docs.json](docs.json) |
| **workflow_rules.json** | 工作流强制规则 | [workflow_rules.json](workflow_rules.json) |

### 项目模块文档

**位置**: `project/`

| 模块 | 说明文档位置 |
|------|----------|
| 🎯 **规则体系** | [project/rules-docs/](project/rules-docs/) - **含前端交互规范** |
| 📊 **YL-monitor** | [project/YL-monitor-docs/](project/YL-monitor-docs/) |
| 🖥️ **user (GUI)** | [project/user-docs/](project/user-docs/) |
| 🔧 **AR-backend** | [project/AR-backend-docs/](project/AR-backend-docs/) |
| 🗂️ **api-map** | [project/api-map-docs/](project/api-map-docs/) |
| 🚀 **scripts** | [project/scripts-docs/](project/scripts-docs/) |
| 📌 **其他** | [project/other-docs/](project/other-docs/) |

### 任务详情

**位置**: `tasks/`

- 具体任务的执行记录与详细文档
- 格式: `<module>-<sequence>-task.md`
- 示例: `YL-monitor-001-task.md`, `AR-backend-001-task.md`

### 历史与参考

**位置**: `archive/`

- 项目大纲与版本历史
- 参考资料与备忘

---

## 🔗 关键文档快速链接

### 必读

- ✨ [**前端交互规范**](project/rules-docs/frontend-interaction-spec.md) - 前端/YL-monitor 开发必读
- ⚙️ [**规则体系**](../rules/README.md) - 理解项目规则
- 📋 [**任务进度**](TODO.md) - 当前任务状态

### 各模块入口

- 🏠 [项目总览](../README.md)
- 📊 [监控前端](../YL-monitor/README.md)
- 🖥️ [用户GUI](../user/README.md)
- 🔌 [后端服务](../AR-backend/README.md)
- 🗂️ [接口映射](../api-map/README.md)
- 🚀 [脚本集合](../scripts/README.md)
- ⚖️ [规则中心](../rules/README.md)

---

## 🎯 按职责找文档

### 前端开发者
→ [project/rules-docs/frontend-interaction-spec.md](project/rules-docs/frontend-interaction-spec.md)

### 后端开发者
→ [../AR-backend/README.md](../AR-backend/README.md) 与 [project/AR-backend-docs/](project/AR-backend-docs/)

### 测试/QA
→ [project/scripts-docs/](project/scripts-docs/) 与 [TODO.md](TODO.md)

### DevOps/运维
→ [../scripts/README.md](../scripts/README.md) 与 [project/scripts-docs/](project/scripts-docs/)

### 项目经理
→ [TODO.md](TODO.md) 与 [../rules/L1-meta-goal.json](../rules/L1-meta-goal.json)

---

## 💡 常见问题

**Q: 我不知道从哪里开始**
- A: 从本页的"快速入门"部分开始，按顺序阅读 3-4 份文档

**Q: 我找不到某个功能的文档**
- A: 尝试查看 [README.md](README.md) 的「核心目录」部分，或搜索 `project/` 下的相关目录

**Q: 我需要了解 API**
- A: 查看 [../api-map/README.md](../api-map/README.md) 与 [../api-map/routes/](../api-map/routes/)

**Q: 我需要修改前端**
- A: 必须先阅读 [project/rules-docs/frontend-interaction-spec.md](project/rules-docs/frontend-interaction-spec.md)

**Q: 系统有问题，我该看什么**
- A: 先看 [../rules/L3-constraints.json](../rules/L3-constraints.json)（约束）和 [../rules/L5-execution.json](../rules/L5-execution.json)（执行步骤）

---

## 📝 文档维护

- 新增功能 → 在对应 `project/<module>-docs/` 添加文档
- 新增任务 → 在 [TODO.md](TODO.md) 记录，在 `tasks/` 创建详情文档
- 规则变更 → 同时更新 `../rules/` 与本文档
- 文档优化 → 保持与本导航的一致性
