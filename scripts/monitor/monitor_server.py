#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同源监控服务入口：
- 提供 /monitor/api/* 蓝图接口
- 同时托管 YL-monitor 静态页面（同源联调）

启动：
  python3 scripts/monitor/monitor_server.py
"""

import os
import sys
import time
import uuid
import queue
import threading
import subprocess
from pathlib import Path
from flask import Flask, send_from_directory
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
YL_MONITOR_DIR = PROJECT_ROOT / "YL-monitor"
API_MAP_DIR = PROJECT_ROOT / "api-map"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

MONITOR_ROUTER_PATH = PROJECT_ROOT / "YL-monitor" / "monitor" / "monitor-py" / "monitor_router.py"


def create_app():
    app = Flask(__name__)
    CORS(app)

    # 注册 /monitor/api/* 蓝图
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("monitor_router", MONITOR_ROUTER_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        module.register_routes(app)
    except Exception as exc:
        print(f"[monitor_server] 蓝图注册失败: {exc}")

    # 静态页面托管（同源）
    @app.route("/")
    def index():
        return send_from_directory(YL_MONITOR_DIR, "index/index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        file_path = YL_MONITOR_DIR / path
        if file_path.exists():
            return send_from_directory(YL_MONITOR_DIR, path)
        return ("Not Found", 404)

    # api-map registry & routes
    @app.route("/api-map/<path:path>")
    def serve_api_map(path):
        file_path = API_MAP_DIR / path
        if file_path.exists():
            return send_from_directory(API_MAP_DIR, path)
        return ("Not Found", 404)

    # /api/scripts async runner (queue + cancel)
    script_history = []
    active_jobs = {}
    job_queue = queue.Queue()
    jobs_lock = threading.Lock()

    def record_history(job):
        script_history.append(job)
        if len(script_history) > 200:
            del script_history[:50]

    def list_script_categories():
        categories = {}
        for category_dir in sorted(SCRIPTS_DIR.iterdir()):
            if not category_dir.is_dir():
                continue
            if category_dir.name.startswith("."):
                continue
            scripts = [p.stem for p in category_dir.glob("*.py")]
            if scripts:
                categories[category_dir.name] = {
                    "name": category_dir.name,
                    "icon": "📂",
                    "description": "",
                    "scripts": sorted(scripts)
                }
        return categories

    def build_job_record(job_id, category, name, args):
        return {
            "id": job_id,
            "category": category,
            "name": name,
            "args": args,
            "status": "pending",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "queued_at": time.time(),
            "started_at": None,
            "finished_at": None,
            "duration": None,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "cancel_requested": False
        }

    def run_worker():
        while True:
            job_id = job_queue.get()
            with jobs_lock:
                job = active_jobs.get(job_id)
            if not job:
                job_queue.task_done()
                continue

            if job.get("cancel_requested"):
                job["status"] = "cancelled"
                job["finished_at"] = time.time()
                job["duration"] = 0
                with jobs_lock:
                    active_jobs.pop(job_id, None)
                record_history(job)
                job_queue.task_done()
                continue

            script_path = SCRIPTS_DIR / job["category"] / f"{job['name']}.py"
            if not script_path.exists():
                job["status"] = "failed"
                job["stderr"] = f"script not found: {script_path}"
                job["finished_at"] = time.time()
                job["duration"] = 0
                with jobs_lock:
                    active_jobs.pop(job_id, None)
                record_history(job)
                job_queue.task_done()
                continue

            job["status"] = "running"
            job["started_at"] = time.time()

            process = subprocess.Popen(
                [sys.executable, str(script_path)] + list(job["args"] or []),
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while True:
                if job.get("cancel_requested"):
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    job["status"] = "cancelled"
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.2)

            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()

            job["stdout"] = stdout or ""
            job["stderr"] = stderr or ""
            job["exit_code"] = process.returncode
            job["finished_at"] = time.time()
            job["duration"] = round(job["finished_at"] - job["started_at"], 3)
            job["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

            if job["status"] != "cancelled":
                job["status"] = "success" if process.returncode == 0 else "failed"

            with jobs_lock:
                active_jobs.pop(job_id, None)
            record_history(job)
            job_queue.task_done()

    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()

    @app.route("/api/scripts/categories")
    def scripts_categories():
        return {"success": True, "data": list_script_categories()}

    @app.route("/api/scripts/status")
    def scripts_status():
        with jobs_lock:
            active = []
            for job in active_jobs.values():
                if job["status"] not in ("pending", "running"):
                    continue
                progress = 0 if job["status"] == "pending" else 50
                active.append({
                    "id": job["id"],
                    "name": job["name"],
                    "category": job["category"],
                    "status": job["status"],
                    "progress": progress,
                    "queued_at": job["queued_at"],
                    "started_at": job["started_at"]
                })
        return {
            "success": True,
            "data": {
                "active_scripts": active,
                "queue_length": len([j for j in active if j["status"] == "pending"]),
                "running": len([j for j in active if j["status"] == "running"])
            }
        }

    @app.route("/api/scripts/history")
    def scripts_history():
        return {"success": True, "data": script_history[-50:]}

    @app.route("/api/scripts/cancel", methods=["POST"])
    def scripts_cancel():
        from flask import request
        payload = request.get_json(silent=True) or {}
        job_id = payload.get("job_id") or payload.get("id")
        script_id = payload.get("script_id")

        cancelled = []

        with jobs_lock:
            if job_id and job_id in active_jobs:
                active_jobs[job_id]["cancel_requested"] = True
                cancelled.append(job_id)
            elif script_id:
                for job in active_jobs.values():
                    if f"{job['category']}.{job['name']}" == script_id:
                        job["cancel_requested"] = True
                        cancelled.append(job["id"])

        if not cancelled:
            return {"success": False, "error": "no active job found"}, 404

        return {"success": True, "data": {"cancelled": cancelled}}

    @app.route("/api/scripts/list")
    def scripts_list():
        categories = list_script_categories()
        scripts = []
        for category, meta in categories.items():
            for script_name in meta.get("scripts", []):
                scripts.append({
                    "id": f"{category}.{script_name}",
                    "category": category,
                    "name": script_name.replace("_", " ")
                })
        return {"success": True, "scripts": scripts}

    @app.route("/api/scripts/run", methods=["POST"])
    def scripts_run():
        from flask import request
        payload = request.get_json(silent=True) or {}
        script_id = payload.get("script_id")
        category = payload.get("category")
        name = payload.get("name")
        args = payload.get("args") or []

        if script_id and (not category or not name):
            if "." in script_id:
                category, name = script_id.split(".", 1)

        if not category or not name:
            return {"success": False, "error": "missing category/name"}, 400

        job_id = uuid.uuid4().hex
        job = build_job_record(job_id, category, name, args)
        with jobs_lock:
            active_jobs[job_id] = job
        job_queue.put(job_id)
        return {"success": True, "data": job}

    return app


def main():
    port = int(os.environ.get("PORT", "5000"))
    app = create_app()
    print(f"[monitor_server] http://localhost:{port} (static + /monitor/api)")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
