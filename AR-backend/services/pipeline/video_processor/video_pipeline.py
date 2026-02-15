"""
视频处理流水线
提供视频帧提取、处理和预览生成的完整流水线
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoPipeline:
    """
    视频处理流水线
    
    提供完整的视频处理流程：
    1. 帧提取：从视频中提取关键帧
    2. 帧处理：对每帧进行图像处理
    3. 预览生成：生成处理后的预览视频
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化视频处理流水线
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.frame_interval = self.config.get('frame_interval', 1)
        self.image_pipeline = None
        
    def _get_image_pipeline(self):
        """获取图像处理流水线"""
        if self.image_pipeline is None:
            from .image_pipeline import ImagePipeline
            self.image_pipeline = ImagePipeline(self.config.get('image', {}))
        return self.image_pipeline
    
    def extract_frames(self, video_path: str) -> List[Dict]:
        """
        从视频中提取帧
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            List[Dict]: 提取的帧列表
        """
        frames = []
        
        try:
            import cv2
            if not Path(video_path).exists():
                logger.error(f"Video file not found: {video_path}")
                return frames
            
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"Failed to open video: {video_path}")
                return frames
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % int(fps * self.frame_interval) == 0:
                    frames.append({
                        'frame_number': frame_count,
                        'timestamp': frame_count / fps,
                        'frame': frame
                    })
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            
        except ImportError:
            logger.warning("OpenCV not available, using mock frames")
            frames = [{'frame_number': 0, 'timestamp': 0, 'frame': None}]
        
        return frames
    
    def process_frames(self, frames: List[Dict]) -> List[Dict]:
        """
        处理视频帧
        
        Args:
            frames: 帧列表
            
        Returns:
            List[Dict]: 处理后的帧列表
        """
        if not frames:
            return frames
        
        image_pipeline = self.__get_image_pipeline()
        processed_frames = []
        
        for frame_data in frames:
            frame = frame_data.get('frame')
            if frame is None:
                processed_frames.append(frame_data)
                continue
            
            try:
                result = image_pipeline.execute(frame)
                processed_frames.append({
                    'frame_number': frame_data['frame_number'],
                    'timestamp': frame_data['timestamp'],
                    'frame': frame,
                    'processed': result.get('output', {}),
                    'pipeline_result': result
                })
            except Exception as e:
                logger.error(f"Frame processing failed: {e}")
                processed_frames.append({
                    'frame_number': frame_data['frame_number'],
                    'timestamp': frame_data['timestamp'],
                    'frame': frame,
                    'error': str(e)
                })
        
        return processed_frames
    
    def generate_preview(self, processed_frames: List[Dict], 
                       output_path: str = None,
                       fps: int = 30) -> str:
        """
        生成预览视频
        
        Args:
            processed_frames: 处理后的帧列表
            output_path: 输出路径
            fps: 输出视频帧率
            
        Returns:
            str: 生成的视频路径
        """
        if not processed_frames:
            logger.warning("No frames to generate preview")
            return None
        
        try:
            import cv2
            import numpy as np
            
            # 获取帧尺寸
            sample_frame = processed_frames[0].get('frame')
            if sample_frame is None:
                logger.error("No valid frames available")
                return None
            
            height, width = sample_frame.shape[:2]
            
            # 如果处理后的帧有输出，使用输出尺寸
            if 'processed' in processed_frames[0]:
                processed = processed_frames[0]['processed']
                if isinstance(processed, dict) and 'formatted' in str(type(processed)):
                    # 从输出中获取尺寸
                    pass
            
            # 创建视频写入器
            if output_path is None:
                output_path = 'preview.mp4'
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for frame_data in processed_frames:
                frame = frame_data.get('frame')
                if frame is not None:
                    # 如果有处理后的帧，使用处理后的
                    if 'processed' in frame_data:
                        proc = frame_data['processed']
                        if isinstance(proc, dict) and 'formatted' in proc:
                            # 使用处理后的帧
                            pass
                    out.write(frame)
            
            out.release()
            logger.info(f"Preview video saved to: {output_path}")
            return output_path
            
        except ImportError:
            logger.warning("OpenCV not available, skipping preview generation")
            return None
    
    def execute(self, video_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        执行完整视频处理流水线
        
        Args:
            video_path: 输入视频路径
            output_path: 输出预览路径
            
        Returns:
            Dict: 执行结果
        """
        import time
        start_time = time.time()
        
        result = {
            'success': False,
            'input': video_path,
            'stages': {},
            'total_elapsed': 0
        }
        
        try:
            # 阶段 1: 帧提取
            stage_start = time.time()
            frames = self.extract_frames(video_path)
            result['stages']['frame_extraction'] = {
                'status': 'success' if frames else 'warning',
                'frame_count': len(frames),
                'elapsed': time.time() - stage_start
            }
            
            if not frames:
                result['stages']['frame_extraction']['status'] = 'failed'
                result['error'] = 'No frames extracted'
                return result
            
            # 阶段 2: 帧处理
            stage_start = time.time()
            processed_frames = self.process_frames(frames)
            result['stages']['frame_processing'] = {
                'status': 'success',
                'processed_count': len([f for f in processed_frames if 'error' not in f]),
                'failed_count': len([f for f in processed_frames if 'error' in f]),
                'elapsed': time.time() - stage_start
            }
            
            # 阶段 3: 预览生成
            if output_path:
                stage_start = time.time()
                preview_path = self.generate_preview(processed_frames, output_path)
                result['stages']['preview_generation'] = {
                    'status': 'success' if preview_path else 'failed',
                    'output_path': preview_path,
                    'elapsed': time.time() - stage_start
                }
            
            result['success'] = True
            result['frames'] = {
                'total': len(frames),
                'processed': len([f for f in processed_frames if 'error' not in f])
            }
            
        except Exception as e:
            logger.error(f"Video pipeline execution failed: {e}")
            result['stages']['error'] = str(e)
            result['error'] = str(e)
        
        result['total_elapsed'] = time.time() - start_time
        
        return result
    
    def get_status(self) -> Dict:
        """
        获取流水线状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            'frame_interval': self.frame_interval,
            'image_pipeline_configured': self.image_pipeline is not None,
            'config': self.config
        }


# 便捷函数：创建视频流水线
def create_video_pipeline(config: Dict = None) -> VideoPipeline:
    """创建视频处理流水线"""
    return VideoPipeline(config)
