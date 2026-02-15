/**
 * 控制栏组件
 * 拆分自: page-dag.js renderControlBar()
 * 版本: v1.0.0
 */

export class ControlBar {
  /**
   * @param {DAGPage} page - DAG页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('dag-control-bar');
    this.buttons = new Map();
  }

  /**
   * 渲染控制栏
   */
  render() {
    if (!this.mount) {
      console.warn('[ControlBar] 挂载点不存在: #dag-control-bar');
      return;
    }

    this.mount.innerHTML = this.generateHTML();
    this.bindEvents();
    this.updateButtonStates();
    
    console.log('[ControlBar] 控制栏渲染完成');
  }

  /**
   * 生成HTML
   * @returns {string}
   */
  generateHTML() {
    return `
      <div class="dag-control-group">
        <div class="dag-control-title">
          <span>🔄</span>
          <span>DAG流水线</span>
        </div>
      </div>
      <div class="dag-control-group">
        ${this.renderButton('btn-save', '💾', '保存', false)}
        ${this.renderButton('btn-undo', '↩️', '撤销', true)}
        ${this.renderButton('btn-redo', '↪️', '重做', true)}
        ${this.renderButton('btn-export', '📥', '导出', false)}
        ${this.renderButton('btn-edge-edit', '🔗', '连线', false, this.page.edgeEditMode ? 'active' : '')}
        <div class="control-divider"></div>
        ${this.renderButton('btn-run', '▶️', '运行', false, 'primary')}
        ${this.renderButton('btn-stop', '⏹️', '停止', true, 'danger')}
      </div>
    `;
  }

  /**
   * 渲染单个按钮
   * @param {string} id - 按钮ID
   * @param {string} icon - 图标
   * @param {string} text - 文本
   * @param {boolean} disabled - 是否禁用
   * @param {string} extraClass - 额外类名
   * @returns {string}
   */
  renderButton(id, icon, text, disabled, extraClass = '') {
    return `
      <button class="dag-control-btn ${extraClass}" id="${id}" ${disabled ? 'disabled' : ''} title="${text}">
        <span>${icon}</span> ${text}
      </button>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 文件操作
    this.bindButton('btn-save', () => this.page.saveDAG());
    this.bindButton('btn-export', () => this.page.exportDAG());

    // 编辑操作
    this.bindButton('btn-undo', () => this.page.undo());
    this.bindButton('btn-redo', () => this.page.redo());

    // 模式切换
    this.bindButton('btn-edge-edit', () => this.page.toggleEdgeEditMode());

    // 执行控制
    this.bindButton('btn-run', () => this.page.executionManager.run());
    this.bindButton('btn-stop', () => this.page.executionManager.stop());
  }

  /**
   * 绑定单个按钮事件
   * @param {string} id - 按钮ID
   * @param {Function} handler - 事件处理函数
   */
  bindButton(id, handler) {
    const btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener('click', handler);
      this.buttons.set(id, { element: btn, handler });
    }
  }

  /**
   * 更新按钮状态
   */
  updateButtonStates() {
    // 更新撤销/重做按钮状态
    const undoBtn = document.getElementById('btn-undo');
    const redoBtn = document.getElementById('btn-redo');
    
    if (undoBtn) {
      undoBtn.disabled = !this.page.commandManager.canUndo();
    }
    if (redoBtn) {
      redoBtn.disabled = !this.page.commandManager.canRedo();
    }

    // 更新执行按钮状态
    const runBtn = document.getElementById('btn-run');
    const stopBtn = document.getElementById('btn-stop');
    
    if (runBtn && stopBtn) {
      const isRunning = this.page.executionManager.isRunning();
      runBtn.disabled = isRunning;
      stopBtn.disabled = !isRunning;
    }

    // 更新连线编辑按钮状态
    const edgeEditBtn = document.getElementById('btn-edge-edit');
    if (edgeEditBtn) {
      edgeEditBtn.classList.toggle('active', this.page.edgeEditMode);
    }
  }

  /**
   * 设置按钮禁用状态
   * @param {string} id - 按钮ID
   * @param {boolean} disabled - 是否禁用
   */
  setButtonDisabled(id, disabled) {
    const btn = document.getElementById(id);
    if (btn) {
      btn.disabled = disabled;
    }
  }

  /**
   * 设置按钮激活状态
   * @param {string} id - 按钮ID
   * @param {boolean} active - 是否激活
   */
  setButtonActive(id, active) {
    const btn = document.getElementById(id);
    if (btn) {
      btn.classList.toggle('active', active);
    }
  }

  /**
   * 获取按钮元素
   * @param {string} id - 按钮ID
   * @returns {HTMLElement|null}
   */
  getButton(id) {
    return document.getElementById(id);
  }
}
