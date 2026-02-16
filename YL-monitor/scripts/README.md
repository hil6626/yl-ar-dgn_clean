# scripts/ 脚本目录

> YL-Monitor 自动化脚本库，按功能分类组织

## 📁 目录结构

```
scripts/
├── _common.py                    # ✅ BaseScript 基类定义（核心）
├── script_registry.json           # ✅ 脚本注册中心（白名单）
│
├── monitor/                      # 📊 监控类脚本
│   ├── README.md                # 监控脚本说明
│   └── 01~13_*.py              # 11个监控脚本
│
├── maintenance/                 # 🔧 维护类脚本
│   ├── README.md                # 维护脚本说明
│   └── 11~54_*.py              # 18个维护脚本
│
├── optimize/                    # ⚡ 优化类脚本
│   ├── README.md                # 优化脚本说明
│   └── 16~51_*.py               # 23个优化脚本
│
├── alert/                       # 🚨 告警类脚本
│   ├── README.md                # 告警脚本说明
│   └── 14_*.py                  # 1个告警脚本
│
└── tools/                       # 🛠️ 运维工具脚本
    ├── README.md                # 工具脚本说明
    └── *_*.py / *.sh            # 9个运维工具
```

## 🎯 快速索引

| 类别 | 脚本数量 | 说明 |
|------|---------|------|
| [monitor/](./monitor/README.md) | 11 | 系统与服务实时监控 |
| [maintenance/](./maintenance/README.md) | 18 | 系统维护与巡检 |
| [optimize/](./optimize/README.md) | 23 | 性能优化与清理 |
| [alert/](./alert/README.md) | 1 | 告警与通知 |
| [tools/](./tools/README.md) | 9 | 运维工具 |

## 📋 完整脚本清单

### 监控类 (Monitor) - 01~13

| ID | 名称 | 状态 |
|----|------|------|
| 01 | CPU使用率监控 | ✅ 已实现 |
| 02 | 内存使用率监控 | ✅ 已实现 |
| 03 | 磁盘空间与I/O监控 | ✅ 已实现 |
| 04 | 系统负载与进程监控 | ✅ 已实现 |
| 05 | 端口服务可用性检查 | ✅ 已实现 |
| 06 | 网络延迟与带宽监控 | ⏳ 待实现 |
| 07 | 外部API健康检查 | ✅ 已实现 |
| 08 | Web应用可用性检测 | ⏳ 待实现 |
| 09 | 数据库连接与查询监控 | ⏳ 待实现 |
| 10 | 日志异常扫描 | ✅ 已实现 |
| 13 | AR节点资源监控 | ⏳ 待实现 |

### 维护类 (Maintenance) - 11~54

| ID | 名称 | 状态 |
|----|------|------|
| 11 | 脚本执行状态监控 | ⏳ 待实现 |
| 12 | DAG节点状态监控 | ⏳ 待实现 |
| 15 | 定时巡检报告生成 | ⏳ 待实现 |
| 22 | 系统更新补丁检查 | ⏳ 待实现 |
| 25 | 文件备份归档 | ⏳ 待实现 |
| 26 | 日志异常归档 | ⏳ 待实现 |
| 30 | 应用配置检查修复 | ⏳ 待实现 |
| 33 | 自动归档回滚 | ⏳ 待实现 |
| 36 | 系统启动加速优化 | ⏳ 待实现 |
| 38 | 数据库索引优化 | ⏳ 待实现 |
| 39 | 日志智能归类标签 | ⏳ 待实现 |
| 40 | 历史数据压缩归档 | ⏳ 待实现 |
| 41 | 自动数据摘要 | ⏳ 待实现 |
| 42 | 服务依赖检测 | ⏳ 待实现 |
| 44 | API负载测试 | ⏳ 待实现 |
| 52 | 自动配置异常修复 | ⏳ 待实现 |
| 53 | 多环境脚本同步 | ⏳ 待实现 |
| 54 | 安全策略校验 | ⏳ 待实现 |

### 优化类 (Optimize) - 16~51

| ID | 名称 | 状态 |
|----|------|------|
| 16 | 资源趋势分析 | ⏳ 待实现 |
| 17 | 磁盘垃圾清理 | ✅ 已实现 |
| 18 | 重复文件去重 | ⏳ 待实现 |
| 19 | 缓存清理 | ⏳ 待实现 |
| 20 | 临时文件清理 | ✅ 已实现 |
| 21 | 日志轮转压缩 | ⏳ 待实现 |
| 23 | 数据库冗余清理 | ⏳ 待实现 |
| 24 | 缓存数据库维护 | ⏳ 待实现 |
| 27 | 应用临时数据清理 | ⏳ 待实现 |
| 28 | 浏览器历史管理 | ⏳ 待实现 |
| 29 | 服务缓存刷新 | ⏳ 待实现 |
| 31 | 清理优化组合任务 | ⏳ 待实现 |
| 32 | 智能维护脚本 | ⏳ 待实现 |
| 34 | 进程优先级调整 | ⏳ 待实现 |
| 35 | 内存泄漏检测告警 | ⏳ 待实现 |
| 37 | CPU核心负载均衡 | ⏳ 待实现 |
| 43 | 流量异常识别 | ⏳ 待实现 |
| 45 | 负载均衡调优 | ⏳ 待实现 |
| 46 | 任务依赖自动修复 | ⏳ 待实现 |
| 47 | AR渲染节点调度 | ⏳ 待实现 |
| 48 | 脚本异常回滚 | ⏳ 待实现 |
| 49 | 脚本优先级调度 | ⏳ 待实现 |
| 50 | 性能趋势预测 | ⏳ 待实现 |
| 51 | 智能清理策略生成 | ⏳ 待实现 |

### 告警类 (Alert) - 14

| ID | 名称 | 状态 |
|----|------|------|
| 14 | 阈值告警通知 | ⏳ 待实现 |

## 🔧 使用方式

### 通过前端页面

1. 打开浏览器访问：`http://0.0.0.0:5500/scripts`
2. 查看脚本列表
3. 点击执行按钮运行脚本

### 通过 API 调用

```bash
# 获取脚本列表
GET /api/scripts/list

# 执行脚本
POST /api/scripts/run
{"script_id": "01"}
```

### 直接运行

```bash
# 进入项目目录
cd YL-monitor

# 运行监控脚本
python3 scripts/monitor/01_cpu_usage_monitor.py --pretty

# 运行维护脚本
python3 scripts/maintenance/15_scheduled_inspection_report.py --pretty

# 运行优化脚本（dry-run模式）
python3 scripts/optimize/17_disk_junk_cleanup.py --pretty

# 运行优化脚本（真实执行）
python3 scripts/optimize/17_disk_junk_cleanup.py --apply --pretty
```

## 📦 统一输出格式

所有脚本返回标准 JSON 格式：

```json
{
  "id": "01",
  "name": "CPU使用率监控",
  "type": "monitor",
  "status": "ok" | "error",
  "timestamp": "2026-02-05T10:30:00Z",
  "host": {
    "hostname": "server01",
    "platform": "Linux x86_64"
  },
  "metrics": {
    "cpu_percent": 45.2,
    "load_average": [1.2, 1.5, 1.8]
  },
  "message": "CPU使用率正常",
  "detail": {
    "duration_ms": 125
  }
}
```

## 🛠️ 运维工具

| 工具 | 说明 |
|------|------|
| `project_run.sh` | 项目启动脚本 |
| `docker_build.sh` | Docker 镜像构建 |
| `docker_start.sh` | Docker 容器启动 |
| `docker_stop.sh` | Docker 容器停止 |
| `cleanup_old_files.py` | 清理旧文件 |
| `verify_frontend_optimization.py` | 前端优化验证 |
| `verify_static_resources.sh` | 静态资源验证 |
| `verify_deployment.py` | 部署验证 |
| `test_api_functionality.py` | API 功能测试 |

## 📖 相关文档

- [脚本注册表](./script_registry.json) - 脚本白名单配置
- [项目架构](../../ARCHITECTURE.md) - 完整架构设计
- [部署文档](../../README.md) - 项目说明

## ✅ 脚本状态

- **✅ 已实现**：功能完整，可直接使用
- **⏳ 待实现**：已有占位文件，逻辑待补充

---

**最后更新**: 2026-02-05

