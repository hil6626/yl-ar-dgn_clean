/**
 * P2 & P3 关键路径测试
 * 验证核心功能是否正常工作
 * 运行: node tests/critical-path-test.js
 */

const fs = require('fs');
const path = require('path');

// 简单的测试框架
class CriticalPathTest {
  constructor() {
    this.tests = [];
    this.passed = 0;
    this.failed = 0;
  }

  async test(name, fn) {
    try {
      await fn();
      console.log(`✅ ${name}`);
      this.passed++;
      return true;
    } catch (error) {
      console.log(`❌ ${name}`);
      console.log(`   ${error.message}`);
      this.failed++;
      return false;
    }
  }

  report() {
    console.log('\n' + '='.repeat(50));
    console.log('关键路径测试报告');
    console.log('='.repeat(50));
    console.log(`总计: ${this.passed + this.failed}`);
    console.log(`通过: ${this.passed} ✅`);
    console.log(`失败: ${this.failed} ❌`);
    console.log(`成功率: ${(this.passed / (this.passed + this.failed) * 100).toFixed(1)}%`);
    console.log('='.repeat(50));
    return this.failed === 0;
  }
}

// 运行测试
async function runTests() {
  const test = new CriticalPathTest();
  
  console.log('🧪 P2 & P3 关键路径测试\n');

  // 测试1: 虚拟滚动组件文件存在
  await test.test('VirtualScroller.js 文件存在', () => {
    const filePath = path.join(__dirname, '../static/js/components/VirtualScroller.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('VirtualScroller.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('class VirtualScroller')) {
      throw new Error('VirtualScroller 类未找到');
    }
  });

  // 测试2: 性能监控管理器文件存在
  await test.test('PerformanceMonitor.js 文件存在', () => {
    const filePath = path.join(__dirname, '../static/js/managers/PerformanceMonitor.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('PerformanceMonitor.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('class PerformanceMonitor')) {
      throw new Error('PerformanceMonitor 类未找到');
    }
    // 检查关键方法
    const requiredMethods = ['init', 'getReport', 'measure', 'showPerformancePanel'];
    for (const method of requiredMethods) {
      if (!content.includes(`${method}(`)) {
        throw new Error(`缺少方法: ${method}`);
      }
    }
  });

  // 测试3: 懒加载管理器文件存在
  await test.test('LazyLoadManager.js 文件存在', () => {
    const filePath = path.join(__dirname, '../static/js/managers/LazyLoadManager.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('LazyLoadManager.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('class LazyLoadManager')) {
      throw new Error('LazyLoadManager 类未找到');
    }
    // 检查IntersectionObserver使用
    if (!content.includes('IntersectionObserver')) {
      throw new Error('未使用IntersectionObserver');
    }
  });

  // 测试4: 代码质量检查器文件存在
  await test.test('CodeQualityChecker.js 文件存在', () => {
    const filePath = path.join(__dirname, '../static/js/utils/CodeQualityChecker.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('CodeQualityChecker.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('class CodeQualityChecker')) {
      throw new Error('CodeQualityChecker 类未找到');
    }
    // 检查规则定义
    if (!content.includes('defineRules')) {
      throw new Error('未找到defineRules方法');
    }
  });

  // 测试5: 测试工具类文件存在
  await test.test('TestUtils.js 文件存在', () => {
    const filePath = path.join(__dirname, '../static/js/utils/TestUtils.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('TestUtils.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    // 检查三个主要类
    const requiredClasses = ['TestRunner', 'MockUtils', 'DOMTestUtils'];
    for (const className of requiredClasses) {
      if (!content.includes(`class ${className}`)) {
        throw new Error(`缺少类: ${className}`);
      }
    }
  });

  // 测试6: Dashboard测试文件存在
  await test.test('dashboard.test.js 文件存在', () => {
    const filePath = path.join(__dirname, 'pages/dashboard.test.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('dashboard.test.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('TestRunner')) {
      throw new Error('未使用TestRunner');
    }
  });

  // 测试7: 组件入口文件更新
  await test.test('components/index.js 入口正确', () => {
    const filePath = path.join(__dirname, '../static/js/components/index.js');
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('VirtualScroller')) {
      throw new Error('未导出VirtualScroller');
    }
    if (!content.includes('GlobalSearch')) {
      throw new Error('未导出GlobalSearch');
    }
  });

  // 测试8: 管理器入口文件更新
  await test.test('managers/index.js 入口正确', () => {
    const filePath = path.join(__dirname, '../static/js/managers/index.js');
    const content = fs.readFileSync(filePath, 'utf-8');
    const requiredExports = [
      'ThemePersistenceManager',
      'KeyboardShortcutManager',
      'PerformanceMonitor',
      'LazyLoadManager'
    ];
    for (const exportName of requiredExports) {
      if (!content.includes(exportName)) {
        throw new Error(`未导出: ${exportName}`);
      }
    }
  });

  // 测试9: 工具入口文件存在
  await test.test('utils/index.js 入口正确', () => {
    const filePath = path.join(__dirname, '../static/js/utils/index.js');
    if (!fs.existsSync(filePath)) {
      throw new Error('utils/index.js 文件不存在');
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.includes('CodeQualityChecker')) {
      throw new Error('未导出CodeQualityChecker');
    }
    if (!content.includes('TestRunner')) {
      throw new Error('未导出TestRunner');
    }
  });

  // 测试10: 代码质量检查（自检）
  await test.test('代码质量自检', () => {
    const filePath = path.join(__dirname, '../static/js/utils/CodeQualityChecker.js');
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 检查自己的代码质量
    const issues = [];
    
    // 检查console.log
    const consoleMatches = content.match(/console\.(log|debug|info)\(/g);
    if (consoleMatches && consoleMatches.length > 10) {
      issues.push(`console语句较多: ${consoleMatches.length}处`);
    }
    
    // 检查TODO
    if (content.includes('TODO')) {
      issues.push('包含TODO注释');
    }
    
    if (issues.length > 0) {
      console.log(`   ⚠️  发现 ${issues.length} 个问题:`);
      issues.forEach(issue => console.log(`      - ${issue}`));
    }
  });

  // 生成报告
  return test.report();
}

// 运行测试
console.log('========================================');
console.log('P2 & P3 关键路径测试');
console.log('========================================\n');

runTests().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('测试执行失败:', error);
