/**
 * 主题持久化管理器
 * 处理主题切换的持久化存储和同步
 * 版本: v1.0.0
 */

export class ThemePersistenceManager {
  constructor() {
    this.STORAGE_KEY = 'yl_monitor_theme';
    this.SYNC_CHANNEL = 'theme_sync';
    this.currentTheme = 'light';
    this.listeners = new Set();
    this.broadcastChannel = null;
    this.initBroadcastChannel();
  }

  /**
   * 初始化广播通道（跨标签页同步）
   */
  initBroadcastChannel() {
    if (typeof BroadcastChannel !== 'undefined') {
      this.broadcastChannel = new BroadcastChannel(this.SYNC_CHANNEL);
      this.broadcastChannel.onmessage = (event) => {
        if (event.data.type === 'theme_change') {
          this.applyTheme(event.data.theme, false);
        }
      };
    }
  }

  /**
   * 初始化主题
   * @returns {string} 当前主题
   */
  init() {
    // 1. 检查本地存储
    const savedTheme = this.getStoredTheme();
    
    // 2. 检查系统偏好
    const systemTheme = this.getSystemTheme();
    
    // 3. 检查URL参数
    const urlTheme = this.getUrlTheme();
    
    // 优先级: URL > 本地存储 > 系统偏好
    const theme = urlTheme || savedTheme || systemTheme;
    
    this.applyTheme(theme);
    
    // 监听系统主题变化
    this.watchSystemTheme();
    
    console.log('[ThemePersistenceManager] 主题初始化完成:', theme);
    return theme;
  }

  /**
   * 获取存储的主题
   * @returns {string|null}
   */
  getStoredTheme() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        const { theme, timestamp } = JSON.parse(data);
        // 检查是否过期（30天）
        if (Date.now() - timestamp < 30 * 24 * 60 * 60 * 1000) {
          return theme;
        }
      }
    } catch (error) {
      console.error('[ThemePersistenceManager] 读取存储主题失败:', error);
    }
    return null;
  }

  /**
   * 获取系统主题偏好
   * @returns {string}
   */
  getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  /**
   * 获取URL主题参数
   * @returns {string|null}
   */
  getUrlTheme() {
    const params = new URLSearchParams(window.location.search);
    return params.get('theme');
  }

  /**
   * 监听系统主题变化
   */
  watchSystemTheme() {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    mediaQuery.addEventListener('change', (e) => {
      // 只有在用户没有手动设置主题时才自动切换
      if (!this.getStoredTheme()) {
        const newTheme = e.matches ? 'dark' : 'light';
        this.applyTheme(newTheme);
      }
    });
  }

  /**
   * 应用主题
   * @param {string} theme - 主题名称
   * @param {boolean} save - 是否保存到存储
   */
  applyTheme(theme, save = true) {
    if (!['light', 'dark', 'auto'].includes(theme)) {
      theme = 'light';
    }

    this.currentTheme = theme;

    // 确定实际应用的主题
    let actualTheme = theme;
    if (theme === 'auto') {
      actualTheme = this.getSystemTheme();
    }

    // 应用到DOM
    document.documentElement.setAttribute('data-theme', actualTheme);
    document.body.classList.remove('theme-light', 'theme-dark');
    document.body.classList.add(`theme-${actualTheme}`);

    // 更新meta theme-color
    this.updateMetaThemeColor(actualTheme);

    // 保存到本地存储
    if (save) {
      this.saveTheme(theme);
    }

    // 广播到其他标签页
    this.broadcastTheme(theme);

    // 触发监听器
    this.notifyListeners(theme, actualTheme);

    console.log('[ThemePersistenceManager] 主题已应用:', theme, '(实际:', actualTheme + ')');
  }

  /**
   * 更新meta theme-color
   * @param {string} theme - 主题
   */
  updateMetaThemeColor(theme) {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      const colors = {
        'light': '#ffffff',
        'dark': '#0f172a'
      };
      meta.setAttribute('content', colors[theme] || colors.light);
    }
  }

  /**
   * 保存主题
   * @param {string} theme - 主题名称
   */
  saveTheme(theme) {
    try {
      const data = {
        theme,
        timestamp: Date.now(),
        url: window.location.href
      };
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('[ThemePersistenceManager] 保存主题失败:', error);
    }
  }

  /**
   * 广播主题变化
   * @param {string} theme - 主题名称
   */
  broadcastTheme(theme) {
    if (this.broadcastChannel) {
      this.broadcastChannel.postMessage({
        type: 'theme_change',
        theme,
        timestamp: Date.now()
      });
    }
  }

  /**
   * 切换主题
   * @returns {string} 新主题
   */
  toggleTheme() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
    return newTheme;
  }

  /**
   * 设置主题
   * @param {string} theme - 主题名称
   */
  setTheme(theme) {
    this.applyTheme(theme);
  }

  /**
   * 获取当前主题
   * @returns {string}
   */
  getCurrentTheme() {
    return this.currentTheme;
  }

  /**
   * 获取实际应用的主题（处理auto情况）
   * @returns {string}
   */
  getActualTheme() {
    if (this.currentTheme === 'auto') {
      return this.getSystemTheme();
    }
    return this.currentTheme;
  }

  /**
   * 添加主题变化监听器
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消监听函数
   */
  onThemeChange(callback) {
    this.listeners.add(callback);
    
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * 通知所有监听器
   * @param {string} theme - 设置的主题
   * @param {string} actualTheme - 实际应用的主题
   */
  notifyListeners(theme, actualTheme) {
    this.listeners.forEach(callback => {
      try {
        callback(theme, actualTheme);
      } catch (error) {
        console.error('[ThemePersistenceManager] 监听器错误:', error);
      }
    });
  }

  /**
   * 创建主题切换UI
   * @param {HTMLElement} container - 容器元素
   */
  createThemeToggle(container) {
    const toggle = document.createElement('button');
    toggle.className = 'theme-toggle-btn';
    toggle.id = 'theme-toggle';
    toggle.innerHTML = this.getThemeIcon(this.currentTheme);
    toggle.title = `当前主题: ${this.currentTheme} (点击切换)`;
    
    toggle.addEventListener('click', () => {
      const newTheme = this.toggleTheme();
      toggle.innerHTML = this.getThemeIcon(newTheme);
      toggle.title = `当前主题: ${newTheme} (点击切换)`;
    });

    // 监听主题变化更新图标
    this.onThemeChange((theme) => {
      toggle.innerHTML = this.getThemeIcon(theme);
      toggle.title = `当前主题: ${theme} (点击切换)`;
    });

    container.appendChild(toggle);
    return toggle;
  }

  /**
   * 获取主题图标
   * @param {string} theme - 主题
   * @returns {string}
   */
  getThemeIcon(theme) {
    const icons = {
      'light': '☀️',
      'dark': '🌙',
      'auto': '🔄'
    };
    return icons[theme] || '☀️';
  }

  /**
   * 创建主题选择器
   * @param {HTMLElement} container - 容器元素
   */
  createThemeSelector(container) {
    const selector = document.createElement('div');
    selector.className = 'theme-selector';
    selector.innerHTML = `
      <div class="theme-options">
        <button class="theme-option ${this.currentTheme === 'light' ? 'active' : ''}" data-theme="light">
          <span class="theme-icon">☀️</span>
          <span class="theme-label">亮色</span>
        </button>
        <button class="theme-option ${this.currentTheme === 'dark' ? 'active' : ''}" data-theme="dark">
          <span class="theme-icon">🌙</span>
          <span class="theme-label">暗色</span>
        </button>
        <button class="theme-option ${this.currentTheme === 'auto' ? 'active' : ''}" data-theme="auto">
          <span class="theme-icon">🔄</span>
          <span class="theme-label">自动</span>
        </button>
      </div>
    `;

    // 绑定点击事件
    selector.querySelectorAll('.theme-option').forEach(btn => {
      btn.addEventListener('click', () => {
        const theme = btn.dataset.theme;
        this.setTheme(theme);
        
        // 更新选中状态
        selector.querySelectorAll('.theme-option').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });

    // 监听主题变化
    this.onThemeChange((theme) => {
      selector.querySelectorAll('.theme-option').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
      });
    });

    container.appendChild(selector);
    return selector;
  }

  /**
   * 导出主题设置
   * @returns {Object}
   */
  exportSettings() {
    return {
      theme: this.currentTheme,
      timestamp: Date.now()
    };
  }

  /**
   * 导入主题设置
   * @param {Object} settings - 设置对象
   */
  importSettings(settings) {
    if (settings && settings.theme) {
      this.applyTheme(settings.theme);
    }
  }

  /**
   * 清理存储
   */
  clearStorage() {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('[ThemePersistenceManager] 清理存储失败:', error);
    }
  }

  /**
   * 销毁
   */
  destroy() {
    this.listeners.clear();
    
    if (this.broadcastChannel) {
      this.broadcastChannel.close();
      this.broadcastChannel = null;
    }
  }
}
