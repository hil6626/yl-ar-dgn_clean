/**
 * Alerts告警详情抽屉组件
 * 显示告警详细信息和操作按钮
 * 版本: v1.0.0
 */

export class AlertDetailDrawer {
  constructor(options = {}) {
    this.options = {
      onAcknowledge: () => {},
      onResolve: () => {},
      onEscalate: () => {},
      onClose: () => {},
      ...options
    };
    
    this.drawer = null;
    this.alert = null;
    this.isOpen = false;
  }

  /**
   * 显示告警详情抽屉
   * @param {Object} alert - 告警数据
   */
  show(alert) {
    this.alert = alert;
    this.render();
    this.bindEvents();
    this.populateData();
    
    // 显示动画
    requestAnimationFrame(() => {
      this.drawer.classList.add('active');
      this.isOpen = true;
    });
    
    console.log('[AlertDetailDrawer] 显示告警详情:', alert.id);
  }

  /**
   * 渲染抽屉
   */
  render() {
    // 移除已存在的抽屉
    this.close();
    
    this.drawer = document.createElement('div');
    this.drawer.className = 'alert-detail-drawer';
    this.drawer.id = 'alert-detail-drawer';
    this.drawer.innerHTML = `
      <div class="drawer-overlay"></div>
      <div class="drawer-content">
        <div class="drawer-header">
          <div class="drawer-title">
            <span class="alert-level-badge" id="drawer-alert-level"></span>
            <span class="alert-title-text" id="drawer-alert-title">告警详情</span>
          </div>
          <button class="btn btn-sm btn-ghost drawer-close-btn" data-action="close-drawer">
            ✕
          </button>
        </div>
        
        <div class="drawer-body">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h4 class="section-title">📋 基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">告警ID</span>
                <span class="detail-value" id="detail-id">-</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">告警级别</span>
                <span class="detail-value" id="detail-level">-</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">告警规则</span>
                <span class="detail-value" id="detail-rule">-</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">目标节点</span>
                <span class="detail-value" id="detail-node">-</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">触发时间</span>
                <span class="detail-value" id="detail-triggered">-</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">持续时间</span>
                <span class="detail-value" id="detail-duration">-</span>
              </div>
            </div>
          </div>
          
          <!-- 告警内容 -->
          <div class="detail-section">
            <h4 class="section-title">📝 告警内容</h4>
            <div class="alert-message-box" id="detail-message">
              -
            </div>
          </div>
          
          <!-- 指标数据 -->
          <div class="detail-section" id="metrics-section" style="display: none;">
            <h4 class="section-title">📊 指标数据</h4>
            <div class="metrics-grid" id="detail-metrics">
            </div>
          </div>
          
          <!-- 处理记录 -->
          <div class="detail-section" id="history-section" style="display: none;">
            <h4 class="section-title">📜 处理记录</h4>
            <div class="history-list" id="detail-history">
            </div>
          </div>
          
          <!-- 相关告警 -->
          <div class="detail-section" id="related-section" style="display: none;">
            <h4 class="section-title">🔗 相关告警</h4>
            <div class="related-alerts" id="detail-related">
            </div>
          </div>
        </div>
        
        <div class="drawer-footer">
          <div class="action-buttons">
            <button class="btn btn-primary" data-action="acknowledge" id="btn-acknowledge">
              ✓ 确认告警
            </button>
            <button class="btn btn-success" data-action="resolve" id="btn-resolve">
              ✓ 解决告警
            </button>
            <button class="btn btn-warning" data-action="escalate" id="btn-escalate">
              ⚡ 升级告警
            </button>
            <button class="btn btn-ghost" data-action="close-alert" id="btn-close-alert">
              关闭
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.drawer);
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 关闭按钮
    this.drawer.querySelector('[data-action="close-drawer"]')?.addEventListener('click', () => {
      this.close();
    });
    
    // 点击遮罩关闭
    this.drawer.querySelector('.drawer-overlay')?.addEventListener('click', () => {
      this.close();
    });
    
    // 确认告警
    this.drawer.querySelector('[data-action="acknowledge"]')?.addEventListener('click', () => {
      this.acknowledgeAlert();
    });
    
    // 解决告警
    this.drawer.querySelector('[data-action="resolve"]')?.addEventListener('click', () => {
      this.resolveAlert();
    });
    
    // 升级告警
    this.drawer.querySelector('[data-action="escalate"]')?.addEventListener('click', () => {
      this.escalateAlert();
    });
    
    // 关闭告警
    this.drawer.querySelector('[data-action="close-alert"]')?.addEventListener('click', () => {
      this.closeAlert();
    });
    
    // ESC键关闭
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }

  /**
   * 填充数据
   */
  populateData() {
    if (!this.alert) return;
    
    // 基本信息
    document.getElementById('detail-id').textContent = this.alert.id || '-';
    document.getElementById('detail-level').textContent = this.getLevelText(this.alert.level);
    document.getElementById('detail-rule').textContent = this.alert.rule_name || '-';
    document.getElementById('detail-node').textContent = this.alert.node_name || '-';
    document.getElementById('detail-triggered').textContent = this.formatTime(this.alert.triggered_at);
    document.getElementById('detail-duration').textContent = this.calculateDuration(this.alert.triggered_at);
    
    // 告警内容
    document.getElementById('detail-message').textContent = this.alert.message || '-';
    
    // 级别徽章
    const levelBadge = document.getElementById('drawer-alert-level');
    levelBadge.className = `alert-level-badge level-${this.alert.level}`;
    levelBadge.textContent = this.getLevelText(this.alert.level);
    
    // 标题
    document.getElementById('drawer-alert-title').textContent = this.alert.title || '告警详情';
    
    // 指标数据
    if (this.alert.metrics && Object.keys(this.alert.metrics).length > 0) {
      this.populateMetrics(this.alert.metrics);
    }
    
    // 处理记录
    if (this.alert.history && this.alert.history.length > 0) {
      this.populateHistory(this.alert.history);
    }
    
    // 相关告警
    if (this.alert.related_alerts && this.alert.related_alerts.length > 0) {
      this.populateRelatedAlerts(this.alert.related_alerts);
    }
    
    // 更新按钮状态
    this.updateButtonStates();
  }

  /**
   * 填充指标数据
   * @param {Object} metrics - 指标数据
   */
  populateMetrics(metrics) {
    const section = document.getElementById('metrics-section');
    const container = document.getElementById('detail-metrics');
    
    section.style.display = 'block';
    container.innerHTML = Object.entries(metrics).map(([key, value]) => `
      <div class="metric-item">
        <span class="metric-name">${key}</span>
        <span class="metric-value">${value}</span>
      </div>
    `).join('');
  }

  /**
   * 填充处理记录
   * @param {Array} history - 处理记录
   */
  populateHistory(history) {
    const section = document.getElementById('history-section');
    const container = document.getElementById('detail-history');
    
    section.style.display = 'block';
    container.innerHTML = history.map(record => `
      <div class="history-item">
        <span class="history-time">${this.formatTime(record.timestamp)}</span>
        <span class="history-action">${record.action}</span>
        <span class="history-user">${record.user}</span>
        ${record.comment ? `<span class="history-comment">${record.comment}</span>` : ''}
      </div>
    `).join('');
  }

  /**
   * 填充相关告警
   * @param {Array} related - 相关告警
   */
  populateRelatedAlerts(related) {
    const section = document.getElementById('related-section');
    const container = document.getElementById('detail-related');
    
    section.style.display = 'block';
    container.innerHTML = related.map(alert => `
      <div class="related-alert-item" data-alert-id="${alert.id}">
        <span class="related-level level-${alert.level}"></span>
        <span class="related-title">${alert.title}</span>
        <span class="related-time">${this.formatTime(alert.triggered_at)}</span>
      </div>
    `).join('');
    
    // 绑定点击事件
    container.querySelectorAll('.related-alert-item').forEach(item => {
      item.addEventListener('click', () => {
        const alertId = item.dataset.alertId;
        const relatedAlert = related.find(a => a.id === alertId);
        if (relatedAlert) {
          this.show(relatedAlert);
        }
      });
    });
  }

  /**
   * 更新按钮状态
   */
  updateButtonStates() {
    const acknowledgeBtn = document.getElementById('btn-acknowledge');
    const resolveBtn = document.getElementById('btn-resolve');
    
    if (this.alert.status === 'acknowledged') {
      acknowledgeBtn.disabled = true;
      acknowledgeBtn.textContent = '✓ 已确认';
    }
    
    if (this.alert.status === 'resolved') {
      acknowledgeBtn.disabled = true;
      resolveBtn.disabled = true;
      resolveBtn.textContent = '✓ 已解决';
    }
  }

  /**
   * 确认告警
   */
  acknowledgeAlert() {
    if (this.options.onAcknowledge) {
      this.options.onAcknowledge(this.alert);
    }
    
    this.showToast('success', '告警已确认');
    this.close();
  }

  /**
   * 解决告警
   */
  resolveAlert() {
    if (this.options.onResolve) {
      this.options.onResolve(this.alert);
    }
    
    this.showToast('success', '告警已解决');
    this.close();
  }

  /**
   * 升级告警
   */
  escalateAlert() {
    if (this.options.onEscalate) {
      this.options.onEscalate(this.alert);
    }
    
    this.showToast('warning', '告警已升级');
    this.close();
  }

  /**
   * 关闭告警
   */
  closeAlert() {
    if (this.options.onClose) {
      this.options.onClose(this.alert);
    }
    
    this.close();
  }

  /**
   * 关闭抽屉
   */
  close() {
    if (this.drawer) {
      this.drawer.classList.remove('active');
      this.isOpen = false;
      
      setTimeout(() => {
        if (this.drawer) {
          this.drawer.remove();
          this.drawer = null;
        }
      }, 300);
    }
  }

  /**
   * 获取级别文本
   * @param {string} level - 级别
   * @returns {string}
   */
  getLevelText(level) {
    const levels = {
      critical: '严重',
      warning: '警告',
      info: '信息',
      resolved: '已解决'
    };
    return levels[level] || level;
  }

  /**
   * 格式化时间
   * @param {string} timestamp - 时间戳
   * @returns {string}
   */
  formatTime(timestamp) {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString('zh-CN');
  }

  /**
   * 计算持续时间
   * @param {string} startTime - 开始时间
   * @returns {string}
   */
  calculateDuration(startTime) {
    if (!startTime) return '-';
    
    const start = new Date(startTime);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);
    
    if (diff < 60) return `${diff}秒`;
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时`;
    return `${Math.floor(diff / 86400)}天`;
  }

  /**
   * 显示Toast
   * @param {string} type - 类型
   * @param {string} message - 消息
   */
  showToast(type, message) {
    if (window.YLMonitor?.uiComponents?.showToast) {
      window.YLMonitor.uiComponents.showToast({ type, message });
    } else {
      console.log(`[${type}] ${message}`);
    }
  }

  /**
   * 销毁
   */
  destroy() {
    this.close();
  }
}
