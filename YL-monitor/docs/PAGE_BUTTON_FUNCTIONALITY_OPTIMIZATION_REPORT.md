# YL-Monitor 页面功能按钮执行逻辑优化报告

**报告日期**: 2026-02-12  
**报告版本**: v1.0  
**分析页面**: 6个核心页面（Dashboard, API Doc, DAG, Scripts, Alerts, AR）

---

## 📋 执行摘要

本报告针对YL-Monitor各页面的功能按钮执行逻辑进行深入分析，识别出**23个功能优化点**，其中**P0优先级8个**，**P1优先级12个**，**P2优先级3个**。

### 关键发现

1. **DAG页面**存在最严重的功能缺失：撤销/重做按钮无实际功能
2. **所有页面**缺乏统一的加载状态反馈机制
3. **实时功能**普遍缺失：仅Alerts页面有基础实时更新
4. **确认机制**不完整：部分删除操作无二次确认

---

## 🎯 各页面详细分析

### 1. Dashboard 仪表盘页面

#### 现有功能按钮清单

| 按钮/功能 | 当前状态 | 问题 | 优化建议 |
|-----------|----------|------|----------|
| 概览卡片点击 | ✅ 已实现 | 无视觉反馈 | 添加点击动画+加载提示 |
| 自动刷新(30s) | ✅ 已实现 | 无更新提示 | 添加Toast+时间戳 |
| 功能矩阵刷新 | ✅ 已实现 | 无加载状态 | 按钮旋转动画 |
| 资源图表 | ⚠️ 静态 | 无交互 | 添加点击查看详情 |

#### 功能执行逻辑优化代码

```javascript
// ===== 优化1: 卡片点击反馈 =====
handleCardClick(cardId) {
    const card = document.querySelector(`[data-card-id="${cardId}"]`);
    
    // 视觉反馈
    card.style.transform = 'scale(0.95)';
    card.style.transition = 'transform 0.15s ease';
    
    // 显示加载提示
    this.ui.showToast({ 
        type: 'info', 
        message: '正在跳转...',
        duration: 800 
    });
    
    setTimeout(() => {
        card.style.transform = 'scale(1)';
        window.location.href = pageMap[cardId];
    }, 200);
}

// ===== 优化2: 数据刷新反馈 =====
async refreshData() {
    // 显示刷新中
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    refreshBtn?.classList.add('refreshing'); // 添加旋转动画类
    
    await Promise.all([
        this.renderOverviewCards(),
        this.loadMonitorData(),
        this.loadResourceData()
    ]);
    
    // 显示更新时间
    const now = new Date().toLocaleTimeString('zh-CN');
    this.ui.showToast({ 
        type: 'success', 
        message: `数据已更新 ${now}`,
        duration: 2000
    });
    
    // 数据更新动画
    document.querySelectorAll('.stat-card').forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('data-updated');
            setTimeout(() => card.classList.remove('data-updated'), 1000);
        }, index * 100); // 级联动画
    });
    
    refreshBtn?.classList.remove('refreshing');
}
```

#### 功能落实检查清单

- [x] 卡片点击跳转
- [x] 自动刷新数据
- [ ] 卡片点击视觉反馈（待实现）
- [ ] 刷新状态提示（待实现）
- [ ] 资源图表交互（待实现）
- [ ] 暂停自动刷新按钮（待实现）

---

### 2. API Doc 文档页面

#### 现有功能按钮清单

| 按钮/功能 | 当前状态 | 问题 | 优化建议 |
|-----------|----------|------|----------|
| 搜索API | ✅ 已实现 | 无高亮 | 添加结果高亮 |
| 复制cURL | ✅ 已实现 | 降级方案不完整 | 完善降级+手动复制弹窗 |
| 在线测试 | ✅ 已实现 | 无参数验证 | 添加表单验证 |
| 导出文档 | ✅ 已实现 | 仅JSON格式 | 添加Markdown/HTML |
| 侧边栏筛选 | ✅ 已实现 | 无动画 | 添加展开/折叠动画 |
| 请求历史 | ❌ 未实现 | - | 添加历史记录面板 |

#### 功能执行逻辑优化代码

```javascript
// ===== 优化1: 增强复制功能（三级降级） =====
async copyToClipboard(text) {
    const showManualCopy = (text) => {
        // 显示手动复制弹窗
        this.ui.renderModal({
            title: '手动复制',
            content: `
                <p>自动复制失败，请手动复制以下内容：</p>
                <textarea readonly style="width:100%;height:100px;">${text}</textarea>
            `,
            buttons: [{ label: '关闭', action: 'close' }]
        });
    };
    
    try {
        // 第一级：现代Clipboard API
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            this.ui.showToast({ type: 'success', message: '已复制到剪贴板' });
            return;
        }
        
        // 第二级：execCommand
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.cssText = 'position:fixed;left:-9999px;opacity:0;';
        document.body.appendChild(textarea);
        textarea.select();
        
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        
        if (success) {
            this.ui.showToast({ type: 'success', message: '已复制到剪贴板' });
        } else {
            throw new Error('execCommand failed');
        }
    } catch (err) {
        // 第三级：手动复制弹窗
        console.warn('复制失败，使用手动复制:', err);
        showManualCopy(text);
    }
}

// ===== 优化2: 在线测试参数验证 =====
async sendTestRequest() {
    const endpoint = this.currentEndpoint;
    const errors = [];
    
    // 验证必填参数
    endpoint.params?.forEach(param => {
        if (param.required) {
            const input = document.getElementById(`param-${param.name}`);
            const value = input?.value.trim();
            
            if (!value) {
                errors.push(`${param.name} 为必填项`);
                input?.classList.add('error');
            } else {
                input?.classList.remove('error');
            }
        }
    });
    
    // 验证JSON格式
    if (endpoint.method !== 'GET') {
        const bodyText = document.getElementById('test-request-body')?.value;
        try {
            JSON.parse(bodyText);
        } catch (e) {
            errors.push('请求体JSON格式错误: ' + e.message);
        }
    }
    
    if (errors.length > 0) {
        this.ui.showToast({ 
            type: 'error', 
            message: errors.join('；'),
            duration: 5000
        });
        return;
    }
    
    // 发送请求...
    this.executeTestRequest();
}

// ===== 优化3: 多格式导出 =====
exportAPIDoc(format = 'json') {
    const formats = {
        json: {
            mime: 'application/json',
            ext: 'json',
            generator: (doc) => JSON.stringify(doc, null, 2)
        },
        markdown: {
            mime: 'text/markdown',
            ext: 'md',
            generator: (doc) => this.generateMarkdown(doc)
        },
        html: {
            mime: 'text/html',
            ext: 'html',
            generator: (doc) => this.generateHTML(doc)
        }
    };
    
    const config = formats[format];
    if (!config) return;
    
    const doc = {
        title: 'YL-Monitor API文档',
        version: 'v1.0.0',
        generatedAt: new Date().toISOString(),
        modules: this.apiData
    };
    
    const content = config.generator(doc);
    const blob = new Blob([content], { type: config.mime });
    
    // 下载文件
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `yl-monitor-api-doc.${config.ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    this.ui.showToast({ 
        type: 'success', 
        message: `已导出为 ${format.toUpperCase()} 格式` 
    });
}

// ===== 优化4: 请求历史记录 =====
class RequestHistory {
    constructor(maxSize = 50) {
        this.maxSize = maxSize;
        this.history = JSON.parse(localStorage.getItem('api-request-history') || '[]');
    }
    
    add(record) {
        record.timestamp = Date.now();
        this.history.unshift(record);
        
        if (this.history.length > this.maxSize) {
            this.history.pop();
        }
        
        localStorage.setItem('api-request-history', JSON.stringify(this.history));
    }
    
    getRecent(count = 10) {
        return this.history.slice(0, count);
    }
    
    clear() {
        this.history = [];
        localStorage.removeItem('api-request-history');
    }
}

// 使用历史记录
async sendTestRequest() {
    // ... 发送请求 ...
    
    // 记录到历史
    this.requestHistory.add({
        endpoint: this.currentEndpoint.path,
        method: this.currentEndpoint.method,
        timestamp: Date.now(),
        success: response.ok
    });
}
```

#### 功能落实检查清单

- [x] 搜索API端点
- [x] 复制cURL命令
- [x] 在线测试API
- [x] 导出JSON文档
- [ ] 复制降级方案完善（待实现）
- [ ] 在线测试参数验证（待实现）
- [ ] Markdown/HTML导出（待实现）
- [ ] 请求历史记录（待实现）
- [ ] API收藏功能（待实现）

---

### 3. DAG 流水线页面 ⭐ P0优先级

#### 现有功能按钮清单

| 按钮/功能 | 当前状态 | 问题 | 优先级 |
|-----------|----------|------|--------|
| 节点拖拽添加 | ✅ 已实现 | - | - |
| 节点位置拖拽 | ✅ 已实现 | 无撤销 | P1 |
| 画布缩放 | ✅ 已实现 | - | - |
| 保存DAG | ✅ 已实现 | 无自动保存 | P1 |
| 导出DAG | ✅ 已实现 | - | - |
| 运行/停止 | ✅ 已实现 | 无实时状态 | P1 |
| 撤销 | ❌ 无功能 | 按钮存在但无效 | **P0** |
| 重做 | ❌ 无功能 | 按钮存在但无效 | **P0** |
| 删除节点 | ⚠️ 有确认 | 使用原生confirm | P1 |
| 连线编辑 | ❌ 未实现 | 无法修改连线 | **P0** |

#### 功能执行逻辑优化代码

```javascript
// ===== 优化1: 撤销/重做功能（命令模式）⭐ P0 =====
class CommandManager {
    constructor(page) {
        this.page = page;
        this.undoStack = [];
        this.redoStack = [];
        this.maxHistory = 50;
    }
    
    execute(command) {
        command.execute();
        this.undoStack.push(command);
        this.redoStack = []; // 清空重做栈
        
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
}

// 具体命令实现
class AddNodeCommand {
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

class DeleteNodeCommand {
    constructor(page, node, edges) {
        this.page = page;
        this.node = node;
        this.removedEdges = edges;
    }
    
    execute() {
        this.page.nodes = this.page.nodes.filter(n => n.id !== this.node.id);
        this.page.edges = this.page.edges.filter(e => 
            !this.removedEdges.includes(e)
        );
        this.page.renderNodes();
        this.page.renderEdges();
    }
    
    undo() {
        this.page.nodes.push(this.node);
        this.page.edges.push(...this.removedEdges);
        this.page.renderNodes();
        this.page.renderEdges();
    }
}

class MoveNodeCommand {
    constructor(page, nodeId, oldPos, newPos) {
        this.page = page;
        this.nodeId = nodeId;
        this.oldPos = oldPos;
        this.newPos = newPos;
    }
    
    execute() {
        const node = this.page.nodes.find(n => n.id === this.nodeId);
        if (node) {
            node.x = this.newPos.x;
            node.y = this.newPos.y;
            this.page.renderNodes();
            this.page.renderEdges();
        }
    }
    
    undo() {
        const node = this.page.nodes.find(n => n.id === this.nodeId);
        if (node) {
            node.x = this.oldPos.x;
            node.y = this.oldPos.y;
            this.page.renderNodes();
            this.page.renderEdges();
        }
    }
}

// 在DAGPage中使用
class DAGPage {
    constructor(deps) {
        this.commandManager = new CommandManager(this);
    }
    
    // 添加节点
    handleDrop(e) {
        // ... 创建节点 ...
        const command = new AddNodeCommand(this, newNode);
        this.commandManager.execute(command);
    }
    
    // 删除节点
    deleteNode() {
        if (!this.selectedNode) return;
        
        // 找到相关边线
        const relatedEdges = this.edges.filter(e => 
            e.from === this.selectedNode.id || 
            e.to === this.selectedNode.id
        );
        
        this.ui.showConfirm({
            title: '删除节点',
            message: `确定删除 "${this.selectedNode.name}" 吗？相关连线也会被删除。`,
            type: 'danger',
            onConfirm: () => {
                const command = new DeleteNodeCommand(this, this.selectedNode, relatedEdges);
                this.commandManager.execute(command);
                this.selectedNode = null;
                this.renderNodeProperties();
            }
        });
    }
    
    // 绑定撤销/重做按钮
    bindEvents() {
        document.getElementById('btn-undo')?.addEventListener('click', () => {
            this.commandManager.undo();
        });
        
        document.getElementById('btn-redo')?.addEventListener('click', () => {
            this.commandManager.redo();
        });
    }
}

// ===== 优化2: 自动保存到本地存储 =====
class AutoSaveManager {
    constructor(page, interval = 30000) {
        this.page = page;
        this.interval = interval;
        this.timer = null;
        this.storageKey = 'dag-draft';
    }
    
    start() {
        this.timer = setInterval(() => this.save(), this.interval);
        
        // 页面关闭前保存
        window.addEventListener('beforeunload', () => this.save());
    }
    
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    save() {
        const data = {
            nodes: this.page.nodes,
            edges: this.page.edges,
            timestamp: Date.now(),
            version: '1.0'
        };
        localStorage.setItem(this.storageKey, JSON.stringify(data));
    }
    
    load() {
        const saved = localStorage.getItem(this.storageKey);
        if (!saved) return null;
        
        const data = JSON.parse(saved);
        const age = Date.now() - data.timestamp;
        
        // 只恢复24小时内的草稿
        if (age > 24 * 60 * 60 * 1000) {
            localStorage.removeItem(this.storageKey);
            return null;
        }
        
        return data;
    }
    
    clear() {
        localStorage.removeItem(this.storageKey);
    }
}

// ===== 优化3: WebSocket实时状态更新 =====
class DAGWebSocketManager {
    constructor(page) {
        this.page = page;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        const wsUrl = `wss://${window.location.host}/ws/dag`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('[DAG] WebSocket连接成功');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    this.connect();
                }, 3000 * this.reconnectAttempts);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('[DAG] WebSocket错误:', error);
        };
    }
    
    handleMessage(data) {
        switch(data.type) {
            case 'node.status':
                this.updateNodeStatus(data.nodeId, data.status);
                break;
            case 'execution.progress':
                this.updateExecutionProgress(data.progress, data.nodeId);
                break;
            case 'execution.log':
                this.page.addExecutionLog(data.level, data.message);
                break;
            case 'execution.complete':
                this.handleExecutionComplete(data.success);
                break;
        }
    }
    
    updateNodeStatus(nodeId, status) {
        const node = this.page.nodes.find(n => n.id === nodeId);
        if (!node) return;
        
        const oldStatus = node.status;
        node.status = status;
        
        // 视觉反馈
        const nodeEl = document.querySelector(`[data-node-id="${nodeId}"]`);
        if (nodeEl) {
            // 状态变化动画
            nodeEl.classList.add('status-changing');
            setTimeout(() => {
                nodeEl.classList.remove('status-changing');
                nodeEl.className = `dag-node shape-${node.shape} status-${status}`;
            }, 300);
        }
        
        this.page.renderNodes();
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
```

#### 功能落实检查清单

- [x] 节点拖拽添加
- [x] 节点位置拖拽
- [x] 画布缩放/适应
- [x] 保存/导出DAG
- [x] 运行/停止DAG
- [ ] **撤销功能** ⭐ P0 - 待实现
- [ ] **重做功能** ⭐ P0 - 待实现
- [ ] **连线编辑** ⭐ P0 - 待实现
- [ ] 自动保存 ⭐ P1 - 待实现
- [ ] WebSocket实时状态 ⭐ P1 - 待实现
- [ ] 删除节点使用确认弹窗 ⭐ P1 - 待实现

---

### 4. Scripts 脚本管理页面

#### 现有功能按钮清单

| 按钮/功能 | 当前状态 | 问题 | 优先级 |
|-----------|----------|------|--------|
| 新建脚本 | ⚠️ 占位 | 显示"开发中" | P1 |
| 导入脚本 | ✅ 已实现 | 无文件预览 | P2 |
| 运行脚本 | ✅ 已实现 | 无进度显示 | P1 |
| 停止脚本 | ✅ 已实现 | - | - |
| 编辑脚本 | ⚠️ 占位 | 显示"开发中" | P1 |
| 删除脚本 | ✅ 已实现 | 使用原生confirm | P1 |
| 查看日志 | ✅ 已实现 | 非实时 | P1 |
| 批量启用/禁用 | ⚠️ 占位 | 显示"开发中" | P1 |
| 批量删除 | ✅ 已实现 | 使用原生confirm | P1 |
| 批量运行/停止 | ⚠️ 占位 | 显示"开发中" | P1 |
| 筛选/搜索 | ✅ 已实现 | - | - |
| 拖拽排序 | ✅ 已实现 | 不持久化 | **P0** |

#### 功能执行逻辑优化代码

```javascript
// ===== 优化1: 拖拽排序持久化 ⭐ P0 =====
async handleDrop(e, targetCard) {
    e.preventDefault();
    
    const draggedId = this.draggedScript;
    const targetId = targetCard.dataset.scriptId;
    
    if (!draggedId || draggedId === targetId) return;
    
    // 找到索引
    const draggedIndex = this.scripts.findIndex(s => s.id === draggedId);
    const targetIndex = this.scripts.findIndex(s => s.id === targetId);
    
    if (draggedIndex === -1 || targetIndex === -1) return;
    
    // 交换位置
    const [moved] = this.scripts.splice(draggedIndex, 1);
    this.scripts.splice(targetIndex, 0, moved);
    
    // 重新渲染
    this.applyFilters();
    this.renderGrid();
    
    // 保存到服务器
    try {
        const order = this.scripts.map(s => s.id);
        const response = await fetch(`${this.apiBaseUrl}/scripts/reorder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order })
        });
        
        if (!response.ok) throw new Error('保存失败');
        
        this.showToast('success', '脚本顺序已保存');
    } catch (error) {
        console.error('保存顺序失败:', error);
        this.showToast('error', '保存顺序失败，请重试');
        
        // 恢复原始顺序
        await this.loadScripts();
    }
}

// ===== 优化2: 批量删除增强确认 =====
async batchDelete() {
    if (this.selectedScripts.size === 0) return;
    
    const selectedItems = this.scripts.filter(s => 
        this.selectedScripts.has(s.id)
    );
    
    this.ui.showConfirm({
        title: `批量删除 ${selectedItems.length} 个脚本`,
        message: '以下脚本将被永久删除，此操作不可撤销：',
        type: 'danger',
        confirmText: '确认删除',
        content: `
            <div class="batch-delete-preview">
                ${selectedItems.map(s => `
                    <div class="delete-preview-item">
                        <span class="icon">🗑️</span>
                        <span class="name">${s.name}</span>
                        <span class="status ${s.status}">${s.status}</span>
                    </div>
                `).join('')}
            </div>
        `,
        onConfirm: async () => {
            // 显示进度弹窗
            const progressModal = this.ui.renderModal({
                title: '正在删除...',
                content: `
                    <div class="delete-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="delete-progress-fill"></div>
                        </div>
                        <div class="progress-text" id="delete-progress-text">0 / ${selectedItems.length}</div>
                    </div>
                `,
                closable: false,
                buttons: []
            });
            
            let completed = 0;
            const errors = [];
            
            for (const script of selectedItems) {
                try {
                    const response = await fetch(
                        `${this.apiBaseUrl}/scripts/${script.id}`, 
                        { method: 'DELETE' }
                    );
                    
                    if (!response.ok) throw new Error(`删除 ${script.name} 失败`);
                    
                    completed++;
                    
                    // 更新进度
                    const fill = document.getElementById('delete-progress-fill');
                    const text = document.getElementById('delete-progress-text');
                    if (fill) {
                        fill.style.width = `${(completed / selectedItems.length) * 100}%`;
                    }
                    if (text) {
                        text.textContent = `${completed} / ${selectedItems.length}`;
                    }
                    
                } catch (error) {
                    errors.push(script.name);
                }
            }
            
            this.ui.closeModal(progressModal);
            
            if (errors.length > 0) {
                this.ui.showToast({
                    type: 'warning',
                    message: `已删除 ${completed} 个，${errors.length} 个失败`
                });
            } else {
                this.showToast('success', `成功删除 ${completed} 个脚本`);
            }
            
            this.clearSelection();
            this.loadScripts();
        }
    });
}

// ===== 优化3: 实时日志查看 =====
class LogWebSocketManager {
    constructor(page) {
        this.page = page;
        this.connections = new Map(); // scriptId -> WebSocket
    }
    
    connect(scriptId) {
        if (this.connections.has(scriptId)) return;
        
        const ws = new WebSocket(
            `wss://${window.location.host}/ws/scripts/${scriptId}/logs`
        );
        
        ws.onmessage = (event) => {
            const log = JSON.parse(event.data);
            this.appendLog(scriptId, log);
        };
        
        ws.onclose = () => {
            this.connections.delete(scriptId);
        };
        
        this.connections.set(scriptId, ws);
    }
    
    disconnect(scriptId) {
        const ws = this.connections.get(scriptId);
        if (ws) {
            ws.close();
            this.connections.delete(scriptId);
        }
    }
    
    disconnectAll() {
        this.connections.forEach(ws => ws.close());
        this.connections.clear();
    }
    
    appendLog(scriptId, log) {
        const container = document.getElementById('logs-container');
        if (!container) return;
        
        const entry = document.createElement('div');
        entry.className = `log-entry log-${log.level}`;
        entry.innerHTML = `
            <span class="log-time">${new Date(log.timestamp).toLocaleTimeString()}</span>
            <span class="log-level">${log.level.toUpperCase()}</span>
            <span class="log-message">${log.message}</span>
        `;
        
        container.appendChild(entry);
        container.scrollTop = container.scrollHeight;
    }
}

// ===== 优化4: 脚本执行进度跟踪 =====
async runScript(scriptId) {
    try {
        const response = await fetch(
            `${this.apiBaseUrl}/scripts/${scriptId}/run`,
            { method: 'POST' }
        );
        
        if (!response.ok) throw new Error('启动失败');
        
        const data = await response.json();
        
        // 如果有执行ID，跟踪进度
        if (data.executionId) {
            this.trackExecutionProgress(scriptId, data.executionId);
        }
        
        this.showToast('success', '脚本已开始运行');
        this.loadScripts();
        
    } catch (error) {
        this.showToast('error', '启动脚本失败: ' + error.message);
    }
}

trackExecutionProgress(scriptId, executionId) {
    // 创建进度弹窗
    const modalId = this.ui.renderModal({
        title: '脚本执行中',
        content: `
            <div class="execution-tracker">
                <div class="progress-section">
                    <div class="progress-bar">
                        <div class="progress-fill" id="exec-progress-fill"></div>
                    </div>
                    <div class="progress-info">
                        <span id="exec-progress-text">0%</span>
                        <span id="exec-status">初始化...</span>
                    </div>
                </div>
                <div class="execution-logs" id="exec-logs"></div>
            </div>
        `,
        closable: false,
        buttons: [{
            label: '停止执行',
            variant: 'danger',
            action: 'stop',
            onClick: () => this.stopExecution(executionId)
        }]
    });
    
    // 连接WebSocket接收进度
    const ws = new WebSocket(
        `wss://${window.location.host}/ws/executions/${executionId}`
    );
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'progress':
                const fill = document.getElementById('exec-progress-fill');
                const text = document.getElementById('exec-progress-text');
                if (fill) fill.style.width = `${data.value}%`;
                if (text) text.textContent = `${data.value}%`;
                break;
                
            case 'status':
                const status = document.getElementById('exec-status');
                if (status) status.textContent = data.message;
                break;
                
            case 'log':
                const logs = document.getElementById('exec-logs');
                if (logs) {
                    logs.innerHTML += `<div class="log-line">[${data.level}] ${data.message}</div>`;
                    logs.scrollTop = logs.scrollHeight;
                }
                break;
                
            case 'complete':
                ws.close();
                this.ui.closeModal(modalId);
                
                if (data.success) {
                    this.showToast('success', '脚本执行完成');
                } else {
                    this.showToast('error', '脚本执行失败');
                }
                
                this.loadScripts();
                break;
        }
    };
}
```

#### 功能落实检查清单

- [x] 导入脚本
- [x] 运行/停止脚本
- [x] 删除脚本（有确认）
- [x] 查看日志
- [x] 筛选/搜索
- [x] 拖拽排序
- [ ] **拖拽排序持久化** ⭐ P0 - 待实现
- [ ] 新建脚本功能 ⭐ P1 - 待实现
- [ ] 编辑脚本功能 ⭐ P1 - 待实现
- [ ] 批量操作功能 ⭐ P1 - 待实现
- [ ] 实时日志查看 ⭐ P1 - 待实现
- [ ] 执行进度跟踪 ⭐ P1 - 待实现
- [ ] 批量删除增强确认 ⭐ P1 - 待实现

---

### 5. Alerts 告警中心页面

#### 现有功能按钮清单

| 按钮/功能 | 当前状态 | 问题 | 优先级 |
|-----------|----------|------|--------|
| 标签切换 | ✅ 已实现 | - | - |
| 告警确认 | ✅ 已实现 | 无批量确认 | P1 |
| 告警忽略 | ✅ 已实现 | - | - |
| 规则启用/禁用 | ✅ 已实现 | - | - |
| 规则编辑 | ✅ 已实现 | - | - |
| 规则删除 | ✅ 已实现 | 使用原生confirm | P1 |
| 实时告警推送 | ⚠️ 部分 | 需要优化重连 | P1 |
| 告警详情查看 | ❌ 未实现 | - | P1 |
| 批量确认 | ❌ 未实现 | - | **P0** |

#### 功能执行逻辑优化代码

```javascript
// ===== 优化1: 批量确认告警 ⭐ P0 =====
class BatchAlertManager {
    constructor(page) {
        this.page = page;
        this.selectedAlerts = new Set();
    }
    
    toggleSelection(alertId) {
        if (this.selectedAlerts.has(alertId)) {
            this.selectedAlerts.delete(alertId);
        } else {
            this.selectedAlerts.add(alertId);
        }
        this.updateUI();
    }
    
    selectAll(alerts) {
        alerts.forEach(a => this.selectedAlerts.add(a.id));
        this.updateUI();
    }
    
    clearSelection() {
        this.selectedAlerts.clear();
        this.updateUI();
    }
    
    updateUI() {
        const count = this.selectedAlerts.size;
        const toolbar = document.getElementById('alert-batch-toolbar');
        
        if (count > 0) {
            toolbar.classList.remove('hidden');
            document.getElementById('selected-alert-count').textContent = count;
        } else {
            toolbar.classList.add('hidden');
        }
    }
    
    async batchAcknowledge() {
        if (this.selectedAlerts.size === 0) return;
        
        this.page.ui.showConfirm({
            title: `确认 ${this.selectedAlerts.size} 个告警`,
            message: '确认后这些告警将被标记为已处理',
            type: 'info',
            onConfirm: async () => {
                // 显示进度
                const progressModal = this.page.ui.renderModal({
                    title: '正在确认...',
                    content: `<div class="progress-bar"><div class="progress-fill" id="ack-progress"></div></div>`,
                    closable: false,
                    buttons: []
                });
                
                let completed = 0;
                
                for (const alertId of this.selectedAlerts) {
                    try {
                        await fetch(`${this.page.apiBaseUrl}/alerts/${alertId}/acknowledge`, {
                            method: 'POST'
                        });
                        completed++;
                        
                        const fill = document.getElementById('ack-progress');
                        if (fill) {
                            fill.style.width = `${(completed / this.selectedAlerts.size) * 100}%`;
                        }
                    } catch (error) {
                        console.error(`确认告警 ${alertId} 失败:`, error);
                    }
                }
                
                this.page.ui.closeModal(progressModal);
                this.clearSelection();
                this.page.loadAlerts();
                this.page.showToast('success', `已确认 ${completed} 个告警`);
            }
        });
    }
}

// ===== 优化2: 告警详情抽屉 =====
showAlertDetail(alertId) {
    const alert = this.alerts.find(a => a.id === alertId);
    if (!alert) return;
    
    // 创建详情抽屉
    const drawer = document.createElement('div');
    drawer.className = 'alert-detail-drawer';
    drawer.innerHTML = `
        <div class="drawer-overlay" onclick="this.parentElement.remove()"></div>
        <div class="drawer-content">
            <div class="drawer-header">
                <h3>告警详情</h3>
                <button class="btn-close" onclick="this.closest('.alert-detail-drawer').remove()">×</button>
            </div>
            <div class="drawer-body">
                <div class="detail-section">
                    <label>告警级别</label>
                    <span class="alert-level ${alert.level}">${alert.level}</span>
                </div>
                <div class="detail-section">
                    <label>告警消息</label>
                    <p>${alert.message}</p>
                </div>
                <div class="detail-section">
                    <label>发生时间</label>
                    <p>${new Date(alert.timestamp).toLocaleString()}</p>
                </div>
                <div class="detail-section">
                    <label>来源</label>
                    <p>${alert.source || '未知'}</p>
                </div>
                <div class="detail-section">
                    <label>详细信息</label>
                    <pre>${JSON.stringify(alert.details || {}, null, 2)}</pre>
                </div>
            </div>
            <div class="drawer-footer">
                <button class="btn btn-primary" onclick="alertPage.acknowledgeAlert('${alertId}')">
                    确认告警
                </button>
                <button class="btn btn-secondary" onclick="alertPage.ignoreAlert('${alertId}')">
                    忽略
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(drawer);
    
    // 动画显示
    requestAnimationFrame(() => {
        drawer.querySelector('.drawer-content').classList.add('open');
    });
}

// ===== 优化3: WebSocket重连机制 =====
class AlertWebSocketManager {
    constructor(page) {
        this.page = page;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        this.heartbeatInterval = null;
    }
    
    connect() {
        const ws
