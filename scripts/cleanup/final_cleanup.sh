#!/bin/bash
# Final Cleanup Script - Remove all completed task documents
# 最终清理脚本 - 移除所有已完成的任务文档

echo "=========================================="
echo "  最终清理 - 移除所有已完成的任务文档"
echo "=========================================="

TASKS_DIR="/workspaces/yl-ar-dgn/docs/tasks"
ARCHIVE_DIR="/workspaces/yl-ar-dgn/docs/cleanup-archive/tasks"

# 确保归档目录存在
mkdir -p "$ARCHIVE_DIR"

echo ""
echo "📦 移动所有任务文档到归档..."

# 移动所有任务相关文档
move_files() {
    local pattern=$1
    local description=$2
    
    for file in $TASKS_DIR/$pattern; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            echo "  → 移动: $basename"
            mv "$file" "$ARCHIVE_DIR/"
        fi
    done
}

# 移动任务文档
move_files "*-task.md" "任务文档"
move_files "task-*-deploy-*.md" "部署跟踪"
move_files "task-*-deploy-*.md" "部署跟踪"
move_files "*-execution-report.md" "执行报告"
move_files "IMPLEMENTATION_PLAN.md" "实施计划"

# 保留核心文档
echo ""
echo "✅ 保留核心文档:"
echo "  - README.md"
echo "  - TASK_EXECUTION_SUMMARY.md"
echo "  - IMPLEMENTATION_SUMMARY.md"
echo "  - TODO.md"

# 更新归档索引
echo ""
echo "📝 更新归档索引..."

cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Tasks Archive
# 任务归档

**最后更新:** 2026-02-04

本文档包含从 `docs/tasks/` 目录归档的所有已完成的任务文档。

## 归档内容

### 任务文档 (8个)
- other-001-task.md (基础设施搭建)
- rules-003-task.md (前端交互规范)
- AR-backend-004-task.md (性能监控)
- scripts-006-task.md (CI/CD集成)
- user-003-task.md (GUI组件)
- api-map-005-task.md (接口安全)
- other-004-task.md (文档体系)
- rules-002-task.md (规则重构)

### 部署跟踪 (4个)
- task-001-deploy-infra.md
- task-002-deploy-rules.md
- task-003-deploy-ar-backend-performance.md
- task-004-deploy-scripts-cicd.md

### 执行报告 (8个)
- 所有任务的执行报告

### 其他
- IMPLEMENTATION_PLAN.md

## 统计

| 类别 | 数量 |
|------|------|
| 任务文档 | 8 |
| 部署跟踪 | 4 |
| 执行报告 | 8 |
| 其他 | 1 |
| **总计** | **21** |

---

**版本:** 1.0.0  
**最后更新:** 2026-02-04
EOF

echo ""
echo "=========================================="
echo "✅ 清理完成!"
echo "=========================================="
echo ""
echo "已归档文档数: $(ls $ARCHIVE_DIR/*.md 2>/dev/null | wc -l)"
echo "保留文档数: $(ls $TASKS_DIR/*.md 2>/dev/null | wc -l)"
