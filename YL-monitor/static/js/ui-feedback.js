/**
 * UI反馈系统 - 替代被删除的ui-components.js
 * 提供Toast提示和确认对话框功能
 * 版本: v1.0.0
 */

class UIFeedback {
  constructor() {
    this.toastContainer = null;
    this.modalContainer = null;
    this.eventListeners = new Map();
    this.init();
  }

  init() {
    // 确保容器存在
    this.ensureContainers();
  }

  /**
   * 注册事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event).add(callback);
  }

  /**
   * 移除事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).delete(callback);
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件名称
   * @param {*} data - 事件数据
   */
  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[UIFeedback] 事件处理错误 (${event}):`, error);
        }
      });
    }
  }

  ensureContainers() {
    // Toast容器
    this.toastContainer = document.getElementById('toast-mount');
    if (!this.toastContainer) {
      this.toastContainer = document.createElement('div');
      this.toastContainer.id = 'toast-mount';
      this.toastContainer.className = 'toast-container';
      document.body.appendChild(this.toastContainer);
    }

    // Modal容器
    this.modalContainer = document.getElementById('modal-mount');
    if (!this.modalContainer) {
      this.modalContainer = document.createElement('div');
      this.modalContainer.id = 'modal-mount';
      this.modalContainer.className = 'modal-container';
      document.body.appendChild(this.modalContainer);
    }
  }

  /**
   * 显示Toast提示
   * @param {Object} options - 配置选项
   * @param {string} options.type - 类型: success, error, warning, info
   * @param {string} options.message - 消息内容
   * @param {number} options.duration - 显示时长(毫秒)
   */
  showToast({ type = 'info', message = '', duration = 3000 }) {
    this.ensureContainers();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    this.toastContainer.appendChild(toast);

    // 动画进入
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // 自动关闭
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  /**
   * 显示确认对话框
   * @param {Object} options - 配置选项
   * @param {string} options.title - 标题
   * @param {string} options.message - 消息内容(支持HTML)
   * @param {string} options.type - 类型: danger, warning, info
   * @param {string} options.confirmText - 确认按钮文本
   * @param {string} options.cancelText - 取消按钮文本
   * @param {Function} options.onConfirm - 确认回调
   * @param {Function} options.onCancel - 取消回调
   */
  showConfirm({ 
    title = '确认', 
    message = '', 
    type = 'info',
    confirmText = '确认',
    cancelText = '取消',
    onConfirm = () => {},
    onCancel = () => {}
  }) {
    this.ensureContainers();

    const typeColors = {
      danger: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    };

    const modal = document.createElement('div');
    modal.className = 'modal-overlay show';
    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title">${title}</h3>
          <button class="modal-close" data-action="cancel">×</button>
        </div>
        <div class="modal-body">
          ${message}
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-action="cancel">${cancelText}</button>
          <button class="btn btn-primary" data-action="confirm" style="background: ${typeColors[type] || typeColors.info}">
            ${confirmText}
          </button>
        </div>
      </div>
    `;

    this.modalContainer.appendChild(modal);

    // 绑定事件
    const handleAction = (action) => {
      modal.classList.remove('show');
      setTimeout(() => modal.remove(), 300);
      
      if (action === 'confirm') {
        onConfirm();
      } else {
        onCancel();
      }
    };

    modal.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        handleAction(btn.dataset.action);
      });
    });

    // 点击背景关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        handleAction('cancel');
      }
    });

    // ESC键关闭
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        handleAction('cancel');
        document.removeEventListener('keydown', handleEsc);
      }
    };
    document.addEventListener('keydown', handleEsc);
  }

  /**
   * 显示加载中
   * @param {string} message - 提示消息
   * @returns {Function} 关闭函数
   */
  showLoading(message = '加载中...') {
    this.ensureContainers();

    const loading = document.createElement('div');
    loading.className = 'loading-overlay show';
    loading.innerHTML = `
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <span class="loading-text">${message}</span>
      </div>
    `;

    this.modalContainer.appendChild(loading);

    return () => {
      loading.classList.remove('show');
      setTimeout(() => loading.remove(), 300);
    };
  }
}

// 创建全局实例
const uiFeedback = new UIFeedback();

// 导出
export { UIFeedback, uiFeedback };
export default uiFeedback;
