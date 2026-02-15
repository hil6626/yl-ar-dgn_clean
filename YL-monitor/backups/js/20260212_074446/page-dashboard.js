/**
 * YL-Monitor Dashboard 页面逻辑
 * 功能：概览卡片、实时监控、资源图表、功能矩阵
 * 版本：v1.0.0
 * 创建时间：2026-02-10
 */

export default class DashboardPage {
    constructor(deps) {
        this.themeManager = deps.themeManager;
        this.ui = deps.uiComponents;
        this.apiBaseUrl = '/api/v1';
        this.refreshInterval = null;
        this.charts = {};
    }

    /**
     * 初始化页面
     */
    async init() {
        console.log('[DashboardPage] 初始化仪表盘页面...');

        // 1. 渲染导航栏
        this.renderNavbar();

        // 2. 渲染概览卡片
        await this.renderOverviewCards();

        // 3. 渲染实时监控
        await this.renderRealtimeMonitor();

        // 4. 渲染资源图表
        await this.renderResourceCharts();

        // 5. 渲染功能矩阵
        await this.renderFunctionMatrix();

        // 6. 启动自动刷新
        this.startAutoRefresh();

        // 7. 绑定全局事件
        this.bindEvents();

        console.log('[DashboardPage] 仪表盘页面初始化完成 ✅');
    }

    /**
     * 渲染导航栏
     */
    renderNavbar() {
        this.ui.renderNavbar('navbar-mount', {
            logo: '/static/img/logo-dashboard.svg',
            brandText: '浏览器监控平台',
            theme: 'dark',
            items: [
                { id: 'dashboard', label: '仪表盘', icon: '📊', active: true, href: '/dashboard' },
                { id: 'api-doc', label: 'API文档', icon: '📚', href: '/api-doc' },
                { id: 'dag', label: 'DAG流水线', icon: '🔄', href: '/dag' },
                { id: 'scripts', label: '脚本管理', icon: '📜', href: '/scripts' }
            ]
        });
    }

    /**
     * 渲染概览卡片
     */
    async renderOverviewCards() {
        const mount = document.getElementById('overview-cards-mount');
        if (!mount) return;

        // 获取统计数据
        const stats = await this.fetchOverviewStats();

        mount.innerHTML = `
            <div class="card-grid-4">
                <div class="stat-card" data-card-id="api-status">
                    <div class="stat-icon info">🔌</div>
                    <div class="stat-info">
                        <div class="stat-value text-info">${stats.api.healthy}/${stats.api.total}</div>
                        <div class="stat-label">API接口状态</div>
                        <div class="stat-trend ${stats.api.trend > 0 ? 'up' : 'down'}">
                            ${stats.api.trend > 0 ? '↑' : '↓'} ${Math.abs(stats.api.trend)}%
                        </div>
                    </div>
                </div>

                <div class="stat-card" data-card-id="node-status">
                    <div class="stat-icon success">📦</div>
                    <div class="stat-info">
                        <div class="stat-value text-success">${stats.nodes.running}/${stats.nodes.total}</div>
                        <div class="stat-label">DAG节点状态</div>
                        <div class="stat-trend up">↑ ${stats.nodes.active}%</div>
                    </div>
                </div>

                <div class="stat-card" data-card-id="script-status">
                    <div class="stat-icon warning">📜</div>
                    <div class="stat-info">
                        <div class="stat-value text-warning">${stats.scripts.active}/${stats.scripts.total}</div>
                        <div class="stat-label">脚本执行状态</div>
                        <div class="stat-trend ${stats.scripts.trend >= 0 ? 'up' : 'down'}">
                            ${stats.scripts.trend >= 0 ? '↑' : '↓'} ${Math.abs(stats.scripts.trend)}%
                        </div>
                    </div>
                </div>

                <div class="stat-card" data-card-id="completion-rate">
                    <div class="stat-icon">✅</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.completion}%</div>
                        <div class="stat-label">整体完成度</div>
                        <div class="completion-bar">
                            <div class="completion-progress">
                                <div class="completion-fill" style="width: ${stats.completion}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 绑定卡片点击事件
        mount.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', () => {
                const cardId = card.dataset.cardId;
                this.handleCardClick(cardId);
            });
        });
    }

    /**
     * 获取概览统计数据
     */
    async fetchOverviewStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/overview`);
            if (!response.ok) throw new Error('获取概览数据失败');
            return await response.json();
        } catch (error) {
            console.error('[DashboardPage] 获取概览数据失败:', error);
            // 返回默认数据
            return {
                api: { total: 24, healthy: 22, trend: 5 },
                nodes: { total: 15, running: 12, active: 80 },
                scripts: { total: 30, active: 25, trend: 10 },
                completion: 85
            };
        }
    }

    /**
     * 渲染实时监控
     */
    async renderRealtimeMonitor() {
        const mount = document.getElementById('realtime-monitor-mount');
        if (!mount) return;

        mount.innerHTML = `
            <div class="monitor-grid-3">
                <div class="monitor-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span class="status-dot online pulse"></span>
                            <span>API实时监控</span>
                        </div>
                        <span class="text-sm text-secondary">实时监控中</span>
                    </div>
                    <div class="panel-content" id="api-monitor-content">
                        <div class="loading-state">
                            <div class="loading-spinner"></div>
                            <span>加载中...</span>
                        </div>
                    </div>
                </div>

                <div class="monitor-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span class="status-dot online pulse"></span>
                            <span>DAG执行监控</span>
                        </div>
                        <span class="text-sm text-secondary">实时监控中</span>
                    </div>
                    <div class="panel-content" id="dag-monitor-content">
                        <div class="loading-state">
                            <div class="loading-spinner"></div>
                            <span>加载中...</span>
                        </div>
                    </div>
                </div>

                <div class="monitor-panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span class="status-dot online pulse"></span>
                            <span>脚本执行监控</span>
                        </div>
                        <span class="text-sm text-secondary">实时监控中</span>
                    </div>
                    <div class="panel-content" id="script-monitor-content">
                        <div class="loading-state">
                            <div class="loading-spinner"></div>
                            <span>加载中...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 加载监控数据
        await this.loadMonitorData();
    }

    /**
     * 加载监控数据
     */
    async loadMonitorData() {
        try {
            // 并行加载三种监控数据
            const [apiData, dagData, scriptData] = await Promise.all([
                fetch(`${this.apiBaseUrl}/monitor/api`).then(r => r.json()).catch(() => null),
                fetch(`${this.apiBaseUrl}/monitor/dag`).then(r => r.json()).catch(() => null),
                fetch(`${this.apiBaseUrl}/monitor/scripts`).then(r => r.json()).catch(() => null)
            ]);

            // 更新API监控
            const apiContent = document.getElementById('api-monitor-content');
            if (apiContent && apiData) {
                apiContent.innerHTML = this.renderAPIMonitorList(apiData);
            }

            // 更新DAG监控
            const dagContent = document.getElementById('dag-monitor-content');
            if (dagContent && dagData) {
                dagContent.innerHTML = this.renderDAGMonitorList(dagData);
            }

            // 更新脚本监控
            const scriptContent = document.getElementById('script-monitor-content');
            if (scriptContent && scriptData) {
                scriptContent.innerHTML = this.renderScriptMonitorList(scriptData);
            }

        } catch (error) {
            console.error('[DashboardPage] 加载监控数据失败:', error);
        }
    }

    /**
     * 渲染API监控列表
     */
    renderAPIMonitorList(data) {
        if (!data.items || data.items.length === 0) {
            return '<div class="empty-state">暂无API监控数据</div>';
        }

        return `
            <div class="monitor-list">
                ${data.items.map(item => `
                    <div class="monitor-item ${item.status}">
                        <div class="item-name">${item.name}</div>
                        <div class="item-status">${item.status === 'online' ? '✅' : '❌'}</div>
                        <div class="item-latency">${item.latency}ms</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * 渲染DAG监控列表
     */
    renderDAGMonitorList(data) {
        if (!data.executions || data.executions.length === 0) {
            return '<div class="empty-state">暂无DAG执行数据</div>';
        }

        return `
            <div class="monitor-list">
                ${data.executions.map(exec => `
                    <div class="monitor-item ${exec.status}">
                        <div class="item-name">${exec.dag_name}</div>
                        <div class="item-status">${this.getStatusIcon(exec.status)}</div>
                        <div class="item-progress">${exec.progress}%</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * 渲染脚本监控列表
     */
    renderScriptMonitorList(data) {
        if (!data.executions || data.executions.length === 0) {
            return '<div class="empty-state">暂无脚本执行数据</div>';
        }

        return `
            <div class="monitor-list">
                ${data.executions.map(exec => `
                    <div class="monitor-item ${exec.status}">
                        <div class="item-name">${exec.script_name}</div>
                        <div class="item-status">${this.getStatusIcon(exec.status)}</div>
                        <div class="item-time">${exec.duration}s</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * 获取状态图标
     */
    getStatusIcon(status) {
        const icons = {
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'pending': '⏳',
            'online': '✅',
            'offline': '❌'
        };
        return icons[status] || '❓';
    }

    /**
     * 渲染资源图表
     */
    async renderResourceCharts() {
        const mount = document.getElementById('resource-charts-mount');
        if (!mount) return;

        mount.innerHTML = `
            <div class="card-grid-3">
                <div class="chart-card">
                    <div class="chart-header">
                        <h4 class="chart-title">CPU 使用率</h4>
                        <div class="chart-value" id="cpu-value">--%</div>
                    </div>
                    <div class="gauge-container">
                        <svg class="gauge" viewBox="0 0 100 100">
                            <circle class="gauge-bg" cx="50" cy="50" r="45"></circle>
                            <circle class="gauge-fill" cx="50" cy="50" r="45" 
                                    stroke-dasharray="283" stroke-dashoffset="283"
                                    id="cpu-gauge-fill"></circle>
                        </svg>
                        <div class="gauge-value" id="cpu-gauge-value">--%</div>
                    </div>
                </div>

                <div class="chart-card">
                    <div class="chart-header">
                        <h4 class="chart-title">内存 使用率</h4>
                        <div class="chart-value" id="memory-value">--%</div>
                    </div>
                    <div class="gauge-container">
                        <svg class="gauge" viewBox="0 0 100 100">
                            <circle class="gauge-bg" cx="50" cy="50" r="45"></circle>
                            <circle class="gauge-fill" cx="50" cy="50" r="45" 
                                    stroke-dasharray="283" stroke-dashoffset="283"
                                    id="memory-gauge-fill"></circle>
                        </svg>
                        <div class="gauge-value" id="memory-gauge-value">--%</div>
                    </div>
                </div>

                <div class="chart-card">
                    <div class="chart-header">
                        <h4 class="chart-title">磁盘 使用率</h4>
                        <div class="chart-value" id="disk-value">--%</div>
                    </div>
                    <div class="gauge-container">
                        <svg class="gauge" viewBox="0 0 100 100">
                            <circle class="gauge-bg" cx="50" cy="50" r="45"></circle>
                            <circle class="gauge-fill" cx="50" cy="50" r="45" 
                                    stroke-dasharray="283" stroke-dashoffset="283"
                                    id="disk-gauge-fill"></circle>
                        </svg>
                        <div class="gauge-value" id="disk-gauge-value">--%</div>
                    </div>
                </div>
            </div>
        `;

        // 加载资源数据
        await this.loadResourceData();
    }

    /**
     * 加载资源数据
     */
    async loadResourceData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/system/resources`);
            const data = await response.json();

            // 更新仪表盘
            this.updateGauge('cpu', data.cpu);
            this.updateGauge('memory', data.memory);
            this.updateGauge('disk', data.disk);

        } catch (error) {
            console.error('[DashboardPage] 加载资源数据失败:', error);
        }
    }

    /**
     * 更新仪表盘
     */
    updateGauge(type, value) {
        const valueEl = document.getElementById(`${type}-value`);
        const gaugeValueEl = document.getElementById(`${type}-gauge-value`);
        const gaugeFillEl = document.getElementById(`${type}-gauge-fill`);

        if (valueEl) valueEl.textContent = `${value}%`;
        if (gaugeValueEl) gaugeValueEl.textContent = `${value}%`;

        if (gaugeFillEl) {
            // 计算stroke-dashoffset: 283是圆周长，根据百分比计算偏移
            const offset = 283 - (283 * value / 100);
            gaugeFillEl.style.strokeDashoffset = offset;
            
            // 根据值设置颜色
            if (value > 80) {
                gaugeFillEl.style.stroke = 'var(--accent)';
            } else if (value > 60) {
                gaugeFillEl.style.stroke = 'var(--warning)';
            } else {
                gaugeFillEl.style.stroke = 'var(--primary)';
            }
        }
    }

    /**
     * 渲染功能矩阵
     */
    async renderFunctionMatrix() {
        const mount = document.getElementById('function-matrix-mount');
        if (!mount) return;

        // 获取功能矩阵数据
        const matrixData = await this.fetchFunctionMatrix();

        mount.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">功能完成度矩阵</h3>
                    <button class="btn btn-secondary btn-sm" data-action="refresh-matrix">
                        <span>🔄</span> 刷新
                    </button>
                </div>
                <div class="card-body">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th>功能名称</th>
                                <th>API</th>
                                <th>脚本</th>
                                <th>DAG</th>
                                <th>监控</th>
                                <th>完成度</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${matrixData.map(item => `
                                <tr>
                                    <td>
                                        <div class="font-medium">${item.name}</div>
                                        <div class="text-sm text-secondary">${item.description}</div>
                                    </td>
                                    <td>${this.getStatusBadge(item.api)}</td>
                                    <td>${this.getStatusBadge(item.script)}</td>
                                    <td>${this.getStatusBadge(item.dag)}</td>
                                    <td>${this.getStatusBadge(item.monitor)}</td>
                                    <td>
                                        <div class="completion-bar">
                                            <div class="completion-progress">
                                                <div class="completion-fill" style="width: ${item.completion}%"></div>
                                            </div>
                                            <span class="completion-text ${item.completion < 100 ? 'text-warning' : 'text-success'}">${item.completion}%</span>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // 绑定刷新按钮
        const refreshBtn = mount.querySelector('[data-action="refresh-matrix"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.renderFunctionMatrix());
        }
    }

    /**
     * 获取功能矩阵数据
     */
    async fetchFunctionMatrix() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/function-matrix`);
            if (!response.ok) throw new Error('获取功能矩阵失败');
            return await response.json();
        } catch (error) {
            console.error('[DashboardPage] 获取功能矩阵失败:', error);
            // 返回示例数据
            return [
                { name: '告警管理', description: '告警规则配置与通知', api: true, script: true, dag: true, monitor: true, completion: 100 },
                { name: '指标采集', description: '系统指标自动采集', api: true, script: true, dag: false, monitor: true, completion: 75 },
                { name: 'DAG编排', description: '可视化流程编排', api: true, script: false, dag: true, monitor: true, completion: 75 },
                { name: '脚本执行', description: '自动化脚本管理', api: true, script: true, dag: false, monitor: false, completion: 50 }
            ];
        }
    }

    /**
     * 获取状态徽章
     */
    getStatusBadge(status) {
        if (status === true || status === 'completed') {
            return '<span class="status-badge success">✅ 完成</span>';
        } else if (status === 'partial') {
            return '<span class="status-badge warning">⚠️ 部分</span>';
        } else {
            return '<span class="status-badge error">❌ 未完成</span>';
        }
    }

    /**
     * 启动自动刷新
     */
    startAutoRefresh() {
        // 每30秒刷新一次数据
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 30000);

        console.log('[DashboardPage] 自动刷新已启动（30秒间隔）');
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
     * 刷新数据
     */
    async refreshData() {
        console.log('[DashboardPage] 刷新数据...');
        await Promise.all([
            this.renderOverviewCards(),
            this.loadMonitorData(),
            this.loadResourceData()
        ]);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
                this.refreshData();
            }
        });

        // 监听UI事件
        this.ui.on('cardClick', (data) => {
            console.log('[DashboardPage] 卡片点击:', data.cardId);
        });
    }

    /**
     * 处理卡片点击
     */
    handleCardClick(cardId) {
        // 根据卡片ID导航到相应页面
        const pageMap = {
            'api-status': '/api-doc',
            'node-status': '/dag',
            'script-status': '/scripts'
        };

        const targetPage = pageMap[cardId];
        if (targetPage) {
            window.location.href = targetPage;
        }
    }

    /**
     * 处理全局动作
     */
    handleAction(action, context, event) {
        switch(action) {
            case 'refresh-dashboard':
                this.refreshData();
                this.ui.showToast({ type: 'success', message: '数据已刷新' });
                break;
            default:
                console.log('[DashboardPage] 未处理的动作:', action);
        }
    }

    /**
     * 页面销毁清理
     */
    destroy() {
        this.stopAutoRefresh();
        console.log('[DashboardPage] 页面已清理');
    }
}
