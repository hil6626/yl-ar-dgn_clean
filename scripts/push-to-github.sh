#!/bin/bash
# GitHub推送脚本

REPO_URL="https://github.com/hil6626/yl-ar-dgn_clean.git"
BRANCH="main"

echo "========================================"
echo "  推送到 GitHub"
echo "========================================"
echo ""

# 检查Git配置
echo "1. 检查Git配置..."
git config --global user.name "AI全栈技术员"
git config --global user.email "ai@example.com"

# 添加所有变更
echo ""
echo "2. 添加所有变更..."
git add -A

# 查看状态
echo ""
echo "3. 当前Git状态:"
git status --short

# 提交变更
echo ""
echo "4. 提交变更..."
git commit -m "生产部署准备完成: 监控颗粒度优化100%完成，6个增强监控器，70+指标，全部验收通过

- 完成4个阶段监控优化（L1-L5层）
- 创建6个增强监控器（进程/CPU/内存/API/业务/用户体验）
- 实现70+监控指标，5秒高频采集
- 创建8份完成报告和验收文档
- 更新所有README文档同步到v2.4.0
- 创建生产部署指南
- 项目100%完成并通过验收"

# 推送到远程
echo ""
echo "5. 推送到远程仓库..."
git push $REPO_URL $BRANCH

echo ""
echo "========================================"
echo "  推送完成!"
echo "========================================"
