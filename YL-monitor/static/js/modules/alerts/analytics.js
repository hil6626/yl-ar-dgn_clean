/**
 * 统计分析模块
 * 从 alert-analytics.js 提取重构
 */

export class AnalyticsModule {
    constructor(alertCenter) {
        this.center = alertCenter;
        this.timeRange = '7d';
        this.charts = {};
        this.initialized = false;
    }

    /**
     * 初始化模块
     */
    async init() {
        if (this.initialized) {
            this.refreshData();
            return;
        }

        console.log('[AnalyticsModule] 初始化统计分析模块...');
        
        this.bindEvents();
        await this.loadData();
        
        this.initialized = true;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 时间范围选择
        const timeButtons = document.querySelectorAll('.time-range-selector .btn');
        timeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const range = btn.dataset.range;
                this.setTimeRange(range);
                
                // 更新按钮状态
                timeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }

    /**
     * 设置时间范围
     */
    async setTimeRange(range) {
        this.timeRange = range;
        await this.loadData();
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            // 并行加载统计数据和图表数据
            await Promise.all([
                this.loadStats(),
                this.loadCharts()
            ]);
        } catch (error) {
            console.error('[AnalyticsModule] 加载数据失败:', error);
        }
    }

    /**
     * 加载统计数据
     */
    async loadStats() {
        try {
            const response = await fetch(
                `${this.center.apiBaseUrl}/alerts/analytics/stats?range=${this.timeRange}`
            );
            
            if (!response.ok) throw new Error('获取统计失败');
            
            const stats = await response.json();
            
            // 更新DOM
            this.updateStat('stat-ana-total', stats.total || 0);
            this.updateStat('stat-ana-warning', stats.warning || 0);
            this.updateStat('stat-ana-critical', stats.critical || 0);
            
        } catch (error) {
            console.error('[AnalyticsModule] 加载统计失败:', error);
        }
    }

    /**
     * 更新统计
     */
    updateStat(id, value) {
        const el = document.getElementById(id);
        if (el) {
            this.center.animateNumber(el, parseInt(el.textContent) || 0, value);
        }
    }

    /**
     * 加载图表
     */
    async loadCharts() {
        try {
            const response = await fetch(
                `${this.center.apiBaseUrl}/alerts/analytics/trend?range=${this.timeRange}`
            );
            
            if (!response.ok) throw new Error('获取图表数据失败');
            
            const data = await response.json();
            
            this.renderTrendChart(data.trend || []);
            this.renderLevelChart(data.level_distribution || {});
            this.renderMetricChart(data.metric_distribution || {});
            
        } catch (error) {
            console.error('[AnalyticsModule] 加载图表失败:', error);
        }
    }

    /**
     * 渲染趋势图
     */
    renderTrendChart(trendData) {
        const canvas = document.getElementById('trend-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // 销毁旧图表
        if (this.charts.trend) {
            this.charts.trend.destroy();
        }

        const labels = trendData.map(d => d.date || d.time);
        const criticalData = trendData.map(d => d.critical || 0);
        const warningData = trendData.map(d => d.warning || 0);
        const infoData = trendData.map(d => d.info || 0);

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '严重',
                        data: criticalData,
                        borderColor: '#dc2626',
                        backgroundColor: 'rgba(220, 38, 38, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: '警告',
                        data: warningData,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: '信息',
                        data: infoData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    /**
     * 渲染级别分布图
     */
    renderLevelChart(distribution) {
        const canvas = document.getElementById('level-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.level) {
            this.charts.level.destroy();
        }

        const data = {
            labels: ['严重', '警告', '信息'],
            datasets: [{
                data: [
                    distribution.critical || 0,
                    distribution.warning || 0,
                    distribution.info || 0
                ],
                backgroundColor: ['#dc2626', '#f59e0b', '#3b82f6'],
                borderWidth: 0
            }]
        };

        this.charts.level = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    /**
     * 渲染指标分布图
     */
    renderMetricChart(distribution) {
        const canvas = document.getElementById('metric-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.metric) {
            this.charts.metric.destroy();
        }

        const labels = Object.keys(distribution).map(key => this.getMetricLabel(key));
        const data = Object.values(distribution);

        this.charts.metric = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '告警数',
                    data: data,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)'
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    /**
     * 获取指标标签
     */
    getMetricLabel(metric) {
        const labels = {
            cpu: 'CPU',
            memory: '内存',
            disk: '磁盘',
            network: '网络',
            load: '负载',
            process: '进程'
        };
        return labels[metric] || metric;
    }

    /**
     * 刷新数据
     */
    async refreshData() {
        await this.loadData();
    }

    /**
     * 销毁图表
     */
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
        this.initialized = false;
    }
}
