/**
 * DAG WebSocket管理器
 * 处理DAG执行状态的实时推送
 * 版本: v1.0.0
 */

export class DAGWebSocketManager {
  constructor(page) {
    this.page = page;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
    this.heartbeatInterval = null;
  }

  /**
   * 初始化WebSocket连接
   * @param {string} executionId - 执行ID
   * @returns {Promise<boolean>}
   */
  async connect(executionId) {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.log('[DAGWebSocketManager] 已存在连接');
        resolve(true);
        return;
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/dag/executions/${executionId}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('[DAGWebSocketManager] WebSocket连接已建立');
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.emit('connected', { executionId });
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onclose = (event) => {
          console.log('[DAGWebSocketManager] WebSocket连接已关闭', event.code);
          this.stopHeartbeat();
          this.emit('disconnected', { code: event.code });

          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(executionId);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[DAGWebSocketManager] WebSocket错误:', error);
          this.emit('error', { error });
          reject(error);
        };

      } catch (error) {
        console.error('[DAGWebSocketManager] 创建WebSocket失败:', error);
        reject(error);
      }
    });
  }

  /**
   * 处理收到的消息
   * @param {string} data - 消息数据
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data);
      console.log('[DAGWebSocketManager] 收到消息:', message.type);

      // 触发对应类型的事件监听
      this.emit(message.type, message);

      // 触发通用消息事件
      this.emit('message', message);

    } catch (error) {
      console.error('[DAGWebSocketManager] 消息解析失败:', error);
      this.emit('parse_error', { data, error });
    }
  }

  /**
   * 发送消息
   * @param {Object} message - 消息对象
   * @returns {boolean}
   */
  send(message) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[DAGWebSocketManager] WebSocket未连接');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('[DAGWebSocketManager] 发送消息失败:', error);
      return false;
    }
  }

  /**
   * 订阅事件
   * @param {string} event - 事件类型
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消订阅函数
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    
    this.listeners.get(event).add(callback);

    // 返回取消订阅函数
    return () => {
      this.off(event, callback);
    };
  }

  /**
   * 取消订阅
   * @param {string} event - 事件类型
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件类型
   * @param {*} data - 事件数据
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[DAGWebSocketManager] 事件处理错误 [${event}]:`, error);
        }
      });
    }
  }

  /**
   * 启动心跳
   */
  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping', timestamp: Date.now() });
    }, 30000); // 30秒心跳
  }

  /**
   * 停止心跳
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 计划重连
   * @param {string} executionId - 执行ID
   */
  scheduleReconnect(executionId) {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(`[DAGWebSocketManager] ${delay}ms后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(executionId).catch(error => {
        console.error('[DAGWebSocketManager] 重连失败:', error);
      });
    }, delay);
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.stopHeartbeat();
    
    if (this.ws) {
      // 正常关闭，不触发重连
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    // 清空所有监听器
    this.listeners.clear();
    
    console.log('[DAGWebSocketManager] 已断开连接');
  }

  /**
   * 获取连接状态
   * @returns {string}
   */
  getState() {
    if (!this.ws) return 'CLOSED';
    
    const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
    return states[this.ws.readyState] || 'UNKNOWN';
  }

  /**
   * 是否已连接
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 请求执行状态
   * @param {string} executionId - 执行ID
   */
  requestStatus(executionId) {
    this.send({
      type: 'request_status',
      execution_id: executionId
    });
  }

  /**
   * 订阅执行更新
   * @param {string} executionId - 执行ID
   */
  subscribeExecution(executionId) {
    this.send({
      type: 'subscribe',
      execution_id: executionId
    });
  }

  /**
   * 取消订阅执行
   * @param {string} executionId - 执行ID
   */
  unsubscribeExecution(executionId) {
    this.send({
      type: 'unsubscribe',
      execution_id: executionId
    });
  }
}
