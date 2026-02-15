#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import run_script


SCRIPT_ID = "10"
NAME = "日志异常扫描"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[10] 日志异常扫描")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument("--path", action="append", default=[], help="Log file or directory (repeatable).")
    p.add_argument("--pattern", action="append", default=[], help="Regex pattern (repeatable).")
    p.add_argument("--max-lines", type=int, default=5500, help="Max lines to scan per file.")
    return p


def run(args: argparse.Namespace):
    targets = [Path(p) for p in (args.path or [])] or [Path("/var/log")]
    patterns = [re.compile(p, re.IGNORECASE) for p in (args.pattern or [])] or [
        re.compile(r"\\b(error|exception|traceback|fatal)\\b", re.IGNORECASE),
    ]

    files: list[Path] = []
    for t in targets:
        if t.is_file():
            files.append(t)
        elif t.is_dir():
            for p in t.rglob("*.log"):
                files.append(p)

    findings: list[dict[str, object]] = []
    scanned_files = 0
    for fp in sorted(set(files))[:50]:
        if not fp.exists():
            continue
        try:
            with fp.open("r", encoding="utf-8", errors="replace") as f:
                hits = 0
                for i, line in enumerate(f, start=1):
                    if i > int(args.max_lines):
                        break
                    if any(p.search(line) for p in patterns):
                        hits += 1
                        if hits <= 20:
                            findings.append({"file": str(fp), "line": i, "text": line.strip()[:300]})
                scanned_files += 1
        except (PermissionError, IsADirectoryError):
            continue

    metrics = {"scanned_files": scanned_files, "finding_count": len(findings), "findings": findings}
    message = None if not findings else "anomalies found"
    return metrics, message, {"patterns": [p.pattern for p in patterns]}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
