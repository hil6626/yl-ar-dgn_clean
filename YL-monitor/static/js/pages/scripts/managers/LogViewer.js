/**
 * 日志查看器管理器
 * 拆分自: page-scripts.js viewLogs() 和 generateSampleLogs()
 * 版本: v1.0.0
 */

export class LogViewer {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
    this.modal = null;
    this.container = null;
  }

  /**
   * 查看脚本日志
   * @param {string} scriptId - 脚本ID
   */
  async view(scriptId) {
    const script = this.page.scripts.find(s => s.id === scriptId);
    if (!script) return;

    this.modal = document.getElementById('logs-modal');
    this.container = document.getElementById('logs-container');

    // 显示加载状态
    this.container.innerHTML = '<div class="logs-loading">加载中...</div>';
    this.modal.classList.remove('hidden');

    try {
      // 尝试从后端获取日志
      const logs = await this.fetchLogs(scriptId);
      this.render(logs);
    } catch (error) {
      // 使用示例日志
      const logs = this.generateSampleLogs(script.name);
      this.render(logs);
    }
  }

  /**
   * 从后端获取日志
   * @param {string} scriptId - 脚本ID
   * @returns {Promise<Array>}
   */
  async fetchLogs(scriptId) {
    const response = await fetch(`${this.page.apiBaseUrl}/scripts/${scriptId}/logs`);
    if (!response.ok) throw new Error('获取日志失败');
    return await response.json();
  }

  /**
   * 渲染日志
   * @param {Array} logs - 日志数据
   */
  render(logs) {
    if (!this.container) return;

    this.container.innerHTML = logs.map(log => `
      <div class="log-entry">
        <span class="log-time">${log.time}</span>
        <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
        <span class="log-message">${log.message}</span>
      </div>
    `).join('');

    // 滚动到底部
    this.container.scrollTop = this.container.scrollHeight;
  }

  /**
   * 生成示例日志
   * @param {string} scriptName - 脚本名称
   * @returns {Array} 示例日志
   */
  generateSampleLogs(scriptName) {
    const levels = ['info', 'success', 'warning', 'error'];
    const messages = [
      `[${scriptName}] 脚本开始执行`,
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
   * 关闭日志查看器
   */
  close() {
    if (this.modal) {
      this.modal.classList.add('hidden');
    }
  }
}
