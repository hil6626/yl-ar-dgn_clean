#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人脸检测处理器"""

import logging
from typing import Any, Dict, Optional

from backend.processor_manager import BaseProcessor
from backend.services.face_detection.face_detector import FaceDetector

logger = logging.getLogger(__name__)


class FaceDetectionProcessor(BaseProcessor):
    """人脸检测处理器"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.face_detector: Optional[FaceDetector] = None

    def _load_model(self):
        self.face_detector = FaceDetector(self.config)
        self.model_path = self.config.get('haar_cascade_path') or 'opencv_haar'

    def process(self, input_data: Any, **kwargs) -> Dict:
        """
        处理输入帧，输出检测结果
        input_data: np.ndarray 或 dict(frame=...)
        """
        if self.face_detector is None:
            raise RuntimeError("FaceDetector 未初始化")

        frame = input_data
        if isinstance(input_data, dict):
            frame = input_data.get('frame')

        if frame is None:
            raise ValueError("缺少 frame 参数")

        faces = self.face_detector.detect_faces(frame)
        return {
            'success': True,
            'faces': faces,
            'processor': 'face_detection'
        }
