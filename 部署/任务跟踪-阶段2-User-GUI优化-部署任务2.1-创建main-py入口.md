# 阶段2 - 任务2.1: 创建 main.py 入口 - 详细部署文档

**任务ID:** 2.1  
**任务名称:** 创建 main.py 入口  
**优先级:** P0（阻塞性）  
**预计工时:** 2小时  
**状态:** 待执行  
**前置依赖:** 阶段1完成

---

## 一、任务目标

创建完善的 User GUI 启动入口 main.py，解决模块导入路径问题，确保GUI能正确启动并加载所有依赖。

## 二、部署内容

### 2.1 创建/修改文件清单

| 序号 | 文件路径 | 操作类型 | 说明 |
|------|----------|----------|------|
| 1 | `user/main.py` | 新建/重写 | 主启动入口 |
| 2 | `user/__init__.py` | 新建 | 包初始化 |
| 3 | `user/services/__init__.py` | 新建 | 服务包初始化 |
| 4 | `user/config/__init__.py` | 新建 | 配置包初始化 |
| 5 | `user/config/app_config.yaml` | 新建 | 应用配置 |
| 6 | `user/utils/path_manager.py` | 新建 | 路径管理器 |

### 2.2 详细代码实现

#### 文件1: user/main.py（完整版）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR Live Studio - User GUI 启动入口
主程序入口，处理启动流程、异常处理和日志配置
"""

import os
import sys
import argparse
import logging
import traceback
from pathlib import Path
from datetime import datetime

# ============================================================================
# 路径设置（必须在其他导入之前）
# ============================================================================

def setup_paths():
    """
    设置项目路径
    确保能正确导入所有模块
    """
    # 当前文件目录
    current_dir = Path(__file__).parent.resolve()
    
    # 项目根目录
    project_root = current_dir.parent
    
    # 需要添加到路径的目录
    paths_to_add = [
        str(current_dir),  # user目录
        str(project_root),  # 项目根目录
        str(project_root / 'AR-backend'),  # AR-backend
        str(project_root / 'AR-backend' / 'core'),  # AR-backend核心
        str(project_root / 'AR-backend' / 'services'),  # AR-backend服务
    ]
    
    # 添加到sys.path（避免重复）
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return current_dir, project_root


# 立即设置路径
USER_DIR, PROJECT_ROOT = setup_paths()


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(log_dir: Path, log_level: str = "INFO"):
    """
    配置日志系统
    """
    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件名（带日期）
    log_file = log_dir / f"user_gui_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 文件处理器
            logging.FileHandler(log_file, encoding='utf-8'),
            # 控制台处理器
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置第三方库日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logger = logging.getLogger('Main')
    logger.info(f"日志系统初始化完成: {log_file}")
    
    return logger


# ============================================================================
# 配置加载
# ============================================================================

def load_config(config_dir: Path):
    """
    加载应用配置
    """
    import yaml
    
    config_file = config_dir / 'app_config.yaml'
    default_config = {
        'app': {
            'name': 'AR Live Studio',
            'version': '2.0.0',
            'organization': 'AR Studio Team'
        },
        'gui': {
            'style': 'Fusion',
            'theme': 'dark',
            'window_title': 'AR Live Studio'
        },
        'camera': {
            'default_device': 0,
            'width': 1280,
            'height': 720,
            'fps': 30
        },
        'audio': {
            'sample_rate': 44100,
            'channels': 2
        },
        'monitoring': {
            'enabled': True,
            'report_interval': 30
        }
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # 合并配置
                    def merge_dict(base, update):
                        for key, value in update.items():
                            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                                merge_dict(base[key], value)
                            else:
                                base[key] = value
                    
                    merge_dict(default_config, user_config)
                    logging.getLogger('Main').info(f"配置加载成功: {config_file}")
        except Exception as e:
            logging.getLogger('Main').error(f"加载配置失败: {e}")
    
    return default_config


# ============================================================================
# 环境检查
# ============================================================================

def check_environment():
    """
    检查运行环境
    """
    logger = logging.getLogger('Main')
    checks = {
        'python_version': False,
        'pyqt5': False,
        'opencv': False,
        'numpy': False,
        'project_structure': False
    }
    
    # 检查Python版本
    if sys.version_info >= (3, 8):
        checks['python_version'] = True
        logger.info(f"Python版本: {sys.version}")
    else:
        logger.error(f"Python版本过低: {sys.version}，需要3.8+")
    
    # 检查PyQt5
    try:
        from PyQt5.QtWidgets import QApplication
        checks['pyqt5'] = True
        logger.info("PyQt5: 已安装")
    except ImportError:
        logger.error("PyQt5: 未安装")
        logger.info("安装命令: pip install PyQt5")
    
    # 检查OpenCV
    try:
        import cv2
        checks['opencv'] = True
        logger.info(f"OpenCV: {cv2.__version__}")
    except ImportError:
        logger.error("OpenCV: 未安装")
        logger.info("安装命令: pip install opencv-python")
    
    # 检查NumPy
    try:
        import numpy as np
        checks['numpy'] = True
        logger.info(f"NumPy: {np.__version__}")
    except ImportError:
        logger.error("NumPy: 未安装")
        logger.info("安装命令: pip install numpy")
    
    # 检查项目结构
    required_dirs = ['gui', 'services', 'config']
    missing_dirs = []
    for dir_name in required_dirs:
        if not (USER_DIR / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if not missing_dirs:
        checks['project_structure'] = True
        logger.info("项目结构: 完整")
    else:
        logger.error(f"项目结构: 缺少目录 {missing_dirs}")
    
    # 返回检查结果
    all_passed = all(checks.values())
    if all_passed:
        logger.info("环境检查通过 ✓")
    else:
        logger.error("环境检查失败 ✗")
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            logger.error(f"  {status} {check}")
    
    return all_passed, checks


# ============================================================================
# 异常处理
# ============================================================================

class ExceptionHandler:
    """
    全局异常处理器
    """
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.logger = logging.getLogger('ExceptionHandler')
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        处理未捕获的异常
        """
        # 记录异常
        self.logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # 保存详细错误报告
        error_file = self.log_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"AR Live Studio 错误报告\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"平台: {sys.platform}\n")
            f.write("-" * 60 + "\n")
            f.write("异常详情:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        
        self.logger.error(f"错误报告已保存: {error_file}")
        
        # 显示错误对话框（如果GUI可用）
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            if QApplication.instance():
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("AR Live Studio - 错误")
                msg_box.setText("程序发生错误")
                msg_box.setInformativeText(str(exc_value))
                msg_box.setDetailedText(f"错误报告已保存至:\n{error_file}")
                msg_box.exec_()
        except:
            pass


# ============================================================================
# 主程序
# ============================================================================

def main():
    """
    主函数
    """
    # 创建必要目录
    log_dir = USER_DIR / 'logs'
    config_dir = USER_DIR / 'config'
    data_dir = USER_DIR / 'data'
    
    for dir_path in [log_dir, config_dir, data_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 设置日志
    logger = setup_logging(log_dir)
    logger.info("=" * 60)
    logger.info("AR Live Studio 启动")
    logger.info("=" * 60)
    
    # 设置异常处理
    exception_handler = ExceptionHandler(log_dir)
    sys.excepthook = exception_handler.handle_exception
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AR Live Studio')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--log-level', '-l', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='禁用状态上报')
    parser.add_argument('--test', action='store_true',
                       help='测试模式（不启动GUI）')
    args = parser.parse_args()
    
    # 重新配置日志级别
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # 检查环境
    env_ok, env_checks = check_environment()
    if not env_ok:
        logger.error("环境检查失败，程序退出")
        return 1
    
    # 测试模式
    if args.test:
        logger.info("测试模式，跳过GUI启动")
        return 0
    
    # 加载配置
    config = load_config(config_dir)
    logger.info(f"应用配置: {config['app']['name']} v{config['app']['version']}")
    
    # 禁用监控（如果指定）
    if args.no_monitoring:
        config['monitoring']['enabled'] = False
        logger.info("状态上报已禁用")
    
    # 启动GUI
    try:
        from PyQt5.QtWidgets import QApplication
        from gui.gui import ARApp
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setStyle(config['gui']['style'])
        app.setApplicationName(config['app']['name'])
        app.setApplicationVersion(config['app']['version'])
        app.setOrganizationName(config['app']['organization'])
        
        # 创建主窗口
        logger.info("初始化主窗口...")
        window = ARApp()
        
        # 应用配置
        window.setWindowTitle(config['gui']['window_title'])
        
        # 显示窗口
        window.show()
        logger.info("主窗口已显示")
        
        # 运行应用
        exit_code = app.exec_()
        logger.info(f"应用退出，代码: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"启动GUI失败: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

#### 文件2: user/__init__.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 包初始化
"""

__version__ = "2.0.0"
__author__ = "AR Studio Team"

# 导出入口
from .main import main

__all__ = ['main']
```

#### 文件3: user/services/__init__.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 服务包初始化
"""

from .status_reporter import StatusReporter, get_reporter
from .monitor_client import MonitorClient
from .local_http_server import LocalHTTPServer

__all__ = [
    'StatusReporter',
    'get_reporter',
    'MonitorClient',
    'LocalHTTPServer'
]
```

#### 文件4: user/config/__init__.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User GUI 配置包初始化
"""

import yaml
from pathlib import Path

def load_config(config_name: str = "app_config"):
    """加载配置文件"""
    config_file = Path(__file__).parent / f"{config_name}.yaml"
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    return {}

__all__ = ['load_config']
```

#### 文件5: user/config/app_config.yaml

```yaml
# AR Live Studio - User GUI 应用配置

app:
  name: "AR Live Studio"
  version: "2.0.0"
  organization: "AR Studio Team"
  description: "实时视觉音频处理平台"

# GUI配置
gui:
  style: "Fusion"
  theme: "dark"
  window_title: "AR Live Studio"
  window_width: 1400
  window_height: 900
  min_width: 1200
  min_height: 700

# 摄像头配置
camera:
  default_device: 0
  width: 1280
  height: 720
  fps: 30
  buffer_size: 1

# 音频配置
audio:
  sample_rate: 44100
  channels: 2
  buffer_size: 1024
  format: "float32"

# 人脸合成配置
face:
  models_dir: "models"
  default_model: "default"
  blend_ratio: 0.5

# 监控配置
monitoring:
  enabled: true
  report_interval: 30
  timeout: 5
  max_retries: 3
  local_server_port: 5502

# 日志配置
logging:
  level: "INFO"
  max_file_size: 10485760  # 10MB
  backup_count: 5

# 快捷键配置
shortcuts:
  start_camera: "Ctrl+S"
  stop_camera: "Ctrl+X"
  take_screenshot: "Ctrl+P"
  toggle_fullscreen: "F11"
```

#### 文件6: user/utils/path_manager.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理器
统一管理项目路径，解决导入问题
"""

import sys
from pathlib import Path
from typing import Optional


class PathManager:
    """
    路径管理器（单例）
    """
    
    _instance: Optional['PathManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # 设置基础路径
        self.user_dir = Path(__file__).parent.parent.resolve()
        self.project_root = self.user_dir.parent
        self.ar_backend_dir = self.project_root / 'AR-backend'
        
        # 设置并验证路径
        self._setup_paths()
    
    def _setup_paths(self):
        """设置Python路径"""
        paths_to_add = [
            str(self.user_dir),
            str(self.project_root),
            str(self.ar_backend_dir),
            str(self.ar_backend_dir / 'core'),
            str(self.ar_backend_dir / 'services'),
            str(self.ar_backend_dir / 'integrations'),
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
    
    # 路径属性
    @property
    def user_dir(self) -> Path:
        """User GUI目录"""
        return self._user_dir
    
    @user_dir.setter
    def user_dir(self, value: Path):
        self._user_dir = value
    
    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return self._project_root
    
    @project_root.setter
    def project_root(self, value: Path):
        self._project_root = value
    
    @property
    def ar_backend_dir(self) -> Path:
        """AR-backend目录"""
        return self._ar_backend_dir
    
    @ar_backend_dir.setter
    def ar_backend_dir(self, value: Path):
        self._ar_backend_dir = value
    
    # 常用路径方法
    def get_config_dir(self) -> Path:
        """获取配置目录"""
        return self.user_dir / 'config'
    
    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        return self.user_dir / 'logs'
    
    def get_data_dir(self) -> Path:
        """获取数据目录"""
        return self.user_dir / 'data'
    
    def get_assets_dir(self) -> Path:
        """获取资源目录"""
        return self.user_dir / 'assets'
    
    def get_models_dir(self) -> Path:
        """获取模型目录"""
        return self.ar_backend_dir / 'models'
    
    def ensure_dirs(self):
        """确保必要目录存在"""
        dirs = [
            self.get_config_dir(),
            self.get_logs_dir(),
            self.get_data_dir(),
            self.get_assets_dir(),
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# 全局实例
_path_manager: Optional[PathManager] = None

def get_path_manager() -> PathManager:
    """获取路径管理器实例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager


# 便捷函数
def setup_paths():
    """设置路径（便捷函数）"""
    manager = get_path_manager()
    manager.ensure_dirs()
    return manager
```

## 三、关联内容修复

### 3.1 需要同步修复的文件

| 文件 | 修复内容 | 原因 |
|------|----------|------|
| `user/gui/gui.py` | 修复导入路径 | 使用新的路径管理 |
| `user/README.md` | 更新启动说明 | 文档同步 |

### 3.2 详细修复说明

#### 修复1: user/gui/gui.py

修改导入部分：

```python
# 在文件开头添加
import sys
from pathlib import Path

# 使用路径管理器
user_dir = Path(__file__).parent.parent
if str(user_dir) not in sys.path:
    sys.path.insert(0, str(user_dir))

# 然后导入其他模块
from utils.path_manager import setup_paths
setup_paths()

# 现在可以正常导入
from services.status_reporter import get_reporter
from services.local_http_server import LocalHTTPServer
```

## 四、部署执行步骤

### 4.1 执行前检查

```bash
# 1. 检查当前main.py
cat user/main.py

# 2. 检查目录结构
ls -la user/

# 3. 检查Python版本
python3 --version
```

### 4.2 部署执行

```bash
# 1. 备份原main.py（如果存在）
mv user/main.py user/main.py.backup 2>/dev/null || true

# 2. 创建目录
mkdir -p user/services
mkdir -p user/config
mkdir -p user/utils
mkdir -p user/logs

# 3. 创建__init__.py文件
touch user/__init__.py
touch user/services/__init__.py
touch user/config/__init__.py

# 4. 创建main.py（复制上述代码）

# 5. 创建配置文件（复制上述代码）
# user/config/app_config.yaml

# 6. 创建路径管理器（复制上述代码）
# user/utils/path_manager.py

# 7. 安装依赖
pip install pyyaml

# 8. 测试启动
cd user
python3 main.py --test

# 9. 正常启动
python3 main.py
```

### 4.3 部署验证

```bash
# 1. 测试模式验证
python3 user/main.py --test
# 预期输出: 测试模式，跳过GUI启动

# 2. 环境检查验证
python3 user/main.py --log-level DEBUG
# 检查日志输出中的环境检查结果

# 3. 检查日志文件
ls -la user/logs/

# 4. 验证配置加载
cat user/logs/user_gui_*.log | grep "配置加载"

# 5. 启动GUI（手动验证）
python3 user/main.py
```

## 五、常见问题及解决

### 问题1: 模块导入错误

**现象:** `ModuleNotFoundError: No module named 'gui'`

**解决:**
```python
# 确保路径设置正确
# 在main.py开头检查
print("Python路径:", sys.path)
print("当前目录:", Path.cwd())
```

### 问题2: 配置文件未找到

**现象:** 使用默认配置而非用户配置

**解决:**
```bash
# 检查配置文件路径
ls -la user/config/app_config.yaml

# 检查权限
chmod 644 user/config/app_config.yaml
```

### 问题3: 日志文件未创建

**现象:** logs目录为空

**解决:**
```bash
# 检查目录权限
chmod 755 user/logs

# 检查磁盘空间
df -h
```

## 六、验证清单

- [ ] main.py创建完成
- [ ] __init__.py文件创建完成
- [ ] 路径管理器创建完成
- [ ] 配置文件创建完成
- [ ] 测试模式运行正常
- [ ] 环境检查通过
- [ ] 配置加载正常
- [ ] 日志记录正常
- [ ] GUI能正常启动

## 七、下一步

完成本任务后，继续执行 **任务2.2: 创建路径修复模块**

查看文档: `部署/任务跟踪-阶段2-User-GUI优化-部署任务2.2-创建路径修复模块.md`
