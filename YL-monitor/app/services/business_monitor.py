#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务功能层监控器 (L4)
提供视频处理、人脸合成、音频处理的详细监控
"""

import logging
import statistics
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class VideoProcessingMetrics:
    """视频处理指标"""
    fps: float
    target_fps: int
    frame_count: int
    dropped_frames: int
    drop_rate: float
    processing_time_ms: float
    resolution: str
    codec: str
    bitrate_kbps: float
    buffer_size: int
    buffer_usage_percent: float
    is_streaming: bool
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FaceSwapMetrics:
    """人脸合成指标"""
    model_name: str
    model_load_time_ms: float
    inference_time_ms: float
    faces_detected: int
    faces_swapped: int
    quality_score: float
    gpu_utilization: float
    memory_used_mb: float
    batch_size: int
    total_frames_processed: int
    avg_confidence: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
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
    effects_active: List[str]
    pitch_shift_semitones: float
    reverb_wetness: float
    speed_ratio: float
    noise_gate_threshold: float
    compressor_ratio: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessFunctionMetrics:
    """业务功能整体指标"""
    video: VideoProcessingMetrics
    face_swap: FaceSwapMetrics
    audio: AudioProcessingMetrics
    overall_health: str
    active_sessions: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "video": self.video.to_dict(),
            "face_swap": self.face_swap.to_dict(),
            "audio": self.audio.to_dict(),
            "overall_health": self.overall_health,
            "active_sessions": self.active_sessions,
            "timestamp": self.timestamp
        }


class VideoProcessingMonitor:
    """
    视频处理监控器
    
    监控指标：
    - FPS（实际/目标）
    - 丢帧率
    - 处理时间
    - 分辨率/编码
    - 码率
    - 缓冲区状态
    - 流状态
    """
    
    def __init__(self, target_fps: int = 30, history_size: int = 100):
        self.target_fps = target_fps
        self.history_size = history_size
        
        self._frame_times: deque = deque(maxlen=history_size)
        self._dropped_frames = 0
        self._total_frames = 0
        self._is_streaming = False
        self._resolution = "1920x1080"
        self._codec = "H.264"
        self._bitrate = 5000  # kbps
        
        # 模拟缓冲区
        self._buffer_size = 30
        self._buffer_usage = 0
    
    def record_frame(self, processing_time_ms: float, dropped: bool = False):
        """
        记录帧处理
        
        Args:
            processing_time_ms: 处理时间（毫秒）
            dropped: 是否丢帧
        """
        self._total_frames += 1
        self._frame_times.append({
            'timestamp': datetime.now().isoformat(),
            'processing_time': processing_time_ms
        })
        
        if dropped:
            self._dropped_frames += 1
        
        # 更新缓冲区（模拟）
        self._buffer_usage = min(self._buffer_size, 
                                self._buffer_usage + 1)
    
    def start_stream(self):
        """开始视频流"""
        self._is_streaming = True
        logger.info("视频流开始")
    
    def stop_stream(self):
        """停止视频流"""
        self._is_streaming = False
        self._buffer_usage = 0
        logger.info("视频流停止")
    
    def get_metrics(self) -> VideoProcessingMetrics:
        """
        获取视频处理指标
        """
        # 计算FPS
        if len(self._frame_times) >= 2:
            # 使用最近30帧的数据计算FPS
            recent_times = list(self._frame_times)[-30:]
            if len(recent_times) >= 2:
                # 简化计算，使用帧数作为FPS估计
                actual_fps = min(self.target_fps, len(recent_times))
            else:
                actual_fps = 0
            
            # 计算平均处理时间
            times = [f['processing_time'] for f in self._frame_times]
            avg_time = statistics.mean(times)
        else:
            actual_fps = 0
            avg_time = 0
        
        # 计算丢帧率
        drop_rate = (
            (self._dropped_frames / self._total_frames * 100)
            if self._total_frames > 0 else 0
        )
        
        # 缓冲区使用率
        buffer_usage_pct = (
            (self._buffer_usage / self._buffer_size * 100)
            if self._buffer_size > 0 else 0
        )
        
        return VideoProcessingMetrics(
            fps=round(actual_fps, 1),
            target_fps=self.target_fps,
            frame_count=self._total_frames,
            dropped_frames=self._dropped_frames,
            drop_rate=round(drop_rate, 2),
            processing_time_ms=round(avg_time, 2),
            resolution=self._resolution,
            codec=self._codec,
            bitrate_kbps=round(self._bitrate, 1),
            buffer_size=self._buffer_size,
            buffer_usage_percent=round(buffer_usage_pct, 1),
            is_streaming=self._is_streaming,
            timestamp=datetime.now().isoformat()
        )


class FaceSwapMonitor:
    """
    人脸合成监控器
    
    监控指标：
    - 模型加载时间
    - 推理时间
    - 检测到的人脸数
    - 合成成功数
    - 质量评分
    - GPU利用率
    - 内存使用
    - 置信度
    """
    
    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        
        self._model_load_time = 0
        self._inference_times: deque = deque(maxlen=100)
        self._faces_detected = 0
        self._faces_swapped = 0
        self._total_frames = 0
        self._confidence_scores: deque = deque(maxlen=100)
        
        # 模拟GPU状态
        self._gpu_util = 0
        self._memory_used = 0
    
    def record_model_load(self, load_time_ms: float):
        """
        记录模型加载时间
        
        Args:
            load_time_ms: 加载时间（毫秒）
        """
        self._model_load_time = load_time_ms
        logger.info(f"模型 {self.model_name} 加载完成，"
                   f"耗时 {load_time_ms:.2f}ms")
    
    def record_inference(
        self,
        inference_time_ms: float,
        faces_detected: int,
        faces_swapped: int,
        confidence: float,
        gpu_util: float = 0,
        memory_mb: float = 0
    ):
        """
        记录推理结果
        
        Args:
            inference_time_ms: 推理时间（毫秒）
            faces_detected: 检测到的人脸数
            faces_swapped: 合成成功的人脸数
            confidence: 置信度分数
            gpu_util: GPU利用率
            memory_mb: 内存使用（MB）
        """
        self._inference_times.append({
            'timestamp': datetime.now().isoformat(),
            'inference_time': inference_time_ms
        })
        
        self._faces_detected += faces_detected
        self._faces_swapped += faces_swapped
        self._total_frames += 1
        self._confidence_scores.append(confidence)
        
        self._gpu_util = gpu_util
        self._memory_used = memory_mb
    
    def get_metrics(self) -> FaceSwapMetrics:
        """
        获取人脸合成指标
        """
        # 计算平均推理时间
        if self._inference_times:
            times = [i['inference_time'] for i in self._inference_times]
            avg_inference = statistics.mean(times)
        else:
            avg_inference = 0
        
        # 计算平均置信度
        if self._confidence_scores:
            avg_confidence = statistics.mean(self._confidence_scores)
        else:
            avg_confidence = 0
        
        # 质量评分（基于置信度和成功率）
        success_rate = (
            (self._faces_swapped / self._faces_detected * 100)
            if self._faces_detected > 0 else 0
        )
        quality_score = (avg_confidence * 0.7 + success_rate * 0.3)
        
        return FaceSwapMetrics(
            model_name=self.model_name,
            model_load_time_ms=round(self._model_load_time, 2),
            inference_time_ms=round(avg_inference, 2),
            faces_detected=self._faces_detected,
            faces_swapped=self._faces_swapped,
            quality_score=round(quality_score, 2),
            gpu_utilization=round(self._gpu_util, 1),
            memory_used_mb=round(self._memory_used, 1),
            batch_size=1,  # 默认单帧处理
            total_frames_processed=self._total_frames,
            avg_confidence=round(avg_confidence, 3),
            timestamp=datetime.now().isoformat()
        )


class AudioProcessingMonitor:
    """
    音频处理监控器
    
    监控指标：
    - 采样率/通道数
    - 处理延迟
    - 实时因子（RTF）
    - 缓冲区欠载/过载
    - 活跃音效
    - 音效参数
    """
    
    def __init__(self, sample_rate: int = 44100, channels: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels
        
        self._processing_times: deque = deque(maxlen=100)
        self._underruns = 0
        self._overruns = 0
        self._effects_active: List[str] = []
        
        # 音效参数
        self._pitch_shift = 0
        self._reverb_wetness = 0.3
        self._speed_ratio = 1.0
        self._noise_gate = -60
        self._compressor_ratio = 1.0
    
    def record_processing(
        self,
        processing_time_ms: float,
        buffer_size: int,
        realtime: bool = True
    ):
        """
        记录音频处理
        
        Args:
            processing_time_ms: 处理时间（毫秒）
            buffer_size: 缓冲区大小（样本数）
            realtime: 是否实时处理
        """
        self._processing_times.append({
            'timestamp': datetime.now().isoformat(),
            'processing_time': processing_time_ms,
            'buffer_size': buffer_size
        })
        
        # 检测缓冲区问题
        if realtime:
            expected_time = (buffer_size / self.sample_rate * 1000)
            rtf = processing_time_ms / expected_time if expected_time > 0 else 0
            
            if rtf > 1.0:
                self._overruns += 1
            elif rtf < 0.5:
                self._underruns += 1
    
    def set_effects(
        self,
        effects: List[str],
        pitch_shift: float = 0,
        reverb: float = 0.3,
        speed: float = 1.0,
        noise_gate: float = -60,
        compressor: float = 1.0
    ):
        """
        设置音效参数
        
        Args:
            effects: 活跃音效列表
            pitch_shift: 音高偏移（半音）
            reverb: 混响湿度
            speed: 速度比例
            noise_gate: 噪声门限（dB）
            compressor: 压缩比
        """
        self._effects_active = effects
        self._pitch_shift = pitch_shift
        self._reverb_wetness = reverb
        self._speed_ratio = speed
        self._noise_gate = noise_gate
        self._compressor_ratio = compressor
    
    def get_metrics(self) -> AudioProcessingMetrics:
        """
        获取音频处理指标
        """
        # 计算平均处理延迟
        if self._processing_times:
            times = [p['processing_time'] for p in self._processing_times]
            avg_delay = statistics.mean(times)
            
            # 计算实时因子
            last_buffer = self._processing_times[-1]['buffer_size']
            expected_time = (last_buffer / self.sample_rate * 1000)
            rtf = avg_delay / expected_time if expected_time > 0 else 0
        else:
            avg_delay = 0
            rtf = 0
        
        return AudioProcessingMetrics(
            sample_rate=self.sample_rate,
            channels=self.channels,
            processing_delay_ms=round(avg_delay, 2),
            realtime_factor=round(rtf, 3),
            buffer_underruns=self._underruns,
            buffer_overruns=self._overruns,
            effects_active=self._effects_active,
            pitch_shift_semitones=round(self._pitch_shift, 1),
            reverb_wetness=round(self._reverb_wetness, 2),
            speed_ratio=round(self._speed_ratio, 2),
            noise_gate_threshold=round(self._noise_gate, 1),
            compressor_ratio=round(self._compressor_ratio, 1),
            timestamp=datetime.now().isoformat()
        )


class BusinessCollector:
    """
    业务功能指标采集器
    
    整合视频处理、人脸合成、音频处理监控器
    """
    
    def __init__(self):
        self.video_monitor = VideoProcessingMonitor(target_fps=30)
        self.face_monitor = FaceSwapMonitor(model_name="inswap_128")
        self.audio_monitor = AudioProcessingMonitor(
            sample_rate=44100, 
            channels=2
        )
        
        self._active_sessions = 0
    
    def start_session(self):
        """开始会话"""
        self._active_sessions += 1
        self.video_monitor.start_stream()
        logger.info(f"业务会话开始，当前活跃: {self._active_sessions}")
    
    def stop_session(self):
        """停止会话"""
        self._active_sessions = max(0, self._active_sessions - 1)
        self.video_monitor.stop_stream()
        logger.info(f"业务会话停止，当前活跃: {self._active_sessions}")
    
    def collect_all(self) -> Dict[str, Any]:
        """
        采集所有业务功能层指标
        """
        try:
            video_metrics = self.video_monitor.get_metrics()
            face_metrics = self.face_monitor.get_metrics()
            audio_metrics = self.audio_monitor.get_metrics()
            
            # 评估整体健康状态
            health_factors = []
            
            # 视频健康度
            if video_metrics.drop_rate < 5:
                health_factors.append(1.0)
            elif video_metrics.drop_rate < 10:
                health_factors.append(0.7)
            else:
                health_factors.append(0.3)
            
            # 人脸合成健康度
            if face_metrics.quality_score > 0.8:
                health_factors.append(1.0)
            elif face_metrics.quality_score > 0.5:
                health_factors.append(0.7)
            else:
                health_factors.append(0.3)
            
            # 音频健康度
            if audio_metrics.realtime_factor < 1.0:
                health_factors.append(1.0)
            elif audio_metrics.realtime_factor < 1.5:
                health_factors.append(0.7)
            else:
                health_factors.append(0.3)
            
            avg_health = statistics.mean(health_factors)
            if avg_health >= 0.9:
                overall_health = "excellent"
            elif avg_health >= 0.7:
                overall_health = "good"
            elif avg_health >= 0.5:
                overall_health = "fair"
            else:
                overall_health = "poor"
            
            return {
                "timestamp": datetime.now().isoformat(),
                "layer": "L4_business_functions",
                "video": video_metrics.to_dict(),
                "face_swap": face_metrics.to_dict(),
                "audio": audio_metrics.to_dict(),
                "overall_health": overall_health,
                "active_sessions": self._active_sessions
            }
            
        except Exception as e:
            logger.error(f"采集业务功能指标失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "layer": "L4_business_functions",
                "error": str(e)
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        获取健康状态摘要
        """
        metrics = self.collect_all()
        
        if "error" in metrics:
            return {
                "status": "error",
                "error": metrics["error"],
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": metrics["overall_health"],
            "active_sessions": metrics["active_sessions"],
            "components": {
                "video": "healthy" if metrics["video"]["drop_rate"] < 5 else "degraded",
                "face_swap": "healthy" if metrics["face_swap"]["quality_score"] > 0.7 else "degraded",
                "audio": "healthy" if metrics["audio"]["realtime_factor"] < 1.0 else "degraded"
            },
            "timestamp": datetime.now().isoformat()
        }


# 全局采集器实例
business_collector = BusinessCollector()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("业务功能层监控测试")
    print("=" * 60)
    
    collector = BusinessCollector()
    
    # 模拟一些活动
    print("\n1. 模拟视频处理...")
    collector.start_session()
    
    # 模拟帧处理
    for i in range(50):
        collector.video_monitor.record_frame(
            processing_time_ms=25 + (i % 10),
            dropped=(i % 20 == 0)  # 每20帧丢1帧
        )
    
    # 模拟人脸合成
    print("2. 模拟人脸合成...")
    collector.face_monitor.record_model_load(1500.0)
    for i in range(30):
        collector.face_monitor.record_inference(
            inference_time_ms=45 + (i % 15),
            faces_detected=1,
            faces_swapped=1,
            confidence=0.85 + (i % 10) / 100,
            gpu_util=65.0,
            memory_mb=512.0
        )
    
    # 模拟音频处理
    print("3. 模拟音频处理...")
    collector.audio_monitor.set_effects(
        effects=["pitch_shift", "reverb"],
        pitch_shift=2.0,
        reverb=0.4,
        speed=1.0
    )
    for i in range(40):
        collector.audio_monitor.record_processing(
            processing_time_ms=5 + (i % 3),
            buffer_size=1024,
            realtime=True
        )
    
    # 获取指标
    print("\n4. 采集指标...")
    metrics = collector.collect_all()
    
    print(f"\n整体健康状态: {metrics['overall_health']}")
    print(f"活跃会话数: {metrics['active_sessions']}")
    
    print("\n视频处理指标:")
    video = metrics['video']
    print(f"  FPS: {video['fps']}/{video['target_fps']}")
    print(f"  丢帧率: {video['drop_rate']:.2f}%")
    print(f"  处理时间: {video['processing_time_ms']:.2f}ms")
    print(f"  分辨率: {video['resolution']}")
    print(f"  流状态: {'运行中' if video['is_streaming'] else '停止'}")
    
    print("\n人脸合成指标:")
    face = metrics['face_swap']
    print(f"  模型: {face['model_name']}")
    print(f"  模型加载: {face['model_load_time_ms']:.2f}ms")
    print(f"  推理时间: {face['inference_time_ms']:.2f}ms")
    print(f"  人脸检测: {face['faces_detected']}")
    print(f"  合成成功: {face['faces_swapped']}")
    print(f"  质量评分: {face['quality_score']:.2f}")
    print(f"  GPU利用率: {face['gpu_utilization']:.1f}%")
    
    print("\n音频处理指标:")
    audio = metrics['audio']
    print(f"  采样率: {audio['sample_rate']}Hz")
    print(f"  通道: {audio['channels']}")
    print(f"  处理延迟: {audio['processing_delay_ms']:.2f}ms")
    print(f"  实时因子: {audio['realtime_factor']:.3f}")
    print(f"  活跃音效: {', '.join(audio['effects_active'])}")
    print(f"  音高偏移: {audio['pitch_shift_semitones']:.1f}半音")
    print(f"  缓冲区欠载: {audio['buffer_underruns']}")
    print(f"  缓冲区过载: {audio['buffer_overruns']}")
    
    # 健康摘要
    print("\n5. 健康摘要:")
    health = collector.get_health_summary()
    print(f"  状态: {health['status']}")
    print("  组件状态:")
    for comp, status in health['components'].items():
        icon = "✅" if status == "healthy" else "⚠️"
        print(f"    {icon} {comp}: {status}")
    
    collector.stop_session()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
