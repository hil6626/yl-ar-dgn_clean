#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人脸识别模块
支持 LBPH / Eigen / Fisher (依赖 cv2.face)
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """人脸识别器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.recognizer_type = self.config.get('recognizer_type', 'lbph')
        self.threshold = float(self.config.get('threshold', 100.0))
        self.face_size = tuple(self.config.get('face_size', (100, 100)))

        self.known_faces: Dict[str, List] = {}
        self.known_labels: List[str] = []
        self.recognizer = None

        self._initialize_recognizer()

    def _initialize_recognizer(self) -> None:
        """初始化识别器"""
        try:
            import cv2
            if not hasattr(cv2, 'face'):
                raise RuntimeError("cv2.face 模块不可用，请安装 opencv-contrib-python")

            if self.recognizer_type == 'lbph':
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            elif self.recognizer_type == 'eigen':
                self.recognizer = cv2.face.EigenFaceRecognizer_create()
            elif self.recognizer_type == 'fisher':
                self.recognizer = cv2.face.FisherFaceRecognizer_create()
            else:
                raise ValueError(f"不支持的识别器类型: {self.recognizer_type}")

            logger.info(f"人脸识别器初始化成功: {self.recognizer_type}")
        except Exception as exc:
            logger.error(f"人脸识别器初始化失败: {exc}")
            self.recognizer = None

    def extract_features(self, face_image):
        """从人脸图像提取特征"""
        try:
            return self._preprocess_face(face_image)
        except Exception as exc:
            logger.error(f"特征提取失败: {exc}")
            return None

    def recognize_face(self, face_image) -> Dict:
        """识别人脸"""
        if self.recognizer is None:
            return {'label': 'unknown', 'confidence': 0.0, 'threshold': self.threshold}

        try:
            processed_face = self._preprocess_face(face_image)
            label_id, confidence = self.recognizer.predict(processed_face)

            label = 'unknown'
            if 0 <= label_id < len(self.known_labels):
                label = self.known_labels[label_id]

            return {
                'label': label,
                'confidence': float(confidence),
                'threshold': self.threshold
            }
        except Exception as exc:
            logger.error(f"人脸识别失败: {exc}")
            return {'label': 'unknown', 'confidence': 0.0, 'threshold': self.threshold}

    def add_known_face(self, face_image, label: str) -> None:
        """添加已知人脸"""
        features = self.extract_features(face_image)
        if features is None:
            return

        if label not in self.known_faces:
            self.known_faces[label] = []
            self.known_labels.append(label)
        self.known_faces[label].append(features)

    def train_recognizer(self) -> None:
        """训练识别器"""
        if self.recognizer is None:
            return

        faces = []
        labels = []
        for label_index, label in enumerate(self.known_labels):
            for face in self.known_faces.get(label, []):
                faces.append(face)
                labels.append(label_index)

        if faces:
            import numpy as np
            self.recognizer.train(faces, np.array(labels))
            logger.info("人脸识别器训练完成")

    def _preprocess_face(self, face_image):
        """预处理人脸图像"""
        import cv2
        if len(face_image.shape) > 2:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_image

        gray = cv2.equalizeHist(gray)
        resized = cv2.resize(gray, self.face_size)
        return resized
