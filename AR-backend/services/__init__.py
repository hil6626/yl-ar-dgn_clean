"""
AR Backend Services 统一导出模块 (v3.0.0)

此模块提供所有服务的统一导入接口。
按照功能分为: core, face, pipeline, monitor, security, integration, utils

使用方式:
    from services import HealthCheck
    from services.face.detection import FaceDetector
    from services.monitor.performance import PerformanceCollector
"""

__version__ = "3.0.0"
__author__ = "AI 编程代理"

# Core services
from .core.health_check import HealthCheck
from .core.config_service import ConfigService

# Face services
from .face.detection import FaceDetector
from .face.detection import FaceDetector as FaceDetectionProcessor
from .face.recognition import FaceRecognizer
from .face.recognition import FaceRecognizer as FaceRecognitionProcessor
from .face.synthesis import FaceLiveCam

# Pipeline services
from .pipeline.video_processor import ImagePipeline
from .pipeline.video_processor import PipelineManager
from .pipeline.video_processor import VideoPipeline
from .pipeline.video_processor import InferenceEngine

# Monitor services
from .monitor.performance import PerformanceCollector
from .monitor.resource import ResourceMonitor
from .monitor.system import SystemMonitor
from .monitor.health import HealthService

# Security services
from .security import AuthService, RBACService, AuditService

# Integration services
from .integration import FaceSwapIntegration, DeepFaceLabIntegration, OBSCameraIntegration

# Utils services
from .utils import CacheManager, NotificationService, DeploymentTracker

__all__ = [
    # Core
    "HealthCheck", "ConfigService",
    
    # Face
    "FaceDetector", "FaceRecognizer", "FaceLiveCam",
    
    # Pipeline
    "ImagePipeline", "PipelineManager", "VideoPipeline", "InferenceEngine",
    
    # Monitor
    "PerformanceCollector", "ResourceMonitor", "SystemMonitor", "HealthService",
    
    # Security
    "AuthService", "RBACService", "AuditService",
    
    # Integration
    "FaceSwapIntegration", "DeepFaceLabIntegration", "OBSCameraIntegration",
    
    # Utils
    "CacheManager", "NotificationService", "DeploymentTracker",
]
