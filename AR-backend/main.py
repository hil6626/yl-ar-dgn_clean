"""
AR Live Studio - 主程序入口
启动PyQt5图形界面应用程序
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """
    主函数：启动AR Live Studio应用程序
    """
    parser = argparse.ArgumentParser(description='AR Live Studio')
    parser.add_argument(
        '--monitor-only',
        action='store_true',
        help='仅启动监控服务'
    )
    args = parser.parse_args()
    
    if args.monitor_only:
        # 仅启动监控服务
        from monitor_server import app
        app.run(host='0.0.0.0', port=5501, threaded=True)
    else:
        # 启动完整GUI
        from PyQt5.QtWidgets import QApplication
        from gui import ARApp
        
        app = QApplication(sys.argv)
        window = ARApp()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
