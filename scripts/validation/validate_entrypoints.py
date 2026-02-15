#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入口一致性校验：根据 rules/L2-understanding.json 检查 entrypoints 是否存在

用法：
  python3 scripts/validation/validate_entrypoints.py --json
"""

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
L2_FILE = PROJECT_ROOT / "rules" / "L2-understanding.json"


def main():
    parser = argparse.ArgumentParser(description="入口一致性校验")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    report = {
        "status": "ok",
        "l2_file": str(L2_FILE),
        "missing": [],
        "checked": []
    }

    data = json.loads(L2_FILE.read_text(encoding="utf-8"))
    modules = data.get("architecture", {}).get("modules", [])

    for module in modules:
        for ep in module.get("entrypoints", []):
            path = PROJECT_ROOT / ep
            report["checked"].append(str(path))
            if not path.exists():
                report["missing"].append(str(path))

    if report["missing"]:
        report["status"] = "error"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report)


if __name__ == "__main__":
    main()
