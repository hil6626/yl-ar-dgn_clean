/**
 * 全局状态管理器
 * 实现页面间的状态共享和同步
 * 版本: v1.0.0
 */

export class GlobalStateManager {
  constructor() {
    this.state = {
      // 用户状态
      user: null,
      isAuthenticated: false,
      
      // 系统状态
      systemStatus: 'online',
      lastUpdate: null,
      
      // 通知状态
      notifications: {
        sound: true,
        desktop: false,
        count: 0
      },
      
      // 告警状态
      alerts: {
        unread: 0,
        critical: 0,
        warning: 0
      },
      
      // 任务状态
      tasks: {
        running: 0,
        queued: 0,
        completed: 0
      },
      
      // 连接状态
      connection: {
        websocket: 'disconnected',
        lastPing: null
      }
    };
    
    this.listeners = new Map();
    this.storageKey = 'yl_monitor_global_state';
    
    // 从localStorage恢复状态
    this.loadFromStorage();
  }

  /**
   * 初始化
   */
  init() {
    // 监听存储变化（多标签页同步）
    window.addEventListener('storage', (e) => {
      if (e.key === this.storageKey) {
        this.handleStorageChange(e.newValue);
      }
    });
    
    // 定期保存状态
    setInterval(() => this.saveToStorage(), 5000);
    
    console.log('[GlobalStateManager] 全局状态管理器已初始化');
  }

  /**
   * 获取状态
   */
  getState(key = null) {
    if (key) {
      return this.getNestedValue(this.state, key);
    }
    return { ...this.state };
  }

  /**
   * 设置状态
   */
  setState(key, value, options = {}) {
    const { silent = false, persist = true } = options;
    
    const oldValue = this.getNestedValue(this.state, key);
    this.setNestedValue(this.state, key, value);
    
    if (!silent) {
      this.emit('state:changed', { key, value, oldValue });
      this.emit(`state:${key}`, value);
    }
    
    if (persist) {
      this.saveToStorage();
    }
  }

  /**
   * 更新状态（合并）
   */
  updateState(updates, options = {}) {
    Object.entries(updates).forEach(([key, value]) => {
      this.setState(key, value, options);
    });
  }

  /**
   * 获取嵌套值
   */
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : undefined;
    }, obj);
  }

  /**
   * 设置嵌套值
   */
  setNestedValue(obj, path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    
    const target = keys.reduce((current, key) => {
      if (!current[key]) current[key] = {};
      return current[key];
    }, obj);
    
    target[lastKey] = value;
  }

  /**
   * 保存到localStorage
   */
  saveToStorage() {
    try {
      const data = {
        state: this.state,
        timestamp: Date.now()
      };
      localStorage.setItem(this.storageKey, JSON.stringify(data));
    } catch (error) {
      console.warn('[GlobalStateManager] 保存状态失败:', error);
    }
  }

  /**
   * 从localStorage加载
   */
  loadFromStorage() {
    try {
      const data = localStorage.getItem(this.storageKey);
      if (data) {
        const parsed = JSON.parse(data);
        if (parsed.state) {
          this.state = { ...this.state, ...parsed.state };
          console.log('[GlobalStateManager] 状态已从存储恢复');
        }
      }
    } catch (error) {
      console.warn('[GlobalStateManager] 加载状态失败:', error);
    }
  }

  /**
   * 处理存储变化
   */
  handleStorageChange(newValue) {
    try {
      const data = JSON.parse(newValue);
      if (data.state) {
        // 合并新状态
        Object.entries(data.state).forEach(([key, value]) => {
          if (JSON.stringify(this.state[key]) !== JSON.stringify(value)) {
            this.state[key] = value;
            this.emit('state:sync', { key, value });
          }
        });
      }
    } catch (error) {
      console.warn('[GlobalStateManager] 处理存储变化失败:', error);
    }
  }

  /**
   * 更新告警计数
   */
  updateAlertCounts(counts) {
    this.setState('alerts', {
      ...this.state.alerts,
      ...counts
    });
    
    // 更新页面徽标
    this.updateFaviconBadge();
  }

  /**
   * 更新任务计数
   */
  updateTaskCounts(counts) {
    this.setState('tasks', {
      ...this.state.tasks,
      ...counts
    });
  }

  /**
   * 更新连接状态
   */
  updateConnectionStatus(status) {
    this.setState('connection', {
      ...this.state.connection,
      ...status,
      lastPing: Date.now()
    });
  }

  /**
   * 更新通知设置
   */
  updateNotificationSettings(settings) {
    this.setState('notifications', {
      ...this.state.notifications,
      ...settings
    });
  }

  /**
   * 更新页面徽标
   */
  updateFaviconBadge() {
    const total = this.state.alerts.unread;
    
    // 更新标题显示未读数
    if (total > 0) {
      const baseTitle = document.title.replace(/^\(\d+\)\s*/, '');
      document.title = `(${total}) ${baseTitle}`;
    }
    
    // 可以在这里添加favicon徽标更新逻辑
  }

  /**
   * 同步所有页面状态
   */
  syncAllPages() {
    // 触发全局同步事件
    this.emit('state:fullSync', this.state);
    
    // 广播到所有打开的窗口
    this.broadcastMessage({
      type: 'state:sync',
      data: this.state
    });
  }

  /**
   * 广播消息
   */
  broadcastMessage(message) {
    // 使用BroadcastChannel（如果支持）
    if (window.BroadcastChannel) {
      const channel = new BroadcastChannel('yl_monitor_state');
      channel.postMessage(message);
      channel.close();
    }
  }

  /**
   * 重置状态
   */
  resetState() {
    this.state = {
      user: null,
      isAuthenticated: false,
      systemStatus: 'online',
      lastUpdate: null,
      notifications: { sound: true, desktop: false, count: 0 },
      alerts: { unread: 0, critical: 0, warning: 0 },
      tasks: { running: 0, queued: 0, completed: 0 },
      connection: { websocket: 'disconnected', lastPing: null }
    };
    
    this.saveToStorage();
    this.emit('state:reset');
  }

  /**
   * 事件监听
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  /**
   * 移除监听
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[GlobalStateManager] 事件处理错误:`, error);
        }
      });
    }
    
    // 触发自定义事件
    document.dispatchEvent(new CustomEvent(event, { detail: data }));
  }

  /**
   * 销毁
   */
  destroy() {
    this.listeners.clear();
  }
}

// 创建全局实例
const globalStateManager = new GlobalStateManager();

// 导出
export { globalStateManager };
export default GlobalStateManager;
