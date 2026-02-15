/**
 * API Doc页面入口
 * 重构自: page-api-doc.js (600+行 → 模块化拆分)
 * 版本: v9.1.0 (增强版)
 */

// 导入组件
import { Sidebar, EndpointDetail, TestPanel, CopyManager, ParamValidator } from './components/index.js';

// 导入管理器
import { APIDataManager, CurlGenerator, ExportManager, RequestHistory } from './managers/index.js';

/**
 * API Doc页面主类
 */
export default class APIDocPage {
  /**
   * @param {Object} deps - 依赖项（可选）
   * @param {Object} deps.themeManager - 主题管理器（可选）
   * @param {Object} deps.uiComponents - UI组件库（可选）
   */
  constructor(deps = {}) {
    this.themeManager = deps.themeManager || null;
    this.ui = deps.uiComponents || { showToast: () => {} };
    this.apiBaseUrl = '/api/v1';
    this.apiData = [];
    this.currentEndpoint = null;
    this.sidebarCollapsed = false;
    
    // 初始化管理器
    this.dataManager = new APIDataManager(this);
    this.curlGenerator = new CurlGenerator();
    this.exportManager = new ExportManager(this);
    this.requestHistory = new RequestHistory(this);
    
    // 初始化组件
    this.sidebar = new Sidebar(this);
    this.endpointDetail = new EndpointDetail(this);
    this.testPanel = new TestPanel(this);
    this.copyManager = new CopyManager(this);
    this.paramValidator = new ParamValidator();
    
    // 挂载点引用
    this.mounts = {
      header: document.getElementById('api-header-mount'),
      sidebar: document.getElementById('api-sidebar-mount'),
      content: document.getElementById('api-content-mount'),
      testPanel: document.getElementById('api-test-panel-mount')
    };
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[APIDocPage] 初始化API文档页面 v9.1.0 (增强版)...');

    // 1. 渲染头部
    this.renderHeader();
    
    // 2. 渲染侧边栏
    this.sidebar.render();
    
    // 3. 加载API数据
    this.apiData = await this.dataManager.load();
    
    // 4. 渲染模块列表
    this.sidebar.renderModulesList();
    
    // 5. 渲染主内容区（空状态）
    this.endpointDetail.renderEmpty();
    
    // 6. 默认选中第一个端点
    if (this.apiData.length > 0 && this.apiData[0].endpoints.length > 0) {
      this.selectEndpoint(this.apiData[0].endpoints[0]);
    }
    
    // 7. 绑定事件
    this.bindEvents();
    
    // 8. 初始化代码高亮
    this.initCodeHighlight();

    console.log('[APIDocPage] API文档页面初始化完成 ✅');
    console.log('[APIDocPage] 增强功能: 三级复制降级 | 参数验证 | 多格式导出 | 请求历史');
  }

  /**
   * 渲染头部
   */
  renderHeader() {
    if (!this.mounts.header) return;

    this.mounts.header.innerHTML = `
      <div class="api-header-content">
        <div class="api-header-title">
          <span class="icon">📚</span>
          <div>
            <h1>API文档中心</h1>
            <p class="api-header-subtitle">交互式API文档 - 支持在线测试</p>
          </div>
        </div>
        <div class="api-header-actions">
          <div class="api-search-box" style="position: relative; margin-right: 12px;">
            <span class="search-icon" style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%);">🔍</span>
            <input type="text" id="api-search-input" placeholder="搜索API..." 
                   style="padding: 8px 12px 8px 36px; border: 1px solid rgba(255,255,255,0.3); 
                          background: rgba(255,255,255,0.1); color: white; border-radius: 6px; width: 240px;">
          </div>
          <button class="btn" id="export-api-doc">
            <span>📥</span> 导出文档
          </button>
        </div>
      </div>
    `;

    // 绑定搜索事件
    const searchInput = document.getElementById('api-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
    }

    // 绑定导出事件
    const exportBtn = document.getElementById('export-api-doc');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportManager.showExportDialog());
    }

    // 绑定历史记录按钮
    const historyBtn = document.getElementById('api-history-btn');
    if (historyBtn) {
      historyBtn.addEventListener('click', () => this.requestHistory.showHistoryPanel());
    }
  }

  /**
   * 通过ID选择端点
   * @param {string} endpointId - 端点ID
   */
  selectEndpointById(endpointId) {
    for (const module of this.apiData) {
      const endpoint = module.endpoints.find(e => e.id === endpointId);
      if (endpoint) {
        this.selectEndpoint(endpoint);
        break;
      }
    }
  }

  /**
   * 选择端点
   * @param {Object} endpoint - 端点数据
   */
  selectEndpoint(endpoint) {
    this.currentEndpoint = endpoint;
    
    // 更新侧边栏激活状态
    this.sidebar.updateActiveState(endpoint.id);
    
    // 渲染端点详情
    this.endpointDetail.render(endpoint);
  }

  /**
   * 切换侧边栏
   */
  toggleSidebar() {
    const sidebar = this.mounts.sidebar;
    const toggle = document.getElementById('sidebar-toggle');
    
    this.sidebarCollapsed = !this.sidebarCollapsed;
    sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
    toggle.innerHTML = this.sidebarCollapsed ? '<span>▶</span>' : '<span>◀</span>';
  }

  /**
   * 筛选侧边栏
   * @param {string} keyword - 关键词
   */
  filterSidebar(keyword) {
    const links = document.querySelectorAll('.api-endpoint-link');
    const modules = document.querySelectorAll('.api-module-group');
    
    if (!keyword) {
      links.forEach(link => link.style.display = 'flex');
      modules.forEach(m => m.style.display = 'block');
      return;
    }

    const lowerKeyword = keyword.toLowerCase();
    
    links.forEach(link => {
      const text = link.textContent.toLowerCase();
      link.style.display = text.includes(lowerKeyword) ? 'flex' : 'none';
    });

    // 隐藏没有匹配端点的模块
    modules.forEach(module => {
      const visibleLinks = module.querySelectorAll('.api-endpoint-link[style*="flex"]');
      module.style.display = visibleLinks.length > 0 ? 'block' : 'none';
    });
  }

  /**
   * 搜索处理
   * @param {string} keyword - 关键词
   */
  handleSearch(keyword) {
    this.filterSidebar(keyword);
  }

  /**
   * 生成cURL命令
   * @param {Object} endpoint - 端点数据
   * @returns {string}
   */
  generateCurlCommand(endpoint) {
    return this.curlGenerator.generate(endpoint);
  }

  /**
   * 打开测试面板
   */
  openTestPanel() {
    if (!this.currentEndpoint) return;
    this.testPanel.open(this.currentEndpoint);
  }

  /**
   * 关闭测试面板
   */
  closeTestPanel() {
    this.testPanel.close();
  }

  /**
   * 发送测试请求（带验证和历史记录）
   */
  async sendTestRequest() {
    if (!this.currentEndpoint) return;

    const endpoint = this.currentEndpoint;
    
    // 获取参数值
    const paramValues = this.testPanel.getAllParamValues();
    
    // 验证参数
    const validation = this.paramValidator.validate(endpoint, paramValues);
    if (!validation.valid) {
      // 显示验证错误
      const testPanelEl = document.getElementById('api-test-panel-mount');
      if (testPanelEl) {
        this.paramValidator.highlightErrors(testPanelEl);
        
        // 显示错误提示
        const errorHtml = this.paramValidator.getErrorHtml();
        const resultEl = testPanelEl.querySelector('.test-result');
        if (resultEl) {
          resultEl.innerHTML = errorHtml;
          resultEl.className = 'test-result error';
        }
      }
      
      this.ui.showToast({
        type: 'error',
        message: `验证失败: ${validation.errors[0].message}`
      });
      return;
    }

    // 清除验证错误
    const testPanelEl = document.getElementById('api-test-panel-mount');
    if (testPanelEl) {
      this.paramValidator.clearValidation(testPanelEl);
    }

    // 构建URL
    let url = `${window.location.origin}${endpoint.path}`;
    const pathParams = this.testPanel.getPathParams(endpoint.params);
    Object.entries(pathParams).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, value);
    });

    // 获取请求体
    const body = this.testPanel.getRequestBody();

    this.testPanel.showResult('发送请求中...');
    const startTime = Date.now();

    try {
      const response = await fetch(url, {
        method: endpoint.method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer YOUR_TOKEN_HERE'
        },
        body: body ? JSON.stringify(body) : null
      });

      const duration = Date.now() - startTime;
      const data = await response.json();
      const resultText = `状态码: ${response.status}\n\n${JSON.stringify(data, null, 2)}`;
      
      this.testPanel.showResult(resultText);

      // 保存到历史记录
      this.requestHistory.add({
        endpoint: endpoint,
        method: endpoint.method,
        path: endpoint.path,
        params: paramValues,
        body: body,
        response: data,
        status: response.status,
        duration: duration
      });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.testPanel.showResult('请求失败: ' + error.message, true);
      
      // 保存失败记录到历史
      this.requestHistory.add({
        endpoint: endpoint,
        method: endpoint.method,
        path: endpoint.path,
        params: paramValues,
        body: body,
        response: { error: error.message },
        status: 0,
        duration: duration
      });
    }
  }

  /**
   * 复制到剪贴板（使用三级降级方案）
   * @param {string} text - 文本内容
   * @param {string} description - 描述
   */
  async copyToClipboard(text, description = '内容') {
    await this.copyManager.copy(text, description);
  }

  /**
   * 初始化代码高亮
   */
  initCodeHighlight() {
    if (window.hljs) {
      window.hljs.highlightAll();
    }
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 点击遮罩关闭测试面板
    document.addEventListener('click', (e) => {
      if (e.target.id === 'api-test-overlay') {
        this.closeTestPanel();
      }
    });

    // ESC键关闭测试面板
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.testPanel.isOpen) {
        this.closeTestPanel();
      }
    });
  }

  /**
   * 处理全局动作
   * @param {string} action - 动作名称
   * @param {HTMLElement} context - 上下文元素
   * @param {Event} event - 事件
   */
  handleAction(action, context, event) {
    switch(action) {
      case 'refresh-api-doc':
        this.init();
        break;
      case 'select-endpoint':
        const endpointId = context.dataset.endpointId;
        if (endpointId) this.selectEndpointById(endpointId);
        break;
      case 'copy-to-clipboard':
        const text = context.dataset.text;
        const desc = context.dataset.description || '内容';
        if (text) this.copyToClipboard(text, desc);
        break;
      case 'show-export-dialog':
        this.exportManager.showExportDialog();
        break;
      case 'show-history-panel':
        this.requestHistory.showHistoryPanel();
        break;
      case 'open-test-panel':
        this.openTestPanel();
        break;
      case 'close-test-panel':
        this.closeTestPanel();
        break;
      case 'send-test-request':
        this.sendTestRequest();
        break;
      default:
        console.log('[APIDocPage] 未处理的动作:', action);
    }
  }
}
