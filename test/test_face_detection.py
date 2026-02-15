#!/usr/bin/env python3
"""
Face Detection Unit Tests
测试人脸检测核心逻辑
"""

import unittest
from typing import Optional, List, Tuple
import numpy as np
import cv2
from pathlib import Path

from test_utils import add_project_paths

PATHS = add_project_paths()

from face_live_cam import FaceLiveCamModule, FaceInfo


class TestFaceDetection(unittest.TestCase):
    """人脸检测测试类"""

    def setUp(self) -> None:
        """测试前准备"""
        self.module: FaceLiveCamModule = FaceLiveCamModule()
        self.test_image_path: Path = Path(__file__).parent / "test_data" / "test_face.jpg"

        # 创建测试数据目录
        self.test_data_dir: Path = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

        # 创建测试图像
        self._create_test_image()

    def tearDown(self):
        """测试后清理"""
        if self.module:
            self.module.cleanup()

    def _create_test_image(self) -> None:
        """创建测试图像"""
        try:
            # 创建一个简单的测试图像（随机颜色块）
            img: np.ndarray = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            success: bool = cv2.imwrite(str(self.test_image_path), img)
            if not success:
                raise IOError(f"无法写入测试图像: {self.test_image_path}")
        except Exception as e:
            self.fail(f"创建测试图像失败: {e}")

    def test_module_initialization(self):
        """测试模块初始化"""
        self.assertTrue(self.module.initialize())
        self.assertTrue(self.module.initialized)
        self.assertIsNotNone(self.module.face_detector)
        self.assertIn(self.module.detector_type, ['dnn', 'haar'])

    def test_face_info_dataclass(self) -> None:
        """测试FaceInfo数据类"""
        bbox: Tuple[int, int, int, int] = (10, 20, 50, 60)
        confidence: float = 0.95
        face_id: int = 1

        try:
            face_info: FaceInfo = FaceInfo(
                bbox=bbox,
                confidence=confidence,
                face_id=face_id
            )

            self.assertEqual(face_info.bbox, bbox, "边界框不匹配")
            self.assertEqual(face_info.confidence, confidence, "置信度不匹配")
            self.assertEqual(face_info.face_id, face_id, "人脸ID不匹配")
            self.assertIsNotNone(face_info.landmarks, "关键点不应为空")
        except Exception as e:
            self.fail(f"FaceInfo数据类测试失败: {e}")

    def test_detect_faces_in_image(self):
        """测试图像中的人脸检测"""
        # 初始化模块
        self.assertTrue(self.module.initialize())

        # 读取测试图像
        image = cv2.imread(str(self.test_image_path))
        self.assertIsNotNone(image)

        # 检测人脸（随机图像可能不包含人脸，这是正常的）
        if image is not None:
            faces = self.module._detect_all_faces(image)
        else:
            self.fail("Failed to load test image")

        # 验证返回类型
        self.assertIsInstance(faces, list)
        if len(faces) > 0:
            for face in faces:
                self.assertIsInstance(face, FaceInfo)
                self.assertIsInstance(face.bbox, tuple)
                self.assertEqual(len(face.bbox), 4)

    def test_process_frame_without_source(self) -> None:
        """测试处理帧（无源人脸）"""
        try:
            # 初始化模块
            self.assertTrue(self.module.initialize(), "模块初始化失败")

            # 创建测试帧
            test_frame: np.ndarray = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

            # 处理帧（应该直接返回原帧，因为没有源人脸）
            result: np.ndarray = self.module.process_frame(test_frame)

            # 验证结果
            self.assertEqual(result.shape, test_frame.shape, "处理后帧尺寸应保持不变")
        except Exception as e:
            self.fail(f"无源人脸帧处理测试失败: {e}")

    def test_module_status(self):
        """测试模块状态获取"""
        # 初始化前状态
        status = self.module.get_status()
        self.assertFalse(status['initialized'])
        self.assertFalse(status['source_loaded'])

        # 初始化后状态
        self.module.initialize()
        status = self.module.get_status()
        self.assertTrue(status['initialized'])
        self.assertIn('model_type', status)
        self.assertIn('frame_count', status)

    def test_health_check(self) -> None:
        """测试健康检查"""
        try:
            # 未初始化状态
            health: dict = self.module.health_check()
            self.assertEqual(health['status'], 'error', "未初始化时状态应为error")

            # 初始化后状态
            self.assertTrue(self.module.initialize(), "模块初始化失败")
            health = self.module.health_check()
            self.assertEqual(health['status'], 'ok', "初始化后状态应为ok")
            self.assertIn('statistics', health, "健康检查应包含统计信息")
        except Exception as e:
            self.fail(f"健康检查测试失败: {e}")

    def test_module_reset(self):
        """测试模块重置"""
        self.module.initialize()
        self.module.frame_count = 10
        self.module.fps_processing = 30.0

        self.module.reset()

        self.assertIsNone(self.module.source_face)
        self.assertEqual(self.module.frame_count, 0)
        self.assertEqual(self.module.fps_processing, 0.0)


if __name__ == '__main__':
    unittest.main()
