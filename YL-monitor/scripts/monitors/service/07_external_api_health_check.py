#!/usr/bin/env python3
from __future__ import annotations

import argparse

from _common import http_get_timing_ms, run_script


SCRIPT_ID = "07"
NAME = "外部接口健康检查"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[07] 外部接口健康检查")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument("--url", action="append", default=[], help="URL to check (repeatable).")
    p.add_argument("--timeout", type=float, default=5.0, help="Request timeout seconds.")
    return p


def run(args: argparse.Namespace):
    urls = args.url or []
    if not urls:
        urls = ["https://example.com/"]

    results: list[dict[str, object]] = []
    ok = 0
    for url in urls:
        timing = http_get_timing_ms(url, float(args.timeout))
        code = timing.get("http_code")
        is_ok = isinstance(code, int) and 200 <= code < 400
        if is_ok:
            ok += 1
        results.append({"url": url, "ok": is_ok, **timing})

    metrics = {"checks": results, "ok_count": ok, "total": len(results), "success_rate": round(ok / max(1, len(results)), 4)}
    message = None if ok == len(results) else "some urls unhealthy"
    return metrics, message, {}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
