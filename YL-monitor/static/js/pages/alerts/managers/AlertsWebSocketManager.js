/**
 * Alerts WebSocket管理器
 * 实现自动重连和心跳检测
 * 版本: v1.0.0
 */

export class AlertsWebSocketManager {
  constructor(options = {}) {
    this.options = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...options
    };
    
    this.ws = null;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.isConnected = false;
    this.listeners = new Map();
    this.connectionStatus = 'disconnected'; // disconnected, connecting, connected, reconnecting, error
  }

  /**
   * 初始化WebSocket连接
   */
  init() {
    this.connect();
    console.log('[AlertsWebSocketManager] 初始化完成');
  }

  /**
   * 建立WebSocket连接
   */
  connect() {
    try {
      const wsUrl = this.getWebSocketUrl();
      this.updateStatus('connecting');
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = () => this.handleClose();
      this.ws.onerror = (error) => this.handleError(error);
      
    } catch (error) {
      console.error('[AlertsWebSocketManager] 连接失败:', error);
      this.updateStatus('error');
      this.scheduleReconnect();
    }
  }

  /**
   * 获取WebSocket URL
   * @returns {string}
   */
  getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/alerts`;
  }

  /**
   * 连接打开处理
   */
  handleOpen() {
    console.log('[AlertsWebSocketManager] WebSocket已连接');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.updateStatus('connected');
    
    // 发送初始化消息
    this.send({
      type: 'init',
      client: 'yl-monitor',
      version: '1.0.0'
    });
    
    // 启动心跳
    this.startHeartbeat();
    
    // 通知所有监听器
    this.emit('connected', { timestamp: Date.now() });
    this.emit('status_change', { status: 'connected' });
  }

  /**
   * 消息处理
   * @param {MessageEvent} event - 消息事件
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'alert':
          this.handleAlertMessage(message);
          break;
        case 'alert_update':
          this.handleAlertUpdate(message);
          break;
        case 'alert_resolved':
          this.handleAlertResolved(message);
          break;
        case 'stats_update':
          this.handleStatsUpdate(message);
          break;
        case 'heartbeat':
          // 心跳响应，无需处理
          break;
        default:
          console.log('[AlertsWebSocketManager] 未知消息类型:', message.type);
      }
      
      // 通知通用监听器
      this.emit('message', message);
      
    } catch (error) {
      console.error('[AlertsWebSocketManager] 消息解析失败:', error);
    }
  }

  /**
   * 处理告警消息
   * @param {Object} message - 告警消息
   */
  handleAlertMessage(message) {
    const { alert } = message.data;
    
    this.emit('new_alert', {
      alert,
      timestamp: new Date()
    });
    
    // 显示通知
    this.showNotification('warning', `新告警: ${alert.title}`);
  }

  /**
   * 处理告警更新
   * @param {Object} message - 更新消息
   */
  handleAlertUpdate(message) {
    const { alert_id, changes } = message.data;
    
    this.emit('alert_update', {
      alertId: alert_id,
      changes,
      timestamp: new Date()
    });
  }

  /**
   * 处理告警解决
   * @param {Object} message - 解决消息
   */
  handleAlertResolved(message) {
    const { alert_id, resolved_by } = message.data;
    
    this.emit('alert_resolved', {
      alertId: alert_id,
      resolvedBy: resolved_by,
      timestamp: new Date()
    });
    
    this.showNotification('success', '告警已解决');
  }

  /**
   * 处理统计更新
   * @param {Object} message - 统计消息
   */
  handleStatsUpdate(message) {
    const { stats } = message.data;
    
    this.emit('stats_update', {
      stats,
      timestamp: new Date()
    });
  }

  /**
   * 连接关闭处理
   */
  handleClose() {
    console.log('[AlertsWebSocketManager] WebSocket已关闭');
    this.isConnected = false;
    this.stopHeartbeat();
    this.updateStatus('disconnected');
    this.scheduleReconnect();
  }

  /**
   * 错误处理
   * @param {Error} error - 错误对象
   */
  handleError(error) {
    console.error('[AlertsWebSocketManager] WebSocket错误:', error);
    this.updateStatus('error');
    this.emit('error', error);
  }

  /**
   * 安排重连
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('[AlertsWebSocketManager] 重连次数超限，停止重连');
      this.updateStatus('error');
      this.emit('reconnect_failed');
      return;
    }
    
    this.reconnectAttempts++;
    this.updateStatus('reconnecting');
    
    const delay = Math.min(
      this.options.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1),
      30000
    );
    
    console.log(`[AlertsWebSocketManager] ${delay/1000}秒后尝试第${this.reconnectAttempts}次重连...`);
    
    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.options.maxReconnectAttempts,
      delay: delay
    });
    
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * 启动心跳
   */
  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'heartbeat',
          timestamp: Date.now()
        });
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * 停止心跳
   */
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 发送消息
   * @param {Object} message - 消息对象
   */
  send(message) {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[AlertsWebSocketManager] WebSocket未连接，无法发送消息');
    }
  }

  /**
   * 更新连接状态
   * @param {string} status - 状态
   */
  updateStatus(status) {
    this.connectionStatus = status;
    this.emit('status_change', { status });
    
    // 更新UI状态指示器
    this.updateStatusIndicator(status);
  }

  /**
   * 更新状态指示器UI
   * @param {string} status - 状态
   */
  updateStatusIndicator(status) {
    const indicator = document.getElementById('alerts-ws-status');
    if (!indicator) return;
    
    const statusConfig = {
      connected: { class: 'online', text: '已连接', icon: '🟢' },
      connecting: { class: 'connecting', text: '连接中...', icon: '🟡' },
      reconnecting: { class: 'reconnecting', text: '重连中...', icon: '🟠' },
      disconnected: { class: 'offline', text: '已断开', icon: '🔴' },
      error: { class: 'error', text: '连接错误', icon: '❌' }
    };
    
    const config = statusConfig[status] || statusConfig.disconnected;
    indicator.className = `ws-status-indicator ${config.class}`;
    indicator.innerHTML = `${config.icon} ${config.text}`;
  }

  /**
   * 显示通知
   * @param {string} type - 类型
   * @param {string} message - 消息
   */
  showNotification(type, message) {
    if (window.YLMonitor?.uiComponents?.showToast) {
      window.YLMonitor.uiComponents.showToast({ type, message });
    }
  }

  /**
   * 添加事件监听器
   * @param {string} event - 事件名
   * @param {Function} callback - 回调函数
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  /**
   * 移除事件监听器
   * @param {string} event - 事件名
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件名
   * @param {*} data - 数据
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('[AlertsWebSocketManager] 监听器错误:', error);
        }
      });
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.updateStatus('disconnected');
    
    console.log('[AlertsWebSocketManager] 已断开连接');
  }

  /**
   * 获取连接状态
   * @returns {Object}
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      status: this.connectionStatus,
      reconnectAttempts: this.reconnectAttempts,
      url: this.getWebSocketUrl()
    };
  }
}
