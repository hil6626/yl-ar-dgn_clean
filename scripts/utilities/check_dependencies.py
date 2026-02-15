#!/usr/bin/env python3
"""依赖检查包装器（轻量）"""
import importlib
import sys
from pathlib import Path

REQS = ['psutil', 'requests']

def main():
    missing = []
    for r in REQS:
        try:
            importlib.import_module(r)
        except Exception:
            missing.append(r)
    if missing:
        print('Missing packages:', missing)
        sys.exit(2)
    print('All required packages installed')

if __name__ == '__main__':
    main()
