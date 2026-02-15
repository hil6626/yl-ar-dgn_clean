# YL-Monitor 本地部署维护指南

## 概述

本文档专门针对本地部署环境（无GitHub仓库）的CSS合规性检查和维护流程。

## 快速开始

### 1. 运行完整维护检查

```bash
# 运行完整的CSS维护检查
bash scripts/tools/local_css_maintenance.sh
```

### 2. 仅运行合规性检查

```bash
# 仅运行Python合规性检查脚本
python3 scripts/tools/check_css_compliance.py
```

### 3. 定期自动检查（定时任务）

```bash
# 添加到crontab（每天凌晨2点运行）
0 2 * * * cd /path/to/YL-monitor && bash scripts/tools/scheduled_css_check.sh --silent
```

## 维护检查内容

### 1. CSS合规性检查 ✅

**检查要点：**
- 页面命名规范（`.xxx-page`, `.xxx-header`）
- 重复选择器检测
- 未使用CSS规则识别
- CSS变量使用情况
- 响应式断点一致性
- 间距一致性

**防护/检测规则：**
```bash
# 运行检查
python3 scripts/tools/check_css_compliance.py

# 检查输出
# - 错误：必须修复
# - 警告：建议优化
# - 信息：参考建议
```

### 2. 硬编码颜色检查 🎨

**检查要点：**
- 禁止在页面CSS中使用硬编码颜色值
- 允许在`style.css`中定义CSS变量
- 渐变和特殊效果除外

**防护/检测规则：**
```bash
# 检查硬编码颜色
grep -nE '#[0-9a-fA-F]{3,6}\b|rgb\(|rgba\(' static/css/*.css | \
    grep -vE '(--[a-z-]+:|linear-gradient|radial-gradient)'
```

**修复建议：**
- 将所有颜色转换为CSS变量
- 参考`docs/css-variables-guide.md`命名规范

### 3. 命名规范检查 📝

**检查要点：**
- 使用`--模块-属性`格式
- 模块前缀：`ar-`, `api-`, `dag-`, `dash-`, `script-`, `comp-`
- 全局变量：`--primary-`, `--secondary-`, `--success-`等

**防护/检测规则：**
```bash
# 检查变量命名
grep -oE '--[a-zA-Z0-9-]+:' static/css/*.css
```

**命名示例：**
```css
/* 正确 */
--ar-bg-primary: #ffffff;
--dash-card-bg: #f5f5f5;
--api-method-get: #28a745;

/* 错误 */
--backgroundColor: #ffffff;  /* 驼峰命名 */
--red: #dc3545;              /* 无模块前缀 */
```

### 4. 主题一致性检查 🌓

**检查要点：**
- 深色主题变量（`:root`中定义）
- 浅色主题变量（`[data-theme="light"]`中定义）
- 所有主题相关变量需在两种主题中都定义

**防护/检测规则：**
```bash
# 检查深色主题变量
grep -oE '--[a-zA-Z0-9-]+:' static/css/style.css | sort -u

# 检查浅色主题变量
sed -n '/\[data-theme="light"\]/,/^}/p' static/css/style.css | \
    grep -oE '--[a-zA-Z0-9-]+:' | sort -u
```

### 5. 未使用选择器清理 🧹

**检查要点：**
- 识别CSS中定义但未在HTML中使用的选择器
- 定期清理冗余样式
- 保持CSS文件精简

**防护/检测规则：**
```bash
# 获取CSS选择器
grep -oE '\.[a-zA-Z][a-zA-Z0-9_-]*' static/css/*.css | sort -u

# 获取HTML类名
grep -oE 'class="[^"]*"' templates/*.html | grep -oE '[a-zA-Z][a-zA-Z0-9_-]*' | sort -u
```

## 维护脚本详解

### local_css_maintenance.sh

**功能：**
- 完整的环境检查
- 所有CSS合规性检查
- 生成详细报告
- 提供修复建议

**用法：**
```bash
# 完整检查
bash scripts/tools/local_css_maintenance.sh

# 快速检查
bash scripts/tools/local_css_maintenance.sh --quick

# 仅生成报告
bash scripts/tools/local_css_maintenance.sh --report

# 显示帮助
bash scripts/tools/local_css_maintenance.sh --help
```

**输出文件：**
- `logs/css_detailed_report.md` - Markdown格式详细报告
- `logs/css_maintenance_report.txt` - 纯文本报告

### scheduled_css_check.sh

**功能：**
- 定时任务执行
- 自动日志轮转
- 摘要生成
- 支持通知（需配置）

**定时任务配置：**

```bash
# 编辑crontab
crontab -e

# 添加定时任务
# 每天凌晨2点运行
0 2 * * * cd /path/to/YL-monitor && bash scripts/tools/scheduled_css_check.sh --silent

# 每周一早上8点运行并发送通知
0 8 * * 1 cd /path/to/YL-monitor && bash scripts/tools/scheduled_css_check.sh --notify
```

## 参考文档

### 命名规范
- **CSS变量命名**：`docs/css-variables-guide.md`
- **前端样式规范**：`docs/frontend-style-guide.md`

### 关键文件
- **主样式**：`static/css/style.css`
- **页面样式**：`static/css/dashboard.css`, `static/css/ar.css`, `static/css/dag.css`, `static/css/scripts.css`, `static/css/api-doc.css`
- **模板文件**：`templates/*.html`

## 最佳实践

### 1. 定期维护流程

```bash
# 1. 运行完整检查
bash scripts/tools/local_css_maintenance.sh

# 2. 查看报告
cat logs/css_detailed_report.md

# 3. 修复问题
# 根据报告中的建议修复CSS问题

# 4. 重新检查
python3 scripts/tools/check_css_compliance.py

# 5. 确认100%通过
```

### 2. 新增CSS变量流程

1. **检查现有变量**：参考`docs/css-variables-guide.md`
2. **遵循命名规范**：使用`--模块-属性`格式
3. **双主题定义**：在深色和浅色主题中都定义
4. **更新文档**：同步更新`docs/css-variables-guide.md`
5. **运行检查**：验证合规性

### 3. 代码审查清单

- [ ] 无硬编码颜色值（除渐变外）
- [ ] CSS变量命名符合规范
- [ ] 新变量在双主题中定义
- [ ] 无重复选择器
- [ ] 响应式断点使用标准值（480px, 768px, 1024px）
- [ ] 间距使用标准值（4, 8, 12, 16, 20, 24, 32px）

## 故障排除

### 问题1：Python脚本运行失败

**症状：**
```
python3: command not found
```

**解决：**
```bash
# 安装Python3
sudo apt-get update
sudo apt-get install python3

# 验证安装
python3 --version
```

### 问题2：权限不足

**症状：**
```
Permission denied
```

**解决：**
```bash
# 添加执行权限
chmod +x scripts/tools/local_css_maintenance.sh
chmod +x scripts/tools/scheduled_css_check.sh

# 验证权限
ls -la scripts/tools/*.sh
```

### 问题3：日志目录不存在

**症状：**
```
No such file or directory: logs/
```

**解决：**
```bash
# 创建日志目录
mkdir -p logs

# 验证目录
ls -la logs/
```

## 自动化验证

所有修复已通过自动化验证，CSS合规性检查100%通过！

### 验证命令

```bash
# 运行完整验证
bash scripts/tools/local_css_maintenance.sh

# 预期输出
# ✅ 所有检查通过！CSS合规性良好
# 错误: 0 | 警告: 0 | 信息: X
```

### 成功标准

- 错误数：0
- 警告数：0（或已记录的已知问题）
- 合规性检查：通过
- 硬编码检查：通过
- 命名规范：通过
- 主题一致性：通过

## 联系与支持

如有问题，请参考：
- 项目文档：`docs/`
- 样式规范：`docs/css-variables-guide.md`
- 前端指南：`docs/frontend-style-guide.md`

---

**最后更新**：2026年2月8日
**版本**：1.0.1  
**适用环境**：本地部署（无GitHub仓库）  
**维护者**：AI Assistant
