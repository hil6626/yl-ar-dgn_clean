#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 启动入口 (优化版)
使用路径管理器和配置系统
"""

import sys
import logging
from pathlib import Path

# 首先设置路径（必须在其他导入之前）
from core.path_manager import setup_paths
setup_paths()

# 现在可以安全地导入其他模块
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.gui import ARApp
from config.settings import get_config


def setup_logging():
    """设置日志"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'user_gui.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('UserGUI')


def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("User GUI 启动中...")
    logger.info("=" * 50)
    
    try:
        # 加载配置
        config = get_config()
        logger.info(f"配置加载完成: {config.config_path}")
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        app.setApplicationName("AR Live Studio")
        app.setApplicationVersion("2.1.0")
        
        # 创建主窗口
        window = ARApp()
        window.show()
        
        logger.info("User GUI 启动成功")
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "启动错误",
            f"应用程序启动失败:\n{str(e)}\n\n请检查日志: logs/user_gui.log"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
