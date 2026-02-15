/**
 * Dashboard资源图表交互组件
 * 实现图表点击详情弹窗
 * 版本: v1.0.0
 */

export class ResourceChartInteraction {
  constructor(options = {}) {
    this.options = {
      onViewHistory: () => {},
      ...options
    };
    
    this.modal = null;
    this.currentMetric = null;
    this.historicalData = [];
  }

  /**
   * 初始化图表交互
   * @param {HTMLElement} chartContainer - 图表容器
   */
  init(chartContainer) {
    if (!chartContainer) return;
    
    // 为图表添加点击事件
    chartContainer.addEventListener('click', (e) => {
      const chartElement = e.target.closest('[data-metric]');
      if (chartElement) {
        const metric = chartElement.dataset.metric;
        const title = chartElement.dataset.title || metric;
        this.showDetailModal(metric, title);
      }
    });
    
    // 添加悬停提示
    chartContainer.addEventListener('mouseover', (e) => {
      const chartElement = e.target.closest('[data-metric]');
      if (chartElement) {
        chartElement.style.cursor = 'pointer';
        chartElement.title = '点击查看详情';
      }
    });
    
    console.log('[ResourceChartInteraction] 图表交互已初始化');
  }

  /**
   * 显示详情弹窗
   * @param {string} metric - 指标名称
   * @param {string} title - 标题
   */
  async showDetailModal(metric, title) {
    this.currentMetric = metric;
    
    // 获取历史数据
    await this.loadHistoricalData(metric);
    
    this.renderModal(metric, title);
    this.bindEvents();
    
    // 显示动画
    requestAnimationFrame(() => {
      this.modal.classList.add('active');
    });
    
    console.log(`[ResourceChartInteraction] 显示详情: ${metric}`);
  }

  /**
   * 加载历史数据
   * @param {string} metric - 指标名称
   */
  async loadHistoricalData(metric) {
    try {
      const response = await fetch(`/api/v1/metrics/history?metric=${metric}&hours=24`);
      if (!response.ok) {
        throw new Error('加载历史数据失败');
      }
      
      this.historicalData = await response.json();
    } catch (error) {
      console.error('[ResourceChartInteraction] 加载历史数据失败:', error);
      // 使用模拟数据
      this.historicalData = this.generateMockData(metric);
    }
  }

  /**
   * 生成模拟数据
   * @param {string} metric - 指标名称
   * @returns {Array}
   */
  generateMockData(metric) {
    const data = [];
    const now = new Date();
    
    for (let i = 24; i >= 0; i--) {
      const time = new Date(now - i * 60 * 60 * 1000);
      let value;
      
      switch (metric) {
        case 'cpu':
          value = Math.random() * 30 + 40; // 40-70%
          break;
        case 'memory':
          value = Math.random() * 20 + 50; // 50-70%
          break;
        case 'disk':
          value = Math.random() * 10 + 60; // 60-70%
          break;
        case 'network':
          value = Math.random() * 100 + 50; // 50-150 MB/s
          break;
        default:
          value = Math.random() * 100;
      }
      
      data.push({
        timestamp: time.toISOString(),
        value: Math.round(value * 100) / 100,
        formattedTime: time.toLocaleString('zh-CN', { 
          month: 'short', 
          day: 'numeric', 
          hour: '2-digit',
          minute: '2-digit'
        })
      });
    }
    
    return data;
  }

  /**
   * 渲染弹窗
   * @param {string} metric - 指标名称
   * @param {string} title - 标题
   */
  renderModal(metric, title) {
    // 移除已存在的弹窗
    this.closeModal();
    
    const currentValue = this.historicalData[this.historicalData.length - 1]?.value || 0;
    const avgValue = this.historicalData.reduce((sum, d) => sum + d.value, 0) / this.historicalData.length;
    const maxValue = Math.max(...this.historicalData.map(d => d.value));
    const minValue = Math.min(...this.historicalData.map(d => d.value));
    
    this.modal = document.createElement('div');
    this.modal.className = 'resource-detail-modal';
    this.modal.id = 'resource-detail-modal';
    this.modal.innerHTML = `
      <div class="modal-overlay">
        <div class="modal-content">
          <div class="modal-header">
            <div class="modal-title">
              <span class="metric-icon">${this.getMetricIcon(metric)}</span>
              <span>${title} 详情</span>
            </div>
            <button class="btn btn-sm btn-ghost modal-close-btn" data-action="close-modal">
              ✕
            </button>
          </div>
          
          <div class="modal-body">
            <!-- 当前状态 -->
            <div class="current-status">
              <div class="status-value ${this.getStatusClass(currentValue, metric)}">
                <span class="value-number">${currentValue.toFixed(1)}</span>
                <span class="value-unit">${this.getMetricUnit(metric)}</span>
              </div>
              <div class="status-label">当前使用率</div>
            </div>
            
            <!-- 统计信息 -->
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-value">${avgValue.toFixed(1)}${this.getMetricUnit(metric)}</div>
                <div class="stat-label">24小时平均</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">${maxValue.toFixed(1)}${this.getMetricUnit(metric)}</div>
                <div class="stat-label">24小时最高</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">${minValue.toFixed(1)}${this.getMetricUnit(metric)}</div>
                <div class="stat-label">24小时最低</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">${this.historicalData.length}</div>
                <div class="stat-label">数据点数</div>
              </div>
            </div>
            
            <!-- 历史趋势图 -->
            <div class="history-chart-section">
              <h4 class="section-title">📈 24小时趋势</h4>
              <div class="history-chart" id="history-chart">
                ${this.renderSimpleChart()}
              </div>
            </div>
            
            <!-- 数据表格 -->
            <div class="data-table-section">
              <h4 class="section-title">📋 历史数据</h4>
              <div class="data-table-container">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>时间</th>
                      <th>数值</th>
                      <th>状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this.historicalData.slice(-10).reverse().map(d => `
                      <tr>
                        <td>${d.formattedTime}</td>
                        <td>${d.value.toFixed(2)}${this.getMetricUnit(metric)}</td>
                        <td>
                          <span class="status-badge ${this.getStatusClass(d.value, metric)}">
                            ${this.getStatusText(d.value, metric)}
                          </span>
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="btn btn-primary" data-action="view-full-history">
              查看完整历史
            </button>
            <button class="btn btn-ghost" data-action="export-data">
              导出数据
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.modal);
  }

  /**
   * 渲染简单图表
   * @returns {string}
   */
  renderSimpleChart() {
    if (this.historicalData.length === 0) return '<div class="no-data">暂无数据</div>';
    
    const values = this.historicalData.map(d => d.value);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    
    const points = this.historicalData.map((d, i) => {
      const x = (i / (this.historicalData.length - 1)) * 100;
      const y = 100 - ((d.value - min) / range) * 100;
      return `${x},${y}`;
    }).join(' ');
    
    return `
      <svg class="trend-chart" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline
          fill="none"
          stroke="var(--primary-color, #3b82f6)"
          stroke-width="2"
          points="${points}"
        />
        <defs>
          <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="var(--primary-color, #3b82f6)" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="var(--primary-color, #3b82f6)" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <polygon
          fill="url(#chartGradient)"
          points="0,100 ${points} 100,100"
        />
      </svg>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 关闭按钮
    this.modal.querySelector('[data-action="close-modal"]')?.addEventListener('click', () => {
      this.closeModal();
    });
    
    // 点击遮罩关闭
    this.modal.querySelector('.modal-overlay')?.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.closeModal();
      }
    });
    
    // 查看完整历史
    this.modal.querySelector('[data-action="view-full-history"]')?.addEventListener('click', () => {
      if (this.options.onViewHistory) {
        this.options.onViewHistory(this.currentMetric);
      }
      this.closeModal();
    });
    
    // 导出数据
    this.modal.querySelector('[data-action="export-data"]')?.addEventListener('click', () => {
      this.exportData();
    });
    
    // ESC键关闭
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal) {
        this.closeModal();
      }
    });
  }

  /**
   * 导出数据
   */
  exportData() {
    const csvContent = [
      ['时间', '数值', '单位'].join(','),
      ...this.historicalData.map(d => [
        d.formattedTime,
        d.value,
        this.getMetricUnit(this.currentMetric)
      ].join(','))
    ].join('\n');
    
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `metric-${this.currentMetric}-history-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
    
    this.showToast('success', '数据已导出');
  }

  /**
   * 关闭弹窗
   */
  closeModal() {
    if (this.modal) {
      this.modal.classList.remove('active');
      setTimeout(() => {
        if (this.modal) {
          this.modal.remove();
          this.modal = null;
        }
      }, 300);
    }
  }

  /**
   * 获取指标图标
   * @param {string} metric - 指标
   * @returns {string}
   */
  getMetricIcon(metric) {
    const icons = {
      cpu: '💻',
      memory: '🧠',
      disk: '💾',
      network: '🌐'
    };
    return icons[metric] || '📊';
  }

  /**
   * 获取指标单位
   * @param {string} metric - 指标
   * @returns {string}
   */
  getMetricUnit(metric) {
    const units = {
      cpu: '%',
      memory: '%',
      disk: '%',
      network: 'MB/s'
    };
    return units[metric] || '';
  }

  /**
   * 获取状态样式类
   * @param {number} value - 数值
   * @param {string} metric - 指标
   * @returns {string}
   */
  getStatusClass(value, metric) {
    const thresholds = {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 80, critical: 90 },
      disk: { warning: 80, critical: 90 },
      network: { warning: 100, critical: 150 }
    };
    
    const t = thresholds[metric] || { warning: 70, critical: 85 };
    
    if (value >= t.critical) return 'critical';
    if (value >= t.warning) return 'warning';
    return 'normal';
  }

  /**
   * 获取状态文本
   * @param {number} value - 数值
   * @param {string} metric - 指标
   * @returns {string}
   */
  getStatusText(value, metric) {
    const cls = this.getStatusClass(value, metric);
    const texts = {
      normal: '正常',
      warning: '警告',
      critical: '严重'
    };
    return texts[cls] || '未知';
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
    this.closeModal();
  }
}
