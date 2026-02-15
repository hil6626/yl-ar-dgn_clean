/**
 * YL-Monitor 脚本管理器
 * 提供脚本分类展示、执行控制、批量操作功能
 * 版本: v1.0.0
 */

class ScriptsManager {
    constructor() {
        this.scripts = [];
        this.categories = [];
        this.selectedScripts = new Set();
        this.currentCategory = 'all';
        this.ws = null;
        this.searchQuery = '';
        this.sortBy = 'name';
        
        // DOM 元素
        this.elements = {
            header: document.getElementById('scripts-header'),
            filterBar: document.getElementById('scripts-filter-bar'),
            batchToolbar: document.getElementById('scripts-batch-toolbar'),
            grid: document.getElementById('scripts-grid'),
            stats: document.getElementById('scripts-stats'),
            logsModal: document.getElementById('logs-modal'),
            logsContainer: document.getElementById('logs-container'),
            closeLogsModal: document.getElementById('close-logs-modal')
        };
        
        this.init();
    }
    
    async init() {
        console.log('[ScriptsManager] 初始化脚本管理器...');
        
        // 初始化 WebSocket
        this.initWebSocket();
        
        // 加载数据
        await this.loadCategories();
        await this.loadScripts();
        
        // 渲染页面
        this.renderHeader();
        this.renderFilterBar();
        this.renderScriptsGrid();
        this.renderStats();
        
        // 绑定事件
        this.bindEvents();
        
        console.log('[ScriptsManager] 初始化完成');
    }
    
    /**
     * 初始化 WebSocket 连接
     */
    initWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/scripts`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('[ScriptsManager] WebSocket 已连接');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('[ScriptsManager] WebSocket 已断开，5秒后重连...');
            setTimeout(() => this.initWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            console.error('[ScriptsManager] WebSocket 错误:', error);
        };
    }
    
    /**
     * 处理 WebSocket 消息
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'script_update':
                this.updateScriptCard(data.script_id, data.data);
                break;
            case 'execution_update':
                this.updateExecutionStatus(data);
                break;
            case 'log':
                this.appendLog(data.execution_id, data.message);
                break;
            case 'all_scripts_status':
                this.updateAllScriptsStatus(data.scripts);
                break;
        }
    }
    
    /**
     * 加载脚本分类
     */
    async loadCategories() {
        try {
            const response = await fetch('/api/v1/scripts/categories');
            this.categories = await response.json();
            console.log(`[ScriptsManager] 加载了 ${this.categories.length} 个分类`);
        } catch (error) {
            console.error('[ScriptsManager] 加载分类失败:', error);
            this.categories = [];
        }
    }
    
    /**
     * 加载脚本列表
     */
    async loadScripts() {
        try {
            const url = this.currentCategory === 'all' 
                ? '/api/v1/scripts' 
                : `/api/v1/scripts?category=${this.currentCategory}`;
            
            const response = await fetch(url);
            this.scripts = await response.json();
            console.log(`[ScriptsManager] 加载了 ${this.scripts.length} 个脚本`);
        } catch (error) {
            console.error('[ScriptsManager] 加载脚本失败:', error);
            this.scripts = [];
        }
    }
    
    /**
     * 渲染页面头部
     */
    renderHeader() {
        this.elements.header.innerHTML = `
            <div class="scripts-title-section">
                <div>
                    <h2>脚本管理</h2>
                    <div class="scripts-subtitle">自动化控制中心 • 共 ${this.scripts.length} 个脚本</div>
                </div>
            </div>
            <div class="scripts-actions">
                <button class="btn btn-primary" id="refresh-scripts">
                    <span>🔄</span> 刷新
                </button>
                <button class="btn btn-secondary" id="view-stats">
                    <span>📊</span> 统计
                </button>
            </div>
        `;
    }
    
    /**
     * 渲染筛选栏
     */
    renderFilterBar() {
        const categoryTabs = this.categories.map(cat => `
            <button class="filter-tab ${this.currentCategory === cat.id ? 'active' : ''}" 
                    data-category="${cat.id}">
                <span>${cat.icon}</span> ${cat.name}
                <span class="count">${cat.script_count}</span>
            </button>
        `).join('');
        
        this.elements.filterBar.innerHTML = `
            <div class="filter-section">
                <span class="filter-label">分类筛选</span>
                <div class="filter-tabs">
                    <button class="filter-tab ${this.currentCategory === 'all' ? 'active' : ''}" 
                            data-category="all">
                        <span>📁</span> 全部
                        <span class="count">${this.scripts.length}</span>
                    </button>
                    ${categoryTabs}
                </div>
            </div>
            <div class="filter-section">
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="script-search" 
                           placeholder="搜索脚本..." 
                           value="${this.searchQuery}">
                </div>
                <select class="sort-select" id="sort-select">
                    <option value="name" ${this.sortBy === 'name' ? 'selected' : ''}>按名称</option>
                    <option value="status" ${this.sortBy === 'status' ? 'selected' : ''}>按状态</option>
                    <option value="executions" ${this.sortBy === 'executions' ? 'selected' : ''}>按执行次数</option>
                </select>
            </div>
        `;
    }
    
    /**
     * 渲染脚本卡片网格
     */
    renderScriptsGrid() {
        if (this.scripts.length === 0) {
            this.elements.grid.innerHTML = `
                <div class="scripts-empty-state">
                    <div class="empty-icon">📭</div>
                    <div class="empty-title">暂无脚本</div>
                    <div class="empty-description">该分类下没有脚本，请尝试其他分类</div>
                </div>
            `;
            return;
        }
        
        // 过滤和排序
        let filteredScripts = this.filterScripts();
        filteredScripts = this.sortScripts(filteredScripts);
        
        const cardsHtml = filteredScripts.map(script => this.createScriptCard(script)).join('');
        
        this.elements.grid.innerHTML = cardsHtml;
        
        // 更新批量工具栏
        this.updateBatchToolbar();
    }
    
    /**
     * 创建脚本卡片 HTML
     */
    createScriptCard(script) {
        const status = script.status || {};
        const isRunning = status.is_running;
        const isSelected = this.selectedScripts.has(script.id);
        
        // 状态样式
        const statusClass = isRunning ? 'running' : 
                           (status.current_status === 'success' ? 'stopped' : 
                           (status.current_status === 'error' ? 'error' : 'stopped'));
        const statusText = isRunning ? '运行中' : 
                          (status.current_status === 'success' ? '空闲' : 
                          (status.current_status === 'error' ? '失败' : '空闲'));
        
        // 分类图标映射
        const categoryIcons = {
            'system-monitor': '🔍',
            'service-monitor': '🌐',
            'ar-monitor': '🎥',
            'resource-optimizer': '🧹',
            'service-optimizer': '⚡',
            'maintenance-backup': '💾',
            'maintenance-health': '🏥',
            'maintenance-cleanup': '🧽',
            'alert-handler': '🚨',
            'tools': '🛠️',
            'core': '🔧'
        };
        
        const icon = categoryIcons[script.category] || '📄';
        
        return `
            <div class="script-card ${isSelected ? 'selected' : ''}" data-script-id="${script.id}">
                <div class="script-card-header">
                    <div class="script-card-title">
                        <input type="checkbox" class="script-checkbox" 
                               ${isSelected ? 'checked' : ''} 
                               data-script-id="${script.id}">
                        <div class="script-icon">${icon}</div>
                        <div class="script-info">
                            <h4 class="script-name">${script.name}</h4>
                            <div class="script-path">${script.filename}</div>
                        </div>
                    </div>
                    <div class="script-status ${statusClass}">
                        <span>${statusText}</span>
                    </div>
                </div>
                
                <div class="script-description">${script.description || '暂无描述'}</div>
                
                <div class="script-meta">
                    <div class="meta-item">
                        <span class="meta-label">类型</span>
                        <span class="meta-value">${script.script_type || '未知'}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">执行次数</span>
                        <span class="meta-value">${status.execution_count || 0}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">成功率</span>
                        <span class="meta-value">
                            ${status.execution_count > 0 
                                ? Math.round((status.success_count / status.execution_count) * 100) 
                                : 0}%
                        </span>
                    </div>
                </div>
                
                <div class="script-stats">
                    <div class="stat-item">
                        <span class="stat-icon success">✓</span>
                        <span>${status.success_count || 0} 成功</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-icon danger">✗</span>
                        <span>${status.fail_count || 0} 失败</span>
                    </div>
                    ${status.last_execution ? `
                    <div class="stat-item">
                        <span>🕐</span>
                        <span>${this.formatTime(status.last_execution)}</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="script-actions">
                    ${isRunning ? `
                        <button class="btn btn-danger btn-sm stop-script" data-script-id="${script.id}">
                            <span>⏹</span> 停止
                        </button>
                    ` : `
                        <button class="btn btn-primary btn-sm execute-script" data-script-id="${script.id}">
                            <span>▶</span> 执行
                        </button>
                    `}
                    <button class="btn btn-secondary btn-sm view-history" data-script-id="${script.id}">
                        <span>📊</span> 历史
                    </button>
                    <button class="btn btn-ghost btn-sm view-logs" data-script-id="${script.id}">
                        <span>📋</span> 日志
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * 过滤脚本
     */
    filterScripts() {
        if (!this.searchQuery) return this.scripts;
        
        const query = this.searchQuery.toLowerCase();
        return this.scripts.filter(script => 
            script.name.toLowerCase().includes(query) ||
            (script.description && script.description.toLowerCase().includes(query)) ||
            script.filename.toLowerCase().includes(query)
        );
    }
    
    /**
     * 排序脚本
     */
    sortScripts(scripts) {
        switch (this.sortBy) {
            case 'name':
                return scripts.sort((a, b) => a.name.localeCompare(b.name));
            case 'status':
                return scripts.sort((a, b) => {
                    const statusA = a.status?.is_running ? 2 : (a.status?.current_status === 'error' ? 1 : 0);
                    const statusB = b.status?.is_running ? 2 : (b.status?.current_status === 'error' ? 1 : 0);
                    return statusB - statusA;
                });
            case 'executions':
                return scripts.sort((a, b) => 
                    (b.status?.execution_count || 0) - (a.status?.execution_count || 0)
                );
            default:
                return scripts;
        }
    }
    
    /**
     * 渲染统计区域
     */
    renderStats() {
        const totalScripts = this.scripts.length;
        const runningScripts = this.scripts.filter(s => s.status?.is_running).length;
        const totalExecutions = this.scripts.reduce((sum, s) => sum + (s.status?.execution_count || 0), 0);
        const successRate = totalExecutions > 0 
            ? Math.round((this.scripts.reduce((sum, s) => sum + (s.status?.success_count || 0), 0) / totalExecutions) * 100)
            : 0;
        
        this.elements.stats.innerHTML = `
            <div class="stats-header">
                <h3>执行统计</h3>
                <button class="btn btn-ghost btn-sm" id="refresh-stats">🔄 刷新</button>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-value">${totalScripts}</div>
                    <div class="stat-card-label">总脚本数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value" style="color: ${runningScripts > 0 ? 'var(--primary-500)' : 'inherit'}">
                        ${runningScripts}
                    </div>
                    <div class="stat-card-label">运行中</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${totalExecutions}</div>
                    <div class="stat-card-label">总执行次数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value" style="color: ${successRate >= 90 ? 'var(--success)' : (successRate >= 70 ? 'var(--warning)' : 'var(--danger)')}">
                        ${successRate}%
                    </div>
                    <div class="stat-card-label">成功率</div>
                </div>
            </div>
        `;
    }
    
    /**
     * 更新批量工具栏
     */
    updateBatchToolbar() {
        const selectedCount = this.selectedScripts.size;
        
        if (selectedCount === 0) {
            this.elements.batchToolbar.classList.add('hidden');
            return;
        }
        
        this.elements.batchToolbar.classList.remove('hidden');
        this.elements.batchToolbar.innerHTML = `
            <div class="batch-info">
                已选择 <strong>${selectedCount}</strong> 个脚本
            </div>
            <div class="batch-actions">
                <button class="btn btn-success btn-sm" id="batch-execute">
                    <span>▶</span> 执行选中
                </button>
                <button class="btn btn-danger btn-sm" id="batch-stop">
                    <span>⏹</span> 停止选中
                </button>
                <button class="btn btn-secondary btn-sm" id="clear-selection">
                    <span>✕</span> 清除选择
                </button>
            </div>
        `;
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 分类筛选
        this.elements.filterBar.addEventListener('click', (e) => {
            if (e.target.closest('.filter-tab')) {
                const tab = e.target.closest('.filter-tab');
                const category = tab.dataset.category;
                this.switchCategory(category);
            }
        });
        
        // 搜索
        const searchInput = document.getElementById('script-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value;
                this.renderScriptsGrid();
            });
        }
        
        // 排序
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.renderScriptsGrid();
            });
        }
        
        // 脚本卡片操作
        this.elements.grid.addEventListener('click', (e) => {
            // 复选框
            if (e.target.classList.contains('script-checkbox')) {
                const scriptId = e.target.dataset.scriptId;
                if (e.target.checked) {
                    this.selectedScripts.add(scriptId);
                } else {
                    this.selectedScripts.delete(scriptId);
                }
                this.renderScriptsGrid();
            }
            
            // 执行按钮
            if (e.target.closest('.execute-script')) {
                const scriptId = e.target.closest('.execute-script').dataset.scriptId;
                this.executeScript(scriptId);
            }
            
            // 停止按钮
            if (e.target.closest('.stop-script')) {
                const scriptId = e.target.closest('.stop-script').dataset.scriptId;
                this.stopScript(scriptId);
            }
            
            // 历史按钮
            if (e.target.closest('.view-history')) {
                const scriptId = e.target.closest('.view-history').dataset.scriptId;
                this.viewHistory(scriptId);
            }
            
            // 日志按钮
            if (e.target.closest('.view-logs')) {
                const scriptId = e.target.closest('.view-logs').dataset.scriptId;
                this.viewLogs(scriptId);
            }
        });
        
        // 批量操作
        this.elements.batchToolbar.addEventListener('click', (e) => {
            if (e.target.closest('#batch-execute')) {
                this.batchExecute();
            }
            if (e.target.closest('#batch-stop')) {
                this.batchStop();
            }
            if (e.target.closest('#clear-selection')) {
                this.clearSelection();
            }
        });
        
        // 头部按钮
        this.elements.header.addEventListener('click', (e) => {
            if (e.target.closest('#refresh-scripts')) {
                this.refresh();
            }
        });
        
        // 关闭日志模态框
        this.elements.closeLogsModal.addEventListener('click', () => {
            this.elements.logsModal.classList.add('hidden');
        });
        
        // 点击模态框背景关闭
        this.elements.logsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.logsModal) {
                this.elements.logsModal.classList.add('hidden');
            }
        });
    }
    
    /**
     * 切换分类
     */
    async switchCategory(category) {
        this.currentCategory = category;
        this.selectedScripts.clear();
        await this.loadScripts();
        this.renderFilterBar();
        this.renderScriptsGrid();
        this.renderStats();
    }
    
    /**
     * 执行脚本
     */
    async executeScript(scriptId) {
        try {
            const response = await fetch(`/api/v1/scripts/${scriptId}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`脚本执行已启动: ${result.script_name}`, 'success');
                // 刷新状态
                setTimeout(() => this.refresh(), 1000);
            } else {
                this.showToast(`执行失败: ${result.message || '未知错误'}`, 'error');
            }
        } catch (error) {
            console.error('执行脚本失败:', error);
            this.showToast('执行失败，请检查网络连接', 'error');
        }
    }
    
    /**
     * 停止脚本
     */
    async stopScript(scriptId) {
        try {
            const response = await fetch(`/api/v1/scripts/${scriptId}/stop`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('脚本已停止', 'success');
                setTimeout(() => this.refresh(), 500);
            } else {
                this.showToast('停止失败', 'error');
            }
        } catch (error) {
            console.error('停止脚本失败:', error);
            this.showToast('停止失败，请检查网络连接', 'error');
        }
    }
    
    /**
     * 批量执行
     */
    async batchExecute() {
        if (this.selectedScripts.size === 0) return;
        
        const scriptIds = Array.from(this.selectedScripts);
        
        try {
            const response = await fetch('/api/v1/scripts/batch-execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    script_ids: scriptIds,
                    parallel: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`已启动 ${scriptIds.length} 个脚本的执行`, 'success');
                this.clearSelection();
                setTimeout(() => this.refresh(), 1000);
            } else {
                this.showToast(`批量执行失败: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('批量执行失败:', error);
            this.showToast('批量执行失败', 'error');
        }
    }
    
    /**
     * 批量停止
     */
    async batchStop() {
        // 简化处理：逐个停止
        const promises = Array.from(this.selectedScripts).map(id => this.stopScript(id));
        await Promise.all(promises);
        this.clearSelection();
    }
    
    /**
     * 清除选择
     */
    clearSelection() {
        this.selectedScripts.clear();
        this.renderScriptsGrid();
    }
    
    /**
     * 查看历史
     */
    async viewHistory(scriptId) {
        try {
            const response = await fetch(`/api/v1/scripts/${scriptId}/history?limit=10`);
            const history = await response.json();
            
            // 显示在历史模态框中
            this.showHistoryModal(history);
        } catch (error) {
            console.error('加载历史失败:', error);
            this.showToast('加载历史失败', 'error');
        }
    }
    
    /**
     * 查看日志
     */
    async viewLogs(scriptId) {
        try {
            const response = await fetch(`/api/v1/scripts/${scriptId}/logs?limit=50`);
            const logs = await response.json();
            
            this.elements.logsContainer.innerHTML = logs.map(log => `
                <div class="log-entry">
                    <span class="log-time">${this.formatTime(log.timestamp)}</span>
                    <span class="log-level ${log.status || 'info'}">${log.status || 'INFO'}</span>
                    <span class="log-message">${log.message}</span>
                </div>
            `).join('');
            
            this.elements.logsModal.classList.remove('hidden');
        } catch (error) {
            console.error('加载日志失败:', error);
            this.showToast('加载日志失败', 'error');
        }
    }
    
    /**
     * 显示历史模态框
     */
    showHistoryModal(history) {
        // 简化：使用日志模态框显示历史
        this.elements.logsContainer.innerHTML = history.map(record => `
            <div class="log-entry">
                <span class="log-time">${this.formatTime(record.started_at)}</span>
                <span class="log-level ${record.status}">${record.status.toUpperCase()}</span>
                <span class="log-message">
                    执行ID: ${record.id} | 
                    耗时: ${record.duration?.toFixed(2) || 0}s | 
                    返回码: ${record.returncode}
                </span>
            </div>
        `).join('');
        
        this.elements.logsModal.classList.remove('hidden');
    }
    
    /**
     * 更新脚本卡片
     */
    updateScriptCard(scriptId, data) {
        const card = document.querySelector(`[data-script-id="${scriptId}"]`);
        if (!card) return;
        
        // 更新状态显示
        const statusEl = card.querySelector('.script-status');
        if (statusEl && data.status) {
            statusEl.className = `script-status ${data.status}`;
            statusEl.innerHTML = `<span>${data.status === 'running' ? '运行中' : '空闲'}</span>`;
        }
        
        // 更新按钮
        const actionsEl = card.querySelector('.script-actions');
        if (actionsEl && data.is_running !== undefined) {
            if (data.is_running) {
                actionsEl.innerHTML = `
                    <button class="btn btn-danger btn-sm stop-script" data-script-id="${scriptId}">
                        <span>⏹</span> 停止
                    </button>
                    <button class="btn btn-secondary btn-sm view-history" data-script-id="${scriptId}">
                        <span>📊</span> 历史
                    </button>
                    <button class="btn btn-ghost btn-sm view-logs" data-script-id="${scriptId}">
                        <span>📋</span> 日志
                    </button>
                `;
            } else {
                actionsEl.innerHTML = `
                    <button class="btn btn-primary btn-sm execute-script" data-script-id="${scriptId}">
                        <span>▶</span> 执行
                    </button>
                    <button class="btn btn-secondary btn-sm view-history" data-script-id="${scriptId}">
                        <span>📊</span> 历史
                    </button>
                    <button class="btn btn-ghost btn-sm view-logs" data-script-id="${scriptId}">
                        <span>📋</span> 日志
                    </button>
                `;
            }
        }
    }
    
    /**
     * 更新所有脚本状态
     */
    updateAllScriptsStatus(scripts) {
        scripts.forEach(script => {
            this.updateScriptCard(script.id, {
                status: script.status,
                is_running: script.is_running
            });
        });
    }
    
    /**
     * 更新执行状态
     */
    updateExecutionStatus(data) {
        // 可以在这里更新执行进度条等
        console.log('执行更新:', data);
    }
    
    /**
     * 追加日志
     */
    appendLog(executionId, message) {
        // 如果日志模态框打开，追加日志
        if (!this.elements.logsModal.classList.contains('hidden')) {
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <span class="log-time">${this.formatTime(new Date().toISOString())}</span>
                <span class="log-level info">INFO</span>
                <span class="log-message">${message}</span>
            `;
            this.elements.logsContainer.appendChild(logEntry);
            this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
        }
    }
    
    /**
     * 刷新数据
     */
    async refresh() {
        await this.loadScripts();
        this.renderScriptsGrid();
        this.renderStats();
        this.showToast('数据已刷新', 'success');
    }
    
    /**
     * 显示 Toast 提示
     */
    showToast(message, type = 'info') {
        // 使用全局 UI 反馈系统
        if (window.uiFeedback) {
            window.uiFeedback.show(message, type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
    
    /**
     * 格式化时间
     */
    formatTime(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.scriptsManager = new ScriptsManager();
});
