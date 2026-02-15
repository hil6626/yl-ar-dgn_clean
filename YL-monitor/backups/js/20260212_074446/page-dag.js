/**
 * YL-Monitor DAG流水线页面逻辑
 * 版本: v8.1.0
 * 特性: 三栏布局、节点拖拽、画布缩放、执行控制、撤销重做
 */

// ==================== 命令模式实现 ====================

/**
 * 命令管理器 - 实现撤销/重做功能
 */
class CommandManager {
    constructor(page) {
        this.page = page;
        this.undoStack = [];
        this.redoStack = [];
        this.maxHistory = 50;
    }
    
    /**
     * 执行命令
     */
    execute(command) {
        command.execute();
        this.undoStack.push(command);
        this.redoStack = []; // 清空重做栈
        
        // 限制历史记录大小
        if (this.undoStack.length > this.maxHistory) {
            this.undoStack.shift();
        }
        
        this.updateUI();
    }
    
    /**
     * 撤销
     */
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
    
    /**
     * 重做
     */
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
    
    /**
     * 更新UI状态
     */
    updateUI() {
        const undoBtn = document.getElementById('btn-undo');
        const redoBtn = document.getElementById('btn-redo');
        
        if (undoBtn) undoBtn.disabled = this.undoStack.length === 0;
        if (redoBtn) redoBtn.disabled = this.redoStack.length === 0;
    }
    
    /**
     * 清空历史
     */
    clear() {
        this.undoStack = [];
        this.redoStack = [];
        this.updateUI();
    }
}

/**
 * 添加节点命令
 */
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

/**
 * 删除节点命令
 */
class DeleteNodeCommand {
    constructor(page, node, relatedEdges) {
        this.page = page;
        this.node = node;
        this.nodeId = node.id;
        this.relatedEdges = relatedEdges || [];
    }
    
    execute() {
        // 删除相关边线
        this.page.edges = this.page.edges.filter(e => 
            !this.relatedEdges.some(re => re.from === e.from && re.to === e.to)
        );
        
        // 删除节点
        this.page.nodes = this.page.nodes.filter(n => n.id !== this.nodeId);
        
        this.page.renderNodes();
        this.page.renderEdges();
    }
    
    undo() {
        // 恢复节点
        this.page.nodes.push(this.node);
        
        // 恢复边线
        this.page.edges.push(...this.relatedEdges);
        
        this.page.renderNodes();
        this.page.renderEdges();
    }
}

/**
 * 移动节点命令
 */
class MoveNodeCommand {
    constructor(page, nodeId, oldPos, newPos) {
        this.page = page;
        this.nodeId = nodeId;
        this.oldPos = { ...oldPos };
        this.newPos = { ...newPos };
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

/**
 * 更新节点属性命令
 */
class UpdateNodePropertyCommand {
    constructor(page, nodeId, property, oldValue, newValue) {
        this.page = page;
        this.nodeId = nodeId;
        this.property = property;
        this.oldValue = oldValue;
        this.newValue = newValue;
    }
    
    execute() {
        const node = this.page.nodes.find(n => n.id === this.nodeId);
        if (node) {
            node[this.property] = this.newValue;
            this.page.renderNodes();
        }
    }
    
    undo() {
        const node = this.page.nodes.find(n => n.id === this.nodeId);
        if (node) {
            node[this.property] = this.oldValue;
            this.page.renderNodes();
        }
    }
}

/**
 * 添加连线命令
 */
class AddEdgeCommand {
    constructor(page, edge) {
        this.page = page;
        this.edge = edge;
    }
    
    execute() {
        this.page.edges.push(this.edge);
        this.page.renderEdges();
    }
    
    undo() {
        this.page.edges = this.page.edges.filter(e => 
            !(e.from === this.edge.from && e.to === this.edge.to)
        );
        this.page.renderEdges();
    }
}

/**
 * 删除连线命令
 */
class DeleteEdgeCommand {
    constructor(page, edge) {
        this.page = page;
        this.edge = edge;
    }
    
    execute() {
        this.page.edges = this.page.edges.filter(e => 
            !(e.from === this.edge.from && e.to === this.edge.to)
        );
        this.page.renderEdges();
    }
    
    undo() {
        this.page.edges.push(this.edge);
        this.page.renderEdges();
    }
}

// ==================== 自动保存管理器 ====================

/**
 * 自动保存管理器 - 实现DAG自动保存和草稿恢复
 */
class AutoSaveManager {
    constructor(page) {
        this.page = page;
        this.autoSaveInterval = null;
        this.AUTO_SAVE_DELAY = 30000; // 30秒自动保存
        this.DRAFT_EXPIRY = 24 * 60 * 60 * 1000; // 24小时过期
        this.STORAGE_KEY = 'yl_dag_draft';
        this.lastSaveTime = null;
        this.hasUnsavedChanges = false;
    }
    
    /**
     * 初始化自动保存
     */
    init() {
        // 检查是否有未恢复的草稿
        this.checkDraftRecovery();
        
        // 启动自动保存定时器
        this.startAutoSave();
        
        // 监听页面关闭事件
        window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
        
        console.log('[AutoSaveManager] 自动保存管理器已初始化');
    }
    
    /**
     * 启动自动保存
     */
    startAutoSave() {
        // 清除现有定时器
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        // 每30秒自动保存
        this.autoSaveInterval = setInterval(() => {
            this.autoSave();
        }, this.AUTO_SAVE_DELAY);
    }
    
    /**
     * 停止自动保存
     */
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }
    
    /**
     * 执行自动保存
     */
    async autoSave() {
        if (!this.hasUnsavedChanges) {
            return; // 没有变更，跳过保存
        }
        
        try {
            const draftData = {
                nodes: this.page.nodes,
                edges: this.page.edges,
                timestamp: Date.now(),
                version: '1.0.0'
            };
            
            // 保存到localStorage
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(draftData));
            this.lastSaveTime = Date.now();
            this.hasUnsavedChanges = false;
            
            console.log('[AutoSaveManager] 草稿已自动保存');
            
            // 显示保存提示（每5分钟显示一次）
            if (this.shouldShowSaveNotification()) {
                this.page.ui.showToast({ 
                    type: 'info', 
                    message: 'DAG草稿已自动保存' 
                });
            }
            
        } catch (error) {
            console.error('[AutoSaveManager] 自动保存失败:', error);
        }
    }
    
    /**
     * 标记有未保存的变更
     */
    markUnsaved() {
        this.hasUnsavedChanges = true;
    }
    
    /**
     * 检查是否需要显示保存通知
     */
    shouldShowSaveNotification() {
        if (!this.lastSaveTime) return true;
        
        const fiveMinutes = 5 * 60 * 1000;
        return (Date.now() - this.lastSaveTime) >= fiveMinutes;
    }
    
    /**
     * 检查草稿恢复
     */
    checkDraftRecovery() {
        try {
            const draftJson = localStorage.getItem(this.STORAGE_KEY);
            if (!draftJson) return;
            
            const draft = JSON.parse(draftJson);
            
            // 检查草稿是否过期
            if (Date.now() - draft.timestamp > this.DRAFT_EXPIRY) {
                console.log('[AutoSaveManager] 草稿已过期，清除');
                localStorage.removeItem(this.STORAGE_KEY);
                return;
            }
            
            // 显示恢复提示
            this.showDraftRecoveryDialog(draft);
            
        } catch (error) {
            console.error('[AutoSaveManager] 检查草稿失败:', error);
        }
    }
    
    /**
     * 显示草稿恢复对话框
     */
    showDraftRecoveryDialog(draft) {
        const saveTime = new Date(draft.timestamp).toLocaleString('zh-CN');
        
        this.page.ui.showConfirm({
            title: '恢复DAG草稿',
            message: `检测到未保存的DAG草稿（${saveTime}），是否恢复？`,
            type: 'info',
            confirmText: '恢复草稿',
            cancelText: '丢弃',
            onConfirm: () => {
                this.restoreDraft(draft);
            },
            onCancel: () => {
                this.clearDraft();
            }
        });
    }
    
    /**
     * 恢复草稿
     */
    restoreDraft(draft) {
        try {
            this.page.nodes = draft.nodes || [];
            this.page.edges = draft.edges || [];
            
            this.page.renderNodes();
            this.page.renderEdges();
            
            this.page.ui.showToast({ 
                type: 'success', 
                message: 'DAG草稿已恢复' 
            });
            
            console.log('[AutoSaveManager] 草稿已恢复');
            
        } catch (error) {
            console.error('[AutoSaveManager] 恢复草稿失败:', error);
            this.page.ui.showToast({ 
                type: 'error', 
                message: '恢复草稿失败' 
            });
        }
    }
    
    /**
     * 清除草稿
     */
    clearDraft() {
        localStorage.removeItem(this.STORAGE_KEY);
        console.log('[AutoSaveManager] 草稿已清除');
    }
    
    /**
     * 处理页面关闭
     */
    handleBeforeUnload(e) {
        if (this.hasUnsavedChanges) {
            // 立即保存
            this.autoSave();
            
            // 显示确认提示
            e.preventDefault();
            e.returnValue = '有未保存的变更，确定要离开吗？';
            return e.returnValue;
        }
    }
    
    /**
     * 手动保存触发
     */
    onManualSave() {
        this.hasUnsavedChanges = false;
        this.clearDraft(); // 清除草稿，因为已正式保存
    }
}

// ==================== DAG页面类 ====================

export default class DAGPage {
    constructor(deps) {
        this.themeManager = deps.themeManager;
        this.ui = deps.uiComponents;
        this.apiBaseUrl = '/api/v1';
        
        // 命令管理器（撤销/重做）
        this.commandManager = new CommandManager(this);
        
        // 自动保存管理器
        this.autoSaveManager = new AutoSaveManager(this);
        
        // 画布状态
        this.canvas = null;
        this.canvasContainer = null;
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.isDragging = false;
        this.isNodeDragging = false;
        this.dragNode = null;
        this.dragOffset = { x: 0, y: 0 };
        this.dragStartPos = null; // 记录拖拽开始位置
        
        // 数据
        this.nodes = [];
        this.edges = [];
        this.selectedNode = null;
        this.selectedEdge = null; // 选中的连线
        this.executionStatus = 'idle';
        this.executionProgress = 0;
        
        // 连线编辑状态
        this.isEdgeEditing = false;
        this.edgeEditMode = false; // 连线编辑模式
        
        // 节点库
        this.nodeTemplates = [
            {
                category: '基础节点',
                icon: '🔧',
                expanded: true,
                nodes: [
                    { type: 'start', name: '开始节点', shape: 'circle', icon: '🚀', color: '#10b981' },
                    { type: 'end', name: '结束节点', shape: 'circle', icon: '🏁', color: '#ef4444' }
                ]
            },
            {
                category: '处理节点',
                icon: '⚙️',
                expanded: true,
                nodes: [
                    { type: 'process', name: '处理节点', shape: 'rect', icon: '⚙️', color: '#3b82f6' },
                    { type: 'condition', name: '条件判断', shape: 'diamond', icon: '❓', color: '#f59e0b' },
                    { type: 'loop', name: '循环节点', shape: 'hexagon', icon: '🔄', color: '#8b5cf6' }
                ]
            },
            {
                category: '数据节点',
                icon: '📦',
                expanded: false,
                nodes: [
                    { type: 'input', name: '数据输入', shape: 'rounded', icon: '📥', color: '#06b6d4' },
                    { type: 'output', name: '数据输出', shape: 'rounded', icon: '📤', color: '#ec4899' },
                    { type: 'transform', name: '数据转换', shape: 'rect', icon: '🔀', color: '#6366f1' }
                ]
            }
        ];
    }

    async init() {
        console.log('[DAGPage] 初始化DAG页面...');
        
        // 1. 渲染导航栏
        this.renderNavbar();
        
        // 2. 渲染控制栏
        this.renderControlBar();
        
        // 3. 渲染节点库
        this.renderNodePanel();
        
        // 4. 渲染画布
        this.renderCanvas();
        
        // 5. 渲染属性面板
        this.renderPropertiesPanel();
        
        // 6. 渲染执行面板
        this.renderExecutionPanel();
        
        // 7. 加载DAG数据
        await this.loadDAGData();
        
        // 8. 初始化自动保存
        this.autoSaveManager.init();
        
        // 9. 绑定事件
        this.bindEvents();
        
        console.log('[DAGPage] DAG页面初始化完成 ✅');
    }

    renderNavbar() {
        this.ui.renderNavbar('navbar-mount', {
            logo: '/static/img/logo.svg',
            brandText: '浏览器监控平台',
            theme: 'dark',
            items: [
                { id: 'dashboard', label: '仪表盘', icon: '📊', href: '/dashboard' },
                { id: 'api-doc', label: 'API文档', icon: '📚', href: '/api-doc' },
                { id: 'dag', label: 'DAG流水线', icon: '🔄', active: true, href: '/dag' },
                { id: 'scripts', label: '脚本管理', icon: '📜', href: '/scripts' }
            ]
        });
    }

    renderControlBar() {
        const mount = document.getElementById('dag-control-bar');
        if (!mount) return;

        mount.innerHTML = `
            <div class="dag-control-group">
                <div class="dag-control-title">
                    <span>🔄</span>
                    <span>DAG流水线</span>
                </div>
            </div>
            <div class="dag-control-group">
                <button class="dag-control-btn" id="btn-save" title="保存">
                    <span>💾</span> 保存
                </button>
                <button class="dag-control-btn" id="btn-undo" title="撤销" disabled>
                    <span>↩️</span> 撤销
                </button>
                <button class="dag-control-btn" id="btn-redo" title="重做" disabled>
                    <span>↪️</span> 重做
                </button>
                <button class="dag-control-btn" id="btn-export" title="导出">
                    <span>📥</span> 导出
                </button>
                <button class="dag-control-btn ${this.edgeEditMode ? 'active' : ''}" id="btn-edge-edit" title="连线编辑">
                    <span>🔗</span> 连线
                </button>
                <div style="width: 1px; height: 24px; background: var(--border); margin: 0 8px;"></div>
                <button class="dag-control-btn primary" id="btn-run" title="运行">
                    <span>▶️</span> 运行
                </button>
                <button class="dag-control-btn danger" id="btn-stop" title="停止" disabled>
                    <span>⏹️</span> 停止
                </button>
            </div>
        `;

        // 绑定控制按钮事件
        document.getElementById('btn-save')?.addEventListener('click', () => this.saveDAG());
        document.getElementById('btn-undo')?.addEventListener('click', () => this.undo());
        document.getElementById('btn-redo')?.addEventListener('click', () => this.redo());
        document.getElementById('btn-export')?.addEventListener('click', () => this.exportDAG());
        document.getElementById('btn-edge-edit')?.addEventListener('click', () => this.toggleEdgeEditMode());
        document.getElementById('btn-run')?.addEventListener('click', () => this.runDAG());
        document.getElementById('btn-stop')?.addEventListener('click', () => this.stopDAG());
    }

    renderNodePanel() {
        const mount = document.getElementById('dag-nodes-panel');
        if (!mount) return;

        mount.innerHTML = `
            <div class="dag-nodes-header">
                <h3>节点库</h3>
            </div>
            <div class="dag-nodes-content">
                ${this.nodeTemplates.map((category, catIndex) => `
                    <div class="dag-node-category">
                        <div class="dag-category-header ${category.expanded ? 'expanded' : ''}" data-category="${catIndex}">
                            <span class="category-icon">${category.icon}</span>
                            <span class="category-name">${category.category}</span>
                            <span class="category-toggle">▶</span>
                        </div>
                        <div class="dag-category-nodes ${category.expanded ? 'expanded' : ''}" id="category-${catIndex}">
                            ${category.nodes.map((node, nodeIndex) => `
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

        // 绑定分类展开/折叠
        mount.querySelectorAll('.dag-category-header').forEach(header => {
            header.addEventListener('click', () => {
                const catIndex = header.dataset.category;
                const nodesContainer = document.getElementById(`category-${catIndex}`);
                const isExpanded = header.classList.contains('expanded');
                
                header.classList.toggle('expanded', !isExpanded);
                nodesContainer.classList.toggle('expanded', !isExpanded);
            });
        });

        // 绑定拖拽事件
        mount.querySelectorAll('.dag-node-template').forEach(template => {
            template.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('nodeType', template.dataset.nodeType);
                e.dataTransfer.setData('nodeShape', template.dataset.nodeShape);
                e.dataTransfer.setData('nodeName', template.dataset.nodeName);
                e.dataTransfer.setData('nodeIcon', template.dataset.nodeIcon);
                e.dataTransfer.setData('nodeColor', template.dataset.nodeColor);
                e.dataTransfer.effectAllowed = 'copy';
            });
        });
    }

    renderCanvas() {
        this.canvasContainer = document.getElementById('dag-canvas-container');
        this.canvas = document.getElementById('dag-canvas');
        
        if (!this.canvas || !this.canvasContainer) return;

        // 设置画布尺寸
        this.updateCanvasTransform();

        // 绑定画布控制按钮
        document.getElementById('zoom-in')?.addEventListener('click', () => this.zoomIn());
        document.getElementById('zoom-out')?.addEventListener('click', () => this.zoomOut());
        document.getElementById('zoom-fit')?.addEventListener('click', () => this.zoomFit());
    }

    renderPropertiesPanel() {
        const mount = document.getElementById('dag-properties-panel');
        if (!mount) return;

        mount.innerHTML = `
            <div class="dag-properties-header">
                <h3>属性面板</h3>
            </div>
            <div class="dag-properties-content" id="properties-content">
                <div class="dag-properties-empty">
                    <div class="empty-icon">📋</div>
                    <p>选择节点查看属性</p>
                </div>
            </div>
        `;
    }

    renderExecutionPanel() {
        const mount = document.getElementById('dag-execution-panel');
        if (!mount) return;

        // 绑定折叠/展开
        const header = mount.querySelector('.execution-panel-header');
        if (header) {
            header.addEventListener('click', () => {
                const isCollapsed = mount.classList.contains('collapsed');
                mount.classList.toggle('collapsed', !isCollapsed);
                mount.classList.toggle('expanded', isCollapsed);
            });
        }
    }

    async loadDAGData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dag/definition`);
            if (!response.ok) throw new Error('加载DAG数据失败');
            
            const data = await response.json();
            this.nodes = data.nodes || this.getSampleNodes();
            this.edges = data.edges || this.getSampleEdges();
        } catch (error) {
            console.warn('[DAGPage] 使用示例数据:', error);
            this.nodes = this.getSampleNodes();
            this.edges = this.getSampleEdges();
        }

        this.renderNodes();
        this.renderEdges();
    }

    getSampleNodes() {
        return [
            { id: 'node-1', type: 'start', name: '开始', shape: 'circle', icon: '🚀', x: 100, y: 200, status: 'success', color: '#10b981' },
            { id: 'node-2', type: 'process', name: '数据处理', shape: 'rect', icon: '⚙️', x: 300, y: 200, status: 'success', color: '#3b82f6' },
            { id: 'node-3', type: 'condition', name: '条件判断', shape: 'diamond', icon: '❓', x: 500, y: 200, status: 'running', color: '#f59e0b' },
            { id: 'node-4', type: 'process', name: '分支A', shape: 'rect', icon: '🔀', x: 700, y: 100, status: 'pending', color: '#6366f1' },
            { id: 'node-5', type: 'process', name: '分支B', shape: 'rect', icon: '🔀', x: 700, y: 300, status: 'pending', color: '#6366f1' },
            { id: 'node-6', type: 'end', name: '结束', shape: 'circle', icon: '🏁', x: 900, y: 200, status: 'pending', color: '#ef4444' }
        ];
    }

    getSampleEdges() {
        return [
            { from: 'node-1', to: 'node-2' },
            { from: 'node-2', to: 'node-3' },
            { from: 'node-3', to: 'node-4', label: '是' },
            { from: 'node-3', to: 'node-5', label: '否' },
            { from: 'node-4', to: 'node-6' },
            { from: 'node-5', to: 'node-6' }
        ];
    }

    renderNodes() {
        const container = document.getElementById('dag-nodes-layer');
        if (!container) return;

        container.innerHTML = this.nodes.map(node => `
            <div class="dag-node shape-${node.shape} status-${node.status} ${this.selectedNode?.id === node.id ? 'selected' : ''}"
                 data-node-id="${node.id}"
                 style="left: ${node.x}px; top: ${node.y}px; border-color: ${node.color}">
                <div class="node-content">
                    <div class="node-icon">${node.icon}</div>
                    <div class="node-name">${node.name}</div>
                    <div class="node-status">
                        <span class="status-dot"></span>
                        <span>${this.getStatusText(node.status)}</span>
                    </div>
                </div>
                <div class="connection-point top"></div>
                <div class="connection-point bottom"></div>
                <div class="connection-point left"></div>
                <div class="connection-point right"></div>
            </div>
        `).join('');

        // 绑定节点事件
        container.querySelectorAll('.dag-node').forEach(nodeEl => {
            // 点击选中
            nodeEl.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectNode(nodeEl.dataset.nodeId);
            });

            // 拖拽
            nodeEl.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                this.startNodeDrag(e, nodeEl.dataset.nodeId);
            });
        });
    }

    renderEdges() {
        const svg = document.getElementById('dag-edges-layer');
        if (!svg) return;

        // 清空现有边线
        svg.innerHTML = '';

        // 计算边线路径
        this.edges.forEach((edge, index) => {
            const fromNode = this.nodes.find(n => n.id === edge.from);
            const toNode = this.nodes.find(n => n.id === edge.to);
            
            if (!fromNode || !toNode) return;

            const path = this.calculateBezierPath(fromNode, toNode);
            
            const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            pathEl.setAttribute('d', path);
            
            // 检查是否选中
            const isSelected = this.selectedEdge && 
                this.selectedEdge.from === edge.from && 
                this.selectedEdge.to === edge.to;
            
            let className = 'dag-edge-path';
            if (edge.label) className += ' conditional';
            if (isSelected) className += ' selected';
            if (this.edgeEditMode) className += ' editable';
            
            pathEl.setAttribute('class', className);
            pathEl.setAttribute('data-edge-index', index);
            pathEl.setAttribute('data-edge-from', edge.from);
            pathEl.setAttribute('data-edge-to', edge.to);
            
            // 绑定点击事件
            pathEl.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectEdge(edge);
            });
            
            // 绑定双击删除
            pathEl.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                this.deleteEdge(edge);
            });
            
            svg.appendChild(pathEl);

            // 添加标签
            if (edge.label) {
                const midX = (fromNode.x + toNode.x) / 2 + 60;
                const midY = (fromNode.y + toNode.y) / 2 + 30;
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', midX);
                text.setAttribute('y', midY);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('fill', 'var(--text-secondary)');
                text.setAttribute('font-size', '12');
                text.textContent = edge.label;
                
                svg.appendChild(text);
            }
        });
    }

    calculateBezierPath(fromNode, toNode) {
        const fromX = fromNode.x + 60;
        const fromY = fromNode.y + 30;
        const toX = toNode.x + 60;
        const toY = toNode.y + 30;
        
        const controlX1 = fromX + (toX - fromX) / 2;
        const controlY1 = fromY;
        const controlX2 = fromX + (toX - fromX) / 2;
        const controlY2 = toY;
        
        return `M ${fromX} ${fromY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${toX} ${toY}`;
    }

    getStatusText(status) {
        const statusMap = {
            pending: '等待中',
            running: '运行中',
            success: '成功',
            error: '失败',
            warning: '警告'
        };
        return statusMap[status] || status;
    }

    selectNode(nodeId) {
        this.selectedNode = this.nodes.find(n => n.id === nodeId);
        this.selectedEdge = null; // 清除连线选中
        this.renderNodes(); // 重新渲染以更新选中状态
        this.renderEdges(); // 重新渲染边线以清除选中状态
        this.renderNodeProperties();
    }
    
    /**
     * 选中连线
     */
    selectEdge(edge) {
        this.selectedEdge = edge;
        this.selectedNode = null; // 清除节点选中
        this.renderEdges(); // 重新渲染以更新选中状态
        this.renderNodes(); // 重新渲染节点以清除选中状态
        this.renderEdgeProperties(); // 显示连线属性
    }
    
    /**
     * 显示连线属性
     */
    renderEdgeProperties() {
        const mount = document.getElementById('properties-content');
        if (!mount) return;
        
        if (!this.selectedEdge) {
            mount.innerHTML = `
                <div class="dag-properties-empty">
                    <div class="empty-icon">📋</div>
                    <p>选择连线查看属性</p>
                </div>
            `;
            return;
        }
        
        const fromNode = this.nodes.find(n => n.id === this.selectedEdge.from);
        const toNode = this.nodes.find(n => n.id === this.selectedEdge.to);
        
        mount.innerHTML = `
            <div class="dag-property-group">
                <label class="dag-property-label">连线信息</label>
                <div class="edge-info">
                    <p>从: ${fromNode?.name || this.selectedEdge.from}</p>
                    <p>到: ${toNode?.name || this.selectedEdge.to}</p>
                </div>
            </div>
            
            <div class="dag-property-group">
                <label class="dag-property-label">条件标签</label>
                <input type="text" class="dag-property-input" id="edge-label" 
                       value="${this.selectedEdge.label || ''}" placeholder="输入条件标签">
            </div>
            
            <div class="dag-property-actions">
                <button class="dag-control-btn primary" id="btn-save-edge">
                    <span>💾</span> 保存
                </button>
                <button class="dag-control-btn danger" id="btn-delete-edge">
                    <span>🗑️</span> 删除连线
                </button>
            </div>
        `;
        
        // 绑定保存和删除
        document.getElementById('btn-save-edge')?.addEventListener('click', () => this.saveEdgeProperties());
        document.getElementById('btn-delete-edge')?.addEventListener('click', () => this.deleteEdge(this.selectedEdge));
    }
    
    /**
     * 保存连线属性
     */
    saveEdgeProperties() {
        if (!this.selectedEdge) return;
        
        const label = document.getElementById('edge-label')?.value;
        this.selectedEdge.label = label || undefined;
        
        this.renderEdges();
        
        // 标记有未保存变更
        this.autoSaveManager.markUnsaved();
        
        this.ui.showToast({ type: 'success', message: '连线属性已保存' });
    }
    
    /**
     * 删除连线
     */
    deleteEdge(edge) {
        if (!edge) return;
        
        const fromNode = this.nodes.find(n => n.id === edge.from);
        const toNode = this.nodes.find(n => n.id === edge.to);
        
        this.ui.showConfirm({
            title: '删除连线',
            message: `确定要删除从 "${fromNode?.name || edge.from}" 到 "${toNode?.name || edge.to}" 的连线吗？`,
            type: 'danger',
            confirmText: '删除',
            onConfirm: () => {
                const command = new DeleteEdgeCommand(this, edge);
                this.commandManager.execute(command);
                
                this.selectedEdge = null;
                this.renderEdgeProperties();
                
                // 标记有未保存变更
                this.autoSaveManager.markUnsaved();
                
                this.ui.showToast({ type: 'success', message: '连线已删除' });
            }
        });
    }
    
    /**
     * 切换连线编辑模式
     */
    toggleEdgeEditMode() {
        this.edgeEditMode = !this.edgeEditMode;
        
        // 更新按钮状态
        const btn = document.getElementById('btn-edge-edit');
        if (btn) {
            btn.classList.toggle('active', this.edgeEditMode);
        }
        
        // 重新渲染边线
        this.renderEdges();
        
        this.ui.showToast({ 
            type: 'info', 
            message: this.edgeEditMode ? '进入连线编辑模式，可以选中和删除连线' : '退出连线编辑模式' 
        });
    }

    renderNodeProperties() {
        const mount = document.getElementById('properties-content');
        if (!mount) return;

        if (!this.selectedNode) {
            mount.innerHTML = `
                <div class="dag-properties-empty">
                    <div class="empty-icon">📋</div>
                    <p>选择节点查看属性</p>
                </div>
            `;
            return;
        }

        const node = this.selectedNode;
        
        mount.innerHTML = `
            <div class="dag-property-group">
                <label class="dag-property-label">节点ID</label>
                <input type="text" class="dag-property-input" value="${node.id}" readonly>
            </div>
            
            <div class="dag-property-group">
                <label class="dag-property-label">节点名称</label>
                <input type="text" class="dag-property-input" id="prop-name" value="${node.name}">
            </div>
            
            <div class="dag-property-group">
                <label class="dag-property-label">节点类型</label>
                <select class="dag-property-select" id="prop-type">
                    <option value="start" ${node.type === 'start' ? 'selected' : ''}>开始节点</option>
                    <option value="process" ${node.type === 'process' ? 'selected' : ''}>处理节点</option>
                    <option value="condition" ${node.type === 'condition' ? 'selected' : ''}>条件判断</option>
                    <option value="end" ${node.type === 'end' ? 'selected' : ''}>结束节点</option>
                </select>
            </div>
            
            <div class="dag-property-group">
                <label class="dag-property-label">执行脚本</label>
                <input type="text" class="dag-property-input" id="prop-script" placeholder="输入脚本路径">
            </div>
            
            <div class="dag-property-group">
                <label class="dag-property-label">节点配置</label>
                <textarea class="dag-property-textarea" id="prop-config" placeholder="JSON配置..."></textarea>
            </div>
            
            <div class="dag-property-group">
                <label class="dag-property-toggle">
                    <input type="checkbox" id="prop-enabled" checked>
                    <span class="dag-toggle-slider"></span>
                    <span>启用节点</span>
                </label>
            </div>
            
            <div class="dag-property-actions">
                <button class="dag-control-btn primary" id="btn-save-node">
                    <span>💾</span> 保存
                </button>
                <button class="dag-control-btn danger" id="btn-delete-node">
                    <span>🗑️</span> 删除
                </button>
            </div>
        `;

        // 绑定属性保存和删除
        document.getElementById('btn-save-node')?.addEventListener('click', () => this.saveNodeProperties());
        document.getElementById('btn-delete-node')?.addEventListener('click', () => this.deleteNode());
    }

    saveNodeProperties() {
        if (!this.selectedNode) return;
        
        const name = document.getElementById('prop-name')?.value;
        const type = document.getElementById('prop-type')?.value;
        
        if (name) this.selectedNode.name = name;
        if (type) this.selectedNode.type = type;
        
        this.renderNodes();
        
        // 标记有未保存变更
        this.autoSaveManager.markUnsaved();
        
        this.ui.showToast({ type: 'success', message: '节点属性已保存' });
    }

    deleteNode() {
        if (!this.selectedNode) return;
        
        this.ui.showConfirm({
            title: '删除节点',
            message: `确定要删除节点 "${this.selectedNode.name}" 吗？`,
            type: 'danger',
            confirmText: '删除',
            onConfirm: () => {
                // 删除相关边线
                this.edges = this.edges.filter(e => e.from !== this.selectedNode.id && e.to !== this.selectedNode.id);
                
                // 删除节点
                this.nodes = this.nodes.filter(n => n.id !== this.selectedNode.id);
                
                this.selectedNode = null;
                this.renderNodes();
                this.renderEdges();
                this.renderNodeProperties();
                
                // 标记有未保存变更
                this.autoSaveManager.markUnsaved();
                
                this.ui.showToast({ type: 'success', message: '节点已删除' });
            }
        });
    }

    bindEvents() {
        // 画布拖拽
        this.canvas?.addEventListener('mousedown', (e) => {
            if (e.target === this.canvas || e.target.classList.contains('dag-edges-layer')) {
                this.startCanvasDrag(e);
            }
        });

        // 画布点击 - 清除选中
        this.canvas?.addEventListener('click', (e) => {
            if (e.target === this.canvas || e.target.id === 'dag-edges-layer') {
                this.selectedNode = null;
                this.selectedEdge = null;
                this.renderNodes();
                this.renderEdges();
                this.renderNodeProperties();
            }
        });

        // 画布拖放
        this.canvas?.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        this.canvas?.addEventListener('drop', (e) => {
            e.preventDefault();
            this.handleDrop(e);
        });

        // 全局鼠标事件
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.addEventListener('mouseup', () => this.handleMouseUp());
        
        // 键盘事件 - Delete键删除选中
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                if (this.selectedNode) {
                    this.deleteNode();
                } else if (this.selectedEdge) {
                    this.deleteEdge(this.selectedEdge);
                }
            }
        });
    }

    startCanvasDrag(e) {
        this.isDragging = true;
        this.dragStartX = e.clientX - this.translateX;
        this.dragStartY = e.clientY - this.translateY;
        this.canvas.classList.add('dragging');
    }

    startNodeDrag(e, nodeId) {
        this.isNodeDragging = true;
        this.dragNode = this.nodes.find(n => n.id === nodeId);
        
        if (this.dragNode) {
            const rect = this.canvas.getBoundingClientRect();
            this.dragOffset.x = (e.clientX - rect.left) / this.scale - this.dragNode.x;
            this.dragOffset.y = (e.clientY - rect.top) / this.scale - this.dragNode.y;
            
            // 记录拖拽开始位置（用于撤销）
            this.dragStartPos = { x: this.dragNode.x, y: this.dragNode.y };
        }
    }

    handleMouseMove(e) {
        if (this.isDragging) {
            this.translateX = e.clientX - this.dragStartX;
            this.translateY = e.clientY - this.dragStartY;
            this.updateCanvasTransform();
        }
        
        if (this.isNodeDragging && this.dragNode) {
            const rect = this.canvas.getBoundingClientRect();
            this.dragNode.x = (e.clientX - rect.left) / this.scale - this.dragOffset.x;
            this.dragNode.y = (e.clientY - rect.top) / this.scale - this.dragOffset.y;
            
            // 更新节点位置
            const nodeEl = document.querySelector(`[data-node-id="${this.dragNode.id}"]`);
            if (nodeEl) {
                nodeEl.style.left = `${this.dragNode.x}px`;
                nodeEl.style.top = `${this.dragNode.y}px`;
            }
            
            // 重新渲染边线
            this.renderEdges();
        }
    }

    handleMouseUp() {
        // 如果节点被拖拽，记录移动命令
        if (this.isNodeDragging && this.dragNode && this.dragStartPos) {
            const newPos = { x: this.dragNode.x, y: this.dragNode.y };
            
            // 只有位置真正改变时才记录命令
            if (this.dragStartPos.x !== newPos.x || this.dragStartPos.y !== newPos.y) {
                const command = new MoveNodeCommand(
                    this, 
                    this.dragNode.id, 
                    this.dragStartPos, 
                    newPos
                );
                this.commandManager.execute(command);
                
                // 标记有未保存变更
                this.autoSaveManager.markUnsaved();
            }
        }
        
        this.isDragging = false;
        this.isNodeDragging = false;
        this.dragNode = null;
        this.dragStartPos = null;
        this.canvas?.classList.remove('dragging');
    }

    handleDrop(e) {
        const nodeType = e.dataTransfer.getData('nodeType');
        const nodeShape = e.dataTransfer.getData('nodeShape');
        const nodeName = e.dataTransfer.getData('nodeName');
        const nodeIcon = e.dataTransfer.getData('nodeIcon');
        const nodeColor = e.dataTransfer.getData('nodeColor');
        
        if (!nodeType) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - this.translateX) / this.scale - 60;
        const y = (e.clientY - rect.top - this.translateY) / this.scale - 30;
        
        const newNode = {
            id: `node-${Date.now()}`,
            type: nodeType,
            name: nodeName,
            shape: nodeShape,
            icon: nodeIcon,
            color: nodeColor,
            x: Math.max(0, x),
            y: Math.max(0, y),
            status: 'pending'
        };
        
        // 使用命令模式添加节点
        const command = new AddNodeCommand(this, newNode);
        this.commandManager.execute(command);
        
        // 标记有未保存变更
        this.autoSaveManager.markUnsaved();
        
        this.ui.showToast({ type: 'success', message: `已添加节点: ${nodeName}` });
    }

    updateCanvasTransform() {
        if (this.canvas) {
            this.canvas.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
        }
    }

    zoomIn() {
        this.scale = Math.min(this.scale * 1.2, 3);
        this.updateCanvasTransform();
        this.updateZoomDisplay();
    }

    zoomOut() {
        this.scale = Math.max(this.scale / 1.2, 0.3);
        this.updateCanvasTransform();
        this.updateZoomDisplay();
    }

    zoomFit() {
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.updateCanvasTransform();
        this.updateZoomDisplay();
    }

    updateZoomDisplay() {
        const display = document.getElementById('zoom-level');
        if (display) {
            display.textContent = `${Math.round(this.scale * 100)}%`;
        }
    }

    async saveDAG() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dag/definition`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nodes: this.nodes, edges: this.edges })
            });
            
            if (!response.ok) throw new Error('保存失败');
            
            // 通知自动保存管理器已手动保存
            this.autoSaveManager.onManualSave();
            
            this.ui.showToast({ type: 'success', message: 'DAG已保存' });
        } catch (error) {
            console.error('[DAGPage] 保存失败:', error);
            this.ui.showToast({ type: 'error', message: '保存失败' });
        }
    }

    undo() {
        this.commandManager.undo();
    }

    redo() {
        this.commandManager.redo();
    }

    exportDAG() {
        const dagData = {
            name: 'YL-Monitor DAG',
            version: '1.0.0',
            createdAt: new Date().toISOString(),
            nodes: this.nodes,
            edges: this.edges
        };
        
        const blob = new Blob([JSON.stringify(dagData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'dag-definition.json';
        a.click();
        URL.revokeObjectURL(url);
        
        this.ui.showToast({ type: 'success', message: 'DAG已导出' });
    }

    async runDAG() {
        this.executionStatus = 'running';
        this.executionProgress = 0;
        
        // 更新UI
        document.getElementById('btn-run')?.setAttribute('disabled', 'true');
        document.getElementById('btn-stop')?.removeAttribute('disabled');
        
        const statusBadge = document.getElementById('execution-status');
        if (statusBadge) {
            statusBadge.textContent = '运行中';
            statusBadge.className = 'execution-status-badge running';
        }
        
        // 展开执行面板
        const panel = document.getElementById('dag-execution-panel');
        if (panel) {
            panel.classList.remove('collapsed');
            panel.classList.add('expanded');
        }
        
        // 模拟执行进度
        this.simulateExecution();
        
        try {
            await fetch(`${this.apiBaseUrl}/dag/execute`, { method: 'POST' });
        } catch (error) {
            console.warn('[DAGPage] 执行请求失败:', error);
        }
    }

    simulateExecution() {
        const interval = setInterval(() => {
            if (this.executionStatus !== 'running') {
                clearInterval(interval);
                return;
            }
            
            this.executionProgress += 5;
            
            // 更新进度条
            const fill = document.getElementById('progress-fill');
            const text = document.getElementById('progress-text');
            if (fill) fill.style.width = `${this.executionProgress}%`;
            if (text) text.textContent = `${this.executionProgress}%`;
            
            // 添加日志
            this.addExecutionLog('info', `执行进度: ${this.executionProgress}%`);
            
            if (this.executionProgress >= 100) {
                clearInterval(interval);
                this.executionComplete();
            }
        }, 500);
    }

    executionComplete() {
        this.executionStatus = 'success';
        
        const statusBadge = document.getElementById('execution-status');
        if (statusBadge) {
            statusBadge.textContent = '完成';
            statusBadge.className = 'execution-status-badge success';
        }
        
        document.getElementById('btn-run')?.removeAttribute('disabled');
        document.getElementById('btn-stop')?.setAttribute('disabled', 'true');
        
        this.addExecutionLog('success', 'DAG执行完成');
        this.ui.showToast({ type: 'success', message: 'DAG执行完成' });
    }

    stopDAG() {
        this.executionStatus = 'stopped';
        
        const statusBadge = document.getElementById('execution-status');
        if (statusBadge) {
            statusBadge.textContent = '已停止';
            statusBadge.className = 'execution-status-badge error';
        }
        
        document.getElementById('btn-run')?.removeAttribute('disabled');
        document.getElementById('btn-stop')?.setAttribute('disabled', 'true');
        
        this.addExecutionLog('error', 'DAG执行已停止');
        this.ui.showToast({ type: 'warning', message: 'DAG已停止' });
    }

    addExecutionLog(level, message) {
        const logsContainer = document.getElementById('execution-logs');
        if (!logsContainer) return;
        
        const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        const logItem = document.createElement('div');
        logItem.className = 'execution-log-item';
        logItem.innerHTML = `
            <span class="execution-log-time">${time}</span>
            <span class="execution-log-level ${level}">${level.toUpperCase()}</span>
            <span class="execution-log-message">${message}</span>
        `;
        
        logsContainer.appendChild(logItem);
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    handleAction(action, context, event) {
        switch(action) {
            case 'refresh-dag':
                this.loadDAGData();
                break;
            default:
                console.log('[DAGPage] 未处理的动作:', action);
        }
    }
}
