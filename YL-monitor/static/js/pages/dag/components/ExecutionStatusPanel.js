/**
 * DAG执行状态实时面板组件
 * 版本: v1.0.0
 */

export class ExecutionStatusPanel {
  constructor(page) {
    this.page = page;
    this.container = null;
    this.ws = null;
    this.currentExecution = null;
    this.isExpanded = true;
  }

  /**
   * 初始化面板
   * @param {HTMLElement} container - 容器元素
   */
  init(container) {
    this.container = container;
    this.render();
    this.bindEvents();
  }

  /**
   * 渲染面板
   */
  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="execution-status-panel" id="execution-status-panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="status-indicator" id="execution-status-indicator"></span>
            <span>执行状态</span>
          </div>
          <div class="panel-actions">
            <button class="btn btn-sm btn-ghost" data-action="toggle-panel" title="折叠/展开">
              <span id="toggle-icon">▼</span>
            </button>
            <button class="btn btn-sm btn-ghost" data-action="close-panel" title="关闭">
              ✕
            </button>
          </div>
        </div>
        
        <div class="panel-content" id="panel-content">
          <!-- 执行概览 -->
          <div class="execution-overview">
            <div class="overview-item">
              <span class="overview-label">状态</span>
              <span class="overview-value" id="execution-status-text">未开始</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">进度</span>
              <span class="overview-value" id="execution-progress-text">0%</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">已运行</span>
              <span class="overview-value" id="execution-duration">-</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">当前节点</span>
              <span class="overview-value" id="current-node">-</span>
            </div>
          </div>
          
          <!-- 进度条 -->
          <div class="progress-section">
            <div class="progress-bar-container">
              <div class="progress-bar" id="execution-progress-bar" style="width: 0%"></div>
            </div>
          </div>
          
          <!-- 节点执行列表 -->
          <div class="nodes-execution-list">
            <div class="list-header">
              <span>节点执行顺序</span>
              <span id="completed-count">0/0</span>
            </div>
            <div class="nodes-list" id="nodes-execution-list">
              <div class="empty-state">暂无执行数据</div>
            </div>
          </div>
          
          <!-- 实时日志 -->
          <div class="execution-logs-section">
            <div class="logs-header">
              <span>📋 实时日志</span>
              <button class="btn btn-xs btn-ghost" data-action="clear-logs">
                清空
              </button>
            </div>
            <div class="logs-container" id="execution-logs-container">
              <div class="log-placeholder">等待执行开始...</div>
            </div>
          </div>
          
          <!-- 控制按钮 -->
          <div class="execution-controls">
            <button class="btn btn-primary" data-action="start-execution" id="btn-start-exec">
              ▶️ 开始执行
            </button>
            <button class="btn btn-warning" data-action="pause-execution" id="btn-pause-exec" disabled>
              ⏸️ 暂停
            </button>
            <button class="btn btn-danger" data-action="stop-execution" id="btn-stop-exec" disabled>
              ⏹️ 停止
            </button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.container) return;

    // 折叠/展开
    this.container.querySelector('[data-action="toggle-panel"]').addEventListener('click', () => {
      this.togglePanel();
    });

    // 关闭面板
    this.container.querySelector('[data-action="close-panel"]').addEventListener('click', () => {
      this.close();
    });

    // 控制按钮
    this.container.querySelector('[data-action="start-execution"]').addEventListener('click', () => {
      this.startExecution();
    });

    this.container.querySelector('[data-action="pause-execution"]').addEventListener('click', () => {
      this.pauseExecution();
    });

    this.container.querySelector('[data-action="stop-execution"]').addEventListener('click', () => {
      this.stopExecution();
    });

    // 清空日志
    this.container.querySelector('[data-action="clear-logs"]').addEventListener('click', () => {
      this.clearLogs();
    });
  }

  /**
   * 切换面板折叠状态
   */
  togglePanel() {
    this.isExpanded = !this.isExpanded;
    const content = document.getElementById('panel-content');
    const icon = document.getElementById('toggle-icon');
    
    if (content) {
      content.style.display = this.isExpanded ? 'block' : 'none';
    }
    
    if (icon) {
      icon.textContent = this.isExpanded ? '▼' : '▶';
    }
  }

  /**
   * 开始执行
   */
  async startExecution() {
    try {
      const response = await fetch('/api/v1/dag/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dag_id: this.page.dagId,
          nodes: this.page.nodes.map(n => n.id),
          edges: this.page.edges
        })
      });

      if (!response.ok) {
        throw new Error('启动执行失败');
      }

      const data = await response.json();
      this.currentExecution = {
        id: data.execution_id,
        status: 'running',
        startTime: Date.now()
      };

      // 连接WebSocket
      this.connectWebSocket(data.execution_id);

      // 更新UI状态
      this.updateExecutionStatus('running');
      this.updateButtonStates('running');

      this.addLog('info', `执行已启动 [ID: ${data.execution_id}]`);

    } catch (error) {
      this.page.ui.showToast({
        type: 'error',
        message: `启动失败: ${error.message}`
      });
    }
  }

  /**
   * 暂停执行
   */
  async pauseExecution() {
    if (!this.currentExecution) return;

    try {
      const response = await fetch(`/api/v1/executions/${this.currentExecution.id}/pause`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('暂停失败');
      }

      this.updateExecutionStatus('paused');
      this.updateButtonStates('paused');
      this.addLog('warning', '执行已暂停');

    } catch (error) {
      this.page.ui.showToast({
        type: 'error',
        message: `暂停失败: ${error.message}`
      });
    }
  }

  /**
   * 停止执行
   */
  async stopExecution() {
    if (!this.currentExecution) return;

    this.page.ui.showConfirm({
      title: '停止执行',
      message: '确定要停止当前DAG执行吗？',
      type: 'warning',
      confirmText: '停止',
      onConfirm: async () => {
        try {
          const response = await fetch(`/api/v1/executions/${this.currentExecution.id}/stop`, {
            method: 'POST'
          });

          if (!response.ok) {
            throw new Error('停止失败');
          }

          this.updateExecutionStatus('stopped');
          this.updateButtonStates('stopped');
          this.addLog('error', '执行已停止');

          // 断开WebSocket
          this.disconnectWebSocket();

        } catch (error) {
          this.page.ui.showToast({
            type: 'error',
            message: `停止失败: ${error.message}`
          });
        }
      }
    });
  }

  /**
   * 连接WebSocket
   * @param {string} executionId - 执行ID
   */
  connectWebSocket(executionId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dag/executions/${executionId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[ExecutionStatusPanel] WebSocket已连接');
        this.addLog('info', '已连接到执行状态服务');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('[ExecutionStatusPanel] 消息解析失败:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('[ExecutionStatusPanel] WebSocket已断开');
        this.addLog('info', '执行状态连接已关闭');
      };

      this.ws.onerror = (error) => {
        console.error('[ExecutionStatusPanel] WebSocket错误:', error);
        this.addLog('error', '执行状态连接出错');
      };

    } catch (error) {
      console.error('[ExecutionStatusPanel] 创建WebSocket失败:', error);
    }
  }

  /**
   * 断开WebSocket
   */
  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 处理WebSocket消息
   * @param {Object} data - 消息数据
   */
  handleMessage(data) {
    switch (data.type) {
      case 'status':
        this.updateExecutionStatus(data.status);
        break;
        
      case 'progress':
        this.updateProgress(data.progress, data.current_node);
        break;
        
      case 'node_start':
        this.handleNodeStart(data.node_id, data.node_name);
        break;
        
      case 'node_complete':
        this.handleNodeComplete(data.node_id, data.result);
        break;
        
      case 'node_error':
        this.handleNodeError(data.node_id, data.error);
        break;
        
      case 'log':
        this.addLog(data.level, data.message, data.timestamp);
        break;
        
      case 'complete':
        this.handleExecutionComplete(data);
        break;
        
      default:
        console.log('[ExecutionStatusPanel] 未知消息类型:', data.type);
    }
  }

  /**
   * 更新执行状态
   * @param {string} status - 状态
   */
  updateExecutionStatus(status) {
    const indicator = document.getElementById('execution-status-indicator');
    const statusText = document.getElementById('execution-status-text');
    
    const statusMap = {
      'running': { text: '运行中', class: 'running', color: '#10b981' },
      'paused': { text: '已暂停', class: 'paused', color: '#f59e0b' },
      'stopped': { text: '已停止', class: 'stopped', color: '#ef4444' },
      'completed': { text: '已完成', class: 'completed', color: '#3b82f6' },
      'failed': { text: '失败', class: 'failed', color: '#ef4444' }
    };

    const info = statusMap[status] || statusMap['stopped'];
    
    if (indicator) {
      indicator.className = `status-indicator ${info.class}`;
    }
    
    if (statusText) {
      statusText.textContent = info.text;
      statusText.style.color = info.color;
    }

    if (this.currentExecution) {
      this.currentExecution.status = status;
    }
  }

  /**
   * 更新进度
   * @param {number} progress - 进度百分比
   * @param {string} currentNode - 当前节点
   */
  updateProgress(progress, currentNode) {
    const progressBar = document.getElementById('execution-progress-bar');
    const progressText = document.getElementById('execution-progress-text');
    const currentNodeEl = document.getElementById('current-node');
    
    if (progressBar) {
      progressBar.style.width = `${progress}%`;
    }
    
    if (progressText) {
      progressText.textContent = `${Math.round(progress)}%`;
    }
    
    if (currentNodeEl && currentNode) {
      currentNodeEl.textContent = currentNode;
    }

    // 更新已运行时间
    this.updateDuration();
  }

  /**
   * 处理节点开始
   * @param {string} nodeId - 节点ID
   * @param {string} nodeName - 节点名称
   */
  handleNodeStart(nodeId, nodeName) {
    this.addNodeToList(nodeId, nodeName, 'running');
    this.addLog('info', `节点开始执行: ${nodeName}`);
  }

  /**
   * 处理节点完成
   * @param {string} nodeId - 节点ID
   * @param {Object} result - 执行结果
   */
  handleNodeComplete(nodeId, result) {
    this.updateNodeStatus(nodeId, 'completed');
    this.addLog('success', `节点执行完成: ${result.node_name || nodeId}`);
    this.updateCompletedCount();
  }

  /**
   * 处理节点错误
   * @param {string} nodeId - 节点ID
   * @param {string} error - 错误信息
   */
  handleNodeError(nodeId, error) {
    this.updateNodeStatus(nodeId, 'error');
    this.addLog('error', `节点执行失败 [${nodeId}]: ${error}`);
  }

  /**
   * 处理执行完成
   * @param {Object} data - 完成数据
   */
  handleExecutionComplete(data) {
    this.updateExecutionStatus(data.status);
    this.updateProgress(100, '-');
    this.updateButtonStates('completed');
    
    const duration = data.duration || (Date.now() - (this.currentExecution?.startTime || Date.now()));
    this.addLog('info', `执行完成 [状态: ${data.status}] [总耗时: ${this.formatDuration(duration)}]`);
    
    this.page.ui.showToast({
      type: data.status === 'success' ? 'success' : 'error',
      message: `DAG执行${data.status === 'success' ? '成功' : '失败'}`
    });

    // 断开WebSocket
    this.disconnectWebSocket();
  }

  /**
   * 添加节点到列表
   * @param {string} nodeId - 节点ID
   * @param {string} nodeName - 节点名称
   * @param {string} status - 状态
   */
  addNodeToList(nodeId, nodeName, status) {
    const list = document.getElementById('nodes-execution-list');
    if (!list) return;

    // 移除空状态
    const emptyState = list.querySelector('.empty-state');
    if (emptyState) {
      emptyState.remove();
    }

    const nodeEl = document.createElement('div');
    nodeEl.className = `node-execution-item ${status}`;
    nodeEl.id = `node-exec-${nodeId}`;
    nodeEl.innerHTML = `
      <span class="node-status-icon">${this.getStatusIcon(status)}</span>
      <span class="node-name">${nodeName || nodeId}</span>
      <span class="node-status">${status}</span>
    `;

    list.appendChild(nodeEl);
  }

  /**
   * 更新节点状态
   * @param {string} nodeId - 节点ID
   * @param {string} status - 状态
   */
  updateNodeStatus(nodeId, status) {
    const nodeEl = document.getElementById(`node-exec-${nodeId}`);
    if (nodeEl) {
      nodeEl.className = `node-execution-item ${status}`;
      const statusIcon = nodeEl.querySelector('.node-status-icon');
      const statusText = nodeEl.querySelector('.node-status');
      
      if (statusIcon) {
        statusIcon.textContent = this.getStatusIcon(status);
      }
      
      if (statusText) {
        statusText.textContent = status;
      }
    }
  }

  /**
   * 获取状态图标
   * @param {string} status - 状态
   * @returns {string}
   */
  getStatusIcon(status) {
    const icons = {
      'running': '⏳',
      'completed': '✅',
      'error': '❌',
      'pending': '⏸️'
    };
    return icons[status] || '⏸️';
  }

  /**
   * 更新已完成计数
   */
  updateCompletedCount() {
    const list = document.getElementById('nodes-execution-list');
    const countEl = document.getElementById('completed-count');
    
    if (!list || !countEl) return;
    
    const items = list.querySelectorAll('.node-execution-item');
    const completed = list.querySelectorAll('.node-execution-item.completed').length;
    
    countEl.textContent = `${completed}/${items.length}`;
  }

  /**
   * 更新按钮状态
   * @param {string} status - 执行状态
   */
  updateButtonStates(status) {
    const startBtn = document.getElementById('btn-start-exec');
    const pauseBtn = document.getElementById('btn-pause-exec');
    const stopBtn = document.getElementById('btn-stop-exec');

    const states = {
      'running': { start: true, pause: false, stop: false },
      'paused': { start: false, pause: true, stop: false },
      'stopped': { start: false, pause: true, stop: true },
      'completed': { start: false, pause: true, stop: true }
    };

    const state = states[status] || states['stopped'];
    
    if (startBtn) startBtn.disabled = state.start;
    if (pauseBtn) pauseBtn.disabled = state.pause;
    if (stopBtn) stopBtn.disabled = state.stop;
  }

  /**
   * 更新运行时长
   */
  updateDuration() {
    if (!this.currentExecution || !this.currentExecution.startTime) return;
    
    const duration = Date.now() - this.currentExecution.startTime;
    const durationEl = document.getElementById('execution-duration');
    
    if (durationEl) {
      durationEl.textContent = this.formatDuration(duration);
    }
  }

  /**
   * 格式化时长
   * @param {number} ms - 毫秒
   * @returns {string}
   */
  formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * 添加日志
   * @param {string} level - 日志级别
   * @param {string} message - 消息
   * @param {string} timestamp - 时间戳
   */
  addLog(level, message, timestamp) {
    const container = document.getElementById('execution-logs-container');
    if (!container) return;

    const placeholder = container.querySelector('.log-placeholder');
    if (placeholder) {
      placeholder.remove();
    }

    const time = timestamp 
      ? new Date(timestamp).toLocaleTimeString('zh-CN')
      : new Date().toLocaleTimeString('zh-CN');

    const logEl = document.createElement('div');
    logEl.className = `execution-log log-${level}`;
    logEl.innerHTML = `
      <span class="log-time">[${time}]</span>
      <span class="log-level">${level.toUpperCase()}</span>
      <span class="log-message">${this.escapeHtml(message)}</span>
    `;

    container.appendChild(logEl);
    container.scrollTop = container.scrollHeight;
  }

  /**
   * 清空日志
   */
  clearLogs() {
    const container = document.getElementById('execution-logs-container');
    if (container) {
      container.innerHTML = '<div class="log-placeholder">日志已清空</div>';
    }
  }

  /**
   * HTML转义
   * @param {string} text - 文本
   * @returns {string}
   */
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * 关闭面板
   */
  close() {
    this.disconnectWebSocket();
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}
