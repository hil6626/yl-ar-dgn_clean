#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人脸检测模块
支持 Haar 级联和 DNN 模型
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class FaceDetector:
    """人脸检测器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.detector_type = self.config.get('detector_type', 'opencv_haar')
        self.scale_factor = self.config.get('scale_factor', 1.1)
        self.min_neighbors = self.config.get('min_neighbors', 5)
        self.min_size = tuple(self.config.get('min_size', (30, 30)))
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.max_faces = self.config.get('max_faces', 0)

        self.face_cascade = None
        self.dnn_net = None
        self._initialize_detector()

    def _initialize_detector(self) -> None:
        """初始化检测器"""
        if self.detector_type == 'opencv_haar':
            self.face_cascade = self._load_haar_cascade()
            if self.face_cascade is None:
                raise RuntimeError("Haar 级联加载失败")
        elif self.detector_type == 'dnn':
            self.dnn_net = self._load_dnn_model()
            if self.dnn_net is None:
                raise RuntimeError("DNN 模型加载失败")
        else:
            raise ValueError(f"不支持的检测器类型: {self.detector_type}")

    def _load_haar_cascade(self):
        """加载 Haar 级联"""
        try:
            import cv2
            cascade_path = self.config.get('haar_cascade_path')
            if not cascade_path:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            cascade = cv2.CascadeClassifier(cascade_path)
            if cascade.empty():
                logger.error(f"Haar 级联无效: {cascade_path}")
                return None
            logger.info(f"Haar 级联加载成功: {cascade_path}")
            return cascade
        except Exception as exc:
            logger.error(f"加载 Haar 级联失败: {exc}")
            return None

    def _load_dnn_model(self):
        """加载 DNN 模型"""
        try:
            import cv2
            prototxt_path = self.config.get('prototxt_path')
            caffemodel_path = self.config.get('caffemodel_path')
            if not prototxt_path or not caffemodel_path:
                logger.error("DNN 模型路径未配置")
                return None
            net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)
            logger.info("DNN 模型加载成功")
            return net
        except Exception as exc:
            logger.error(f"加载 DNN 模型失败: {exc}")
            return None

    def detect_faces(self, frame) -> List[Dict]:
        """检测图像中的人脸"""
        try:
            if self.detector_type == 'opencv_haar':
                return self._detect_haar(frame)
            if self.detector_type == 'dnn':
                return self._detect_dnn(frame)
            return []
        except Exception as exc:
            logger.error(f"人脸检测失败: {exc}")
            return []

    def _detect_haar(self, frame) -> List[Dict]:
        """使用 Haar 级联检测"""
        import cv2

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size
        )

        results = [self._convert_bbox(face, 1.0) for face in faces]
        return self._limit_faces(results)

    def _detect_dnn(self, frame) -> List[Dict]:
        """使用 DNN 模型检测"""
        import cv2
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.dnn_net.setInput(blob)
        detections = self.dnn_net.forward()

        results: List[Dict] = []
        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < self.confidence_threshold:
                continue
            box = detections[0, 0, i, 3:7] * [w, h, w, h]
            (x1, y1, x2, y2) = box.astype("int").tolist()
            results.append(self._convert_bbox((x1, y1, x2 - x1, y2 - y1), confidence))

        return self._limit_faces(results)

    def _convert_bbox(self, bbox: Tuple[int, int, int, int], confidence: float) -> Dict:
        x, y, w, h = bbox
        return {
            'bbox': [int(x), int(y), int(x + w), int(y + h)],
            'confidence': float(confidence),
            'landmarks': []
        }

    def _limit_faces(self, faces: List[Dict]) -> List[Dict]:
        if self.max_faces and len(faces) > self.max_faces:
            return faces[: self.max_faces]
        return faces
