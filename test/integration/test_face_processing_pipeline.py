#!/usr/bin/env python3
"""
Face Processing Pipeline Integration Tests
测试人脸检测 → 识别 → GUI/Camera 数据联动
"""

import unittest
import numpy as np
import cv2
import sys
from pathlib import Path
from unittest.mock import Mock, patch

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import add_project_paths

PATHS = add_project_paths()

from face_live_cam import FaceLiveCamModule, FaceInfo
from camera import CameraModule


class TestFaceProcessingPipeline(unittest.TestCase):
    """人脸处理管道集成测试类"""

    def setUp(self) -> None:
        """测试前准备"""
        self.face_module: Optional[FaceLiveCamModule] = FaceLiveCamModule()
        self.camera: Optional[CameraModule] = CameraModule()

        # 创建测试数据目录
        self.test_data_dir: Path = Path(__file__).parent.parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

        # 创建测试图像
        self._create_test_images()

    def tearDown(self) -> None:
        """测试后清理"""
        if self.face_module:
            try:
                self.face_module.cleanup()
            except Exception:
                pass
        if self.camera:
            try:
                # 清理相机资源
                pass
            except Exception:
                pass

    def _create_test_images(self) -> None:
        """创建测试图像"""
        try:
            # 创建源人脸图像
            self.source_image_path: Path = self.test_data_dir / "pipeline_source.jpg"
            img: np.ndarray = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            success: bool = cv2.imwrite(str(self.source_image_path), img)
            if not success:
                raise IOError(f"无法写入源人脸图像: {self.source_image_path}")

            # 创建测试帧
            self.test_frame_path: Path = self.test_data_dir / "pipeline_frame.jpg"
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            success = cv2.imwrite(str(self.test_frame_path), img)
            if not success:
                raise IOError(f"无法写入测试帧图像: {self.test_frame_path}")
        except Exception as e:
            self.fail(f"创建测试图像失败: {e}")

    def test_pipeline_initialization(self) -> None:
        """测试管道初始化"""
        try:
            # 初始化人脸模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")

            # 初始化相机模块
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 设置人脸模块到相机
            self.camera.set_face_module(self.face_module)

            # 验证设置
            self.assertIsNotNone(self.camera.face_module, "相机应设置人脸模块")
        except Exception as e:
            self.fail(f"管道初始化测试失败: {e}")

    def test_face_detection_integration(self) -> None:
        """测试人脸检测集成"""
        try:
            # 初始化模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 设置人脸检测处理器
            self.camera.set_face_detection_processor(self.face_module)

            # 创建测试帧
            test_frame: Optional[np.ndarray] = cv2.imread(str(self.test_frame_path))
            self.assertIsNotNone(test_frame, "无法加载测试帧")

            # 执行人脸检测
            if test_frame is not None:
                faces = self.camera._run_face_detection(test_frame)
            else:
                self.fail("无法加载测试帧")

            # 验证结果
            self.assertIsInstance(faces, list, "人脸检测结果应为列表")
            self.assertEqual(self.camera.last_face_count, len(faces), "人脸计数不匹配")
        except Exception as e:
            self.fail(f"人脸检测集成测试失败: {e}")

    def test_face_recognition_integration(self) -> None:
        """测试人脸识别集成"""
        try:
            # 初始化模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 设置人脸识别处理器
            self.camera.set_face_recognition_processor(self.face_module)

            # 设置源人脸
            self.face_module.set_source(str(self.source_image_path))

            # 创建测试帧
            test_frame: Optional[np.ndarray] = cv2.imread(str(self.test_frame_path))
            self.assertIsNotNone(test_frame, "无法加载测试帧")

            # 执行人脸识别
            faces = self.camera._run_face_detection(test_frame)

            # 验证结果
            self.assertIsInstance(faces, list, "人脸识别结果应为列表")
        except Exception as e:
            self.fail(f"人脸识别集成测试失败: {e}")

    def test_camera_face_module_integration(self) -> None:
        """测试相机与人脸模块集成"""
        try:
            # 初始化模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 设置人脸模块
            self.camera.set_face_module(self.face_module)

            # 加载源人脸图像
            result: bool = self.camera.load_face_image(str(self.source_image_path))
            # 结果可能为False（如果图像中无人脸），这是正常的
            self.assertIsInstance(result, bool, "加载人脸图像结果应为布尔值")
        except Exception as e:
            self.fail(f"相机与人脸模块集成测试失败: {e}")

    def test_data_flow_integration(self):
        """测试数据流集成"""
        # 初始化模块
        self.assertTrue(self.face_module.initialize())
        self.assertTrue(self.camera.initialize())

        # 设置回调
        detected_faces = []
        def face_callback(faces):
            detected_faces.extend(faces)

        self.camera.set_faces_callback(face_callback)

        # 创建测试帧
        test_frame = cv2.imread(str(self.test_frame_path))
        self.assertIsNotNone(test_frame)

        # 处理帧
        if test_frame is not None:
            faces = self.camera._run_face_detection(test_frame)
        else:
            self.fail("Failed to load test frame")

        # 验证数据流
        self.assertEqual(len(detected_faces), len(faces))
        self.assertEqual(self.camera.last_faces, faces)

    def test_pipeline_performance(self) -> None:
        """测试管道性能"""
        try:
            # 初始化模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 创建测试帧
            test_frame: Optional[np.ndarray] = cv2.imread(str(self.test_frame_path))
            self.assertIsNotNone(test_frame, "无法加载测试帧")

            # 执行多次处理测试性能
            import time
            start_time: float = time.time()

            if test_frame is not None:
                for _ in range(10):
                    faces = self.camera._run_face_detection(test_frame)
            else:
                self.fail("无法加载测试帧")

            end_time: float = time.time()
            avg_time: float = (end_time - start_time) / 10

            # 验证性能（应该在合理范围内）
            self.assertLess(avg_time, 1.0, f"平均处理时间 {avg_time:.3f} 秒超过1秒限制")
        except Exception as e:
            self.fail(f"管道性能测试失败: {e}")

    def test_error_handling_integration(self) -> None:
        """测试错误处理集成"""
        try:
            # 初始化模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 测试无效输入 - 这里我们不直接调用内部方法，而是测试边界情况
            # 由于_run_face_detection是私有方法，我们测试公开接口
            faces = self.camera._run_face_detection(np.zeros((100, 100, 3), dtype=np.uint8))

            # 验证结果类型
            self.assertIsInstance(faces, list, "人脸检测结果应为列表")
        except Exception as e:
            self.fail(f"错误处理集成测试失败: {e}")

    def test_module_cleanup_integration(self) -> None:
        """测试模块清理集成"""
        try:
            # 初始化模块
            self.assertTrue(self.face_module.initialize(), "人脸模块初始化失败")
            self.assertTrue(self.camera.initialize(), "相机模块初始化失败")

            # 执行一些操作
            test_frame: Optional[np.ndarray] = cv2.imread(str(self.test_frame_path))
            if test_frame is not None:
                self.camera._run_face_detection(test_frame)

            # 清理模块
            self.face_module.cleanup()

            # 验证清理状态
            self.assertFalse(self.face_module.initialized, "人脸模块应被清理")
        except Exception as e:
            self.fail(f"模块清理集成测试失败: {e}")


if __name__ == '__main__':
    unittest.main()
