# YL-Monitor 功能按钮优化实施路线图

**制定日期**: 2026-02-12  
**版本**: v1.0  
**目标**: 优化所有页面功能按钮执行逻辑，确保功能完整落实

---

## 🎯 优化总览

| 页面 | 功能按钮数 | P0问题 | P1问题 | P2问题 | 预计工时 |
|------|-----------|--------|--------|--------|----------|
| Dashboard | 5 | 0 | 3 | 1 | 4h |
| API Doc | 8 | 0 | 4 | 1 | 6h |
| **DAG** | **10** | **4** | 3 | 0 | **16h** |
| **Scripts** | **12** | **1** | 5 | 1 | **12h** |
| **Alerts** | **8** | **1** | 3 | 0 | **8h** |
| AR | 6 | 0 | 2 | 2 | 6h |
| **总计** | **49** | **6** | **20** | **5** | **52h** |

---

## 🚨 P0优先级 - 必须立即修复

### 1. DAG页面 - 撤销/重做功能缺失 ⭐⭐⭐

**问题描述**: 
- 撤销/重做按钮存在但无实际功能
- 用户误操作后无法恢复
- 严重影响用户体验

**影响范围**: 
- 所有使用DAG编辑功能的用户
- 可能导致工作丢失

**解决方案**:
```javascript
// 实现命令模式
class CommandManager {
    constructor() {
        this.undoStack = [];
        this.redoStack = [];
    }
    
    execute(command) {
        command.execute();
        this.undoStack.push(command);
        this.redoStack = [];
    }
    
    undo() {
        if (this.undoStack.length === 0) return;
        const command = this.undoStack.pop();
        command.undo();
        this.redoStack.push(command);
    }
    
    redo() {
        if (this.redoStack.length === 0) return;
        const command = this.redoStack.pop();
        command.execute();
        this.undoStack.push(command);
    }
}
```

**实施步骤**:
1. [ ] 创建CommandManager类
2. [ ] 实现AddNodeCommand
3. [ ] 实现DeleteNodeCommand  
4. [ ] 实现MoveNodeCommand
5. [ ] 绑定撤销/重做按钮
6. [ ] 添加单元测试

**预计工时**: 6小时

---

### 2. DAG页面 - 连线编辑功能缺失 ⭐⭐⭐

**问题描述**:
- 无法编辑节点之间的连线
- 只能删除重连，无法修改

**解决方案**:
```javascript
// 添加连线编辑功能
class EdgeEditor {
    constructor(page) {
        this.page = page;
        this.selectedEdge = null;
    }
    
    enableEdgeEditing() {
        // 点击连线选中
        // 拖拽端点重新连接
        // 双击删除连线
    }
}
```

**预计工时**: 4小时

---

### 3. Scripts页面 - 拖拽排序不持久化 ⭐⭐⭐

**问题描述**:
- 拖拽排序后刷新页面恢复原始顺序
- 用户期望排序被保存

**解决方案**:
```javascript
// 保存排序到服务器
async saveScriptOrder(orderedIds) {
    await fetch('/api/v1/scripts/reorder', {
        method: 'POST',
        body: JSON.stringify({ order: orderedIds })
    });
}
```

**预计工时**: 2小时

---

### 4. Alerts页面 - 批量确认功能缺失 ⭐⭐

**问题描述**:
- 只能单个确认告警
- 大量告警时操作繁琐

**解决方案**:
```javascript
// 实现批量确认
async batchAcknowledge(alertIds) {
    for (const id of alertIds) {
        await fetch(`/api/v1/alerts/${id}/acknowledge`, {
            method: 'POST'
        });
    }
}
```

**预计工时**: 3小时

---

### 5. DAG页面 - 删除节点使用原生confirm ⭐⭐

**问题描述**:
- 使用浏览器原生confirm
- 与UI风格不统一
- 无法显示详细信息

**解决方案**:
```javascript
// 使用统一的确认弹窗
this.ui.showConfirm({
    title: '删除节点',
    message: `确定删除 "${node.name}" 吗？`,
    type: 'danger',
    onConfirm: () => this.deleteNode()
});
```

**预计工时**: 1小时

---

## 📋 P1优先级 - 重要功能增强

### Dashboard页面

| 功能 | 优化内容 | 工时 |
|------|----------|------|
| 卡片点击反馈 | 添加缩放动画+加载提示 | 1h |
| 刷新状态提示 | Toast通知+时间戳 | 1h |
| 资源图表交互 | 点击查看详情弹窗 | 2h |

### API Doc页面

| 功能 | 优化内容 | 工时 |
|------|----------|------|
| 复制降级方案 | 三级降级+手动复制弹窗 | 2h |
| 在线测试验证 | 参数验证+JSON格式检查 | 2h |
| 多格式导出 | Markdown/HTML导出 | 2h |
| 请求历史记录 | localStorage存储历史 | 2h |

### DAG页面

| 功能 | 优化内容 | 工时 |
|------|----------|------|
| 自动保存 | localStorage自动保存草稿 | 2h |
| WebSocket实时状态 | 节点状态实时更新 | 3h |
| 草稿恢复 | 页面加载时恢复草稿 | 1h |

### Scripts页面

| 功能 | 优化内容 | 工时 |
|------|----------|------|
| 新建脚本功能 | 创建脚本表单+API | 3h |
| 编辑脚本功能 | 编辑脚本表单+API | 2h |
| 批量操作功能 | 启用/禁用/运行/停止 | 3h |
| 实时日志查看 | WebSocket日志推送 | 3h |
| 执行进度跟踪 | 进度弹窗+WebSocket | 3h |

### Alerts页面

| 功能 | 优化内容 | 工时 |
|------|----------|------|
| 告警详情抽屉 | 侧滑详情面板 | 2h |
| WebSocket重连 | 自动重连机制 | 2h |
| 规则删除确认 | 统一确认弹窗 | 1h |

### AR页面

| 功能 | 优化内容 | 工时 |
|------|----------|------|
| 3D可视化 | Three.js场景渲染 | 4h |
| 实时预览 | WebSocket视频流 | 2h |

---

## 📅 实施计划

### 第一周 - P0优先级修复

**Day 1-2**: DAG页面撤销/重做功能
- 实现CommandManager
- 实现具体命令类
- 绑定按钮事件

**Day 3**: DAG页面连线编辑
- 实现EdgeEditor
- 添加连线交互

**Day 4**: Scripts排序持久化 + Alerts批量确认
- 后端API开发
- 前端集成

**Day 5**: DAG删除确认优化 + 测试
- 统一确认弹窗
- 单元测试

### 第二周 - P1优先级功能

**Day 1-2**: Dashboard + API Doc优化
- 卡片点击反馈
- 复制降级方案
- 在线测试验证

**Day 3-4**: DAG + Scripts增强
- 自动保存
- WebSocket实时状态
- 新建/编辑脚本

**Day 5**: Alerts + AR优化
- 告警详情抽屉
- 3D可视化基础

### 第三周 - 完善和测试

**Day 1-2**: 剩余P1功能
- 多格式导出
- 请求历史
- 批量操作

**Day 3-4**: 集成测试
- 端到端测试
- 性能测试

**Day 5**: 文档和部署
- 更新文档
- 部署上线

---

## ✅ 验收标准

### P0功能验收

- [ ] DAG撤销/重做可以正常使用
- [ ] DAG连线可以编辑和删除
- [ ] Scripts排序刷新后保持不变
- [ ] Alerts可以批量确认告警
- [ ] 所有删除操作有统一确认弹窗

### P1功能验收

- [ ] 所有按钮点击有视觉反馈
- [ ] 复制功能在所有浏览器正常工作
- [ ] 表单提交有验证提示
- [ ] WebSocket连接断开后自动重连
- [ ] 自动保存的草稿可以恢复

---

## 📊 成功指标

| 指标 | 当前值 | 目标值 | 测量方法 |
|------|--------|--------|----------|
| 功能按钮可用率 | 75% | 95% | 功能测试 |
| 用户操作错误率 | 15% | 5% | 用户反馈 |
| 功能完成度 | 60% | 90% | 需求对比 |
| 代码覆盖率 | 40% | 70% | 测试报告 |

---

## 📝 注意事项

1. **向后兼容**: 所有优化需保持向后兼容
2. **渐进增强**: 核心功能优先，增强功能其次
3. **错误处理**: 所有异步操作需有错误处理
4. **性能监控**: 添加性能监控，避免优化导致性能下降
5. **用户反馈**: 收集用户反馈，持续优化

---

**制定人**: AI Assistant  
**审核人**: 待审核  
**批准人**: 待批准
