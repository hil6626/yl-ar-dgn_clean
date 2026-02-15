#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep-Live-Cam 人脸合成模块封装
提供实时人脸合成功能接口

功能:
- 加载静态图片并提取人脸
- 将提取的人脸合成到实时摄像头画面
- 支持GPU加速
- 提供健康检查接口

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-09
"""

import cv2
import numpy as np
import os
import sys
import time
import logging
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class FaceInfo:
    """人脸信息数据类"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    landmarks: Optional[np.ndarray] = None
    confidence: float = 0.0
    face_id: int = 0


class FaceLiveCamModule:
    """
    Deep-Live-Cam 人脸合成模块封装类
    
    提供完整的实时人脸合成功能，支持:
    - 图片人脸提取
    - 实时视频流人脸合成
    - GPU加速支持
    - 多种合成参数调节
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 Deep-Live-Cam 模块
        
        Args:
            config: 配置参数
                - model_type: 模型类型 ('quick', 'standard', 'high')
                - gpu_id: GPU设备ID
                - frame_size: 处理帧大小
                - keep_fps: 是否保持帧率
        """
        self.config = {
            'model_type': 'quick',
            'gpu_id': 0,
            'frame_size': 640,
            'keep_fps': True,
            'face_scale': 1.0,
            'blend_alpha': 0.5,
        }
        if config:
            self.config.update(config)
        
        # 模块状态
        self.initialized = False
        self.is_processing = False
        
        # 人脸数据
        self.source_face: Optional[np.ndarray] = None
        self.source_face_landmarks: Optional[np.ndarray] = None
        self.source_face_info: Optional[FaceInfo] = None
        
        # 目标人脸列表
        self.target_faces: List[FaceInfo] = []
        
        # 处理统计
        self.frame_count = 0
        self.process_time_total = 0.0
        self.fps_processing = 0.0
        
        # 回调函数
        self.on_face_detected: Optional[Callable[[FaceInfo], None]] = None
        self.on_process_complete: Optional[Callable[[float], None]] = None
        
        # 模型路径
        self.models_dir = Path(__file__).parent / "Deep-Live-Cam" / "models"
        self.current_model = None
        
        # 检测器
        self.face_detector = None
        self.face_landmarker = None
        self.detector_type = "unknown"  # 检测器类型: dnn, haar, mediapipe
        
        # 性能优化
        self.frame_skip = 0  # 跳帧计数
        self.max_frame_size = 1280  # 最大帧尺寸
        self.detection_interval = 1  # 人脸检测间隔（帧）
        
    def initialize(self) -> bool:
        """
        初始化模块
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("正在初始化 Deep-Live-Cam 模块...")
            
            # 初始化人脸检测器
            self._init_face_detector()
            
            # 检查模型文件
            self._check_models()
            
            self.initialized = True
            logger.info("Deep-Live-Cam 模块初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Deep-Live-Cam 模块初始化失败: {e}")
            self.initialized = False
            return False
    
    def _init_face_detector(self) -> None:
        """
        初始化人脸检测器
        优化版本：支持多种检测器，自动选择最优方案
        """
        try:
            # 首先尝试加载 DNN 检测器（Caffe模型）
            prototxt = Path(__file__).parent / "Deep-Live-Cam" / "models" / "deploy.prototxt"
            caffemodel = Path(__file__).parent / "Deep-Live-Cam" / "models" / "res10_300x300_ssd_iter_140000.caffemodel"
            
            if prototxt.exists() and caffemodel.exists():
                try:
                    self.face_detector = cv2.dnn.readNetFromCaffe(
                        str(prototxt),
                        str(caffemodel)
                    )
                    
                    # 尝试使用 GPU 加速
                    try:
                        self.face_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                        self.face_detector.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                        logger.info("已启用 CUDA GPU 加速")
                    except Exception:
                        # 回退到 CPU
                        self.face_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                        self.face_detector.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                        logger.info("使用 CPU 进行人脸检测")
                    
                    self.detector_type = "dnn"
                    logger.info("已加载 Caffe DNN 人脸检测模型")
                except Exception as e:
                    logger.warning(f"DNN模型加载失败: {e}, 回退到 Haar Cascade")
                    self._use_haar_cascade()
            else:
                # 使用 Haar Cascade
                self._use_haar_cascade()
            
            # 初始化关键点检测器
            self._init_landmarker()
            
        except Exception as e:
            logger.warning(f"人脸检测器初始化警告: {e}")
            self._use_haar_cascade()
    
    def _use_haar_cascade(self) -> None:
        """使用 Haar Cascade 作为备选检测器"""
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.detector_type = "haar"
        logger.info("已加载 Haar Cascade 人脸检测器")
    
    def _init_landmarker(self) -> None:
        """
        初始化人脸关键点检测器
        """
        try:
            # 尝试加载 Dlib 关键点检测器
            predictor_path = Path(__file__).parent / "Deep-Live-Cam" / "models" / "shape_predictor_68_face_landmarks.dat"
            if predictor_path.exists():
                try:
                    import dlib
                    self.face_landmarker = dlib.shape_predictor(str(predictor_path))
                    logger.info("已加载人脸关键点检测器")
                except ImportError:
                    logger.warning("Dlib 未安装，关键点检测功能不可用")
        except Exception as e:
            logger.warning(f"关键点检测器加载失败: {e}")
    
    def _check_models(self) -> None:
        """
        检查模型文件
        """
        model_types = ['quick', 'standard', 'high']
        for model_type in model_types:
            model_path = self.models_dir / model_type
            if model_path.exists():
                logger.info(f"模型类型 {model_type} 可用")
            else:
                logger.warning(f"模型类型 {model_type} 不存在: {model_path}")
    
    def set_source(self, image_path: str) -> bool:
        """
        设置源人脸图像
        
        Args:
            image_path: 源图像路径
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"源图像不存在: {image_path}")
                return False
            
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"无法读取图像: {image_path}")
                return False
            
            # 检测并提取人脸
            face_info = self._extract_face(image)
            if face_info is None:
                logger.error(f"图像中未检测到人脸: {image_path}")
                return False
            
            self.source_face = image
            self.source_face_info = face_info
            self.source_face_landmarks = face_info.landmarks
            
            logger.info(f"已设置源人脸: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"设置源人脸失败: {e}")
            return False
    
    def _extract_face(self, image: np.ndarray) -> Optional[FaceInfo]:
        """
        从图像中提取人脸
        
        Args:
            image: 输入图像
            
        Returns:
            FaceInfo: 人脸信息，提取失败返回 None
        """
        try:
            # 转换为灰度图进行检测
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用级联分类器检测人脸
            if isinstance(self.face_detector, cv2.CascadeClassifier):
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                if len(faces) == 0:
                    return None
                
                # 取最大的人脸
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                bbox = (x, y, x + w, y + h)
                
                # 检测关键点
                landmarks = self._detect_landmarks(image, (x, y, w, h))
                
                return FaceInfo(
                    bbox=bbox,
                    landmarks=landmarks,
                    confidence=1.0,
                    face_id=0
                )
            
            # 使用 DNN 检测器
            elif isinstance(self.face_detector, cv2.dnn.Net):
                (h, w) = image.shape[:2]
                resized = cv2.resize(image, (300, 300))
                if resized is not None:
                    blob = cv2.dnn.blobFromImage(
                        resized,
                        1.0,
                        (300, 300),
                        (104.0, 177.0, 123.0)
                    )
                    
                    self.face_detector.setInput(blob)
                    detections = self.face_detector.forward()
                    
                    # 找到置信度最高的人脸
                    for i in range(0, detections.shape[2]):
                        confidence = detections[0, 0, i, 2]
                        
                        if confidence > 0.5:
                            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                            (startX, startY, endX, endY) = box.astype("int")
                            bbox = (startX, startY, endX, endY)
                            
                            # 检测关键点
                            landmarks = self._detect_landmarks(image, (startX, startY, endX - startX, endY - startY))
                            
                            return FaceInfo(
                                bbox=bbox,
                                landmarks=landmarks,
                                confidence=confidence,
                                face_id=0
                            )
                
                return None
                
        except Exception as e:
            logger.error(f"人脸提取失败: {e}")
            return None
    
    def _detect_landmarks(self, image: np.ndarray, face_rect: Tuple) -> Optional[np.ndarray]:
        """
        检测人脸关键点
        
        Args:
            image: 输入图像
            face_rect: 人脸区域 (x, y, w, h)
            
        Returns:
            np.ndarray: 关键点坐标数组
        """
        try:
            if self.face_landmarker is not None:
                try:
                    import dlib
                    x, y, w, h = face_rect
                    rect = dlib.rectangle(x, y, x + w, y + h)
                    shape = self.face_landmarker(image, rect)
                    
                    landmarks = np.array([[p.x, p.y] for p in shape.parts()])
                    return landmarks
                except ImportError:
                    pass
                except Exception:
                    pass
            
            # 使用简单方法估算关键点
            x, y, w, h = face_rect
            landmarks = np.array([
                [x + w // 2, y + h // 3],       # 鼻子
                [x + w // 3, y + h // 2],       # 左眼
                [x + 2 * w // 3, y + h // 2],   # 右眼
                [x + w // 4, y + 2 * h // 3],   # 左嘴角
                [x + 3 * w // 4, y + 2 * h // 3] # 右嘴角
            ])
            return landmarks
                
        except Exception as e:
            logger.warning(f"关键点检测失败: {e}")
            return None
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理视频帧，将源人脸合成到目标帧
        优化版本：添加性能优化，支持帧跳过和尺寸调整
        
        Args:
            frame: 输入视频帧
            
        Returns:
            np.ndarray: 合成后的视频帧
        """
        if not self.initialized:
            logger.warning("模块未初始化")
            return frame
        
        if self.source_face is None:
            logger.warning("未设置源人脸")
            return frame
        
        start_time = time.time()
        
        try:
            # 性能优化：调整大帧尺寸
            original_size = frame.shape[:2]
            frame_for_process = frame
            scale_factor = 1.0
            
            if max(original_size) > self.max_frame_size:
                scale = self.max_frame_size / max(original_size)
                new_size = (int(original_size[1] * scale), int(original_size[0] * scale))
                frame_for_process = cv2.resize(frame, new_size)
                scale_factor = scale
            
            # 性能优化：跳帧检测（每隔detection_interval帧检测一次）
            self.frame_skip += 1
            should_detect = (self.frame_skip % self.detection_interval == 0)
            
            if should_detect or len(self.target_faces) == 0:
                # 检测目标帧中的人脸
                self.target_faces = self._detect_all_faces(frame_for_process)
            
            if len(self.target_faces) == 0:
                # 无人脸，直接返回
                return frame
            
            # 对每个检测到的人脸进行替换
            for face_info in self.target_faces:
                # 调整人脸坐标到原始帧尺寸
                if scale_factor != 1.0:
                    adjusted_bbox = tuple(int(coord / scale_factor) for coord in face_info.bbox)
                    adjusted_face = FaceInfo(
                        bbox=adjusted_bbox,
                        landmarks=face_info.landmarks,
                        confidence=face_info.confidence,
                        face_id=face_info.face_id
                    )
                    result = self._replace_face(result, adjusted_face)
                else:
                    result = self._replace_face(result, face_info)
            
            # 更新统计信息
            process_time = time.time() - start_time
            self.frame_count += 1
            self.process_time_total += process_time
            
            if self.frame_count % 30 == 0:
                self.fps_processing = self.frame_count / self.process_time_total
                logger.debug(f"处理帧率: {self.fps_processing:.2f} fps")
            
            return result
            
        except Exception as e:
            logger.error(f"帧处理失败: {e}")
            return frame
    
    def _detect_all_faces(self, image: np.ndarray) -> List[FaceInfo]:
        """
        检测图像中所有的人脸
        
        Args:
            image: 输入图像
            
        Returns:
            List[FaceInfo]: 检测到的人脸列表
        """
        try:
            # 检查检测器是否可用
            if self.face_detector is None:
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用级联分类器
            if isinstance(self.face_detector, cv2.CascadeClassifier):
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
            else:
                # 其他检测器类型
                return []
            
            face_list = []
            for i, (x, y, w, h) in enumerate(faces):
                bbox = (x, y, x + w, y + h)
                landmarks = self._detect_landmarks(image, (x, y, w, h))
                
                face_info = FaceInfo(
                    bbox=bbox,
                    landmarks=landmarks,
                    confidence=1.0,
                    face_id=i
                )
                face_list.append(face_info)
                
                # 回调通知
                if self.on_face_detected:
                    self.on_face_detected(face_info)
            
            return face_list
            
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
            return []
    
    def _replace_face(self, frame: np.ndarray, target_info: FaceInfo) -> np.ndarray:
        """
        替换单个人脸
        
        Args:
            frame: 输入帧
            target_info: 目标人脸信息
            
        Returns:
            np.ndarray: 处理后的帧
        """
        try:
            x1, y1, x2, y2 = target_info.bbox
            target_w = x2 - x1
            target_h = y2 - y1
            
            if target_w <= 0 or target_h <= 0:
                return frame
            
            # 调整源人脸大小以匹配目标人脸
            source_resized = cv2.resize(
                self.source_face,
                (target_w, target_h),
                interpolation=cv2.INTER_LINEAR
            )
            
            # 创建人脸区域掩码
            mask = np.ones_like(source_resized) * 255
            if self.source_face_landmarks is not None and target_info.landmarks is not None:
                # 使用关键点创建更精确的掩码
                mask = self._create_face_mask(
                    source_resized.shape[:2],
                    target_info.landmarks
                )
            
            # 泊松融合实现自然过渡
            blended = self._seamless_clone(
                source_resized,
                frame[y1:y2, x1:x2],
                mask
            )
            
            # 混合原始帧和融合结果
            blend_alpha = self.config.get('blend_alpha', 0.5)
            frame[y1:y2, x1:x2] = cv2.addWeighted(
                frame[y1:y2, x1:x2],
                1 - blend_alpha,
                blended,
                blend_alpha,
                0
            )
            
            return frame
            
        except Exception as e:
            logger.error(f"人脸替换失败: {e}")
            return frame
    
    def _create_face_mask(self, shape: Tuple, landmarks: np.ndarray) -> np.ndarray:
        """
        基于关键点创建人脸掩码
        
        Args:
            shape: 图像形状
            landmarks: 关键点坐标
            
        Returns:
            np.ndarray: 掩码图像
        """
        try:
            mask = np.zeros(shape[:2], dtype=np.uint8)
            
            if landmarks is None or len(landmarks) < 5:
                # 使用简单的椭圆掩码
                center = (shape[1] // 2, shape[0] // 2)
                axes = (shape[1] // 2, shape[0] // 2)
                cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
            else:
                # 使用关键点创建凸包掩码
                hull = cv2.convexHull(landmarks.astype(np.int32))
                cv2.fillConvexPoly(mask, hull, 255)
            
            # 模糊掩码边缘
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
            
            return mask
            
        except Exception as e:
            logger.warning(f"掩码创建失败: {e}")
            return np.ones(shape[:2], dtype=np.uint8) * 255
    
    def _seamless_clone(self, src: np.ndarray, dst: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        使用泊松融合进行无缝克隆
        
        Args:
            src: 源图像
            dst: 目标区域
            mask: 掩码
            
        Returns:
            np.ndarray: 融合后的图像
        """
        try:
            # 确保尺寸一致
            src_h, src_w = src.shape[:2]
            dst_h, dst_w = dst.shape[:2]
            
            if src_h != dst_h or src_w != dst_w:
                resized_src = cv2.resize(src, (dst_w, dst_h))
                resized_mask = cv2.resize(mask, (dst_w, dst_h))
                if resized_src is None or resized_mask is None:
                    return src
            else:
                resized_src = src
                resized_mask = mask
            
            # 归一化掩码
            resized_mask = resized_mask.astype(np.float32) / 255.0
            
            # 简单加权融合
            result = resized_src * resized_mask + dst * (1 - resized_mask)
            return result.astype(np.uint8)
            
        except Exception as e:
            logger.warning(f"无缝克隆失败: {e}")
            return src
    
    def get_source_face_info(self) -> Optional[Dict]:
        """
        获取源人脸信息
        
        Returns:
            Dict: 人脸信息字典
        """
        if self.source_face_info is None:
            return None
        
        return {
            'bbox': self.source_face_info.bbox,
            'confidence': self.source_face_info.confidence,
            'has_landmarks': self.source_face_info.landmarks is not None
        }
    
    def get_status(self) -> Dict:
        """
        获取模块状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            'initialized': self.initialized,
            'is_processing': self.is_processing,
            'source_loaded': self.source_face is not None,
            'model_type': self.config.get('model_type'),
            'frame_count': self.frame_count,
            'fps_processing': self.fps_processing,
            'faces_detected': len(self.target_faces)
        }
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        return {
            'name': 'Deep-Live-Cam',
            'status': 'ok' if self.initialized else 'error',
            'message': '模块正常运行' if self.initialized else '模块未初始化',
            'statistics': self.get_status()
        }
    
    def reset(self) -> None:
        """
        重置模块状态
        """
        self.source_face = None
        self.source_face_landmarks = None
        self.source_face_info = None
        self.target_faces = []
        self.frame_count = 0
        self.process_time_total = 0
        self.fps_processing = 0
        logger.info("Deep-Live-Cam 模块已重置")
    
    def cleanup(self) -> None:
        """
        清理资源
        """
        self.reset()
        self.initialized = False
        logger.info("Deep-Live-Cam 模块资源已清理")
    
    def set_frame_callback(self, callback: Callable[[FaceInfo], None]) -> None:
        """
        设置人脸检测回调
        
        Args:
            callback: 回调函数
        """
        self.on_face_detected = callback
    
    def set_process_callback(self, callback: Callable[[float], None]) -> None:
        """
        设置处理完成回调
        
        Args:
            callback: 回调函数
        """
        self.on_process_complete = callback


# 便捷函数
def create_face_live_cam(config: Optional[Dict] = None) -> FaceLiveCamModule:
    """
    创建 Deep-Live-Cam 模块实例
    
    Args:
        config: 配置参数
        
    Returns:
        FaceLiveCamModule: 模块实例
    """
    module = FaceLiveCamModule(config)
    return module


def main():
    """主函数 - 测试模块"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deep-Live-Cam 模块测试')
    parser.add_argument('--image', type=str, help='测试图片路径')
    parser.add_argument('--camera', action='store_true', help='测试摄像头')
    args = parser.parse_args()
    
    # 创建模块
    module = FaceLiveCamModule()
    if not module.initialize():
        print("模块初始化失败")
        return
    
    print("模块初始化成功")
    print(f"状态: {module.health_check()}")
    
    if args.image:
        # 测试图片处理
        module.set_source(args.image)
        image = cv2.imread(args.image)
        if image is not None:
            result = module.process_frame(image)
            cv2.imwrite('result.jpg', result)
            print("处理完成，结果已保存到 result.jpg")
    
    if args.camera:
        # 测试摄像头
        import time
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 处理帧
            result = module.process_frame(frame)
            
            # 显示结果
            cv2.imshow('Deep-Live-Cam', result)
            
            # 按 'q' 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    # 清理
    module.cleanup()


if __name__ == '__main__':
    main()

