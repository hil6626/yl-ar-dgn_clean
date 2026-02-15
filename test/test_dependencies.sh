#!/bin/bash

# AR 系统依赖安装测试脚本
# 用于验证所有依赖项是否正确安装

echo "🔍 AR 系统依赖安装测试"
echo "========================"

# 检查Python版本
echo "📋 Python版本检查:"
python3 --version

# 检查虚拟环境
echo ""
echo "📋 虚拟环境检查:"
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未检测到虚拟环境"
else
    echo "✅ 虚拟环境: $VIRTUAL_ENV"
fi

# 检查关键依赖
echo ""
echo "📋 核心依赖检查:"

# Web框架
check_import() {
    local package=$1
    local import_name=${2:-$1}
    if python3 -c "import $import_name" 2>/dev/null; then
        echo "✅ $package"
    else
        echo "❌ $package"
    fi
}

echo "Web框架:"
check_import "flask"
check_import "flask_socketio" "flask_socketio"
check_import "flask_cors" "flask_cors"

echo ""
echo "数据处理:"
check_import "numpy"
check_import "PIL" "PIL"

echo ""
echo "计算机视觉:"
check_import "cv2" "cv2"
check_import "mediapipe"

echo ""
echo "音频处理:"
check_import "soundfile"
check_import "librosa"

echo ""
echo "系统监控:"
check_import "psutil"

echo ""
echo "网络通信:"
check_import "requests"
check_import "urllib3"

echo ""
echo "工具库:"
check_import "yaml" "yaml"
check_import "dateutil" "dateutil"

echo ""
echo "机器学习:"
check_import "torch"
check_import "torchvision"
check_import "torchaudio"

echo ""
echo "🎯 测试完成"