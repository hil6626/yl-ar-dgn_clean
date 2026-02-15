#!/bin/bash
# YL-Monitor 旧文件清理脚本
# 功能：备份并清理冗余的旧页面脚本文件
# 版本: v1.0.0

set -e

echo "=== YL-Monitor 旧文件清理脚本 ==="
echo "执行时间: $(date)"
echo ""

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean/YL-monitor"
BACKUP_DIR="$PROJECT_ROOT/backups/js/$(date +%Y%m%d_%H%M%S)"

# 要备份和清理的旧文件列表
OLD_FILES=(
    "static/js/page-dag.js"
    "static/js/page-dag-simple.js"
    "static/js/page-scripts.js"
    "static/js/page-scripts-real.js"
    "static/js/page-api-doc.js"
    "static/js/page-api-doc-simple.js"
    "static/js/page-ar.js"
    "static/js/page-alert-center.js"
    "static/js/page-dashboard.js"
)

echo "1. 创建备份目录: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo ""
echo "2. 备份旧文件..."
for file in "${OLD_FILES[@]}"; do
    full_path="$PROJECT_ROOT/$file"
    if [ -f "$full_path" ]; then
        echo "  备份: $file"
        cp "$full_path" "$BACKUP_DIR/"
        echo -e "  ${GREEN}✓${NC} 已备份"
    else
        echo -e "  ${YELLOW}⚠${NC} 文件不存在: $file"
    fi
done

echo ""
echo "3. 检查新模块化入口..."
NEW_ENTRIES=(
    "static/js/pages/dag/index.js"
    "static/js/pages/scripts/index.js"
    "static/js/pages/api-doc/index.js"
    "static/js/pages/ar/index.js"
    "static/js/pages/alerts/index.js"
    "static/js/pages/dashboard/index.js"
)

all_entries_exist=true
for entry in "${NEW_ENTRIES[@]}"; do
    full_path="$PROJECT_ROOT/$entry"
    if [ -f "$full_path" ]; then
        echo -e "  ${GREEN}✓${NC} $entry"
    else
        echo -e "  ${RED}✗${NC} $entry (缺失!)"
        all_entries_exist=false
    fi
done

if [ "$all_entries_exist" = false ]; then
    echo ""
    echo -e "${RED}错误: 部分新模块化入口缺失，中止清理操作${NC}"
    echo "请确保所有新模块化入口文件已创建后再运行此脚本"
    exit 1
fi

echo ""
echo "4. 清理旧文件..."
read -p "确认要删除旧文件吗? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    for file in "${OLD_FILES[@]}"; do
        full_path="$PROJECT_ROOT/$file"
        if [ -f "$full_path" ]; then
            rm "$full_path"
            echo -e "  ${GREEN}✓${NC} 已删除: $file"
        fi
    done
    echo ""
    echo -e "${GREEN}清理完成!${NC}"
else
    echo ""
    echo -e "${YELLOW}操作已取消，旧文件保留${NC}"
fi

echo ""
echo "5. 生成清理报告..."
REPORT_FILE="$PROJECT_ROOT/backups/cleanup_report_$(date +%Y%m%d_%H%M%S).md"
cat > "$REPORT_FILE" << EOF
# YL-Monitor 文件清理报告

**执行时间**: $(date)

## 备份信息
- **备份目录**: $BACKUP_DIR
- **备份文件数**: $(ls -1 "$BACKUP_DIR" 2>/dev/null | wc -l)

## 清理的文件列表
$(for file in "${OLD_FILES[@]}"; do echo "- $file"; done)

## 新模块化入口状态
$(for entry in "${NEW_ENTRIES[@]}"; do 
    if [ -f "$PROJECT_ROOT/$entry" ]; then 
        echo "- ✅ $entry"
    else 
        echo "- ❌ $entry (缺失)"
    fi
done)

## 操作结果
- 清理操作: $([ "$confirm" == [yY] || "$confirm" == [yY][eE][sS] ] && echo "已执行" || echo "已取消")

## 建议后续操作
1. 验证所有页面正常加载
2. 检查浏览器控制台是否有404错误
3. 测试各页面核心功能
4. 清理备份目录（确认无误后）
EOF

echo "  报告已保存: $REPORT_FILE"

echo ""
echo "=== 清理脚本执行完成 ==="
echo ""
echo "备份位置: $BACKUP_DIR"
echo "报告位置: $REPORT_FILE"
echo ""
echo "建议操作:"
echo "1. 启动应用并测试所有页面"
echo "2. 检查浏览器控制台是否有错误"
echo "3. 确认无误后可删除备份: rm -rf $BACKUP_DIR"
