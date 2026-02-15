#!/bin/bash

# YL-monitor 任务文档完整性验证脚本
# 用途：验证所有 14 个任务文档是否已正确创建和完善

echo "=========================================="
echo "  YL-monitor 任务文档完整性验证"
echo "=========================================="
echo ""

DOCS_DIR="/workspaces/yl-ar-dgn/docs/project/YL-monitor-docs"
TOTAL_TASKS=14
CREATED_TASKS=0
VERIFIED_TASKS=0

# 检查目录是否存在
echo "1️⃣  检查文档目录..."
if [ -d "$DOCS_DIR" ]; then
  echo "   ✅ 目录存在: $DOCS_DIR"
else
  echo "   ❌ 目录不存在: $DOCS_DIR"
  exit 1
fi

echo ""
echo "2️⃣  检查任务文档..."

# 检查每个任务文档
for i in $(seq 1 $TOTAL_TASKS); do
  TASK_NUM=$(printf "%03d" $i)
  TASK_FILE="$DOCS_DIR/YL-monitor-$TASK_NUM-task.md"
  
  if [ -f "$TASK_FILE" ]; then
    CREATED_TASKS=$((CREATED_TASKS + 1))
    
    # 检查文件大小
    FILE_SIZE=$(wc -c < "$TASK_FILE")
    FILE_LINES=$(wc -l < "$TASK_FILE")
    
    if [ $FILE_SIZE -gt 5000 ]; then
      VERIFIED_TASKS=$((VERIFIED_TASKS + 1))
      echo "   ✅ YL-monitor-$(printf "%03d" $i): 存在 ($FILE_LINES 行, $FILE_SIZE 字节)"
    else
      echo "   ⚠️  YL-monitor-$(printf "%03d" $i): 存在但可能不完整 ($FILE_LINES 行, $FILE_SIZE 字节)"
    fi
  else
    echo "   ❌ YL-monitor-$(printf "%03d" $i): 缺失"
  fi
done

echo ""
echo "3️⃣  检查核心部分..."

# 检查任务文档是否包含必需部分
SAMPLE_FILE="$DOCS_DIR/YL-monitor-001-task.md"
if [ -f "$SAMPLE_FILE" ]; then
  echo "   检查 YL-monitor-001 的内容完整性..."
  
  REQUIRED_SECTIONS=(
    "任务目标与范围"
    "影响范围"
    "同步修正"
    "部署与验证"
    "异常处理"
    "完成情况总结"
  )
  
  FOUND_SECTIONS=0
  for section in "${REQUIRED_SECTIONS[@]}"; do
    if grep -q "## .*$section" "$SAMPLE_FILE"; then
      echo "     ✅ $section"
      FOUND_SECTIONS=$((FOUND_SECTIONS + 1))
    else
      echo "     ❌ 缺少: $section"
    fi
  done
  
  echo "   核心部分覆盖率: $FOUND_SECTIONS/${#REQUIRED_SECTIONS[@]}"
fi

echo ""
echo "4️⃣  检查附加文档..."

ADDITIONAL_FILES=("TODO.md" "TODO-v2.md" "COMPLETION_REPORT.md")
for file in "${ADDITIONAL_FILES[@]}"; do
  if [ -f "$DOCS_DIR/$file" ]; then
    echo "   ✅ $file"
  else
    echo "   ⚠️  $file (可选)"
  fi
done

echo ""
echo "=========================================="
echo "  验证总结"
echo "=========================================="
echo "已创建任务文档: $CREATED_TASKS / $TOTAL_TASKS"
echo "验证通过的文档: $VERIFIED_TASKS / $TOTAL_TASKS"

if [ $CREATED_TASKS -eq $TOTAL_TASKS ]; then
  echo ""
  echo "✅ 所有 14 个任务文档已成功创建！"
  echo ""
  echo "下一步操作："
  echo "1. 备份原始 TODO.md: cp $DOCS_DIR/TODO.md $DOCS_DIR/TODO-backup.md"
  echo "2. 使用新版 TODO: mv $DOCS_DIR/TODO-v2.md $DOCS_DIR/TODO.md"
  echo "3. 提交到 git: git add $DOCS_DIR/YL-monitor-*-task.md"
  echo ""
else
  echo ""
  echo "⚠️  还有 $((TOTAL_TASKS - CREATED_TASKS)) 个任务文档缺失"
fi

echo ""
echo "详细统计："
printf "%-10s%-15s%-15s\n" "任务" "文件名" "状态"
printf "%-10s%-15s%-15s\n" "----" "--------" "------"

for i in $(seq 1 $TOTAL_TASKS); do
  TASK_NUM=$(printf "%03d" $i)
  TASK_FILE="$DOCS_DIR/YL-monitor-$TASK_NUM-task.md"
  
  if [ -f "$TASK_FILE" ]; then
    FILE_LINES=$(wc -l < "$TASK_FILE")
    if [ $FILE_LINES -gt 150 ]; then
      STATUS="✅ 完整"
    else
      STATUS="⚠️  部分"
    fi
  else
    STATUS="❌ 缺失"
  fi
  
  printf "YL-001-$(printf "%02d" $i)%-2s%-15s%-15s\n" "" "YL-monitor-$TASK_NUM-task.md" "$STATUS"
done

echo ""
echo "=========================================="
echo "验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
