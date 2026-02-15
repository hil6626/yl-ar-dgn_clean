#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import time

from _common import run_script


SCRIPT_ID = "17"
NAME = "磁盘垃圾清理"
TYPE = "优化"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[17] 磁盘垃圾清理")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument("--path", action="append", default=[], help="Directory to clean (repeatable).")
    p.add_argument("--older-than-days", type=int, default=7, help="Delete files older than N days.")
    p.add_argument("--apply", action="store_true", help="Actually delete files (default: dry-run).")
    p.add_argument("--max-files", type=int, default=200, help="Max files to delete/plan per run.")
    return p


def run(args: argparse.Namespace):
    paths = [Path(p) for p in (args.path or [])] or [Path("/tmp")]
    cutoff = time.time() - int(args.older_than_days) * 86400

    planned: list[dict[str, object]] = []
    deleted = 0
    total_bytes = 0
    for base in paths:
        if not base.exists() or not base.is_dir():
            continue
        for fp in base.rglob("*"):
            if len(planned) >= int(args.max_files):
                break
            if not fp.is_file():
                continue
            try:
                st = fp.stat()
            except (FileNotFoundError, PermissionError):
                continue
            if st.st_mtime > cutoff:
                continue
            planned.append({"file": str(fp), "size_bytes": st.st_size})
            if args.apply:
                try:
                    fp.unlink()
                    deleted += 1
                    total_bytes += st.st_size
                except (FileNotFoundError, PermissionError, IsADirectoryError):
                    continue

    metrics = {
        "dry_run": not bool(args.apply),
        "planned_count": len(planned),
        "deleted_count": deleted,
        "deleted_bytes": total_bytes,
        "planned": planned,
    }
    message = None if planned else "no junk found"
    return metrics, message, {"cutoff_days": int(args.older_than_days), "paths": [str(p) for p in paths]}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
