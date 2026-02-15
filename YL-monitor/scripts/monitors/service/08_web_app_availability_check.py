#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import socket
from pathlib import Path

from _common import read_first_line, run_script, tcp_connect_latency_ms, http_get_timing_ms


SCRIPT_ID = "08"
NAME = "Web 应用可用性检测"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[08] Web 应用可用性检测")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return p


def run(args: argparse.Namespace):
    import urllib.request
    import urllib.error
    import time
    
    metrics = {}
    detail = {}
    
    # 检查本地 YL-Monitor 服务
    local_services = [
        {"name": "YL-Monitor Main", "url": "http://127.0.0.1:5500", "endpoint": "/api/v1/dashboard/health"},
        {"name": "YL-Monitor API", "url": "http://127.0.0.1:5500", "endpoint": "/api/v1/health"},
    ]
    
    service_results = []
    ok_count = 0
    
    for svc in local_services:
        full_url = f"{svc['url']}{svc['endpoint']}"
        start = time.time()
        try:
            req = urllib.request.Request(full_url, method="GET")
            req.add_header("User-Agent", "YL-Monitor-Check/1.0")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                elapsed = (time.time() - start) * 1000
                status = resp.status
                body = resp.read(1024).decode("utf-8", errors="replace")
                
                is_ok = 200 <= status < 400
                if is_ok:
                    ok_count += 1
                
                service_results.append({
                    "name": svc["name"],
                    "url": full_url,
                    "status_code": status,
                    "ok": is_ok,
                    "response_time_ms": round(elapsed, 2),
                    "response_preview": body[:200] if body else None,
                })
        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start) * 1000
            service_results.append({
                "name": svc["name"],
                "url": full_url,
                "status_code": e.code,
                "ok": False,
                "response_time_ms": round(elapsed, 2),
                "error": f"HTTP {e.code}",
            })
        except urllib.error.URLError as e:
            elapsed = (time.time() - start) * 1000
            service_results.append({
                "name": svc["name"],
                "url": full_url,
                "status_code": None,
                "ok": False,
                "response_time_ms": round(elapsed, 2),
                "error": str(e.reason),
            })
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            service_results.append({
                "name": svc["name"],
                "url": full_url,
                "status_code": None,
                "ok": False,
                "response_time_ms": round(elapsed, 2),
                "error": str(e),
            })
    
    metrics["services"] = service_results
    metrics["ok_count"] = ok_count
    metrics["total_count"] = len(local_services)
    metrics["success_rate"] = round(ok_count / max(1, len(local_services)), 4)
    
    # 检查静态资源可访问性
    static_checks = []
    static_paths = [
        "/static/css/",
        "/static/js/",
    ]
    
    for path in static_paths:
        url = f"http://127.0.0.1:5500{path}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "YL-Monitor-Check/1.0")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                static_checks.append({
                    "path": path,
                    "accessible": 200 <= resp.status < 400,
                    "status": resp.status,
                })
        except Exception as e:
            static_checks.append({
                "path": path,
                "accessible": False,
                "error": str(e),
            })
    
    metrics["static_resources"] = static_checks
    metrics["static_accessible_count"] = sum(1 for c in static_checks if c.get("accessible"))
    
    # 检查关键页面
    page_checks = []
    pages = [
        {"name": "Dashboard", "path": "/"},
        {"name": "API Docs", "path": "/api/docs"},
        {"name": "Health Check", "path": "/api/v1/health"},
    ]
    
    for page in pages:
        url = f"http://127.0.0.1:5500{page['path']}"
        start = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "YL-Monitor-Check/1.0")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                elapsed = (time.time() - start) * 1000
                page_checks.append({
                    "name": page["name"],
                    "path": page["path"],
                    "status_code": resp.status,
                    "accessible": 200 <= resp.status < 400,
                    "response_time_ms": round(elapsed, 2),
                })
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            page_checks.append({
                "name": page["name"],
                "path": page["path"],
                "accessible": False,
                "error": str(e),
                "response_time_ms": round(elapsed, 2),
            })
    
    metrics["pages"] = page_checks
    metrics["pages_accessible_count"] = sum(1 for p in page_checks if p.get("accessible"))
    
    detail["services_checked"] = [s["name"] for s in local_services]
    detail["pages_checked"] = [p["name"] for p in pages]
    
    message = None if ok_count > 0 else "web application unavailable"
    
    return metrics, message, detail


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
