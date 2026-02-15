/**
 * 页面视觉回归测试
 * 测试所有主要页面的渲染效果
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

// 页面配置
const pages = [
  { name: 'platform', path: '/', title: '平台首页' },
  { name: 'dashboard', path: '/dashboard', title: '仪表盘' },
  { name: 'scripts', path: '/scripts', title: '脚本管理' },
  { name: 'dag', path: '/dag', title: 'DAG流水线' },
  { name: 'ar', path: '/ar', title: 'AR监控' },
  { name: 'api-doc', path: '/api-doc', title: 'API文档' },
];

// 截图配置
const screenshotOptions = {
  fullPage: true,
  animations: 'disabled',
  mask: [
    // 遮罩动态内容（时间、状态指示器等）
    '[id="current-time"]',
    '[id="connection-status"]',
  ],
};

/**
 * 桌面端测试
 */
test.describe('桌面端视觉测试 (1920x1080)', () => {
  test.use({ viewport: { width: 1920, height: 1080 } });

  for (const page of pages) {
    test(`${page.title} 页面渲染`, async ({ page: pageObj }) => {
      await pageObj.goto(page.path);
      await pageObj.waitForLoadState('networkidle');
      
      // 等待页面特定元素加载
      await pageObj.waitForSelector('.main-content', { state: 'visible' });
      
      // 截图对比
      await expect(pageObj).toHaveScreenshot(
        `desktop-${page.name}.png`,
        screenshotOptions
      );
    });
  }
});

/**
 * 平板端测试
 */
test.describe('平板端视觉测试 (1024x768)', () => {
  test.use({ viewport: { width: 1024, height: 768 } });

  for (const page of pages) {
    test(`${page.title} 页面渲染`, async ({ page: pageObj }) => {
      await pageObj.goto(page.path);
      await pageObj.waitForLoadState('networkidle');
      await pageObj.waitForSelector('.main-content', { state: 'visible' });
      
      await expect(pageObj).toHaveScreenshot(
        `tablet-${page.name}.png`,
        screenshotOptions
      );
    });
  }
});

/**
 * 移动端测试
 */
test.describe('移动端视觉测试 (375x667)', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  for (const page of pages) {
    test(`${page.title} 页面渲染`, async ({ page: pageObj }) => {
      await pageObj.goto(page.path);
      await pageObj.waitForLoadState('networkidle');
      await pageObj.waitForSelector('.main-content', { state: 'visible' });
      
      await expect(pageObj).toHaveScreenshot(
        `mobile-${page.name}.png`,
        screenshotOptions
      );
    });
  }
});

/**
 * 深色模式测试
 */
test.describe('深色模式视觉测试', () => {
  test.use({ 
    viewport: { width: 1920, height: 1080 },
    colorScheme: 'dark'
  });

  for (const page of pages.slice(0, 3)) { // 只测试前3个页面
    test(`${page.title} 深色模式`, async ({ page: pageObj }) => {
      await pageObj.goto(page.path);
      await pageObj.waitForLoadState('networkidle');
      
      // 切换到深色模式
      await pageObj.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'dark');
      });
      
      await pageObj.waitForTimeout(500); // 等待主题切换动画
      
      await expect(pageObj).toHaveScreenshot(
        `dark-${page.name}.png`,
        screenshotOptions
      );
    });
  }
});

/**
 * 页面头部对齐测试
 */
test.describe('页面头部对齐测试', () => {
  test.use({ viewport: { width: 1920, height: 1080 } });

  test('所有页面头部对齐一致', async ({ page: pageObj }) => {
    const results = [];
    
    for (const page of pages) {
      await pageObj.goto(page.path);
      await pageObj.waitForSelector('.main-content', { state: 'visible' });
      
      // 获取头部元素的位置信息
      const headerInfo = await pageObj.evaluate(() => {
        const headers = document.querySelectorAll('[class$="-header"]');
        const info = [];
        headers.forEach(h => {
          const rect = h.getBoundingClientRect();
          info.push({
            class: h.className,
            top: rect.top,
            left: rect.left,
            height: rect.height,
            display: window.getComputedStyle(h).display,
            alignItems: window.getComputedStyle(h).alignItems
          });
        });
        return info;
      });
      
      results.push({
        page: page.name,
        headers: headerInfo
      });
    }
    
    // 验证所有页面头部使用flex布局
    for (const result of results) {
      for (const header of result.headers) {
        expect(header.display).toBe('flex');
        expect(header.alignItems).toBe('center');
      }
    }
  });
});

/**
 * 响应式布局测试
 */
test.describe('响应式布局断点测试', () => {
  const breakpoints = [
    { width: 480, name: 'mobile' },
    { width: 768, name: 'tablet' },
    { width: 1024, name: 'small-desktop' },
    { width: 1920, name: 'desktop' }
  ];

  for (const bp of breakpoints) {
    test(`断点 ${bp.width}px 布局正常`, async ({ page: pageObj }) => {
      await pageObj.setViewportSize({ width: bp.width, height: 1080 });
      await pageObj.goto('/dashboard');
      await pageObj.waitForLoadState('networkidle');
      
      // 检查页面容器padding
      const padding = await pageObj.evaluate(() => {
        const page = document.querySelector('.dashboard-page');
        if (!page) return null;
        const style = window.getComputedStyle(page);
        return style.padding;
      });
      
      expect(padding).toBeTruthy();
      
      // 截图记录
      await pageObj.screenshot({
        path: `test-results/responsive-${bp.name}.png`,
        fullPage: true
      });
    });
  }
});
