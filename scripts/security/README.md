# scripts/security

本目录提供安全扫描与依赖漏洞检测脚本，用于本地开发自检与部署前安全核查。

## 快速开始

在项目根目录执行：

```bash
# 1) 系统安全扫描（文本输出）
python3 scripts/security/security_scan.py

# 2) 系统安全扫描（JSON 输出，结果也会落到 logs/security_results.json）
python3 scripts/security/security_scan.py --output json

# 3) 依赖漏洞检测（建议显式指定 requirements 文件）
python3 scripts/security/vulnerability_check.py --requirements AR-backend/requirements/requirements.txt --output text
```

不确定参数时：`python3 scripts/security/<script>.py --help`。

## 脚本说明

- `security_scan.py`：综合安全扫描（权限/端口/依赖/配置等），支持 `--output json|text|html`。
- `vulnerability_check.py`：依赖漏洞检测与报告，支持 `--requirements <path>` 与 `--output json|text`（并根据漏洞严重性返回不同退出码）。

## 输出与退出码

- `security_scan.py`：默认会将最新结果写入 `logs/security_results.json`，退出码通常用于 CI/CD 判定（无失败为 `0`）。
- `vulnerability_check.py`：若存在 `critical` 漏洞返回 `2`；存在 `high` 返回 `1`；否则返回 `0`。
