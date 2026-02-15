/**
 * AR监控页面模块
 * 适配新挂载点架构
 * 版本: v8.0.0
 */

class ARPage {
    constructor(deps) {
        this.apiBaseUrl = '/api/v1';
        this.deps = deps;
        this.arNodes = [];
        this.arWs = null;
        
        // 挂载点引用
        this.mounts = {
            sidebar: document.getElementById('sidebar-mount'),
            mainContent: document.getElementById('main-content-mount')
        };
    }

    /**
     * 初始化页面
     */
    async init() {
        console.log('[ARPage] 初始化AR监控页面...');
        
        // 1. 渲染侧边栏
        this.renderSidebar();
        
        // 2. 渲染主内容区
        this.renderMainContent();
        
        // 3. 加载AR节点数据
        await this.loadARNodes();
        
        // 4. 连接WebSocket
        this.connectARWebSocket();
        
        // 5. 绑定事件
        this.bindEvents();
        
        console.log('[ARPage] AR监控页面初始化完成 ✅');
    }

    /**
     * 渲染侧边栏
     */
    renderSidebar() {
        if (!this.mounts.sidebar) return;
        
        this.mounts.sidebar.innerHTML = `
            <div class="ar-sidebar">
                <!-- 节点列表 -->
                <div class="ar-nodes-section">
                    <div class="ar-nodes-header">
                        <span>🥽</span>
                        <span>AR 节点</span>
                    </div>
                    <ul id="ar-nodes-list" class="ar-nodes-list">
                        <li class="ar-node-item loading">
                            <span class="loading-spinner"></span>
                            <span>加载节点中...</span>
                        </li>
                    </ul>
                </div>
                
                <!-- 资源监控 -->
                <div class="ar-resources-section">
                    <div class="ar-resources-title">
                        <span>📊</span>
                        <span>资源监控</span>
                    </div>
                    <div class="resource-monitor">
                        <div class="resource-item">
                            <div class="resource-header">
                                <div class="resource-label">
                                    <span class="resource-icon cpu">CPU</span>
                                    <span>处理器</span>
                                </div>
                                <span id="cpu-value" class="resource-value">0%</span>
                            </div>
                            <div class="resource-progress-bar">
                                <div id="cpu-fill" class="resource-progress-fill cpu" style="width: 0%"></div>
                            </div>
                        </div>
                        <div class="resource-item">
                            <div class="resource-header">
                                <div class="resource-label">
                                    <span class="resource-icon memory">MEM</span>
                                    <span>内存</span>
                                </div>
                                <span id="memory-value" class="resource-value">0%</span>
                            </div>
                            <div class="resource-progress-bar">
                                <div id="memory-fill" class="resource-progress-fill memory" style="width: 0%"></div>
                            </div>
                        </div>
                        <div class="resource-item">
                            <div class="resource-header">
                                <div class="resource-label">
                                    <span class="resource-icon gpu">GPU</span>
                                    <span>显卡</span>
                                </div>
                                <span id="gpu-value" class="resource-value">0%</span>
                            </div>
                            <div class="resource-progress-bar">
                                <div id="gpu-fill" class="resource-progress-fill gpu" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 控制按钮 -->
                <div class="ar-controls-section">
                    <button class="ar-control-btn start" data-action="start-ar">
                        <span>▶</span>
                        <span>启动场景</span>
                    </button>
                    <button class="ar-control-btn stop" data-action="stop-ar">
                        <span>⏹</span>
                        <span>停止场景</span>
                    </button>
                    <button class="ar-control-btn refresh" data-action="refresh-ar">
                        <span>🔄</span>
                        <span>刷新状态</span>
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 渲染主内容区
     */
    renderMainContent() {
        if (!this.mounts.mainContent) return;
        
        this.mounts.mainContent.innerHTML = `
            <div class="ar-main">
                <!-- 页面头部 -->
                <div class="ar-page-header">
                    <div class="ar-title-section">
                        <div class="ar-icon">🥽</div>
                        <div>
                            <h2 class="ar-title">AR 监控</h2>
                            <p class="ar-subtitle">增强现实节点管理与可视化</p>
                        </div>
                    </div>
                    <div class="ar-header-actions">
                        <button class="btn btn-secondary" data-action="refresh-ar">
                            <span>🔄</span>
                            <span>刷新</span>
                        </button>
                        <button class="btn btn-secondary" data-action="settings-ar">
                            <span>⚙️</span>
                            <span>设置</span>
                        </button>
                    </div>
                </div>
                
                <!-- 统计卡片 -->
                <div class="ar-stats-grid">
                    <div class="ar-stat-card">
                        <div class="ar-stat-icon total">📊</div>
                        <div class="ar-stat-info">
                            <div id="total-nodes" class="ar-stat-value">0</div>
                            <div class="ar-stat-label">总节点数</div>
                        </div>
                    </div>
                    <div class="ar-stat-card">
                        <div class="ar-stat-icon online">✓</div>
                        <div class="ar-stat-info">
                            <div id="online-nodes" class="ar-stat-value online">0</div>
                            <div class="ar-stat-label">在线节点</div>
                        </div>
                    </div>
                    <div class="ar-stat-card">
                        <div class="ar-stat-icon offline">✗</div>
                        <div class="ar-stat-info">
                            <div id="offline-nodes" class="ar-stat-value offline">0</div>
                            <div class="ar-stat-label">离线节点</div>
                        </div>
                    </div>
                </div>
                
                <!-- AR可视化区域 -->
                <div class="ar-visualization-section">
                    <div class="ar-visualization-header">
                        <div class="ar-visualization-title">
                            <span>🎬</span>
                            <span>AR 场景可视化</span>
                        </div>
                        <div class="ar-scene-status">
                            <span class="status-dot" id="scene-status-dot"></span>
                            <span id="scene-status" class="status-badge-ar idle">状态: 空闲</span>
                        </div>
                    </div>
                    <div class="ar-visualization-container" id="ar-visualization">
                        <div class="ar-empty-state">
                            <div class="ar-empty-icon">🥽</div>
                            <div class="ar-empty-title">AR 场景监控</div>
                            <div class="ar-empty-description">实时显示 AR 节点状态和资源使用情况</div>
                            <button class="btn btn-primary mt-4" data-action="start-ar">
                                <span>▶</span>
                                <span>启动场景</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 加载AR节点
     */
    async loadARNodes() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/ar/nodes`);
            if (!response.ok) throw new Error('获取AR节点失败');
            
            const data = await response.json();
            this.arNodes = data.nodes || [];
            
            this.renderARNodes(this.arNodes);
            this.updateARStats(this.arNodes);
            
        } catch (error) {
            console.error('[ARPage] 加载AR节点失败:', error);
            this.deps.uiComponents.showToast({
                type: 'error',
                message: '加载AR节点失败'
            });
            
            // 显示空状态
            const list = document.getElementById('ar-nodes-list');
            if (list) {
                list.innerHTML = '<li class="empty-item">暂无AR节点</li>';
            }
        }
    }

    /**
     * 渲染AR节点列表
     */
    renderARNodes(nodes) {
        const list = document.getElementById('ar-nodes-list');
        if (!list) return;
        
        if (nodes.length === 0) {
            list.innerHTML = '<li class="ar-node-item empty"><span>暂无AR节点</span></li>';
            return;
        }
        
        list.innerHTML = nodes.map(node => `
            <li class="ar-node-item" data-node-id="${node.id}" data-action="select-node">
                <span class="node-status-indicator ${node.status}"></span>
                <div class="node-info">
                    <div class="node-name">${node.name}</div>
                    <div class="node-meta">${node.ip_address || 'N/A'}</div>
                </div>
                <span class="node-status-text ${node.status}">${this.getARNodeStatusText(node.status)}</span>
            </li>
        `).join('');
        
        // 绑定节点选择事件
        list.querySelectorAll('[data-action="select-node"]').forEach(item => {
            item.addEventListener('click', () => {
                const nodeId = item.dataset.nodeId;
                this.selectNode(nodeId);
            });
        });
    }

    /**
     * 更新AR统计
     */
    updateARStats(nodes) {
        const total = nodes.length;
        const online = nodes.filter(n => n.status === 'online').length;
        const offline = total - online;
        
        const totalEl = document.getElementById('total-nodes');
        const onlineEl = document.getElementById('online-nodes');
        const offlineEl = document.getElementById('offline-nodes');
        
        if (totalEl) totalEl.textContent = total;
        if (onlineEl) onlineEl.textContent = online;
        if (offlineEl) offlineEl.textContent = offline;
    }

    /**
     * 选择节点
     */
    selectNode(nodeId) {
        const node = this.arNodes.find(n => n.id === nodeId);
        if (!node) return;
        
        const panel = document.getElementById('node-details-panel');
        const content = document.getElementById('node-details-content');
        
        if (!panel || !content) return;
        
        content.innerHTML = `
            <div class="node-details">
                <div class="detail-row">
                    <span class="detail-label">节点名称</span>
                    <span class="detail-value">${node.name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">IP地址</span>
                    <span class="detail-value">${node.ip_address || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">状态</span>
                    <span class="detail-value">
                        <span class="status-badge status-${node.status}">
                            ${this.getARNodeStatusText(node.status)}
                        </span>
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">最后在线</span>
                    <span class="detail-value">${node.last_seen || '未知'}</span>
                </div>
                <div class="detail-actions mt-4">
                    <button class="btn btn-primary btn-sm" data-action="refresh-node" data-node-id="${node.id}">
                        刷新状态
                    </button>
                    <button class="btn btn-secondary btn-sm" data-action="view-logs" data-node-id="${node.id}">
                        查看日志
                    </button>
                </div>
            </div>
        `;
        
        panel.style.display = 'block';
        
        // 高亮选中的节点
        document.querySelectorAll('#ar-nodes-list .nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.nodeId === nodeId);
        });
    }

    /**
     * 连接AR WebSocket
     */
    connectARWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/ar`;
        
        this.arWs = new WebSocket(wsUrl);
        
        this.arWs.onopen = () => {
            console.log('[ARPage] WebSocket已连接');
            this.deps.uiComponents.showToast({
                type: 'success',
                message: 'AR监控已连接'
            });
        };
        
        this.arWs.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('[ARPage] WebSocket消息解析失败:', error);
            }
        };
        
        this.arWs.onclose = () => {
            console.log('[ARPage] WebSocket已断开，3秒后重连...');
            setTimeout(() => this.connectARWebSocket(), 3000);
        };
        
        this.arWs.onerror = (error) => {
            console.error('[ARPage] WebSocket错误:', error);
        };
    }

    /**
     * 处理WebSocket消息
     */
    handleWebSocketMessage(data) {
        if (data.type === 'ar_status') {
            if (data.nodes) {
                this.arNodes = data.nodes;
                this.renderARNodes(this.arNodes);
                this.updateARStats(this.arNodes);
            }
            if (data.resources) {
                this.updateResourceBars(data.resources);
            }
        }
    }

    /**
     * 更新资源条
     */
    updateResourceBars(resources) {
        const cpu = resources.cpu || 0;
        const memory = resources.memory || 0;
        const gpu = resources.gpu || 0;
        
        const cpuValue = document.getElementById('cpu-value');
        const cpuFill = document.getElementById('cpu-fill');
        const memoryValue = document.getElementById('memory-value');
        const memoryFill = document.getElementById('memory-fill');
        const gpuValue = document.getElementById('gpu-value');
        const gpuFill = document.getElementById('gpu-fill');
        
        if (cpuValue) cpuValue.textContent = `${cpu}%`;
        if (cpuFill) cpuFill.style.width = `${cpu}%`;
        
        if (memoryValue) memoryValue.textContent = `${memory}%`;
        if (memoryFill) memoryFill.style.width = `${memory}%`;
        
        if (gpuValue) gpuValue.textContent = `${gpu}%`;
        if (gpuFill) gpuFill.style.width = `${gpu}%`;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 全局点击事件委托
        document.addEventListener('click', (e) => {
            const actionEl = e.target.closest('[data-action]');
            if (!actionEl) return;
            
            const action = actionEl.dataset.action;
            this.handleAction(action, actionEl);
        });
    }

    /**
     * 处理动作
     */
    handleAction(action, element) {
        switch(action) {
            case 'refresh-ar':
                this.refreshAR();
                break;
            case 'start-ar':
                this.startARScene();
                break;
            case 'stop-ar':
                this.stopARScene();
                break;
            case 'settings-ar':
                this.openSettings();
                break;
            case 'close-details':
            case 'close-modal':
                this.closeNodeDetails();
                break;
            case 'refresh-node':
                const nodeId = element.dataset.nodeId;
                this.refreshNode(nodeId);
                break;
            case 'view-logs':
                const logNodeId = element.dataset.nodeId;
                this.viewNodeLogs(logNodeId);
                break;
        }
    }

    /**
     * 刷新AR
     */
    async refreshAR() {
        await this.loadARNodes();
        this.deps.uiComponents.showToast({
            type: 'success',
            message: '已刷新AR节点状态'
        });
    }

    /**
     * 启动AR场景
     */
    startARScene() {
        const statusEl = document.getElementById('scene-status');
        const statusDot = document.getElementById('scene-status-dot');
        const vizContainer = document.getElementById('ar-visualization');
        
        if (statusEl) {
            statusEl.textContent = '状态: 渲染中';
            statusEl.className = 'status-badge-ar rendering';
        }
        
        if (statusDot) {
            statusDot.className = 'status-dot busy';
        }
        
        if (vizContainer) {
            vizContainer.innerHTML = `
                <div class="ar-rendering-state">
                    <div class="ar-rendering-spinner"></div>
                    <div class="ar-rendering-text">AR场景渲染中...</div>
                    <div class="ar-rendering-subtext">正在连接AR节点</div>
                </div>
            `;
        }
        
        this.deps.uiComponents.showToast({
            type: 'info',
            message: '正在启动AR场景...'
        });
        
        // 模拟启动过程
        setTimeout(() => {
            this.renderAR3DScene();
            
            if (statusEl) {
                statusEl.textContent = '状态: 运行中';
                statusEl.className = 'status-badge-ar running';
            }
            if (statusDot) {
                statusDot.className = 'status-dot online pulse';
            }
            this.deps.uiComponents.showToast({
                type: 'success',
                message: 'AR场景已启动'
            });
        }, 2000);
    }

    /**
     * 停止AR场景
     */
    stopARScene() {
        const statusEl = document.getElementById('scene-status');
        const statusDot = document.getElementById('scene-status-dot');
        const vizContainer = document.getElementById('ar-visualization');
        
        if (statusEl) {
            statusEl.textContent = '状态: 空闲';
            statusEl.className = 'status-badge-ar idle';
        }
        
        if (statusDot) {
            statusDot.className = 'status-dot offline';
        }
        
        if (vizContainer) {
            vizContainer.innerHTML = `
                <div class="ar-empty-state">
                    <div class="ar-empty-icon">🥽</div>
                    <div class="ar-empty-title">AR 场景监控</div>
                    <div class="ar-empty-description">实时显示 AR 节点状态和资源使用情况</div>
                    <button class="btn btn-primary mt-4" data-action="start-ar">
                        <span>▶</span>
                        <span>启动场景</span>
                    </button>
                </div>
            `;
        }
        
        this.deps.uiComponents.showToast({
            type: 'info',
            message: 'AR场景已停止'
        });
    }

    /**
     * 打开设置
     */
    openSettings() {
        this.deps.uiComponents.showToast({
            type: 'info',
            message: '设置功能开发中...'
        });
    }

    /**
     * 关闭节点详情
     */
    closeNodeDetails() {
        this.closeNodeModal();
    }
    
    /**
     * 关闭节点详情弹窗
     */
    closeNodeModal() {
        const modal = document.getElementById('ar-node-modal');
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => modal.remove(), 300);
        }
        
        // 取消高亮
        document.querySelectorAll('#ar-nodes-list .ar-node-item').forEach(item => {
            item.classList.remove('active');
        });
    }
    
    /**
     * 渲染3D AR场景
     */
    renderAR3DScene() {
        const vizContainer = document.getElementById('ar-visualization');
        if (!vizContainer) return;
        
        // 获取节点状态
        const nodes = this.arNodes.length > 0 ? this.arNodes : [
            { id: 'ar-1', name: 'AR-01', status: 'online' },
            { id: 'ar-2', name: 'AR-02', status: 'online' },
            { id: 'ar-3', name: 'AR-03', status: 'busy' },
            { id: 'ar-4', name: 'AR-04', status: 'offline' }
        ];
        
        vizContainer.innerHTML = `
            <div class="ar-3d-scene">
                <div class="ar-nodes-3d">
                    ${nodes.map(node => `
                        <div class="ar-node-3d ${node.status}" data-node-id="${node.id}">
                            <span class="ar-node-3d-icon">🥽</span>
                            <span class="ar-node-3d-label">${node.name}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="ar-video-preview">
                    <div class="ar-video-preview-header">
                        <span class="status-dot online pulse"></span>
                        <span>实时预览</span>
                    </div>
                    <div class="ar-video-preview-content">
                        <span>视频流 (模拟)</span>
                    </div>
                </div>
            </div>
        `;
        
        // 绑定节点点击事件
        vizContainer.querySelectorAll('.ar-node-3d').forEach(nodeEl => {
            nodeEl.addEventListener('click', () => {
                const nodeId = nodeEl.dataset.nodeId;
                const node = this.arNodes.find(n => n.id === nodeId) || 
                    nodes.find(n => n.id === nodeId);
                if (node) {
                    this.showNodeModal(node);
                }
            });
        });
    }
    
    /**
     * 显示节点详情弹窗
     */
    showNodeModal(node) {
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'ar-node-modal';
        modal.id = 'ar-node-modal';
        modal.innerHTML = `
            <div class="ar-node-modal-content">
                <div class="ar-node-modal-header">
                    <div class="ar-node-modal-title">
                        <span class="node-status-indicator ${node.status}"></span>
                        <span>${node.name}</span>
                    </div>
                    <button class="btn btn-sm btn-ghost" data-action="close-modal">×</button>
                </div>
                <div class="ar-node-modal-body">
                    <div class="ar-node-details-grid">
                        <div class="ar-detail-item">
                            <span class="ar-detail-label">节点ID</span>
                            <span class="ar-detail-value">${node.id}</span>
                        </div>
                        <div class="ar-detail-item">
                            <span class="ar-detail-label">IP地址</span>
                            <span class="ar-detail-value">${node.ip_address || 'N/A'}</span>
                        </div>
                        <div class="ar-detail-item">
                            <span class="ar-detail-label">状态</span>
                            <span class="ar-detail-value status-${node.status}">${this.getARNodeStatusText(node.status)}</span>
                        </div>
                        <div class="ar-detail-item">
                            <span class="ar-detail-label">最后在线</span>
                            <span class="ar-detail-value">${node.last_seen || '未知'}</span>
                        </div>
                    </div>
                    
                    <div class="ar-resource-details">
                        <div class="ar-resource-details-title">
                            <span>📊</span>
                            <span>资源使用趋势</span>
                        </div>
                        <div class="ar-resource-chart">
                            <span>资源使用图表 (开发中)</span>
                        </div>
                    </div>
                    
                    <div class="flex gap-2 mt-4">
                        <button class="btn btn-primary" data-action="refresh-node" data-node-id="${node.id}">
                            🔄 刷新状态
                        </button>
                        <button class="btn btn-secondary" data-action="view-logs" data-node-id="${node.id}">
                            📋 查看日志
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 显示动画
        requestAnimationFrame(() => {
            modal.classList.add('active');
        });
        
        // 绑定关闭事件
        modal.querySelector('[data-action="close-modal"]').addEventListener('click', () => {
            this.closeNodeModal();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeNodeModal();
            }
        });
    }

    /**
     * 刷新节点
     */
    async refreshNode(nodeId) {
        this.deps.uiComponents.showToast({
            type: 'info',
            message: `正在刷新节点 ${nodeId}...`
        });
        
        // 重新加载所有节点
        await this.loadARNodes();
        
        // 如果当前选中的节点是刷新的节点，更新详情
        const panel = document.getElementById('node-details-panel');
        if (panel && panel.style.display !== 'none') {
            this.selectNode(nodeId);
        }
    }

    /**
     * 查看节点日志
     */
    viewNodeLogs(nodeId) {
        this.deps.uiComponents.showToast({
            type: 'info',
            message: `查看节点 ${nodeId} 日志功能开发中...`
        });
    }

    /**
     * 获取节点状态文本
     */
    getARNodeStatusText(status) {
        const statusMap = {
            'online': '在线',
            'offline': '离线',
            'busy': '繁忙',
            'error': '错误'
        };
        return statusMap[status] || status || '未知';
    }
}

// 导出页面类
export default ARPage;
