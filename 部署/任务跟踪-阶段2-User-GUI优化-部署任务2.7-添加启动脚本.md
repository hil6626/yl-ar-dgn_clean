# Phase 2 - Task 2.7: Add Startup Script - Detailed Deployment Document

**Task ID:** 2.7  
**Task Name:** Add Startup Script  
**Priority:** P2 (Normal)  
**Estimated Hours:** 2 hours  
**Status:** Pending  
**Prerequisites:** Tasks 2.1, 2.6 completed

---

## I. Task Objectives

Create startup scripts for Linux and Windows to simplify the application launch process.

## II. Deployment Content

### 2.1 File List

| No. | File Path | Type | Description |
|-----|-----------|------|-------------|
| 1 | `user/start.sh` | New | Linux startup script |
| 2 | `user/start.bat` | New | Windows startup script |
| 3 | `user/start.py` | New | Cross-platform startup script |

### 2.2 Detailed Code Implementation

#### File 1: user/start.sh

```bash
#!/bin/bash
# AR Live Studio Startup Script (Linux/Mac)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}AR Live Studio Startup${NC}"
echo "======================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found${NC}"
    exit 1
fi

# Check virtual environment
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip list | grep -q PyQt5 || {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
}

# Check AR-backend
if [ -d "../AR-backend" ]; then
    echo -e "${YELLOW}AR-backend found${NC}"
else
    echo -e "${RED}Warning: AR-backend not found${NC}"
fi

# Start application
echo -e "${GREEN}Starting AR Live Studio...${NC}"
python3 main.py "$@"

echo -e "${GREEN}AR Live Studio exited${NC}"
```

#### File 2: user/start.bat

```batch
@echo off
REM AR Live Studio Startup Script (Windows)

echo AR Live Studio Startup
echo ====================

REM Get script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Check virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check dependencies
echo Checking dependencies...
pip list | findstr "PyQt5" >nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start application
echo Starting AR Live Studio...
python main.py %*

echo AR Live Studio exited
```

#### File 3: user/start.py

```python
#!/usr/bin/env python3
"""
Cross-platform startup script
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        return False
    print(f"Python version: {sys.version}")
    return True


def check_dependencies():
    """Check and install dependencies"""
    required = ['PyQt5', 'opencv-python', 'numpy', 'pyyaml', 'requests']
    
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        
        missing = [pkg for pkg in required if pkg.replace('-', '_') not in installed]
        
        if missing:
            print(f"Installing missing packages: {missing}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        
        return True
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        return False


def setup_environment():
    """Setup environment"""
    script_dir = Path(__file__).parent
    
    # Add to Python path
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    # Check for AR-backend
    ar_backend = script_dir.parent / 'AR-backend'
    if ar_backend.exists():
        print(f"AR-backend found: {ar_backend}")
        if str(ar_backend) not in sys.path:
            sys.path.insert(0, str(ar_backend))
    
    return True


def main():
    """Main function"""
    print("=" * 50)
    print("AR Live Studio Startup")
    print("=" * 50)
    
    # Check Python
    if not check_python():
        return 1
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Start application
    print("Starting application...")
    
    try:
        from main import main as app_main
        return app_main()
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

## III. Deployment Steps

```bash
# 1. Create scripts
# user/start.sh
# user/start.bat
# user/start.py

# 2. Add execute permission (Linux/Mac)
chmod +x user/start.sh

# 3. Test startup
cd user
./start.sh --test

# Or use Python script
python3 start.py
```

## IV. Verification Checklist

- [ ] Linux script works
- [ ] Windows script works
- [ ] Dependency check normal
- [ ] Error handling effective
- [ ] Cross-platform compatible

## V. Next Step

After completing this task, proceed to **Task 2.8: Functional Verification Testing**

View document: `部署/任务跟踪-阶段2-User-GUI优化-部署任务2.8-功能验证测试.md`
