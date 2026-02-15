#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _common import run_script


SCRIPT_ID = "02"
NAME = "内存使用率监控"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[02] 内存使用率监控")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return p


def run(args: argparse.Namespace):
    meminfo: dict[str, int] = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue
            k, rest = line.split(":", 1)
            parts = rest.strip().split()
            if not parts or not parts[0].isdigit():
                continue
            meminfo[k] = int(parts[0])  # kB

    total_kb = meminfo.get("MemTotal")
    avail_kb = meminfo.get("MemAvailable")
    if not total_kb or avail_kb is None:
        raise RuntimeError("missing MemTotal/MemAvailable in /proc/meminfo")

    used_kb = total_kb - avail_kb
    usage_pct = (used_kb / total_kb) * 100.0
    metrics = {
        "mem_total_mb": round(total_kb / 1024.0, 2),
        "mem_used_mb": round(used_kb / 1024.0, 2),
        "mem_available_mb": round(avail_kb / 1024.0, 2),
        "mem_usage_pct": round(usage_pct, 2),
    }
    return metrics, None, {}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
