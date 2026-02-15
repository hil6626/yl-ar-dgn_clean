#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re

from _common import run_script


SCRIPT_ID = "04"
NAME = "系统负载 & 关键进程"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[04] 系统负载 & 关键进程")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument(
        "--process",
        action="append",
        default=[],
        help="Regex to match process comm/cmdline (repeatable).",
    )
    p.add_argument("--max-procs", type=int, default=50, help="Max processes to scan.")
    return p


def run(args: argparse.Namespace):
    load1, load5, load15 = os.getloadavg()

    patterns = [re.compile(p) for p in (args.process or [])]
    found: dict[str, int] = {p.pattern: 0 for p in patterns}
    scanned = 0

    if patterns:
        for pid in os.listdir("/proc"):
            if scanned >= int(args.max_procs):
                break
            if not pid.isdigit():
                continue
            comm_path = f"/proc/{pid}/comm"
            cmd_path = f"/proc/{pid}/cmdline"
            try:
                with open(comm_path, "r", encoding="utf-8") as f:
                    comm = f.read().strip()
                with open(cmd_path, "rb") as f:
                    raw = f.read().replace(b"\x00", b" ").strip()
                cmdline = raw.decode("utf-8", errors="replace")
            except (FileNotFoundError, PermissionError):
                continue
            scanned += 1
            text = f"{comm} {cmdline}"
            for p in patterns:
                if p.search(text):
                    found[p.pattern] += 1

    metrics = {"loadavg_1": load1, "loadavg_5": load5, "loadavg_15": load15, "proc_scanned": scanned}
    if patterns:
        metrics["proc_matches"] = found
    return metrics, None, {}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
