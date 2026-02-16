#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务功能监控器 - L4层增强
提供视频处理、人脸合成、音频处理的实时监控
"""

import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoProcessingMetrics:
    """视频处理指标"""
    fps: float
    frame_count: int
    dropped_frames: int
    drop_rate: float
    processing_time_ms: float
    resolution: str
    codec: str
    bitrate_mbps: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FaceSwapMetrics:
    """人脸合成指标"""
    model_name: str
    inference_time_ms: float
    quality_score: float
    faces_detected: int
    faces_swapped: int
    gpu_utilization: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AudioProcessingMetrics:
    """音频处理指标"""
    sample_rate: int
    channels: int
    processing_delay_ms: float
    realtime_factor: float
    buffer_underruns: int
    buffer_overruns: int
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class BusinessMonitor:
    """
    业务功能监控器
    监控视频处理、人脸合成、音频处理等核心业务
    """
    
    def __init__(self):
        self.video_history: deque = deque(maxlen=1000)
        self.face_history: deque = deque(maxlen=1000)
        self.audio_history: deque = deque(maxlen=1000)
        self.running = False
        
        # 模拟数据（实际应从AR-backend获取）
        self._frame_count = 0
        self._dropped_frames = 0
        self._last_frame_time = time.time()
        
    def collect_video_metrics(self) -> Optional[VideoProcessingMetrics]:
        """采集视频处理指标"""
        try:
            # 模拟视频处理数据
            # 实际实现应从AR-backend的视频处理模块获取
            current_time = time.time()
            
            # 计算FPS
            time_diff = current_time - self._last_frame_time
            fps = 30.0 if time_diff > 0 else 0  # 假设30fps
            
            self._frame_count += 1
            
            # 模拟丢帧（随机丢帧率1-5%）
            import random
            if random.random() < 0.03:  # 3%丢帧率
                self._dropped_frames += 1
            
            drop_rate = (self._dropped_frames / self._frame_count * 100) if self._frame_count > 0 else 0
            
            # 模拟处理时间（33ms = 30fps）
            processing_time = 33.3 + random.uniform(-5, 5)
            
            metrics = VideoProcessingMetrics(
                fps=round(fps, 1),
                frame_count=self._frame_count,
                dropped_frames=self._dropped_frames,
                drop_rate=round(drop_rate, 2),
                processing_time_ms=round(processing_time, 1),
                resolution="1920x1080",
                codec="H.264",
                bitrate_mbps=4.5,
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.video_history.append(metrics)
            self._last_frame_time = current_time
            
            return metrics
            
        except Exception as e:
            logger.error(f"采集视频指标失败: {e}")
            return None
    
    def collect_face_metrics(self) -> Optional[FaceSwapMetrics]:
        """采集人脸合成指标"""
        try:
            import random
            
            # 模拟人脸合成数据
            models = ["Deep-Live-Cam", "DeepFaceLab", "FaceSwap"]
            model_name = random.choice(models)
            
            # 模拟推理时间（50-200ms）
            inference_time = random.uniform(50, 200)
            
            # 模拟质量评分（0.7-0.95）
            quality_score = random.uniform(0.7, 0.95)
            
            # 模拟检测到的人脸数
            faces_detected = random.randint(1, 3)
            faces_swapped = faces_detected  # 假设全部成功
            
            # 模拟GPU利用率
            gpu_util = random.uniform(30, 80)
            
            metrics = FaceSwapMetrics(
                model_name=model_name,
                inference_time_ms=round(inference_time, 1),
                quality_score=round(quality_score, 2),
                faces_detected=faces_detected,
                faces_swapped=faces_swapped,
                gpu_utilization=round(gpu_util, 1),
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.face_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"采集人脸指标失败: {e}")
            return None
    
    def collect_audio_metrics(self) -> Optional[AudioProcessingMetrics]:
        """采集音频处理指标"""
        try:
            import random
            
            # 模拟音频处理数据
            sample_rate = 48000  # 48kHz
            channels = 2  # 立体声
            
            # 模拟处理延迟（5-20ms）
            processing_delay = random.uniform(5, 20)
            
            # 实时因子（1.0表示实时，<1表示慢于实时，>1表示快于实时）
            realtime_factor = random.uniform(0.9, 1.1)
            
            # 模拟缓冲区问题
            buffer_underruns = random.randint(0, 2)
            buffer_overruns = random.randint(0, 1)
            
            metrics = AudioProcessingMetrics(
                sample_rate=sample_rate,
                channels=channels,
                processing_delay_ms=round(processing_delay, 1),
                realtime_factor=round(realtime_factor, 2),
                buffer_underruns=buffer_underruns,
                buffer_overruns=buffer_overruns,
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.audio_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"采集音频指标失败: {e}")
            return None
    
    async def start_monitoring(self, interval: int = 5):
        """启动持续监控"""
        self.running = True
        logger.info(f"启动业务功能监控 (间隔: {interval}秒)")
        
        while self.running:
            try:
                # 采集视频指标（每秒采集，但只记录每5秒）
                video_metrics = self.collect_video_metrics()
                if video_metrics and len(self.video_history) % 5 == 0:
                    logger.debug(f"视频: {video_metrics.fps}fps, "
                               f"丢帧率: {video_metrics.drop_rate}%")
                
                # 采集人脸指标（每5秒）
                if len(self.video_history) % 5 == 0:
                    face_metrics = self.collect_face_metrics()
                    if face_metrics:
                        logger.debug(f"人脸: {face_metrics.model_name}, "
                                   f"质量: {face_metrics.quality_score}")
                
                # 采集音频指标（每5秒）
                if len(self.video_history) % 5 == 0:
                    audio_metrics = self.collect_audio_metrics()
                    if audio_metrics:
                        logger.debug(f"音频: 延迟{audio_metrics.processing_delay_ms}ms, "
                                   f"实时因子: {audio_metrics.realtime_factor}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"业务监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logger.info("停止业务功能监控")
    
    def get_video_stats(self, count: int = 100) -> List[Dict]:
        """获取视频统计"""
        return [m.to_dict() for m in list(self.video_history)[-count:]]
    
    def get_face_stats(self, count: int = 100) -> List[Dict]:
        """获取人脸统计"""
        return [m.to_dict() for m in list(self.face_history)[-count:]]
    
    def get_audio_stats(self, count: int = 100) -> List[Dict]:
        """获取音频统计"""
        return [m.to_dict() for m in list(self.audio_history)[-count:]]
    
    def get_latest_video(self) -> Optional[VideoProcessingMetrics]:
        """获取最新视频指标"""
        if self.video_history:
            return self.video_history[-1]
        return None
    
    def get_latest_face(self) -> Optional[FaceSwapMetrics]:
        """获取最新人脸指标"""
        if self.face_history:
            return self.face_history[-1]
        return None
    
    def get_latest_audio(self) -> Optional[AudioProcessingMetrics]:
        """获取最新音频指标"""
        if self.audio_history:
            return self.audio_history[-1]
        return None
    
    def get_business_health(self) -> Dict:
        """获取业务健康状态"""
        video = self.get_latest_video()
        face = self.get_latest_face()
        audio = self.get_latest_audio()
        
        issues = []
        
        # 视频检查
        if video:
            if video.drop_rate > 5:
                issues.append(f"视频丢帧率过高: {video.drop_rate}%")
            if video.fps < 25:
                issues.append(f"视频FPS过低: {video.fps}")
        
        # 人脸检查
        if face:
            if face.quality_score < 0.7:
                issues.append(f"人脸合成质量较低: {face.quality_score}")
            if face.inference_time_ms > 200:
                issues.append(f"人脸推理时间过长: {face.inference_time_ms}ms")
        
        # 音频检查
        if audio:
            if audio.realtime_factor < 0.9:
                issues.append(f"音频处理慢于实时: {audio.realtime_factor}")
            if audio.buffer_underruns > 0:
                issues.append(f"音频缓冲区欠载: {audio.buffer_underruns}次")
        
        # 评估状态
        if len(issues) >= 3:
            status = "critical"
        elif len(issues) >= 1:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "issues": issues,
            "video_healthy": video.drop_rate < 5 if video else False,
            "face_healthy": face.quality_score > 0.7 if face else False,
            "audio_healthy": audio.realtime_factor > 0.9 if audio else False,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        monitor = BusinessMonitor()
        
        # 启动监控
        task = asyncio.create_task(monitor.start_monitoring(interval=5))
        
        # 运行60秒
        await asyncio.sleep(60)
        
        # 获取统计
        video = monitor.get_latest_video()
        face = monitor.get_latest_face()
        audio = monitor.get_latest_audio()
        
        print(f"\n视频处理指标:")
        if video:
            print(f"  FPS: {video.fps}")
            print(f"  丢帧率: {video.drop_rate}%")
            print(f"  处理时间: {video.processing_time_ms}ms")
        
        print(f"\n人脸合成指标:")
        if face:
            print(f"  模型: {face.model_name}")
            print(f"  推理时间: {face.inference_time_ms}ms")
            print(f"  质量评分: {face.quality_score}")
        
        print(f"\n音频处理指标:")
        if audio:
            print(f"  延迟: {audio.processing_delay_ms}ms")
            print(f"  实时因子: {audio.realtime_factor}")
        
        # 健康状态
        health = monitor.get_business_health()
        print(f"\n业务健康状态:")
        print(f"  状态: {health['status']}")
        print(f"  问题: {health['issues']}")
        
        # 停止监控
        monitor.stop_monitoring()
        task.cancel()
    
    asyncio.run(test())
