#!/bin/bash
# Directory Structure Refactoring Script
# 目录结构重构脚本

echo "=========================================="
echo "  项目目录结构整理"
echo "=========================================="

cd /workspaces/yl-ar-dgn

# 1. 合并 infrastructure/logs 到 logs/
echo ""
echo "📦 1. 合并 logs 目录..."

INFRA_LOGS="/workspaces/yl-ar-dgn/infrastructure/logs"
MAIN_LOGS="/workspaces/yl-ar-dgn/logs"

# 检查infrastructure/logs是否有内容
if [ "$(ls -A $INFRA_LOGS 2>/dev/null)" ]; then
    # 移动子目录到主logs
    for dir in $INFRA_LOGS/*/; do
        if [ -d "$dir" ]; then
            basename=$(basename "$dir")
            echo "  → 移动: infrastructure/logs/$basename → logs/infrastructure/"
            mkdir -p $MAIN_LOGS/infrastructure
            mv "$dir" $MAIN_LOGS/infrastructure/ 2>/dev/null || true
        fi
    done
    # 移动文件
    for file in $INFRA_LOGS/*; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            echo "  → 移动: infrastructure/$basename → logs/infrastructure/"
            mv "$file" $MAIN_LOGS/infrastructure/ 2>/dev/null || true
        fi
    done
fi

# 2. 合并 infrastructure/data 到 data/
echo ""
echo "📦 2. 合并 data 目录..."

INFRA_DATA="/workspaces/yl-ar-dgn/infrastructure/data"
MAIN_DATA="/workspaces/yl-ar-dgn/data"

if [ -d "$INFRA_DATA" ] && [ "$(ls -A $INFRA_DATA 2>/dev/null)" ]; then
    for dir in $INFRA_DATA/*/; do
        if [ -d "$dir" ]; then
            basename=$(basename "$dir")
            echo "  → 移动: infrastructure/data/$basename → data/infrastructure/"
            mkdir -p $MAIN_DATA/infrastructure
            mv "$dir" $MAIN_DATA/infrastructure/ 2>/dev/null || true
        fi
    done
fi

# 3. 合并 infrastructure/configs 到 config/
echo ""
echo "📦 3. 合并 configs 目录..."

INFRA_CONFIGS="/workspaces/yl-ar-dgn/infrastructure/configs"
MAIN_CONFIG="/workspaces/yl-ar-dgn/config"

if [ -d "$INFRA_CONFIGS" ] && [ "$(ls -A $INFRA_CONFIGS 2>/dev/null)" ]; then
    for file in $INFRA_CONFIGS/*; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            echo "  → 移动: infrastructure/configs/$basename → config/infrastructure/"
            mkdir -p $MAIN_CONFIG/infrastructure
            cp "$file" $MAIN_CONFIG/infrastructure/ 2>/dev/null || true
        fi
    done
fi

# 4. 合并 infrastructure/backups 到 config/backups
echo ""
echo "📦 4. 合并 backups 目录..."

INFRA_BACKUPS="/workspaces/yl-ar-dgn/infrastructure/backups"

if [ -d "$INFRA_BACKUPS" ] && [ "$(ls -A $INFRA_BACKUPS 2>/dev/null)" ]; then
    mkdir -p $MAIN_CONFIG/backups
    for dir in $INFRA_BACKUPS/*/; do
        if [ -d "$dir" ]; then
            basename=$(basename "$dir")
            echo "  → 移动: infrastructure/backups/$basename → config/backups/"
            cp -r "$dir" $MAIN_CONFIG/backups/ 2>/dev/null || true
        fi
    done
fi

echo ""
echo "=========================================="
echo "✅ 目录整理完成!"
echo "=========================================="
