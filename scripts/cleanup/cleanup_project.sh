#!/bin/bash
# YL-AR-DGN Project Cleanup Script
# 项目清理脚本

echo "=========================================="
echo "  YL-AR-DGN 项目清理工具"
echo "=========================================="
echo ""

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数变量
DELETED_COUNT=0
ERROR_COUNT=0

# 清理函数
cleanup_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        local count=$(find "$dir" -type f \( -name "*.pyc" -o -name "*.tmp" -o -name "*.log" -o -name "__pycache__" -o -name ".pytest_cache" -o -name "*.egg-info" \) 2>/dev/null | wc -l)
        
        if [ "$count" -gt 0 ]; then
            find "$dir" -type f \( -name "*.pyc" -o -name "*.tmp" -o -name "*.log" \) -delete 2>/dev/null
            find "$dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
            find "$dir" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
            find "$dir" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
            
            echo -e "${GREEN}✓${NC} 清理 $description: $count 个文件"
            ((DELETED_COUNT+=count))
        else
            echo -e "${YELLOW}○${NC} $description: 无需清理"
        fi
    else
        echo -e "${YELLOW}○${NC} $description: 目录不存在"
    fi
}

# 检查重复文件
check_duplicates() {
    echo ""
    echo -e "${YELLOW}检查重复文件...${NC}"
    
    # 查找可能的重复文件
    find . -type f -name "*.md" | sort | uniq -d | while read file; do
        echo -e "${RED}!${NC} 重复文件: $file"
    done
}

# 清理日志文件
cleanup_logs() {
    echo ""
    echo -e "${YELLOW}清理日志文件...${NC}"
    
    # 清理 logs 目录
    if [ -d "logs" ]; then
        # 保留最近7天的日志
        find logs -name "*.log" -mtime +7 -delete 2>/dev/null
        echo -e "${GREEN}✓${NC} 清理7天前的日志文件"
    fi
}

# 清理临时文件
cleanup_temp() {
    echo ""
    echo -e "${YELLOW}清理临时文件...${NC}"
    
    find . -type f -name "*.tmp" -delete 2>/dev/null
    find . -type f -name ".DS_Store" -delete 2>/dev/null
    find . -type f -name "Thumbs.db" -delete 2>/dev/null
    
    echo -e "${GREEN}✓${NC} 清理临时文件完成"
}

# 清理Docker缓存
cleanup_docker() {
    echo ""
    echo -e "${YELLOW}Docker 缓存清理...${NC}"
    
    docker system prune -af --filter "until=24h" 2>/dev/null || echo -e "${YELLOW}○${NC} Docker 不可用，跳过"
}

# 清理旧测试报告
cleanup_test_reports() {
    echo ""
    echo -e "${YELLOW}清理测试报告...${NC}"
    
    # 查找并清理旧的测试结果文件
    find . -type f -name "*.xml" -path "*/test-results/*" -mtime +7 -delete 2>/dev/null
    find . -type f -name "*.html" -path "*/test-results/*" -mtime +7 -delete 2>/dev/null
    
    echo -e "${GREEN}✓${NC} 清理测试报告完成"
}

# 显示清理建议
show_suggestions() {
    echo ""
    echo "=========================================="
    echo "  清理建议"
    echo "=========================================="
    echo ""
    echo "1. Docker 缓存清理 (手动):"
    echo "   docker system prune -af"
    echo ""
    echo "2. 未使用的 Docker 镜像:"
    echo "   docker image prune -af"
    echo ""
    echo "3. 未使用的 Docker 卷:"
    echo "   docker volume prune -af"
    echo ""
    echo "4. 清理完成后检查:"
    echo "   du -sh ."
    echo ""
}

# 主程序
main() {
    echo -e "${GREEN}开始清理项目...${NC}"
    echo ""
    
    # 清理各目录
    cleanup_dir "." "项目根目录"
    cleanup_dir "YL-monitor" "YL-monitor 模块"
    cleanup_dir "AR-backend" "AR-backend 模块"
    cleanup_dir "scripts" "脚本目录"
    cleanup_dir "test" "测试目录"
    cleanup_dir "user" "用户模块"
    
    # 清理其他目录
    cleanup_logs
    cleanup_temp
    cleanup_test_reports
    
    # Docker 缓存 (可选)
    read -p "是否清理 Docker 缓存? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_docker
    fi
    
    # 显示结果
    echo ""
    echo "=========================================="
    echo -e "${GREEN}清理完成!${NC}"
    echo "=========================================="
    echo ""
    echo "已清理文件数: $DELETED_COUNT"
    echo "错误数: $ERROR_COUNT"
    
    # 显示磁盘使用情况
    echo ""
    echo "当前磁盘使用:"
    du -sh . 2>/dev/null || echo "无法计算磁盘使用"
    
    show_suggestions
}

# 执行主程序
main
