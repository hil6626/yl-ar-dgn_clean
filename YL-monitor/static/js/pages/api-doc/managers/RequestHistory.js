/**
 * API Doc请求历史记录管理器
 * 版本: v1.0.0
 */

export class RequestHistory {
  constructor(page) {
    this.page = page;
    this.storageKey = 'yl_api_request_history';
    this.maxHistory = 50; // 最多保存50条记录
  }

  /**
   * 添加历史记录
   * @param {Object} record - 请求记录
   */
  add(record) {
    const history = this.getAll();
    
    const newRecord = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      endpoint: record.endpoint,
      method: record.method,
      path: record.path,
      params: record.params,
      body: record.body,
      response: record.response,
      status: record.status,
      duration: record.duration
    };

    // 添加到开头
    history.unshift(newRecord);

    // 限制数量
    if (history.length > this.maxHistory) {
      history.pop();
    }

    // 保存到localStorage
    this.save(history);
  }

  /**
   * 获取所有历史记录
   * @returns {Array}
   */
  getAll() {
    try {
      const data = localStorage.getItem(this.storageKey);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('[RequestHistory] 读取历史记录失败:', e);
      return [];
    }
  }

  /**
   * 保存历史记录
   * @param {Array} history - 历史记录数组
   */
  save(history) {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(history));
    } catch (e) {
      console.error('[RequestHistory] 保存历史记录失败:', e);
    }
  }

  /**
   * 删除单条记录
   * @param {string} id - 记录ID
   */
  delete(id) {
    const history = this.getAll();
    const filtered = history.filter(r => r.id !== id);
    this.save(filtered);
  }

  /**
   * 清空所有记录
   */
  clear() {
    localStorage.removeItem(this.storageKey);
  }

  /**
   * 获取最近N条记录
   * @param {number} n - 数量
   * @returns {Array}
   */
  getRecent(n = 10) {
    return this.getAll().slice(0, n);
  }

  /**
   * 按端点筛选
   * @param {string} endpointId - 端点ID
   * @returns {Array}
   */
  getByEndpoint(endpointId) {
    return this.getAll().filter(r => r.endpoint.id === endpointId);
  }

  /**
   * 显示历史记录面板
   */
  showHistoryPanel() {
    const history = this.getAll();
    
    const panel = document.createElement('div');
    panel.className = 'api-history-panel';
    panel.innerHTML = `
      <div class="api-history-content">
        <div class="api-history-header">
          <h3>📜 请求历史</h3>
          <div class="api-history-actions">
            <button class="btn btn-sm btn-secondary" data-action="clear-history">
              清空
            </button>
            <button class="btn btn-sm btn-ghost" data-action="close-history">×</button>
          </div>
        </div>
        <div class="api-history-body">
          ${history.length === 0 ? `
            <div class="history-empty">
              <span>📝</span>
              <p>暂无请求历史</p>
            </div>
          ` : `
            <div class="history-list">
              ${history.map(record => this.renderHistoryItem(record)).join('')}
            </div>
          `}
        </div>
      </div>
    `;

    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
      .api-history-panel {
        position: fixed;
        top: 0;
        right: 0;
        bottom: 0;
        width: 400px;
        background: var(--bg-primary);
        box-shadow: -4px 0 20px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
      }
      @keyframes slideInRight {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
      }
      .api-history-content {
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .api-history-header {
        padding: 20px;
        border-bottom: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .api-history-header h3 {
        margin: 0;
        color: var(--text-primary);
      }
      .api-history-actions {
        display: flex;
        gap: 8px;
      }
      .api-history-body {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
      }
      .history-empty {
        text-align: center;
        padding: 60px 20px;
        color: var(--text-secondary);
      }
      .history-empty span {
        font-size: 48px;
        display: block;
        margin-bottom: 16px;
      }
      .history-item {
        padding: 16px;
        border: 1px solid var(--border);
        border-radius: 8px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .history-item:hover {
        border-color: var(--primary);
        background: var(--primary-50);
      }
      .history-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .history-method {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
      }
      .history-method-GET { background: #dbeafe; color: #1e40af; }
      .history-method-POST { background: #d1fae5; color: #065f46; }
      .history-method-PUT { background: #fef3c7; color: #92400e; }
      .history-method-DELETE { background: #fee2e2; color: #991b1b; }
      .history-status {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 4px;
      }
      .history-status-success { background: #d1fae5; color: #065f46; }
      .history-status-error { background: #fee2e2; color: #991b1b; }
      .history-path {
        font-family: monospace;
        font-size: 13px;
        color: var(--text-primary);
        margin-bottom: 8px;
        word-break: break-all;
      }
      .history-meta {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: var(--text-secondary);
      }
      .history-time::before { content: '🕐 '; }
      .history-duration::before { content: '⏱️ '; }
    `;
    document.head.appendChild(style);

    document.body.appendChild(panel);

    // 绑定事件
    panel.querySelector('[data-action="close-history"]').addEventListener('click', () => {
      panel.remove();
    });

    panel.querySelector('[data-action="clear-history"]')?.addEventListener('click', () => {
      if (confirm('确定要清空所有请求历史吗？')) {
        this.clear();
        panel.remove();
        this.showHistoryPanel(); // 重新打开显示空状态
      }
    });

    // 点击历史项重新加载
    panel.querySelectorAll('.history-item').forEach(item => {
      item.addEventListener('click', () => {
        const recordId = item.dataset.recordId;
        const record = history.find(r => r.id === recordId);
        if (record) {
          this.loadRecord(record);
          panel.remove();
        }
      });
    });
  }

  /**
   * 渲染历史记录项
   * @param {Object} record - 记录数据
   * @returns {string}
   */
  renderHistoryItem(record) {
    const time = new Date(record.timestamp).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    const statusClass = record.status >= 200 && record.status < 300 ? 'success' : 'error';

    return `
      <div class="history-item" data-record-id="${record.id}">
        <div class="history-item-header">
          <span class="history-method history-method-${record.method}">${record.method}</span>
          <span class="history-status history-status-${statusClass}">${record.status}</span>
        </div>
        <div class="history-path">${record.path}</div>
        <div class="history-meta">
          <span class="history-time">${time}</span>
          <span class="history-duration">${record.duration}ms</span>
        </div>
      </div>
    `;
  }

  /**
   * 加载历史记录到测试面板
   * @param {Object} record - 记录数据
   */
  loadRecord(record) {
    // 先选择对应的端点
    this.page.selectEndpoint(record.endpoint);
    
    // 打开测试面板
    setTimeout(() => {
      this.page.openTestPanel();
      
      // 填充参数
      if (record.params) {
        this.page.testPanel.fillParams(record.params);
      }
      
      // 填充请求体
      if (record.body) {
        this.page.testPanel.fillBody(record.body);
      }
    }, 100);
  }
}
