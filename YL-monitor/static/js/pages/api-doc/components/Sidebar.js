/**
 * API文档侧边栏组件
 * 拆分自: page-api-doc.js
 * 版本: v1.0.0
 */

export class Sidebar {
  constructor(page) {
    this.page = page;
    this.container = document.getElementById('api-sidebar-mount');
  }

  /**
   * 渲染侧边栏
   */
  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="api-sidebar-header">
        <h3>API模块</h3>
        <button class="api-sidebar-toggle" id="sidebar-toggle" title="折叠/展开">
          <span>◀</span>
        </button>
      </div>
      <div class="api-search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="sidebar-search" placeholder="筛选模块...">
      </div>
      <ul class="api-modules-list" id="api-modules-list">
        <!-- 动态加载 -->
      </ul>
    `;

    this.bindEvents();
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 绑定折叠按钮
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.page.toggleSidebar());
    }

    // 绑定侧边栏搜索
    const sidebarSearch = document.getElementById('sidebar-search');
    if (sidebarSearch) {
      sidebarSearch.addEventListener('input', (e) => this.page.filterSidebar(e.target.value));
    }
  }

  /**
   * 渲染模块列表
   */
  renderModulesList() {
    const list = document.getElementById('api-modules-list');
    if (!list) return;

    const apiData = this.page.apiData;

    list.innerHTML = apiData.map((module, moduleIndex) => `
      <li class="api-module-group">
        <div class="api-module-header ${module.expanded ? 'expanded' : ''}" data-module="${moduleIndex}">
          <span class="toggle-icon">▶</span>
          <span class="module-icon">${module.icon}</span>
          <span class="module-name">${module.module}</span>
        </div>
        <ul class="api-module-children ${module.expanded ? 'expanded' : ''}" id="module-${moduleIndex}">
          ${module.endpoints.map(endpoint => `
            <li class="api-endpoint-link" 
                data-endpoint-id="${endpoint.id}"
                data-module="${moduleIndex}"
                data-action="select-endpoint">
              <span class="method-badge http-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
              <span class="endpoint-path">${endpoint.name}</span>
            </li>
          `).join('')}
        </ul>
      </li>
    `).join('');

    // 绑定模块展开/折叠
    list.querySelectorAll('.api-module-header').forEach(header => {
      header.addEventListener('click', (e) => {
        const moduleIndex = header.dataset.module;
        const children = document.getElementById(`module-${moduleIndex}`);
        const isExpanded = header.classList.contains('expanded');
        
        header.classList.toggle('expanded', !isExpanded);
        children.classList.toggle('expanded', !isExpanded);
      });
    });
  }

  /**
   * 更新激活状态
   * @param {string} endpointId - 当前选中的端点ID
   */
  updateActiveState(endpointId) {
    document.querySelectorAll('.api-endpoint-link').forEach(link => {
      link.classList.toggle('active', link.dataset.endpointId === endpointId);
    });
  }
}
