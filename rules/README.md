# 规则中心（Rules）

项目的运行规则与系统逻辑中枢。以**分层规则框架**为单一真相来源，指导整个项目的架构、开发、部署与运维。

---

## 📋 框架概述

### 五层规则架构

| 层级 | 文件 | 描述 | 用途 |
|------|------|------|------|
| **L1** | `L1-meta-goal.json` | 元目标层 | 定义项目最高优先级目标、演进方向与成熟度路线图 |
| **L2** | `L2-understanding.json` | 理解层 | 系统理解深度、技术决策前提与领域认知 |
| **L3** | `L3-constraints.json` | 约束层 | 项目边界、技术限制、依赖关系与必去风险 |
| **L4** | `L4-decisions.json` | 决策层 | 架构方案、接口设计、工作流规范与选型依据 |
| **L5** | `L5-execution.json` | 执行层 | 具体操作步骤、脚本命令、部署流程与验证标准 |

---

## 🎯 核心规范

### 前端交互规范
- 📄 [前端联动与交互规范](../docs/project/rules-docs/frontend-interaction-spec.md)
  - 前端组件生命周期
  - API 调用约定
  - 事件流管理
  - 错误处理标准

---

## 🚀 快速导航

### 系统初始化
1. 查看 **L1 元目标** 了解项目方向
2. 查看 **L3 约束** 理解系统限制
3. 查看 **L5 执行** 获取启动命令

### 规则引擎校验（建议）
```bash
# 校验 rules.config.js 与 L1~L5 是否可用
python3 scripts/validation/validate_rules_engine.py --json

# 校验入口是否存在（基于 L2-understanding.json）
python3 scripts/validation/validate_entrypoints.py --json
```

### 开发工作流
1. 查看 **L2 理解** 确保认知一致
2. 查看 **L4 决策** 理解架构约定
3. 查看 **L5 执行** 操作实现步骤

### 问题排查
- 架构问题 → 查看 **L4 决策**
- 流程问题 → 查看 **L5 执行**
- 边界问题 → 查看 **L3 约束**

---

## 📚 文件说明

### index.js
规则系统的入口与加载器，管理所有规则文件的加载与访问。

### rules.config.js
规则引擎的基本配置，包含版本、依赖路径与全局设置。

---

## 🔄 更新流程

修改规则时必须遵循层级关系：
1. **底层变更**（L5 执行）→ 仅更新执行步骤
2. **决策变更**（L4 以上）→ 级联更新相关下层规则
3. **目标变更**（L1 以上）→ 重新梳理整个规则体系

---

## 📖 相关文档

- [项目总览] → [../README.md](../README.md)
- [任务追踪] → [../docs/TODO.md](../docs/TODO.md)
- [后端说明] → [../AR-backend/README.md](../AR-backend/README.md)
- [监控前端] → [../YL-monitor/README.md](../YL-monitor/README.md)
