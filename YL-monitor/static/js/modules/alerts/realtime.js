/**
 * 实时告警模块
 * 版本: v8.0.0
 * 特性: 时间轴布局、快速操作、筛选功能
 */

export class RealtimeModule {
    constructor(alertCenter) {
        this.center = alertCenter;
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.alerts = [];
        this.filters = {
            level: 'all',
            status: 'all',
            search: ''
        };
        this.refreshInterval = null;
        this.initialized = false;
        
        // 批量选择状态
        this.selectedAlerts = new Set();
        this.batchMode = false;
    }

    /**
     * 设置筛选条件
     */
    setFilter(key, value) {
        this.filters[key] = value;
        this.currentPage = 1;
        this.loadAlerts();
        
        // 更新筛选器UI
        const filterEl = document.getElementById(`filter-${key}`);
        if (filterEl) {
            filterEl.value = value;
        }
    }

    /**
     * 渲染模块
     */
    async render(container) {
        this.container = container;
        
        container.innerHTML = `
            <div class="alerts-realtime-container">
                <!-- 筛选控制栏 -->
                <div class="filter-bar">
                    <div class="filter-group">
                        <label>级别</label>
                        <select id="filter-level" class="form-select">
                            <option value="all">全部</option>
                            <option value="critical">严重</option>
                            <option value="warning">警告</option>
                            <option value="info">信息</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>状态</label>
                        <select id="filter-status" class="form-select">
                            <option value="all">全部</option>
                            <option value="active">活跃</option>
                            <option value="acknowledged">已确认</option>
                            <option value="resolved">已解决</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>搜索</label>
                        <div class="search-box">
                            <input type="text" id="search-alerts" placeholder="搜索告警..." class="form-input">
                            <span class="search-icon">🔍</span>
                        </div>
                    </div>
                    <div class="filter-actions">
                        <button class="btn btn-secondary btn-sm" id="refresh-alerts">
                            <span>🔄</span> 刷新
                        </button>
                        <button class="btn btn-secondary btn-sm" id="batch-select-mode">
                            <span>☑️</span> 批量选择
                        </button>
                        <button class="btn btn-primary btn-sm" id="acknowledge-all">
                            <span>✓</span> 全部确认
                        </button>
                    </div>
                </div>
                
                <!-- 批量操作工具栏 -->
                <div class="batch-toolbar hidden" id="batch-toolbar">
                    <div class="batch-info">
                        已选择 <strong id="selected-count">0</strong> 个告警
                    </div>
                    <div class="batch-actions">
                        <button class="btn btn-success btn-sm" id="batch-acknowledge">
                            <span>✓</span> 批量确认
                        </button>
                        <button class="btn btn-secondary btn-sm" id="batch-select-all">
                            <span>☑️</span> 全选
                        </button>
                        <button class="btn btn-secondary btn-sm" id="batch-clear">
                            <span>✗</span> 清除
                        </button>
                        <button class="btn btn-ghost btn-sm" id="batch-cancel">
                            取消
                        </button>
                    </div>
                </div>
                
                <!-- 告警时间轴 -->
                <div class="alerts-timeline" id="alerts-timeline">
                    <div class="loading-state">
                        <div class="loading-spinner"></div>
                        <span>加载告警数据...</span>
                    </div>
                </div>
                
                <!-- 分页 -->
                <div class="pagination-bar" id="pagination-bar">
                    <button class="btn btn-sm btn-secondary" id="prev-page" disabled>上一页</button>
                    <span class="page-info" id="page-info">第 1 页 / 共 1 页</span>
                    <button class="btn btn-sm btn-secondary" id="next-page" disabled>下一页</button>
                </div>
            </div>
        `;
        
        // 绑定事件
        this.bindEvents();
        
        // 加载数据
        await this.loadAlerts();
        
        // 启动自动刷新
        this.startAutoRefresh();
        
        this.initialized = true;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-alerts');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadAlerts());
        }

        // 全部确认按钮
        const ackAllBtn = document.getElementById('acknowledge-all');
        if (ackAllBtn) {
            ackAllBtn.addEventListener('click', () => this.acknowledgeAll());
        }

        // 批量选择模式按钮
        const batchModeBtn = document.getElementById('batch-select-mode');
        if (batchModeBtn) {
            batchModeBtn.addEventListener('click', () => this.toggleBatchMode());
        }

        // 批量操作按钮
        const batchAckBtn = document.getElementById('batch-acknowledge');
        const batchSelectAllBtn = document.getElementById('batch-select-all');
        const batchClearBtn = document.getElementById('batch-clear');
        const batchCancelBtn = document.getElementById('batch-cancel');

        if (batchAckBtn) {
            batchAckBtn.addEventListener('click', () => this.batchAcknowledge());
        }

        if (batchSelectAllBtn) {
            batchSelectAllBtn.addEventListener('click', () => this.selectAll());
        }

        if (batchClearBtn) {
            batchClearBtn.addEventListener('click', () => this.clearSelection());
        }

        if (batchCancelBtn) {
            batchCancelBtn.addEventListener('click', () => this.toggleBatchMode());
        }

        // 筛选器
        const levelFilter = document.getElementById('filter-level');
        const statusFilter = document.getElementById('filter-status');
        const searchInput = document.getElementById('search-alerts');

        if (levelFilter) {
            levelFilter.addEventListener('change', (e) => {
                this.filters.level = e.target.value;
                this.currentPage = 1;
                this.loadAlerts();
            });
        }

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.currentPage = 1;
                this.loadAlerts();
            });
        }

        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.currentPage = 1;
                    this.loadAlerts();
                }, 300);
            });
        }

        // 分页按钮
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.loadAlerts();
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.currentPage < this.totalPages) {
                    this.currentPage++;
                    this.loadAlerts();
                }
            });
        }
    }

    /**
     * 加载告警数据
     */
    async loadAlerts() {
        const timeline = document.getElementById('alerts-timeline');
        if (!timeline) return;

        // 显示加载状态
        timeline.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <span>加载告警数据...</span>
            </div>
        `;

        try {
            // 构建查询参数
            const params = new URLSearchParams({
                page: this.currentPage,
                size: this.pageSize,
                ...this.filters
            });

            const response = await fetch(`${this.center.apiBaseUrl}/alerts?${params}`);
            if (!response.ok) throw new Error('获取告警失败');

            const data = await response.json();
            this.alerts = data.items || [];
            this.totalPages = data.total_pages || 1;

            // 检查新告警并发送通知
            this.checkNewAlerts(this.alerts);

            // 渲染时间轴
            this.renderTimeline();

            // 更新分页
            this.updatePagination();

        } catch (error) {
            console.error('[RealtimeModule] 加载告警失败:', error);
            timeline.innerHTML = `
                <div class="alerts-empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-title">加载失败</div>
                    <div class="empty-description">无法加载告警数据，请稍后重试</div>
                    <button class="btn btn-primary" data-action="refresh-alerts">
                        重新加载
                    </button>
                </div>
            `;
        }
    }

    /**
     * 检查新告警
     */
    checkNewAlerts(alerts) {
        const activeAlerts = alerts.filter(a => a.status === 'active');
        const criticalAlerts = activeAlerts.filter(a => a.level === 'critical');
        
        // 如果有严重告警，发送通知
        if (criticalAlerts.length > 0) {
            this.center.sendDesktopNotification('严重告警', {
                body: `检测到 ${criticalAlerts.length} 个严重告警，请立即处理！`,
                requireInteraction: true
            });
            this.center.playAlertSound();
        }
    }

    /**
     * 渲染时间轴
     */
    renderTimeline() {
        const timeline = document.getElementById('alerts-timeline');
        if (!timeline) return;

        if (this.alerts.length === 0) {
            timeline.innerHTML = `
                <div class="alerts-empty-state">
                    <div class="empty-icon">📭</div>
                    <div class="empty-title">暂无告警</div>
                    <div class="empty-description">当前没有符合条件的告警数据</div>
                </div>
            `;
            return;
        }

        timeline.innerHTML = this.alerts.map(alert => this.renderTimelineItem(alert)).join('');

        // 绑定操作按钮事件
        this.bindAlertActions();
    }

    /**
     * 渲染时间轴项
     */
    renderTimelineItem(alert) {
        const levelClass = `level-${alert.level}`;
        const isSelected = this.selectedAlerts.has(alert.id);
        
        return `
            <div class="timeline-item ${levelClass} ${isSelected ? 'selected' : ''}" data-alert-id="${alert.id}">
                ${this.batchMode ? `
                    <div class="timeline-checkbox">
                        <input type="checkbox" class="alert-checkbox" data-alert-id="${alert.id}" ${isSelected ? 'checked' : ''}>
                    </div>
                ` : ''}
                <div class="timeline-header">
                    <div class="timeline-meta">
                        <span class="timeline-time">${this.center.formatTime(alert.timestamp)}</span>
                        <span class="timeline-level ${alert.level}">${this.getLevelLabel(alert.level)}</span>
                    </div>
                    <div class="timeline-actions">
                        ${alert.status === 'active' ? `
                            <button class="btn-quick-action success" data-action="acknowledge-alert" data-alert-id="${alert.id}">
                                <span>✓</span> 确认
                            </button>
                        ` : ''}
                        <button class="btn-quick-action" data-action="view-alert-detail" data-alert-id="${alert.id}">
                            <span>👁️</span> 详情
                        </button>
                    </div>
                </div>
                <div class="timeline-content">
                    <div class="timeline-title">${alert.rule_name || '未知规则'}</div>
                    <div class="timeline-message">${alert.message || '无详细信息'}</div>
                </div>
                <div class="timeline-footer">
                    <div class="timeline-node">
                        <span>📍</span>
                        <span>${alert.node_name || '未知节点'}</span>
                    </div>
                    <span class="status-badge ${alert.status}">${this.getStatusLabel(alert.status)}</span>
                </div>
            </div>
        `;
    }

    /**
     * 绑定告警操作事件
     */
    bindAlertActions() {
        // 使用事件委托处理告警操作
        const timeline = document.getElementById('alerts-timeline');
        if (!timeline) return;
        
        timeline.addEventListener('click', (e) => {
            // 处理复选框点击
            const checkbox = e.target.closest('.alert-checkbox');
            if (checkbox) {
                const alertId = checkbox.dataset.alertId;
                if (checkbox.checked) {
                    this.selectedAlerts.add(alertId);
                } else {
                    this.selectedAlerts.delete(alertId);
                }
                this.updateBatchToolbar();
                this.renderTimeline(); // 重新渲染以更新选中样式
                return;
            }
            
            const actionBtn = e.target.closest('[data-action]');
            if (!actionBtn) return;
            
            const action = actionBtn.dataset.action;
            const alertId = actionBtn.dataset.alertId;
            
            switch(action) {
                case 'acknowledge-alert':
                    if (alertId) this.acknowledge(alertId);
                    break;
                case 'view-alert-detail':
                    if (alertId) this.viewDetail(alertId);
                    break;
                case 'refresh-alerts':
                    this.loadAlerts();
                    break;
            }
        });
    }

    /**
     * 切换批量选择模式
     */
    toggleBatchMode() {
        this.batchMode = !this.batchMode;
        
        // 显示/隐藏批量工具栏
        const batchToolbar = document.getElementById('batch-toolbar');
        const batchModeBtn = document.getElementById('batch-select-mode');
        
        if (batchToolbar) {
            batchToolbar.classList.toggle('hidden', !this.batchMode);
        }
        
        if (batchModeBtn) {
            batchModeBtn.classList.toggle('active', this.batchMode);
        }
        
        // 清除选择
        if (!this.batchMode) {
            this.selectedAlerts.clear();
        }
        
        this.updateBatchToolbar();
        this.renderTimeline();
    }

    /**
     * 更新批量工具栏
     */
    updateBatchToolbar() {
        const countEl = document.getElementById('selected-count');
        if (countEl) {
            countEl.textContent = this.selectedAlerts.size;
        }
    }

    /**
     * 全选当前页
     */
    selectAll() {
        this.alerts.forEach(alert => {
            if (alert.status === 'active') {
                this.selectedAlerts.add(alert.id);
            }
        });
        this.updateBatchToolbar();
        this.renderTimeline();
    }

    /**
     * 清除选择
     */
    clearSelection() {
        this.selectedAlerts.clear();
        this.updateBatchToolbar();
        this.renderTimeline();
    }

    /**
     * 批量确认告警
     */
    async batchAcknowledge() {
        if (this.selectedAlerts.size === 0) {
            this.center.showToast('请先选择要确认的告警', 'warning');
            return;
        }

        // 获取选中的告警详情
        const selectedAlertIds = Array.from(this.selectedAlerts);
        const selectedAlerts = this.alerts.filter(a => this.selectedAlerts.has(a.id));
        
        // 显示确认弹窗
        this.showBatchConfirmDialog(selectedAlerts, selectedAlertIds);
    }

    /**
     * 显示批量确认弹窗
     */
    showBatchConfirmDialog(alerts, alertIds) {
        const modal = document.createElement('div');
        modal.className = 'modal batch-confirm-modal';
        modal.innerHTML = `
            <div class="modal-overlay" data-action="close-modal"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>批量确认告警</h3>
                    <button class="btn-close" data-action="close-modal">×</button>
                </div>
                <div class="modal-body">
                    <p class="confirm-message">确定要确认以下 <strong>${alerts.length}</strong> 个告警吗？</p>
                    <div class="alert-preview-list">
                        ${alerts.map(alert => `
                            <div class="alert-preview-item level-${alert.level}">
                                <span class="preview-level">${this.getLevelLabel(alert.level)}</span>
                                <span class="preview-title">${alert.rule_name || '未知规则'}</span>
                                <span class="preview-node">${alert.node_name || '未知节点'}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" id="confirm-batch-ack">
                        <span>✓</span> 确认 (${alerts.length})
                    </button>
                    <button class="btn btn-secondary" data-action="close-modal">取消</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 绑定事件
        modal.addEventListener('click', async (e) => {
            const actionBtn = e.target.closest('[data-action]');
            const confirmBtn = e.target.closest('#confirm-batch-ack');
            
            if (actionBtn && actionBtn.dataset.action === 'close-modal') {
                modal.remove();
            } else if (confirmBtn) {
                await this.executeBatchAcknowledge(alertIds);
                modal.remove();
            }
        });
    }

    /**
     * 执行批量确认
     */
    async executeBatchAcknowledge(alertIds) {
        try {
            this.center.showToast(`正在确认 ${alertIds.length} 个告警...`, 'info');

            const response = await fetch(`${this.center.apiBaseUrl}/alerts/batch-acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ alert_ids: alertIds })
            });

            if (!response.ok) throw new Error('批量确认失败');

            const result = await response.json();
            
            this.center.showToast(`成功确认 ${result.acknowledged_count || alertIds.length} 个告警`, 'success');
            
            // 清除选择并刷新
            this.selectedAlerts.clear();
            this.updateBatchToolbar();
            await this.loadAlerts();
            await this.center.loadStats();

        } catch (error) {
            console.error('[RealtimeModule] 批量确认失败:', error);
            this.center.showToast('批量确认失败，请重试', 'error');
        }
    }

    /**
     * 获取级别标签
     */
    getLevelLabel(level) {
        const labels = {
            critical: '严重',
            warning: '警告',
            info: '信息'
        };
        return labels[level] || level;
    }

    /**
     * 获取状态标签
     */
    getStatusLabel(status) {
        const labels = {
            active: '活跃',
            acknowledged: '已确认',
            resolved: '已解决'
        };
        return labels[status] || status;
    }

    /**
     * 确认单个告警
     */
    async acknowledge(alertId) {
        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alerts/${alertId}/acknowledge`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('确认失败');

            this.center.showToast('告警已确认', 'success');
            await this.loadAlerts();
            await this.center.loadStats();

        } catch (error) {
            console.error('[RealtimeModule] 确认告警失败:', error);
            this.center.showToast('确认失败，请重试', 'error');
        }
    }

    /**
     * 确认所有告警
     */
    async acknowledgeAll() {
        if (!confirm('确定要确认所有活跃告警吗？')) return;

        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alerts/acknowledge-all`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('批量确认失败');

            this.center.showToast('所有告警已确认', 'success');
            await this.loadAlerts();
            await this.center.loadStats();

        } catch (error) {
            console.error('[RealtimeModule] 批量确认失败:', error);
            this.center.showToast('批量确认失败', 'error');
        }
    }

    /**
     * 查看告警详情
     */
    viewDetail(alertId) {
        const alert = this.alerts.find(a => a.id === alertId);
        if (!alert) return;

        // 创建详情模态框
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-overlay" data-action="close-modal"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>告警详情</h3>
                    <button class="btn-close" data-action="close-modal">×</button>
                </div>
                <div class="modal-body">
                    <div class="detail-item">
                        <label>告警ID:</label>
                        <span>${alert.id}</span>
                    </div>
                    <div class="detail-item">
                        <label>级别:</label>
                        <span class="timeline-level ${alert.level}">${this.getLevelLabel(alert.level)}</span>
                    </div>
                    <div class="detail-item">
                        <label>时间:</label>
                        <span>${new Date(alert.timestamp).toLocaleString('zh-CN')}</span>
                    </div>
                    <div class="detail-item">
                        <label>节点:</label>
                        <span>${alert.node_name || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>规则:</label>
                        <span>${alert.rule_name || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>消息:</label>
                        <span>${alert.message || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>状态:</label>
                        <span class="status-badge ${alert.status}">${this.getStatusLabel(alert.status)}</span>
                    </div>
                    ${alert.details ? `
                        <div class="detail-item">
                            <label>详细信息:</label>
                            <pre>${JSON.stringify(alert.details, null, 2)}</pre>
                        </div>
                    ` : ''}
                </div>
                <div class="modal-footer">
                    ${alert.status === 'active' ? `
                        <button class="btn btn-primary" data-action="acknowledge-alert" data-alert-id="${alert.id}" data-close-modal="true">
                            确认告警
                        </button>
                    ` : ''}
                    <button class="btn btn-secondary" data-action="close-modal">关闭</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // 绑定模态框事件
        modal.addEventListener('click', (e) => {
            const actionBtn = e.target.closest('[data-action]');
            if (!actionBtn) return;
            
            const action = actionBtn.dataset.action;
            const alertId = actionBtn.dataset.alertId;
            const closeModal = actionBtn.dataset.closeModal;
            
            if (action === 'close-modal') {
                modal.remove();
            } else if (action === 'acknowledge-alert' && alertId) {
                this.acknowledge(alertId);
                if (closeModal) {
                    modal.remove();
                }
            }
        });
    }

    /**
     * 更新分页控件
     */
    updatePagination() {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');

        if (prevBtn) {
            prevBtn.disabled = this.currentPage <= 1;
        }

        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= this.totalPages;
        }

        if (pageInfo) {
            pageInfo.textContent = `第 ${this.currentPage} 页 / 共 ${this.totalPages} 页`;
        }
    }

    /**
     * 启动自动刷新
     */
    startAutoRefresh() {
        // 每30秒刷新一次
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.loadAlerts();
            }
        }, 30000);
    }

    /**
     * 停止自动刷新
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * 销毁模块
     */
    destroy() {
        this.stopAutoRefresh();
        this.initialized = false;
    }
}
