/**
 * 脚本卡片组件
 * 拆分自: page-scripts.js renderScriptCard()
 * 版本: v1.0.0
 */

export class ScriptCard {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
  }

  /**
   * 渲染脚本卡片
   * @param {Object} script - 脚本数据
   * @param {number} index - 索引
   * @param {boolean} isSelected - 是否选中
   * @returns {string} HTML字符串
   */
  render(script, index, isSelected) {
    const statusConfig = this.getStatusConfig(script.status);
    const scheduleText = this.formatSchedule(script.schedule);
    const lastRunText = script.lastRun ? this.formatTime(script.lastRun) : '从未运行';

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
   * @param {string} status - 状态码
   * @returns {Object} 状态配置
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
   * @param {string} schedule - Cron表达式
   * @returns {string} 格式化后的文本
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
   * @param {string} timestamp - 时间戳
   * @returns {string} 格式化后的时间文本
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
}
