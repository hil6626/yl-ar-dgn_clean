/**
 * 告警中心页面模块
 * 适配新挂载点架构
 * 版本: v8.0.0
 */

import { RealtimeModule } from './modules/alerts/realtime.js';
import { RulesModule } from './modules/alerts/rules.js';
import { AnalyticsModule } from './modules/alerts/analytics.js';
import { IntelligentModule } from './modules/alerts/intelligent.js';

class AlertCenterPage {
    constructor(deps) {
        this.apiBaseUrl = '/api/v1';
        this.currentTab = 'realtime';
        this.modules = {};
        this.statsRefreshInterval = null;
        this.deps = deps;
        
        // 初始化子模块
        this.realtime = new RealtimeModule(this);
        this.rules = new RulesModule(this);
        this.analytics = new AnalyticsModule(this);
        this.intelligent = new IntelligentModule(this);
        
        // 挂载点引用
        this.mounts = {
            statsCards: document.getElementById('stats-cards-mount'),
            tabNavigation: document.getElementById('tab-navigation-mount'),
            tabContent: document.getElementById('tab-content-mount')
        };
    }

    /**
     * 初始化页面
     */
    async init() {
        console.log('[AlertCenterPage] 初始化告警中心页面...');
        
        // 1. 渲染统计卡片
        this.renderStatsCards();
        
        // 2. 渲染标签导航
        this.renderTabNavigation();
        
        // 3. 加载初始数据
        await this.loadStats();
        
        // 4. 初始化当前标签页
        await this.loadTab('realtime');
        
        // 5. 启动统计自动刷新
        this.startStatsRefresh();
        
        // 6. 绑定全局事件
        this.bindGlobalEvents();
        
        console.log('[AlertCenterPage] 告警中心页面初始化完成 ✅');
    }

    /**
     * 渲染统计卡片
     */
    renderStatsCards() {
        if (!this.mounts.statsCards) return;
        
        this.mounts.statsCards.innerHTML = `
            <div class="card-grid-4">
                <div class="stat-card pulse-border-danger" data-severity="critical">
                    <div class="stat-icon danger">🚨</div>
                    <div class="stat-info">
                        <div class="stat-value text-danger" id="stat-critical">0</div>
                        <div class="stat-label">严重告警</div>
                        <div class="stat-trend up" id="trend-critical">↑ 12%</div>
                    </div>
                </div>
                <div class="stat-card" data-severity="warning">
                    <div class="stat-icon warning">⚠️</div>
                    <div class="stat-info">
                        <div class="stat-value text-warning" id="stat-warning">0</div>
                        <div class="stat-label">警告</div>
                        <div class="stat-trend down" id="trend-warning">↓ 5%</div>
                    </div>
                </div>
                <div class="stat-card" data-severity="info">
                    <div class="stat-icon info">ℹ️</div>
                    <div class="stat-info">
                        <div class="stat-value text-info" id="stat-info">0</div>
                        <div class="stat-label">信息</div>
                        <div class="stat-trend neutral" id="trend-info">→ 0%</div>
                    </div>
                </div>
                <div class="stat-card" data-severity="total">
                    <div class="stat-icon">🔔</div>
                    <div class="stat-info">
                        <div class="stat-value" id="stat-total">0</div>
                        <div class="stat-label">今日总计</div>
                        <div class="stat-trend up" id="trend-total">↑ 8%</div>
                    </div>
                </div>
            </div>
        `;
        
        // 绑定卡片点击筛选事件
        this.mounts.statsCards.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', () => {
                const severity = card.dataset.severity;
                if (severity && severity !== 'total') {
                    this.filterBySeverity(severity);
                }
            });
            card.style.cursor = 'pointer';
        });
    }
    
    /**
     * 按严重级别筛选
     */
    filterBySeverity(severity) {
        // 切换到实时告警标签
        if (this.currentTab !== 'realtime') {
            this.switchTab('realtime');
        }
        // 通知实时模块更新筛选
        setTimeout(() => {
            this.realtime.setFilter('level', severity);
        }, 100);
    }

    /**
     * 渲染标签导航
     */
    renderTabNavigation() {
        if (!this.mounts.tabNavigation) return;
        
        this.mounts.tabNavigation.innerHTML = `
            <nav class="nav-tabs">
                <button class="nav-tab active" data-tab="realtime" data-action="switch-tab">
                    <span>📋</span>
                    <span>实时告警</span>
                </button>
                <button class="nav-tab" data-tab="rules" data-action="switch-tab">
                    <span>⚙️</span>
                    <span>规则管理</span>
                </button>
                <button class="nav-tab" data-tab="analytics" data-action="switch-tab">
                    <span>📊</span>
                    <span>统计分析</span>
                </button>
                <button class="nav-tab" data-tab="intelligent" data-action="switch-tab">
                    <span>🤖</span>
                    <span>智能告警</span>
                </button>
            </nav>
        `;
        
        // 绑定标签切换事件
        this.mounts.tabNavigation.querySelectorAll('[data-action="switch-tab"]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const tabName = btn.dataset.tab;
                if (tabName && tabName !== this.currentTab) {
                    await this.switchTab(tabName);
                }
            });
        });
    }

    /**
     * 切换标签页
     */
    async switchTab(tabName) {
        // 更新按钮状态
        this.mounts.tabNavigation?.querySelectorAll('.nav-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // 加载标签页内容
        await this.loadTab(tabName);
        
        this.currentTab = tabName;
        
        // 更新URL（不刷新）
        history.replaceState({ tab: tabName }, '', `#${tabName}`);
        
        console.log(`[AlertCenterPage] 切换到标签页: ${tabName}`);
    }

    /**
     * 加载指定标签页
     */
    async loadTab(tabName) {
        if (!this.mounts.tabContent) return;
        
        // 清空内容区域
        this.mounts.tabContent.innerHTML = '<div class="loading-overlay"><div class="loading-spinner"></div></div>';
        
        switch(tabName) {
            case 'realtime':
                await this.realtime.render(this.mounts.tabContent);
                break;
            case 'rules':
                await this.rules.render(this.mounts.tabContent);
                break;
            case 'analytics':
                await this.analytics.render(this.mounts.tabContent);
                break;
            case 'intelligent':
                await this.intelligent.render(this.mounts.tabContent);
                break;
        }
    }

    /**
     * 加载顶部统计数据
     */
    async loadStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/alerts/stats`);
            if (!response.ok) throw new Error('获取统计失败');
            
            const stats = await response.json();
            
            // 更新DOM
            this.updateStatElement('stat-critical', stats.critical || 0);
            this.updateStatElement('stat-warning', stats.warning || 0);
            this.updateStatElement('stat-info', stats.info || 0);
            this.updateStatElement('stat-total', stats.total || 0);
            
        } catch (error) {
            console.error('[AlertCenterPage] 加载统计失败:', error);
            // 使用默认数据
            this.updateStatElement('stat-critical', 0);
            this.updateStatElement('stat-warning', 0);
            this.updateStatElement('stat-info', 0);
            this.updateStatElement('stat-total', 0);
        }
    }

    /**
     * 更新统计元素
     */
    updateStatElement(id, value) {
        const el = document.getElementById(id);
        if (el) {
            // 数字动画
            this.animateNumber(el, parseInt(el.textContent) || 0, value);
        }
    }

    /**
     * 数字动画
     */
    animateNumber(element, from, to) {
        const duration = 500;
        const start = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            // 缓动函数
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.round(from + (to - from) * easeOutQuart);
            
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * 启动统计自动刷新
     */
    startStatsRefresh() {
        // 每30秒刷新一次
        this.statsRefreshInterval = setInterval(() => {
            this.loadStats();
        }, 30000);
    }

    /**
     * 停止统计刷新
     */
    stopStatsRefresh() {
        if (this.statsRefreshInterval) {
            clearInterval(this.statsRefreshInterval);
            this.statsRefreshInterval = null;
        }
    }

    /**
     * 绑定全局事件
     */
    bindGlobalEvents() {
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopStatsRefresh();
            } else {
                this.startStatsRefresh();
                this.loadStats();
            }
        });
        
        // 处理URL hash
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1);
            if (hash && hash !== this.currentTab && ['realtime', 'rules', 'analytics', 'intelligent'].includes(hash)) {
                this.switchTab(hash);
            }
        });
        
        // 初始化时检查hash
        const initialHash = window.location.hash.slice(1);
        if (initialHash && ['realtime', 'rules', 'analytics', 'intelligent'].includes(initialHash)) {
            this.switchTab(initialHash);
        }
    }

    /**
     * 处理动作
     */
    handleAction(action, context, event) {
        switch(action) {
            case 'switch-tab':
                // 已在renderTabNavigation中处理
                break;
            case 'refresh-alerts':
                this.loadStats();
                this.loadTab(this.currentTab);
                break;
            case 'acknowledge-all':
                this.acknowledgeAllAlerts();
                break;
            default:
                // 转发到当前模块
                const currentModule = this[this.currentTab];
                if (currentModule && typeof currentModule.handleAction === 'function') {
                    currentModule.handleAction(action, context, event);
                }
        }
    }

    /**
     * 确认所有告警
     */
    async acknowledgeAllAlerts() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/alerts/acknowledge-all`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.deps.uiComponents.showToast({
                    type: 'success',
                    message: '已确认所有告警'
                });
                this.loadStats();
                this.loadTab('realtime');
            }
        } catch (error) {
            console.error('[AlertCenterPage] 确认所有告警失败:', error);
            this.deps.uiComponents.showToast({
                type: 'error',
                message: '确认告警失败'
            });
        }
    }

    /**
     * 显示Toast通知
     */
    showToast(message, type = 'info') {
        this.deps.uiComponents.showToast({
            type,
            message
        });
    }

    /**
     * 通用API请求
     */
    async apiRequest(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`API错误: ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('[AlertCenterPage] API请求失败:', error);
            throw error;
        }
    }

    /**
     * 格式化时间
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // 小于1小时显示相对时间
        if (diff < 60000) {
            return '刚刚';
        } else if (diff < 3600000) {
            return `${Math.floor(diff / 60000)}分钟前`;
        } else if (diff < 86400000) {
            return `${Math.floor(diff / 3600000)}小时前`;
        } else {
            return date.toLocaleString('zh-CN', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    /**
     * 格式化持续时间
     */
    formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds}秒`;
        } else if (seconds < 3600) {
            return `${Math.floor(seconds / 60)}分钟`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hours}小时${mins}分钟`;
        }
    }

    /**
     * 渲染通知控制
     */
    renderNotificationControls() {
        const mount = document.getElementById('notification-permission-mount');
        if (!mount) return;
        
        const soundEnabled = localStorage.getItem('alert-sound-enabled') === 'true';
        const desktopEnabled = localStorage.getItem('alert-desktop-enabled') === 'true';
        
        mount.innerHTML = `
            <div class="notification-controls">
                <div class="notification-toggle" id="sound-toggle">
                    <div class="toggle-switch ${soundEnabled ? 'active' : ''}" data-type="sound"></div>
                    <span class="toggle-label">🔔 声音提醒</span>
                </div>
                <div class="notification-toggle" id="desktop-toggle">
                    <div class="toggle-switch ${desktopEnabled ? 'active' : ''}" data-type="desktop"></div>
                    <span class="toggle-label">💻 桌面通知</span>
                </div>
            </div>
        `;
        
        // 绑定开关事件
        mount.querySelectorAll('.notification-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const switchEl = toggle.querySelector('.toggle-switch');
                const type = switchEl.dataset.type;
                const isActive = switchEl.classList.toggle('active');
                
                localStorage.setItem(`alert-${type}-enabled`, isActive);
                
                if (type === 'desktop' && isActive) {
                    this.requestNotificationPermission();
                }
            });
        });
    }
    
    /**
     * 请求通知权限
     */
    async requestNotificationPermission() {
        if (!('Notification' in window)) return;
        
        if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            console.log('[AlertCenterPage] 通知权限:', permission);
        }
    }
    
    /**
     * 发送桌面通知
     */
    sendDesktopNotification(title, options = {}) {
        if (!('Notification' in window)) return;
        if (Notification.permission !== 'granted') return;
        if (localStorage.getItem('alert-desktop-enabled') !== 'true') return;
        
        new Notification(title, {
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: 'yl-alert',
            requireInteraction: true,
            ...options
        });
    }
    
    /**
     * 播放告警声音
     */
    playAlertSound() {
        if (localStorage.getItem('alert-sound-enabled') !== 'true') return;
        
        // 创建简单的蜂鸣声
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
}

// 导出页面类
export default AlertCenterPage;
