#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚠️ DEPRECATED: 此脚本已废弃
替代方案: YL-monitor/scripts/monitor/05_port_service_availability_check.py
          YL-monitor/scripts/monitor/07_external_api_health_check.py

废弃日期: 2026-02-09
原因: 功能重复，YL-monitor版本更完善
保留期限: 30天后删除
"""

import warnings
import sys

warnings.warn(
    "此脚本已废弃，请使用 YL-monitor/scripts/monitor/ 下的监控脚本",
    DeprecationWarning,
    stacklevel=2
)

print("⚠️  此脚本已废弃", file=sys.stderr)
print("请使用以下替代方案:", file=sys.stderr)
print("  - YL-monitor/scripts/monitor/05_port_service_availability_check.py",
      file=sys.stderr)
print("  - YL-monitor/scripts/monitor/07_external_api_health_check.py",
      file=sys.stderr)
print("  - YL-monitor/scripts/monitor/01_cpu_usage_monitor.py", file=sys.stderr)
sys.exit(1)
