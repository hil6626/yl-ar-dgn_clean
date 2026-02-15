/**
 * 键盘快捷键管理器
 * 统一管理应用内所有键盘快捷键
 * 版本: v1.0.0
 */

export class KeyboardShortcutManager {
  constructor() {
    this.shortcuts = new Map();
    this.enabled = true;
    this.context = 'global';
    this.contextShortcuts = new Map();
    this.pressedKeys = new Set();
    this.helpModal = null;
  }

  /**
   * 初始化快捷键管理器
   */
  init() {
    this.bindGlobalListeners();
    this.registerDefaultShortcuts();
    console.log('[KeyboardShortcutManager] 初始化完成');
  }

  /**
   * 绑定全局键盘监听
   */
  bindGlobalListeners() {
    document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    document.addEventListener('keyup', (e) => this.handleKeyUp(e));
    
    // 防止在输入框中触发快捷键
    document.addEventListener('focusin', (e) => {
      if (this.isInputElement(e.target)) {
        this.setContext('input');
      }
    });
    
    document.addEventListener('focusout', (e) => {
      if (this.isInputElement(e.target)) {
        this.setContext('global');
      }
    });
  }

  /**
   * 检查是否为输入元素
   * @param {Element} element - DOM元素
   * @returns {boolean}
   */
  isInputElement(element) {
    const tagName = element.tagName.toLowerCase();
    const inputTypes = ['input', 'textarea', 'select'];
    const editable = element.isContentEditable;
    
    return inputTypes.includes(tagName) || editable;
  }

  /**
   * 处理按键按下
   * @param {KeyboardEvent} e - 键盘事件
   */
  handleKeyDown(e) {
    if (!this.enabled) return;
    
    // 记录按下的键
    this.pressedKeys.add(e.key.toLowerCase());
    
    // 构建快捷键标识
    const shortcut = this.buildShortcutIdentifier(e);
    
    // 查找并执行快捷键
    const handler = this.findShortcutHandler(shortcut);
    if (handler) {
      e.preventDefault();
      e.stopPropagation();
      
      try {
        handler.callback(e);
      } catch (error) {
        console.error(`[KeyboardShortcutManager] 快捷键执行错误 [${shortcut}]:`, error);
      }
    }
  }

  /**
   * 处理按键释放
   * @param {KeyboardEvent} e - 键盘事件
   */
  handleKeyUp(e) {
    this.pressedKeys.delete(e.key.toLowerCase());
  }

  /**
   * 构建快捷键标识符
   * @param {KeyboardEvent} e - 键盘事件
   * @returns {string}
   */
  buildShortcutIdentifier(e) {
    const parts = [];
    
    if (e.ctrlKey || e.metaKey) parts.push('ctrl');
    if (e.altKey) parts.push('alt');
    if (e.shiftKey) parts.push('shift');
    
    // 特殊键映射
    const keyMap = {
      'ArrowUp': 'up',
      'ArrowDown': 'down',
      'ArrowLeft': 'left',
      'ArrowRight': 'right',
      'Enter': 'enter',
      'Escape': 'esc',
      'Tab': 'tab',
      ' ': 'space',
      'Backspace': 'backspace',
      'Delete': 'delete',
      'Home': 'home',
      'End': 'end',
      'PageUp': 'pageup',
      'PageDown': 'pagedown'
    };
    
    const key = keyMap[e.key] || e.key.toLowerCase();
    parts.push(key);
    
    return parts.join('+');
  }

  /**
   * 查找快捷键处理器
   * @param {string} shortcut - 快捷键标识
   * @returns {Object|null}
   */
  findShortcutHandler(shortcut) {
    // 优先查找当前上下文的快捷键
    const contextKey = `${this.context}:${shortcut}`;
    if (this.contextShortcuts.has(contextKey)) {
      return this.contextShortcuts.get(contextKey);
    }
    
    // 查找全局快捷键
    return this.shortcuts.get(shortcut) || null;
  }

  /**
   * 注册快捷键
   * @param {string} shortcut - 快捷键 (如 'ctrl+k', 'shift+?')
   * @param {Function} callback - 回调函数
   * @param {Object} options - 选项
   */
  register(shortcut, callback, options = {}) {
    const {
      description = '',
      context = 'global',
      preventDefault = true
    } = options;
    
    const handler = {
      shortcut,
      callback,
      description,
      context,
      preventDefault
    };
    
    if (context === 'global') {
      this.shortcuts.set(shortcut, handler);
    } else {
      const contextKey = `${context}:${shortcut}`;
      this.contextShortcuts.set(contextKey, handler);
    }
    
    console.log(`[KeyboardShortcutManager] 注册快捷键: [${context}] ${shortcut}`);
  }

  /**
   * 注销快捷键
   * @param {string} shortcut - 快捷键
   * @param {string} context - 上下文
   */
  unregister(shortcut, context = 'global') {
    if (context === 'global') {
      this.shortcuts.delete(shortcut);
    } else {
      const contextKey = `${context}:${shortcut}`;
      this.contextShortcuts.delete(contextKey);
    }
  }

  /**
   * 设置当前上下文
   * @param {string} context - 上下文名称
   */
  setContext(context) {
    this.context = context;
    console.log(`[KeyboardShortcutManager] 上下文切换: ${context}`);
  }

  /**
   * 启用快捷键
   */
  enable() {
    this.enabled = true;
  }

  /**
   * 禁用快捷键
   */
  disable() {
    this.enabled = false;
  }

  /**
   * 注册默认快捷键
   */
  registerDefaultShortcuts() {
    // 全局搜索
    this.register('ctrl+k', () => {
      if (window.globalSearch) {
        window.globalSearch.open();
      }
    }, { description: '打开全局搜索' });
    
    // 主题切换
    this.register('ctrl+shift+l', () => {
      if (window.themeManager) {
        window.themeManager.toggleTheme();
      }
    }, { description: '切换主题' });
    
    // 帮助
    this.register('shift+?', () => {
      this.showHelp();
    }, { description: '显示快捷键帮助' });
    
    // ESC关闭弹窗
    this.register('esc', () => {
      this.handleEscape();
    }, { description: '关闭弹窗/取消操作' });
    
    // 导航快捷键
    this.register('ctrl+1', () => this.navigateTo('/dashboard'), { description: '仪表盘' });
    this.register('ctrl+2', () => this.navigateTo('/alerts'), { description: '告警中心' });
    this.register('ctrl+3', () => this.navigateTo('/dag'), { description: 'DAG流水线' });
    this.register('ctrl+4', () => this.navigateTo('/scripts'), { description: '脚本管理' });
    this.register('ctrl+5', () => this.navigateTo('/ar'), { description: 'AR监控' });
    this.register('ctrl+6', () => this.navigateTo('/api-doc'), { description: 'API文档' });
    
    // 刷新
    this.register('ctrl+r', () => {
      window.location.reload();
    }, { description: '刷新页面' });
    
    // 返回
    this.register('alt+left', () => {
      window.history.back();
    }, { description: '返回上一页' });
  }

  /**
   * 处理ESC键
   */
  handleEscape() {
    // 关闭所有弹窗
    const modals = document.querySelectorAll('.modal.active, .global-search-modal.active');
    modals.forEach(modal => {
      modal.classList.remove('active');
      setTimeout(() => modal.remove(), 200);
    });
    
    // 关闭帮助
    if (this.helpModal) {
      this.closeHelp();
    }
  }

  /**
   * 页面导航
   * @param {string} path - 路径
   */
  navigateTo(path) {
    window.location.href = path;
  }

  /**
   * 显示快捷键帮助
   */
  showHelp() {
    if (this.helpModal) return;
    
    const shortcuts = this.getAllShortcuts();
    
    this.helpModal = document.createElement('div');
    this.helpModal.className = 'keyboard-shortcuts-modal';
    this.helpModal.innerHTML = `
      <div class="shortcuts-overlay" data-action="close-help">
        <div class="shortcuts-content">
          <div class="shortcuts-header">
            <h2>⌨️ 键盘快捷键</h2>
            <button class="btn btn-ghost" data-action="close-help">✕</button>
          </div>
          <div class="shortcuts-body">
            ${this.renderShortcutsByCategory(shortcuts)}
          </div>
          <div class="shortcuts-footer">
            <p>按 <kbd>ESC</kbd> 或点击遮罩关闭</p>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.helpModal);
    
    // 绑定事件
    this.helpModal.querySelector('[data-action="close-help"]').addEventListener('click', (e) => {
      if (e.target === e.currentTarget || e.target.dataset.action === 'close-help') {
        this.closeHelp();
      }
    });
    
    // 显示动画
    requestAnimationFrame(() => {
      this.helpModal.classList.add('active');
    });
  }

  /**
   * 关闭帮助
   */
  closeHelp() {
    if (!this.helpModal) return;
    
    this.helpModal.classList.remove('active');
    setTimeout(() => {
      if (this.helpModal) {
        this.helpModal.remove();
        this.helpModal = null;
      }
    }, 200);
  }

  /**
   * 获取所有快捷键
   * @returns {Array}
   */
  getAllShortcuts() {
    const all = [
      ...Array.from(this.shortcuts.values()),
      ...Array.from(this.contextShortcuts.values())
    ];
    
    // 去重
    const seen = new Set();
    return all.filter(s => {
      const key = `${s.context}:${s.shortcut}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  /**
   * 按类别渲染快捷键
   * @param {Array} shortcuts - 快捷键列表
   * @returns {string}
   */
  renderShortcutsByCategory(shortcuts) {
    const categories = {
      '导航': ['ctrl+1', 'ctrl+2', 'ctrl+3', 'ctrl+4', 'ctrl+5', 'ctrl+6', 'alt+left'],
      '功能': ['ctrl+k', 'ctrl+shift+l', 'ctrl+r', 'shift+?'],
      '通用': ['esc']
    };
    
    let html = '';
    
    Object.entries(categories).forEach(([category, keys]) => {
      const items = shortcuts.filter(s => keys.some(k => s.shortcut.includes(k)));
      if (items.length === 0) return;
      
      html += `
        <div class="shortcuts-category">
          <h3>${category}</h3>
          <div class="shortcuts-list">
            ${items.map(s => `
              <div class="shortcut-item">
                <kbd class="shortcut-key">${this.formatShortcut(s.shortcut)}</kbd>
                <span class="shortcut-desc">${s.description}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    });
    
    return html;
  }

  /**
   * 格式化快捷键显示
   * @param {string} shortcut - 快捷键
   * @returns {string}
   */
  formatShortcut(shortcut) {
    return shortcut
      .replace(/ctrl/g, 'Ctrl')
      .replace(/alt/g, 'Alt')
      .replace(/shift/g, 'Shift')
      .replace(/\+/g, ' + ');
  }

  /**
   * 导出快捷键配置
   * @returns {Object}
   */
  exportConfig() {
    const shortcuts = this.getAllShortcuts();
    return {
      version: '1.0.0',
      shortcuts: shortcuts.map(s => ({
        shortcut: s.shortcut,
        description: s.description,
        context: s.context
      }))
    };
  }

  /**
   * 导入快捷键配置
   * @param {Object} config - 配置对象
   */
  importConfig(config) {
    if (!config || !config.shortcuts) return;
    
    // 清除现有快捷键
    this.shortcuts.clear();
    this.contextShortcuts.clear();
    
    // 重新注册
    config.shortcuts.forEach(s => {
      this.register(s.shortcut, () => {}, {
        description: s.description,
        context: s.context
      });
    });
  }

  /**
   * 销毁
   */
  destroy() {
    this.shortcuts.clear();
    this.contextShortcuts.clear();
    this.pressedKeys.clear();
    
    if (this.helpModal) {
      this.closeHelp();
    }
  }
}
