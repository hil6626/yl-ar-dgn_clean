# scripts/monitor

本目录是“监控与健康检测”脚本集合，覆盖：环境检查、系统健康/资源监控、API 健康检查、日志分析、服务修复，以及监控后端（Flask）。

## 快速开始

在项目根目录执行：

```bash
# 1) 系统健康检查（一次性）
python3 scripts/monitor/health_check.py --once --json

# 2) 系统健康监控（持续输出）
python3 scripts/monitor/monitor.py --interval 5

# 3) API 健康检查（报告）
python3 scripts/monitor/api_health_check.py --url http://localhost:5000 --report

# 4) 资源监控（JSON 输出）
python3 scripts/monitor/resource_monitor.py --json

# 5) 日志分析（默认输出 JSON）
python3 scripts/monitor/log_analyzer.py
```

不确定参数时：`python3 scripts/monitor/<script>.py --help`。

## 后端入口（本地联调）

如果你需要一个本地 API 服务（含 WebSocket）来承载监控数据与脚本调度：

- 路由调度器（推荐优先使用）：`python3 scripts/monitor/monitor_router_refactored.py`（默认端口 `5000`）
- 监控应用（UI + API）：`python3 scripts/monitor/monitor_app.py`
- 同源监控服务（静态页面 + /monitor/api）：`python3 scripts/monitor/monitor_server.py`（默认端口 `5000`）

> 说明：`monitor_app.py` 依赖模板/静态目录配置（Flask `template_folder/static_folder`），若你的仓库未提供对应目录，建议先用 `monitor_router_refactored.py` 跑通接口联调。

## 脚本清单

- `health_check.py`：系统健康检查（CPU/内存/磁盘/服务），支持 `--once/--daemon/--interval/--json`。
- `monitor.py`：系统健康监控（持续模式/阈值/报告），支持 `--interval/--threshold/--report/--json`。
- `resource_monitor.py`：资源监控（CPU/内存/磁盘/网络），支持 `--interval/--threshold/--report/--json`。
- `api_health_check.py`：API 端点健康检查与报告，支持 `--url/--endpoint/--report/--output` 等。
- `log_analyzer.py`：日志分析/报告/实时监控，支持 `--log-file/--analyze/--report/--watch`。
- `deployment_progress.py`：部署进度跟踪（状态/更新/报告）。
- `env_check.py`：运行环境检查（变量/路径/依赖）。
- `dependency_check.py`：依赖检查与建议（更偏“安装前自检”）。
- `service_repair.py`：服务状态检查与修复（支持守护模式）。
- `auto_log_monitor.py`：自动扫描/监控日志并输出告警。
- `utils/`：脚本公共工具与复用模块。

## 输出与日志

- 大多数脚本支持 `--json` 或 `--report`，会将报告写入项目 `logs/`（具体以脚本 `--help` 为准）。
