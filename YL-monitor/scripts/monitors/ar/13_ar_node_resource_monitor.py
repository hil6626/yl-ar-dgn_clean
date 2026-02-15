#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import socket
from pathlib import Path

from _common import read_first_line, run_script, tcp_connect_latency_ms, http_get_timing_ms


SCRIPT_ID = "13"
NAME = "AR 节点状态 & 资源监控"
TYPE = "监控/执行"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[13] AR 节点状态 & 资源监控")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return p


def run(args: argparse.Namespace):
    import subprocess
    import psutil
    import json
    
    metrics = {}
    detail = {}
    
    # 1. 检查 AR 相关进程
    ar_processes = []
    ar_keywords = ["ar_", "arserver", "arcore", "ar_session", "ar_renderer"]
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
        try:
            proc_info = proc.info
            proc_name = proc_info['name'] or ''
            cmdline = ' '.join(proc_info['cmdline'] or [])
            
            # 检查是否匹配 AR 关键词
            is_ar = any(kw in proc_name.lower() or kw in cmdline.lower() for kw in ar_keywords)
            
            if is_ar:
                ar_processes.append({
                    "pid": proc_info['pid'],
                    "name": proc_name,
                    "cpu_percent": round(proc_info['cpu_percent'] or 0, 2),
                    "memory_percent": round(proc_info['memory_percent'] or 0, 2),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    metrics["ar_processes"] = ar_processes
    metrics["ar_process_count"] = len(ar_processes)
    
    # 2. 检查 AR 服务端口
    ar_ports = [8081, 8082, 9090, 9091]  # 常见 AR 服务端口
    port_results = []
    
    for port in ar_ports:
        latency = tcp_connect_latency_ms("127.0.0.1", port, 1.0)
        port_results.append({
            "port": port,
            "reachable": latency is not None,
            "latency_ms": round(latency, 2) if latency else None,
        })
    
    metrics["ar_ports"] = port_results
    metrics["ar_ports_reachable"] = sum(1 for p in port_results if p["reachable"])
    
    # 3. 检查 GPU 资源（如果可用）
    gpu_info = {}
    try:
        # 尝试使用 nvidia-smi
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].split(',')
                if len(parts) >= 3:
                    gpu_info["utilization_pct"] = float(parts[0].strip())
                    gpu_info["memory_used_mb"] = float(parts[1].strip())
                    gpu_info["memory_total_mb"] = float(parts[2].strip())
                    gpu_info["memory_used_pct"] = round(
                        gpu_info["memory_used_mb"] / gpu_info["memory_total_mb"] * 100, 2
                    ) if gpu_info["memory_total_mb"] > 0 else 0
    except Exception:
        pass
    
    if gpu_info:
        metrics["gpu"] = gpu_info
    
    # 4. 检查 AR 会话状态（通过 API）
    ar_session_status = {}
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:5500/api/v1/ar/status", method="GET")
        req.add_header("User-Agent", "YL-Monitor-Check/1.0")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                ar_session_status = json.loads(body)
                ar_session_status["api_reachable"] = True
    except Exception as e:
        ar_session_status["api_reachable"] = False
        ar_session_status["error"] = str(e)
    
    metrics["ar_session"] = ar_session_status
    
    # 5. 检查 AR 资源目录
    ar_dirs = ["app/ar", "data/ar", "static/ar"]
    dir_results = []
    
    for dir_path in ar_dirs:
        dir_info = {"path": dir_path, "exists": False, "file_count": 0, "total_size_mb": 0}
        try:
            from pathlib import Path
            p = Path(dir_path)
            if p.exists():
                dir_info["exists"] = True
                files = list(p.rglob("*"))
                dir_info["file_count"] = len([f for f in files if f.is_file()])
                dir_info["total_size_mb"] = round(
                    sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024), 2
                )
        except Exception as e:
            dir_info["error"] = str(e)
        dir_results.append(dir_info)
    
    metrics["ar_directories"] = dir_results
    metrics["ar_dirs_existing"] = sum(1 for d in dir_results if d["exists"])
    
    # 6. 系统资源概览
    try:
        metrics["system_cpu_percent"] = round(psutil.cpu_percent(interval=0.5), 2)
        metrics["system_memory_percent"] = round(psutil.virtual_memory().percent, 2)
    except Exception:
        pass
    
    detail["ar_keywords_checked"] = ar_keywords
    detail["ar_ports_checked"] = ar_ports
    detail["ar_dirs_checked"] = ar_dirs
    
    # 生成状态消息
    if len(ar_processes) == 0:
        message = "no AR processes detected"
    elif metrics["ar_ports_reachable"] == 0:
        message = "AR service ports not reachable"
    else:
        message = None
    
    return metrics, message, detail


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
