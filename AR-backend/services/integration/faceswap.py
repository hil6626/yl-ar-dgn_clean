#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faceswap 人脸交换模块封装
支持静态和动态人脸替换

功能:
- 人脸检测和特征提取
- 人脸交换和融合
- 实时视频流处理
- 参数调节支持

作者: AI 全栈技术员
版本: 1.0
创建日期: 2026-02-09
"""

import os
import sys
import time
import logging
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path
import numpy as np

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class FaceSwapModule:
    """
    Faceswap 人脸交换模块封装类
    
    提供完整的人脸交换功能，支持:
    - 静态图片人脸交换
    - 实时视频流人脸交换
    - 多种参数调节
    - 效果预览
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 Faceswap 模块
        
        Args:
            config: 配置参数
                - align_eyes: 是否对齐眼睛
                - smooth_edges: 是否平滑边缘
                - color_adjust: 颜色调整方式
                - face_size: 人脸大小
        """
        self.config = {
            'align_eyes': True,
            'smooth_edges': True,
            'color_adjust': 'histogram',  # 'histogram', 'matching', 'none'
            'face_size': 256,
            'blend_alpha': 0.5,
            'enhance_quality': True,
        }
        if config:
            self.config.update(config)
        
        # 模块状态
        self.initialized = False
        self.is_processing = False
        
        # 人脸数据
        self.source_face: Optional[np.ndarray] = None
        self.source_landmarks: Optional[np.ndarray] = None
        self.source_face_info: Optional[Dict] = None
        
        # 检测器
        self.face_detector = None
        self.landmark_detector = None
        
        # 统计
        self.frame_count = 0
        self.process_time_total = 0.0
        self.fps_actual = 0.0
        
        # 回调函数
        self.on_face_detected: Optional[Callable[[Dict], None]] = None
        self.on_process_complete: Optional[Callable[[float], None]] = None
        
        # 性能优化参数
        self.gpu_enabled = False
        self.max_frame_size = 1280
        self.detector_type = "haar"
        self.frame_skip = 0
        self.detection_interval = 1
        self.last_faces: List[Dict] = []
        
    def initialize(self) -> bool:
        """
        初始化模块
        优化版本：添加GPU支持和性能优化
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("正在初始化 Faceswap 模块...")
            
            # 初始化人脸检测器（带GPU支持）
            self._init_detectors()
            
            self.initialized = True
            logger.info("Faceswap 模块初始化成功")
            logger.info(f"  - GPU加速: {'启用' if self.gpu_enabled else '禁用'}")
            logger.info(f"  - 人脸检测器: {self.detector_type}")
            return True
            
        except Exception as e:
            logger.error(f"Faceswap 模块初始化失败: {e}")
            self.initialized = False
            return False
    
    def _init_detectors(self) -> None:
        """初始化检测器（带GPU支持）"""
        if not OPENCV_AVAILABLE or cv2 is None:
            logger.warning("OpenCV 未安装")
            return
            
        try:
            # 尝试加载 DNN 检测器
            models_dir = Path(__file__).parent / "faceswap" / "models"
            prototxt = models_dir / "deploy.prototxt"
            caffemodel = models_dir / "res10_300x300_ssd_iter_140000.caffemodel"
            
            if prototxt.exists() and caffemodel.exists():
                try:
                    self.face_detector = cv2.dnn.readNetFromCaffe(
                        str(prototxt),
                        str(caffemodel)
                    )
                    
                    # 尝试启用 GPU
                    try:
                        self.face_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                        self.face_detector.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                        self.gpu_enabled = True
                        logger.info("已启用 CUDA GPU 加速")
                    except Exception:
                        self.face_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                        self.face_detector.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                        self.gpu_enabled = False
                        logger.info("使用 CPU 进行人脸检测")
                    
                    self.detector_type = "dnn"
                    logger.info("已加载 DNN 人脸检测器")
                except Exception as e:
                    logger.warning(f"DNN模型加载失败: {e}，回退到 Haar Cascade")
                    self._use_haar_cascade()
            else:
                self._use_haar_cascade()
                
        except Exception as e:
            logger.warning(f"人脸检测器初始化失败: {e}")
            self._use_haar_cascade()
    
    def _use_haar_cascade(self) -> None:
        """使用 Haar Cascade 作为备选检测器"""
        if OPENCV_AVAILABLE and cv2 is not None:
            self.face_detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            self.detector_type = "haar"
            logger.info("已加载 Haar Cascade 人脸检测器")
    
    def set_source(self, image_path: str) -> bool:
        """
        设置源人脸
        
        Args:
            image_path: 源图像路径
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"源图像不存在: {image_path}")
                return False
            
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"无法读取图像: {image_path}")
                return False
            
            # 检测人脸
            faces = self._detect_faces(image)
            if len(faces) == 0:
                logger.error(f"图像中未检测到人脸: {image_path}")
                return False
            
            # 选择最大的人脸
            face_info = max(faces, key=lambda f: f['bbox'][2] * f['bbox'][3])
            
            # 提取人脸区域
            x1, y1, x2, y2 = face_info['bbox']
            self.source_face = image[y1:y2, x1:x2].copy()
            self.source_landmarks = face_info.get('landmarks')
            self.source_face_info = face_info
            
            # 调整大小
            self.source_face = cv2.resize(
                self.source_face,
                (self.config['face_size'], self.config['face_size'])
            )
            
            logger.info(f"已设置源人脸: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"设置源人脸失败: {e}")
            return False
    
    def _detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        检测图像中的人脸
        
        Args:
            image: 输入图像
            
        Returns:
            List[Dict]: 人脸信息列表
        """
        faces = []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用级联分类器检测
            detections = self.face_detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            for i, (x, y, w, h) in enumerate(detections):
                bbox = (x, y, x + w, y + h)
                
                # 检测关键点
                landmarks = self._detect_landmarks(image, (x, y, w, h))
                
                face_info = {
                    'bbox': bbox,
                    'landmarks': landmarks,
                    'confidence': 1.0,
                    'face_id': i,
                    'size': w * h
                }
                
                faces.append(face_info)
                
                # 回调
                if self.on_face_detected:
                    self.on_face_detected(face_info)
            
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
        
        return faces
    
    def _detect_landmarks(self, image: np.ndarray, 
                         face_rect: Tuple) -> Optional[np.ndarray]:
        """
        检测人脸关键点
        
        Args:
            image: 输入图像
            face_rect: 人脸区域 (x, y, w, h)
            
        Returns:
            np.ndarray: 关键点数组
        """
        try:
            x, y, w, h = face_rect
            
            # 简单关键点估算
            landmarks = {
                'nose': (x + w // 2, y + h // 2),
                'left_eye': (x + w // 3, y + h // 3),
                'right_eye': (x + 2 * w // 3, y + h // 3),
                'mouth': (x + w // 2, y + 2 * h // 3),
                'left_mouth': (x + w // 4, y + 2 * h // 3),
                'right_mouth': (x + 3 * w // 4, y + 2 * h // 3),
            }
            
            # 返回归一化坐标
            norm_landmarks = np.array([
                landmarks['left_eye'],
                landmarks['right_eye'],
                landmarks['nose'],
                landmarks['mouth'],
                landmarks['left_mouth'],
                landmarks['right_mouth'],
            ], dtype=np.float32)
            
            return norm_landmarks
            
        except Exception:
            return None
    
    def swap_faces(self, source_image: np.ndarray, 
                  target_image: np.ndarray) -> np.ndarray:
        """
        交换人脸
        
        Args:
            source_image: 源图像
            target_image: 目标图像
            
        Returns:
            np.ndarray: 交换后的图像
        """
        if not self.initialized:
            return target_image
        
        try:
            # 检测源图像中的人脸
            source_faces = self._detect_faces(source_image)
            if len(source_faces) == 0:
                logger.warning("源图像中未检测到人脸")
                return target_image
            
            # 检测目标图像中的人脸
            target_faces = self._detect_faces(target_image)
            if len(target_faces) == 0:
                logger.warning("目标图像中未检测到人脸")
                return target_image
            
            # 选择最大的人脸
            source_info = max(source_faces, key=lambda f: f['size'])
            target_info = max(target_faces, key=lambda f: f['size'])
            
            # 执行人脸交换
            return self._perform_swap(source_image, source_info, 
                                    target_image, target_info)
            
        except Exception as e:
            logger.error(f"人脸交换失败: {e}")
            return target_image
    
    def _perform_swap(self, source: np.ndarray, source_info: Dict,
                     target: np.ndarray, target_info: Dict) -> np.ndarray:
        """
        执行人脸交换
        
        Args:
            source: 源图像
            source_info: 源人脸信息
            target: 目标图像
            target_info: 目标人脸信息
            
        Returns:
            np.ndarray: 交换后的图像
        """
        try:
            result = target.copy()
            
            # 提取源人脸
            sx1, sy1, sx2, sy2 = source_info['bbox']
            tx1, ty1, tx2, ty2 = target_info['bbox']
            
            source_face_region = source[sy1:sy2, sx1:sx2]
            target_face_region = target[ty1:ty2, tx1:tx2]
            
            # 调整源人脸大小以匹配目标
            face_w = tx2 - tx1
            face_h = ty2 - ty1
            
            if face_w <= 0 or face_h <= 0:
                return target
            
            resized_source = cv2.resize(
                source_face_region,
                (face_w, face_h),
                interpolation=cv2.INTER_LINEAR
            )
            
            # 颜色匹配
            if self.config['color_adjust'] != 'none':
                resized_source = self._match_colors(resized_source, target_face_region)
            
            # 创建掩码
            mask = self._create_face_mask(
                (face_h, face_w),
                target_info.get('landmarks')
            )
            
            # 泊松融合
            try:
                center = (tx1 + face_w // 2, ty1 + face_h // 2)
                blended = cv2.seamlessClone(
                    resized_source,
                    result[ty1:ty2, tx1:tx2],
                    mask,
                    center,
                    cv2.NORMAL_CLONE
                )
                result[ty1:ty2, tx1:tx2] = blended
            except Exception:
                # 融合失败则直接替换
                result[ty1:ty2, tx1:tx2] = resized_source
            
            return result
            
        except Exception as e:
            logger.error(f"执行人脸交换失败: {e}")
            return target
    
    def _match_colors(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        """
        颜色匹配
        
        Args:
            source: 源图像
            target: 目标图像
            
        Returns:
            np.ndarray: 颜色匹配后的源图像
        """
        try:
            if self.config['color_adjust'] == 'histogram':
                # 直方图匹配
                result = source.copy()
                for i in range(3):
                    source_hist = cv2.calcHist([source], [i], None, [256], [0, 256])
                    target_hist = cv2.calcHist([target], [i], None, [256], [0, 256])
                    
                    source_hist_norm = source_hist / source_hist.sum()
                    target_hist_norm = target_hist / target_hist.sum()
                    
                    lookup = np.zeros(256, dtype=np.uint8)
                    source_cdf = source_hist_norm.cumsum()
                    target_cdf = target_hist_norm.cumsum()
                    
                    for j in range(256):
                        lookup[j] = np.searchsorted(
                            target_cdf, 
                            source_cdf[j],
                            side='left'
                        )
                        lookup[j] = min(255, lookup[j])
                    
                    result[:, :, i] = cv2.LUT(result[:, :, i], lookup)
                
                return result
                
            else:
                # 简单均值匹配
                source_mean = cv2.mean(source)[:3]
                target_mean = cv2.mean(target)[:3]
                diff = [t - s for t, s in zip(target_mean, source_mean)]
                
                result = source.copy().astype(np.float32)
                for i in range(3):
                    result[:, :, i] = np.clip(result[:, :, i] + diff[i], 0, 255)
                
                return result.astype(np.uint8)
                
        except Exception:
            return source
    
    def _create_face_mask(self, size: Tuple[int, int], 
                         landmarks: Optional[np.ndarray]) -> np.ndarray:
        """
        创建人脸掩码
        
        Args:
            size: 掩码大小 (h, w)
            landmarks: 关键点
            
        Returns:
            np.ndarray: 掩码图像
        """
        h, w = size
        mask = np.zeros((h, w), dtype=np.uint8)
        
        if landmarks is not None and len(landmarks) >= 6:
            # 使用关键点创建凸包
            try:
                hull = cv2.convexHull(landmarks.astype(np.int32))
                cv2.fillConvexPoly(mask, hull, 255)
            except Exception:
                # 回退到椭圆掩码
                center = (w // 2, h // 2)
                axes = (w // 2, h // 2)
                cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        else:
            # 默认椭圆掩码
            center = (w // 2, h // 2)
            axes = (w // 2, h // 2)
            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        # 平滑边缘
        if self.config['smooth_edges']:
            mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        return mask
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理视频帧
        
        Args:
            frame: 输入帧
            
        Returns:
            np.ndarray: 处理后的帧
        """
        if not self.initialized or self.source_face is None:
            return frame
        
        start_time = time.time()
        
        try:
            # 检测人脸
            faces = self._detect_faces(frame)
            
            if len(faces) == 0:
                return frame
            
            result = frame.copy()
            
            # 对每个人脸进行处理
            for face_info in faces:
                x1, y1, x2, y2 = face_info['bbox']
                face_w = x2 - x1
                face_h = y2 - y1
                
                if face_w <= 0 or face_h <= 0:
                    continue
                
                # 调整源人脸
                resized_source = cv2.resize(
                    self.source_face,
                    (face_w, face_h),
                    interpolation=cv2.INTER_LINEAR
                )
                
                # 颜色匹配
                target_region = frame[y1:y2, x1:x2]
                if self.config['color_adjust'] != 'none':
                    resized_source = self._match_colors(resized_source, target_region)
                
                # 创建掩码
                mask = self._create_face_mask(
                    (face_h, face_w),
                    face_info.get('landmarks')
                )
                
                # 融合
                try:
                    center = (x1 + face_w // 2, y1 + face_h // 2)
                    result[y1:y2, x1:x2] = cv2.seamlessClone(
                        resized_source,
                        result[y1:y2, x1:x2],
                        mask,
                        center,
                        cv2.NORMAL_CLONE
                    )
                except Exception:
                    result[y1:y2, x1:x2] = resized_source
            
            # 更新统计
            process_time = time.time() - start_time
            self.frame_count += 1
            self.process_time_total += process_time
            
            return result
            
        except Exception as e:
            logger.error(f"帧处理失败: {e}")
            return frame
    
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
            'frame_count': self.frame_count,
            'avg_process_time': (
                self.process_time_total / self.frame_count 
                if self.frame_count > 0 else 0
            ),
            'config': {
                'align_eyes': self.config['align_eyes'],
                'smooth_edges': self.config['smooth_edges'],
                'color_adjust': self.config['color_adjust']
            }
        }
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        return {
            'name': 'FaceSwap',
            'status': 'ok' if self.initialized else 'error',
            'message': '模块正常运行' if self.initialized else '模块未初始化',
            'statistics': self.get_status()
        }
    
    def set_parameter(self, key: str, value) -> None:
        """
        设置参数
        
        Args:
            key: 参数名
            value: 参数值
        """
        if key in self.config:
            self.config[key] = value
            logger.info(f"参数已设置: {key} = {value}")
    
    def get_parameters(self) -> Dict:
        """获取当前参数"""
        return self.config.copy()
    
    def reset(self) -> None:
        """重置模块状态"""
        self.source_face = None
        self.source_landmarks = None
        self.source_face_info = None
        self.frame_count = 0
        self.process_time_total = 0
        logger.info("Faceswap 模块已重置")
    
    def cleanup(self) -> None:
        """清理资源"""
        self.reset()
        self.initialized = False
        logger.info("Faceswap 模块资源已清理")
    
    def set_face_callback(self, callback: Callable[[Dict], None]) -> None:
        """设置人脸检测回调"""
        self.on_face_detected = callback
    
    def set_process_callback(self, callback: Callable[[float], None]) -> None:
        """设置处理完成回调"""
        self.on_process_complete = callback


# 便捷函数
def create_face_swap(config: Optional[Dict] = None) -> FaceSwapModule:
    """
    创建 Faceswap 模块实例
    
    Args:
        config: 配置参数
        
    Returns:
        FaceSwapModule: 模块实例
    """
    return FaceSwapModule(config)


def main():
    """主函数 - 测试模块"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Faceswap 模块测试')
    parser.add_argument('--source', type=str, help='源人脸图片')
    parser.add_argument('--target', type=str, help='目标图片')
    parser.add_argument('--camera', action='store_true', help='测试摄像头')
    args = parser.parse_args()
    
    # 创建模块
    module = FaceSwapModule()
    
    if not module.initialize():
        print("模块初始化失败")
        return
    
    print("模块初始化成功")
    
    if args.source and args.target:
        if module.set_source(args.source):
            print(f"已加载源人脸: {args.source}")
            
            target = cv2.imread(args.target)
            if target is not None:
                result = module.swap_faces(
                    cv2.imread(args.source),
                    target
                )
                cv2.imwrite('result_swap.jpg', result)
                print("人脸交换完成，结果已保存到 result_swap.jpg")
        else:
            print("无法加载源人脸")
    
    if args.camera:
        print("启动摄像头测试...")
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 处理帧
            result = module.process_frame(frame)
            
            # 显示结果
            cv2.imshow('Faceswap', result)
            
            # 按 'q' 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    module.cleanup()


if __name__ == '__main__':
    main()

