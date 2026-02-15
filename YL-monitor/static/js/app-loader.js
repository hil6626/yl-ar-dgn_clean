/**
 * YL-Monitor 应用入口加载器 (简化版)
 * 功能：页面自动检测、动态模块加载
 * 版本：v2.0.0
 * 创建时间：2026-02-12
 */

import { uiFeedback } from './ui-feedback.js';

// 页面路由映射配置
const PAGE_MODULES = {
    'dashboard': {
        module: () => import('./pages/dashboard/index.js'),
        title: '系统仪表盘',
        theme: 'dashboard'
    },
    'api-doc': {
        module: () => import('./pages/api-doc/index.js'),
        title: 'API文档 - 部署验收控制塔',
        theme: 'api-doc'
    },
    'dag': {
        module: () => import('./pages/dag/index.js'),
        title: 'DAG流水线 - 流程编排核心',
        theme: 'dag'
    },
    'scripts': {
        module: () => import('./pages/scripts/index.js'),
        title: '脚本管理 - 自动化控制中心',
        theme: 'scripts'
    },
    'alerts': {
        module: () => import('./pages/alerts/index.js'),
        title: '告警中心 - 智能监控',
        theme: 'alerts'
    },
    'ar': {
        module: () => import('./pages/ar/index.js'),
        title: 'AR监控 - 增强现实节点',
        theme: 'ar'
    }
};

class AppLoader {
    constructor() {
        this.currentPage = null;
        this.pageInstance = null;
        this.isInitialized = false;
    }

    /**
     * 初始化应用
     */
    async init() {
        if (this.isInitialized) {
            console.warn('[AppLoader] 应用已初始化，跳过重复初始化');
            return;
        }

        console.log('[AppLoader] 开始初始化应用...');

        try {
            // 检测当前页面
            const pageInfo = this.detectCurrentPage();
            
            // 如果是静态页面（如 platform.html），只渲染导航栏
            if (!pageInfo) {
                console.log('[AppLoader] 静态页面模式，仅渲染导航栏');
                this.renderNavbar('platform');
                this.isInitialized = true;
                return;
            }
            
            console.log(`[AppLoader] 检测到页面: ${pageInfo.name}`);

            // 渲染导航栏
            this.renderNavbar(pageInfo.name);

            // 更新页面标题
            this.updatePageTitle(pageInfo.title);

            // 加载页面特定模块
            await this.loadPageModule(pageInfo.name);

            this.isInitialized = true;
            console.log('[AppLoader] 应用初始化完成 ✅');

        } catch (error) {
            console.error('[AppLoader] 应用初始化失败:', error);
            this.showInitError(error);
        }
    }

    /**
     * 检测当前页面
     */
    detectCurrentPage() {
        // 方法1: 从HTML data属性获取
        const htmlPage = document.documentElement.dataset.page;
        if (htmlPage && PAGE_MODULES[htmlPage]) {
            return {
                name: htmlPage,
                ...PAGE_MODULES[htmlPage]
            };
        }

        // 方法2: 从body class获取
        const bodyClass = document.body.className;
        for (const [name, config] of Object.entries(PAGE_MODULES)) {
            if (bodyClass.includes(`theme-${name}`) || bodyClass.includes(`page-${name}`)) {
                return { name, ...config };
            }
        }

        // 方法3: 从URL路径推断
        const path = window.location.pathname;
        const pathMap = {
            '/dashboard': 'dashboard',
            '/api-doc': 'api-doc',
            '/dag': 'dag',
            '/scripts': 'scripts',
            '/alerts': 'alerts',
            '/ar': 'ar'
        };

        for (const [route, name] of Object.entries(pathMap)) {
            if (path === route || path.startsWith(route + '/')) {
                if (PAGE_MODULES[name]) {
                    return { name, ...PAGE_MODULES[name] };
                }
            }
        }

        // 如果是根路径，platform.html 是静态页面
        if (path === '/' || path === '') {
            console.log('[AppLoader] 检测到平台首页 (静态页面)，跳过模块加载');
            return null;
        }

        // 默认返回dashboard
        console.warn('[AppLoader] 无法检测页面，使用默认页面: dashboard');
        return { name: 'dashboard', ...PAGE_MODULES['dashboard'] };
    }

    /**
     * 更新页面标题
     */
    updatePageTitle(title) {
        const titleEl = document.querySelector('title');
        if (titleEl) {
            titleEl.textContent = title;
        }
    }

    /**
     * 加载页面特定模块
     */
    async loadPageModule(pageName) {
        if (!pageName) {
            console.log('[AppLoader] 静态页面，跳过模块加载');
            return;
        }
        
        const pageConfig = PAGE_MODULES[pageName];
        if (!pageConfig) {
            throw new Error(`[AppLoader] 未知页面: ${pageName}`);
        }

        console.log(`[AppLoader] 加载页面模块: ${pageName}`);

        try {
            const module = await pageConfig.module();
            const PageClass = module.default || module[Object.keys(module)[0]];
            
            if (!PageClass) {
                throw new Error(`[AppLoader] 页面模块 ${pageName} 没有导出有效的页面类`);
            }

            // 传递UI反馈系统给页面
            this.pageInstance = new PageClass({
                uiComponents: uiFeedback
            });
            
            if (typeof this.pageInstance.init === 'function') {
                await this.pageInstance.init();
            }

            this.currentPage = pageName;
            console.log(`[AppLoader] 页面 ${pageName} 加载完成 ✅`);

        } catch (error) {
            console.error(`[AppLoader] 加载页面 ${pageName} 失败:`, error);
            throw error;
        }
    }

    /**
     * 渲染导航栏
     */
    renderNavbar(currentPage) {
        try {
            const navbarMount = document.getElementById('navbar-mount');
            if (!navbarMount) {
                console.warn('[AppLoader] 导航栏挂载点不存在');
                return;
            }

            const navItems = [
                { page: 'dashboard', href: '/dashboard', icon: '📊', label: '仪表盘' },
                { page: 'api-doc', href: '/api-doc', icon: '📚', label: 'API文档' },
                { page: 'dag', href: '/dag', icon: '🔄', label: 'DAG流水线' },
                { page: 'scripts', href: '/scripts', icon: '📜', label: '脚本管理' },
                { page: 'ar', href: '/ar', icon: '🎥', label: 'AR监控' },
                { page: 'alerts', href: '/alerts', icon: '🔔', label: '告警中心' }
            ];

            const navHTML = `
                <nav class="navbar">
                    <a href="/" class="navbar-brand">
                        <span>🏠</span>
                        <span>夜灵独家</span>
                    </a>
                    <div class="navbar-nav">
                        ${navItems.map(item => `
                            <a href="${item.href}" class="nav-link ${currentPage === item.page ? 'active' : ''}" data-page="${item.page}">
                                <span>${item.icon}</span>
                                <span>${item.label}</span>
                            </a>
                        `).join('')}
                    </div>
                    <div class="flex items-center gap-4">
                        <span id="connection-status" class="status-dot online pulse"></span>
                        <span id="current-time" class="text-sm text-secondary"></span>
                    </div>
                </nav>
            `;

            navbarMount.innerHTML = navHTML;
            console.log('[AppLoader] 导航栏已渲染');

            // 更新时间
            this.updateTime();
            setInterval(() => this.updateTime(), 1000);

        } catch (error) {
            console.error('[AppLoader] 导航栏渲染失败:', error);
        }
    }

    /**
     * 更新时间显示
     */
    updateTime() {
        const timeEl = document.getElementById('current-time');
        if (timeEl) {
            const now = new Date();
            timeEl.textContent = now.toLocaleTimeString('zh-CN');
        }
    }

    /**
     * 显示初始化错误
     */
    showInitError(error) {
        const mount = document.getElementById('main-content-mount') || 
                     document.getElementById('api-content-mount') ||
                     document.getElementById('dag-canvas-container') ||
                     document.body;
        
        if (mount) {
            mount.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: #dc3545;">
                    <h2>❌ 页面加载失败</h2>
                    <p>${error.message}</p>
                    <button onclick="window.location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        重新加载
                    </button>
                </div>
            `;
        }
    }
}

// 初始化应用
const appLoader = new AppLoader();

// DOM加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => appLoader.init());
} else {
    appLoader.init();
}

// 导出全局实例
window.appLoader = appLoader;
