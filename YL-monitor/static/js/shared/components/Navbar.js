/**
 * 全局导航栏组件
 * 版本: v1.2.0 - 修复导航问题，使用传统链接跳转
 */

export class Navbar {
  constructor(options = {}) {
    this.options = {
      currentPage: 'dashboard',
      onNavigate: null,
      ...options
    };
    
    this.navItems = [
      { id: 'dashboard', label: '仪表盘', icon: '📊', href: '/dashboard' },
      { id: 'api-doc', label: 'API文档', icon: '📚', href: '/api-doc' },
      { id: 'dag', label: 'DAG流水线', icon: '🔄', href: '/dag' },
      { id: 'scripts', label: '脚本管理', icon: '📜', href: '/scripts' },
      { id: 'ar', label: 'AR监控', icon: '🎥', href: '/ar' },
      { id: 'alerts', label: '告警中心', icon: '🔔', href: '/alerts', badge: true }
    ];
  }

  /**
   * 渲染导航栏
   */
  render() {
    const mount = document.getElementById('navbar-mount');
    if (!mount) {
      console.warn('[Navbar] 找不到挂载点 #navbar-mount');
      return;
    }

    // 直接渲染为传统HTML链接，不使用JavaScript事件拦截
    mount.innerHTML = `
      <nav class="navbar">
        <a href="/" class="navbar-brand">
          <span class="brand-icon">🏠</span>
          <span class="brand-text">YL-Monitor</span>
        </a>
        
        <div class="navbar-nav">
          ${this.navItems.map(item => this.renderNavItem(item)).join('')}
        </div>
        
        <div class="navbar-actions">
          <span id="connection-status" class="status-dot online pulse" title="WebSocket: 已连接"></span>
          <span id="current-time" class="navbar-time"></span>
        </div>
      </nav>
    `;

    // 启动时间更新
    this.startClock();
    
    console.log('[Navbar] 导航栏已渲染（传统链接模式）');
  }

  /**
   * 渲染导航项 - 使用传统<a>标签，让浏览器自然处理跳转
   */
  renderNavItem(item) {
    const isActive = item.id === this.options.currentPage;
    const badge = item.badge ? `<span class="nav-badge" id="nav-badge-${item.id}">0</span>` : '';
    
    // 使用普通<a>标签，添加data-page属性用于状态更新
    return `
      <a href="${item.href}" class="nav-link ${isActive ? 'active' : ''}" data-page="${item.id}">
        <span class="nav-icon">${item.icon}</span>
        <span class="nav-label">${item.label}</span>
        ${badge}
      </a>
    `;
  }

  /**
   * 更新当前页面
   */
  setCurrentPage(pageId) {
    this.options.currentPage = pageId;
    
    // 更新激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
      if (link.dataset.page === pageId) {
        link.classList.add('active');
      }
    });
  }

  /**
   * 更新徽标
   */
  updateBadge(pageId, count) {
    const badge = document.getElementById(`nav-badge-${pageId}`);
    if (badge) {
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-flex';
      } else {
        badge.style.display = 'none';
      }
    }
  }

  /**
   * 更新时间
   */
  startClock() {
    const updateTime = () => {
      const timeEl = document.getElementById('current-time');
      if (timeEl) {
        timeEl.textContent = new Date().toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
    };
    
    updateTime();
    this.clockInterval = setInterval(updateTime, 1000);
  }

  /**
   * 更新连接状态
   */
  updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-status');
    if (!indicator) return;
    
    const statusMap = {
      'connected': { class: 'online', text: '🟢' },
      'disconnected': { class: 'offline', text: '🔴' },
      'reconnecting': { class: 'reconnecting', text: '🟡' }
    };
    
    const s = statusMap[status] || statusMap.disconnected;
    indicator.className = `status-dot ${s.class} pulse`;
    indicator.title = `WebSocket: ${status}`;
  }

  /**
   * 销毁
   */
  destroy() {
    const mount = document.getElementById('navbar-mount');
    if (mount) {
      mount.removeEventListener('click', this.clickHandler);
    }
    
    if (this.clockInterval) {
      clearInterval(this.clockInterval);
    }
  }
}

// 导出
export default Navbar;
