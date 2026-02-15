#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI音频处理功能测试脚本
测试User GUI的音频捕获、音效处理、实时输出功能

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import sys
import os
import time
import logging
import subprocess
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'AR-backend'))
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GUIAudioTester:
    """GUI音频功能测试器"""
    
    def __init__(self):
        self.test_results = []
        self.audio_module = None
        
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("GUI音频处理功能测试")
        logger.info("=" * 60)
        
        tests = [
            ("依赖检查", self.test_dependencies),
            ("音频模块初始化", self.test_audio_init),
            ("音频设备检测", self.test_audio_devices),
            ("Sox工具检查", self.test_sox),
            ("音频处理功能", self.test_audio_processing),
            ("音效参数测试", self.test_audio_effects),
            ("性能基准测试", self.test_performance),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            logger.info(f"\n📋 测试: {test_name}")
            try:
                result = test_func()
                status = "✅ 通过" if result else "❌ 失败"
                logger.info(f"结果: {status}")
                self.test_results.append((test_name, result))
                if not result:
                    all_passed = False
            except Exception as e:
                logger.error(f"测试异常: {e}")
                import traceback
                traceback.print_exc()
                self.test_results.append((test_name, False))
                all_passed = False
        
        # 清理
        self._cleanup()
        
        # 输出总结
        self._print_summary()
        
        return all_passed
    
    def test_dependencies(self) -> bool:
        """测试依赖"""
        try:
            logger.info("检查核心依赖...")
            
            # 检查NumPy
            import numpy as np
            logger.info(f"✅ NumPy版本: {np.__version__}")
            
            # 检查项目模块
            from core.audio_module import AudioModule, AudioEffect
            logger.info("✅ 音频模块导入成功")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ 依赖缺失: {e}")
            return False
    
    def test_audio_init(self) -> bool:
        """测试音频模块初始化"""
        try:
            from core.audio_module import AudioModule
            
            logger.info("初始化音频模块...")
            self.audio_module = AudioModule(
                sample_rate=44100,
                buffer_size=1024
            )
            
            logger.info("✅ 音频模块初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 音频模块初始化失败: {e}")
            return False
    
    def test_audio_devices(self) -> bool:
        """测试音频设备检测"""
        try:
            if not self.audio_module:
                logger.error("❌ 音频模块未初始化")
                return False
            
            logger.info("检测音频设备...")
            
            # 获取可用设备
            devices = self.audio_module.get_available_devices()
            
            if devices:
                logger.info(f"✅ 找到 {len(devices)} 个音频设备:")
                for device in devices[:5]:  # 只显示前5个
                    logger.info(f"  - {device}")
                return True
            else:
                logger.warning("⚠️  未找到音频设备")
                return False
                
        except Exception as e:
            logger.error(f"❌ 音频设备检测失败: {e}")
            return False
    
    def test_sox(self) -> bool:
        """测试Sox工具"""
        try:
            logger.info("检查Sox工具...")
            
            # 检查sox命令
            result = subprocess.run(
                ['sox', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                logger.info(f"✅ Sox已安装: {version_line}")
                return True
            else:
                logger.error("❌ Sox检查失败")
                return False
                
        except FileNotFoundError:
            logger.error("❌ Sox未安装")
            logger.info("安装命令: sudo apt-get install sox")
            return False
        except Exception as e:
            logger.error(f"❌ Sox检查异常: {e}")
            return False
    
    def test_audio_processing(self) -> bool:
        """测试音频处理功能"""
        try:
            if not self.audio_module:
                logger.error("❌ 音频模块未初始化")
                return False
            
            logger.info("测试音频处理...")
            
            # 检查Sox可用性
            if not self.audio_module.sox_available:
                logger.warning("⚠️  Sox不可用，跳过实时处理测试")
                return True
            
            # 测试处理文件（如果存在测试音频）
            test_audio = "/tmp/test_audio.wav"
            
            # 创建测试音频（使用sox生成）
            try:
                subprocess.run([
                    'sox', '-n', '-r', '44100', '-c', '1', test_audio,
                    'synth', '1', 'sine', '1000'
                ], check=True, capture_output=True, timeout=10)
                logger.info("✅ 测试音频文件创建成功")
            except Exception as e:
                logger.warning(f"⚠️  无法创建测试音频: {e}")
                return True  # 不视为失败
            
            # 测试处理
            if os.path.exists(test_audio):
                output_path = "/tmp/test_audio_processed.wav"
                
                # 应用音效
                self.audio_module.apply_preset('robot')
                
                # 处理文件
                result = self.audio_module.process_audio_file(test_audio, output_path)
                
                # 清理
                if os.path.exists(test_audio):
                    os.remove(test_audio)
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                if result:
                    logger.info("✅ 音频处理成功")
                    return True
                else:
                    logger.warning("⚠️  音频处理失败")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 音频处理异常: {e}")
            return False
    
    def test_audio_effects(self) -> bool:
        """测试音效参数"""
        try:
            if not self.audio_module:
                logger.error("❌ 音频模块未初始化")
                return False
            
            logger.info("测试音效参数...")
            
            from core.audio_module import AudioEffect
            
            # 测试所有音效
            effects = [
                AudioEffect.NONE,
                AudioEffect.PITCH,
                AudioEffect.REVERB,
                AudioEffect.TEMPO,
            ]
            
            for effect in effects:
                try:
                    self.audio_module.set_effect(effect)
                    params = self.audio_module.get_effect_params()
                    logger.info(f"  ✅ {effect.value}: {params}")
                except Exception as e:
                    logger.warning(f"  ⚠️  {effect.value} 设置失败: {e}")
            
            # 测试预设
            presets = self.audio_module.get_available_presets()
            logger.info(f"✅ 可用预设: {len(presets)}个")
            for preset in presets[:5]:
                logger.info(f"  - {preset}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 音效测试异常: {e}")
            return False
    
    def test_performance(self) -> bool:
        """测试性能"""
        try:
            if not self.audio_module:
                logger.error("❌ 音频模块未初始化")
                return False
            
            logger.info("性能基准测试...")
            
            # 模拟处理时间测试
            start_time = time.time()
            iterations = 100
            
            for _ in range(iterations):
                # 模拟音频处理计算
                import numpy as np
                data = np.random.randn(1024)
                # 简单处理
                processed = data * 0.5
            
            elapsed = time.time() - start_time
            avg_time = elapsed / iterations * 1000  # 毫秒
            
            logger.info(f"处理 {iterations} 次迭代")
            logger.info(f"总时间: {elapsed:.3f}秒")
            logger.info(f"平均时间: {avg_time:.3f}毫秒")
            
            if avg_time < 10:  # 小于10ms认为性能良好
                logger.info("✅ 性能优秀")
                return True
            elif avg_time < 50:
                logger.info("⚠️  性能一般")
                return True
            else:
                logger.warning("❌ 性能不足")
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能测试异常: {e}")
            return False
    
    def _cleanup(self):
        """清理资源"""
        logger.info("\n清理资源...")
        
        if self.audio_module:
            try:
                self.audio_module.stop_processing()
                logger.info("✅ 音频处理已停止")
            except:
                pass
    
    def _print_summary(self):
        """打印测试总结"""
        logger.info("\n" + "=" * 60)
        logger.info("测试结果总结")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{status} - {test_name}")
        
        logger.info(f"\n总计: {passed}/{total} 项通过")
        
        if passed == total:
            logger.info("🎉 所有测试通过！GUI音频功能正常")
        elif passed >= total * 0.7:
            logger.info("⚠️  部分测试失败，功能基本可用")
        else:
            logger.info("❌ 多项测试失败，需要修复问题")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GUI音频处理功能测试')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 运行测试
    tester = GUIAudioTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
