#!/usr/bin/env python3
"""
YL-Monitor 服务器启动脚本
正确设置Python路径后启动应用
"""

import sys
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.absolute()

# 将项目根目录添加到Python路径
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['PYTHONPATH'] = str(project_root)

# 现在导入并启动应用
from app.main import app
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv('YL_MONITOR_PORT', '5500'))
    host = os.getenv('YL_MONITOR_HOST', '0.0.0.0')
    
    print(f"启动 YL-Monitor 服务器...")
    print(f"访问地址: http://{host}:{port}")
    print(f"项目路径: {project_root}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
