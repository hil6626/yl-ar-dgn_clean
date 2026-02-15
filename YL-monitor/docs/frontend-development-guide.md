# 前端开发指南

## 概述

本文档补充说明 YL-Monitor 前端开发规范，包括样式规范、检测工具和测试方法。

## 样式规范

### 命名规范

所有页面必须使用统一的命名格式：

```css
/* 页面容器 */
.platform-page
.dashboard-page
.ar-page
.dag-page
.scripts-page
.api-doc-page

/* 页面头部 */
.platform-header
.dashboard-header
.ar-header
.dag-header
.scripts-header
.api-doc-header
```

### 间距系统

标准间距变量：

```css
:root {
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --spacing-xxl: 40px;
}
```

### 响应式断点

```css
/* 移动端 */
@media (max-width: 480px) { }

/* 平板/小屏幕 */
@media (max-width: 768px) { }

/* 中等屏幕 */
@media (max-width: 1024px) { }
```

## 检测工具

### CSS合规性检查

运行CSS合规性检测脚本：

```bash
# 检查CSS是否符合规范
python3 scripts/tools/check_css_compliance.py
```

检查内容包括：
- 页面命名规范
- 重复的选择器
- 未使用的CSS规则
- CSS变量使用情况
- 响应式断点一致性
- 间距一致性

### 检查结果

脚本会生成详细报告：
- ❌ 错误：必须修复的问题
- ⚠️ 警告：建议优化的问题
- ℹ️ 建议：可选的改进建议

报告保存位置：`logs/css_compliance_report.txt`

## 视觉回归测试

### 安装依赖

```bash
cd tests/visual-regression
npm install
npm run install:browsers
```

### 生成基准截图

```bash
# 首次运行或有意修改UI时
npm run test:baseline
```

### 运行对比测试

```bash
# 检查是否有意外的视觉变化
npm run test
```

### 查看报告

```bash
npm run test:report
```

### 测试覆盖

- **桌面端** (1920x1080) - 完整布局
- **平板端** (1024x768) - 中等屏幕适配
- **移动端** (375x667) - 小屏幕适配
- **深色模式** - 主题切换测试

## 开发工作流

### 1. 修改样式前

```bash
# 运行合规性检查，确保当前状态良好
python3 scripts/tools/check_css_compliance.py
```

### 2. 修改样式

遵循规范文档 `docs/frontend-style-guide.md`

### 3. 修改后验证

```bash
# 1. 检查合规性
python3 scripts/tools/check_css_compliance.py

# 2. 运行视觉回归测试
cd tests/visual-regression
npm run test

# 3. 如有意修改，更新基准
npm run test:baseline
```

## 持续集成

建议在CI/CD流程中添加：

```yaml
# GitHub Actions 示例
- name: CSS Compliance Check
  run: python3 scripts/tools/check_css_compliance.py

- name: Visual Regression Test
  run: |
    cd tests/visual-regression
    npm install
    npm run test
```

## 相关文档

- `docs/frontend-style-guide.md` - 完整样式规范
- `tests/visual-regression/README.md` - 视觉测试详细说明
- `部署/Tasks/TASK-083-PAGE-RENDERING-ALIGNMENT.md` - 修复记录

---

**最后更新**：2026年2月8日
**版本**：1.0.1  
**维护者**：AI Assistant
