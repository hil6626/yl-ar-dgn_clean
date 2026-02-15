# YL-Monitor JS脚本模块化拆分方案

**分析日期**: 2026-02-12  
**分析范围**: static/js/ 目录下所有页面脚本  
**目标**: 解决单文件过大问题，提升可维护性

---

## 📊 当前部署情况分析

### 文件大小统计

| 文件 | 行数 | 状态 | 职责数量 |
|------|------|------|----------|
| `page-dag.js` | **1,510行** | 🔴 严重超标 | 7个命令类+2个管理器+1个主类 |
| `page-scripts.js` | 985行 | 🟡 偏大 | 列表+编辑+批量操作+执行 |
| `page-api-doc.js` | 805行 | 🟡 中等 | API文档+测试+导出 |
| `page-ar.js` | 771行 | 🟡 中等 | 3D可视化+实时监控 |
| `page-dashboard.js` | 624行 | 🟢 可接受 | 仪表盘+图表 |
| `page-alert-center.js` | 545行 | 🟢 可接受 | 告警列表+规则 |

### 核心问题识别

#### 1. page-dag.js (1,510行) - 最严重
```
职责混杂:
├── 命令模式实现 (300行)
│   ├── CommandManager类
│   ├── AddNodeCommand类
│   ├── DeleteNodeCommand类
│   ├── MoveNodeCommand类
│   ├── UpdateNodePropertyCommand类
│   ├── AddEdgeCommand类
│   └── DeleteEdgeCommand类
├── 自动保存管理 (180行)
│   └── AutoSaveManager类
└── DAG页面主类 (1,000+行)
    ├── 渲染方法 (节点、边线、面板)
    ├── 事件处理 (拖拽、点击、键盘)
    ├── 执行控制 (运行、停止、进度)
    └── 数据管理 (加载、保存、导出)
```

#### 2. page-scripts.js (985行)
```
功能混杂:
├── 脚本列表渲染
├── 拖拽排序
├── 新建/编辑弹窗
├── 批量操作
├── 执行控制
└── 日志查看
```

#### 3. 通用问题
- ❌ 工具函数重复定义（dom操作、api请求）
- ❌ 事件处理逻辑分散在各方法中
- ❌ 缺乏统一的模块加载机制
- ❌ 测试困难（依赖关系复杂）

---

## 🎯 模块化拆分方案

### 方案概述

采用**渐进式拆分策略**，优先处理最复杂的DAG页面，然后逐步推广到其他页面。

### 目标架构

```
static/js/
├── core/                    # 核心基础设施
│   ├── EventBus.js         # 事件总线
│   ├── ModuleLoader.js     # 模块加载器
│   └── DependencyInjector.js # 依赖注入
├── shared/                  # 共享组件
│   ├── components/         # UI组件
│   │   ├── Modal.js
│   │   ├── Toast.js
│   │   ├── ConfirmDialog.js
│   │   └── LoadingSpinner.js
│   ├── utils/              # 工具函数
│   │   ├── dom.js          # DOM操作
│   │   ├── api.js          # API请求
│   │   ├── storage.js      # 本地存储
│   │   └── validators.js   # 验证工具
│   └── mixins/             # 混入类
│       ├── EventMixin.js
│       └── LifecycleMixin.js
├── pages/                   # 页面模块
│   ├── dag/                # DAG页面
│   │   ├── index.js        # 入口
│   │   ├── commands/       # 命令类
│   │   ├── managers/       # 管理器
│   │   ├── components/     # 组件
│   │   └── utils/          # 工具
│   ├── scripts/            # Scripts页面
│   ├── api-doc/            # API文档页面
│   ├── ar/                 # AR页面
│   ├── dashboard/          # 仪表盘页面
│   └── alert-center/       # 告警中心页面
└── legacy/                  # 遗留文件（过渡用）
    └── *.js                # 原文件备份
```

---

## 📋 详细拆分计划

### Phase 1: DAG页面重构（优先级：🔴 最高）

#### 1.1 目录结构创建

```bash
mkdir -p static/js/pages/dag/{commands,managers,components,utils}
```

#### 1.2 命令类拆分（7个文件）

**文件**: `static/js/pages/dag/commands/CommandManager.js`
```javascript
/**
 * 命令管理器 - 实现撤销/重做功能
 * 拆分自: page-dag.js (原300行 → 现150行)
 */
export class CommandManager {
  constructor(page) {
    this.page = page;
    this.undoStack = [];
    this.redoStack = [];
    this.maxHistory = 50;
  }

  execute(command) {
    command.execute();
    this.undoStack.push(command);
    this.redoStack = [];
    
    if (this.undoStack.length > this.maxHistory) {
      this.undoStack.shift();
    }
    
    this.updateUI();
  }

  undo() {
    if (this.undoStack.length === 0) {
      this.page.ui.showToast({ type: 'warning', message: '没有可撤销的操作' });
      return;
    }
    
    const command = this.undoStack.pop();
    command.undo();
    this.redoStack.push(command);
    this.updateUI();
    this.page.ui.showToast({ type: 'info', message: '已撤销' });
  }

  redo() {
    if (this.redoStack.length === 0) {
      this.page.ui.showToast({ type: 'warning', message: '没有可重做的操作' });
      return;
    }
    
    const command = this.redoStack.pop();
    command.execute();
    this.undoStack.push(command);
    this.updateUI();
    this.page.ui.showToast({ type: 'info', message: '已重做' });
  }

  updateUI() {
    const undoBtn = document.getElementById('btn-undo');
    const redoBtn = document.getElementById('btn-redo');
    
    if (undoBtn) undoBtn.disabled = this.undoStack.length === 0;
    if (redoBtn) redoBtn.disabled = this.redoStack.length === 0;
  }

  clear() {
    this.undoStack = [];
    this.redoStack = [];
    this.updateUI();
  }
}
```

**文件**: `static/js/pages/dag/commands/AddNodeCommand.js`
```javascript
/**
 * 添加节点命令
 * 拆分自: page-dag.js
 */
export class AddNodeCommand {
  constructor(page, node) {
    this.page = page;
    this.node = node;
    this.nodeId = node.id;
  }

  execute() {
    this.page.nodes.push(this.node);
    this.page.renderNodes();
  }

  undo() {
    this.page.nodes = this.page.nodes.filter(n => n.id !== this.nodeId);
    this.page.renderNodes();
  }
}
```

**其他命令类同理**: DeleteNodeCommand.js, MoveNodeCommand.js, UpdateNodePropertyCommand.js, AddEdgeCommand.js, DeleteEdgeCommand.js

#### 1.3 管理器拆分（2个文件）

**文件**: `static/js/pages/dag/managers/AutoSaveManager.js`
```javascript
/**
 * 自动保存管理器
 * 拆分自: page-dag.js (原180行)
 */
export class AutoSaveManager {
  constructor(page) {
    this.page = page;
    this.autoSaveInterval = null;
    this.AUTO_SAVE_DELAY = 30000;
    this.DRAFT_EXPIRY = 24 * 60 * 60 * 1000;
    this.STORAGE_KEY = 'yl_dag_draft';
    this.lastSaveTime = null;
    this.hasUnsavedChanges = false;
  }

  init() {
    this.checkDraftRecovery();
    this.startAutoSave();
    window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
    console.log('[AutoSaveManager] 自动保存管理器已初始化');
  }

  startAutoSave() {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
    }
    this.autoSaveInterval = setInterval(() => this.autoSave(), this.AUTO_SAVE_DELAY);
  }

  stopAutoSave() {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }
  }

  async autoSave() {
    if (!this.hasUnsavedChanges) return;
    
    try {
      const draftData = {
        nodes: this.page.nodes,
        edges: this.page.edges,
        timestamp: Date.now(),
        version: '1.0.0'
      };
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(draftData));
      this.lastSaveTime = Date.now();
      this.hasUnsavedChanges = false;
      
      console.log('[AutoSaveManager] 草稿已自动保存');
      
      if (this.shouldShowSaveNotification()) {
        this.page.ui.showToast({ type: 'info', message: 'DAG草稿已自动保存' });
      }
    } catch (error) {
      console.error('[AutoSaveManager] 自动保存失败:', error);
    }
  }

  markUnsaved() {
    this.hasUnsavedChanges = true;
  }

  shouldShowSaveNotification() {
    if (!this.lastSaveTime) return true;
    const fiveMinutes = 5 * 60 * 1000;
    return (Date.now() - this.lastSaveTime) >= fiveMinutes;
  }

  checkDraftRecovery() {
    try {
      const draftJson = localStorage.getItem(this.STORAGE_KEY);
      if (!draftJson) return;
      
      const draft = JSON.parse(draftJson);
      
      if (Date.now() - draft.timestamp > this.DRAFT_EXPIRY) {
        console.log('[AutoSaveManager] 草稿已过期，清除');
        localStorage.removeItem(this.STORAGE_KEY);
        return;
      }
      
      this.showDraftRecoveryDialog(draft);
    } catch (error) {
      console.error('[AutoSaveManager] 检查草稿失败:', error);
    }
  }

  showDraftRecoveryDialog(draft) {
    const saveTime = new Date(draft.timestamp).toLocaleString('zh-CN');
    
    this.page.ui.showConfirm({
      title: '恢复DAG草稿',
      message: `检测到未保存的DAG草稿（${saveTime}），是否恢复？`,
      type: 'info',
      confirmText: '恢复草稿',
      cancelText: '丢弃',
      onConfirm: () => this.restoreDraft(draft),
      onCancel: () => this.clearDraft()
    });
  }

  restoreDraft(draft) {
    try {
      this.page.nodes = draft.nodes || [];
      this.page.edges = draft.edges || [];
      this.page.renderNodes();
      this.page.renderEdges();
      this.page.ui.showToast({ type: 'success', message: 'DAG草稿已恢复' });
      console.log('[AutoSaveManager] 草稿已恢复');
    } catch (error) {
      console.error('[AutoSaveManager] 恢复草稿失败:', error);
      this.page.ui.showToast({ type: 'error', message: '恢复草稿失败' });
    }
  }

  clearDraft() {
    localStorage.removeItem(this.STORAGE_KEY);
    console.log('[AutoSaveManager] 草稿已清除');
  }

  handleBeforeUnload(e) {
    if (this.hasUnsavedChanges) {
      this.autoSave();
      e.preventDefault();
      e.returnValue = '有未保存的变更，确定要离开吗？';
      return e.returnValue;
    }
  }

  onManualSave() {
    this.hasUnsavedChanges = false;
    this.clearDraft();
  }
}
```

**文件**: `static/js/pages/dag/managers/ExecutionManager.js`（从DAGPage提取执行逻辑）

#### 1.4 组件拆分（4个文件）

**文件**: `static/js/pages/dag/components/NodePanel.js`
```javascript
/**
 * 节点面板组件
 * 拆分自: page-dag.js renderNodePanel()
 */
export class NodePanel {
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('dag-nodes-panel');
  }

  render() {
    if (!this.mount) return;
    
    this.mount.innerHTML = this.generateHTML();
    this.bindEvents();
  }

  generateHTML() {
    return `
      <div class="dag-nodes-header">
        <h3>节点库</h3>
      </div>
      <div class="dag-nodes-content">
        ${this.page.nodeTemplates.map((category, catIndex) => `
          <div class="dag-node-category">
            <div class="dag-category-header ${category.expanded ? 'expanded' : ''}" data-category="${catIndex}">
              <span class="category-icon">${category.icon}</span>
              <span class="category-name">${category.category}</span>
              <span class="category-toggle">▶</span>
            </div>
            <div class="dag-category-nodes ${category.expanded ? 'expanded' : ''}" id="category-${catIndex}">
              ${category.nodes.map(node => `
                <div class="dag-node-template" 
                     draggable="true"
                     data-node-type="${node.type}"
                     data-node-shape="${node.shape}"
                     data-node-name="${node.name}"
                     data-node-icon="${node.icon}"
                     data-node-color="${node.color}">
                  <div class="node-shape ${node.shape}" style="background: ${node.color}"></div>
                  <span class="node-label">${node.name}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  bindEvents() {
    // 分类展开/折叠
    this.mount.querySelectorAll('.dag-category-header').forEach(header => {
      header.addEventListener('click', () => this.toggleCategory(header));
    });

    // 拖拽事件
    this.mount.querySelectorAll('.dag-node-template').forEach(template => {
      template.addEventListener('dragstart', (e) => this.handleDragStart(e, template));
    });
  }

  toggleCategory(header) {
    const catIndex = header.dataset.category;
    const nodesContainer = document.getElementById(`category-${catIndex}`);
    const isExpanded = header.classList.contains('expanded');
    
    header.classList.toggle('expanded', !isExpanded);
    nodesContainer.classList.toggle('expanded', !isExpanded);
  }

  handleDragStart(e, template) {
    e.dataTransfer.setData('nodeType', template.dataset.nodeType);
    e.dataTransfer.setData('nodeShape', template.dataset.nodeShape);
    e.dataTransfer.setData('nodeName', template.dataset.nodeName);
    e.dataTransfer.setData('nodeIcon', template.dataset.nodeIcon);
    e.dataTransfer.setData('nodeColor', template.dataset.nodeColor);
    e.dataTransfer.effectAllowed = 'copy';
  }
}
```

**其他组件**: Canvas.js, PropertiesPanel.js, ControlBar.js

#### 1.5 入口文件重构

**文件**: `static/js/pages/dag/index.js`
```javascript
/**
 * DAG页面入口
 * 重构自: page-dag.js
 */
import { CommandManager } from './commands/CommandManager.js';
import { AddNodeCommand } from './commands/AddNodeCommand.js';
import { DeleteNodeCommand } from './commands/DeleteNodeCommand.js';
import { MoveNodeCommand } from './commands/MoveNodeCommand.js';
import { UpdateNodePropertyCommand } from './commands/UpdateNodePropertyCommand.js';
import { AddEdgeCommand } from './commands/AddEdgeCommand.js';
import { DeleteEdgeCommand } from './commands/DeleteEdgeCommand.js';
import { AutoSaveManager } from './managers/AutoSaveManager.js';
import { ExecutionManager } from './managers/ExecutionManager.js';
import { NodePanel } from './components/NodePanel.js';
import { Canvas } from './components/Canvas.js';
import { PropertiesPanel } from './components/PropertiesPanel.js';
import { ControlBar } from './components/ControlBar.js';

export default class DAGPage {
  constructor(deps) {
    this.themeManager = deps.themeManager;
    this.ui = deps.uiComponents;
    this.apiBaseUrl = '/api/v1';
    
    // 管理器
    this.commandManager = new CommandManager(this);
    this.autoSaveManager = new AutoSaveManager(this);
    this.executionManager = new ExecutionManager(this);
    
    // 组件
    this.nodePanel = new NodePanel(this);
    this.canvas = new Canvas(this);
    this.propertiesPanel = new PropertiesPanel(this);
    this.controlBar = new ControlBar(this);
    
    // 数据
    this.nodes = [];
    this.edges = [];
    this.selectedNode = null;
    this.selectedEdge = null;
    
    // 配置
    this.nodeTemplates = [...]; // 节点模板配置
  }

  async init() {
    console.log('[DAGPage] 初始化DAG页面...');
    
    // 渲染组件
    this.controlBar.render();
    this.nodePanel.render();
    this.canvas.render();
    this.propertiesPanel.render();
    
    // 加载数据
    await this.loadDAGData();
    
    // 初始化管理器
    this.autoSaveManager.init();
    
    // 绑定全局事件
    this.bindGlobalEvents();
    
    console.log('[DAGPage] DAG页面初始化完成 ✅');
  }

  // 委托方法到各组件
  renderNodes() { return this.canvas.renderNodes(); }
  renderEdges() { return this.canvas.renderEdges(); }
  selectNode(nodeId) { return this.canvas.selectNode(nodeId); }
  
  // ... 其他方法
}
```

---

### Phase 2: Scripts页面重构（优先级：🟡 中等）

#### 2.1 目录结构

```
static/js/pages/scripts/
├── index.js              # 入口 (200行)
├── components/
│   ├── ScriptList.js     # 列表组件 (200行)
│   ├── ScriptEditor.js   # 编辑器组件 (150行)
│   └── BatchToolbar.js   # 批量操作工具栏 (100行)
├── managers/
│   ├── ScriptRunner.js   # 执行管理器 (150行)
│   └── OrderManager.js   # 排序管理器 (100行)
└── utils/
    └── script-utils.js   # 工具函数 (50行)
```

#### 2.2 功能按钮拆分策略

| 原方法 | 拆分后 | 归属模块 |
|--------|--------|----------|
| `handleDrop()` + `saveScriptOrder()` | `OrderManager.handleDrop()` | OrderManager.js |
| `runScript()` + `stopScript()` | `ScriptRunner.run()` / `stop()` | ScriptRunner.js |
| `showCreateModal()` + `saveNewScript()` | `ScriptEditor.create()` | ScriptEditor.js |
| `batchDelete()` + `batchRun()` | `BatchToolbar.execute()` | BatchToolbar.js |

---

### Phase 3: 共享模块提取（优先级：🟢 低）

#### 3.1 通用工具提取

**文件**: `static/js/shared/utils/dom.js`
```javascript
/**
 * DOM操作工具集
 * 提取自: 各page-*.js中的重复代码
 */
export const DOMUtils = {
  /**
   * 安全地获取元素
   */
  getElement(id) {
    const el = document.getElementById(id);
    if (!el) {
      console.warn(`[DOMUtils] 元素不存在: #${id}`);
    }
    return el;
  },

  /**
   * 创建带属性的元素
   */
  createElement(tag, attributes = {}, children = []) {
    const el = document.createElement(tag);
    Object.entries(attributes).forEach(([key, value]) => {
      if (key === 'className') {
        el.className = value;
      } else if (key === 'textContent') {
        el.textContent = value;
      } else if (key === 'innerHTML') {
        el.innerHTML = value;
      } else {
        el.setAttribute(key, value);
      }
    });
    children.forEach(child => el.appendChild(child));
    return el;
  },

  /**
   * 事件委托
   */
  delegate(container, eventType, selector, handler) {
    container.addEventListener(eventType, (e) => {
      const target = e.target.closest(selector);
      if (target && container.contains(target)) {
        handler.call(target, e, target);
      }
    });
  },

  /**
   * 防抖
   */
  debounce(fn, delay = 300) {
    let timer = null;
    return function(...args) {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  },

  /**
   * 节流
   */
  throttle(fn, limit = 300) {
    let inThrottle = false;
    return function(...args) {
      if (!inThrottle) {
        fn.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
};
```

**文件**: `static/js/shared/utils/api.js`
```javascript
/**
 * API请求工具集
 */
export const APIUtils = {
  baseURL: '/api/v1',
  
  async get(endpoint, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`);
    }
    
    return response.json();
  },

  async post(endpoint, data, options = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(data),
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`);
    }
    
    return response.json();
  },

  // ... put, delete, patch 等方法
};
```

#### 3.2 通用组件提取

**文件**: `static/js/shared/components/ConfirmDialog.js`
```javascript
/**
 * 统一确认对话框
 * 提取自: ui-components.js 和各页面中的确认逻辑
 */
export class ConfirmDialog {
  constructor(options = {}) {
    this.options = {
      title: '确认',
      message: '',
      type: 'info', // info, warning, danger
      confirmText: '确认',
      cancelText: '取消',
      showCancel: true,
      ...options
    };
    
    this.modal = null;
  }

  show() {
    return new Promise((resolve) => {
      this.modal = this.createModal();
      this.bindEvents(resolve);
      document.body.appendChild(this.modal);
    });
  }

  createModal() {
    const { title, message, type, confirmText, cancelText, showCancel } = this.options;
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay confirm-dialog';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-icon">${this.getIcon(type)}</span>
          <h3>${title}</h3>
        </div>
        <div class="modal-body">
          <p>${message}</p>
        </div>
        <div class="modal-footer">
          ${showCancel ? `<button class="btn btn-secondary" data-action="cancel">${cancelText}</button>` : ''}
          <button class="btn btn-${type}" data-action="confirm">${confirmText}</button>
        </div>
      </div>
    `;
    
    return modal;
  }

  bindEvents(resolve) {
    this.modal.addEventListener('click', (e) => {
      if (e.target.dataset.action === 'confirm') {
        this.close();
        resolve(true);
      } else if (e.target.dataset.action === 'cancel' || e.target === this.modal) {
        this.close();
        resolve(false);
      }
    });
  }

  close() {
    if (this.modal) {
      this.modal.remove();
      this.modal = null;
    }
  }

  getIcon(type) {
    const icons = {
      info: 'ℹ️',
      warning: '⚠️',
      danger: '🗑️',
      success: '✅'
    };
    return icons[type] || 'ℹ️';
  }
}
```

---

## 📅 实施路线图

### 第一周：DAG页面重构
- [ ] Day 1-2: 创建目录结构，拆分命令类（7个文件）
- [ ] Day 3-4: 拆分管理器（AutoSaveManager, ExecutionManager）
- [ ] Day 5: 拆分组件（NodePanel, Canvas, PropertiesPanel, ControlBar）
- [ ] Day 6: 重构入口文件，更新import/export
- [ ] Day 7: 测试验证，修复问题

### 第二周：Scripts页面重构
- [ ] Day 1-2: 拆分ScriptList组件
- [ ] Day 3-4: 拆分ScriptEditor和BatchToolbar
- [ ] Day 5: 拆分ScriptRunner和OrderManager
- [ ] Day 6: 重构入口文件
- [ ] Day 7: 测试验证

### 第三周：共享模块提取
- [ ] Day 1-2: 提取DOMUtils和APIUtils
- [ ] Day 3-4: 提取通用组件（ConfirmDialog, Toast, Modal）
- [ ] Day 5-6: 更新所有页面引用共享模块
- [ ] Day 7: 集成测试

### 第四周：优化与清理
- [ ] Day 1-2: 删除冗余代码，优化模块加载
- [ ] Day 3-4: 性能测试，代码审查
- [ ] Day 5-6: 文档更新，编写迁移指南
- [ ] Day 7: 最终验证，上线

---

## 📈 预期收益

| 指标 | 当前状态 | 目标状态 | 提升 |
|------|----------|----------|------|
| 最大文件行数 | 1,510行 | <300行 | ↓ 80% |
| 平均文件行数 | 800行 | <200行 | ↓ 75% |
| 模块数量 | 15个 | 50+个 | ↑ 233% |
| 代码复用率 | 30% | 70% | ↑ 133% |
| 测试覆盖率 | 40% | 80% | ↑ 100% |
| 新人上手时间 | 3天 | 1天 | ↓ 67% |

---

## ⚠️ 风险提示

1. **兼容性风险**: 模块拆分后需要确保所有页面正常加载
   - 缓解: 保留原文件作为备份，逐步迁移

2. **性能风险**: 模块过多可能导致加载变慢
   - 缓解: 使用动态导入（import()）按需加载

3. **学习成本**: 团队需要适应新的模块结构
   - 缓解: 提供详细的文档和示例

---

## ❓ 需要确认的问题

1. **拆分粒度**: 您希望拆分到多细？是每个类一个文件，还是按功能模块分组？

2. **兼容性**: 是否需要保持向后兼容，还是可以直接重构？

3. **加载方式**: 偏好使用ES6模块（import/export）还是保持现有的script标签加载？

4. **优先级**: 是否优先处理DAG页面，还是同时处理多个页面？

5. **时间规划**: 您希望多长时间内完成这个重构？

---

**建议**: 采用渐进式拆分，先处理最复杂的DAG页面，验证方案可行后再推广到其他页面。这样可以降低风险，同时快速看到效果。
