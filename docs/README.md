# YL-AR-DGN 项目文档中心

**版本:** 1.0.0  
**最后更新:** 2026-02-16  
**状态:** 🟢 文档结构已优化

---

## 📚 文档导航

### 🚀 快速开始
| 文档 | 说明 |
|------|------|
| [项目总览](../README.md) | 根目录README，项目完整说明 |
| [快速开始指南](guides/quickstart.md) | 5分钟上手教程 |
| [部署索引](../部署/0.部署索引.md) | 部署文档总入口 |
| [TODO_DEPLOY](../部署/TODO_DEPLOY.md) | 任务跟踪清单 |

### 🏗️ 架构文档
| 文档 | 说明 |
|------|------|
| [系统架构](architecture/system-architecture.md) | 系统架构图详细说明 |
| [数据流说明](architecture/data-flow.md) | 数据流向和处理流程 |
| [API设计](architecture/api-design.md) | API接口设计规范 |

### 📖 使用指南
| 文档 | 说明 |
|------|------|
| [故障排查](guides/troubleshooting.md) | 常见问题排查方法 |
| [常见问题](guides/faq.md) | FAQ汇总 |

### 🛠️ 开发文档
| 文档 | 说明 |
|------|------|
| [编码规范](development/coding-standards.md) | 代码编写规范 |
| [测试指南](development/testing-guide.md) | 测试方法和工具 |
| [贡献指南](development/contribution.md) | 如何贡献代码 |

### 📋 任务文档
| 文档 | 说明 |
|------|------|
| [任务索引](tasks/README.md) | 所有任务文档索引 |

---

## 🔧 组件文档

| 组件 | 文档 | 版本 | 状态 |
|------|------|------|------|
| **AR-backend** | [README](../AR-backend/README.md) | 3.2.0 | 🟢 运行中 |
| **YL-monitor** | [README](../YL-monitor/README.md) | 1.0.8 | 🟢 运行中 |
| **User GUI** | [README](../user/README.md) | 2.2.0 | 🟢 运行中 |
| **Scripts** | [README](../scripts/README.md) | 2.3.0 | 🟢 可用 |
| **Rules** | [README](../rules/README.md) | 1.2.0 | 🟡 部分完成 |

---

## 📊 部署文档

| 文档 | 说明 |
|------|------|
| [部署索引](../部署/0.部署索引.md) | 文档总入口，包含执行路线图 |
| [TODO_DEPLOY](../部署/TODO_DEPLOY.md) | 任务跟踪清单 (29个任务) |
| [完成报告](../部署/完成报告-阶段1到阶段3.md) | 阶段1-3合并完成报告 |
| [项目部署大纲](../部署/1.项目部署大纲.md) | 项目整体部署规划 |
| [整体方案](../部署/2.整体方案.md) | 系统整体架构方案 |
| [监控整合方案](../部署/3.监控整合方案.md) | 监控整合详细方案 |
| [User-GUI优化方案](../部署/4.User-GUI优化方案.md) | GUI优化详细方案 |
| [规则架构部署](../部署/5.规则架构部署.md) | 规则架构详细方案 |
| [脚本整合方案](../部署/6.脚本整合方案.md) | 脚本整合详细方案 |
| [联调测试方案](../部署/7.联调测试方案.md) | 端到端测试方案 |

---

## 🎯 快速链接

### 常用命令
```bash
# 查看所有服务状态
./scripts/yl-ar-dgn.sh status

# 验证项目完整性
./scripts/yl-ar-dgn.sh validate

# 启动 User GUI
cd user && python3 main.py
```

### 服务地址
| 服务 | 地址 | 端口 |
|------|------|------|
| YL-monitor | http://0.0.0.0:5500 | 5500 |
| AR-backend | http://0.0.0.0:5501 | 5501 |
| User GUI | http://0.0.0.0:5502 | 5502 |

---

## 📈 项目状态

| 阶段 | 状态 | 进度 |
|------|------|------|
| 阶段1: 监控整合 | ✅ 已完成 | 100% |
| 阶段2: User GUI优化 | ✅ 已完成 | 100% |
| 阶段3: 规则架构部署 | 🟡 部分完成 | 60% |
| 阶段4: 脚本整合 | ⬜ 待开始 | 0% |
| 阶段5: 联调测试 | ⬜ 待开始 | 0% |

**总体进度:** 40% (12/30任务完成)

---

## 🆘 获取帮助

### 常见问题排查
```bash
# 查看服务日志
tail -f YL-monitor/logs/app.log
tail -f AR-backend/logs/monitor.log
tail -f user/logs/user_gui.log

# 检查进程状态
ps aux | grep -E "yl-monitor|ar-backend|user-gui"

# 检查端口占用
netstat -tlnp | grep -E "5500|5501|5502"
```

### 文档反馈
如发现文档问题，请更新对应文档或联系项目维护者。

---

**维护者:** YL-AR-DGN 项目团队  
**最后更新:** 2026-02-16
