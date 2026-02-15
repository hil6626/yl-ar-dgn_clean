#!/bin/bash

# YL-Monitor MCP Server 验证脚本
# 用于验证 MCP Server 配置和与 VS Code/Postman 的联动

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MCP_SERVER="${PROJECT_ROOT}/.vscode/mcp-server.js"
MCP_CONFIG="${PROJECT_ROOT}/.vscode/mcp.json"
POSTMAN_COLLECTION="${PROJECT_ROOT}/tests/postman/yl-monitor-collection.json"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  YL-Monitor MCP Server 验证工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Node.js
echo -e "${YELLOW}[1/8] 检查 Node.js 环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js 未安装${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js 版本: ${NODE_VERSION}${NC}"

# 检查 MCP Server 文件
echo -e "${YELLOW}[2/8] 检查 MCP Server 文件...${NC}"
if [ ! -f "$MCP_SERVER" ]; then
    echo -e "${RED}✗ MCP Server 脚本不存在: ${MCP_SERVER}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MCP Server 脚本存在${NC}"

if [ ! -f "$MCP_CONFIG" ]; then
    echo -e "${RED}✗ MCP 配置文件不存在: ${MCP_CONFIG}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MCP 配置文件存在${NC}"

# 检查 MCP Server 语法
echo -e "${YELLOW}[3/8] 验证 MCP Server 语法...${NC}"
if ! node --check "$MCP_SERVER" 2>/dev/null; then
    echo -e "${RED}✗ MCP Server 脚本语法错误${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MCP Server 语法正确${NC}"

# 检查 MCP 配置 JSON
echo -e "${YELLOW}[4/8] 验证 MCP 配置...${NC}"
if ! python3 -c "import json; json.load(open('${MCP_CONFIG}'))" 2>/dev/null; then
    echo -e "${RED}✗ MCP 配置文件 JSON 格式错误${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MCP 配置 JSON 格式正确${NC}"

# 检查 Postman 集合
echo -e "${YELLOW}[5/8] 检查 Postman 集合...${NC}"
if [ ! -f "$POSTMAN_COLLECTION" ]; then
    echo -e "${YELLOW}⚠ Postman 集合不存在，将使用默认端点${NC}"
else
    if ! python3 -c "import json; json.load(open('${POSTMAN_COLLECTION}'))" 2>/dev/null; then
        echo -e "${RED}✗ Postman 集合 JSON 格式错误${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Postman 集合存在且格式正确${NC}"
fi

# 测试 MCP Server 功能
echo -e "${YELLOW}[6/8] 测试 MCP Server 核心功能...${NC}"

# 测试 list_files
echo -e "${BLUE}  测试 list_files...${NC}"
LIST_RESULT=$(echo '{"command": "list_files", "args": {"path": "app", "recursive": false}, "id": 1}' | timeout 5 node "$MCP_SERVER" "$PROJECT_ROOT" 2>/dev/null | head -1)

if echo "$LIST_RESULT" | grep -q '"success":true'; then
    FILE_COUNT=$(echo "$LIST_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['count'])" 2>/dev/null || echo "0")
    echo -e "${GREEN}  ✓ list_files 成功 (找到 ${FILE_COUNT} 个文件)${NC}"
else
    echo -e "${RED}  ✗ list_files 失败${NC}"
    echo "  响应: $LIST_RESULT"
fi

# 测试 read_file
echo -e "${BLUE}  测试 read_file...${NC}"
READ_RESULT=$(echo '{"command": "read_file", "args": {"path": "app/main.py"}, "id": 2}' | timeout 5 node "$MCP_SERVER" "$PROJECT_ROOT" 2>/dev/null | head -1)

if echo "$READ_RESULT" | grep -q '"success":true'; then
    FILE_SIZE=$(echo "$READ_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['size'])" 2>/dev/null || echo "0")
    echo -e "${GREEN}  ✓ read_file 成功 (文件大小: ${FILE_SIZE} bytes)${NC}"
else
    echo -e "${RED}  ✗ read_file 失败${NC}"
fi

# 测试 search
echo -e "${BLUE}  测试 search...${NC}"
SEARCH_RESULT=$(echo '{"command": "search", "args": {"pattern": "def.*health", "path": "app", "filePattern": "*.py"}, "id": 3}' | timeout 10 node "$MCP_SERVER" "$PROJECT_ROOT" 2>/dev/null | head -1)

if echo "$SEARCH_RESULT" | grep -q '"success":true'; then
    MATCH_COUNT=$(echo "$SEARCH_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['totalFiles'])" 2>/dev/null || echo "0")
    echo -e "${GREEN}  ✓ search 成功 (找到 ${MATCH_COUNT} 个文件匹配)${NC}"
else
    echo -e "${YELLOW}  ⚠ search 可能失败或超时${NC}"
fi

# 测试 get_api_collection
echo -e "${BLUE}  测试 get_api_collection...${NC}"
API_RESULT=$(echo '{"command": "get_api_collection", "args": {"collection": "yl-monitor-collection"}, "id": 4}' | timeout 5 node "$MCP_SERVER" "$PROJECT_ROOT" 2>/dev/null | head -1)

if echo "$API_RESULT" | grep -q '"success":true'; then
    ENDPOINT_COUNT=$(echo "$API_RESULT" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['result']['endpoints']))" 2>/dev/null || echo "0")
    echo -e "${GREEN}  ✓ get_api_collection 成功 (找到 ${ENDPOINT_COUNT} 个端点)${NC}"
else
    echo -e "${YELLOW}  ⚠ get_api_collection 可能失败${NC}"
fi

# 检查 YL-Monitor 服务状态
echo -e "${YELLOW}[7/8] 检查 YL-Monitor 服务状态...${NC}"
if curl -s http://localhost:5500/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ YL-Monitor 服务运行中 (端口 5500)${NC}"
    
    # 测试 api_request
    echo -e "${BLUE}  测试 api_request...${NC}"
    API_REQ_RESULT=$(echo '{"command": "api_request", "args": {"method": "GET", "endpoint": "/api/health"}, "id": 5}' | timeout 5 node "$MCP_SERVER" "$PROJECT_ROOT" 2>/dev/null | head -1)
    
    if echo "$API_REQ_RESULT" | grep -q '"success":true'; then
        STATUS_CODE=$(echo "$API_REQ_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['statusCode'])" 2>/dev/null || echo "0")
        echo -e "${GREEN}  ✓ api_request 成功 (HTTP ${STATUS_CODE})${NC}"
    else
        echo -e "${YELLOW}  ⚠ api_request 可能失败${NC}"
    fi
else
    echo -e "${YELLOW}⚠ YL-Monitor 服务未运行 (端口 5500)${NC}"
    echo -e "${YELLOW}  提示: 运行 ./scripts/tools/start_and_verify.sh 启动服务${NC}"
fi

# 检查 VS Code 扩展
echo -e "${YELLOW}[8/8] 检查 VS Code 扩展配置...${NC}"
VSCODE_EXT_DIR="${PROJECT_ROOT}/vscode-extension"
if [ -d "$VSCODE_EXT_DIR" ]; then
    if [ -f "${VSCODE_EXT_DIR}/package.json" ]; then
        echo -e "${GREEN}✓ VS Code 扩展目录存在${NC}"
        
        # 检查 package.json 中的 MCP 配置
        if grep -q "mcp" "${VSCODE_EXT_DIR}/package.json" 2>/dev/null; then
            echo -e "${GREEN}✓ VS Code 扩展包含 MCP 配置${NC}"
        else
            echo -e "${YELLOW}⚠ VS Code 扩展可能缺少 MCP 配置${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ VS Code 扩展缺少 package.json${NC}"
    fi
else
    echo -e "${YELLOW}⚠ VS Code 扩展目录不存在${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  MCP Server 验证完成!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}使用说明:${NC}"
echo -e "  1. 在 VS Code 中打开命令面板 (Ctrl+Shift+P)"
echo -e "  2. 输入 'YL-Monitor' 查看可用命令"
echo -e "  3. 使用 'MCP: 列出文件' 测试文件访问"
echo -e "  4. 使用 'MCP: 搜索代码' 测试代码搜索"
echo -e "  5. 使用 '在 Postman 中打开集合' 打开 API 测试"
echo ""
echo -e "${YELLOW}手动测试 MCP Server:${NC}"
echo -e "  node ${MCP_SERVER} ${PROJECT_ROOT}"
echo ""
