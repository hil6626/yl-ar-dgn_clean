# 编码规范

**版本:** 1.0.0  
**最后更新:** 2026-02-16  
**适用范围:** YL-AR-DGN 项目所有代码

---

## 📋 目录

1. [Python 编码规范](#python-编码规范)
2. [项目结构规范](#项目结构规范)
3. [命名规范](#命名规范)
4. [注释规范](#注释规范)
5. [错误处理规范](#错误处理规范)
6. [日志规范](#日志规范)
7. [测试规范](#测试规范)

---

## Python 编码规范

### 代码风格

**遵循 PEP 8**

```python
# ✅ 正确的缩进（4个空格）
def example_function():
    if True:
        print("正确")

# ❌ 错误的缩进（Tab或2个空格）
def example_function():
  if True:
    print("错误")
```

**行长度**
```python
# ✅ 每行不超过100字符
def long_function_name(
        param_one, param_two, param_three,
        param_four, param_five):
    pass

# ❌ 超过100字符
def long_function_name(param_one, param_two, param_three, param_four, param_five, param_six, param_seven):
    pass
```

**导入顺序**
```python
# 1. 标准库
import os
import sys
from pathlib import Path

# 2. 第三方库
import numpy as np
import cv2
from fastapi import FastAPI

# 3. 本地模块
from core.path_manager import PathManager
from services.ar_backend_client import ARBackendClient
```

---

## 项目结构规范

### 目录结构

```
组件目录/
├── README.md              # 组件说明
├── main.py               # 入口文件
├── config/               # 配置文件
│   ├── settings.py
│   └── config.yaml
├── core/                 # 核心模块
│   ├── __init__.py
│   └── processor.py
├── services/             # 服务层
│   ├── __init__.py
│   └── client.py
├── utils/                # 工具函数
│   ├── __init__.py
│   └── helpers.py
├── tests/                # 测试代码
│   ├── __init__.py
│   └── test_*.py
└── logs/                 # 日志目录
    └── app.log
```

### 文件组织

**每个Python文件应包含**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块简短描述

详细描述，说明模块的功能、用途和主要类/函数。
"""

# 1. 导入（按规范顺序）
import os
import sys

import numpy as np

from core.module import SomeClass

# 2. 常量定义（大写）
DEFAULT_PORT = 5500
MAX_RETRY = 3

# 3. 类定义
class MyClass:
    """类文档字符串"""
    pass

# 4. 函数定义
def my_function():
    """函数文档字符串"""
    pass

# 5. 主程序入口
if __name__ == "__main__":
    main()
```

---

## 命名规范

### 变量命名

| 类型 | 规范 | 示例 |
|------|------|------|
| **变量** | 小写 + 下划线 | `user_name`, `port_number` |
| **常量** | 大写 + 下划线 | `DEFAULT_PORT`, `MAX_RETRY` |
| **类** | 大驼峰 | `PathManager`, `ARBackendClient` |
| **函数** | 小写 + 下划线 | `get_status()`, `process_frame()` |
| **私有** | 单下划线前缀 | `_internal_var`, `_helper_func` |
| **保护** | 单下划线前缀 | `_protected_method()` |
| **私有类属性** | 双下划线前缀 | `__private_attr` |

### 示例

```python
# ✅ 正确的命名
DEFAULT_TIMEOUT = 30  # 常量

class FaceProcessor:  # 类
    def __init__(self):
        self.model_path = "models/face.pth"  # 实例变量
        self._is_loaded = False  # 保护属性
    
    def process_frame(self, frame):  # 方法
        """处理单帧图像"""
        pass

def load_face_model(model_path):  # 函数
    """加载人脸模型"""
    pass

# ❌ 错误的命名
defaultTimeout = 30  # 驼峰命名常量
class faceProcessor:  # 小写类名
    def ProcessFrame(self, Frame):  # 大写方法名
        pass
```

---

## 注释规范

### 文档字符串（Docstring）

**所有模块、类、函数必须有文档字符串**

```python
def process_video(
    input_path: str,
    output_path: str,
    fps: int = 30,
    quality: str = "high"
) -> bool:
    """
    处理视频文件，应用人脸合成效果。
    
    Args:
        input_path (str): 输入视频文件路径
        output_path (str): 输出视频文件路径
        fps (int, optional): 输出帧率，默认30
        quality (str, optional): 输出质量，可选 "low", "medium", "high"
    
    Returns:
        bool: 处理成功返回True，失败返回False
    
    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 参数无效
    
    Example:
        >>> process_video("input.mp4", "output.mp4", fps=24, quality="medium")
        True
    """
    pass
```

### 行内注释

```python
# ✅ 好的注释：解释"为什么"而不是"是什么"
x = x + 1  # 补偿边界框的偏移量

# ❌ 差的注释：重复代码 obvious 的内容
x = x + 1  # x增加1
```

### TODO 注释

```python
# TODO(username): 描述待办事项，包含截止日期
# TODO(alice): 优化人脸检测算法，截止日期 2026-03-01

# FIXME: 标记需要修复的问题
# FIXME: 内存泄漏问题，需要调查

# NOTE: 重要说明
# NOTE: 此函数线程不安全，需要外部加锁
```

---

## 错误处理规范

### 异常处理原则

**1. 捕获具体异常，不要捕获所有异常**

```python
# ✅ 好的做法
try:
    result = int(user_input)
except ValueError:
    logger.error(f"无效的输入: {user_input}")
    return None

# ❌ 差的做法
try:
    result = int(user_input)
except:  # 捕获所有异常，包括 KeyboardInterrupt
    pass
```

**2. 使用自定义异常**

```python
class YLARException(Exception):
    """YL-AR-DGN 项目基础异常"""
    pass

class ServiceNotFoundError(YLARException):
    """服务未找到异常"""
    pass

class ProcessingError(YLARException):
    """处理错误异常"""
    pass

# 使用
def connect_to_service(host, port):
    if not check_port_open(host, port):
        raise ServiceNotFoundError(f"服务未运行: {host}:{port}")
```

**3. 异常链**

```python
try:
    process_frame(frame)
except cv2.error as e:
    # 保留原始异常信息
    raise ProcessingError(f"图像处理失败: {e}") from e
```

**4. 资源清理**

```python
# ✅ 使用上下文管理器
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ✅ 使用 try-finally
camera = cv2.VideoCapture(0)
try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        process_frame(frame)
finally:
    camera.release()  # 确保释放资源
```

---

## 日志规范

### 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(
    log_file: str = "logs/app.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    配置日志系统。
    
    Args:
        log_file: 日志文件路径
        level: 日志级别
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger("yl-ar-dgn")
    logger.setLevel(level)
    
    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # 文件处理器（轮转）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
```

### 日志级别使用

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| **DEBUG** | 调试信息，详细流程 | `logger.debug(f"处理帧: {frame_id}")` |
| **INFO** | 正常操作信息 | `logger.info("服务启动成功")` |
| **WARNING** | 警告，非致命问题 | `logger.warning("内存使用率超过80%")` |
| **ERROR** | 错误，功能受影响 | `logger.error("模型加载失败")` |
| **CRITICAL** | 严重错误，系统可能崩溃 | `logger.critical("无法访问摄像头")` |

### 日志内容规范

```python
# ✅ 好的日志：包含上下文信息
logger.info(f"人脸模型加载成功: {model_path}, 大小: {model_size}MB, 耗时: {load_time:.2f}s")

# ❌ 差的日志：信息不足
logger.info("模型加载成功")
```

---

## 测试规范

### 测试文件组织

```
tests/
├── __init__.py
├── conftest.py          # pytest 配置和fixture
├── unit/                # 单元测试
│   ├── test_path_manager.py
│   ├── test_ar_backend_client.py
│   └── test_settings.py
├── integration/         # 集成测试
│   ├── test_monitor_integration.py
│   └── test_gui_integration.py
└── e2e/                 # 端到端测试
    └── test_full_workflow.py
```

### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch

from user.core.path_manager import PathManager


class TestPathManager:
    """PathManager 测试类"""
    
    @pytest.fixture
    def path_manager(self):
        """创建 PathManager 实例"""
        return PathManager()
    
    def test_find_project_root(self, path_manager):
        """测试查找项目根目录"""
        root = path_manager._find_project_root()
        assert root is not None
        assert (root / "README.md").exists()
    
    def test_setup_python_path(self, path_manager):
        """测试设置 Python 路径"""
        with patch('sys.path', []) as mock_path:
            path_manager.setup_python_path()
            assert len(mock_path) > 0
            assert any("AR-backend" in p for p in mock_path)
    
    def test_setup_paths_with_invalid_root(self, path_manager):
        """测试无效根目录的情况"""
        with patch.object(path_manager, '_find_project_root', return_value=None):
            with pytest.raises(RuntimeError):
                path_manager.setup_python_path()
```

### 测试命名规范

```python
# 测试函数命名
def test_<被测对象>_<测试场景>_<预期结果>():
    pass

# 示例
def test_ar_backend_client_health_check_success():
    """ARBackendClient 健康检查 - 服务正常 - 返回健康状态"""
    pass

def test_ar_backend_client_health_check_timeout():
    """ARBackendClient 健康检查 - 连接超时 - 返回不健康状态"""
    pass
```

### Mock 使用规范

```python
# ✅ 使用 patch 装饰器
@patch('requests.get')
def test_health_check(mock_get):
    mock_get.return_value.json.return_value = {"status": "healthy"}
    result = client.health_check()
    assert result["status"] == "healthy"

# ✅ 使用上下文管理器
def test_with_context_manager():
    with patch('cv2.VideoCapture') as mock_cap:
        mock_cap.return_value.isOpened.return_value = True
        # 测试代码
```

---

## 代码审查清单

提交代码前，请确认以下事项：

- [ ] 代码遵循 PEP 8 规范
- [ ] 所有函数和类都有文档字符串
- [ ] 复杂的逻辑有适当的注释
- [ ] 错误处理完善，没有裸 except
- [ ] 日志记录适当，没有敏感信息泄露
- [ ] 单元测试覆盖新增代码
- [ ] 所有测试通过 (`pytest`)
- [ ] 代码风格检查通过 (`flake8`, `black`)
- [ ] 类型检查通过 (`mypy`)

---

## 工具推荐

| 工具 | 用途 | 命令 |
|------|------|------|
| **black** | 代码格式化 | `black .` |
| **flake8** | 代码风格检查 | `flake8 .` |
| **mypy** | 类型检查 | `mypy .` |
| **pylint** | 代码质量检查 | `pylint src/` |
| **pytest** | 测试运行 | `pytest` |
| **isort** | 导入排序 | `isort .` |

---

## 示例代码

完整的规范示例见项目中的以下文件：
- `user/core/path_manager.py` - 类设计和文档字符串
- `user/services/ar_backend_client.py` - 错误处理和日志
- `AR-backend/monitor_server.py` - API 设计和错误处理

---

**最后更新:** 2026-02-16  
**维护者:** YL-AR-DGN 项目团队
