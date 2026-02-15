/**
 * 确认对话框组件
 * 共享模块 - 所有页面可复用
 * 版本: v1.0.0
 */

/**
 * 确认对话框配置
 */
const DIALOG_CONFIG = {
  backdropClose: true,
  escapeClose: true
};

/**
 * 确认对话框管理器类
 */
export class ConfirmDialogManager {
  constructor() {
    this.container = null;
    this.currentDialog = null;
    this.init();
  }
  
  /**
   * 初始化对话框容器
   */
  init() {
    this.container = document.getElementById('confirm-dialog-container');
    
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'confirm-dialog-container';
      this.container.className = 'confirm-dialog-container';
      document.body.appendChild(this.container);
    }
  }
  
  /**
   * 显示确认对话框
   * @param {Object} options - 配置选项
   * @param {string} options.title - 标题
   * @param {string} options.message - 消息内容
   * @param {string} options.type - 类型: info, success, warning, danger
   * @param {string} options.confirmText - 确认按钮文本
   * @param {string} options.cancelText - 取消按钮文本
   * @param {Function} options.onConfirm - 确认回调
   * @param {Function} options.onCancel - 取消回调
   * @returns {Promise<boolean>}
   */
  show(options) {
    return new Promise((resolve) => {
      const {
        title = '确认',
        message,
        type = 'info',
        confirmText = '确认',
        cancelText = '取消',
        onConfirm,
        onCancel
      } = options;
      
      // 关闭当前对话框
      this.close();
      
      // 创建对话框元素
      const dialog = document.createElement('div');
      dialog.className = `confirm-dialog confirm-dialog-${type}`;
      dialog.innerHTML = `
        <div class="confirm-dialog-backdrop"></div>
        <div class="confirm-dialog-content">
          <div class="confirm-dialog-header">
            <span class="confirm-dialog-icon">${this.getIcon(type)}</span>
            <h3 class="confirm-dialog-title">${this.escapeHtml(title)}</h3>
          </div>
          <div class="confirm-dialog-body">
            <p class="confirm-dialog-message">${this.escapeHtml(message)}</p>
          </div>
          <div class="confirm-dialog-footer">
            <button class="btn btn-secondary confirm-dialog-cancel">${this.escapeHtml(cancelText)}</button>
            <button class="btn btn-primary confirm-dialog-confirm ${type === 'danger' ? 'btn-danger' : ''}">${this.escapeHtml(confirmText)}</button>
          </div>
        </div>
      `;
      
      this.container.appendChild(dialog);
      this.currentDialog = dialog;
      
      // 绑定事件
      const backdrop = dialog.querySelector('.confirm-dialog-backdrop');
      const confirmBtn = dialog.querySelector('.confirm-dialog-confirm');
      const cancelBtn = dialog.querySelector('.confirm-dialog-cancel');
      
      const handleConfirm = () => {
        this.close();
        if (onConfirm) onConfirm();
        resolve(true);
      };
      
      const handleCancel = () => {
        this.close();
        if (onCancel) onCancel();
        resolve(false);
      };
      
      confirmBtn.addEventListener('click', handleConfirm);
      cancelBtn.addEventListener('click', handleCancel);
      
      if (DIALOG_CONFIG.backdropClose) {
        backdrop.addEventListener('click', handleCancel);
      }
      
      if (DIALOG_CONFIG.escapeClose) {
        const handleEscape = (e) => {
          if (e.key === 'Escape') {
            document.removeEventListener('keydown', handleEscape);
            handleCancel();
          }
        };
        document.addEventListener('keydown', handleEscape);
      }
      
      // 动画进入
      requestAnimationFrame(() => {
        dialog.classList.add('show');
      });
    });
  }
  
  /**
   * 关闭对话框
   */
  close() {
    if (!this.currentDialog) return;
    
    const dialog = this.currentDialog;
    dialog.classList.remove('show');
    dialog.classList.add('hide');
    
    setTimeout(() => {
      if (this.container.contains(dialog)) {
        this.container.removeChild(dialog);
      }
    }, 300);
    
    this.currentDialog = null;
  }
  
  /**
   * 获取图标
   * @param {string} type - 类型
   * @returns {string}
   */
  getIcon(type) {
    const icons = {
      info: 'ℹ',
      success: '✓',
      warning: '⚠',
      danger: '⚠'
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
}

// 创建单例实例
let dialogManager = null;

/**
 * 获取对话框管理器实例
 * @returns {ConfirmDialogManager}
 */
export function getConfirmDialogManager() {
  if (!dialogManager) {
    dialogManager = new ConfirmDialogManager();
  }
  return dialogManager;
}

/**
 * 显示确认对话框（便捷函数）
 * @param {Object} options - 配置选项
 * @returns {Promise<boolean>}
 */
export function showConfirm(options) {
  return getConfirmDialogManager().show(options);
}

// 默认导出
export default ConfirmDialogManager;
