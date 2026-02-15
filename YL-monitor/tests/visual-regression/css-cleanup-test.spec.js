/**
 * CSS清理前后视觉回归测试
 * 确保CSS清理不会破坏UI
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// 测试页面列表
const PAGES = [
  { name: 'dashboard', url: '/dashboard' },
  { name: 'ar', url: '/ar' },
  { name: 'dag', url: '/dag' },
  { name: 'scripts', url: '/scripts' },
  { name: 'api-doc', url: '/api-doc' }
];

// 截图目录
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
const BASELINE_DIR = path.join(SCREENSHOT_DIR, 'baseline');
const CURRENT_DIR = path.join(SCREENSHOT_DIR, 'current');
const DIFF_DIR = path.join(SCREENSHOT_DIR, 'diff');

// 确保目录存在
[SCREENSHOT_DIR, BASELINE_DIR, CURRENT_DIR, DIFF_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

test.describe('CSS清理视觉回归测试', () => {
  
  test.beforeEach(async ({ page }) => {
    // 设置视口大小
    await page.setViewportSize({ width: 1280, height: 720 });
    
    // 等待页面加载
    await page.goto('http://0.0.0.0:5500');
    await page.waitForLoadState('networkidle');
  });

  test('生成基线截图', async ({ page }) => {
    for (const pageConfig of PAGES) {
      // 导航到页面
      await page.goto(`http://0.0.0.0:5500${pageConfig.url}`);
      await page.waitForLoadState('networkidle');
      
      // 等待动画完成
      await page.waitForTimeout(1000);
      
      // 截图
      const screenshotPath = path.join(BASELINE_DIR, `${pageConfig.name}.png`);
      await page.screenshot({ 
        path: screenshotPath,
        fullPage: true 
      });
      
      console.log(`✅ 基线截图已生成: ${pageConfig.name}.png`);
    }
  });

  test('对比CSS清理后的页面', async ({ page }) => {
    const results = [];
    
    for (const pageConfig of PAGES) {
      // 导航到页面
      await page.goto(`http://0.0.0.0:5500${pageConfig.url}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
      
      // 当前截图
      const currentPath = path.join(CURRENT_DIR, `${pageConfig.name}.png`);
      await page.screenshot({ 
        path: currentPath,
        fullPage: true 
      });
      
      // 对比
      const baselinePath = path.join(BASELINE_DIR, `${pageConfig.name}.png`);
      
      if (fs.existsSync(baselinePath)) {
        // 使用像素对比
        const diff = await compareScreenshots(baselinePath, currentPath, pageConfig.name);
        results.push({
          page: pageConfig.name,
          diff: diff,
          passed: diff < 0.1 // 差异小于10%视为通过
        });
      } else {
        console.warn(`⚠️  基线截图不存在: ${pageConfig.name}.png`);
        results.push({
          page: pageConfig.name,
          diff: null,
          passed: false
        });
      }
    }
    
    // 生成报告
    generateReport(results);
    
    // 断言
    const failedTests = results.filter(r => !r.passed);
    expect(failedTests.length).toBe(0);
  });

});

/**
 * 对比两张截图
 */
async function compareScreenshots(baselinePath, currentPath, name) {
  // 这里简化处理，实际应该使用像素级对比库如 pixelmatch
  // 返回差异百分比（0-1）
  
  const baseline = fs.statSync(baselinePath);
  const current = fs.statSync(currentPath);
  
  // 简单的文件大小对比（实际应该使用图像对比）
  const sizeDiff = Math.abs(baseline.size - current.size) / baseline.size;
  
  console.log(`📊 ${name}: 文件大小差异 ${(sizeDiff * 100).toFixed(2)}%`);
  
  return sizeDiff;
}

/**
 * 生成测试报告
 */
function generateReport(results) {
  const reportPath = path.join(SCREENSHOT_DIR, 'report.html');
  
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>CSS清理视觉回归测试报告</title>
  <style>
    body { font-family: system-ui, sans-serif; padding: 20px; }
    .pass { color: green; }
    .fail { color: red; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f5f5f5; }
    img { max-width: 300px; border: 1px solid #ddd; }
  </style>
</head>
<body>
  <h1>CSS清理视觉回归测试报告</h1>
  <p>生成时间: ${new Date().toLocaleString()}</p>
  
  <table>
    <tr>
      <th>页面</th>
      <th>状态</th>
      <th>差异</th>
      <th>基线</th>
      <th>当前</th>
    </tr>
    ${results.map(r => `
    <tr>
      <td>${r.page}</td>
      <td class="${r.passed ? 'pass' : 'fail'}">${r.passed ? '✅ 通过' : '❌ 失败'}</td>
      <td>${r.diff !== null ? (r.diff * 100).toFixed(2) + '%' : 'N/A'}</td>
      <td><img src="baseline/${r.page}.png" alt="基线"></td>
      <td><img src="current/${r.page}.png" alt="当前"></td>
    </tr>
    `).join('')}
  </table>
</body>
</html>
  `;
  
  fs.writeFileSync(reportPath, html);
  console.log(`📄 报告已生成: ${reportPath}`);
}
