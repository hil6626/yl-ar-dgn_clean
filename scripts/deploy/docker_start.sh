#!/usr/bin/env bash

# YL-Monitor Docker 启动脚本

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 启动 YL-Monitor Docker 容器..."

# 检查 docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

COMPOSE_BIN="docker compose"
if command -v docker-compose &> /dev/null; then
    COMPOSE_BIN="docker-compose"
fi

COMPOSE_FILE="docker-compose.yaml"
if [[ "${1:-}" == "--dev" ]]; then
    COMPOSE_FILE="docker-compose.dev.yaml"
fi

# 检查环境文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，使用 .env.example 作为模板"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件，请根据需要修改配置"
    fi
fi

# 停止可能存在的旧容器
echo "🛑 停止旧容器..."
${COMPOSE_BIN} -f "${COMPOSE_FILE}" down || true

# 启动容器
echo "🏗️  启动容器..."
${COMPOSE_BIN} -f "${COMPOSE_FILE}" up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if ${COMPOSE_BIN} -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
    echo "✅ YL-Monitor 服务启动成功!"
    echo ""
    echo "🌐 访问地址:"
    echo "   - Web UI: http://0.0.0.0:5500"
    echo "   - API 文档: http://0.0.0.0:5500/docs"
    echo ""
    echo "📊 查看日志: ${COMPOSE_BIN} -f ${COMPOSE_FILE} logs -f"
    echo "🛑 停止服务: ${COMPOSE_BIN} -f ${COMPOSE_FILE} down"
else
    echo "❌ 服务启动失败，查看日志:"
    ${COMPOSE_BIN} -f "${COMPOSE_FILE}" logs
    exit 1
fi
