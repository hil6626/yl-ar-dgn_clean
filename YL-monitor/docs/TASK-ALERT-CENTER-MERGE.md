# 告警中心合并实施任务跟踪

**任务ID:** ALERT-CENTER-MERGE-001  
**开始时间:** 2026-02-11  
**预计完成:** 2天  
**状态:** 进行中

---

## 一、合并范围

### 源页面（4个 → 合并）
1. `templates/alerts.html` - 告警列表
2. `templates/alert_rules.html` - 规则管理
3. `templates/alert_analytics.html` - 统计分析
4. `templates/intelligent_alert.html` - 智能告警

### 目标页面（1个）
- `templates/alert_center.html` - 统一告警中心

---

## 二、关联文件清单

### JS文件（4个 → 1个）
| 原文件 | 功能模块 | 合并方式 |
|--------|----------|----------|
| `page-alerts.js` | 告警列表 | 提取为模块 |
| `alert-rules-manager.js` | 规则管理 | 提取为模块 |
| `alert-analytics.js` | 统计分析 | 提取为模块 |
| `intelligent-alert.js` | 智能告警 | 提取为模块 |
| **新文件** | `alert-center.js` | 主控制器 |
| **新文件** | `modules/alerts/*.js` | 4个子模块 |

### CSS文件（4个 → 1个）
| 原文件 | 合并方式 |
|--------|----------|
| `alerts.css` | 内容整合 |
| `alert-rules.css` | 内容整合 |
| `alert-analytics.css` | 内容整合 |
| `intelligent-alert.css` | 内容整合 |
| **新文件** | `alert-center.css` |

### Python路由（需同步更新）
- `app/routes/alerts.py` - 添加统一路由
- `app/main.py` - 注册新路由，移除旧路由

### 配置更新
- `config/nodes.yaml` - 更新节点配置
- `config/alert_rules.yaml` - 确保路径一致

### 导航更新
- `templates/base.html` - 更新导航链接
- 所有页面的导航引用

---

## 三、实施步骤

### 阶段1：创建新结构（第1天上午）
- [ ] 1.1 创建 `templates/alert_center.html`
- [ ] 1.2 创建 `static/js/alert-center.js` 主控制器
- [ ] 1.3 创建 `static/js/modules/alerts/` 目录
- [ ] 1.4 创建 `static/css/alert-center.css`

### 阶段2：提取和重构JS模块（第1天下午）
- [ ] 2.1 从 `page-alerts.js` 提取 `realtime.js` 模块
- [ ] 2.2 从 `alert-rules-manager.js` 提取 `rules.js` 模块
- [ ] 2.3 从 `alert-analytics.js` 提取 `analytics.js` 模块
- [ ] 2.4 从 `intelligent-alert.js` 提取 `intelligent.js` 模块
- [ ] 2.5 整合公共函数到 `alert-center.js`

### 阶段3：整合CSS（第1天下午）
- [ ] 3.1 提取公共样式
- [ ] 3.2 整合标签页样式
- [ ] 3.3 整合统计卡片样式
- [ ] 3.4 整合表格样式

### 阶段4：Python路由更新（第2天上午）
- [ ] 4.1 在 `app/routes/alerts.py` 添加 `/alerts` 路由
- [ ] 4.2 更新 `app/main.py` 注册路由
- [ ] 4.3 添加旧URL重定向（兼容性）

### 阶段5：导航和链接更新（第2天上午）
- [ ] 5.1 更新 `templates/base.html` 导航
- [ ] 5.2 更新所有页面的返回链接
- [ ] 5.3 更新API文档中的链接

### 阶段6：测试验证（第2天下午）
- [ ] 6.1 功能测试：4个标签页切换
- [ ] 6.2 数据测试：告警加载、规则CRUD
- [ ] 6.3 图表测试：统计分析图表渲染
- [ ] 6.4 响应式测试：移动端适配
- [ ] 6.5 性能测试：首屏加载时间

### 阶段7：清理沉积文件（第2天下午）
- [ ] 7.1 删除旧HTML文件（备份后）
- [ ] 7.2 删除旧JS文件
- [ ] 7.3 删除旧CSS文件
- [ ] 7.4 清理缓存和临时文件
- [ ] 7.5 更新版本号

---

## 四、依赖关系图

```
alert_center.html
├── alert-center.js (主控制器)
│   ├── modules/alerts/realtime.js
│   ├── modules/alerts/rules.js
│   ├── modules/alerts/analytics.js
│   └── modules/alerts/intelligent.js
├── alert-center.css (统一样式)
└── API Routes
    ├── GET /api/alerts/realtime
    ├── GET /api/alerts/rules
    ├── GET /api/alerts/analytics
    └── GET /api/alerts/intelligent
```

---

## 五、风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 功能丢失 | 逐函数对比，确保100%迁移 |
| 样式冲突 | 使用BEM命名规范，隔离作用域 |
| 数据不加载 | 保持API端点不变，仅改前端 |
| 用户书签失效 | 旧URL 301重定向到新URL |
| 性能下降 | 懒加载非活动标签页 |

---

## 六、验证清单

### 功能验证
- [ ] 实时告警列表加载正常
- [ ] 告警筛选和搜索正常
- [ ] 告警确认/解决操作正常
- [ ] 规则CRUD操作正常
- [ ] 规则启用/禁用正常
- [ ] 统计分析图表渲染正常
- [ ] 时间范围切换正常
- [ ] 智能告警配置正常

### 兼容性验证
- [ ] 旧 `/alerts` URL 重定向正常
- [ ] 旧 `/alert-rules` URL 重定向正常
- [ ] 旧 `/alert-analytics` URL 重定向正常
- [ ] 旧 `/intelligent-alert` URL 重定向正常

### 性能验证
- [ ] 首屏加载 < 2秒
- [ ] 标签页切换 < 500ms
- [ ] 内存占用无泄漏

---

## 七、完成标准

✅ 所有4个原页面功能在新页面可用  
✅ 所有旧URL有重定向  
✅ 所有沉积文件已删除  
✅ 测试通过率100%  
✅ 性能指标达标  

---

**更新记录：**  
- 2026-02-11: 任务创建，开始实施
