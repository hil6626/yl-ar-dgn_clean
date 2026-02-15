#!/bin/bash
#===============================================================================
# AR Backend Services 目录清理与完善脚本
#
# 功能:
#   1. 整合 pipeline 目录文件
#   2. 整合 monitor 目录文件
#   3. 清理残留的空旧目录
#
# 用法:
#   bash scripts/cleanup-services-structure.sh
#
#===============================================================================

set -euo pipefail

#-------------------------------------------------------------------------------
# 颜色定义
#-------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#-------------------------------------------------------------------------------
# 日志函数
#-------------------------------------------------------------------------------
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

#-------------------------------------------------------------------------------
# 主函数
#-------------------------------------------------------------------------------
main() {
    cd /workspaces/yl-ar-dgn/AR-backend/services
    
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          AR Backend Services 结构清理脚本                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # ---------- 整合 pipeline 目录 ----------
    log_info "检查并整合 pipeline 目录..."
    
    # 移动 pipeline 下的 .py 文件
    if [ -f "pipeline/image_pipeline.py" ]; then
        mkdir -p pipeline/video_processor
        cp pipeline/image_pipeline.py pipeline/video_processor/ 2>/dev/null || true
        cp pipeline/pipeline_manager.py pipeline/video_processor/ 2>/dev/null || true
        cp pipeline/video_pipeline.py pipeline/video_processor/ 2>/dev/null || true
        log_success "整合 pipeline 目录文件"
    fi
    
    # 检查是否有 inference_engine 子目录需要移动
    if [ -d "pipeline/inference_engine" ]; then
        cp -r pipeline/inference_engine/* pipeline/video_processor/ 2>/dev/null || true
        log_success "整合 inference_engine 到 pipeline/video_processor"
    fi
    
    # ---------- 整合 monitor 目录 ----------
    log_info "检查并整合 monitor 目录..."
    
    # 检查 health 子目录
    if [ -d "health" ]; then
        mkdir -p monitor/health
        cp -r health/* monitor/health/ 2>/dev/null || true
        log_success "整合 health 到 monitor/health"
    fi
    
    # 检查其他可能的子目录
    for subdir in performance resource system; do
        if [ -d "$subdir" ]; then
            mkdir -p monitor/$subdir
            cp -r $subdir/* monitor/$subdir/ 2>/dev/null || true
            log_success "整合 $subdir 到 monitor/$subdir"
        fi
    done
    
    # ---------- 清理残留目录 ----------
    log_info "清理残留的空旧目录..."
    
    # 需要清理的目录列表
    DIRS_TO_REMOVE=(
        "adaptive_optimizer"
        "display_manager"
        "face_alignment"
        "face_blender"
        "face_synthesis"
        "frame_buffer"
        "health"
        "inference_engine"
        "logging"
        "model_loader"
        "model_manager"
        "output_processor"
        "performance_monitor"
        "recorder"
        "resource_manager"
        "system_integrator"
        "video_pipeline"
        "video_stream"
        "workflow_manager"
    )
    
    for dir in "${DIRS_TO_REMOVE[@]}"; do
        if [ -d "$dir" ]; then
            # 检查目录是否为空
            if [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
                rmdir "$dir" 2>/dev/null || true
                log_success "删除空目录: $dir"
            else
                log_warn "目录非空，保留: $dir"
            fi
        fi
    done
    
    # ---------- 创建最终的 __init__.py ----------
    log_info "更新统一导出索引..."
    
    cat > "__init__.py" << 'EOF'
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
EOF
    
    log_success "统一导出索引已更新"
    
    # ---------- 最终验证 ----------
    echo ""
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  最终目录结构${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
    
    echo "服务模块:"
    for dir in core face pipeline monitor security integration utils; do
        if [ -d "$dir" ]; then
            file_count=$(find "$dir" -name "*.py" 2>/dev/null | wc -l)
            echo -e "  ${GREEN}✓${NC} $dir/ ($file_count 文件)"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ 服务结构清理完成!${NC}"
    echo ""
}

main "$@"

