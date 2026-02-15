#!/bin/bash
# Cleanup Completed Tasks Documentation
# 清理已完成任务文档

echo "=========================================="
echo "  清理已完成的任务文档"
echo "=========================================="

ARCHIVE_DIR="/workspaces/yl-ar-dgn/docs/cleanup-archive"
TASKS_DIR="/workspaces/yl-ar-dgn/docs/tasks"
PROJECT_DIR="/workspaces/yl-ar-dgn/docs/project"

# 创建归档目录
mkdir -p "$ARCHIVE_DIR/tasks"
mkdir -p "$ARCHIVE_DIR/project"

# 清理 tasks 目录中已完成的任务文档
echo ""
echo "📦 移动已完成的文档到归档..."

# 任务文档 - 保留索引，清理详细内容
move_task_doc() {
    local file=$1
    if [ -f "$TASKS_DIR/$file" ]; then
        echo "  → 移动: $file"
        mv "$TASKS_DIR/$file" "$ARCHIVE_DIR/tasks/"
    fi
}

# 移动已完成的任务文档
move_task_doc "other-001-task.md"
move_task_doc "rules-003-task.md"
move_task_doc "AR-backend-004-task.md"
move_task_doc "scripts-006-task.md"
move_task_doc "user-003-task.md"
move_task_doc "api-map-005-task.md"
move_task_doc "other-004-task.md"
move_task_doc "rules-002-task.md"

# 移动部署跟踪文档
move_task_doc "task-001-deploy-infra.md"
move_task_doc "task-002-deploy-rules.md"
move_task_doc "task-003-deploy-ar-backend-performance.md"
move_task_doc "task-004-deploy-scripts-cicd.md"

# 移动执行报告
move_task_doc "task-001-deploy-infra-execution-report.md"
move_task_doc "task-002-deploy-rules-execution-report.md"
move_task_doc "task-003-deploy-ar-backend-performance-execution-report.md"
move_task_doc "task-004-deploy-scripts-cicd-execution-report.md"
move_task_doc "api-map-005-task-execution-report.md"
move_task_doc "other-004-task-execution-report.md"
move_task_doc "rules-002-task-execution-report.md"
move_task_doc "user-003-task-execution-report.md"

# 清理 project 目录中已归档的子目录
echo ""
echo "📦 移动已归档的模块文档..."

move_project_doc() {
    local dir=$1
    if [ -d "$PROJECT_DIR/$dir" ]; then
        echo "  → 移动目录: $dir/"
        mv "$PROJECT_DIR/$dir" "$ARCHIVE_DIR/project/"
    fi
}

move_project_doc "api-map-docs"
move_project_doc "AR-backend-docs"
move_project_doc "scripts-docs"
move_project_doc "user-docs"
move_project_doc "YL-monitor-docs"

# 创建归档索引
echo ""
echo "📝 创建归档索引..."

cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Cleanup Archive
# 清理归档目录

**最后更新:** 2026-02-04

本文档包含从主目录清理过来的已完成/废弃的文档。

## 目录结构

```
cleanup-archive/
├── README.md              # 本文档
├── tasks/                 # 已完成任务文档
│   ├── *-task.md         # 任务文档
│   ├── task-*-deploy-*.md # 部署跟踪
│   └── *-execution-report.md # 执行报告
│
└── project/               # 已归档模块文档
    ├── api-map-docs/     # API映射文档
    ├── AR-backend-docs/  # 后端文档
    ├── scripts-docs/     # 脚本文档
    ├── user-docs/        # 用户文档
    └── YL-monitor-docs/  # 监控文档
```

## 已清理内容

### 任务文档 (12个)
- ✅ other-001-task.md (基础设施搭建)
- ✅ rules-003-task.md (前端交互规范)
- ✅ AR-backend-004-task.md (性能监控)
- ✅ scripts-006-task.md (CI/CD集成)
- ✅ user-003-task.md (GUI组件)
- ✅ api-map-005-task.md (接口安全)
- ✅ other-004-task.md (文档体系)
- ✅ rules-002-task.md (规则重构)

### 部署跟踪 (4个)
- ✅ task-001-deploy-infra.md
- ✅ task-002-deploy-rules.md
- ✅ task-003-deploy-ar-backend-performance.md
- ✅ task-004-deploy-scripts-cicd.md

### 执行报告 (8个)
- ✅ 所有任务的执行报告

### 模块文档 (5个)
- ✅ api-map-docs/
- ✅ AR-backend-docs/
- ✅ scripts-docs/
- ✅ user-docs/
- ✅ YL-monitor-docs/

## 保留文档

### tasks/ 目录保留
- README.md (任务文档中心)
- TASK_EXECUTION_SUMMARY.md (执行总览)
- IMPLEMENTATION_SUMMARY.md (实施总结)
- TODO.md (进度跟踪)

### project/ 目录保留
- README.md (模块文档说明)
- optimization-analysis.md (优化分析)
- rules-docs/ (规则文档)

---

**版本:** 1.0.0  
**最后更新:** 2026-02-04
EOF

echo ""
echo "=========================================="
echo "✅ 清理完成!"
echo "=========================================="
echo ""
echo "已移动文档到: $ARCHIVE_DIR"
echo ""
echo "保留的文档:"
echo "  tasks/: README.md, TASK_EXECUTION_SUMMARY.md,"
echo "          IMPLEMENTATION_SUMMARY.md, TODO.md"
echo "  project/: README.md, optimization-analysis.md,"
echo "            rules-docs/"
