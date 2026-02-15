# YL-Monitor 前端样式规范文档

## 1. 命名规范

### 1.1 页面容器命名
所有页面必须使用统一的命名格式：
```css
/* 正确 */
.platform-page
.dashboard-page
.ar-page
.dag-page
.scripts-page
.api-doc-page

/* 错误 */
.page  /* 缺少后缀 */
.platform  /* 缺少 -page 后缀 */
```

### 1.2 页面头部命名
```css
/* 正确 */
.platform-header
.dashboard-header
.ar-header
.dag-header
.scripts-header
.api-doc-header

/* 错误 */
.page-header  /* 不统一 */
.header  /* 过于笼统 */
```

### 1.3 CSS类名命名规则
- 使用小写字母和连字符（kebab-case）
- 避免使用驼峰命名
- 使用语义化命名，避免无意义的缩写

```css
/* 正确 */
.dashboard-grid
.script-card
.api-endpoint-header

/* 错误 */
.dashboardGrid  /* 驼峰命名 */
.sc  /* 缩写不明确 */
.apiEndpointHeader  /* 驼峰命名 */
```

## 2. 间距系统

### 2.1 标准间距变量
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

### 2.2 页面布局间距规范

| 元素 | 间距值 | 说明 |
|------|--------|------|
| 页面容器padding | 20px | 统一使用20px |
| 页面头部margin-bottom | 20px | 与内容区分隔 |
| 卡片间距 | 16px-20px | 网格布局使用 |
| 组件内部padding | 16px | 卡片、面板等 |
| 按钮组间距 | 8px-12px | 按钮之间 |
| 表单元素间距 | 12px-16px | 表单项之间 |

### 2.3 使用示例
```css
.dashboard-page {
    padding: 20px;  /* 标准页面padding */
}

.dashboard-header {
    margin-bottom: 20px;  /* 标准头部间距 */
}

.dashboard-grid {
    gap: 16px;  /* 标准网格间距 */
}
```

## 3. 响应式标准

### 3.1 断点定义
```css
/* 移动端 */
@media (max-width: 480px) { }

/* 平板/小屏幕 */
@media (max-width: 768px) { }

/* 中等屏幕 */
@media (max-width: 1024px) { }

/* 大屏幕（可选） */
@media (max-width: 1200px) { }
```

### 3.2 响应式布局规范

#### 页面容器响应式
```css
@media (max-width: 768px) {
    .dashboard-page {
        padding: 16px;  /* 移动端减小padding */
    }
    
    .dashboard-header {
        flex-direction: column;  /* 垂直排列 */
        align-items: flex-start;
        gap: 12px;
    }
}
```

#### 网格布局响应式
```css
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: repeat(2, 1fr);  /* 2列 */
        gap: 12px;
    }
}

@media (max-width: 480px) {
    .dashboard-grid {
        grid-template-columns: 1fr;  /* 单列 */
    }
}
```

## 4. 颜色系统

### 4.1 主题颜色变量
```css
:root {
    /* 主色调 */
    --primary-color: #007bff;
    --primary-light: #6bb3ff;
    --primary-dark: #0056b3;
    
    /* 状态色 */
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    
    /* 中性色 */
    --secondary-color: #6c757d;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
}
```

### 4.2 背景色变量
```css
:root {
    --bg-primary: #f5f5f5;    /* 主背景 */
    --bg-secondary: #ffffff; /* 卡片背景 */
    --bg-tertiary: #f0f0f0;  /* 辅助背景 */
}
```

### 4.3 文字颜色变量
```css
:root {
    --text-primary: #333333;   /* 主要文字 */
    --text-secondary: #666666; /* 次要文字 */
    --text-muted: #999999;     /* 辅助文字 */
}
```

## 5. 组件规范

### 5.1 卡片组件
```css
.card {
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: var(--box-shadow);
    border: 1px solid var(--border-color);
}
```

### 5.2 按钮组件
```css
.btn {
    display: inline-block;
    padding: 10px 20px;
    border-radius: var(--border-radius);
    font-size: 14px;
    font-weight: 500;
}

.btn-primary { background-color: var(--primary-color); color: white; }
.btn-secondary { background-color: var(--secondary-color); color: white; }
```

## 6. 文件组织规范

### 6.1 CSS文件结构
```
static/css/
├── style.css          # 基础样式、变量、通用组件
├── dashboard.css      # 仪表盘页面特有样式
├── ar.css            # AR监控页面特有样式
├── dag.css           # DAG页面特有样式
├── scripts.css       # 脚本管理页面特有样式
└── api-doc.css       # API文档页面特有样式
```

### 6.2 样式编写原则
1. **基础样式在 style.css** - 所有页面共享的样式
2. **页面特有样式在独立文件** - 只包含该页面特有的组件和布局
3. **避免重复定义** - 检查是否已在 style.css 中定义
4. **使用CSS变量** - 便于主题切换和维护

## 7. 检测规则

### 7.1 禁止事项
- ❌ 禁止在页面CSS中定义 `.xxx-page` 和 `.xxx-header`
- ❌ 禁止使用固定像素值（应使用CSS变量）
- ❌ 禁止重复定义已存在于 style.css 的样式
- ❌ 禁止使用 `!important`（特殊情况除外）

### 7.2 推荐做法
- ✅ 使用CSS变量保持样式一致性
- ✅ 使用Flexbox和Grid进行布局
- ✅ 添加适当的过渡动画
- ✅ 编写响应式样式

## 8. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2025年 | 初始版本，建立基础规范 |
| 1.0.1 | 2026-02-08 | 同步版本号，更新时间戳 |

---

**最后更新**：2026年2月8日

**注意**: 所有新页面开发必须遵循此规范，现有页面逐步迁移。
