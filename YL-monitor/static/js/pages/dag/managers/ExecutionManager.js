/**
 * 执行管理器 - 处理DAG执行控制
 * 拆分自: page-dag.js 中的执行相关方法
 * 版本: v1.0.0
 */

export class ExecutionManager {
  /**
   * @param {DAGPage} page - DAG页面实例
   */
  constructor(page) {
    this.page = page;
    this.executionStatus = 'idle'; // idle, running, success, error, stopped
    this.executionProgress = 0;
    this.executionInterval = null;
  }

  /**
   * 运行DAG
   */
  async run() {
    this.executionStatus = 'running';
    this.executionProgress = 0;
    
    // 更新UI
    this.updateExecutionUI('running');
    
    // 展开执行面板
    this.expandExecutionPanel();
    
    // 模拟执行进度
    this.startProgressSimulation();
    
    // 调用后端API
    try {
      await fetch(`${this.page.apiBaseUrl}/dag/execute`, { method: 'POST' });
    } catch (error) {
      console.warn('[ExecutionManager] 执行请求失败:', error);
    }
  }

  /**
   * 停止DAG执行
   */
  stop() {
    this.executionStatus = 'stopped';
    this.stopProgressSimulation();
    
    // 更新UI
    this.updateExecutionUI('stopped');
    
    // 添加日志
    this.addExecutionLog('error', 'DAG执行已停止');
    this.page.ui.showToast({ type: 'warning', message: 'DAG已停止' });
  }

  /**
   * 执行完成
   */
  complete() {
    this.executionStatus = 'success';
    this.stopProgressSimulation();
    
    // 更新UI
    this.updateExecutionUI('success');
    
    // 添加日志
    this.addExecutionLog('success', 'DAG执行完成');
    this.page.ui.showToast({ type: 'success', message: 'DAG执行完成' });
  }

  /**
   * 开始进度模拟
   */
  startProgressSimulation() {
    this.executionInterval = setInterval(() => {
      if (this.executionStatus !== 'running') {
        this.stopProgressSimulation();
        return;
      }
      
      this.executionProgress += 5;
      
      // 更新进度条
      this.updateProgressBar();
      
      // 添加日志
      this.addExecutionLog('info', `执行进度: ${this.executionProgress}%`);
      
      if (this.executionProgress >= 100) {
        this.complete();
      }
    }, 500);
  }

  /**
   * 停止进度模拟
   */
  stopProgressSimulation() {
    if (this.executionInterval) {
      clearInterval(this.executionInterval);
      this.executionInterval = null;
    }
  }

  /**
   * 更新执行UI状态
   * @param {string} status - 执行状态
   */
  updateExecutionUI(status) {
    const btnRun = document.getElementById('btn-run');
    const btnStop = document.getElementById('btn-stop');
    const statusBadge = document.getElementById('execution-status');
    
    const statusConfig = {
      running: { text: '运行中', className: 'running', runDisabled: true, stopDisabled: false },
      success: { text: '完成', className: 'success', runDisabled: false, stopDisabled: true },
      stopped: { text: '已停止', className: 'error', runDisabled: false, stopDisabled: true },
      error: { text: '失败', className: 'error', runDisabled: false, stopDisabled: true },
      idle: { text: '就绪', className: 'pending', runDisabled: false, stopDisabled: true }
    };
    
    const config = statusConfig[status] || statusConfig.idle;
    
    if (btnRun) {
      btnRun.disabled = config.runDisabled;
    }
    if (btnStop) {
      btnStop.disabled = config.stopDisabled;
    }
    if (statusBadge) {
      statusBadge.textContent = config.text;
      statusBadge.className = `execution-status-badge ${config.className}`;
    }
  }

  /**
   * 更新进度条
   */
  updateProgressBar() {
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');
    
    if (fill) {
      fill.style.width = `${this.executionProgress}%`;
    }
    if (text) {
      text.textContent = `${this.executionProgress}%`;
    }
  }

  /**
   * 展开执行面板
   */
  expandExecutionPanel() {
    const panel = document.getElementById('dag-execution-panel');
    if (panel) {
      panel.classList.remove('collapsed');
      panel.classList.add('expanded');
    }
  }

  /**
   * 添加执行日志
   * @param {string} level - 日志级别 (info, success, error, warning)
   * @param {string} message - 日志消息
   */
  addExecutionLog(level, message) {
    const logsContainer = document.getElementById('execution-logs');
    if (!logsContainer) return;
    
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    const logItem = document.createElement('div');
    logItem.className = 'execution-log-item';
    logItem.innerHTML = `
      <span class="execution-log-time">${time}</span>
      <span class="execution-log-level ${level}">${level.toUpperCase()}</span>
      <span class="execution-log-message">${message}</span>
    `;
    
    logsContainer.appendChild(logItem);
    logsContainer.scrollTop = logsContainer.scrollHeight;
  }

  /**
   * 清除执行日志
   */
  clearExecutionLogs() {
    const logsContainer = document.getElementById('execution-logs');
    if (logsContainer) {
      logsContainer.innerHTML = '';
    }
  }

  /**
   * 获取执行状态
   * @returns {string}
   */
  getStatus() {
    return this.executionStatus;
  }

  /**
   * 获取执行进度
   * @returns {number}
   */
  getProgress() {
    return this.executionProgress;
  }

  /**
   * 是否正在执行
   * @returns {boolean}
   */
  isRunning() {
    return this.executionStatus === 'running';
  }
}
