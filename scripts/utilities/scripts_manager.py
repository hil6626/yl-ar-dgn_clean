#!/usr/bin/env python3
"""简化版 Scripts Manager
用于在新位置运行脚本的轻量调度示例
"""
import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class ScriptManager:
    def __init__(self):
        pass

    def run_script(self, category: str, name: str, args: list = None):
        args = args or []
        script_path = BASE_DIR / category / f"{name}.py"
        if not script_path.exists():
            raise FileNotFoundError(f"脚本未找到: {script_path}")
        cmd = [sys.executable, str(script_path)] + args
        return subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('category')
    parser.add_argument('name')
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    mgr = ScriptManager()
    res = mgr.run_script(args.category, args.name, args.args)
    print('exit', res.returncode)

if __name__ == '__main__':
    main()
