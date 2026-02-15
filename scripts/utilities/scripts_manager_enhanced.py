#!/usr/bin/env python3
"""增强版 Scripts Manager（线程池示例）"""
import argparse
import concurrent.futures
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class EnhancedScriptManager:
    def __init__(self, max_workers: int = 3):
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def _run(self, cmd):
        return subprocess.run(cmd)

    def run_script_async(self, category: str, name: str, args: list = None):
        args = args or []
        script_path = BASE_DIR / category / f"{name}.py"
        if not script_path.exists():
            raise FileNotFoundError(script_path)
        cmd = [sys.executable, str(script_path)] + args
        return self.pool.submit(self._run, cmd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('category')
    parser.add_argument('name')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    mgr = EnhancedScriptManager(max_workers=args.workers)
    fut = mgr.run_script_async(args.category, args.name)
    res = fut.result()
    print('exit', res.returncode)

if __name__ == '__main__':
    main()
