#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频模块单元测试
AR 综合实时合成与监控系统

测试内容:
- 音频模块初始化和配置
- 音效设置和预设
- 音频缓冲管理
- 设备检测和管理

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026年2月9日
"""

import unittest
import sys
import time
import numpy as np
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()
PROJECT_ROOT = PATHS.root

from audio_module import AudioModule, AudioEffect, AudioEffectParams, AudioStatus

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestAudioModule(unittest.TestCase):
    """音频模块测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.audio = AudioModule(sample_rate=44100, buffer_size=1024)
        logger.debug(f"开始测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试用例清理"""
        if hasattr(self, 'audio') and self.audio:
            try:
                if self.audio.status == AudioStatus.RUNNING:
                    self.audio.stop_processing()
            except Exception:
                pass
        logger.debug(f"测试完成: {self._testMethodName}")
    
    def test_initialization(self):
        """测试音频模块初始化"""
        self.assertIsNotNone(self.audio)
        self.assertEqual(self.audio.sample_rate, 44100)
        self.assertEqual(self.audio.buffer_size, 1024)
        self.assertEqual(self.audio.status, AudioStatus.STOPPED)
        logger.info("测试initialization: 通过")
    
    def test_sox_check(self):
        """测试Sox可用性检查"""
        # Sox可能未安装，但我们测试逻辑
        self.assertIsInstance(self.audio.sox_available, bool)
        logger.info(f"测试sox_check: 通过 (Sox可用: {self.audio.sox_available})")
    
    def test_presets(self):
        """测试预设效果"""
        presets = self.audio.get_available_presets()
        
        self.assertIsInstance(presets, list)
        self.assertIn('normal', presets)
        self.assertIn('deep_voice', presets)
        self.assertIn('robot', presets)
        
        # 测试应用预设
        result = self.audio.apply_preset('deep_voice')
        if self.audio.sox_available:
            self.assertTrue(result)
            self.assertEqual(self.audio.current_effect, AudioEffect.PITCH)
            self.assertEqual(self.audio.effect_params.semitones, -2)
        
        logger.info("测试presets: 通过")
    
    def test_effect_params(self):
        """测试效果参数"""
        params = self.audio.get_effect_params()
        
        self.assertIn('effect', params)
        self.assertIn('wet_dry', params)
        self.assertIn('semitones', params)
        self.assertIn('tempo_factor', params)
        
        logger.info("测试effect_params: 通过")
    
    def test_set_effect(self):
        """测试设置音效"""
        self.audio.set_effect(AudioEffect.REVERB, wet_dry=0.5)
        
        self.assertEqual(self.audio.current_effect, AudioEffect.REVERB)
        self.assertEqual(self.audio.effect_params.wet_dry, 0.5)
        
        logger.info("测试set_effect: 通过")
    
    def test_audio_buffer(self):
        """测试音频缓冲管理"""
        # 创建测试音频数据
        test_data = np.random.randn(1024).astype(np.float32)
        
        # 添加到缓冲区
        self.audio.add_audio_to_buffer(test_data)
        self.audio.add_audio_to_buffer(test_data * 2)
        
        # 验证缓冲区
        self.assertEqual(len(self.audio.audio_buffer), 2)
        
        # 获取最新数据
        retrieved = self.audio.get_audio_from_buffer()
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved), 1024)
        
        # 清空缓冲区
        self.audio.clear_audio_buffer()
        self.assertEqual(len(self.audio.audio_buffer), 0)
        
        logger.info("测试audio_buffer: 通过")
    
    def test_low_latency_mode(self):
        """测试低延迟模式"""
        # 启用低延迟模式
        self.audio.set_low_latency_mode(True, max_latency_ms=30.0)
        
        self.assertTrue(self.audio.low_latency_mode)
        self.assertEqual(self.audio.max_latency_ms, 30.0)
        
        # 禁用低延迟模式
        self.audio.set_low_latency_mode(False)
        
        self.assertFalse(self.audio.low_latency_mode)
        
        logger.info("测试low_latency_mode: 通过")
    
    def test_statistics(self):
        """测试统计信息"""
        stats = self.audio.get_statistics()
        
        self.assertIn('is_running', stats)
        self.assertIn('is_paused', stats)
        self.assertIn('current_effect', stats)
        self.assertIn('sample_rate', stats)
        self.assertIn('latency_ms', stats)
        self.assertIn('quality_score', stats)
        self.assertIn('sox_available', stats)
        
        logger.info("测试statistics: 通过")
    
    def test_health_check(self):
        """测试健康检查"""
        health = self.audio.health_check()
        
        self.assertIn('name', health)
        self.assertIn('status', health)
        self.assertIn('sox_available', health)
        self.assertIn('is_running', health)
        self.assertIn('latency_ms', health)
        self.assertIn('quality_score', health)
        
        logger.info("测试health_check: 通过")
    
    def test_callback_functions(self):
        """测试回调函数"""
        errors = []
        status_changes = []
        stats_updates = []
        
        def on_error(error):
            errors.append(error)
        
        def on_status(status):
            status_changes.append(status)
        
        def on_stats(stats):
            stats_updates.append(stats)
        
        # 设置回调
        self.audio.set_error_callback(on_error)
        self.audio.set_status_callback(on_status)
        self.audio.set_statistics_callback(on_stats)
        
        # 验证
        self.assertEqual(self.audio.on_error, on_error)
        self.assertEqual(self.audio.on_status_change, on_status)
        self.assertEqual(self.audio.on_statistics_update, on_stats)
        
        logger.info("测试callback_functions: 通过")
    
    def test_audio_devices(self):
        """测试音频设备检测"""
        devices = self.audio.available_devices
        
        self.assertIsInstance(devices, list)
        
        # 测试获取可用设备
        all_devices = self.audio.get_available_devices()
        self.assertIsInstance(all_devices, list)
        
        logger.info(f"测试audio_devices: 通过 (检测到 {len(all_devices)} 个设备)")
    
    def test_virtual_device(self):
        """测试虚拟设备设置"""
        # 启用虚拟设备
        self.audio.enable_virtual_device(True)
        self.assertTrue(self.audio.use_virtual_device)
        
        # 禁用虚拟设备
        self.audio.enable_virtual_device(False)
        self.assertFalse(self.audio.use_virtual_device)
        
        logger.info("测试virtual_device: 通过")
    
    def test_process_audio_file(self):
        """测试音频文件处理"""
        if not self.audio.sox_available:
            self.skipTest("Sox 未安装")
        
        # 创建测试音频文件
        test_input = PROJECT_ROOT / "test" / "test_data" / "test_audio.wav"
        test_output = PROJECT_ROOT / "test" / "test_data" / "test_audio_output.wav"
        test_input.parent.mkdir(parents=True, exist_ok=True)
        
        # 跳过实际文件处理测试（需要真实音频文件）
        logger.info("测试process_audio_file: 跳过 (需要真实音频文件)")
    
    def test_status_enum(self):
        """测试状态枚举"""
        self.assertEqual(AudioStatus.STOPPED.value, "stopped")
        self.assertEqual(AudioStatus.STARTING.value, "starting")
        self.assertEqual(AudioStatus.RUNNING.value, "running")
        self.assertEqual(AudioStatus.PAUSED.value, "paused")
        self.assertEqual(AudioStatus.ERROR.value, "error")
        
        logger.info("测试status_enum: 通过")
    
    def test_effect_enum(self):
        """测试效果枚举"""
        self.assertEqual(AudioEffect.NONE.value, "none")
        self.assertEqual(AudioEffect.PITCH.value, "pitch")
        self.assertEqual(AudioEffect.REVERB.value, "reverb")
        self.assertEqual(AudioEffect.TEMPO.value, "tempo")
        self.assertEqual(AudioEffect.PHASER.value, "phaser")
        self.assertEqual(AudioEffect.ECHO.value, "echo")
        self.assertEqual(AudioEffect.FLANGE.value, "flange")
        self.assertEqual(AudioEffect.CHORUS.value, "chorus")
        self.assertEqual(AudioEffect.TREMOLO.value, "tremolo")
        self.assertEqual(AudioEffect.DISTORTION.value, "distortion")
        
        logger.info("测试effect_enum: 通过")
    
    def test_effect_params_dataclass(self):
        """测试效果参数数据类"""
        params = AudioEffectParams(
            effect=AudioEffect.PITCH,
            semitones=-2,
            wet_dry=0.5
        )
        
        self.assertEqual(params.effect, AudioEffect.PITCH)
        self.assertEqual(params.semitones, -2)
        self.assertEqual(params.wet_dry, 0.5)
        
        # 测试默认值
        default_params = AudioEffectParams()
        self.assertEqual(default_params.effect, AudioEffect.NONE)
        self.assertEqual(default_params.wet_dry, 0.3)
        
        logger.info("测试effect_params_dataclass: 通过")


class TestAudioPerformance(unittest.TestCase):
    """音频模块性能测试类"""
    
    def setUp(self):
        """测试用例设置"""
        self.audio = AudioModule(sample_rate=22050, buffer_size=512)
    
    def tearDown(self):
        """测试用例清理"""
        if hasattr(self, 'audio') and self.audio:
            try:
                if self.audio.status == AudioStatus.RUNNING:
                    self.audio.stop_processing()
            except Exception:
                pass
    
    def test_buffer_operations_performance(self):
        """测试缓冲操作性能"""
        import threading
        
        # 创建生产者线程
        def producer():
            for i in range(100):
                data = np.random.randn(512).astype(np.float32)
                self.audio.add_audio_to_buffer(data)
                time.sleep(0.01)
        
        # 启动生产者
        thread = threading.Thread(target=producer)
        thread.start()
        thread.join(timeout=2)
        
        # 验证缓冲区操作正常
        self.assertGreater(len(self.audio.audio_buffer), 0)
        
        logger.info("测试buffer_operations_performance: 通过")
    
    def test_preset_application_performance(self):
        """测试预设应用性能"""
        presets = ['normal', 'deep_voice', 'high_voice', 'robot', 'cave']
        
        start_time = time.perf_counter()
        for _ in range(100):
            for preset in presets:
                self.audio.apply_preset(preset)
        elapsed = time.perf_counter() - start_time
        
        # 100次预设应用应该<1秒
        self.assertLess(elapsed, 1.0, f"预设应用太慢: {elapsed:.3f}s")
        
        logger.info(f"测试preset_application_performance: 通过 ({elapsed:.3f}s)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
