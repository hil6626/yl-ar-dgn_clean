#!/bin/bash
#===============================================================================
# AR Backend Services 目录重组脚本
#
# 功能:
#   1. 备份原services目录
#   2. 创建新的目录结构
#   3. 移动服务文件到对应子目录
#   4. 清理原文件和空目录
#   5. 创建统一导出索引
#
# 用法:
#   bash scripts/restructure-services.sh [--backup-only|--verify-only]
#
# 依赖:
#   - Bash 4.0+
#   - rsync (用于备份)
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
NC='\033[0m' # No Color

#-------------------------------------------------------------------------------
# 全局变量
#-------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICES_DIR="$PROJECT_DIR/AR-backend/services"
BACKUP_DIR=""
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 计数器
declare -i FILE_COUNT=0
declare -i DIR_COUNT=0
declare -i SKIP_COUNT=0

#-------------------------------------------------------------------------------
# 日志函数
#-------------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
}

#-------------------------------------------------------------------------------
# 帮助信息
#-------------------------------------------------------------------------------
show_help() {
    cat << EOF
用法: $(basename "$0") [选项]

AR Backend Services 目录重组脚本

选项:
    --backup-only    仅创建备份，不执行重组
    --verify-only    仅验证当前结构，不执行任何修改
    --rollback       回滚到上次备份
    -h, --help       显示帮助信息

示例:
    $(basename "$0")                   # 执行完整重组
    $(basename "$0") --backup-only     # 仅创建备份
    $(basename "$0") --verify-only     # 仅验证结构
    $(basename "$0") --rollback        # 回滚上次备份

注意事项:
    - 脚本会自动创建备份
    - 重组前请确保没有运行的服务
    - 重组后需要更新导入路径
EOF
}

#-------------------------------------------------------------------------------
# 检查前置条件
#-------------------------------------------------------------------------------
check_prerequisites() {
    log_section "检查前置条件"

    # 检查 services 目录是否存在
    if [ ! -d "$SERVICES_DIR" ]; then
        log_error "services 目录不存在: $SERVICES_DIR"
        exit 1
    fi
    log_success "services 目录存在"

    # 检查 rsync 是否可用
    if ! command -v rsync &> /dev/null; then
        log_warn "rsync 未安装，将使用 cp 替代"
    fi

    # 检查是否有足够的磁盘空间 (至少 1GB)
    AVAILABLE_KB=$(df -k "$PROJECT_DIR" | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_KB" -lt 1048576 ]; then
        log_warn "磁盘空间不足 1GB，可用: $(($AVAILABLE_KB / 1024))MB"
    else
        log_success "磁盘空间充足: $(($AVAILABLE_KB / 1024 / 1024))GB"
    fi
}

#-------------------------------------------------------------------------------
# 备份原目录
#-------------------------------------------------------------------------------
backup_original() {
    log_section "步骤1: 备份原 services 目录"

    BACKUP_DIR="$PROJECT_DIR/services.backup.$TIMESTAMP"

    log_info "创建备份目录: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"

    if command -v rsync &> /dev/null; then
        rsync -av --progress "$SERVICES_DIR/" "$BACKUP_DIR/"
    else
        cp -r "$SERVICES_DIR"/* "$BACKUP_DIR/"
    fi

    log_success "备份完成: $BACKUP_DIR"
    log_info "备份大小: $(du -sh "$BACKUP_DIR" | cut -f1)"
}

#-------------------------------------------------------------------------------
# 创建新目录结构
#-------------------------------------------------------------------------------
create_directory_structure() {
    log_section "步骤2: 创建新的目录结构"

    cd "$SERVICES_DIR"

    log_info "创建主目录..."

    # 创建子目录
    mkdir -p core
    mkdir -p face/{detection,recognition,synthesis}
    mkdir -p pipeline/{inference_engine,video_processor}
    mkdir -p monitor/{performance,resource,system,health}
    mkdir -p security
    mkdir -p integration
    mkdir -p utils

    log_success "子目录创建完成"

    # 创建 __init__.py 文件
    log_info "创建 __init__.py 文件..."
    touch core/__init__.py
    touch face/__init__.py
    touch face/detection/__init__.py
    touch face/recognition/__init__.py
    touch face/synthesis/__init__.py
    touch pipeline/__init__.py
    touch pipeline/inference_engine/__init__.py
    touch monitor/__init__.py
    touch monitor/performance/__init__.py
    touch monitor/resource/__init__.py
    touch monitor/system/__init__.py
    touch monitor/health/__init__.py
    touch security/__init__.py
    touch integration/__init__.py
    touch utils/__init__.py

    log_success "所有 __init__.py 文件创建完成"
}

#-------------------------------------------------------------------------------
# 移动文件到对应目录
#-------------------------------------------------------------------------------
move_files() {
    log_section "步骤3: 移动服务文件"

    cd "$SERVICES_DIR"

    # ---------- Core 服务 ----------
    log_info "移动 Core 服务..."
    [ -f "health_check.py" ] && { cp health_check.py core/; rm health_check.py; log_success "health_check.py -> core/"; }
    [ -f "config_service.py" ] && { cp config_service.py core/; rm config_service.py; log_success "config_service.py -> core/"; }

    # ---------- Face 服务 ----------
    log_info "移动 Face 服务..."

    # 人脸检测
    if [ -f "face_detection_processor.py" ]; then
        cp face_detection_processor.py face/detection/processor.py
        rm face_detection_processor.py
        log_success "face_detection_processor.py -> face/detection/processor.py"
    fi
    if [ -d "face_detection" ]; then
        cp -r face_detection/* face/detection/ 2>/dev/null || true
        rm -rf face_detection
        log_success "face_detection/ -> face/detection/"
    fi

    # 人脸识别
    if [ -f "face_recognition_processor.py" ]; then
        cp face_recognition_processor.py face/recognition/processor.py
        rm face_recognition_processor.py
        log_success "face_recognition_processor.py -> face/recognition/processor.py"
    fi
    if [ -d "face_recognition" ]; then
        cp -r face_recognition/* face/recognition/ 2>/dev/null || true
        rm -rf face_recognition
        log_success "face_recognition/ -> face/recognition/"
    fi

    # 人脸合成/直播
    if [ -f "face_live_cam.py" ]; then
        cp face_live_cam.py face/synthesis/live_cam.py
        rm face_live_cam.py
        log_success "face_live_cam.py -> face/synthesis/live_cam.py"
    fi

    # 清理空的人脸子目录
    rm -rf face_blender face_alignment face_synthesis 2>/dev/null || true

    # ---------- Monitor 服务 ----------
    log_info "移动 Monitor 服务..."

    # 性能监控
    [ -f "performance_collector.py" ] && { cp performance_collector.py monitor/performance/collector.py; rm performance_collector.py; log_success "performance_collector.py -> monitor/performance/"; }
    [ -f "performance_optimizer.py" ] && { cp performance_optimizer.py monitor/performance/optimizer.py; rm performance_optimizer.py; log_success "performance_optimizer.py -> monitor/performance/"; }

    # 资源监控
    [ -f "resource_monitor.py" ] && { cp resource_monitor.py monitor/resource/monitor.py; rm resource_monitor.py; log_success "resource_monitor.py -> monitor/resource/"; }

    # 健康检查
    [ -f "health_check_service.py" ] && { cp health_check_service.py monitor/health/service.py; rm health_check_service.py; log_success "health_check_service.py -> monitor/health/"; }

    # 清理重复目录
    rm -rf performance_monitor monitor 2>/dev/null || true

    # ---------- Security 服务 ----------
    log_info "移动 Security 服务..."
    [ -f "auth.py" ] && { cp auth.py security/auth.py; rm auth.py; log_success "auth.py -> security/"; }
    [ -f "rbac.py" ] && { cp rbac.py security/rbac.py; rm rbac.py; log_success "rbac.py -> security/"; }
    [ -f "audit.py" ] && { cp audit.py security/audit.py; rm audit.py; log_success "audit.py -> security/"; }
    [ -f "rbac_manager.py" ] && { cp rbac_manager.py security/manager.py; rm rbac_manager.py; log_success "rbac_manager.py -> security/"; }

    # ---------- Integration 服务 ----------
    log_info "移动 Integration 服务..."
    [ -f "faceswap_module.py" ] && { cp faceswap_module.py integration/faceswap.py; rm faceswap_module.py; log_success "faceswap_module.py -> integration/"; }
    [ -f "deep_face_lab.py" ] && { cp deep_face_lab.py integration/deep_face_lab.py; rm deep_face_lab.py; log_success "deep_face_lab.py -> integration/"; }
    [ -f "obs_virtual_camera.py" ] && { cp obs_virtual_camera.py integration/obs_camera.py; rm obs_virtual_camera.py; log_success "obs_virtual_camera.py -> integration/"; }

    # 清理空目录
    rm -rf deploy display_manager logging model_loader model_manager 2>/dev/null || true

    # ---------- Utils 服务 ----------
    log_info "移动 Utils 服务..."
    [ -f "cache_manager_service.py" ] && { cp cache_manager_service.py utils/cache_manager.py; rm cache_manager_service.py; log_success "cache_manager_service.py -> utils/"; }
    [ -f "notification_service.py" ] && { cp notification_service.py utils/notification.py; rm notification_service.py; log_success "notification_service.py -> utils/"; }
    [ -f "deployment_tracker_service.py" ] && { cp deployment_tracker_service.py utils/deployment_tracker.py; rm deployment_tracker_service.py; log_success "deployment_tracker_service.py -> utils/"; }

    log_success "文件移动完成"
}

#-------------------------------------------------------------------------------
# 清理原文件
#-------------------------------------------------------------------------------
cleanup_original() {
    log_section "步骤4: 清理原文件和空目录"

    cd "$SERVICES_DIR"

    # 列出将被清理的文件
    PY_FILES=$(find . -maxdepth 1 -name "*.py" -type f 2>/dev/null)
    if [ -n "$PY_FILES" ]; then
        log_info "清理独立 .py 文件..."
        for file in $PY_FILES; do
            filename=$(basename "$file")
            # 保留 __init__.py
            if [ "$filename" != "__init__.py" ]; then
                rm -f "$file"
                log_success "删除: $filename"
            fi
        done
    fi

    # 清理空子目录
    log_info "清理空子目录..."
    for dir in */; do
        if [ -d "$dir" ] && [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
            rmdir "$dir" 2>/dev/null || true
        fi
    done

    log_success "清理完成"
}

#-------------------------------------------------------------------------------
# 创建统一导出索引
#-------------------------------------------------------------------------------
create_unified_index() {
    log_section "步骤5: 创建统一导出索引"

    cat > "$SERVICES_DIR/__init__.py" << 'EOF'
"""
AR Backend Services 统一导出模块

此模块提供所有服务的统一导入接口。
按照功能分为: core, face, pipeline, monitor, security, integration, utils

使用方式:
    from services import HealthCheck
    from services.face.detection import FaceDetector
    from services.monitor.performance import PerformanceCollector
"""

# 版本信息
__version__ = "2.0.0"
__author__ = "AI 编程代理"

# Core services
try:
    from .core.health_check import HealthCheck
except ImportError:
    HealthCheck = None

try:
    from .core.config_service import ConfigService
except ImportError:
    ConfigService = None

# Face services
try:
    from .face.detection.processor import FaceDetector
except ImportError:
    FaceDetector = None

try:
    from .face.recognition.processor import FaceRecognizer
except ImportError:
    FaceRecognizer = None

try:
    from .face.synthesis.live_cam import FaceLiveCam
except ImportError:
    FaceLiveCam = None

# Pipeline services
try:
    from .pipeline.frame_buffer import FrameBuffer
except ImportError:
    FrameBuffer = None

try:
    from .pipeline.inference_engine import InferenceEngine
except ImportError:
    InferenceEngine = None

try:
    from .pipeline.video_pipeline import VideoPipeline
except ImportError:
    VideoPipeline = None

try:
    from .pipeline.output_processor import OutputProcessor
except ImportError:
    OutputProcessor = None

# Monitor services
try:
    from .monitor.performance.collector import PerformanceCollector
except ImportError:
    PerformanceCollector = None

try:
    from .monitor.resource.monitor import ResourceMonitor
except ImportError:
    ResourceMonitor = None

try:
    from .monitor.system.service import SystemMonitor
except ImportError:
    SystemMonitor = None

try:
    from .monitor.health.service import HealthService
except ImportError:
    HealthService = None

# Security services
try:
    from .security.auth import AuthService
except ImportError:
    AuthService = None

try:
    from .security.rbac import RBACService
except ImportError:
    RBACService = None

try:
    from .security.audit import AuditService
except ImportError:
    AuditService = None

try:
    from .security.manager import SecurityManager
except ImportError:
    SecurityManager = None

# Integration services
try:
    from .integration.faceswap import FaceSwapIntegration
except ImportError:
    FaceSwapIntegration = None

try:
    from .integration.deep_face_lab import DeepFaceLabIntegration
except ImportError:
    DeepFaceLabIntegration = None

try:
    from .integration.obs_camera import OBSCameraIntegration
except ImportError:
    OBSCameraIntegration = None

# Utils services
try:
    from .utils.cache_manager import CacheManager
except ImportError:
    CacheManager = None

try:
    from .utils.notification import NotificationService
except ImportError:
    NotificationService = None

try:
    from .utils.deployment_tracker import DeploymentTracker
except ImportError:
    DeploymentTracker = None

__all__ = [
    # Core
    ("HealthCheck", "ConfigService"),
    
    # Face
    ("FaceDetector", "FaceRecognizer", "FaceLiveCam"),
    
    # Pipeline
    ("FrameBuffer", "InferenceEngine", "VideoPipeline", "OutputProcessor"),
    
    # Monitor
    ("PerformanceCollector", "ResourceMonitor", "SystemMonitor", "HealthService"),
    
    # Security
    ("AuthService", "RBACService", "AuditService", "SecurityManager"),
    
    # Integration
    ("FaceSwapIntegration", "DeepFaceLabIntegration", "OBSCameraIntegration"),
    
    # Utils
    ("CacheManager", "NotificationService", "DeploymentTracker"),
]
EOF

    log_success "统一导出索引创建完成: $SERVICES_DIR/__init__.py"
}

#-------------------------------------------------------------------------------
# 验证新结构
#-------------------------------------------------------------------------------
verify_new_structure() {
    log_section "步骤6: 验证新目录结构"

    cd "$SERVICES_DIR"

    echo ""
    echo "目录结构:"
    echo "-------------------------------------------"
    tree -L 3 -d 2>/dev/null || find . -type d | head -30
    echo ""

    echo ""
    echo "文件统计:"
    echo "-------------------------------------------"
    TOTAL_DIRS=$(find . -type d | wc -l)
    TOTAL_FILES=$(find . -name "*.py" | wc -l)
    echo "目录数: $TOTAL_DIRS"
    echo "Python文件数: $TOTAL_FILES"
    echo ""

    # 验证关键目录
    echo "关键目录验证:"
    echo "-------------------------------------------"
    for dir in core face pipeline monitor security integration utils; do
        if [ -d "$dir" ]; then
            log_success "$dir/ 存在"
        else
            log_error "$dir/ 不存在"
        fi
    done

    echo ""
    log_success "结构验证完成"
}

#-------------------------------------------------------------------------------
# 回滚函数
#-------------------------------------------------------------------------------
rollback() {
    log_section "回滚操作"

    # 查找最新的备份
    LATEST_BACKUP=$(ls -td "$PROJECT_DIR"/services.backup.*/ 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKUP" ]; then
        log_error "没有找到备份目录"
        exit 1
    fi

    log_info "发现备份: $LATEST_BACKUP"
    read -p "确认回滚? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "执行回滚..."

        # 备份当前状态
        cp -r "$SERVICES_DIR" "$PROJECT_DIR/services.current.$(date +%Y%m%d_%H%M%S)"

        # 恢复原状态
        rm -rf "$SERVICES_DIR"
        cp -r "$LATEST_BACKUP" "$SERVICES_DIR"

        log_success "回滚完成"
        log_info "当前状态已备份到: $PROJECT_DIR/services.current.*/"
    else
        log_info "回滚已取消"
    fi
}

#-------------------------------------------------------------------------------
# 主函数
#-------------------------------------------------------------------------------
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          AR Backend Services 目录重组脚本                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # 解析参数
    case "${1:-}" in
        --backup-only)
            check_prerequisites
            backup_original
            exit 0
            ;;
        --verify-only)
            check_prerequisites
            verify_new_structure
            exit 0
            ;;
        --rollback)
            rollback
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
    esac

    # 执行完整重组
    check_prerequisites
    backup_original
    create_directory_structure
    move_files
    cleanup_original
    create_unified_index
    verify_new_structure

    log_section "重组完成!"
    echo ""
    echo "后续步骤:"
    echo "  1. 更新导入路径: 检查并更新各模块的 import 语句"
    echo "  2. 运行验证: bash scripts/ar-backend-verify.sh"
    echo "  3. 完整验证: cd AR-backend && python3 verify_deployment.py"
    echo ""
    echo "回滚命令:"
    echo "  bash scripts/restructure-services.sh --rollback"
    echo ""
}

#-------------------------------------------------------------------------------
# 入口点
#-------------------------------------------------------------------------------
main "$@"

