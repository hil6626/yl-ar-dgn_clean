/**
 * 页面导航管理器
 * 实现页面间的无缝导航和状态同步
 * 版本: v1.0.0
 */

export class PageNavigator {
  constructor(options = {}) {
    this.options = {
      baseUrl: '/',
      animationDuration: 300,
      ...options
    };
    
    this.navigationHistory = [];
    this.currentPage = null;
    this.pageCache = new Map();
    this.listeners = new Map();
  }

  /**
   * 初始化导航管理器
   */
  init() {
    // 监听浏览器前进/后退
    window.addEventListener('popstate', (e) => this.handlePopState(e));
    
    // 拦截所有链接点击
    document.addEventListener('click', (e) => this.handleLinkClick(e));
    
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.syncPageState();
      }
    });
    
    console.log('[PageNavigator] 页面导航管理器已初始化');
  }

  /**
   * 处理链接点击
   * 注意：YL-Monitor是多页面应用(MPA)，不拦截链接，让浏览器自然跳转
   */
  handleLinkClick(e) {
    const link = e.target.closest('a[href]');
    if (!link) return;
    
    const href = link.getAttribute('href');
    
    // 只处理内部链接
    if (href.startsWith('http') && !href.includes(window.location.host)) {
      return; // 外部链接，正常跳转
    }
    
    // 多页面应用：不阻止默认行为，让浏览器自然跳转
    // 只记录导航历史，不拦截链接
    if (this.isInternalPage(href)) {
      // 记录导航但不阻止默认行为
      const pageName = this.parsePageName(href);
      this.currentPage = pageName;
      this.emit('page:navigate', { page: pageName, href: href });
    }
  }

  /**
   * 判断是否为内部页面
   */
  isInternalPage(href) {
    const internalPages = [
      '/dashboard',
      '/api-doc',
      '/dag',
      '/scripts',
      '/alerts',
      '/ar',
      '/'
    ];
    
    return internalPages.some(page => href === page || href.startsWith(page + '/'));
  }

  /**
   * 导航到指定页面
   * 注意：YL-Monitor是多页面应用(MPA)，使用传统页面跳转
   */
  navigateTo(href, options = {}) {
    // 解析页面名称
    const pageName = this.parsePageName(href);
    
    // 如果已经在当前页面，刷新即可
    if (pageName === this.currentPage && !options.force) {
      console.log(`[PageNavigator] 已经在页面 ${pageName}，跳过导航`);
      return;
    }

    console.log(`[PageNavigator] 导航到: ${href} (页面: ${pageName})`);

    // 多页面应用：使用传统页面跳转
    window.location.href = href;
  }

  /**
   * 解析页面名称
   */
  parsePageName(href) {
    const path = href.replace(window.location.origin, '').replace(/^\//, '');
    const pageMap = {
      '': 'dashboard',
      'dashboard': 'dashboard',
      'api-doc': 'api-doc',
      'dag': 'dag',
      'scripts': 'scripts',
      'alerts': 'alerts',
      'ar': 'ar'
    };
    
    return pageMap[path.split('/')[0]] || 'dashboard';
  }

  /**
   * 执行页面切换动画
   */
  performTransition(callback) {
    const body = document.body;
    
    // 添加过渡类
    body.classList.add('page-transitioning');
    body.style.opacity = '0';
    
    setTimeout(() => {
      callback();
      
      // 恢复显示
      requestAnimationFrame(() => {
        body.style.opacity = '1';
        setTimeout(() => {
          body.classList.remove('page-transitioning');
        }, this.options.animationDuration);
      });
    }, this.options.animationDuration);
  }

  /**
   * 加载页面
   */
  loadPage(pageName, href) {
    // 更新页面标题
    this.updatePageTitle(pageName);
    
    // 更新导航栏激活状态
    this.updateNavigationActiveState(pageName);
    
    // 同步全局状态
    this.syncGlobalState(pageName);
    
    // 触发页面加载完成事件
    this.emit('page:loaded', { page: pageName, href: href });
  }

  /**
   * 更新页面标题
   */
  updatePageTitle(pageName) {
    const titles = {
      'dashboard': '系统仪表盘 - YL-Monitor',
      'api-doc': 'API文档 - YL-Monitor',
      'dag': 'DAG流水线 - YL-Monitor',
      'scripts': '脚本管理 - YL-Monitor',
      'alerts': '告警中心 - YL-Monitor',
      'ar': 'AR监控 - YL-Monitor'
    };
    
    document.title = titles[pageName] || 'YL-Monitor';
  }

  /**
   * 更新导航栏激活状态
   */
  updateNavigationActiveState(pageName) {
    // 移除所有激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    
    // 添加当前页面激活状态
    const activeLink = document.querySelector(`.nav-link[data-page="${pageName}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }
  }

  /**
   * 同步全局状态
   */
  syncGlobalState(pageName) {
    // 更新HTML data属性
    document.documentElement.dataset.page = pageName;
    
    // 更新body class
    document.body.className = document.body.className.replace(/theme-\w+/g, '');
    document.body.classList.add(`theme-${pageName}`);
    
    // 触发状态同步事件
    this.emit('state:sync', { page: pageName });
  }

  /**
   * 同步页面状态（从其他页面返回时调用）
   */
  syncPageState() {
    const pageName = this.parsePageName(window.location.pathname);
    
    if (pageName !== this.currentPage) {
      console.log(`[PageNavigator] 检测到页面变化，同步状态: ${pageName}`);
      this.currentPage = pageName;
      this.loadPage(pageName, window.location.pathname);
    }
  }

  /**
   * 处理浏览器前进/后退
   * 注意：多页面应用，浏览器自然处理前进后退
   */
  handlePopState(e) {
    // 多页面应用：浏览器自然处理前进后退，不需要额外操作
    // 只同步当前页面状态
    this.syncPageState();
  }

  /**
   * 返回上一页
   * 注意：多页面应用，使用浏览器原生后退
   */
  back() {
    history.back();
  }

  /**
   * 获取导航历史
   */
  getHistory() {
    return [...this.navigationHistory];
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.pageCache.clear();
    console.log('[PageNavigator] 页面缓存已清除');
  }

  /**
   * 预加载页面
   */
  preloadPage(pageName) {
    if (this.pageCache.has(pageName)) {
      return;
    }

    // 可以在这里预加载页面资源
    console.log(`[PageNavigator] 预加载页面: ${pageName}`);
  }

  /**
   * 事件监听
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  /**
   * 移除事件监听
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[PageNavigator] 事件处理错误:`, error);
        }
      });
    }
    
    // 也触发自定义事件
    document.dispatchEvent(new CustomEvent(event, { detail: data }));
  }

  /**
   * 销毁
   */
  destroy() {
    this.listeners.clear();
    this.pageCache.clear();
    this.navigationHistory = [];
  }
}

// 创建全局实例
const pageNavigator = new PageNavigator();

// 导出
export { pageNavigator };
export default PageNavigator;
