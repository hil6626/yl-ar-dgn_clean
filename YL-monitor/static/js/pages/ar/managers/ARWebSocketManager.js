/**
 * AR WebSocket管理器
 * 拆分自: page-ar.js
 * 版本: v1.0.0
 */

export class ARWebSocketManager {
  constructor(page) {
    this.page = page;
    this.ws = null;
    this.reconnectInterval = 3000; // 3秒重连
    this.isConnected = false;
  }

  /**
   * 连接WebSocket
   */
  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/ar`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[ARWebSocketManager] WebSocket已连接');
      this.isConnected = true;
      this.page.ui.showToast({
        type: 'success',
        message: 'AR监控已连接'
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('[ARWebSocketManager] WebSocket消息解析失败:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('[ARWebSocketManager] WebSocket已断开，3秒后重连...');
      this.isConnected = false;
      setTimeout(() => this.connect(), this.reconnectInterval);
    };

    this.ws.onerror = (error) => {
      console.error('[ARWebSocketManager] WebSocket错误:', error);
      this.isConnected = false;
    };
  }

  /**
   * 处理WebSocket消息
   * @param {Object} data - 消息数据
   */
  handleMessage(data) {
    if (data.type === 'ar_status') {
      if (data.nodes) {
        this.page.arNodes = data.nodes;
        this.page.sidebar.renderNodes(this.page.arNodes);
        this.page.mainContent.updateStats(this.page.arNodes);
      }
      if (data.resources) {
        this.page.sidebar.updateResources(data.resources);
      }
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  /**
   * 发送消息
   * @param {Object} data - 要发送的数据
   */
  send(data) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
