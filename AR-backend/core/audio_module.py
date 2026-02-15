#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理模块
负责音频流的捕获、处理和输出，使用Sox进行音效修改
增强版本：添加音频缓冲管理、设备选择优化

功能:
- 实时音频流捕获和处理
- 多种音效参数调节（音高、混响、速度、相位）
- 音频质量统计
- 虚拟音频设备支持
- 音频缓冲管理
- 低延迟处理

作者: AI 全栈技术员
版本: 1.2
创建日期: 2026-02-09
最后更新: 2026-02-09
"""

import subprocess
import threading
import time
import os
import tempfile
import logging
from typing import Optional, Callable, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import numpy as np

# 配置日志
logger = logging.getLogger(__name__)


class AudioEffect(Enum):
    """音频效果枚举"""
    NONE = "none"
    PITCH = "pitch"
    REVERB = "reverb"
    TEMPO = "tempo"
    PHASER = "phaser"
    ECHO = "echo"
    FLANGE = "flange"
    CHORUS = "chorus"
    TREMOLO = "tremolo"
    DISTORTION = "distortion"


@dataclass
class AudioEffectParams:
    """音频效果参数"""
    effect: AudioEffect = AudioEffect.NONE
    wet_dry: float = 0.3  # 混响干湿比例
    semitones: int = 0  # 音高半音数
    tempo_factor: float = 1.0  # 速度因子
    gain_in: float = 0.8  # 输入增益
    gain_out: float = 0.8  # 输出增益
    decay: float = 0.5  # 衰减系数
    # 额外参数
    rate: float = 0.5  # 颤音/合唱速率
    depth: float = 0.5  # 颤音/合唱深度
    distortion: float = 0.5  # 失真程度


class AudioStatus(Enum):
    """音频状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AudioModule:
    """
    音频处理模块类
    处理麦克风音频流的捕获、音效修改和输出
    增强版本：添加音频缓冲管理、设备选择优化
    """

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024):
        """
        初始化音频模块

        Args:
            sample_rate: 采样率
            buffer_size: 缓冲区大小
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # 音效设置
        self.current_effect = AudioEffect.NONE
        self.effect_params = AudioEffectParams()
        
        # 状态
        self.status = AudioStatus.STOPPED
        self.is_paused = False
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        
        # 音频缓冲管理
        self.audio_buffer_size = 10  # 缓冲帧数
        self.audio_buffer: deque = deque(maxlen=10)
        self.buffer_lock = threading.Lock()
        self.input_buffer: List[np.ndarray] = []
        self.output_buffer: List[np.ndarray] = []
        
        # 统计信息
        self.frame_count = 0
        self.latency_ms = 0.0
        self.quality_score = 100.0
        self.process_time_avg = 0.0
        self.sample_count = 0
        
        # 低延迟模式
        self.low_latency_mode = False
        self.max_latency_ms = 50.0
        
        # 回调函数
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None
        self.on_statistics_update: Optional[Callable[[Dict], None]] = None
        self.on_audio_data: Optional[Callable[[np.ndarray], None]] = None
        
        # 虚拟音频设备
        self.virtual_device = None
        self.use_virtual_device = False
        
        # 检查 Sox 是否可用
        self.sox_available = self._check_sox()
        
        # 预设效果
        self.presets = self._load_presets()
        
        # 可用设备
        self.available_devices: List[Dict] = []
        self.current_input_device = None
        self.current_output_device = None
        
        # 音频设备检测
        self._detect_audio_devices()
        
        logger.info(f"AudioModule 初始化完成: sample_rate={sample_rate}, buffer_size={buffer_size}")
    
    def _detect_audio_devices(self) -> List[Dict]:
        """检测可用的音频设备"""
        self.available_devices = []
        
        try:
            # 使用 aplay 列出播放设备
            result = subprocess.run(
                ['aplay', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'card' in line and 'device' in line:
                    try:
                        parts = line.split(':')
                        card_info = parts[0].strip()
                        name = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        
                        self.available_devices.append({
                            'type': 'output',
                            'id': card_info,
                            'name': name,
                            'card': card_info.split()[1]
                        })
                    except (IndexError, KeyError):
                        continue
            
            # 使用 arecord 列出录音设备
            result = subprocess.run(
                ['arecord', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'card' in line and 'device' in line:
                    try:
                        parts = line.split(':')
                        card_info = parts[0].strip()
                        name = parts[1].strip() if len(parts) > 1 else 'Unknown'
                        
                        self.available_devices.append({
                            'type': 'input',
                            'id': card_info,
                            'name': name,
                            'card': card_info.split()[1]
                        })
                    except (IndexError, KeyError):
                        continue
                        
        except Exception as e:
            logger.warning(f"检测音频设备失败: {e}")
        
        return self.available_devices
    
    def set_input_device(self, device_id: str) -> bool:
        """
        设置输入设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 是否设置成功
        """
        for device in self.available_devices:
            if device['type'] == 'input' and device['id'] == device_id:
                self.current_input_device = device
                logger.info(f"已设置输入设备: {device['name']}")
                return True
        return False
    
    def set_output_device(self, device_id: str) -> bool:
        """
        设置输出设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 是否设置成功
        """
        for device in self.available_devices:
            if device['type'] == 'output' and device['id'] == device_id:
                self.current_output_device = device
                logger.info(f"已设置输出设备: {device['name']}")
                return True
        return False
    
    # 音频缓冲管理方法
    def add_audio_to_buffer(self, audio_data: np.ndarray) -> None:
        """添加音频数据到缓冲区"""
        with self.buffer_lock:
            self.audio_buffer.append(audio_data.copy())
            self.input_buffer.append(audio_data)
            if len(self.input_buffer) > self.audio_buffer_size:
                self.input_buffer.pop(0)
    
    def get_audio_from_buffer(self) -> Optional[np.ndarray]:
        """从缓冲区获取最新音频数据"""
        with self.buffer_lock:
            if len(self.audio_buffer) > 0:
                return self.audio_buffer[-1].copy()
        return None
    
    def clear_audio_buffer(self) -> None:
        """清空音频缓冲区"""
        with self.buffer_lock:
            self.audio_buffer.clear()
            self.input_buffer.clear()
            self.output_buffer.clear()
        logger.info("音频缓冲区已清空")
    
    def set_low_latency_mode(self, enabled: bool, max_latency_ms: float = 50.0) -> None:
        """
        设置低延迟模式
        
        Args:
            enabled: 是否启用
            max_latency_ms: 最大延迟（毫秒）
        """
        self.low_latency_mode = enabled
        self.max_latency_ms = max_latency_ms
        logger.info(f"低延迟模式已{'启用' if enabled else '禁用'} (max_latency={max_latency_ms}ms)")
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        return {
            'name': 'AudioModule',
            'status': self.status.value,
            'sox_available': self.sox_available,
            'is_running': self.status == AudioStatus.RUNNING,
            'is_paused': self.is_paused,
            'sample_rate': self.sample_rate,
            'buffer_size': self.buffer_size,
            'latency_ms': self.latency_ms,
            'quality_score': self.quality_score,
            'low_latency_mode': self.low_latency_mode,
            'buffer_level': len(self.audio_buffer)
        }

    def _check_sox(self) -> bool:
        """检查 Sox 是否可用"""
        try:
            result = subprocess.run(
                ['sox', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _load_presets(self) -> Dict[str, AudioEffectParams]:
        """加载预设效果"""
        return {
            'normal': AudioEffectParams(effect=AudioEffect.NONE),
            'deep_voice': AudioEffectParams(
                effect=AudioEffect.PITCH,
                semitones=-2
            ),
            'high_voice': AudioEffectParams(
                effect=AudioEffect.PITCH,
                semitones=2
            ),
            'robot': AudioEffectParams(
                effect=AudioEffect.PHASER,
                gain_in=0.8,
                gain_out=0.8,
                wet_dry=0.5
            ),
            'cave': AudioEffectParams(
                effect=AudioEffect.REVERB,
                wet_dry=0.5
            ),
            'fast_talker': AudioEffectParams(
                effect=AudioEffect.TEMPO,
                tempo_factor=1.5
            ),
            'slow_mo': AudioEffectParams(
                effect=AudioEffect.TEMPO,
                tempo_factor=0.7
            ),
            'telephone': AudioEffectParams(
                effect=AudioEffect.ECHO,
                decay=0.3
            )
        }

    def apply_preset(self, preset_name: str) -> bool:
        """
        应用预设效果

        Args:
            preset_name: 预设名称
            
        Returns:
            bool: 是否应用成功
        """
        if preset_name not in self.presets:
            print(f"未知预设: {preset_name}")
            return False
        
        self.effect_params = self.presets[preset_name]
        self.current_effect = self.effect_params.effect
        print(f"已应用预设: {preset_name}")
        return True

    def get_available_presets(self) -> List[str]:
        """获取可用预设列表"""
        return list(self.presets.keys())

    def start_processing(self) -> bool:
        """
        开始音频处理

        Returns:
            bool: 启动是否成功
        """
        if self.is_running:
            print("音频处理已在运行中")
            return False

        if not self.sox_available:
            print("Sox 未安装，无法启动音频处理")
            if self.on_error:
                self.on_error("Sox not installed")
            return False

        try:
            self.is_running = True
            self.is_paused = False

            # 启动音频处理线程
            self.thread = threading.Thread(target=self._audio_loop, daemon=True)
            self.thread.start()

            status = f"音频处理已启动，效果: {self.current_effect.value}"
            print(status)
            if self.on_status_change:
                self.on_status_change("started")
            return True

        except Exception as e:
            print(f"启动音频处理失败: {e}")
            self.is_running = False
            if self.on_error:
                self.on_error(str(e))
            return False

    def stop_processing(self) -> None:
        """
        停止音频处理
        """
        if not self.is_running:
            return

        self.is_running = False

        # 终止音频处理进程
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        # 等待线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        print("音频处理已停止")
        if self.on_status_change:
            self.on_status_change("stopped")

    def pause_processing(self) -> None:
        """暂停音频处理"""
        self.is_paused = True
        print("音频处理已暂停")

    def resume_processing(self) -> None:
        """恢复音频处理"""
        self.is_paused = False
        print("音频处理已恢复")

    def set_effect(self, effect: AudioEffect, **params) -> None:
        """
        设置音效

        Args:
            effect: 效果类型
            **params: 效果参数
        """
        self.current_effect = effect
        self.effect_params.effect = effect
        
        # 更新参数
        for key, value in params.items():
            if hasattr(self.effect_params, key):
                setattr(self.effect_params, key, value)
        
        print(f"音效已设置: {effect.value}")

    def get_effect_params(self) -> Dict:
        """获取当前效果参数"""
        return {
            'effect': self.effect_params.effect.value,
            'wet_dry': self.effect_params.wet_dry,
            'semitones': self.effect_params.semitones,
            'tempo_factor': self.effect_params.tempo_factor,
            'gain_in': self.effect_params.gain_in,
            'gain_out': self.effect_params.gain_out,
            'decay': self.effect_params.decay
        }

    def _build_sox_command(self) -> List[str]:
        """构建 Sox 命令"""
        cmd = ['sox']
        
        # 输入设置
        if self.use_virtual_device:
            cmd.extend(['-t', 'pulse', 'virtual_mic'])
        else:
            cmd.extend(['-t', 'alsa', 'default'])
        
        # 输出设置
        if self.use_virtual_device:
            cmd.extend(['-t', 'pulse', 'virtual_speaker'])
        else:
            cmd.extend(['-t', 'alsa', 'default'])
        
        # 添加效果
        if self.effect_params.effect == AudioEffect.PITCH:
            cmd.extend(['pitch', str(self.effect_params.semitones * 100)])
        elif self.effect_params.effect == AudioEffect.REVERB:
            cmd.extend(['reverb', str(self.effect_params.wet_dry)])
        elif self.effect_params.effect == AudioEffect.TEMPO:
            cmd.extend(['tempo', str(self.effect_params.tempo_factor)])
        elif self.effect_params.effect == AudioEffect.PHASER:
            cmd.extend(['phaser', str(self.effect_params.gain_in), 
                       str(self.effect_params.gain_out), '0.4', '0.4'])
        elif self.effect_params.effect == AudioEffect.ECHO:
            cmd.extend(['echo', '0.8', '0.9', '1000', '0.3'])
        elif self.effect_params.effect == AudioEffect.FLANGE:
            cmd.extend(['flange'])
        
        return cmd

    def _audio_loop(self) -> None:
        """
        音频处理主循环
        """
        while self.is_running:
            try:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                # 构建命令
                cmd = self._build_sox_command()
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 更新统计
                self._update_statistics()
                
                # 等待进程完成或被终止
                self.process.wait()
                
                if self.process.returncode != 0 and self.is_running:
                    error_msg = self.process.stderr.read() if self.process.stderr else "未知错误"
                    print(f"Sox处理错误: {error_msg}")
                    if self.on_error:
                        self.on_error(error_msg.strip())
                    
                    # 如果仍在运行，短暂等待后重试
                    if self.is_running:
                        time.sleep(1)

            except Exception as e:
                if self.is_running:
                    print(f"音频处理异常: {e}")
                    if self.on_error:
                        self.on_error(str(e))
                    time.sleep(1)

    def _update_statistics(self) -> None:
        """更新统计信息"""
        self.frame_count += 1
        
        # 估算延迟 (基于缓冲区大小和采样率)
        self.latency_ms = (self.buffer_size / self.sample_rate) * 1000
        
        # 计算质量分数 (基于延迟)
        if self.latency_ms < 50:
            self.quality_score = 100.0
        elif self.latency_ms < 100:
            self.quality_score = 80.0
        else:
            self.quality_score = max(0, 100 - (self.latency_ms - 100) * 0.5)
        
        # 触发回调
        if self.on_statistics_update:
            self.on_statistics_update(self.get_statistics())

    def process_audio_file(self, input_path: str, output_path: str, 
                          effect: Optional[AudioEffect] = None,
                          params: Optional[Dict] = None) -> bool:
        """
        处理音频文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            effect: 效果类型
            params: 效果参数
            
        Returns:
            bool: 是否处理成功
        """
        if not os.path.exists(input_path):
            print(f"输入文件不存在: {input_path}")
            return False
        
        try:
            cmd = ['sox', input_path, output_path]
            
            # 添加效果
            eff = effect or self.effect_params.effect
            p = params or {}
            
            if eff == AudioEffect.PITCH:
                semitones = p.get('semitones', self.effect_params.semitones)
                cmd.extend(['pitch', str(semitones * 100)])
            elif eff == AudioEffect.REVERB:
                wet_dry = p.get('wet_dry', self.effect_params.wet_dry)
                cmd.extend(['reverb', str(wet_dry)])
            elif eff == AudioEffect.TEMPO:
                factor = p.get('tempo_factor', self.effect_params.tempo_factor)
                cmd.extend(['tempo', str(factor)])
            
            # 执行命令
            result = subprocess.run(cmd, check=True, timeout=300)
            print(f"音频处理完成: {input_path} -> {output_path}")
            return result.returncode == 0
            
        except subprocess.CalledProcessError as e:
            print(f"音频处理失败: {e}")
            return False
        except Exception as e:
            print(f"音频处理异常: {e}")
            return False

    def is_processing(self) -> bool:
        """
        检查是否正在处理音频

        Returns:
            bool: 处理状态
        """
        return self.is_running

    def is_audio_paused(self) -> bool:
        """检查是否暂停"""
        return self.is_paused

    def get_statistics(self) -> Dict:
        """
        获取音频模块统计信息

        Returns:
            Dict: 统计信息字典
        """
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_effect': self.current_effect.value,
            'sample_rate': self.sample_rate,
            'buffer_size': self.buffer_size,
            'latency_ms': self.latency_ms,
            'quality_score': self.quality_score,
            'frame_count': self.frame_count,
            'sox_available': self.sox_available,
            'virtual_device': self.use_virtual_device
        }

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置错误回调函数

        Args:
            callback: 错误回调函数
        """
        self.on_error = callback

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置状态变化回调函数

        Args:
            callback: 状态回调函数
        """
        self.on_status_change = callback

    def set_statistics_callback(self, callback: Callable[[Dict], None]) -> None:
        """
        设置统计信息更新回调函数

        Args:
            callback: 统计回调函数
        """
        self.on_statistics_update = callback

    def set_virtual_device(self, device_name: str) -> bool:
        """
        设置虚拟音频设备

        Args:
            device_name: 设备名称
            
        Returns:
            bool: 是否设置成功
        """
        # 检查设备是否存在
        try:
            result = subprocess.run(
                ['pacmd', 'list-sources'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if device_name in result.stdout:
                self.virtual_device = device_name
                self.use_virtual_device = True
                print(f"已设置虚拟设备: {device_name}")
                return True
            else:
                print(f"设备不存在: {device_name}")
                return False
        except Exception as e:
            print(f"设置虚拟设备失败: {e}")
            return False

    def get_available_devices(self) -> List[str]:
        """
        获取可用的音频设备列表

        Returns:
            List[str]: 设备名称列表
        """
        devices = []
        try:
            # 使用 aplay 列出设备
            result = subprocess.run(
                ['aplay', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if 'card' in line:
                    devices.append(line.strip())
        except Exception as e:
            print(f"获取音频设备列表失败: {e}")
        
        return devices

    def enable_virtual_device(self, enable: bool) -> None:
        """
        启用或禁用虚拟设备

        Args:
            enable: 是否启用
        """
        self.use_virtual_device = enable
        print(f"虚拟设备已{'启用' if enable else '禁用'}")

    def __del__(self):
        """
        析构函数，确保资源释放
        """
        self.stop_processing()


# 便捷函数
def create_audio_module(sample_rate: int = 44100) -> AudioModule:
    """
    创建音频模块实例

    Args:
        sample_rate: 采样率
        
    Returns:
        AudioModule: 音频模块实例
    """
    return AudioModule(sample_rate=sample_rate)


def main():
    """主函数 - 测试音频模块"""
    import argparse
    
    parser = argparse.ArgumentParser(description='音频处理模块测试')
    parser.add_argument('--preset', type=str, default='normal',
                       help='预设效果')
    parser.add_argument('--list-presets', action='store_true',
                       help='列出可用预设')
    parser.add_argument('--input', type=str, help='输入音频文件')
    parser.add_argument('--output', type=str, help='输出音频文件')
    args = parser.parse_args()
    
    # 创建模块
    audio = AudioModule()
    
    if not audio.sox_available:
        print("警告: Sox 未安装")
        return
    
    print(f"Sox 可用: {audio.sox_available}")
    
    if args.list_presets:
        print("可用预设:")
        for preset in audio.get_available_presets():
            print(f"  - {preset}")
        return
    
    if args.preset:
        audio.apply_preset(args.preset)
        print(f"已应用预设: {args.preset}")
        print(f"当前效果: {audio.get_effect_params()}")
    
    if args.input and args.output:
        if audio.process_audio_file(args.input, args.output):
            print("音频处理完成")
        else:
            print("音频处理失败")


if __name__ == '__main__':
    main()

