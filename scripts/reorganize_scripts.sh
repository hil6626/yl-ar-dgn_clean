#!/bin/bash
# Scripts Directory Refactoring Script
# 脚本目录重构脚本

echo "=========================================="
echo "  脚本目录重构"
echo "=========================================="

cd /workspaces/yl-ar-dgn

# 创建新的文件夹结构
echo ""
echo "📁 创建新的文件夹结构..."

# deploy/ - 部署相关
mkdir -p scripts/deploy

# cleanup/ - 清理相关
mkdir -p scripts/cleanup

# docs/ - 文档相关
mkdir -p scripts/docs

# utilities/ - 工具类
mkdir -p scripts/utilities

echo "✅ 文件夹创建完成"

# 移动脚本到对应文件夹
echo ""
echo "📦 移动脚本到对应文件夹..."

# 部署相关
move_deploy() {
    local file=$1
    if [ -f "scripts/$file" ]; then
        echo "  → 移动: scripts/$file → scripts/deploy/"
        mv "scripts/$file" "scripts/deploy/"
    fi
}

# 清理相关
move_cleanup() {
    local file=$1
    if [ -f "scripts/$file" ]; then
        echo "  → 移动: scripts/$file → scripts/cleanup/"
        mv "scripts/$file" "scripts/cleanup/"
    fi
}

# 文档相关
move_docs() {
    local file=$1
    if [ -f "scripts/$file" ]; then
        echo "  → 移动: scripts/$file → scripts/docs/"
        mv "scripts/$file" "scripts/docs/"
    fi
}

# 工具类
move_utilities() {
    local file=$1
    if [ -f "scripts/$file" ]; then
        echo "  → 移动: scripts/$file → scripts/utilities/"
        mv "scripts/$file" "scripts/utilities/"
    fi
}

# 移动部署脚本
move_deploy "deploy.sh"
move_deploy "rollback.sh"
move_deploy "notify_deployment.py"

# 移动清理脚本
move_cleanup "cleanup_project.sh"
move_cleanup "cleanup_tasks_docs.sh"
move_cleanup "final_cleanup.sh"
move_cleanup "refactor_directories.sh"
move_cleanup "clean_cache.sh"

# 移动文档脚本
move_docs "docs_generator.py"
move_docs "verify_yl-monitor_docs.sh"

# 移动工具类脚本
move_utilities "build_gui_components.py"
move_utilities "refactor_rules.py"
move_utilities "check_dependencies.py"
move_utilities "env.sh"
move_utilities "fix_paths_to_local.sh"
move_utilities "scripts_manager_enhanced.py"
move_utilities "scripts_manager.py"
move_utilities "verify_start.sh"

# 删除软链接
echo ""
echo "🔗 删除软链接..."
rm -f scripts/check_scripts_integrity.py
rm -f scripts/validate_backend_services.py
rm -f scripts/validate_frontend_architecture.py

echo ""
echo "=========================================="
echo "✅ 重构完成!"
echo "=========================================="
