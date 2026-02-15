#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test utilities for path resolution, imports, and HTTP helpers.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import requests


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    backend_core: Path
    backend_services: Path
    backend_integrations: Path
    monitor_root: Path
    monitor_py: Path
    scripts: Path
    test_dir: Path


def _candidate_roots(start: Path) -> Iterable[Path]:
    yield start
    yield from start.parents


def find_project_root(start: Optional[Path] = None) -> Path:
    """Find project root by scanning parents for expected directories."""
    start = (start or Path(__file__)).resolve()
    for candidate in _candidate_roots(start):
        if (candidate / "AR-backend").exists() and (candidate / "YL-monitor").exists():
            return candidate
        if (candidate / "AR-backend").exists() and (candidate / "test").exists():
            return candidate
    # Fallback to two levels up from this file.
    return start.parents[1]


def build_project_paths(root: Optional[Path] = None) -> ProjectPaths:
    root = (root or find_project_root()).resolve()
    return ProjectPaths(
        root=root,
        backend_core=root / "AR-backend" / "core",
        backend_services=root / "AR-backend" / "services",
        backend_integrations=root / "AR-backend" / "integrations",
        monitor_root=root / "YL-monitor",
        monitor_py=root / "YL-monitor" / "monitor" / "monitor-py",
        scripts=root / "scripts",
        test_dir=root / "test",
    )


def add_sys_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path and path.exists():
        sys.path.insert(0, path_str)


def add_project_paths(root: Optional[Path] = None) -> ProjectPaths:
    paths = build_project_paths(root)
    add_sys_path(paths.root)
    add_sys_path(paths.backend_core)
    add_sys_path(paths.backend_services)
    add_sys_path(paths.backend_integrations)
    add_sys_path(paths.monitor_root)
    add_sys_path(paths.monitor_py)
    add_sys_path(paths.scripts)
    add_sys_path(paths.test_dir)
    return paths


def get_base_url() -> str:
    return os.environ.get("AR_TEST_BASE_URL", "http://0.0.0.0:5500").rstrip("/")


def get_requests_session(timeout: float = 5.0) -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    def _request(method, url, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return requests.Session.request(session, method, url, **kwargs)

    session.request = _request  # type: ignore[assignment]
    return session


def is_http_available(url: str, timeout: float = 2.0) -> bool:
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code < 500
    except Exception:
        return False


def resolve_monitor_api_prefix(base_url: Optional[str] = None) -> str:
    base_url = (base_url or get_base_url()).rstrip("/")
    candidates = [
        "/monitor/api",
        "/api",
        "",
    ]
    for prefix in candidates:
        health_path = f"{base_url}{prefix}/health" if prefix else f"{base_url}/health"
        if is_http_available(health_path):
            return prefix
    return "/monitor/api"


def import_create_app(paths: Optional[ProjectPaths] = None) -> Callable[[], object]:
    """Find a create_app callable from known monitor entrypoints."""
    paths = paths or add_project_paths()
    candidates = [
        paths.monitor_root / "main.py",
        paths.scripts / "monitor" / "monitor_server.py",
        paths.scripts / "monitor" / "monitor_router.py",
        paths.scripts / "monitor" / "monitor_router_refactored.py",
    ]

    for file_path in candidates:
        if not file_path.exists():
            continue
        module_name = f"test_dynamic_{file_path.stem}"
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[call-arg]
            if hasattr(module, "create_app"):
                return getattr(module, "create_app")
        except Exception:
            continue

    raise RuntimeError("Unable to locate a create_app() entrypoint.")


def require_server(base_url: Optional[str] = None, prefix: Optional[str] = None) -> bool:
    base_url = (base_url or get_base_url()).rstrip("/")
    prefix = resolve_monitor_api_prefix(base_url) if prefix is None else prefix
    if prefix:
        return is_http_available(f"{base_url}{prefix}/health")
    return is_http_available(f"{base_url}/health")


def resolve_api_prefix_with_client(client, candidates: Optional[Iterable[str]] = None) -> str:
    candidates = candidates or ["/monitor/api", "/api", "/api/v1", ""]
    for prefix in candidates:
        path = f"{prefix}/health" if prefix else "/health"
        try:
            resp = client.get(path)
            if resp.status_code == 200:
                return prefix
        except Exception:
            continue
    return ""
