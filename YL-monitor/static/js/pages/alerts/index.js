/**
 * Alerts告警中心页面入口
 * 版本: v1.0.0
 */

import { AlertDetailDrawer } from './components/AlertDetailDrawer.js';
import { AlertsWebSocketManager } from './managers/AlertsWebSocketManager.js';

/**
 * Alerts页面主类
 */
export default class AlertsPage {
  constructor(options = {}) {
    this.options = options;
    this.wsManager = null;
    this.detailDrawer = null;
    this.alerts = [];
    this.selectedAlerts = new Set();
    this.isBatchMode = false;
  }

  async init() {
    console.log('[AlertsPage] 初始化告警中心页面');
    
    // 初始化WebSocket管理器
    this.initWebSocket();
    
    // 初始化告警详情抽屉
    this.initDetailDrawer();
    
    // 绑定事件
    this.bindEvents();
    
    // 加载初始数据
    await this.loadAlerts();
    
    console.log('[AlertsPage] 初始化完成');
  }

  initWebSocket() {
    this.wsManager = new AlertsWebSocketManager({
      onConnect: () => this.updateConnectionStatus('connected'),
      onDisconnect: () => this.updateConnectionStatus('disconnected'),
      onReconnecting: () => this.updateConnectionStatus('reconnecting'),
      onError: () => this.updateConnectionStatus('error'),
      onMessage: (data) => this.handleWebSocketMessage(data)
    });
    
    this.wsManager.connect();
  }

  initDetailDrawer() {
    this.detailDrawer = new AlertDetailDrawer({
      onAcknowledge: (alertId) => this.acknowledgeAlert(alertId),
      onResolve: (alertId) => this.resolveAlert(alertId),
      onEscalate: (alertId) => this.escalateAlert(alertId),
      onClose: (alertId) => this.closeAlert(alertId)
    });
  }

  bindEvents() {
    // 批量选择模式切换
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-action="toggle-batch-mode"]')) {
        this.toggleBatchMode();
      }
      
      if (e.target.matches('[data-action="select-all"]')) {
        this.selectAll();
      }
      
      if (e.target.matches('[data-action="clear-selection"]')) {
        this.clearSelection();
      }
      
      if (e.target.matches('[data-action="batch-acknowledge"]')) {
        this.batchAcknowledge();
      }
      
      if (e.target.matches('[data-action="view-alert-detail"]')) {
        const alertId = e.target.dataset.alertId;
        this.showAlertDetail(alertId);
      }
      
      // 标签页切换
      if (e.target.matches('.nav-tab')) {
        const tabId = e.target.dataset.tab;
        this.switchTab(tabId);
      }
    });

    // 复选框选择
    document.addEventListener('change', (e) => {
      if (e.target.matches('.alert-checkbox')) {
        const alertId = e.target.dataset.alertId;
        if (e.target.checked) {
          this.selectedAlerts.add(alertId);
        } else {
          this.selectedAlerts.delete(alertId);
        }
        this.updateBatchToolbar();
      }
    });
  }

  /**
   * 切换标签页
   */
  switchTab(tabId) {
    console.log(`[AlertsPage] 切换到标签页: ${tabId}`);
    
    // 更新标签按钮状态
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.remove('active');
      if (tab.dataset.tab === tabId) {
        tab.classList.add('active');
      }
    });
    
    // 根据标签页显示不同内容
    const container = document.getElementById('tab-content-mount');
    if (!container) return;
    
    switch (tabId) {
      case 'realtime':
        // 重新渲染实时告警列表
        this.renderAlertsList(container);
        break;
      case 'rules':
        this.renderRulesTab(container);
        break;
      case 'statistics':
        this.renderStatisticsTab(container);
        break;
      case 'intelligent':
        this.renderIntelligentTab(container);
        break;
      default:
        this.renderAlertsList(container);
    }
  }

  /**
   * 渲染告警列表
   */
  renderAlertsList(container) {
    const alerts = Array.isArray(this.alerts) ? this.alerts : [];
    
    if (alerts.length === 0) {
      this.renderEmptyState(container);
      return;
    }

    container.innerHTML = `
      <div class="alerts-timeline">
        ${alerts.map(alert => this.renderAlertCard(alert)).join('')}
      </div>
    `;
  }

  /**
   * 渲染规则管理标签页
   */
  renderRulesTab(container) {
    container.innerHTML = `
      <div class="tab-placeholder">
        <div class="placeholder-icon">📋</div>
        <div class="placeholder-title">规则管理</div>
        <div class="placeholder-desc">告警规则配置功能开发中...</div>
      </div>
    `;
  }

  /**
   * 渲染统计分析标签页
   */
  renderStatisticsTab(container) {
    container.innerHTML = `
      <div class="tab-placeholder">
        <div class="placeholder-icon">📊</div>
        <div class="placeholder-title">统计分析</div>
        <div class="placeholder-desc">告警统计分析功能开发中...</div>
      </div>
    `;
  }

  /**
   * 渲染智能告警标签页
   */
  renderIntelligentTab(container) {
    container.innerHTML = `
      <div class="tab-placeholder">
        <div class="placeholder-icon">🤖</div>
        <div class="placeholder-title">智能告警</div>
        <div class="placeholder-desc">AI智能告警分析功能开发中...</div>
      </div>
    `;
  }

  async loadAlerts() {
    try {
      const response = await fetch('/api/v1/alerts');
      if (!response.ok) throw new Error('加载告警失败');
      
      const data = await response.json();
      // 确保数据是数组
      this.alerts = Array.isArray(data) ? data : (data.alerts || data.data || []);
      this.renderAlerts();
    } catch (error) {
      console.warn('[AlertsPage] 使用示例数据:', error);
      this.alerts = this.getSampleAlerts();
      this.renderAlerts();
      this.showToast('info', '已加载示例告警数据');
    }
  }

  /**
   * 获取示例告警数据
   * @returns {Array} 示例告警
   */
  getSampleAlerts() {
    return [
      {
        id: 'alert-1',
        title: 'CPU使用率过高',
        message: '节点 node-01 的CPU使用率超过85%，持续5分钟',
        level: 'critical',
        status: 'active',
        node_name: 'node-01',
        rule_name: 'CPU高负载告警',
        created_at: new Date(Date.now() - 300000).toISOString()
      },
      {
        id: 'alert-2',
        title: '内存不足警告',
        message: '节点 node-02 的内存使用率超过80%',
        level: 'warning',
        status: 'active',
        node_name: 'node-02',
        rule_name: '内存告警',
        created_at: new Date(Date.now() - 600000).toISOString()
      },
      {
        id: 'alert-3',
        title: '磁盘空间不足',
        message: '节点 node-03 的磁盘使用率超过90%',
        level: 'critical',
        status: 'active',
        node_name: 'node-03',
        rule_name: '磁盘空间告警',
        created_at: new Date(Date.now() - 900000).toISOString()
      },
      {
        id: 'alert-4',
        title: '网络延迟过高',
        message: '节点 node-04 的网络延迟超过100ms',
        level: 'warning',
        status: 'resolved',
        node_name: 'node-04',
        rule_name: '网络延迟告警',
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 'alert-5',
        title: '服务不可用',
        message: 'API服务 health-check 返回503错误',
        level: 'critical',
        status: 'active',
        node_name: 'api-gateway',
        rule_name: '服务健康检查',
        created_at: new Date(Date.now() - 120000).toISOString()
      }
    ];
  }

  renderAlerts() {
    const container = document.getElementById('tab-content-mount');
    if (!container) return;

    // 确保alerts是数组
    const alerts = Array.isArray(this.alerts) ? this.alerts : [];
    
    // 渲染统计卡片
    this.renderStatsCards();

    // 渲染标签导航
    this.renderTabNavigation();

    // 渲染内容区域
    this.renderAlertsList(container);
  }

  renderStatsCards() {
    const container = document.getElementById('stats-cards-mount');
    if (!container) return;

    // 确保alerts是数组
    const alerts = Array.isArray(this.alerts) ? this.alerts : [];
    
    // 计算统计数据
    const critical = alerts.filter(a => a.level === 'critical').length;
    const warning = alerts.filter(a => a.level === 'warning').length;
    const info = alerts.filter(a => a.level === 'info').length;
    const total = alerts.length;

    container.innerHTML = `
      <div class="stats-grid-4">
        <div class="stat-card pulse-border-danger">
          <div class="stat-header">
            <span class="stat-label">严重告警</span>
            <span class="stat-trend up">↑12%</span>
          </div>
          <div class="stat-value text-danger">${critical}</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">警告</span>
            <span class="stat-trend down">↓5%</span>
          </div>
          <div class="stat-value text-warning">${warning}</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">信息</span>
            <span class="stat-trend flat">→0%</span>
          </div>
          <div class="stat-value text-info">${info}</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">总计</span>
            <span class="stat-trend up">↑8%</span>
          </div>
          <div class="stat-value">${total}</div>
        </div>
      </div>
    `;
  }

  renderTabNavigation() {
    const container = document.getElementById('tab-navigation-mount');
    if (!container) return;

    const tabs = [
      { id: 'realtime', label: '实时告警', active: true },
      { id: 'rules', label: '规则管理', active: false },
      { id: 'statistics', label: '统计分析', active: false },
      { id: 'intelligent', label: '智能告警', active: false }
    ];

    container.innerHTML = `
      <div class="tab-navigation-sticky">
        <div class="nav-tabs">
          ${tabs.map(tab => `
            <button class="nav-tab ${tab.active ? 'active' : ''}" data-tab="${tab.id}">
              ${tab.label}
            </button>
          `).join('')}
        </div>
        <div class="notification-controls">
          <label class="notification-toggle">
            <span class="toggle-switch active"></span>
            <span class="toggle-label">🔔 声音通知</span>
          </label>
          <label class="notification-toggle">
            <span class="toggle-switch"></span>
            <span class="toggle-label">🖥️ 桌面通知</span>
          </label>
        </div>
      </div>
    `;
  }

  renderEmptyState(container) {
    container.innerHTML = `
      <div class="alerts-empty-state">
        <div class="empty-icon">🔔</div>
        <div class="empty-title">暂无告警</div>
        <div class="empty-description">当前没有符合条件的告警信息</div>
      </div>
    `;
  }

  renderAlertCard(alert) {
    const isSelected = this.selectedAlerts.has(alert.id);
    const levelColors = {
      critical: '🔴',
      warning: '🟡',
      info: '🔵'
    };
    
    return `
      <div class="timeline-item level-${alert.level} ${isSelected ? 'selected' : ''}" data-alert-id="${alert.id}">
        ${this.isBatchMode ? `
          <div class="timeline-checkbox">
            <input type="checkbox" class="alert-checkbox" data-alert-id="${alert.id}" ${isSelected ? 'checked' : ''}>
          </div>
        ` : ''}
        <div class="timeline-header">
          <div class="timeline-meta">
            <span class="timeline-level ${alert.level}">${levelColors[alert.level] || '⚪'} ${alert.level}</span>
            <span class="timeline-time">${new Date(alert.created_at).toLocaleString()}</span>
          </div>
        </div>
        <div class="timeline-content">
          <div class="timeline-title">${alert.title}</div>
          <div class="timeline-message">${alert.message}</div>
          <div class="timeline-footer">
            <div class="timeline-node">📍 ${alert.node_name || '未知节点'} | 🔔 ${alert.rule_name || '未知规则'}</div>
            <div class="timeline-actions">
              <button class="btn-quick-action" data-action="view-alert-detail" data-alert-id="${alert.id}">
                查看详情
              </button>
              ${alert.status === 'active' ? `
                <button class="btn-quick-action success" data-action="acknowledge-alert" data-alert-id="${alert.id}">
                  ✓ 确认
                </button>
              ` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  toggleBatchMode() {
    this.isBatchMode = !this.isBatchMode;
    this.selectedAlerts.clear();
    this.renderAlerts();
    this.updateBatchToolbar();
  }

  selectAll() {
    this.alerts
      .filter(a => a.status === 'active')
      .forEach(a => this.selectedAlerts.add(a.id));
    this.renderAlerts();
    this.updateBatchToolbar();
  }

  clearSelection() {
    this.selectedAlerts.clear();
    this.renderAlerts();
    this.updateBatchToolbar();
  }

  updateBatchToolbar() {
    const toolbar = document.getElementById('scripts-batch-toolbar');
    if (!toolbar) return;

    if (this.isBatchMode) {
      toolbar.classList.remove('hidden');
      toolbar.innerHTML = `
        <div class="batch-toolbar-content">
          <span class="selection-count">已选择 ${this.selectedAlerts.size} 条告警</span>
          <div class="batch-actions">
            <button class="btn btn-sm btn-outline" data-action="select-all">全选</button>
            <button class="btn btn-sm btn-outline" data-action="clear-selection">清除</button>
            <button class="btn btn-sm btn-success" data-action="batch-acknowledge" ${this.selectedAlerts.size === 0 ? 'disabled' : ''}>
              批量确认
            </button>
            <button class="btn btn-sm btn-ghost" data-action="toggle-batch-mode">退出批量模式</button>
          </div>
        </div>
      `;
    } else {
      toolbar.classList.add('hidden');
    }
  }

  async batchAcknowledge() {
    if (this.selectedAlerts.size === 0) {
      this.showToast('warning', '请先选择要确认的告警');
      return;
    }

    // 获取选中的告警详情
    const selectedAlertObjs = this.alerts.filter(a => this.selectedAlerts.has(a.id));
    
    // 显示确认弹窗
    const confirmed = await this.showConfirm({
      title: '批量确认告警',
      message: `
        <div class="batch-confirm-content">
          <p>确定要确认以下 ${selectedAlertObjs.length} 条告警吗？</p>
          <div class="alert-preview-list">
            ${selectedAlertObjs.slice(0, 5).map(a => `
              <div class="alert-preview-item">
                <span class="level-badge level-${a.level}">${a.level}</span>
                <span class="alert-name">${a.title}</span>
              </div>
            `).join('')}
            ${selectedAlertObjs.length > 5 ? `<div class="more-items">...还有 ${selectedAlertObjs.length - 5} 条告警</div>` : ''}
          </div>
        </div>
      `,
      type: 'warning',
      confirmText: '确认',
      cancelText: '取消'
    });

    if (!confirmed) return;

    try {
      const response = await fetch('/api/v1/alerts/batch-acknowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_ids: Array.from(this.selectedAlerts) })
      });

      if (!response.ok) throw new Error('批量确认失败');

      this.showToast('success', `已成功确认 ${this.selectedAlerts.size} 条告警`);
      this.selectedAlerts.clear();
      this.toggleBatchMode();
      await this.loadAlerts();
    } catch (error) {
      console.error('[AlertsPage] 批量确认失败:', error);
      this.showToast('error', '批量确认失败');
    }
  }

  showAlertDetail(alertId) {
    const alert = this.alerts.find(a => a.id === alertId);
    if (!alert) return;

    this.detailDrawer.show(alert);
  }

  async acknowledgeAlert(alertId) {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('确认告警失败');

      this.showToast('success', '告警已确认');
      await this.loadAlerts();
    } catch (error) {
      console.error('[AlertsPage] 确认告警失败:', error);
      this.showToast('error', '确认告警失败');
    }
  }

  async resolveAlert(alertId) {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}/resolve`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('解决告警失败');

      this.showToast('success', '告警已解决');
      await this.loadAlerts();
    } catch (error) {
      console.error('[AlertsPage] 解决告警失败:', error);
      this.showToast('error', '解决告警失败');
    }
  }

  async escalateAlert(alertId) {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}/escalate`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('升级告警失败');

      this.showToast('success', '告警已升级');
      await this.loadAlerts();
    } catch (error) {
      console.error('[AlertsPage] 升级告警失败:', error);
      this.showToast('error', '升级告警失败');
    }
  }

  async closeAlert(alertId) {
    try {
      const response = await fetch(`/api/v1/alerts/${alertId}/close`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('关闭告警失败');

      this.showToast('success', '告警已关闭');
      this.detailDrawer.hide();
      await this.loadAlerts();
    } catch (error) {
      console.error('[AlertsPage] 关闭告警失败:', error);
      this.showToast('error', '关闭告警失败');
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'new_alert':
        this.showToast('warning', `新告警: ${data.alert.title}`);
        this.alerts.unshift(data.alert);
        this.renderAlerts();
        break;
      case 'alert_update':
        const index = this.alerts.findIndex(a => a.id === data.alert.id);
        if (index !== -1) {
          this.alerts[index] = data.alert;
          this.renderAlerts();
        }
        break;
      case 'alert_resolved':
        const idx = this.alerts.findIndex(a => a.id === data.alert_id);
        if (idx !== -1) {
          this.alerts[idx].status = 'resolved';
          this.renderAlerts();
        }
        break;
      case 'stats_update':
        this.updateStats(data.stats);
        break;
    }
  }

  updateConnectionStatus(status) {
    const indicator = document.getElementById('alerts-ws-status');
    if (!indicator) return;

    const statusMap = {
      connected: { text: '🟢 已连接', class: 'online' },
      disconnected: { text: '🔴 已断开', class: 'offline' },
      reconnecting: { text: '🟡 重连中', class: 'reconnecting' },
      error: { text: '⚠️ 错误', class: 'error' }
    };

    const s = statusMap[status] || statusMap.disconnected;
    indicator.textContent = s.text;
    indicator.className = `ws-status-indicator ${s.class}`;
  }

  updateStats(stats) {
    const container = document.getElementById('stats-cards-mount');
    if (!container || !stats) return;

    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value text-danger">${stats.active || 0}</div>
          <div class="stat-label">活跃告警</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-warning">${stats.warning || 0}</div>
          <div class="stat-label">警告</div>
        </div>
        <div class="stat-card">
          <div class="stat-value text-success">${stats.resolved_today || 0}</div>
          <div class="stat-label">今日已解决</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.total || 0}</div>
          <div class="stat-label">总告警数</div>
        </div>
      </div>
    `;
  }

  showToast(type, message) {
    if (window.YLMonitor?.uiComponents?.showToast) {
      window.YLMonitor.uiComponents.showToast({ type, message });
    } else {
      console.log(`[${type}] ${message}`);
    }
  }

  async showConfirm(options) {
    if (window.YLMonitor?.uiComponents?.showConfirm) {
      return new Promise((resolve) => {
        window.YLMonitor.uiComponents.showConfirm({
          ...options,
          onConfirm: () => resolve(true),
          onCancel: () => resolve(false)
        });
      });
    }
    return confirm(options.message);
  }

  handleAction(action, context, event) {
    switch (action) {
      case 'refresh-alerts':
        this.loadAlerts();
        break;
      case 'filter-alerts':
        this.filterAlerts(context.dataset.filter);
        break;
      default:
        console.log('[AlertsPage] 未处理的动作:', action);
    }
  }

  filterAlerts(filter) {
    // 实现告警筛选逻辑
    console.log('[AlertsPage] 筛选告警:', filter);
  }

  destroy() {
    if (this.wsManager) {
      this.wsManager.disconnect();
    }
  }
}
