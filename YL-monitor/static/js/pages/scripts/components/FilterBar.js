/**
 * 筛选栏组件
 * 拆分自: page-scripts.js renderFilterBar()
 * 版本: v1.0.0
 */

export class FilterBar {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('scripts-filter-bar');
  }

  /**
   * 渲染筛选栏
   */
  render() {
    if (!this.mount) {
      console.warn('[FilterBar] 挂载点不存在: #scripts-filter-bar');
      return;
    }

    const counts = this.getStatusCounts();

    this.mount.innerHTML = `
      <div class="filter-section">
        <span class="filter-label">状态筛选:</span>
        <div class="filter-tabs">
          <button class="filter-tab ${this.page.currentFilter === 'all' ? 'active' : ''}" data-filter="all">
            全部 <span class="count">${counts.all}</span>
          </button>
          <button class="filter-tab ${this.page.currentFilter === 'running' ? 'active' : ''}" data-filter="running">
            运行中 <span class="count">${counts.running}</span>
          </button>
          <button class="filter-tab ${this.page.currentFilter === 'stopped' ? 'active' : ''}" data-filter="stopped">
            已停止 <span class="count">${counts.stopped}</span>
          </button>
          <button class="filter-tab ${this.page.currentFilter === 'error' ? 'active' : ''}" data-filter="error">
            有错误 <span class="count">${counts.error}</span>
          </button>
        </div>
      </div>
      <div class="filter-section">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input type="text" id="script-search" placeholder="搜索脚本名称..." value="${this.page.searchQuery}">
        </div>
        <select class="sort-select" id="sort-scripts">
          <option value="name" ${this.page.sortBy === 'name' ? 'selected' : ''}>按名称</option>
          <option value="status" ${this.page.sortBy === 'status' ? 'selected' : ''}>按状态</option>
          <option value="lastRun" ${this.page.sortBy === 'lastRun' ? 'selected' : ''}>按最后运行</option>
          <option value="created" ${this.page.sortBy === 'created' ? 'selected' : ''}>按创建时间</option>
        </select>
      </div>
    `;

    this.bindEvents();
  }

  /**
   * 获取状态统计
   * @returns {Object} 状态计数
   */
  getStatusCounts() {
    const counts = { 
      all: this.page.scripts.length, 
      running: 0, 
      stopped: 0, 
      error: 0, 
      pending: 0 
    };
    
    this.page.scripts.forEach(s => {
      if (counts[s.status] !== undefined) {
        counts[s.status]++;
      }
    });
    
    return counts;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 筛选标签
    this.mount?.addEventListener('click', (e) => {
      const tab = e.target.closest('.filter-tab');
      if (tab) {
        this.page.setFilter(tab.dataset.filter);
      }
    });

    // 搜索
    document.getElementById('script-search')?.addEventListener('input', (e) => {
      this.page.searchQuery = e.target.value;
      this.page.applyFilters();
      this.page.scriptList.render();
    });

    // 排序
    document.getElementById('sort-scripts')?.addEventListener('change', (e) => {
      this.page.sortBy = e.target.value;
      this.page.applyFilters();
      this.page.scriptList.render();
    });
  }
}
