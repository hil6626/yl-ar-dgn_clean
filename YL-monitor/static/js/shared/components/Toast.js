/**
 * Toast通知组件
 * 共享模块 - 所有页面可复用
 * 版本: v1.0.0
 */

/**
 * Toast配置
 */
const TOAST_CONFIG = {
  duration: 3000,
  maxCount: 5,
  position: 'top-right'
};

/**
 * Toast管理器类
 */
export class ToastManager {
  constructor() {
    this.container = null;
    this.toasts = [];
    this.init();
  }
  
  /**
   * 初始化Toast容器
   */
  init() {
    // 检查是否已存在容器
    this.container = document.getElementById('toast-container');
    
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = `toast-container ${TOAST_CONFIG.position}`;
      document.body.appendChild(this.container);
    }
  }
  
  /**
   * 显示Toast
   * @param {Object} options - 配置选项
   * @param {string} options.type - 类型: success, error, warning, info
   * @param {string} options.message - 消息内容
   * @param {number} options.duration - 显示时长（毫秒）
   * @returns {HTMLElement}
   */
  show(options) {
    const { type = 'info', message, duration = TOAST_CONFIG.duration } = options;
    
    // 限制最大数量
    if (this.toasts.length >= TOAST_CONFIG.maxCount) {
      this.remove(this.toasts[0]);
    }
    
    // 创建Toast元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${this.getIcon(type)}</span>
      <span class="toast-message">${this.escapeHtml(message)}</span>
      <button class="toast-close" aria-label="关闭">×</button>
    `;
    
    // 添加到容器
    this.container.appendChild(toast);
    this.toasts.push(toast);
    
    // 绑定关闭事件
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.remove(toast));
    
    // 自动移除
    const timer = setTimeout(() => this.remove(toast), duration);
    toast.dataset.timer = timer;
    
    // 动画进入
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });
    
    return toast;
  }
  
  /**
   * 移除Toast
   * @param {HTMLElement} toast - Toast元素
   */
  remove(toast) {
    if (!toast || !this.container.contains(toast)) return;
    
    // 清除定时器
    const timer = toast.dataset.timer;
    if (timer) {
      clearTimeout(parseInt(timer));
    }
    
    // 动画退出
    toast.classList.remove('show');
    toast.classList.add('hide');
    
    // 从数组移除
    const index = this.toasts.indexOf(toast);
    if (index > -1) {
      this.toasts.splice(index, 1);
    }
    
    // 从DOM移除
    setTimeout(() => {
      if (this.container.contains(toast)) {
        this.container.removeChild(toast);
      }
    }, 300);
  }
  
  /**
   * 获取图标
   * @param {string} type - 类型
   * @returns {string}
   */
  getIcon(type) {
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    return icons[type] || icons.info;
  }
  
  /**
   * 转义HTML
   * @param {string} text - 文本
   * @returns {string}
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  /**
   * 显示成功Toast
   * @param {string} message - 消息
   * @param {number} duration - 时长
   */
  success(message, duration) {
    return this.show({ type: 'success', message, duration });
  }
  
  /**
   * 显示错误Toast
   * @param {string} message - 消息
   * @param {number} duration - 时长
   */
  error(message, duration) {
    return this.show({ type: 'error', message, duration });
  }
  
  /**
   * 显示警告Toast
   * @param {string} message - 消息
   * @param {number} duration - 时长
   */
  warning(message, duration) {
    return this.show({ type: 'warning', message, duration });
  }
  
  /**
   * 显示信息Toast
   * @param {string} message - 消息
   * @param {number} duration - 时长
   */
  info(message, duration) {
    return this.show({ type: 'info', message, duration });
  }
  
  /**
   * 清除所有Toast
   */
  clear() {
    [...this.toasts].forEach(toast => this.remove(toast));
  }
}

// 创建单例实例
let toastManager = null;

/**
 * 获取Toast管理器实例
 * @returns {ToastManager}
 */
export function getToastManager() {
  if (!toastManager) {
    toastManager = new ToastManager();
  }
  return toastManager;
}

/**
 * 显示Toast（便捷函数）
 * @param {Object} options - 配置选项
 */
export function showToast(options) {
  return getToastManager().show(options);
}

/**
 * 显示成功Toast（便捷函数）
 * @param {string} message - 消息
 */
export function showSuccess(message) {
  return getToastManager().success(message);
}

/**
 * 显示错误Toast（便捷函数）
 * @param {string} message - 消息
 */
export function showError(message) {
  return getToastManager().error(message);
}

/**
 * 显示警告Toast（便捷函数）
 * @param {string} message - 消息
 */
export function showWarning(message) {
  return getToastManager().warning(message);
}

/**
 * 显示信息Toast（便捷函数）
 * @param {string} message - 消息
 */
export function showInfo(message) {
  return getToastManager().info(message);
}

// 默认导出
export default ToastManager;
