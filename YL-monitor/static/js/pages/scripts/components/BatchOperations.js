/**
 * Scripts批量操作组件
 * 实现批量启用、禁用、运行、停止功能
 * 版本: v1.0.0
 */

export class BatchOperations {
  constructor(options = {}) {
    this.options = {
      onBatchEnable: () => {},
      onBatchDisable: () => {},
      onBatchRun: () => {},
      onBatchStop: () => {},
      onBatchDelete: () => {},
      ...options
    };
    
    this.selectedScripts = new Set();
    this.isBatchMode = false;
    this.container = null;
  }

  /**
   * 初始化组件
   * @param {HTMLElement} container - 容器元素
   */
  init(container) {
    this.container = container;
    this.render();
    this.bindEvents();
  }

  /**
   * 渲染批量操作工具栏
   */
  render() {
    this.container.innerHTML = `
      <div class="batch-operations-toolbar" id="batch-operations-toolbar" style="display: none;">
        <div class="batch-info">
          <span class="batch-count">已选择 <strong id="selected-count">0</strong> 个脚本</span>
          <button class="btn btn-sm btn-ghost" data-action="select-all">
            全选
          </button>
          <button class="btn btn-sm btn-ghost" data-action="clear-selection">
            清除
          </button>
        </div>
        
        <div class="batch-actions">
          <button class="btn btn-sm btn-success" data-action="batch-enable" title="批量启用">
            <span>▶️</span>
            <span>启用</span>
          </button>
          
          <button class="btn btn-sm btn-warning" data-action="batch-disable" title="批量禁用">
            <span>⏸️</span>
            <span>禁用</span>
          </button>
          
          <button class="btn btn-sm btn-primary" data-action="batch-run" title="批量运行">
            <span>▶️</span>
            <span>运行</span>
          </button>
          
          <button class="btn btn-sm btn-danger" data-action="batch-stop" title="批量停止">
            <span>⏹️</span>
            <span>停止</span>
          </button>
          
          <div class="divider"></div>
          
          <button class="btn btn-sm btn-error" data-action="batch-delete" title="批量删除">
            <span>🗑️</span>
            <span>删除</span>
          </button>
          
          <button class="btn btn-sm btn-ghost" data-action="exit-batch-mode">
            <span>✕</span>
            <span>退出</span>
          </button>
        </div>
      </div>
      
      <div class="batch-mode-toggle">
        <button class="btn btn-secondary" id="btn-batch-mode" data-action="enter-batch-mode">
          <span>☐</span>
          <span>批量操作</span>
        </button>
      </div>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 进入批量模式
    this.container.querySelector('[data-action="enter-batch-mode"]')?.addEventListener('click', () => {
      this.enterBatchMode();
    });

    // 退出批量模式
    this.container.querySelector('[data-action="exit-batch-mode"]')?.addEventListener('click', () => {
      this.exitBatchMode();
    });

    // 全选
    this.container.querySelector('[data-action="select-all"]')?.addEventListener('click', () => {
      this.selectAll();
    });

    // 清除选择
    this.container.querySelector('[data-action="clear-selection"]')?.addEventListener('click', () => {
      this.clearSelection();
    });

    // 批量启用
    this.container.querySelector('[data-action="batch-enable"]')?.addEventListener('click', () => {
      this.batchEnable();
    });

    // 批量禁用
    this.container.querySelector('[data-action="batch-disable"]')?.addEventListener('click', () => {
      this.batchDisable();
    });

    // 批量运行
    this.container.querySelector('[data-action="batch-run"]')?.addEventListener('click', () => {
      this.batchRun();
    });

    // 批量停止
    this.container.querySelector('[data-action="batch-stop"]')?.addEventListener('click', () => {
      this.batchStop();
    });

    // 批量删除
    this.container.querySelector('[data-action="batch-delete"]')?.addEventListener('click', () => {
      this.batchDelete();
    });
  }

  /**
   * 进入批量模式
   */
  enterBatchMode() {
    this.isBatchMode = true;
    this.selectedScripts.clear();
    
    const toolbar = this.container.querySelector('#batch-operations-toolbar');
    const toggle = this.container.querySelector('.batch-mode-toggle');
    
    if (toolbar) toolbar.style.display = 'flex';
    if (toggle) toggle.style.display = 'none';
    
    // 触发事件通知父组件显示复选框
    this.emit('batch-mode-change', { isBatchMode: true });
    
    console.log('[BatchOperations] 进入批量模式');
  }

  /**
   * 退出批量模式
   */
  exitBatchMode() {
    this.isBatchMode = false;
    this.selectedScripts.clear();
    this.updateSelectedCount();
    
    const toolbar = this.container.querySelector('#batch-operations-toolbar');
    const toggle = this.container.querySelector('.batch-mode-toggle');
    
    if (toolbar) toolbar.style.display = 'none';
    if (toggle) toggle.style.display = 'block';
    
    // 触发事件通知父组件隐藏复选框
    this.emit('batch-mode-change', { isBatchMode: false });
    
    console.log('[BatchOperations] 退出批量模式');
  }

  /**
   * 切换脚本选择
   * @param {string} scriptId - 脚本ID
   * @param {boolean} selected - 是否选中
   */
  toggleScript(scriptId, selected) {
    if (selected) {
      this.selectedScripts.add(scriptId);
    } else {
      this.selectedScripts.delete(scriptId);
    }
    
    this.updateSelectedCount();
  }

  /**
   * 全选
   */
  selectAll() {
    this.emit('select-all');
  }

  /**
   * 清除选择
   */
  clearSelection() {
    this.selectedScripts.clear();
    this.updateSelectedCount();
    this.emit('clear-selection');
  }

  /**
   * 更新选中计数
   */
  updateSelectedCount() {
    const countEl = this.container.querySelector('#selected-count');
    if (countEl) {
      countEl.textContent = this.selectedScripts.size;
    }
  }

  /**
   * 设置选中的脚本（从父组件调用）
   * @param {Array} scriptIds - 脚本ID数组
   */
  setSelectedScripts(scriptIds) {
    this.selectedScripts = new Set(scriptIds);
    this.updateSelectedCount();
  }

  /**
   * 批量启用
   */
  async batchEnable() {
    if (this.selectedScripts.size === 0) {
      this.showToast('warning', '请先选择要启用的脚本');
      return;
    }

    const confirmed = await this.showConfirm({
      title: '批量启用脚本',
      message: `确定要启用选中的 ${this.selectedScripts.size} 个脚本吗？`,
      type: 'info'
    });

    if (confirmed) {
      this.options.onBatchEnable(Array.from(this.selectedScripts));
    }
  }

  /**
   * 批量禁用
   */
  async batchDisable() {
    if (this.selectedScripts.size === 0) {
      this.showToast('warning', '请先选择要禁用的脚本');
      return;
    }

    const confirmed = await this.showConfirm({
      title: '批量禁用脚本',
      message: `确定要禁用选中的 ${this.selectedScripts.size} 个脚本吗？`,
      type: 'warning'
    });

    if (confirmed) {
      this.options.onBatchDisable(Array.from(this.selectedScripts));
    }
  }

  /**
   * 批量运行
   */
  async batchRun() {
    if (this.selectedScripts.size === 0) {
      this.showToast('warning', '请先选择要运行的脚本');
      return;
    }

    const confirmed = await this.showConfirm({
      title: '批量运行脚本',
      message: `确定要运行选中的 ${this.selectedScripts.size} 个脚本吗？`,
      type: 'info'
    });

    if (confirmed) {
      this.options.onBatchRun(Array.from(this.selectedScripts));
    }
  }

  /**
   * 批量停止
   */
  async batchStop() {
    if (this.selectedScripts.size === 0) {
      this.showToast('warning', '请先选择要停止的脚本');
      return;
    }

    const confirmed = await this.showConfirm({
      title: '批量停止脚本',
      message: `确定要停止选中的 ${this.selectedScripts.size} 个脚本吗？`,
      type: 'warning'
    });

    if (confirmed) {
      this.options.onBatchStop(Array.from(this.selectedScripts));
    }
  }

  /**
   * 批量删除
   */
  async batchDelete() {
    if (this.selectedScripts.size === 0) {
      this.showToast('warning', '请先选择要删除的脚本');
      return;
    }

    const confirmed = await this.showConfirm({
      title: '批量删除脚本',
      message: `确定要删除选中的 ${this.selectedScripts.size} 个脚本吗？此操作不可恢复！`,
      type: 'error',
      confirmText: '确认删除',
      cancelText: '取消'
    });

    if (confirmed) {
      this.options.onBatchDelete(Array.from(this.selectedScripts));
    }
  }

  /**
   * 显示确认弹窗
   * @param {Object} options - 弹窗选项
   * @returns {Promise<boolean>}
   */
  showConfirm(options) {
    return new Promise((resolve) => {
      if (window.YLMonitor?.uiComponents?.showConfirm) {
        window.YLMonitor.uiComponents.showConfirm({
          ...options,
          onConfirm: () => resolve(true),
          onCancel: () => resolve(false)
        });
      } else {
        // 降级到原生confirm
        const result = confirm(options.message);
        resolve(result);
      }
    });
  }

  /**
   * 显示Toast通知
   * @param {string} type - 类型
   * @param {string} message - 消息
   */
  showToast(type, message) {
    if (window.YLMonitor?.uiComponents?.showToast) {
      window.YLMonitor.uiComponents.showToast({ type, message });
    } else {
      console.log(`[${type}] ${message}`);
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件名
   * @param {*} data - 数据
   */
  emit(event, data) {
    const eventName = `batchoperations:${event}`;
    window.dispatchEvent(new CustomEvent(eventName, { detail: data }));
  }

  /**
   * 监听事件
   * @param {string} event - 事件名
   * @param {Function} callback - 回调
   */
  on(event, callback) {
    const eventName = `batchoperations:${event}`;
    window.addEventListener(eventName, (e) => callback(e.detail));
  }

  /**
   * 销毁
   */
  destroy() {
    this.selectedScripts.clear();
    this.container.innerHTML = '';
  }
}
