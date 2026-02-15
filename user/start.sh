#!/bin/bash
# AR Live Studio 启动脚本 (Linux/macOS)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  AR Live Studio 启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查Python版本
echo -e "${BLUE}[*] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] 错误: 未找到 python3${NC}"
    echo -e "${YELLOW}    请安装Python 3.8或更高版本${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}[✓] Python版本: $PYTHON_VERSION${NC}"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${BLUE}[*] 激活虚拟环境...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}[!] 警告: 未找到虚拟环境${NC}"
    echo -e "${YELLOW}    建议使用虚拟环境: python3 -m venv venv${NC}"
fi

# 检查关键依赖
echo -e "${BLUE}[*] 检查依赖...${NC}"
REQUIRED_PACKAGES=("PyQt5" "opencv-python" "numpy" "psutil" "requests" "flask")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${YELLOW}[!] 缺少以下依赖包:${NC}"
    printf '    - %s\n' "${MISSING_PACKAGES[@]}"
    echo ""
    read -p "是否自动安装缺失的依赖? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}[*] 安装依赖...${NC}"
        pip install "${MISSING_PACKAGES[@]}"
    else
        echo -e "${RED}[!] 缺少必要依赖，无法启动${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[✓] 所有依赖已安装${NC}"
fi

# 创建必要的目录
echo -e "${BLUE}[*] 创建必要的目录...${NC}"
mkdir -p logs config cache temp

# 设置环境变量
export PROJECT_ROOT="$SCRIPT_DIR/.."
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/..:$SCRIPT_DIR/../AR-backend:$SCRIPT_DIR/../AR-backend/core"

echo -e "${BLUE}[*] 环境配置:${NC}"
echo -e "    PROJECT_ROOT: $PROJECT_ROOT"
echo -e "    PYTHONPATH: $PYTHONPATH"

# 检查AR-backend路径
if [ ! -d "$SCRIPT_DIR/../AR-backend" ]; then
    echo -e "${RED}[!] 错误: 未找到AR-backend目录${NC}"
    echo -e "${YELLOW}    请确保项目结构正确${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] AR-backend目录已找到${NC}"

# 检查端口占用
echo -e "${BLUE}[*] 检查端口...${NC}"
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[!] 警告: 端口 $port 已被占用${NC}"
        return 1
    fi
    return 0
}

if ! check_port 5502; then
    echo -e "${YELLOW}    本地HTTP服务可能已在运行${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动 AR Live Studio${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 启动应用
python3 main.py

# 捕获退出状态
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  应用异常退出 (代码: $EXIT_CODE)${NC}"
    echo -e "${RED}========================================${NC}"
    exit $EXIT_CODE
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AR Live Studio 已正常关闭${NC}"
echo -e "${GREEN}========================================${NC}"
