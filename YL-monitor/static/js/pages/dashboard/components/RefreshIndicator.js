/**
 * Dashboard刷新状态提示组件
 * 版本: v1.0.0
 */

export class RefreshIndicator {
  constructor() {
    this.lastRefreshTime = null;
    this.refreshButton = null;
    this.statusElement = null;
  }

  /**
   * 初始化刷新指示器
   * @param {string} buttonSelector - 刷新按钮选择器
   */
  init(buttonSelector = '[data-action="refresh-dashboard"]') {
    this.refreshButton = document.querySelector(buttonSelector);
    this.createStatusElement();
    this.bindEvents();
  }

  /**
   * 创建状态元素
   */
  createStatusElement() {
    this.statusElement = document.createElement('div');
    this.statusElement.className = 'refresh-status';
    this.statusElement.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-secondary);
      margin-left: 12px;
    `;

    // 插入到刷新按钮旁边
    if (this.refreshButton && this.refreshButton.parentNode) {
      this.refreshButton.parentNode.insertBefore(this.statusElement, this.refreshButton.nextSibling);
    }
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (this.refreshButton) {
      this.refreshButton.addEventListener('click', () => {
        this.startRefreshing();
      });
    }
  }

  /**
   * 开始刷新
   */
  startRefreshing() {
    if (this.refreshButton) {
      this.refreshButton.classList.add('refreshing');
      this.refreshButton.disabled = true;
    }

    this.updateStatus('刷新中...', 'info');

    // 模拟刷新完成
    setTimeout(() => {
      this.finishRefreshing();
    }, 1000);
  }

  /**
   * 完成刷新
   */
  finishRefreshing() {
    if (this.refreshButton) {
      this.refreshButton.classList.remove('refreshing');
      this.refreshButton.disabled = false;
    }

    this.lastRefreshTime = new Date();
    this.updateStatus(`已刷新 ${this.formatTime(this.lastRefreshTime)}`, 'success');

    // 显示Toast通知
    this.showToast('数据已刷新');
  }

  /**
   * 更新状态文本
   * @param {string} text - 状态文本
   * @param {string} type - 状态类型 (info, success, warning)
   */
  updateStatus(text, type) {
    if (!this.statusElement) return;

    const iconMap = {
      info: '🔄',
      success: '✅',
      warning: '⚠️'
    };

    this.statusElement.innerHTML = `
      <span>${iconMap[type] || 'ℹ️'}</span>
      <span>${text}</span>
    `;

    // 根据类型设置颜色
    const colorMap = {
      info: 'var(--text-secondary)',
      success: 'var(--success)',
      warning: 'var(--warning)'
    };

    this.statusElement.style.color = colorMap[type] || colorMap.info;
  }

  /**
   * 格式化时间
   * @param {Date} date - 日期对象
   * @returns {string}
   */
  formatTime(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return '刚刚';
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * 显示Toast通知
   * @param {string} message - 消息内容
   */
  showToast(message) {
    // 使用全局Toast组件
    if (window.YLMonitor && window.YLMonitor.uiComponents) {
      window.YLMonitor.uiComponents.showToast({
        type: 'success',
        message: message
      });
    }
  }

  /**
   * 自动更新时间显示
   */
  startAutoUpdate() {
    setInterval(() => {
      if (this.lastRefreshTime) {
        this.updateStatus(`已刷新 ${this.formatTime(this.lastRefreshTime)}`, 'success');
      }
    }, 60000); // 每分钟更新一次
  }
}
