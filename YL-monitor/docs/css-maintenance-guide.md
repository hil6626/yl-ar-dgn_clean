# YL-Monitor CSS 维护指南

## 📋 概述

本文档提供CSS合规性检查和维护的完整指南，确保项目在本地部署环境下也能保持样式一致性。

## ✅ 当前状态

- **CSS合规性**: ✅ 100% 通过（0错误，0警告）
- **未使用选择器建议**: 275个（可通过清理工具处理）
- **本地部署支持**: ✅ 已配置

## 🔧 维护工具

### 1. CSS合规性检查
```bash
# 运行完整检查
python3 scripts/tools/check_css_compliance.py
```

### 2. 未使用选择器分析
```bash
# 分析未使用的CSS（预览模式）
python3 scripts/tools/perfect_css_cleanup.py

# 实际执行清理（带备份）
python3 scripts/tools/perfect_css_cleanup.py --apply
```

### 3. 本地维护脚本
```bash
# 运行完整本地维护
bash scripts/tools/local_css_maintenance.sh

# 或定期自动检查
bash scripts/tools/scheduled_css_check.sh
```

## 📊 检查结果解读

### 合规性检查输出
```
错误: 0 | 警告: 0 | 建议: 275
```

- **错误**: 必须修复的问题（如命名不规范）
- **警告**: 建议修复的问题（如硬编码颜色）
- **建议**: 可选优化（如未使用选择器）

### 建议类型说明

| 建议类型 | 说明 | 优先级 |
|---------|------|--------|
| 未使用选择器 | HTML/JS中未引用的CSS类 | 低 |
| 硬编码颜色 | 未使用CSS变量的颜色值 | 中 |
| 命名不规范 | 不符合命名约定的类名 | 高 |

## 🎯 定期维护任务

### 每日检查
```bash
# 快速合规性检查
python3 scripts/tools/check_css_compliance.py
```

### 每周维护
```bash
# 1. 运行合规性检查
python3 scripts/tools/check_css_compliance.py

# 2. 分析未使用选择器
python3 scripts/tools/perfect_css_cleanup.py

# 3. 根据需要执行清理
python3 scripts/tools/perfect_css_cleanup.py --apply
```

### 每月审查
1. 审查CSS变量命名规范
2. 检查主题一致性（深色/浅色模式）
3. 更新文档中的变量列表

## 🛡️ 防护规则

### 命名规范
- 页面容器: `.xxx-page`（如 `.dashboard-page`）
- 页面头部: `.xxx-header`（如 `.dashboard-header`）
- 模块变量: `--模块-属性`（如 `--ar-bg-primary`）

### 禁止事项
- ❌ 禁止在页面CSS中定义 `.xxx-page` 和 `.xxx-header`
- ❌ 禁止使用固定像素值（应使用CSS变量）
- ❌ 禁止重复定义已存在于 style.css 的样式
- ❌ 禁止使用 `!important`（特殊情况除外）

### 推荐做法
- ✅ 使用CSS变量保持样式一致性
- ✅ 使用Flexbox和Grid进行布局
- ✅ 添加适当的过渡动画
- ✅ 编写响应式样式

## 🔍 故障排除

### 问题1: 清理工具误删了使用的选择器
**解决方案**: 
1. 从备份恢复: `cp file.css.backup file.css`
2. 更新工具的白名单（在脚本中添加通用类名）

### 问题2: 合规性检查报告过多建议
**解决方案**:
- 建议只是提示，不影响功能
- 定期运行清理工具减少建议数量
- 关注错误和警告，建议可延后处理

### 问题3: 本地部署无法运行检查
**解决方案**:
- 确保Python 3.6+已安装
- 直接运行: `python3 scripts/tools/check_css_compliance.py`
- 无需GitHub仓库或CI/CD环境

## 📈 优化建议

### 性能优化
1. **清理未使用CSS**: 定期运行清理工具
2. **压缩CSS**: 生产环境启用CSS压缩
3. **按需加载**: 考虑按页面懒加载CSS

### 可维护性优化
1. **文档同步**: 添加新变量时更新本文档
2. **代码审查**: 提交前运行合规性检查
3. **自动化**: 设置定时任务自动检查

## 📝 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2025年1月 | 初始版本，建立维护流程 |
| 1.0.1 | 2026-02-08 | 同步版本号，更新时间戳 |

---

**最后更新**：2026年2月8日

**注意**: 所有CSS修改后请运行合规性检查确保符合规范。
