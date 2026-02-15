#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟摄像头功能测试脚本
测试v4l2loopback虚拟摄像头的创建和使用

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-11
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.camera import CameraModule

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VirtualCameraTester:
    """虚拟摄像头测试器"""
    
    def __init__(self):
        self.test_results = []
        self.virtual_device = None
        
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("虚拟摄像头功能测试")
        logger.info("=" * 60)
        
        tests = [
            ("检查v4l2loopback模块", self.test_v4l2loopback_module),
            ("检查虚拟摄像头设备", self.test_virtual_devices),
            ("测试摄像头捕获", self.test_camera_capture),
            ("测试虚拟摄像头输出", self.test_virtual_output),
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
                self.test_results.append((test_name, False))
                all_passed = False
        
        # 输出总结
        self._print_summary()
        
        return all_passed
    
    def test_v4l2loopback_module(self) -> bool:
        """测试v4l2loopback内核模块"""
        try:
            # 检查模块是否加载
            result = subprocess.run(
                ['lsmod'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if 'v4l2loopback' in result.stdout:
                logger.info("✅ v4l2loopback模块已加载")
                return True
            else:
                logger.warning("⚠️  v4l2loopback模块未加载")
                logger.info("尝试加载模块...")
                
                # 尝试加载模块
                load_result = subprocess.run(
                    ['sudo', 'modprobe', 'v4l2loopback'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if load_result.returncode == 0:
                    logger.info("✅ 模块加载成功")
                    return True
                else:
                    logger.error(f"❌ 模块加载失败: {load_result.stderr}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 检查模块失败: {e}")
            return False
    
    def test_virtual_devices(self) -> bool:
        """测试虚拟摄像头设备"""
        try:
            # 检查/dev/video*设备
            video_devices = []
            for i in range(10):
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    video_devices.append(device_path)
            
            if not video_devices:
                logger.warning("⚠️  未找到任何视频设备")
                return False
            
            logger.info(f"找到 {len(video_devices)} 个视频设备:")
            for device in video_devices:
                logger.info(f"  - {device}")
            
            # 检查v4l2-ctl
            try:
                result = subprocess.run(
                    ['v4l2-ctl', '--list-devices'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logger.info("设备详细信息:")
                    for line in result.stdout.split('\n')[:20]:
                        if line.strip():
                            logger.info(f"  {line}")
                    return True
                else:
                    logger.warning("⚠️  v4l2-ctl命令执行失败")
                    return False
                    
            except FileNotFoundError:
                logger.warning("⚠️  v4l2-ctl未安装")
                return False
                
        except Exception as e:
            logger.error(f"❌ 检查设备失败: {e}")
            return False
    
    def test_camera_capture(self) -> bool:
        """测试摄像头捕获"""
        try:
            camera = CameraModule(camera_id=0, width=640, height=480, fps=30)
            
            if not camera.initialize():
                logger.error("❌ 摄像头初始化失败")
                return False
            
            logger.info("✅ 摄像头初始化成功")
            
            # 捕获几帧测试
            capture_count = 0
            max_captures = 10
            
            for _ in range(max_captures):
                frame = camera.get_frame()
                if frame is not None:
                    capture_count += 1
                    h, w = frame.shape[:2]
                    if capture_count == 1:
                        logger.info(f"帧尺寸: {w}x{h}")
            
            camera.stop_stream()
            
            if capture_count > 0:
                logger.info(f"✅ 成功捕获 {capture_count}/{max_captures} 帧")
                return True
            else:
                logger.error("❌ 未能捕获任何帧")
                return False
                
        except Exception as e:
            logger.error(f"❌ 摄像头测试失败: {e}")
            return False
    
    def test_virtual_output(self) -> bool:
        """测试虚拟摄像头输出"""
        try:
            # 检查是否可以写入虚拟设备
            virtual_devices = []
            for i in range(10):
                device = f"/dev/video{i}"
                if os.path.exists(device):
                    # 检查是否可写
                    if os.access(device, os.W_OK):
                        virtual_devices.append(device)
            
            if virtual_devices:
                logger.info(f"✅ 找到 {len(virtual_devices)} 个可写的视频设备")
                for device in virtual_devices:
                    logger.info(f"  - {device}")
                return True
            else:
                logger.warning("⚠️  未找到可写的虚拟摄像头设备")
                logger.info("提示: 可能需要创建v4l2loopback设备")
                return False
                
        except Exception as e:
            logger.error(f"❌ 虚拟输出测试失败: {e}")
            return False
    
    def test_performance(self) -> bool:
        """性能基准测试"""
        try:
            import cv2
            import time
            
            camera = CameraModule(camera_id=0, width=640, height=480, fps=30)
            
            if not camera.initialize():
                return False
            
            logger.info("开始性能测试 (5秒)...")
            
            start_time = time.time()
            frame_count = 0
            test_duration = 5
            
            while time.time() - start_time < test_duration:
                frame = camera.get_frame()
                if frame is not None:
                    frame_count += 1
            
            camera.stop_stream()
            
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed
            
            logger.info(f"捕获帧数: {frame_count}")
            logger.info(f"实际FPS: {actual_fps:.2f}")
            logger.info(f"目标FPS: 30")
            
            # 检查性能
            if actual_fps >= 25:
                logger.info("✅ 性能达标")
                return True
            elif actual_fps >= 15:
                logger.warning("⚠️  性能一般，可能有卡顿")
                return True
            else:
                logger.error("❌ 性能不足，需要优化")
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            return False
    
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
            logger.info("🎉 所有测试通过！")
        elif passed >= total * 0.6:
            logger.info("⚠️  部分测试失败，功能基本可用")
        else:
            logger.info("❌ 多项测试失败，需要修复问题")


def create_virtual_camera_device():
    """创建虚拟摄像头设备（需要root权限）"""
    logger.info("尝试创建虚拟摄像头设备...")
    
    try:
        # 检查是否已存在
        result = subprocess.run(
            ['v4l2-ctl', '--list-devices'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'platform:v4l2loopback' in result.stdout:
            logger.info("✅ 虚拟摄像头设备已存在")
            return True
        
        # 加载模块并创建设备
        logger.info("加载v4l2loopback模块...")
        subprocess.run(
            ['sudo', 'modprobe', 'v4l2loopback', 'devices=1'],
            check=True,
            timeout=10
        )
        
        logger.info("✅ 虚拟摄像头设备创建成功")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 创建设备失败: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ v4l2loopback未安装")
        logger.info("安装命令: sudo apt-get install v4l2loopback-dkms")
        return False
    except Exception as e:
        logger.error(f"❌ 创建设备异常: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='虚拟摄像头功能测试')
    parser.add_argument('--create-device', action='store_true',
                       help='尝试创建虚拟摄像头设备（需要root）')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建设备（如果需要）
    if args.create_device:
        if not create_virtual_camera_device():
            logger.error("无法创建虚拟摄像头设备")
            sys.exit(1)
    
    # 运行测试
    tester = VirtualCameraTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
