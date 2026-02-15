#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则引擎校验：检查 rules.config.js 与 L1~L5 是否可用

用法：
  python3 scripts/validation/validate_rules_engine.py --json
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = PROJECT_ROOT / "rules"


def load_rules_config_via_node():
    """使用 Node 加载 rules.config.js（避免手写 JS 解析）"""
    node_cmd = [
        "node",
        "-e",
        "const cfg=require('./rules/rules.config.js'); console.log(JSON.stringify(cfg));"
    ]
    result = subprocess.run(
        node_cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None, result.stderr.strip()
    try:
        return json.loads(result.stdout.strip()), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def validate_layer_files(layer_files):
    missing = []
    for name in layer_files:
        path = RULES_DIR / name
        if not path.exists():
            missing.append(str(path))
    return missing


def main():
    parser = argparse.ArgumentParser(description="rules 引擎配置校验")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    report = {
        "status": "ok",
        "rules_dir": str(RULES_DIR),
        "config_loaded": False,
        "layer_files": [],
        "missing_layers": [],
        "errors": []
    }

    cfg, err = load_rules_config_via_node()
    if err:
        report["status"] = "error"
        report["errors"].append(err)
    else:
        report["config_loaded"] = True
        layer_files = cfg.get("layerFiles", [])
        report["layer_files"] = layer_files
        report["missing_layers"] = validate_layer_files(layer_files)
        if report["missing_layers"]:
            report["status"] = "error"
            report["errors"].append("missing layer files")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report)


if __name__ == "__main__":
    main()
