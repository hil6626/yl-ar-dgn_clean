/**
 * 脚本执行进度跟踪组件
 * 显示实时执行进度和日志
 * 版本: v1.0.0
 */

export class ExecutionProgressTracker {
  constructor(options = {}) {
    this.options = {
      onClose: () => {},
      onStop: () => {},
      ...options
    };
    
    this.modal = null;
    this.executionId = null;
    this.scriptId = null;
    this.scriptName = '';
    this.logs = [];
    this.progress = 0;
    this.status = 'running'; // running, completed, error, stopped
    this.startTime = null;
    this.logWebSocketManager = null;
  }

  /**
   * 显示进度跟踪弹窗
   * @param {Object} params - 参数
   */
  show(params) {
    this.executionId = params.executionId;
    this.scriptId = params.scriptId;
    this.scriptName = params.scriptName || '未知脚本';
    this.startTime = new Date();
    this.logs = [];
    this.progress = 0;
    this.status = 'running';
    
    this.render();
    this.bindEvents();
    this.startLogStreaming();
    
    console.log(`[ExecutionProgressTracker] 显示执行进度: ${this.executionId}`);
  }

  /**
   * 渲染弹窗
   */
  render() {
    // 移除已存在的弹窗
    this.close();
    
    this.modal = document.createElement('div');
    this.modal.className = 'execution-progress-modal';
    this.modal.id = 'execution-progress-modal';
    this.modal.innerHTML = `
      <div class="execution-progress-overlay">
        <div class="execution-progress-content">
          <div class="execution-progress-header">
            <div class="execution-title">
              <span class="execution-icon">▶️</span>
              <span>${this.scriptName}</span>
              <span class="execution-id">#${this.executionId.slice(-8)}</span>
            </div>
            <div class="execution-actions">
              <button class="btn btn-sm btn-warning" id="btn-stop-execution" title="停止执行">
                ⏹️ 停止
              </button>
              <button class="btn btn-sm btn-ghost" id="btn-close-modal" title="关闭">
                ✕
              </button>
            </div>
          </div>
          
          <div class="execution-progress-body">
            <!-- 进度概览 -->
            <div class="execution-overview">
              <div class="progress-section">
                <div class="progress-header">
                  <span class="progress-label">执行进度</span>
                  <span class="progress-value" id="progress-value">0%</span>
                </div>
                <div class="progress-bar-container">
                  <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
                </div>
              </div>
              
              <div class="execution-stats">
                <div class="stat-item">
                  <span class="stat-label">状态</span>
                  <span class="stat-value" id="execution-status">
                    <span class="status-badge running">运行中</span>
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">开始时间</span>
                  <span class="stat-value" id="start-time">
                    ${this.startTime.toLocaleTimeString('zh-CN')}
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">运行时长</span>
                  <span class="stat-value" id="duration">00:00</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">日志条数</span>
                  <span class="stat-value" id="log-count">0</span>
                </div>
              </div>
            </div>
            
            <!-- 日志查看器 -->
            <div class="execution-logs-section">
              <div class="logs-header">
                <span class="logs-title">📋 执行日志</span>
                <div class="logs-actions">
                  <button class="btn btn-xs btn-ghost" id="btn-clear-logs">
                    清空
                  </button>
                  <button class="btn btn-xs btn-ghost" id="btn-download-logs">
                    下载
                  </button>
                  <button class="btn btn-xs btn-ghost" id="btn-auto-scroll" class="active">
                    自动滚动
                  </button>
                </div>
              </div>
              
              <div class="logs-container" id="logs-container">
                <div class="logs-empty">等待日志输出...</div>
              </div>
            </div>
          </div>
          
          <div class="execution-progress-footer">
            <div class="execution-summary" id="execution-summary"></div>
            <button class="btn btn-primary" id="btn-confirm-close" style="display: none;">
              确定
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.modal);
    
    // 显示动画
    requestAnimationFrame(() => {
      this.modal.classList.add('active');
    });
    
    // 启动时长计时器
    this.startDurationTimer();
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 关闭按钮
    this.modal.querySelector('#btn-close-modal')?.addEventListener('click', () => {
      this.close();
    });
    
    // 确认关闭按钮
    this.modal.querySelector('#btn-confirm-close')?.addEventListener('click', () => {
      this.close();
    });
    
    // 停止执行
    this.modal.querySelector('#btn-stop-execution')?.addEventListener('click', () => {
      this.stopExecution();
    });
    
    // 清空日志
    this.modal.querySelector('#btn-clear-logs')?.addEventListener('click', () => {
      this.clearLogs();
    });
    
    // 下载日志
    this.modal.querySelector('#btn-download-logs')?.addEventListener('click', () => {
      this.downloadLogs();
    });
    
    // 自动滚动切换
    this.modal.querySelector('#btn-auto-scroll')?.addEventListener('click', (e) => {
      e.target.classList.toggle('active');
    });
    
    // 点击遮罩关闭
    this.modal.querySelector('.execution-progress-overlay')?.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.close();
      }
    });
  }

  /**
   * 开始日志流
   */
  startLogStreaming() {
    // 使用LogWebSocketManager订阅日志
    if (this.options.logWebSocketManager) {
      this.logWebSocketManager = this.options.logWebSocketManager;
      
      // 订阅日志事件
      this.logWebSocketManager.on('log', (log) => {
        if (log.executionId === this.executionId) {
          this.addLog(log);
        }
      });
      
      // 订阅执行完成事件
      this.logWebSocketManager.on('execution_complete', (data) => {
        if (data.executionId === this.executionId) {
          this.handleExecutionComplete(data);
        }
      });
      
      // 订阅执行错误事件
      this.logWebSocketManager.on('execution_error', (data) => {
        if (data.executionId === this.executionId) {
          this.handleExecutionError(data);
        }
      });
      
      // 请求历史日志
      this.logWebSocketManager.requestHistoryLogs(this.executionId, { limit: 50 });
    }
  }

  /**
   * 添加日志
   * @param {Object} log - 日志对象
   */
  addLog(log) {
    this.logs.push(log);
    
    const container = this.modal?.querySelector('#logs-container');
    if (!container) return;
    
    // 移除空提示
    const emptyMsg = container.querySelector('.logs-empty');
    if (emptyMsg) {
      emptyMsg.remove();
    }
    
    // 创建日志项
    const logItem = document.createElement('div');
    logItem.className = `log-item log-${log.level}`;
    logItem.innerHTML = `
      <span class="log-time">${log.formattedTime}</span>
      <span class="log-level">${log.level.toUpperCase()}</span>
      <span class="log-content">${this.escapeHtml(log.content)}</span>
    `;
    
    container.appendChild(logItem);
    
    // 更新日志计数
    const countEl = this.modal?.querySelector('#log-count');
    if (countEl) {
      countEl.textContent = this.logs.length;
    }
    
    // 自动滚动
    const autoScrollBtn = this.modal?.querySelector('#btn-auto-scroll');
    if (autoScrollBtn?.classList.contains('active')) {
      container.scrollTop = container.scrollHeight;
    }
    
    // 根据日志内容更新进度（启发式）
    this.updateProgressFromLog(log.content);
  }

  /**
   * 从日志内容更新进度
   * @param {string} content - 日志内容
   */
  updateProgressFromLog(content) {
    // 尝试从日志中提取进度信息
    const progressMatch = content.match(/(\d+)%/);
    if (progressMatch) {
      const newProgress = parseInt(progressMatch[1]);
      if (newProgress > this.progress) {
        this.updateProgress(newProgress);
      }
    }
    
    // 关键词检测
    if (content.includes('完成') || content.includes('finished') || content.includes('completed')) {
      this.updateProgress(100);
    }
  }

  /**
   * 更新进度
   * @param {number} progress - 进度百分比
   */
  updateProgress(progress) {
    this.progress = Math.min(100, Math.max(0, progress));
    
    const progressBar = this.modal?.querySelector('#progress-bar');
    const progressValue = this.modal?.querySelector('#progress-value');
    
    if (progressBar) {
      progressBar.style.width = `${this.progress}%`;
    }
    
    if (progressValue) {
      progressValue.textContent = `${this.progress}%`;
    }
  }

  /**
   * 处理执行完成
   * @param {Object} data - 完成数据
   */
  handleExecutionComplete(data) {
    this.status = data.success ? 'completed' : 'error';
    this.updateProgress(100);
    
    // 更新状态显示
    const statusEl = this.modal?.querySelector('#execution-status');
    if (statusEl) {
      statusEl.innerHTML = `
        <span class="status-badge ${this.status}">
          ${data.success ? '✅ 完成' : '❌ 失败'}
        </span>
      `;
    }
    
    // 更新摘要
    const summaryEl = this.modal?.querySelector('#execution-summary');
    if (summaryEl) {
      summaryEl.innerHTML = `
        <span class="summary-item">
          退出码: <strong>${data.exitCode}</strong>
        </span>
        <span class="summary-item">
          总日志: <strong>${this.logs.length}</strong> 条
        </span>
      `;
    }
    
    // 显示确认关闭按钮
    const confirmBtn = this.modal?.querySelector('#btn-confirm-close');
    if (confirmBtn) {
      confirmBtn.style.display = 'block';
    }
    
    // 禁用停止按钮
    const stopBtn = this.modal?.querySelector('#btn-stop-execution');
    if (stopBtn) {
      stopBtn.disabled = true;
      stopBtn.textContent = '⏹️ 已结束';
    }
    
    this.stopDurationTimer();
  }

  /**
   * 处理执行错误
   * @param {Object} data - 错误数据
   */
  handleExecutionError(data) {
    this.status = 'error';
    
    // 更新状态显示
    const statusEl = this.modal?.querySelector('#execution-status');
    if (statusEl) {
      statusEl.innerHTML = `<span class="status-badge error">❌ 错误</span>`;
    }
    
    // 添加错误日志
    this.addLog({
      level: 'error',
      content: `执行错误: ${data.error}`,
      timestamp: new Date(),
      formattedTime: new Date().toLocaleTimeString('zh-CN')
    });
    
    this.stopDurationTimer();
  }

  /**
   * 停止执行
   */
  stopExecution() {
    if (this.options.onStop) {
      this.options.onStop(this.executionId);
    }
    
    this.addLog({
      level: 'warning',
      content: '用户请求停止执行',
      timestamp: new Date(),
      formattedTime: new Date().toLocaleTimeString('zh-CN')
    });
  }

  /**
   * 清空日志
   */
  clearLogs() {
    this.logs = [];
    const container = this.modal?.querySelector('#logs-container');
    if (container) {
      container.innerHTML = '<div class="logs-empty">日志已清空</div>';
    }
    
    const countEl = this.modal?.querySelector('#log-count');
    if (countEl) {
      countEl.textContent = '0';
    }
  }

  /**
   * 下载日志
   */
  downloadLogs() {
    const logText = this.logs.map(log => 
      `[${log.formattedTime}] [${log.level.toUpperCase()}] ${log.content}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution-${this.executionId.slice(-8)}-logs.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
  }

  /**
   * 启动时长计时器
   */
  startDurationTimer() {
    this.durationTimer = setInterval(() => {
      const duration = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
      const minutes = Math.floor(duration / 60).toString().padStart(2, '0');
      const seconds = (duration % 60).toString().padStart(2, '0');
      
      const durationEl = this.modal?.querySelector('#duration');
      if (durationEl) {
        durationEl.textContent = `${minutes}:${seconds}`;
      }
    }, 1000);
  }

  /**
   * 停止时长计时器
   */
  stopDurationTimer() {
    if (this.durationTimer) {
      clearInterval(this.durationTimer);
      this.durationTimer = null;
    }
  }

  /**
   * HTML转义
   * @param {string} html - HTML字符串
   * @returns {string}
   */
  escapeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }

  /**
   * 关闭弹窗
   */
  close() {
    this.stopDurationTimer();
    
    if (this.modal) {
      this.modal.classList.remove('active');
      setTimeout(() => {
        if (this.modal) {
          this.modal.remove();
          this.modal = null;
        }
      }, 300);
    }
    
    if (this.options.onClose) {
      this.options.onClose();
    }
  }

  /**
   * 销毁
   */
  destroy() {
    this.close();
    this.logs = [];
  }
}
