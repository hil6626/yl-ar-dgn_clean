#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

from _common import run_script


SCRIPT_ID = "01"
NAME = "CPU 使用率监控"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[01] CPU 使用率监控")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument("--interval", type=float, default=0.25, help="Sampling interval seconds.")
    return p


def run(args: argparse.Namespace):
    def read_cpu() -> tuple[int, int]:
        with open("/proc/stat", "r", encoding="utf-8") as f:
            line = f.readline()
        parts = line.split()
        if not parts or parts[0] != "cpu":
            raise RuntimeError("unexpected /proc/stat format")
        nums = list(map(int, parts[1:]))
        idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
        total = sum(nums)
        return idle, total

    idle1, total1 = read_cpu()
    time.sleep(max(0.05, float(args.interval)))
    idle2, total2 = read_cpu()
    idle_delta = idle2 - idle1
    total_delta = total2 - total1
    if total_delta <= 0:
        raise RuntimeError("invalid cpu sampling delta")
    usage_pct = (1.0 - (idle_delta / total_delta)) * 100.0
    return {"cpu_usage_pct": round(usage_pct, 2)}, None, {"interval_s": float(args.interval)}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
