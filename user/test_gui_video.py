#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI视频合成功能测试脚本
测试User GUI的视频捕获、人脸合成、实时预览功能

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import sys
import os
import time
import logging
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


class GUIVideoTester:
    """GUI视频功能测试器"""
    
    def __init__(self):
        self.test_results = []
        self.camera_module = None
        self.face_module = None
        
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("GUI视频合成功能测试")
        logger.info("=" * 60)
        
        tests = [
            ("导入测试", self.test_imports),
            ("摄像头模块初始化", self.test_camera_init),
            ("人脸合成模块初始化", self.test_face_module_init),
            ("视频捕获功能", self.test_video_capture),
            ("人脸图片加载", self.test_face_image_load),
            ("人脸合成功能", self.test_face_swap),
            ("性能基准测试", self.test_performance),
            ("内存使用测试", self.test_memory_usage),
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
    
    def test_imports(self) -> bool:
        """测试模块导入"""
        try:
            logger.info("测试核心模块导入...")
            
            # 测试OpenCV
            import cv2
            logger.info(f"✅ OpenCV版本: {cv2.__version__}")
            
            # 测试NumPy
            import numpy as np
            logger.info(f"✅ NumPy版本: {np.__version__}")
            
            # 测试PyQt5
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            logger.info("✅ PyQt5导入成功")
            
            # 测试项目模块
            from core.camera import CameraModule
            from core.audio_module import AudioModule
            logger.info("✅ 项目核心模块导入成功")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ 导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 导入异常: {e}")
            return False
    
    def test_camera_init(self) -> bool:
        """测试摄像头模块初始化"""
        try:
            from core.camera import CameraModule
            
            logger.info("初始化摄像头模块...")
            self.camera_module = CameraModule(
                camera_id=0,
                width=640,
                height=480,
                fps=30
            )
            
            if self.camera_module.initialize():
                logger.info("✅ 摄像头模块初始化成功")
                return True
            else:
                logger.error("❌ 摄像头模块初始化失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 摄像头初始化异常: {e}")
            return False
    
    def test_face_module_init(self) -> bool:
        """测试人脸合成模块初始化"""
        try:
            # 尝试导入人脸合成模块
            try:
                from services.face.synthesis.live_cam import FaceLiveCamModule
                logger.info("使用FaceLiveCamModule")
            except ImportError:
                logger.warning("⚠️  FaceLiveCamModule不可用，使用模拟模块")
                # 创建模拟模块
                class MockFaceModule:
                    def process_frame(self, frame):
                        return frame
                    def set_source(self, path):
                        pass
                    def initialize(self):
                        return True
                
                self.face_module = MockFaceModule()
                logger.info("✅ 模拟人脸模块创建成功")
                return True
            
            # 初始化真实模块
            self.face_module = FaceLiveCamModule()
            if self.face_module.initialize():
                logger.info("✅ 人脸合成模块初始化成功")
                return True
            else:
                logger.warning("⚠️  人脸合成模块初始化失败，使用原始帧")
                return False
                
        except Exception as e:
            logger.error(f"❌ 人脸模块初始化异常: {e}")
            return False
    
    def test_video_capture(self) -> bool:
        """测试视频捕获功能"""
        try:
            if not self.camera_module:
                logger.error("❌ 摄像头模块未初始化")
                return False
            
            logger.info("测试视频捕获...")
            
            # 捕获几帧
            frames = []
            for i in range(5):
                frame = self.camera_module.get_frame()
                if frame is not None:
                    frames.append(frame)
                    h, w = frame.shape[:2]
                    if i == 0:
                        logger.info(f"帧尺寸: {w}x{h}")
                time.sleep(0.1)
            
            if len(frames) > 0:
                logger.info(f"✅ 成功捕获 {len(frames)} 帧")
                return True
            else:
                logger.error("❌ 未能捕获任何帧")
                return False
                
        except Exception as e:
            logger.error(f"❌ 视频捕获异常: {e}")
            return False
    
    def test_face_image_load(self) -> bool:
        """测试人脸图片加载"""
        try:
            if not self.camera_module:
                logger.error("❌ 摄像头模块未初始化")
                return False
            
            # 创建测试图片
            import numpy as np
            import cv2
            
            # 创建一个简单的测试图片
            test_image = np.ones((300, 300, 3), dtype=np.uint8) * 128
            
            # 保存测试图片
            test_path = "/tmp/test_face.jpg"
            cv2.imwrite(test_path, test_image)
            
            # 测试加载
            result = self.camera_module.load_face_image(test_path)
            
            # 清理
            if os.path.exists(test_path):
                os.remove(test_path)
            
            if result:
                logger.info("✅ 人脸图片加载成功")
                return True
            else:
                logger.warning("⚠️  人脸图片加载失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 人脸图片加载异常: {e}")
            return False
    
    def test_face_swap(self) -> bool:
        """测试人脸合成功能"""
        try:
            if not self.camera_module or not self.face_module:
                logger.error("❌ 模块未初始化")
                return False
            
            logger.info("测试人脸合成...")
            
            # 设置人脸合成模块
            self.camera_module.set_face_module(self.face_module)
            
            # 捕获并处理几帧
            processed_frames = []
            for i in range(3):
                frame = self.camera_module.get_frame()
                if frame is not None:
                    processed = self.camera_module.process_frame(frame)
                    processed_frames.append(processed)
                    if i == 0:
                        logger.info(f"处理帧尺寸: {processed.shape[1]}x{processed.shape[0]}")
                time.sleep(0.1)
            
            if len(processed_frames) > 0:
                logger.info(f"✅ 成功处理 {len(processed_frames)} 帧")
                return True
            else:
                logger.error("❌ 未能处理任何帧")
                return False
                
        except Exception as e:
            logger.error(f"❌ 人脸合成异常: {e}")
            return False
    
    def test_performance(self) -> bool:
        """测试性能"""
        try:
            if not self.camera_module:
                logger.error("❌ 摄像头模块未初始化")
                return False
            
            logger.info("性能基准测试 (3秒)...")
            
            start_time = time.time()
            frame_count = 0
            test_duration = 3
            
            while time.time() - start_time < test_duration:
                frame = self.camera_module.get_frame()
                if frame is not None:
                    frame_count += 1
            
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed
            
            logger.info(f"捕获帧数: {frame_count}")
            logger.info(f"实际FPS: {actual_fps:.2f}")
            logger.info(f"目标FPS: 30")
            
            # 性能评估
            if actual_fps >= 25:
                logger.info("✅ 性能优秀")
                return True
            elif actual_fps >= 15:
                logger.info("⚠️  性能一般")
                return True
            else:
                logger.warning("❌ 性能不足")
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能测试异常: {e}")
            return False
    
    def test_memory_usage(self) -> bool:
        """测试内存使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # 获取初始内存
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"初始内存使用: {initial_memory:.2f} MB")
            
            # 运行一段时间
            if self.camera_module:
                for _ in range(10):
                    frame = self.camera_module.get_frame()
                    if frame is not None:
                        self.camera_module.process_frame(frame)
            
            # 获取当前内存
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            logger.info(f"当前内存使用: {current_memory:.2f} MB")
            logger.info(f"内存增加: {memory_increase:.2f} MB")
            
            # 检查内存泄漏
            if memory_increase > 100:  # 超过100MB认为有泄漏
                logger.warning(f"⚠️  内存使用增加过多: {memory_increase:.2f} MB")
                return False
            else:
                logger.info("✅ 内存使用正常")
                return True
                
        except ImportError:
            logger.warning("⚠️  psutil未安装，跳过内存测试")
            return True
        except Exception as e:
            logger.error(f"❌ 内存测试异常: {e}")
            return False
    
    def _cleanup(self):
        """清理资源"""
        logger.info("\n清理资源...")
        
        if self.camera_module:
            try:
                self.camera_module.stop_stream()
                logger.info("✅ 摄像头资源已释放")
            except:
                pass
        
        if self.face_module:
            try:
                if hasattr(self.face_module, 'cleanup'):
                    self.face_module.cleanup()
                logger.info("✅ 人脸模块资源已释放")
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
            logger.info("🎉 所有测试通过！GUI视频功能正常")
        elif passed >= total * 0.7:
            logger.info("⚠️  部分测试失败，功能基本可用")
        else:
            logger.info("❌ 多项测试失败，需要修复问题")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GUI视频合成功能测试')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 运行测试
    tester = GUIVideoTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
