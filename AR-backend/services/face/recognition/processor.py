#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人脸识别处理器"""

import logging
import os
from typing import Any, Dict, Optional

from backend.processor_manager import BaseProcessor
from backend.services.face_recognition.face_recognizer import FaceRecognizer

logger = logging.getLogger(__name__)


class FaceRecognitionProcessor(BaseProcessor):
    """人脸识别处理器"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.face_recognizer: Optional[FaceRecognizer] = None

    def _load_model(self):
        self.face_recognizer = FaceRecognizer(self.config)
        self._load_known_faces()
        self.face_recognizer.train_recognizer()
        self.model_path = self.config.get('known_faces_path', 'data/known_faces/')

    def process(self, input_data: Any, **kwargs) -> Dict:
        """
        识别人脸
        input_data: dict(frame=..., faces=[...]) 或 np.ndarray
        """
        if self.face_recognizer is None:
            raise RuntimeError("FaceRecognizer 未初始化")

        frame = input_data
        faces = kwargs.get('faces')

        if isinstance(input_data, dict):
            frame = input_data.get('frame')
            faces = input_data.get('faces', faces)

        if frame is None:
            raise ValueError("缺少 frame 参数")

        if not faces:
            return {'success': True, 'faces': [], 'processor': 'face_recognition'}

        results = []
        for face_data in faces:
            bbox = face_data.get('bbox')
            if not bbox or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            face_image = frame[y1:y2, x1:x2]
            recognition = self.face_recognizer.recognize_face(face_image)
            face_data = dict(face_data)
            face_data['recognition'] = recognition
            results.append(face_data)

        return {
            'success': True,
            'faces': results,
            'processor': 'face_recognition'
        }

    def _load_known_faces(self) -> None:
        """加载已知人脸数据"""
        if self.face_recognizer is None:
            return

        known_faces_path = self.config.get('known_faces_path', 'data/known_faces/')
        if not os.path.exists(known_faces_path):
            logger.warning(f"已知人脸目录不存在: {known_faces_path}")
            return

        try:
            import cv2
        except Exception as exc:
            logger.error(f"OpenCV 未安装，无法加载已知人脸: {exc}")
            return

        for filename in os.listdir(known_faces_path):
            if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp')):
                label = filename.split('_')[0]
                image_path = os.path.join(known_faces_path, filename)
                image = cv2.imread(image_path)
                if image is not None:
                    self.face_recognizer.add_known_face(image, label)
