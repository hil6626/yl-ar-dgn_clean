/**
 * Scripts日志WebSocket管理器
 * 实现实时日志推送和查看
 * 版本: v1.0.0
 */

export class LogWebSocketManager {
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
    this.activeLogStreams = new Set(); // 当前活跃的日志流
  }

  /**
   * 初始化WebSocket连接
   */
  init() {
    this.connect();
    console.log('[LogWebSocketManager] 初始化完成');
  }

  /**
   * 建立WebSocket连接
   */
  connect() {
    try {
      const wsUrl = this.getWebSocketUrl();
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = () => this.handleClose();
      this.ws.onerror = (error) => this.handleError(error);
      
    } catch (error) {
      console.error('[LogWebSocketManager] 连接失败:', error);
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
    return `${protocol}//${host}/ws/scripts/logs`;
  }

  /**
   * 连接打开处理
   */
  handleOpen() {
    console.log('[LogWebSocketManager] WebSocket已连接');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
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
  }

  /**
   * 消息处理
   * @param {MessageEvent} event - 消息事件
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'log':
          this.handleLogMessage(message);
          break;
        case 'log_batch':
          this.handleLogBatch(message);
          break;
        case 'execution_start':
          this.handleExecutionStart(message);
          break;
        case 'execution_complete':
          this.handleExecutionComplete(message);
          break;
        case 'execution_error':
          this.handleExecutionError(message);
          break;
        case 'heartbeat':
          // 心跳响应，无需处理
          break;
        default:
          console.log('[LogWebSocketManager] 未知消息类型:', message.type);
      }
      
      // 通知通用监听器
      this.emit('message', message);
      
    } catch (error) {
      console.error('[LogWebSocketManager] 消息解析失败:', error);
    }
  }

  /**
   * 处理日志消息
   * @param {Object} message - 日志消息
   */
  handleLogMessage(message) {
    const { scriptId, executionId, level, content, timestamp } = message.data;
    
    // 只处理活跃的日志流
    if (!this.activeLogStreams.has(executionId)) {
      return;
    }
    
    // 触发日志事件
    this.emit('log', {
      scriptId,
      executionId,
      level, // debug, info, warning, error
      content,
      timestamp: new Date(timestamp),
      formattedTime: new Date(timestamp).toLocaleTimeString('zh-CN')
    });
  }

  /**
   * 处理批量日志
   * @param {Object} message - 批量日志消息
   */
  handleLogBatch(message) {
    const { executionId, logs } = message.data;
    
    if (!this.activeLogStreams.has(executionId)) {
      return;
    }
    
    // 批量触发日志事件
    logs.forEach(log => {
      this.emit('log', {
        executionId,
        level: log.level,
        content: log.content,
        timestamp: new Date(log.timestamp),
        formattedTime: new Date(log.timestamp).toLocaleTimeString('zh-CN')
      });
    });
  }

  /**
   * 处理执行开始
   * @param {Object} message - 执行开始消息
   */
  handleExecutionStart(message) {
    const { scriptId, executionId, startTime } = message.data;
    
    this.activeLogStreams.add(executionId);
    
    this.emit('execution_start', {
      scriptId,
      executionId,
      startTime: new Date(startTime)
    });
    
    console.log(`[LogWebSocketManager] 脚本执行开始: ${executionId}`);
  }

  /**
   * 处理执行完成
   * @param {Object} message - 执行完成消息
   */
  handleExecutionComplete(message) {
    const { scriptId, executionId, endTime, exitCode } = message.data;
    
    this.emit('execution_complete', {
      scriptId,
      executionId,
      endTime: new Date(endTime),
      exitCode,
      success: exitCode === 0
    });
    
    // 延迟移除日志流（让用户能看到最后几条日志）
    setTimeout(() => {
      this.activeLogStreams.delete(executionId);
    }, 5000);
    
    console.log(`[LogWebSocketManager] 脚本执行完成: ${executionId}, 退出码: ${exitCode}`);
  }

  /**
   * 处理执行错误
   * @param {Object} message - 执行错误消息
   */
  handleExecutionError(message) {
    const { scriptId, executionId, error } = message.data;
    
    this.emit('execution_error', {
      scriptId,
      executionId,
      error
    });
    
    console.error(`[LogWebSocketManager] 脚本执行错误: ${executionId}`, error);
  }

  /**
   * 连接关闭处理
   */
  handleClose() {
    console.log('[LogWebSocketManager] WebSocket已关闭');
    this.isConnected = false;
    this.stopHeartbeat();
    this.scheduleReconnect();
  }

  /**
   * 错误处理
   * @param {Error} error - 错误对象
   */
  handleError(error) {
    console.error('[LogWebSocketManager] WebSocket错误:', error);
    this.emit('error', error);
  }

  /**
   * 安排重连
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('[LogWebSocketManager] 重连次数超限，停止重连');
      this.emit('reconnect_failed');
      return;
    }
    
    this.reconnectAttempts++;
    
    const delay = Math.min(
      this.options.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1),
      30000
    );
    
    console.log(`[LogWebSocketManager] ${delay/1000}秒后尝试第${this.reconnectAttempts}次重连...`);
    
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
      console.warn('[LogWebSocketManager] WebSocket未连接，无法发送消息');
    }
  }

  /**
   * 订阅脚本日志
   * @param {string} scriptId - 脚本ID
   * @param {string} executionId - 执行ID
   */
  subscribeScriptLogs(scriptId, executionId) {
    this.activeLogStreams.add(executionId);
    
    this.send({
      type: 'subscribe',
      scriptId,
      executionId
    });
    
    console.log(`[LogWebSocketManager] 订阅脚本日志: ${scriptId}, 执行ID: ${executionId}`);
  }

  /**
   * 取消订阅
   * @param {string} executionId - 执行ID
   */
  unsubscribeScriptLogs(executionId) {
    this.activeLogStreams.delete(executionId);
    
    this.send({
      type: 'unsubscribe',
      executionId
    });
  }

  /**
   * 请求历史日志
   * @param {string} executionId - 执行ID
   * @param {Object} options - 选项
   */
  requestHistoryLogs(executionId, options = {}) {
    this.send({
      type: 'request_history',
      executionId,
      limit: options.limit || 100,
      before: options.before || null
    });
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
          console.error('[LogWebSocketManager] 监听器错误:', error);
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
    this.activeLogStreams.clear();
    
    console.log('[LogWebSocketManager] 已断开连接');
  }

  /**
   * 获取连接状态
   * @returns {Object}
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      activeStreams: this.activeLogStreams.size
    };
  }
}
