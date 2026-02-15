# scripts/validation

本目录存放“校验/验收”类脚本：用于检查项目结构、服务实现与前端架构是否符合约定，并输出可用于 CI 的结果。

## 与根目录同名脚本的关系

在 `scripts/` 根目录下也存在同名脚本（例如 `scripts/check_scripts_integrity.py`）。通常：

- 根目录版本：轻量示例/入口包装（更偏“快速跑通”）。
- `scripts/validation/` 版本：更完整、更严格（更偏“验收/CI”）。

如果你要做发版前检查或 CI 校验，优先使用本目录脚本。

## 快速开始

在项目根目录执行：

```bash
# 脚本完整性检查
python3 scripts/validation/check_scripts_integrity.py --report

# 规则引擎配置校验
python3 scripts/validation/validate_rules_engine.py --json

# 入口一致性校验（基于 rules/L2-understanding.json）
python3 scripts/validation/validate_entrypoints.py --json

# 后端服务实现校验（结构/导入/API 可用性等）
python3 scripts/validation/validate_backend_services.py

# 前端架构校验（文件结构/模块化约束/API 连通性等）
python3 scripts/validation/validate_frontend_architecture.py
```

## 输出与日志

- `check_scripts_integrity.py`：
  - 支持 `--json/--report/--verbose`。
  - 默认会把日志写到 `scripts/logs/scripts_integrity.log`（脚本会自动创建目录）。
- `validate_backend_services.py` / `validate_frontend_architecture.py`：
  - 默认输出到 stdout。
  - 会尝试访问本地 `http://localhost:5000` 的部分 API；如果服务未启动会给出 warning（通常不会直接中断整个脚本）。

## 适配建议（很重要）

这些脚本内置了一套“目标目录结构/接口约定”（例如 `src/backend/...`、`src/frontend/...`）。如果你的当前工程还未采用该结构，校验会出现大量“缺失文件/路径”的报错是正常的。

落地到当前仓库时，建议按以下顺序适配：

1. 先把 `required_files/required_services` 这类路径列表改成与你实际目录一致（例如以 `AR-backend/`、`YL-monitor/` 为准）。
2. 再把 API endpoints 列表改成你真实启动的地址与路由前缀（例如 `/api/v1/...` vs `/api/...`）。
3. 最后再把脚本纳入 CI（确保“失败即失败”的规则不会误伤日常开发）。
