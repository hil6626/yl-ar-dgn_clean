#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import socket
from pathlib import Path

from _common import read_first_line, run_script, tcp_connect_latency_ms, http_get_timing_ms


SCRIPT_ID = "09"
NAME = "数据库连接 & 查询监控"
TYPE = "监控"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"[09] 数据库连接 & 查询监控")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return p


def run(args: argparse.Namespace):
    import sqlite3
    import time
    from pathlib import Path
    
    metrics = {}
    detail = {}
    
    # 数据库配置
    db_paths = [
cd /home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean/YL-monitor && ls -la app/auth/*.py
        "data/metrics.db",
        "data/alerts.db", 
        "data/app.db",
    ]
    
    db_results = []
    connected_count = 0
    query_ok_count = 0
    
    for db_path in db_paths:
        db_file = Path(db_path)
        db_info = {
            "path": db_path,
            "exists": db_file.exists(),
            "size_mb": None,
            "connected": False,
            "query_ok": False,
            "tables": [],
            "error": None,
        }
        
        if not db_file.exists():
            db_info["error"] = "database file not found"
            db_results.append(db_info)
            continue
        
        # 获取文件大小
        try:
            db_info["size_mb"] = round(db_file.stat().st_size / (1024 * 1024), 2)
        except Exception as e:
            db_info["size_error"] = str(e)
        
        # 测试连接
        conn = None
        try:
            conn = sqlite3.connect(str(db_file), timeout=5.0)
            conn.execute("PRAGMA quick_check")
            db_info["connected"] = True
            connected_count += 1
            
            # 获取表列表
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            db_info["tables"] = tables
            db_info["table_count"] = len(tables)
            
            # 执行简单查询测试
            start = time.time()
            conn.execute("SELECT 1")
            elapsed = (time.time() - start) * 1000
            db_info["query_time_ms"] = round(elapsed, 2)
            db_info["query_ok"] = True
            query_ok_count += 1
            
        except sqlite3.Error as e:
            db_info["error"] = f"sqlite error: {str(e)}"
        except Exception as e:
            db_info["error"] = str(e)
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
        
        db_results.append(db_info)
    
    metrics["databases"] = db_results
    metrics["db_exists_count"] = sum(1 for d in db_results if d["exists"])
    metrics["db_connected_count"] = connected_count
    metrics["db_query_ok_count"] = query_ok_count
    metrics["total_dbs"] = len(db_paths)
    
    # 检查数据库目录
    data_dir = Path("data")
    if data_dir.exists():
        try:
            db_files = list(data_dir.glob("*.db"))
            metrics["data_dir_db_count"] = len(db_files)
            metrics["data_dir_total_size_mb"] = round(
                sum(f.stat().st_size for f in db_files if f.exists()) / (1024 * 1024), 2
            )
        except Exception as e:
            detail["data_dir_error"] = str(e)
    
    # SQLite 版本信息
    try:
        metrics["sqlite_version"] = sqlite3.sqlite_version
    except:
        pass
    
    detail["db_paths_checked"] = db_paths
    
    # 生成状态消息
    if connected_count == 0 and metrics["db_exists_count"] > 0:
        message = "database connection failed"
    elif query_ok_count < connected_count:
        message = "some database queries failed"
    else:
        message = None
    
    return metrics, message, detail


if __name__ == "__main__":
    run_script(script_id=SCRIPT_ID, name=NAME, type_=TYPE, build_parser=build_parser, run=run)
