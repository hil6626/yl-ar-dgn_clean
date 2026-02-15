/**
 * 全局搜索组件
 * 支持跨页面搜索脚本、DAG、告警、API文档等
 * 版本: v1.0.0
 */

export class GlobalSearch {
  constructor() {
    this.modal = null;
    this.searchInput = null;
    this.resultsContainer = null;
    this.searchTimeout = null;
    this.currentQuery = '';
    this.selectedIndex = -1;
    this.searchResults = [];
    this.recentSearches = this.loadRecentSearches();
    this.searchHistory = this.loadSearchHistory();
  }

  /**
   * 初始化全局搜索
   */
  init() {
    // 创建搜索触发按钮（添加到导航栏）
    this.createSearchTrigger();
    
    // 绑定快捷键
    this.bindShortcuts();
  }

  /**
   * 创建搜索触发按钮
   */
  createSearchTrigger() {
    const navbar = document.querySelector('.navbar-nav');
    if (!navbar) return;

    const searchBtn = document.createElement('button');
    searchBtn.className = 'nav-link search-trigger';
    searchBtn.innerHTML = `
      <span>🔍</span>
      <span>搜索</span>
      <kbd class="shortcut-hint">Ctrl+K</kbd>
    `;
    searchBtn.addEventListener('click', () => this.open());

    // 插入到导航栏末尾
    navbar.appendChild(searchBtn);
  }

  /**
   * 绑定快捷键
   */
  bindShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl+K 或 Cmd+K 打开搜索
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        this.open();
      }

      // ESC 关闭搜索
      if (e.key === 'Escape' && this.modal) {
        this.close();
      }

      // 上下箭头导航
      if (this.modal) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.navigateResults(1);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.navigateResults(-1);
        } else if (e.key === 'Enter') {
          e.preventDefault();
          this.selectResult();
        }
      }
    });
  }

  /**
   * 打开搜索弹窗
   */
  open() {
    if (this.modal) return;

    this.modal = document.createElement('div');
    this.modal.className = 'global-search-modal';
    this.modal.innerHTML = `
      <div class="search-modal-overlay">
        <div class="search-modal-content">
          <!-- 搜索输入区 -->
          <div class="search-input-container">
            <span class="search-icon">🔍</span>
            <input 
              type="text" 
              class="search-input" 
              id="global-search-input"
              placeholder="搜索脚本、DAG、告警、API文档... (Ctrl+K)"
              autocomplete="off"
            >
            <span class="search-shortcut">ESC 关闭</span>
          </div>
          
          <!-- 搜索结果区 -->
          <div class="search-results-container" id="search-results">
            <div class="search-placeholder">
              <div class="placeholder-icon">🔍</div>
              <p>输入关键词开始搜索</p>
              <p class="placeholder-hint">支持搜索脚本名称、DAG ID、告警内容、API端点</p>
            </div>
          </div>
          
          <!-- 搜索底部 -->
          <div class="search-footer">
            <div class="search-tips">
              <span><kbd>↑</kbd> <kbd>↓</kbd> 导航</span>
              <span><kbd>Enter</kbd> 选择</span>
              <span><kbd>ESC</kbd> 关闭</span>
            </div>
            <div class="search-stats" id="search-stats"></div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.modal);

    // 获取元素引用
    this.searchInput = document.getElementById('global-search-input');
    this.resultsContainer = document.getElementById('search-results');

    // 绑定事件
    this.bindModalEvents();

    // 显示动画
    requestAnimationFrame(() => {
      this.modal.classList.add('active');
      this.searchInput.focus();
    });

    // 显示最近搜索
    if (this.recentSearches.length > 0) {
      this.showRecentSearches();
    }
  }

  /**
   * 绑定弹窗事件
   */
  bindModalEvents() {
    // 输入搜索
    this.searchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      
      // 清除之前的搜索超时
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }

      if (query.length === 0) {
        this.showRecentSearches();
        return;
      }

      // 延迟搜索，避免频繁请求
      this.searchTimeout = setTimeout(() => {
        this.performSearch(query);
      }, 300);
    });

    // 点击遮罩关闭
    this.modal.querySelector('.search-modal-overlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.close();
      }
    });
  }

  /**
   * 执行搜索
   * @param {string} query - 搜索关键词
   */
  async performSearch(query) {
    this.currentQuery = query;
    this.showLoading();

    try {
      // 并行搜索多个资源
      const [scripts, dags, alerts, apiDocs] = await Promise.all([
        this.searchScripts(query),
        this.searchDAGs(query),
        this.searchAlerts(query),
        this.searchAPIDocs(query)
      ]);

      // 合并结果
      this.searchResults = [
        ...scripts.map(s => ({ ...s, type: 'script', category: '脚本' })),
        ...dags.map(d => ({ ...d, type: 'dag', category: 'DAG' })),
        ...alerts.map(a => ({ ...a, type: 'alert', category: '告警' })),
        ...apiDocs.map(d => ({ ...d, type: 'api', category: 'API' }))
      ];

      // 保存到搜索历史
      this.addToHistory(query);

      // 显示结果
      this.displayResults();

    } catch (error) {
      console.error('[GlobalSearch] 搜索失败:', error);
      this.showError('搜索失败，请稍后重试');
    }
  }

  /**
   * 搜索脚本
   * @param {string} query - 关键词
   * @returns {Promise<Array>}
   */
  async searchScripts(query) {
    try {
      const response = await fetch(`/api/v1/scripts/search?q=${encodeURIComponent(query)}&limit=5`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.scripts || [];
    } catch (error) {
      console.error('[GlobalSearch] 搜索脚本失败:', error);
      return [];
    }
  }

  /**
   * 搜索DAG
   * @param {string} query - 关键词
   * @returns {Promise<Array>}
   */
  async searchDAGs(query) {
    try {
      const response = await fetch(`/api/v1/dag/search?q=${encodeURIComponent(query)}&limit=5`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.dags || [];
    } catch (error) {
      console.error('[GlobalSearch] 搜索DAG失败:', error);
      return [];
    }
  }

  /**
   * 搜索告警
   * @param {string} query - 关键词
   * @returns {Promise<Array>}
   */
  async searchAlerts(query) {
    try {
      const response = await fetch(`/api/v1/alerts/search?q=${encodeURIComponent(query)}&limit=5`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.alerts || [];
    } catch (error) {
      console.error('[GlobalSearch] 搜索告警失败:', error);
      return [];
    }
  }

  /**
   * 搜索API文档
   * @param {string} query - 关键词
   * @returns {Promise<Array>}
   */
  async searchAPIDocs(query) {
    try {
      const response = await fetch(`/api/v1/api-docs/search?q=${encodeURIComponent(query)}&limit=5`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.endpoints || [];
    } catch (error) {
      console.error('[GlobalSearch] 搜索API文档失败:', error);
      return [];
    }
  }

  /**
   * 显示搜索结果
   */
  displayResults() {
    if (this.searchResults.length === 0) {
      this.resultsContainer.innerHTML = `
        <div class="search-no-results">
          <div class="no-results-icon">😕</div>
          <p>未找到与 "${this.escapeHtml(this.currentQuery)}" 相关的结果</p>
          <p class="no-results-hint">尝试使用不同的关键词或检查拼写</p>
        </div>
      `;
      this.updateStats(0);
      return;
    }

    // 按类别分组
    const grouped = this.groupByCategory(this.searchResults);
    
    let html = '';
    this.selectedIndex = -1;

    Object.entries(grouped).forEach(([category, items]) => {
      html += `
        <div class="search-category">
          <div class="category-header">
            <span class="category-icon">${this.getCategoryIcon(category)}</span>
            <span class="category-name">${category}</span>
            <span class="category-count">${items.length}</span>
          </div>
          <div class="category-items">
            ${items.map((item, index) => this.renderResultItem(item, index)).join('')}
          </div>
        </div>
      `;
    });

    this.resultsContainer.innerHTML = html;
    this.updateStats(this.searchResults.length);

    // 绑定结果项点击事件
    this.resultsContainer.querySelectorAll('.search-result-item').forEach((el, index) => {
      el.addEventListener('click', () => {
        this.selectedIndex = index;
        this.selectResult();
      });
      
      el.addEventListener('mouseenter', () => {
        this.selectedIndex = index;
        this.highlightResult(index);
      });
    });
  }

  /**
   * 渲染结果项
   * @param {Object} item - 结果项
   * @param {number} index - 索引
   * @returns {string}
   */
  renderResultItem(item, index) {
    const title = item.name || item.title || item.id || '未命名';
    const description = item.description || item.message || item.summary || '';
    const url = this.getItemUrl(item);
    
    return `
      <div class="search-result-item" data-index="${index}" data-url="${url}" data-type="${item.type}">
        <div class="result-icon">${this.getTypeIcon(item.type)}</div>
        <div class="result-content">
          <div class="result-title">${this.highlightMatch(title, this.currentQuery)}</div>
          ${description ? `<div class="result-description">${this.highlightMatch(description, this.currentQuery)}</div>` : ''}
          <div class="result-meta">
            <span class="result-type">${item.category}</span>
            ${item.status ? `<span class="result-status status-${item.status}">${item.status}</span>` : ''}
          </div>
        </div>
        <div class="result-action">→</div>
      </div>
    `;
  }

  /**
   * 获取项目URL
   * @param {Object} item - 结果项
   * @returns {string}
   */
  getItemUrl(item) {
    switch (item.type) {
      case 'script':
        return `/scripts?id=${item.id}`;
      case 'dag':
        return `/dag?id=${item.id}`;
      case 'alert':
        return `/alerts?id=${item.id}`;
      case 'api':
        return `/api-doc?endpoint=${encodeURIComponent(item.path || '')}`;
      default:
        return '/';
    }
  }

  /**
   * 高亮匹配文本
   * @param {string} text - 原文本
   * @param {string} query - 关键词
   * @returns {string}
   */
  highlightMatch(text, query) {
    if (!query || !text) return text;
    
    const regex = new RegExp(`(${this.escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  /**
   * 按类别分组
   * @param {Array} items - 结果项
   * @returns {Object}
   */
  groupByCategory(items) {
    return items.reduce((acc, item) => {
      const category = item.category || '其他';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(item);
      return acc;
    }, {});
  }

  /**
   * 获取类别图标
   * @param {string} category - 类别
   * @returns {string}
   */
  getCategoryIcon(category) {
    const icons = {
      '脚本': '📜',
      'DAG': '🔄',
      '告警': '🔔',
      'API': '📚'
    };
    return icons[category] || '📄';
  }

  /**
   * 获取类型图标
   * @param {string} type - 类型
   * @returns {string}
   */
  getTypeIcon(type) {
    const icons = {
      'script': '📜',
      'dag': '🔄',
      'alert': '🔔',
      'api': '📚'
    };
    return icons[type] || '📄';
  }

  /**
   * 显示最近搜索
   */
  showRecentSearches() {
    if (this.recentSearches.length === 0) {
      this.resultsContainer.innerHTML = `
        <div class="search-placeholder">
          <div class="placeholder-icon">🔍</div>
          <p>输入关键词开始搜索</p>
          <p class="placeholder-hint">支持搜索脚本名称、DAG ID、告警内容、API端点</p>
        </div>
      `;
      return;
    }

    const html = `
      <div class="search-recent">
        <div class="recent-header">
          <span>🕐</span>
          <span>最近搜索</span>
        </div>
        <div class="recent-items">
          ${this.recentSearches.map((query, index) => `
            <div class="recent-item" data-query="${this.escapeHtml(query)}">
              <span class="recent-icon">🔍</span>
              <span class="recent-text">${this.escapeHtml(query)}</span>
              <button class="recent-delete" data-index="${index}">×</button>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    this.resultsContainer.innerHTML = html;

    // 绑定最近搜索点击事件
    this.resultsContainer.querySelectorAll('.recent-item').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target.classList.contains('recent-delete')) {
          e.stopPropagation();
          this.removeRecentSearch(parseInt(e.target.dataset.index));
        } else {
          const query = el.dataset.query;
          this.searchInput.value = query;
          this.performSearch(query);
        }
      });
    });
  }

  /**
   * 显示加载状态
   */
  showLoading() {
    this.resultsContainer.innerHTML = `
      <div class="search-loading">
        <div class="loading-spinner"></div>
        <p>正在搜索...</p>
      </div>
    `;
  }

  /**
   * 显示错误
   * @param {string} message - 错误消息
   */
  showError(message) {
    this.resultsContainer.innerHTML = `
      <div class="search-error">
        <div class="error-icon">⚠️</div>
        <p>${message}</p>
      </div>
    `;
  }

  /**
   * 导航结果
   * @param {number} direction - 方向 (1: 下, -1: 上)
   */
  navigateResults(direction) {
    const items = this.resultsContainer.querySelectorAll('.search-result-item');
    if (items.length === 0) return;

    this.selectedIndex += direction;
    
    // 边界检查
    if (this.selectedIndex < 0) {
      this.selectedIndex = items.length - 1;
    } else if (this.selectedIndex >= items.length) {
      this.selectedIndex = 0;
    }

    this.highlightResult(this.selectedIndex);
    
    // 滚动到可视区域
    const selected = items[this.selectedIndex];
    if (selected) {
      selected.scrollIntoView({ block: 'nearest' });
    }
  }

  /**
   * 高亮结果项
   * @param {number} index - 索引
   */
  highlightResult(index) {
    const items = this.resultsContainer.querySelectorAll('.search-result-item');
    items.forEach((item, i) => {
      item.classList.toggle('selected', i === index);
    });
  }

  /**
   * 选择结果
   */
  selectResult() {
    const items = this.resultsContainer.querySelectorAll('.search-result-item');
    if (this.selectedIndex >= 0 && this.selectedIndex < items.length) {
      const selected = items[this.selectedIndex];
      const url = selected.dataset.url;
      
      if (url) {
        this.close();
        window.location.href = url;
      }
    }
  }

  /**
   * 更新统计
   * @param {number} count - 结果数量
   */
  updateStats(count) {
    const statsEl = document.getElementById('search-stats');
    if (statsEl) {
      statsEl.textContent = count > 0 ? `找到 ${count} 个结果` : '';
    }
  }

  /**
   * 添加到历史
   * @param {string} query - 查询词
   */
  addToHistory(query) {
    // 添加到最近搜索
    this.recentSearches = [query, ...this.recentSearches.filter(q => q !== query)].slice(0, 10);
    this.saveRecentSearches();

    // 添加到搜索历史记录
    this.searchHistory.push({
      query,
      timestamp: Date.now(),
      resultCount: this.searchResults.length
    });
    this.saveSearchHistory();
  }

  /**
   * 移除最近搜索
   * @param {number} index - 索引
   */
  removeRecentSearch(index) {
    this.recentSearches.splice(index, 1);
    this.saveRecentSearches();
    this.showRecentSearches();
  }

  /**
   * 加载最近搜索
   * @returns {Array}
   */
  loadRecentSearches() {
    try {
      const data = localStorage.getItem('global_search_recent');
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  /**
   * 保存最近搜索
   */
  saveRecentSearches() {
    try {
      localStorage.setItem('global_search_recent', JSON.stringify(this.recentSearches));
    } catch (error) {
      console.error('[GlobalSearch] 保存最近搜索失败:', error);
    }
  }

  /**
   * 加载搜索历史
   * @returns {Array}
   */
  loadSearchHistory() {
    try {
      const data = localStorage.getItem('global_search_history');
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  /**
   * 保存搜索历史
   */
  saveSearchHistory() {
    try {
      // 只保留最近100条
      const trimmed = this.searchHistory.slice(-100);
      localStorage.setItem('global_search_history', JSON.stringify(trimmed));
    } catch (error) {
      console.error('[GlobalSearch] 保存搜索历史失败:', error);
    }
  }

  /**
   * 关闭搜索
   */
  close() {
    if (this.modal) {
      this.modal.classList.remove('active');
      setTimeout(() => {
        if (this.modal) {
          this.modal.remove();
          this.modal = null;
        }
      }, 200);
    }
  }

  /**
   * HTML转义
   * @param {string} text - 文本
   * @returns {string}
   */
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * 正则转义
   * @param {string} string - 字符串
   * @returns {string}
   */
  escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\\\$&');
  }
}
