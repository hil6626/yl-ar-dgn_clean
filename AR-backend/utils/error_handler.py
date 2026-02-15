#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR-backend 统一异常处理模块
提供全局异常捕获、错误分类、用户友好的错误提示

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import sys
import traceback
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict, List
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """错误码枚举"""
    # 系统级错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    SYSTEM_ERROR = 1001
    INITIALIZATION_ERROR = 1002
    CONFIGURATION_ERROR = 1003
    
    # 摄像头错误 (2000-2999)
    CAMERA_NOT_FOUND = 2000
    CAMERA_PERMISSION_DENIED = 2001
    CAMERA_INIT_FAILED = 2002
    CAMERA_DISCONNECTED = 2003
    
    # 人脸合成错误 (3000-3999)
    FACE_DETECTION_FAILED = 3000
    FACE_SWAP_FAILED = 3001
    MODEL_NOT_FOUND = 3002
    MODEL_LOAD_FAILED = 3003
    
    # 音频错误 (4000-4999)
    AUDIO_DEVICE_NOT_FOUND = 4000
    AUDIO_INIT_FAILED = 4001
    SOX_NOT_INSTALLED = 4002
    
    # 文件错误 (5000-5999)
    FILE_NOT_FOUND = 5000
    FILE_READ_ERROR = 5001
    FILE_WRITE_ERROR = 5002
    INVALID_FILE_FORMAT = 5003
    
    # 网络错误 (6000-6999)
    NETWORK_ERROR = 6000
    CONNECTION_TIMEOUT = 6001
    API_ERROR = 6002


class ARError(Exception):
    """AR系统基础异常类"""
    
    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'error_code': self.code.value,
            'error_name': self.code.name,
            'message': self.message,
            'details': self.details
        }
    
    def __str__(self):
        return f"[{self.code.name}] {self.message}"


class CameraError(ARError):
    """摄像头相关错误"""
    pass


class FaceSwapError(ARError):
    """人脸合成相关错误"""
    pass


class AudioError(ARError):
    """音频处理相关错误"""
    pass


class FileError(ARError):
    """文件操作相关错误"""
    pass


# 错误消息映射（用户友好的提示）
ERROR_MESSAGES = {
    ErrorCode.UNKNOWN_ERROR: {
        'title': '未知错误',
        'message': '发生未知错误，请查看日志获取详细信息。',
        'suggestion': '如果问题持续，请重启应用程序。'
    },
    ErrorCode.CAMERA_NOT_FOUND: {
        'title': '未找到摄像头',
        'message': '系统未检测到摄像头设备。',
        'suggestion': '请检查摄像头是否已连接，并确保没有其他程序占用摄像头。'
    },
    ErrorCode.CAMERA_PERMISSION_DENIED: {
        'title': '摄像头权限不足',
        'message': '无法访问摄像头，权限被拒绝。',
        'suggestion': '请检查摄像头设备权限，或尝试以管理员身份运行程序。'
    },
    ErrorCode.FACE_DETECTION_FAILED: {
        'title': '人脸检测失败',
        'message': '无法在图像中检测到人脸。',
        'suggestion': '请确保图像清晰，人脸正面朝向摄像头，光线充足。'
    },
    ErrorCode.MODEL_NOT_FOUND: {
        'title': '模型文件缺失',
        'message': '所需的人脸合成模型文件未找到。',
        'suggestion': '请运行安装脚本下载模型文件，或手动放置到models目录。'
    },
    ErrorCode.AUDIO_DEVICE_NOT_FOUND: {
        'title': '未找到音频设备',
        'message': '系统未检测到音频输入/输出设备。',
        'suggestion': '请检查音频设备是否已连接，并确保没有被其他程序占用。'
    },
    ErrorCode.SOX_NOT_INSTALLED: {
        'title': 'Sox未安装',
        'message': '音频处理需要Sox工具，但未检测到安装。',
        'suggestion': '请安装Sox: Ubuntu/Debian运行 `sudo apt-get install sox`'
    },
    ErrorCode.FILE_NOT_FOUND: {
        'title': '文件未找到',
        'message': '指定的文件不存在。',
        'suggestion': '请检查文件路径是否正确。'
    },
    ErrorCode.INVALID_FILE_FORMAT: {
        'title': '文件格式不支持',
        'message': '所选文件的格式不受支持。',
        'suggestion': '请使用支持的格式: JPG, PNG, BMP, WEBP'
    },
    ErrorCode.NETWORK_ERROR: {
        'title': '网络错误',
        'message': '网络连接出现问题。',
        'suggestion': '请检查网络连接，或稍后重试。'
    }
}


def get_user_friendly_message(error_code: ErrorCode) -> Dict[str, str]:
    """
    获取用户友好的错误消息
    
    Args:
        error_code: 错误码
        
    Returns:
        Dict: 包含title, message, suggestion的字典
    """
    return ERROR_MESSAGES.get(error_code, {
        'title': '错误',
        'message': '发生错误，请查看日志。',
        'suggestion': '如果问题持续，请联系技术支持。'
    })


def handle_exception(func: Callable) -> Callable:
    """
    异常处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        Callable: 包装后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ARError as e:
            # 已知的AR错误，记录并重新抛出
            logger.error(f"AR错误: {e}")
            raise
        except cv2.error as e:
            # OpenCV错误
            logger.error(f"OpenCV错误: {e}")
            raise CameraError(
                ErrorCode.CAMERA_INIT_FAILED,
                f"OpenCV操作失败: {str(e)}"
            )
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            raise FileError(
                ErrorCode.FILE_NOT_FOUND,
                f"文件未找到: {str(e)}"
            )
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            raise CameraError(
                ErrorCode.CAMERA_PERMISSION_DENIED,
                f"权限不足: {str(e)}"
            )
        except Exception as e:
            # 未知错误
            logger.exception(f"未处理的异常: {e}")
            raise ARError(
                ErrorCode.UNKNOWN_ERROR,
                f"发生错误: {str(e)}",
                {'traceback': traceback.format_exc()}
            )
    
    return wrapper


def safe_call(func: Callable, default_return: Any = None, 
              error_callback: Optional[Callable] = None) -> Any:
    """
    安全调用函数，捕获所有异常
    
    Args:
        func: 要调用的函数
        default_return: 发生错误时的默认返回值
        error_callback: 错误回调函数
        
    Returns:
        Any: 函数返回值或默认值
    """
    try:
        return func()
    except Exception as e:
        logger.exception(f"安全调用失败: {e}")
        if error_callback:
            error_callback(e)
        return default_return


class ErrorHandler:
    """全局错误处理器"""
    
    def __init__(self):
        self.error_callbacks: Dict[ErrorCode, List[Callable]] = {}
        self.global_callbacks: List[Callable] = []
    
    def register_callback(self, error_code: ErrorCode, callback: Callable):
        """
        注册特定错误码的回调
        
        Args:
            error_code: 错误码
            callback: 回调函数
        """
        if error_code not in self.error_callbacks:
            self.error_callbacks[error_code] = []
        self.error_callbacks[error_code].append(callback)
    
    def register_global_callback(self, callback: Callable):
        """
        注册全局错误回调
        
        Args:
            callback: 回调函数
        """
        self.global_callbacks.append(callback)
    
    def handle(self, error: Exception):
        """
        处理错误
        
        Args:
            error: 异常对象
        """
        # 获取错误码
        if isinstance(error, ARError):
            error_code = error.code
            error_info = get_user_friendly_message(error_code)
        else:
            error_code = ErrorCode.UNKNOWN_ERROR
            error_info = get_user_friendly_message(error_code)
        
        # 记录错误
        logger.error(f"处理错误 [{error_code.name}]: {error}")
        
        # 调用特定错误码的回调
        if error_code in self.error_callbacks:
            for callback in self.error_callbacks[error_code]:
                try:
                    callback(error, error_info)
                except Exception as e:
                    logger.error(f"错误回调执行失败: {e}")
        
        # 调用全局回调
        for callback in self.global_callbacks:
            try:
                callback(error, error_info)
            except Exception as e:
                logger.error(f"全局错误回调执行失败: {e}")


# 全局错误处理器实例
_global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return _global_error_handler


def setup_global_exception_hook():
    """设置全局异常钩子"""
    def exception_hook(exc_type, exc_value, exc_traceback):
        # 记录未捕获的异常
        logger.error("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
        
        # 转换为AR错误并处理
        if issubclass(exc_type, ARError):
            get_error_handler().handle(exc_value)
        else:
            ar_error = ARError(
                ErrorCode.UNKNOWN_ERROR,
                str(exc_value),
                {'traceback': ''.join(traceback.format_tb(exc_traceback))}
            )
            get_error_handler().handle(ar_error)
    
    sys.excepthook = exception_hook


# 便捷函数
def raise_camera_error(message: str, code: ErrorCode = ErrorCode.CAMERA_INIT_FAILED):
    """抛出摄像头错误"""
    raise CameraError(code, message)


def raise_face_swap_error(message: str, code: ErrorCode = ErrorCode.FACE_SWAP_FAILED):
    """抛出人脸合成错误"""
    raise FaceSwapError(code, message)


def raise_audio_error(message: str, code: ErrorCode = ErrorCode.AUDIO_INIT_FAILED):
    """抛出音频错误"""
    raise AudioError(code, message)


def raise_file_error(message: str, code: ErrorCode = ErrorCode.FILE_NOT_FOUND):
    """抛出文件错误"""
    raise FileError(code, message)


# 使用示例
if __name__ == '__main__':
    # 设置全局异常处理
    setup_global_exception_hook()
    
    # 注册错误回调
    def on_camera_error(error, info):
        print(f"摄像头错误: {info['message']}")
    
    get_error_handler().register_callback(ErrorCode.CAMERA_NOT_FOUND, on_camera_error)
    
    # 测试
    try:
        raise CameraError(ErrorCode.CAMERA_NOT_FOUND, "测试错误")
    except Exception as e:
        get_error_handler().handle(e)
