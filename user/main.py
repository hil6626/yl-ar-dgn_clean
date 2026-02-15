#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 启动入口
"""

import sys
import os
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'AR-backend'))
sys.path.insert(0, str(project_root / 'AR-backend' / 'core'))

# 创建必要的目录
(Path(__file__).parent / 'logs').mkdir(exist_ok=True)
(Path(__file__).parent / 'config').mkdir(exist_ok=True)

from PyQt5.QtWidgets import QApplication
from gui.gui import ARApp


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("AR Live Studio")
    app.setApplicationVersion("2.0.0")
    
    # 创建主窗口
    window = ARApp()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
