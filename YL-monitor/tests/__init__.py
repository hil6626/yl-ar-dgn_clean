"""
YL-Monitor 测试包

【功能描述】
测试包初始化文件，定义测试共享配置和工具函数

【作者】
AI Assistant

【创建时间】
2026-02-09

【版本】
1.0.0

【依赖】
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
httpx>=0.25.0
websockets>=12.0

【示例】
    # 运行所有测试
    pytest tests/ -v
    
    # 运行特定测试模块
    pytest tests/integration/ -v
    
    # 运行性能测试
    pytest tests/performance/ -v --timeout=300
"""

import sys
from pathlib import Path

# 【添加项目根目录到路径】
# 确保测试可以导入app模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 【测试版本信息】
__version__ = "1.0.0"
__author__ = "AI Assistant"
__created__ = "2026-02-09"
