// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * 视觉回归测试配置
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './',
  
  /* 运行测试文件 */
  testMatch: '**/*.spec.js',
  
  /* 完全并行运行测试 */
  fullyParallel: true,
  
  /* 失败时禁止重复测试 */
  forbidOnly: !!process.env.CI,
  
  /* 重试次数 */
  retries: process.env.CI ? 2 : 0,
  
  /* 并行工作进程数 */
  workers: process.env.CI ? 1 : undefined,
  
  /* 报告器配置 */
  reporter: [
    ['html', { outputFolder: './reports/html' }],
    ['json', { outputFile: './reports/results.json' }]
  ],
  
  /* 共享配置 */
  use: {
    /* 基础URL */
    baseURL: 'http://0.0.0.0:5500',
    
    /* 截图配置 */
    screenshot: 'only-on-failure',
    
    /* 跟踪配置 */
    trace: 'on-first-retry',
    
    /* 视口大小（默认桌面） */
    viewport: { width: 1920, height: 1080 },
  },

  /* 项目配置 */
  projects: [
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'chromium-tablet',
      use: { 
        ...devices['iPad Mini'],
        viewport: { width: 1024, height: 768 }
      },
    },
    {
      name: 'chromium-mobile',
      use: { 
        ...devices['iPhone 12'],
        viewport: { width: 375, height: 667 }
      },
    },
  ],

  /* 本地开发服务器配置 */
  webServer: {
    command: 'cd ../.. && python -m app.main',
    url: 'http://0.0.0.0:5500',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
