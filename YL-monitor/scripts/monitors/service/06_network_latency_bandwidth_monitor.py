#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import socket
from pathlib import Path

from _common import read_first_line, run_script, tcp_connect_latency_ms, http_get_timing_ms


SCRIPT_ID = "06"
NAME = "网络延迟 & 带宽"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[06] 网络延迟 & 带宽")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return p


def run(args: argparse.Namespace):
    import subprocess
    import time
    
    metrics = {}
    detail = {}
    
    # 1. 获取网络接口统计
    interface_stats = []
    try:
        net_path = Path("/proc/net/dev")
        if net_path.exists():
            with open(net_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or ":" not in line:
                        continue
                    parts = line.split(":")
                    iface = parts[0].strip()
                    if iface in ("lo", "docker0", "br-", "veth"):
                        continue
                    stats = parts[1].strip().split()
                    if len(stats) >= 9:
                        rx_bytes = int(stats[0])
                        tx_bytes = int(stats[8])
                        interface_stats.append({
                            "interface": iface,
                            "rx_mb": round(rx_bytes / (1024 * 1024), 2),
                            "tx_mb": round(tx_bytes / (1024 * 1024), 2),
                        })
    except Exception as e:
        detail["interface_error"] = str(e)
    
    metrics["interfaces"] = interface_stats
    metrics["interface_count"] = len(interface_stats)
    
    # 2. Ping 测试到常用目标
    ping_targets = ["8.8.8.8", "114.114.114.114", "baidu.com"]
    ping_results = []
    
    for target in ping_targets:
        try:
            # 使用 ping 命令测试延迟
            cmd = ["ping", "-c", "1", "-W", "2", target]
            start = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            elapsed = (time.time() - start) * 1000
            
            if result.returncode == 0:
                # 解析 ping 输出中的时间
                output = result.stdout
                time_match = re.search(r"time=([\d.]+)\s*ms", output)
                if time_match:
                    latency = float(time_match.group(1))
                else:
                    latency = round(elapsed, 2)
                ping_results.append({
                    "target": target,
                    "reachable": True,
                    "latency_ms": latency,
                })
            else:
                ping_results.append({
                    "target": target,
                    "reachable": False,
                    "latency_ms": None,
                    "error": "unreachable",
                })
        except subprocess.TimeoutExpired:
            ping_results.append({
                "target": target,
                "reachable": False,
                "latency_ms": None,
                "error": "timeout",
            })
        except Exception as e:
            ping_results.append({
                "target": target,
                "reachable": False,
                "latency_ms": None,
                "error": str(e),
            })
    
    metrics["ping_checks"] = ping_results
    reachable_count = sum(1 for r in ping_results if r.get("reachable"))
    metrics["ping_reachable_count"] = reachable_count
    metrics["ping_total_count"] = len(ping_results)
    
    # 计算平均延迟
    latencies = [r["latency_ms"] for r in ping_results if r.get("latency_ms")]
    if latencies:
        metrics["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
        metrics["min_latency_ms"] = round(min(latencies), 2)
        metrics["max_latency_ms"] = round(max(latencies), 2)
    
    # 3. 检查本地服务端口延迟
    local_ports = [5500, 8080, 3000]
    port_results = []
    for port in local_ports:
        latency = tcp_connect_latency_ms("127.0.0.1", port, 1.0)
        port_results.append({
            "port": port,
            "reachable": latency is not None,
            "latency_ms": round(latency, 2) if latency else None,
        })
    
    metrics["local_port_checks"] = port_results
    
    # 4. 获取路由信息
    try:
        route_result = subprocess.run(
            ["ip", "route", "show"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if route_result.returncode == 0:
            default_route = None
            for line in route_result.stdout.strip().split("\n"):
                if line.startswith("default"):
                    parts = line.split()
                    if "via" in parts:
                        via_idx = parts.index("via")
                        default_route = parts[via_idx + 1]
                        break
            if default_route:
                metrics["default_gateway"] = default_route
                detail["gateway_latency_ms"] = tcp_connect_latency_ms(default_route, 80, 2.0)
    except Exception:
        pass
    
    detail["ping_targets"] = ping_targets
    detail["local_ports_checked"] = local_ports
    
    message = None if reachable_count > 0 else "network connectivity issues detected"
    
    return metrics, message, detail


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
