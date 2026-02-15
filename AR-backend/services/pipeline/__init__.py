"""
流水线模块初始化文件
提供图像、视频等处理流水线的统一接口
"""

from .pipeline_manager import PipelineManager, PipelineStage
from .image_pipeline import ImagePipeline
from .video_pipeline import VideoPipeline

__all__ = ['PipelineManager', 'PipelineStage', 'ImagePipeline', 'VideoPipeline']
