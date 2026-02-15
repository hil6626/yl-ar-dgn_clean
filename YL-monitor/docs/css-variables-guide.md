# YL-Monitor CSS 变量命名规范

## 命名规则

统一使用 `--模块-属性` 格式，确保变量名清晰、可维护。

### 基础结构
```
--[模块前缀]-[属性名]-[状态/变体]
```

### 模块前缀
| 模块 | 前缀 | 示例 |
|------|------|------|
| 全局/主题 | 无 | `--primary-color` |
| AR监控 | `ar-` | `--ar-bg-primary` |
| DAG流水线 | `dag-` | `--dag-node-border` |
| 仪表盘 | `dash-` | `--dash-card-bg` |
| 脚本管理 | `script-` | `--script-status-running` |
| API文档 | `api-` | `--api-method-get` |
| 组件 | `comp-` | `--comp-modal-bg` |

### 属性命名
| 属性类型 | 命名规则 | 示例 |
|----------|----------|------|
| 背景色 | `[模块]-bg-[位置]` | `--ar-bg-primary` |
| 文字色 | `[模块]-text-[层级]` | `--dag-text-secondary` |
| 边框 | `[模块]-border-[位置]` | `--api-border-color` |
| 间距 | `[模块]-spacing-[大小]` | `--dash-spacing-md` |
| 圆角 | `[模块]-radius-[大小]` | `--comp-radius-lg` |
| 阴影 | `[模块]-shadow-[大小]` | `--comp-shadow-md` |

### 状态变体
- 默认状态：无后缀
- 悬停状态：`-hover`
- 激活状态：`-active`
- 禁用状态：`-disabled`
- 深色模式：`-dark`

### 示例
```css
/* AR模块变量 */
--ar-bg-primary: #ffffff;
--ar-bg-secondary: #f5f5f5;
--ar-text-primary: #333333;
--ar-text-muted: #999999;
--ar-border-color: #e0e0e0;
--ar-node-online: #28a745;
--ar-node-offline: #dc3545;

/* DAG模块变量 */
--dag-bg-canvas: #fafafa;
--dag-node-pending: #ffc107;
--dag-node-running: #17a2b8;
--dag-node-completed: #28a745;
--dag-node-failed: #dc3545;

/* AR模块专用变量 */
--ar-status-online-bg: rgba(40, 167, 69, 0.15);
--ar-status-offline-bg: rgba(220, 53, 69, 0.15);
--ar-status-busy-bg: rgba(255, 193, 7, 0.15);
--ar-status-error-bg: rgba(220, 53, 69, 0.15);
--ar-status-rendering-bg: rgba(0, 123, 255, 0.15);
--ar-selected-bg: rgba(0, 123, 255, 0.05);
--ar-node-visual-bg: rgba(0, 123, 255, 0.3);
--ar-viz-gradient-start: #1a1a2e;
--ar-viz-gradient-mid: #16213e;
--ar-viz-gradient-end: #0f3460;
--ar-viz-text: #fff;
--ar-viz-text-muted: #aaa;
--ar-resource-cpu-start: #007bff;
--ar-resource-cpu-end: #00d4ff;
--ar-resource-mem-start: #28a745;
--ar-resource-mem-end: #20c997;
--ar-resource-gpu-start: #ffc107;
--ar-resource-gpu-end: #fd7e14;

/* API文档模块专用变量 */
--api-active-module-bg: rgba(0, 123, 255, 0.1);
--api-method-put-text: #333;
--api-response-bg: #0b1020;
--api-response-text: #e5e7eb;

/* 组件变量 */
--comp-modal-bg: #ffffff;
--comp-modal-overlay: rgba(0, 0, 0, 0.5);
--comp-toast-success: #065f46;
--comp-toast-error: #7f1d1d;
```

## 使用规范

1. **优先使用模块变量**：页面特定样式使用模块变量，通用样式使用全局变量
2. **避免硬编码**：除渐变和特殊效果外，所有颜色值必须使用变量
3. **保持一致性**：相同用途的颜色使用同一变量
4. **文档同步**：添加新变量时同步更新本文档

---

**最后更新**：2025年2月8日  
**版本**：1.0.1  
**维护者**：AI Assistant
