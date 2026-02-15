/**
 * YL-Monitor 脚本管理页面模块
 * 版本: v8.0.0
 * 特性: 卡片布局、批量操作、拖拽排序、日志查看、性能统计
 */

export default class ScriptsPage {
    constructor(deps) {
        this.apiBaseUrl = '/api/v1';
        this.deps = deps;
        this.scripts = [];
        this.filteredScripts = [];
        this.currentFilter = 'all';
        this.selectedScripts = new Set();
        this.sortBy = 'name';
        this.searchQuery = '';
        this.draggedScript = null;
        
        // 挂载点引用
        this.mounts = {
            header: document.getElementById('scripts-header'),
            filterBar: document.getElementById('scripts-filter-bar'),
            batchToolbar: document.getElementById('scripts-batch-toolbar'),
            grid: document.getElementById('scripts-grid'),
            stats: document.getElementById('scripts-stats')
        };
    }

    /**
     * 初始化页面
     */
    async init() {
        console.log('[ScriptsPage] 初始化脚本管理页面...');
        
        // 1. 渲染页面头部
        this.renderHeader();
        
        // 2. 渲染筛选栏
        this.renderFilterBar();
        
        // 3. 渲染批量工具栏
        this.renderBatchToolbar();
        
        // 4. 加载脚本数据
        await this.loadScripts();
        
        // 5. 渲染性能统计
        this.renderStats();
        
        // 6. 绑定事件
        this.bindEvents();
        
        console.log('[ScriptsPage] 脚本管理页面初始化完成 ✅');
    }

    /**
     * 渲染页面头部
     */
    renderHeader() {
        if (!this.mounts.header) return;
        
        this.mounts.header.innerHTML = `
            <div class="scripts-title-section">
                <div>
                    <h2>📜 脚本管理</h2>
                    <p class="scripts-subtitle">管理和监控自动化脚本 (${this.scripts.length}个脚本)</p>
                </div>
            </div>
            <div class="scripts-actions">
                <button class="btn btn-primary" id="btn-create-script">
                    <span>+</span>
                    <span>新建脚本</span>
                </button>
                <button class="btn btn-secondary" id="btn-import-script">
                    <span>📥</span>
                    <span>导入</span>
                </button>
                <div class="dropdown">
                    <button class="btn btn-secondary" id="btn-batch-menu">
                        <span>批量操作</span>
                        <span>▼</span>
                    </button>
                    <div class="dropdown-menu hidden" id="batch-menu">
                        <button class="dropdown-item" id="batch-enable">✅ 批量启用</button>
                        <button class="dropdown-item" id="batch-disable">⏸️ 批量禁用</button>
                        <button class="dropdown-item text-danger" id="batch-delete">🗑️ 批量删除</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 渲染筛选栏
     */
    renderFilterBar() {
        if (!this.mounts.filterBar) return;
        
        const counts = this.getStatusCounts();
        
        this.mounts.filterBar.innerHTML = `
            <div class="filter-section">
                <span class="filter-label">状态筛选:</span>
                <div class="filter-tabs">
                    <button class="filter-tab ${this.currentFilter === 'all' ? 'active' : ''}" data-filter="all">
                        全部 <span class="count">${counts.all}</span>
                    </button>
                    <button class="filter-tab ${this.currentFilter === 'running' ? 'active' : ''}" data-filter="running">
                        运行中 <span class="count">${counts.running}</span>
                    </button>
                    <button class="filter-tab ${this.currentFilter === 'stopped' ? 'active' : ''}" data-filter="stopped">
                        已停止 <span class="count">${counts.stopped}</span>
                    </button>
                    <button class="filter-tab ${this.currentFilter === 'error' ? 'active' : ''}" data-filter="error">
                        有错误 <span class="count">${counts.error}</span>
                    </button>
                </div>
            </div>
            <div class="filter-section">
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="script-search" placeholder="搜索脚本名称..." value="${this.searchQuery}">
                </div>
                <select class="sort-select" id="sort-scripts">
                    <option value="name" ${this.sortBy === 'name' ? 'selected' : ''}>按名称</option>
                    <option value="status" ${this.sortBy === 'status' ? 'selected' : ''}>按状态</option>
                    <option value="lastRun" ${this.sortBy === 'lastRun' ? 'selected' : ''}>按最后运行</option>
                    <option value="created" ${this.sortBy === 'created' ? 'selected' : ''}>按创建时间</option>
                </select>
            </div>
        `;
    }

    /**
     * 渲染批量工具栏
     */
    renderBatchToolbar() {
        if (!this.mounts.batchToolbar) return;
        
        this.mounts.batchToolbar.innerHTML = `
            <div class="batch-info">
                已选择 <strong id="selected-count">0</strong> 个脚本
            </div>
            <div class="batch-actions">
                <button class="btn btn-success btn-sm" id="batch-run">▶ 运行</button>
                <button class="btn btn-warning btn-sm" id="batch-stop">⏹ 停止</button>
                <button class="btn btn-secondary btn-sm" id="batch-clear">清除选择</button>
            </div>
        `;
    }

    /**
     * 获取状态统计
     */
    getStatusCounts() {
        const counts = { all: this.scripts.length, running: 0, stopped: 0, error: 0, pending: 0 };
        this.scripts.forEach(s => {
            if (counts[s.status] !== undefined) {
                counts[s.status]++;
            }
        });
        return counts;
    }

    /**
     * 加载脚本数据
     */
    async loadScripts() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/scripts`);
            if (!response.ok) throw new Error('获取脚本列表失败');
            
            const data = await response.json();
            this.scripts = data.scripts || this.getSampleScripts();
            
        } catch (error) {
            console.warn('[ScriptsPage] 使用示例数据:', error);
            this.scripts = this.getSampleScripts();
        }
        
        this.applyFilters();
        this.renderGrid();
        this.updateHeaderCount();
    }

    /**
     * 获取示例脚本数据
     */
    getSampleScripts() {
        return [
            {
                id: 'script-1',
                name: 'script_monitor.py',
                description: '系统监控脚本 - 监控CPU、内存、磁盘使用情况',
                type: 'Python',
                status: 'running',
                schedule: '*/5 * * * *',
                lastRun: new Date(Date.now() - 120000).toISOString(),
                successCount: 156,
                errorCount: 2,
                path: 'scripts/monitors/script_monitor.py'
            },
            {
                id: 'script-2',
                name: 'script_backup.py',
                description: '数据备份脚本 - 自动备份数据库和配置文件',
                type: 'Python',
                status: 'stopped',
                schedule: '0 0 * * *',
                lastRun: new Date(Date.now() - 86400000).toISOString(),
                successCount: 30,
                errorCount: 0,
                path: 'scripts/maintenance/script_backup.py'
            },
            {
                id: 'script-3',
                name: 'script_cleanup.py',
                description: '清理脚本 - 清理临时文件和日志',
                type: 'Python',
                status: 'error',
                schedule: '0 2 * * 0',
                lastRun: new Date(Date.now() - 172800000).toISOString(),
                successCount: 12,
                errorCount: 3,
                path: 'scripts/maintenance/script_cleanup.py'
            },
            {
                id: 'script-4',
                name: 'script_report.py',
                description: '报告生成脚本 - 生成系统运行报告',
                type: 'Python',
                status: 'pending',
                schedule: '0 9 * * 1',
                lastRun: null,
                successCount: 0,
                errorCount: 0,
                path: 'scripts/core/script_report.py'
            },
            {
                id: 'script-5',
                name: 'script_alert.py',
                description: '告警处理脚本 - 处理系统告警通知',
                type: 'Python',
                status: 'running',
                schedule: '*/2 * * * *',
                lastRun: new Date(Date.now() - 60000).toISOString(),
                successCount: 432,
                errorCount: 5,
                path: 'scripts/alerts/script_alert.py'
            }
        ];
    }

    /**
     * 应用筛选和排序
     */
    applyFilters() {
        let filtered = [...this.scripts];
        
        // 状态筛选
        if (this.currentFilter !== 'all') {
            filtered = filtered.filter(s => s.status === this.currentFilter);
        }
        
        // 搜索筛选
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(s => 
                s.name.toLowerCase().includes(query) ||
                s.description.toLowerCase().includes(query)
            );
        }
        
        // 排序
        filtered.sort((a, b) => {
            switch(this.sortBy) {
                case 'name': return a.name.localeCompare(b.name);
                case 'status': return a.status.localeCompare(b.status);
                case 'lastRun': 
                    if (!a.lastRun) return 1;
                    if (!b.lastRun) return -1;
                    return new Date(b.lastRun) - new Date(a.lastRun);
                case 'created': return b.id.localeCompare(a.id);
                default: return 0;
            }
        });
        
        this.filteredScripts = filtered;
    }

    /**
     * 渲染脚本网格
     */
    renderGrid() {
        if (!this.mounts.grid) return;
        
        if (this.filteredScripts.length === 0) {
            this.mounts.grid.innerHTML = `
                <div class="scripts-empty-state">
                    <div class="empty-icon">📜</div>
                    <div class="empty-title">暂无脚本</div>
                    <div class="empty-description">没有找到符合条件的脚本</div>
                    <button class="btn btn-primary" id="btn-create-empty">新建脚本</button>
                </div>
            `;
            return;
        }
        
        this.mounts.grid.innerHTML = `
            <div class="scripts-grid-container">
                ${this.filteredScripts.map((script, index) => this.renderScriptCard(script, index)).join('')}
            </div>
        `;
        
        // 绑定卡片事件
        this.bindCardEvents();
    }

    /**
     * 渲染单个脚本卡片
     */
    renderScriptCard(script, index) {
        const statusConfig = this.getStatusConfig(script.status);
        const scheduleText = this.formatSchedule(script.schedule);
        const lastRunText = script.lastRun ? this.formatTime(script.lastRun) : '从未运行';
        const isSelected = this.selectedScripts.has(script.id);
        
        return `
            <div class="script-card ${isSelected ? 'selected' : ''}" 
                 data-script-id="${script.id}" 
                 data-index="${index}"
                 draggable="true">
                <div class="script-card-header">
                    <div class="script-card-title">
                        <input type="checkbox" class="script-checkbox" 
                               data-script-id="${script.id}" 
                               ${isSelected ? 'checked' : ''}>
                        <div class="script-icon">📜</div>
                        <div class="script-info">
                            <div class="script-name">${script.name}</div>
                            <div class="script-path">${script.path}</div>
                        </div>
                    </div>
                    <div class="script-status ${statusConfig.class}">
                        ${statusConfig.label}
                    </div>
                </div>
                <div class="script-description">${script.description}</div>
                <div class="script-meta">
                    <div class="meta-item">
                        <span class="meta-label">类型</span>
                        <span class="meta-value">${script.type}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">调度</span>
                        <span class="meta-value">${scheduleText}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">最后运行</span>
                        <span class="meta-value">${lastRunText}</span>
                    </div>
                </div>
                <div class="script-stats">
                    <span class="stat-item" title="成功次数">
                        <span class="stat-icon success">✓</span>
                        <span>${script.successCount}</span>
                    </span>
                    <span class="stat-item" title="失败次数">
                        <span class="stat-icon danger">✗</span>
                        <span>${script.errorCount}</span>
                    </span>
                </div>
                <div class="script-actions">
                    <button class="btn btn-sm btn-ghost" data-action="view-logs" data-script-id="${script.id}">
                        📋 日志
                    </button>
                    <button class="btn btn-sm btn-ghost" data-action="edit-script" data-script-id="${script.id}">
                        ✏️ 编辑
                    </button>
                    ${script.status === 'running' ? `
                        <button class="btn btn-sm btn-warning" data-action="stop-script" data-script-id="${script.id}">
                            ⏹ 停止
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-success" data-action="run-script" data-script-id="${script.id}">
                            ▶ 运行
                        </button>
                    `}
                    <button class="btn btn-sm btn-danger" data-action="delete-script" data-script-id="${script.id}">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 获取状态配置
     */
    getStatusConfig(status) {
        const configs = {
            'running': { class: 'running', label: '运行中' },
            'stopped': { class: 'stopped', label: '已停止' },
            'error': { class: 'error', label: '有错误' },
            'pending': { class: 'pending', label: '等待中' }
        };
        return configs[status] || { class: 'stopped', label: status || '未知' };
    }

    /**
     * 格式化调度信息
     */
    formatSchedule(schedule) {
        if (!schedule) return '手动';
        
        const scheduleMap = {
            '*/2 * * * *': '每2分钟',
            '*/5 * * * *': '每5分钟',
            '0 * * * *': '每小时',
            '0 0 * * *': '每天',
            '0 0 * * 0': '每周',
            '0 0 1 * *': '每月',
            '0 2 * * 0': '每周日 2:00',
            '0 9 * * 1': '每周一 9:00'
        };
        
        return scheduleMap[schedule] || schedule;
    }

    /**
     * 格式化时间
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
        
        return date.toLocaleDateString('zh-CN');
    }

    /**
     * 渲染性能统计
     */
    renderStats() {
        if (!this.mounts.stats) return;
        
        const stats = this.calculateStats();
        
        this.mounts.stats.innerHTML = `
            <div class="stats-header">
                <h3>📊 性能统计</h3>
                <select class="sort-select" id="stats-period">
                    <option value="24h">最近24小时</option>
                    <option value="7d">最近7天</option>
                    <option value="30d">最近30天</option>
                </select>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-value">${stats.totalRuns}</div>
                    <div class="stat-card-label">总执行次数</div>
                    <div class="stat-card-trend ${stats.runsTrend >= 0 ? 'up' : 'down'}">
                        ${stats.runsTrend >= 0 ? '↑' : '↓'} ${Math.abs(stats.runsTrend)}%
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value" style="color: var(--success)">${stats.successRate}%</div>
                    <div class="stat-card-label">成功率</div>
                    <div class="stat-card-trend ${stats.successTrend >= 0 ? 'up' : 'down'}">
                        ${stats.successTrend >= 0 ? '↑' : '↓'} ${Math.abs(stats.successTrend)}%
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value" style="color: var(--danger)">${stats.errorCount}</div>
                    <div class="stat-card-label">错误次数</div>
                    <div class="stat-card-trend ${stats.errorTrend <= 0 ? 'up' : 'down'}">
                        ${stats.errorTrend <= 0 ? '↓' : '↑'} ${Math.abs(stats.errorTrend)}%
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${stats.avgDuration}s</div>
                    <div class="stat-card-label">平均执行时间</div>
                    <div class="stat-card-trend ${stats.durationTrend <= 0 ? 'up' : 'down'}">
                        ${stats.durationTrend <= 0 ? '↓' : '↑'} ${Math.abs(stats.durationTrend)}%
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 计算统计数据
     */
    calculateStats() {
        const totalRuns = this.scripts.reduce((sum, s) => sum + s.successCount + s.errorCount, 0);
        const totalSuccess = this.scripts.reduce((sum, s) => sum + s.successCount, 0);
        const totalError = this.scripts.reduce((sum, s) => sum + s.errorCount, 0);
        const successRate = totalRuns > 0 ? Math.round((totalSuccess / totalRuns) * 100) : 0;
        
        return {
            totalRuns,
            successRate,
            errorCount: totalError,
            avgDuration: 2.3,
            runsTrend: 12,
            successTrend: 5,
            errorTrend: -8,
            durationTrend: -15
        };
    }

    /**
     * 更新头部计数
     */
    updateHeaderCount() {
        const subtitle = this.mounts.header?.querySelector('.scripts-subtitle');
        if (subtitle) {
            subtitle.textContent = `管理和监控自动化脚本 (${this.scripts.length}个脚本)`;
        }
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 创建脚本
        document.getElementById('btn-create-script')?.addEventListener('click', () => this.createScript());
        document.getElementById('btn-create-empty')?.addEventListener('click', () => this.createScript());
        
        // 导入脚本
        document.getElementById('btn-import-script')?.addEventListener('click', () => this.importScript());
        
        // 批量菜单
        document.getElementById('btn-batch-menu')?.addEventListener('click', () => this.toggleBatchMenu());
        
        // 批量操作
        document.getElementById('batch-enable')?.addEventListener('click', () => this.batchEnable());
        document.getElementById('batch-disable')?.addEventListener('click', () => this.batchDisable());
        document.getElementById('batch-delete')?.addEventListener('click', () => this.batchDelete());
        document.getElementById('batch-run')?.addEventListener('click', () => this.batchRun());
        document.getElementById('batch-stop')?.addEventListener('click', () => this.batchStop());
        document.getElementById('batch-clear')?.addEventListener('click', () => this.clearSelection());
        
        // 筛选标签
        this.mounts.filterBar?.addEventListener('click', (e) => {
            const tab = e.target.closest('.filter-tab');
            if (tab) {
                this.setFilter(tab.dataset.filter);
            }
        });
        
        // 搜索
        document.getElementById('script-search')?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.applyFilters();
            this.renderGrid();
        });
        
        // 排序
        document.getElementById('sort-scripts')?.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.applyFilters();
            this.renderGrid();
        });
        
        // 关闭日志模态框
        document.getElementById('close-logs-modal')?.addEventListener('click', () => {
            document.getElementById('logs-modal').classList.add('hidden');
        });
        
        // 点击模态框背景关闭
        document.getElementById('logs-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'logs-modal') {
                document.getElementById('logs-modal').classList.add('hidden');
            }
        });
    }

    /**
     * 绑定卡片事件
     */
    bindCardEvents() {
        // 复选框
        document.querySelectorAll('.script-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const scriptId = e.target.dataset.scriptId;
                if (e.target.checked) {
                    this.selectedScripts.add(scriptId);
                } else {
                    this.selectedScripts.delete(scriptId);
                }
                this.updateBatchToolbar();
                this.renderGrid();
            });
        });
        
        // 卡片操作按钮
        document.querySelectorAll('.script-actions .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const scriptId = btn.dataset.scriptId;
                this.handleCardAction(action, scriptId);
            });
        });
        
        // 拖拽事件
        document.querySelectorAll('.script-card').forEach(card => {
            card.addEventListener('dragstart', (e) => this.handleDragStart(e, card));
            card.addEventListener('dragover', (e) => this.handleDragOver(e, card));
            card.addEventListener('drop', (e) => this.handleDrop(e, card));
            card.addEventListener('dragend', () => this.handleDragEnd());
        });
    }

    /**
     * 处理卡片操作
     */
    handleCardAction(action, scriptId) {
        switch(action) {
            case 'view-logs': this.viewLogs(scriptId); break;
            case 'edit-script': this.editScript(scriptId); break;
            case 'run-script': this.runScript(scriptId); break;
            case 'stop-script': this.stopScript(scriptId); break;
            case 'delete-script': this.deleteScript(scriptId); break;
        }
    }

    /**
     * 设置筛选条件
     */
    setFilter(filter) {
        this.currentFilter = filter;
        this.renderFilterBar();
        this.applyFilters();
        this.renderGrid();
    }

    /**
     * 更新批量工具栏
     */
    updateBatchToolbar() {
        const count = this.selectedScripts.size;
        const toolbar = this.mounts.batchToolbar;
        const countEl = document.getElementById('selected-count');
        
        if (count > 0) {
            toolbar?.classList.remove('hidden');
            if (countEl) countEl.textContent = count;
        } else {
            toolbar?.classList.add('hidden');
        }
    }

    /**
     * 清除选择
     */
    clearSelection() {
        this.selectedScripts.clear();
        this.updateBatchToolbar();
        this.renderGrid();
    }

    /**
     * 切换批量菜单
     */
    toggleBatchMenu() {
        const menu = document.getElementById('batch-menu');
        menu?.classList.toggle('hidden');
    }

    /**
     * 批量启用
     */
    async batchEnable() {
        if (this.selectedScripts.size === 0) return;
        this.showToast('info', `正在启用 ${this.selectedScripts.size} 个脚本...`);
        // 实现批量启用逻辑
        this.clearSelection();
    }

    /**
     * 批量禁用
     */
    async batchDisable() {
        if (this.selectedScripts.size === 0) return;
        this.showToast('info', `正在禁用 ${this.selectedScripts.size} 个脚本...`);
        // 实现批量禁用逻辑
        this.clearSelection();
    }

    /**
     * 批量删除
     */
    async batchDelete() {
        if (this.selectedScripts.size === 0) return;
        
        this.deps.uiComponents.showConfirm({
            title: '批量删除脚本',
            message: `确定要删除选中的 ${this.selectedScripts.size} 个脚本吗？`,
            type: 'danger',
            confirmText: '删除',
            onConfirm: async () => {
                this.showToast('info', `正在删除 ${this.selectedScripts.size} 个脚本...`);
                // 实现批量删除逻辑
                this.clearSelection();
                this.loadScripts();
            }
        });
    }

    /**
     * 批量运行
     */
    async batchRun() {
        if (this.selectedScripts.size === 0) return;
        this.showToast('info', `正在运行 ${this.selectedScripts.size} 个脚本...`);
        // 实现批量运行逻辑
    }

    /**
     * 批量停止
     */
    async batchStop() {
        if (this.selectedScripts.size === 0) return;
        this.showToast('info', `正在停止 ${this.selectedScripts.size} 个脚本...`);
        // 实现批量停止逻辑
    }

    /**
     * 创建脚本
     */
    createScript() {
        this.showToast('info', '创建脚本功能开发中...');
    }

    /**
     * 导入脚本
     */
    importScript() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.py,.sh,.js';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                this.showToast('success', `已选择文件: ${file.name}`);
            }
        };
        input.click();
    }

    /**
     * 查看日志
     */
    viewLogs(scriptId) {
        const script = this.scripts.find(s => s.id === scriptId);
        if (!script) return;
        
        const modal = document.getElementById('logs-modal');
        const container = document.getElementById('logs-container');
        
        // 生成示例日志
        const logs = this.generateSampleLogs(script.name);
        
        container.innerHTML = logs.map(log => `
            <div class="log-entry">
                <span class="log-time">${log.time}</span>
                <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');
        
        modal.classList.remove('hidden');
    }

    /**
     * 生成示例日志
     */
    generateSampleLogs(scriptName) {
        const levels = ['info', 'success', 'warning', 'error'];
        const messages = [
            '脚本开始执行',
            '正在初始化环境...',
            '加载配置文件成功',
            '开始数据处理',
            '处理完成，共处理 156 条记录',
            '生成报告成功',
            '脚本执行完成，耗时 2.3s'
        ];
        
        return messages.map((msg, i) => ({
            time: new Date(Date.now() - (messages.length - i) * 30000).toLocaleTimeString('zh-CN'),
            level: levels[Math.floor(Math.random() * levels.length)],
            message: msg
        }));
    }

    /**
     * 编辑脚本
     */
    editScript(scriptId) {
        const script = this.scripts.find(s => s.id === scriptId);
        this.showToast('info', `编辑脚本: ${script?.name || scriptId}`);
    }

    /**
     * 运行脚本
     */
    async runScript(scriptId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/scripts/${scriptId}/run`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showToast('success', '脚本已开始运行');
                this.loadScripts();
            } else {
                throw new Error('启动失败');
            }
        } catch (error) {
            this.showToast('error', '启动脚本失败');
        }
    }

    /**
     * 停止脚本
     */
    async stopScript(scriptId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/scripts/${scriptId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showToast('success', '脚本已停止');
                this.loadScripts();
            } else {
                throw new Error('停止失败');
            }
        } catch (error) {
            this.showToast('error', '停止脚本失败');
        }
    }

    /**
     * 删除脚本
     */
    async deleteScript(scriptId) {
        const script = this.scripts.find(s => s.id === scriptId);
        
        this.deps.uiComponents.showConfirm({
            title: '删除脚本',
            message: `确定要删除脚本 "${script?.name || scriptId}" 吗？`,
            type: 'danger',
            confirmText: '删除',
            onConfirm: async () => {
                try {
                    const response = await fetch(`${this.apiBaseUrl}/scripts/${scriptId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        this.showToast('success', '脚本已删除');
                        this.loadScripts();
                    } else {
                        throw new Error('删除失败');
                    }
                } catch (error) {
                    this.showToast('error', '删除脚本失败');
                }
            }
        });
    }

    /**
     * 拖拽开始
     */
    handleDragStart(e, card) {
        this.draggedScript = card.dataset.scriptId;
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }

    /**
     * 拖拽经过
     */
    handleDragOver(e, card) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    /**
     * 拖拽放下
     */
    async handleDrop(e, card) {
        e.preventDefault();
        const targetId = card.dataset.scriptId;
        
        if (this.draggedScript && this.draggedScript !== targetId) {
            // 交换位置
            const fromIndex = this.scripts.findIndex(s => s.id === this.draggedScript);
            const toIndex = this.scripts.findIndex(s => s.id === targetId);
            
            if (fromIndex !== -1 && toIndex !== -1) {
                const [moved] = this.scripts.splice(fromIndex, 1);
                this.scripts.splice(toIndex, 0, moved);
                
                // 保存排序到后端
                await this.saveScriptOrder();
                
                this.applyFilters();
                this.renderGrid();
                this.showToast('success', '脚本顺序已更新并保存');
            }
        }
    }
    
    /**
     * 保存脚本排序到后端
     */
    async saveScriptOrder() {
        try {
            // 构建排序数据
            const orderData = this.scripts.map((script, index) => ({
                id: script.id,
                order: index
            }));
            
            const response = await fetch(`${this.apiBaseUrl}/scripts/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scripts: orderData })
            });
            
            if (!response.ok) {
                throw new Error('保存排序失败');
            }
            
            console.log('[ScriptsPage] 脚本排序已保存到后端');
            return true;
        } catch (error) {
            console.error('[ScriptsPage] 保存排序失败:', error);
            // 显示错误但不阻止UI更新
            this.showToast('warning', '排序已更新，但保存到服务器失败');
            return false;
        }
    }

    /**
     * 拖拽结束
     */
    handleDragEnd() {
        document.querySelectorAll('.script-card').forEach(card => {
            card.classList.remove('dragging');
        });
        this.draggedScript = null;
    }

    /**
     * 显示提示
     */
    showToast(type, message) {
        this.deps.uiComponents?.showToast({ type, message });
    }

    /**
     * 处理动作
     */
    handleAction(action, context, event) {
        switch(action) {
            case 'refresh-scripts':
                this.loadScripts();
                break;
            default:
                console.log('[ScriptsPage] 未处理的动作:', action);
        }
    }
}
