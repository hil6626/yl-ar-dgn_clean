#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil

from _common import run_script


SCRIPT_ID = "03"
NAME = "磁盘空间 & I/O"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[03] 磁盘空间 & I/O")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument("--path", default="/", help="Path to check disk usage for.")
    return p


def run(args: argparse.Namespace):
    usage = shutil.disk_usage(args.path)
    used_pct = (usage.used / usage.total) * 100.0 if usage.total else 0.0
    metrics = {
        "path": args.path,
        "disk_total_gb": round(usage.total / (1024**3), 2),
        "disk_used_gb": round(usage.used / (1024**3), 2),
        "disk_free_gb": round(usage.free / (1024**3), 2),
        "disk_used_pct": round(used_pct, 2),
    }
    return metrics, None, {}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
