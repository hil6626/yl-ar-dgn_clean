#!/usr/bin/env python3
from __future__ import annotations

import argparse
import socket

from _common import run_script, tcp_connect_latency_ms


SCRIPT_ID = "05"
NAME = "网络端口 & 服务可用性"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[05] 网络端口 & 服务可用性")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    p.add_argument(
        "--target",
        action="append",
        default=[],
        help="host:port (repeatable). Example: 127.0.0.1:5500",
    )
    p.add_argument("--timeout", type=float, default=1.5, help="TCP connect timeout seconds.")
    return p


def run(args: argparse.Namespace):
    targets = args.target or []
    if not targets:
        targets = ["127.0.0.1:5500"]

    results: list[dict[str, object]] = []
    ok = 0
    for t in targets:
        if ":" not in t:
            results.append({"target": t, "ok": False, "error": "invalid target, expected host:port"})
            continue
        host, port_s = t.rsplit(":", 1)
        try:
            port = int(port_s)
        except ValueError:
            results.append({"target": t, "ok": False, "error": "invalid port"})
            continue
        latency = tcp_connect_latency_ms(host, port, float(args.timeout))
        is_ok = latency is not None
        if is_ok:
            ok += 1
        results.append({"target": t, "ok": is_ok, "latency_ms": round(latency, 2) if latency is not None else None})

    metrics = {"targets": results, "ok_count": ok, "total": len(results), "success_rate": round(ok / max(1, len(results)), 4)}
    message = None if ok == len(results) else "some targets unavailable"
    return metrics, message, {}


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
