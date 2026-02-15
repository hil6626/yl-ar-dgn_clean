#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    return str(obj)


def print_result(payload: dict[str, Any], *, pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
    else:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=_json_default))


@dataclass
class ScriptResult:
    id: str
    name: str
    type: str
    status: str
    timestamp: str = field(default_factory=iso_utc_now)
    host: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    message: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def base_parser(*, description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return p


def host_facts() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "pid": os.getpid(),
    }


def run_script(
    *,
    script_id: str,
    name: str,
    type_: str,
    build_parser: Callable[[], argparse.ArgumentParser],
    run: Callable[[argparse.Namespace], tuple[dict[str, Any], str | None, dict[str, Any]]],
) -> None:
    parser = build_parser()
    args = parser.parse_args()

    started = time.time()
    try:
        metrics, message, detail = run(args)
        payload = ScriptResult(
            id=script_id,
            name=name,
            type=type_,
            status="ok",
            host=host_facts(),
            metrics=metrics,
            message=message,
            detail={
                **detail,
                "duration_ms": int((time.time() - started) * 1000),
            },
        )
        print_result(asdict(payload), pretty=bool(getattr(args, "pretty", False)))
        raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        payload = ScriptResult(
            id=script_id,
            name=name,
            type=type_,
            status="error",
            host=host_facts(),
            metrics={},
            message=str(exc),
            detail={
                "traceback": traceback.format_exc(limit=30),
                "duration_ms": int((time.time() - started) * 1000),
            },
        )
        pretty = bool(getattr(args, "pretty", False)) if "args" in locals() else True
        print_result(asdict(payload), pretty=pretty)
        raise SystemExit(2)


def read_first_line(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None


def tcp_connect_latency_ms(host: str, port: int, timeout_s: float) -> float | None:
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return (time.time() - start) * 1000.0
    except OSError:
        return None


def http_get_timing_ms(url: str, timeout_s: float) -> dict[str, Any]:
    # Use stdlib tooling as much as possible; curl provides better timing, so prefer it if available.
    if shutil_which("curl"):
        # curl timing: %{time_connect} %{time_starttransfer} %{time_total} (seconds)
        cmd = [
            "curl",
            "-sS",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code} %{time_connect} %{time_starttransfer} %{time_total}",
            "--max-time",
            str(timeout_s),
            url,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        out = (proc.stdout or "").strip()
        parts = out.split()
        if len(parts) == 4 and parts[0].isdigit():
            return {
                "http_code": int(parts[0]),
                "connect_ms": float(parts[1]) * 1000.0,
                "ttfb_ms": float(parts[2]) * 1000.0,
                "total_ms": float(parts[3]) * 1000.0,
                "tool": "curl",
            }
        return {"tool": "curl", "raw": out, "stderr": (proc.stderr or "").strip()}

    # Fallback: very coarse timing with urllib
    import urllib.request

    start = time.time()
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            _ = resp.read(1024)
            total_ms = (time.time() - start) * 1000.0
            return {"http_code": int(getattr(resp, "status", 0) or 0), "total_ms": total_ms, "tool": "urllib"}
    except Exception as exc:  # noqa: BLE001
        total_ms = (time.time() - start) * 1000.0
        return {"error": str(exc), "total_ms": total_ms, "tool": "urllib"}


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)

