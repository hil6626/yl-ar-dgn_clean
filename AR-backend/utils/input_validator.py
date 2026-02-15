#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR-backend 输入验证模块
提供参数验证、边界检查、类型检查等功能

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import re
import os
from pathlib import Path
from typing import Any, Optional, List, Tuple, Callable, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"[{field}] {message}")


class ValidationResult:
    """验证结果"""
    def __init__(self, is_valid: bool = True, errors: List[ValidationError] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, field: str, message: str, value: Any = None):
        """添加错误"""
        self.errors.append(ValidationError(field, message, value))
        self.is_valid = False
    
    def merge(self, other: 'ValidationResult'):
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        if not other.is_valid:
            self.is_valid = False
    
    def get_messages(self) -> List[str]:
        """获取所有错误消息"""
        return [str(e) for e in self.errors]
    
    def raise_if_invalid(self):
        """如果验证失败，抛出异常"""
        if not self.is_valid:
            raise ValidationError(
                "validation",
                "; ".join(self.get_messages())
            )


class InputValidator:
    """输入验证器"""
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    
    # 支持的音频格式
    SUPPORTED_AUDIO_FORMATS = {'.wav', '.mp3', '.flac', '.aac', '.ogg', '.m4a'}
    
    @staticmethod
    def validate_string(value: Any, field_name: str, 
                      min_length: int = 0, 
                      max_length: Optional[int] = None,
                      pattern: Optional[str] = None,
                      allow_empty: bool = False) -> ValidationResult:
        """
        验证字符串
        
        Args:
            value: 要验证的值
            field_name: 字段名
            min_length: 最小长度
            max_length: 最大长度
            pattern: 正则表达式模式
            allow_empty: 是否允许空字符串
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 类型检查
        if not isinstance(value, str):
            result.add_error(field_name, f"必须是字符串类型，实际为: {type(value).__name__}", value)
            return result
        
        # 空值检查
        if not value and not allow_empty:
            result.add_error(field_name, "不能为空", value)
            return result
        
        # 长度检查
        if len(value) < min_length:
            result.add_error(field_name, f"长度不能小于 {min_length}", value)
        
        if max_length is not None and len(value) > max_length:
            result.add_error(field_name, f"长度不能超过 {max_length}", value)
        
        # 模式检查
        if pattern and value:
            if not re.match(pattern, value):
                result.add_error(field_name, f"格式不匹配模式: {pattern}", value)
        
        return result
    
    @staticmethod
    def validate_number(value: Any, field_name: str,
                       min_value: Optional[Union[int, float]] = None,
                       max_value: Optional[Union[int, float]] = None,
                       allow_float: bool = True) -> ValidationResult:
        """
        验证数字
        
        Args:
            value: 要验证的值
            field_name: 字段名
            min_value: 最小值
            max_value: 最大值
            allow_float: 是否允许浮点数
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 类型检查
        if not isinstance(value, (int, float)):
            result.add_error(field_name, f"必须是数字类型，实际为: {type(value).__name__}", value)
            return result
        
        # 浮点数检查
        if not allow_float and isinstance(value, float):
            result.add_error(field_name, "必须是整数", value)
            return result
        
        # 范围检查
        if min_value is not None and value < min_value:
            result.add_error(field_name, f"不能小于 {min_value}", value)
        
        if max_value is not None and value > max_value:
            result.add_error(field_name, f"不能超过 {max_value}", value)
        
        return result
    
    @staticmethod
    def validate_file_path(value: Any, field_name: str,
                          must_exist: bool = True,
                          allowed_extensions: Optional[set] = None,
                          max_size_mb: Optional[float] = None) -> ValidationResult:
        """
        验证文件路径
        
        Args:
            value: 要验证的值
            field_name: 字段名
            must_exist: 是否必须存在
            allowed_extensions: 允许的扩展名集合
            max_size_mb: 最大文件大小(MB)
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 类型检查
        if not isinstance(value, (str, Path)):
            result.add_error(field_name, f"必须是字符串或Path类型", value)
            return result
        
        path = Path(value)
        
        # 存在性检查
        if must_exist and not path.exists():
            result.add_error(field_name, f"文件不存在: {path}", value)
            return result
        
        # 扩展名检查
        if allowed_extensions:
            ext = path.suffix.lower()
            if ext not in allowed_extensions:
                result.add_error(
                    field_name, 
                    f"不支持的文件格式: {ext}，支持的格式: {allowed_extensions}", 
                    value
                )
        
        # 文件大小检查
        if max_size_mb and path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                result.add_error(
                    field_name,
                    f"文件过大: {size_mb:.2f}MB，最大允许: {max_size_mb}MB",
                    value
                )
        
        return result
    
    @staticmethod
    def validate_image_path(value: Any, field_name: str = "image_path",
                           must_exist: bool = True,
                           max_size_mb: float = 10.0) -> ValidationResult:
        """
        验证图片路径
        
        Args:
            value: 要验证的值
            field_name: 字段名
            must_exist: 是否必须存在
            max_size_mb: 最大文件大小
            
        Returns:
            ValidationResult: 验证结果
        """
        return InputValidator.validate_file_path(
            value, field_name, must_exist,
            InputValidator.SUPPORTED_IMAGE_FORMATS,
            max_size_mb
        )
    
    @staticmethod
    def validate_video_path(value: Any, field_name: str = "video_path",
                           must_exist: bool = True,
                           max_size_mb: float = 100.0) -> ValidationResult:
        """
        验证视频路径
        
        Args:
            value: 要验证的值
            field_name: 字段名
            must_exist: 是否必须存在
            max_size_mb: 最大文件大小
            
        Returns:
            ValidationResult: 验证结果
        """
        return InputValidator.validate_file_path(
            value, field_name, must_exist,
            InputValidator.SUPPORTED_VIDEO_FORMATS,
            max_size_mb
        )
    
    @staticmethod
    def validate_camera_id(value: Any, field_name: str = "camera_id") -> ValidationResult:
        """
        验证摄像头ID
        
        Args:
            value: 要验证的值
            field_name: 字段名
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 类型检查
        if not isinstance(value, int):
            result.add_error(field_name, f"必须是整数类型", value)
            return result
        
        # 范围检查
        if value < 0 or value > 10:
            result.add_error(field_name, f"必须在 0-10 范围内", value)
        
        return result
    
    @staticmethod
    def validate_resolution(value: Any, field_name: str = "resolution") -> ValidationResult:
        """
        验证分辨率
        
        Args:
            value: 要验证的值 (width, height) 元组
            field_name: 字段名
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 类型检查
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            result.add_error(field_name, "必须是包含两个元素的元组或列表 (width, height)", value)
            return result
        
        width, height = value
        
        # 检查每个值
        width_result = InputValidator.validate_number(width, f"{field_name}[0]", min_value=1, max_value=7680)
        height_result = InputValidator.validate_number(height, f"{field_name}[1]", min_value=1, max_value=4320)
        
        result.merge(width_result)
        result.merge(height_result)
        
        # 常见分辨率检查（警告）
        common_resolutions = [
            (640, 480), (1280, 720), (1920, 1080), 
            (2560, 1440), (3840, 2160)
        ]
        if (width, height) not in common_resolutions:
            logger.warning(f"非标准分辨率: {width}x{height}")
        
        return result
    
    @staticmethod
    def validate_fps(value: Any, field_name: str = "fps") -> ValidationResult:
        """
        验证帧率
        
        Args:
            value: 要验证的值
            field_name: 字段名
            
        Returns:
            ValidationResult: 验证结果
        """
        result = InputValidator.validate_number(value, field_name, min_value=1, max_value=240)
        
        # 常见帧率检查（警告）
        if result.is_valid and value not in [24, 25, 30, 60, 120, 144, 240]:
            logger.warning(f"非标准帧率: {value}")
        
        return result
    
    @staticmethod
    def validate_enum(value: Any, field_name: str, 
                     enum_class: type) -> ValidationResult:
        """
        验证枚举值
        
        Args:
            value: 要验证的值
            field_name: 字段名
            enum_class: 枚举类
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        try:
            if isinstance(value, enum_class):
                return result
            
            # 尝试转换
            enum_class(value)
        except (ValueError, TypeError):
            valid_values = [e.value for e in enum_class]
            result.add_error(
                field_name,
                f"无效值: {value}，有效值: {valid_values}",
                value
            )
        
        return result
    
    @staticmethod
    def validate_list(value: Any, field_name: str,
                     min_length: int = 0,
                     max_length: Optional[int] = None,
                     item_validator: Optional[Callable] = None) -> ValidationResult:
        """
        验证列表
        
        Args:
            value: 要验证的值
            field_name: 字段名
            min_length: 最小长度
            max_length: 最大长度
            item_validator: 列表项验证函数
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 类型检查
        if not isinstance(value, (list, tuple)):
            result.add_error(field_name, f"必须是列表或元组类型", value)
            return result
        
        # 长度检查
        if len(value) < min_length:
            result.add_error(field_name, f"长度不能小于 {min_length}", value)
        
        if max_length is not None and len(value) > max_length:
            result.add_error(field_name, f"长度不能超过 {max_length}", value)
        
        # 列表项验证
        if item_validator:
            for i, item in enumerate(value):
                item_result = item_validator(item, f"{field_name}[{i}]")
                result.merge(item_result)
        
        return result


# 便捷验证函数
def validate_camera_params(camera_id: int, width: int, height: int, fps: int) -> ValidationResult:
    """
    验证摄像头参数
    
    Args:
        camera_id: 摄像头ID
        width: 视频宽度
        height: 视频高度
        fps: 帧率
        
    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult()
    
    result.merge(InputValidator.validate_camera_id(camera_id))
    result.merge(InputValidator.validate_resolution((width, height)))
    result.merge(InputValidator.validate_fps(fps))
    
    return result


def validate_face_swap_params(image_path: str, 
                              similarity: float = 0.7,
                              smooth_edges: bool = True) -> ValidationResult:
    """
    验证人脸合成参数
    
    Args:
        image_path: 源图片路径
        similarity: 相似度阈值
        smooth_edges: 是否平滑边缘
        
    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult()
    
    # 验证图片路径
    result.merge(InputValidator.validate_image_path(image_path))
    
    # 验证相似度
    result.merge(InputValidator.validate_number(
        similarity, "similarity", min_value=0.0, max_value=1.0
    ))
    
    # 验证平滑边缘参数
    if not isinstance(smooth_edges, bool):
        result.add_error("smooth_edges", "必须是布尔值", smooth_edges)
    
    return result


def validate_audio_params(sample_rate: int = 44100,
                         buffer_size: int = 1024,
                         pitch_shift: int = 0) -> ValidationResult:
    """
    验证音频参数
    
    Args:
        sample_rate: 采样率
        buffer_size: 缓冲区大小
        pitch_shift: 音高偏移
        
    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult()
    
    # 验证采样率
    valid_sample_rates = [8000, 16000, 22050, 44100, 48000, 96000]
    if sample_rate not in valid_sample_rates:
        result.add_error(
            "sample_rate",
            f"无效采样率: {sample_rate}，支持的值: {valid_sample_rates}",
            sample_rate
        )
    
    # 验证缓冲区大小
    valid_buffer_sizes = [256, 512, 1024, 2048, 4096]
    if buffer_size not in valid_buffer_sizes:
        result.add_error(
            "buffer_size",
            f"无效缓冲区大小: {buffer_size}，支持的值: {valid_buffer_sizes}",
            buffer_size
        )
    
    # 验证音高偏移
    result.merge(InputValidator.validate_number(
        pitch_shift, "pitch_shift", min_value=-24, max_value=24
    ))
    
    return result


# 使用示例
if __name__ == '__main__':
    # 测试验证
    result = validate_camera_params(0, 1920, 1080, 30)
    print(f"摄像头参数验证: {'通过' if result.is_valid else '失败'}")
    if not result.is_valid:
        for msg in result.get_messages():
            print(f"  - {msg}")
    
    # 测试图片路径验证
    result = InputValidator.validate_image_path("test.jpg", must_exist=False)
    print(f"图片路径验证: {'通过' if result.is_valid else '失败'}")
    
    # 测试无效参数
    result = validate_camera_params(-1, 100, 100, 500)
    print(f"无效参数验证: {'通过' if result.is_valid else '失败'}")
    if not result.is_valid:
        for msg in result.get_messages():
            print(f"  - {msg}")
