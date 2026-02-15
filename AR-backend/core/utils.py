"""
公共工具函数模块
提供项目中常用的工具函数和辅助类
"""

import os
import sys
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import cv2
import numpy as np


def setup_logging(log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    设置日志配置

    Args:
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        logging.Logger: 配置好的日志器
    """
    # 创建日志器
    logger = logging.getLogger('ar_live_studio')
    logger.setLevel(getattr(logging, level.upper()))

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        ensure_dir(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def ensure_dir(dir_path: str) -> None:
    """
    确保目录存在，如果不存在则创建

    Args:
        dir_path: 目录路径
    """
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载JSON配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        Dict[str, Any]: 配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败 {config_path}: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """
    保存配置到JSON文件

    Args:
        config: 配置字典
        config_path: 配置文件路径

    Returns:
        bool: 保存是否成功
    """
    try:
        ensure_dir(os.path.dirname(config_path))
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置文件失败 {config_path}: {e}")
        return False


def get_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
    """
    计算文件哈希值

    Args:
        file_path: 文件路径
        algorithm: 哈希算法 ('md5', 'sha256')

    Returns:
        Optional[str]: 文件哈希值
    """
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        print(f"计算文件哈希失败 {file_path}: {e}")
        return None


def get_image_info(image_path: str) -> Optional[Dict[str, Any]]:
    """
    获取图像文件信息

    Args:
        image_path: 图像文件路径

    Returns:
        Optional[Dict[str, Any]]: 图像信息
    """
    try:
        if not os.path.exists(image_path):
            return None

        image = cv2.imread(image_path)
        if image is None:
            return None

        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        file_size = os.path.getsize(image_path)

        return {
            'path': image_path,
            'width': width,
            'height': height,
            'channels': channels,
            'file_size': file_size,
            'format': os.path.splitext(image_path)[1].lower()
        }
    except Exception as e:
        print(f"获取图像信息失败 {image_path}: {e}")
        return None


def resize_image(image: np.ndarray, target_size: Tuple[int, int],
                keep_aspect_ratio: bool = True) -> np.ndarray:
    """
    调整图像大小

    Args:
        image: 输入图像
        target_size: 目标尺寸 (width, height)
        keep_aspect_ratio: 是否保持宽高比

    Returns:
        np.ndarray: 调整后的图像
    """
    try:
        if keep_aspect_ratio:
            h, w = image.shape[:2]
            target_w, target_h = target_size

            # 计算缩放比例
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)

            # 缩放图像
            resized = cv2.resize(image, (new_w, new_h))

            # 创建目标尺寸的画布
            canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)

            # 将缩放后的图像居中放置
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

            return canvas
        else:
            return cv2.resize(image, target_size)

    except Exception as e:
        print(f"调整图像大小失败: {e}")
        return image


def validate_image_file(file_path: str, max_size_mb: float = 10.0,
                       allowed_formats: List[str] = None) -> Tuple[bool, str]:
    """
    验证图像文件

    Args:
        file_path: 文件路径
        max_size_mb: 最大文件大小(MB)
        allowed_formats: 允许的文件格式

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    if allowed_formats is None:
        allowed_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"

        # 检查文件大小
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"文件过大: {file_size_mb:.2f}MB (最大{max_size_mb}MB)"

        # 检查文件格式
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in allowed_formats:
            return False, f"不支持的文件格式: {ext}"

        # 尝试读取图像
        image = cv2.imread(file_path)
        if image is None:
            return False, "无法读取图像文件"

        return True, "验证通过"

    except Exception as e:
        return False, f"验证失败: {e}"


def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息

    Returns:
        Dict[str, Any]: 系统信息
    """
    try:
        import platform
        import psutil

        return {
            'platform': platform.platform(),
            'python_version': sys.version,
            'cpu_count': os.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/')._asdict()
        }
    except ImportError:
        # 如果没有psutil，使用基本信息
        return {
            'platform': platform.platform(),
            'python_version': sys.version,
            'cpu_count': os.cpu_count()
        }


def format_timestamp(timestamp: Optional[float] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳

    Args:
        timestamp: 时间戳（None表示当前时间）
        format_str: 格式字符串

    Returns:
        str: 格式化的时间字符串
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)

    return dt.strftime(format_str)


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误

    Args:
        a: 被除数
        b: 除数
        default: 默认值

    Returns:
        float: 除法结果
    """
    try:
        return a / b if b != 0 else default
    except (ZeroDivisionError, TypeError):
        return default


class Timer:
    """计时器类"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = datetime.now()

    def stop(self) -> float:
        """
        停止计时

        Returns:
            float: 耗时（秒）
        """
        self.end_time = datetime.now()
        if self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def get_elapsed(self) -> float:
        """
        获取已耗时

        Returns:
            float: 已耗时（秒）
        """
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0


# 全局配置
DEFAULT_CONFIG = {
    'camera': {
        'device_id': 0,
        'width': 1920,
        'height': 1080,
        'fps': 30
    },
    'face_synthesis': {
        'method': 'deepfacelab',
        'model_path': None
    },
    'audio': {
        'sample_rate': 44100,
        'channels': 2
    },
    'logging': {
        'level': 'INFO',
        'file': 'logs/ar_live_studio.log'
    }
}
