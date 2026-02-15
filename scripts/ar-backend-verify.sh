#!/bin/bash
# AR Backend 快速验证脚本
# 功能: 快速检查AR Backend部署状态

echo "=========================================="
echo "  AR Backend 快速验证"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASS=0
FAIL=0
SKIP=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}❌${NC} $1"
    ((FAIL++))
}

check_skip() {
    echo -e "${YELLOW}○${NC} $1"
    ((SKIP++))
}

# 项目目录
PROJECT_DIR="/workspaces/yl-ar-dgn/AR-backend"
cd "$PROJECT_DIR"

echo "项目目录: $PROJECT_DIR"
echo ""

echo "1️⃣ Python 环境检查"
echo "-------------------------------------------"

# Python版本
PYTHON_VERSION=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    check_pass "Python3 可用: $PYTHON_VERSION"
else
    check_fail "Python3 不可用"
fi

# pip
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version 2>&1)
    check_pass "pip3 可用: $PIP_VERSION"
else
    check_fail "pip3 不可用"
fi

echo ""
echo "2️⃣ 虚拟环境检查"
echo "-------------------------------------------"

if [ -d "$PROJECT_DIR/venv" ]; then
    if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
        VENV_PYTHON=$("$PROJECT_DIR/venv/bin/python" --version 2>&1)
        check_pass "虚拟环境存在: $VENV_PYTHON"
    else
        check_fail "虚拟环境损坏 (Python不可执行)"
    fi
else
    check_skip "虚拟环境不存在"
fi

echo ""
echo "3️⃣ 核心依赖检查"
echo "-------------------------------------------"

# 检查核心Python模块
MODULES=("flask" "cv2" "numpy" "psutil" "requests")

for module in "${MODULES[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        check_pass "$module"
    else
        check_fail "$module (未安装)"
    fi
done

echo ""
echo "4️⃣ 目录结构检查"
echo "-------------------------------------------"

DIRS=("core" "services" "config" "data" "app" "requirements")

for dir in "${DIRS[@]}"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        check_pass "$dir/ 目录存在"
    else
        check_fail "$dir/ 目录不存在"
    fi
done

echo ""
echo "5️⃣ 配置文件检查"
echo "-------------------------------------------"

# 检查关键文件
FILES=(
    "requirements/requirements.txt"
    "config/pipeline.yaml"
    "main.py"
    "app/launcher.py"
    "core/path_manager.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        check_pass "$file"
    else
        check_fail "$file 不存在"
    fi
done

echo ""
echo "6️⃣ 模块导入测试"
echo "-------------------------------------------"

# 设置PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# 测试关键模块
MODULES_TEST=(
    "core.path_manager:PathManager"
    "core.utils:Utils"
    "services.health_check:HealthCheck"
    "services.config_service:ConfigService"
)

for module_test in "${MODULES_TEST[@]}"; do
    IFS=':' read -r module classname <<< "$module_test"
    if python3 -c "from $module import $classname" 2>/dev/null; then
        check_pass "$module.$classname"
    else
        check_fail "$module.$classname (导入失败)"
    fi
done

echo ""
echo "7️⃣ 磁盘空间检查"
echo "-------------------------------------------"

DISK_USAGE=$(df -h "$PROJECT_DIR" 2>/dev/null | tail -1 | awk '{print $5 " 已用"}')
check_pass "磁盘使用: $DISK_USAGE"

echo ""
echo "=========================================="
echo "  验证结果汇总"
echo "=========================================="
echo ""
echo -e "✅ 通过: $PASS"
echo -e "❌ 失败: $FAIL"
echo -e "○ 跳过: $SKIP"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  有 $FAIL 项检查失败${NC}"
    echo ""
    echo "建议操作:"
    echo "1. 安装缺失依赖: pip install -r requirements/requirements.txt"
    echo "2. 创建虚拟环境: python3 -m venv venv && source venv/bin/activate && pip install -r requirements/requirements.txt"
    echo "3. 运行完整验证: python3 verify_deployment.py"
    exit 1
fi

