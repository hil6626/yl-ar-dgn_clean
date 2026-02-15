/**
 * 测试工具类
 * 提供单元测试和集成测试支持
 * 版本: v1.0.0
 */

export class TestRunner {
  constructor() {
    this.tests = [];
    this.results = [];
    this.beforeEachFn = null;
    this.afterEachFn = null;
  }

  /**
   * 注册测试
   * @param {string} name - 测试名称
   * @param {Function} fn - 测试函数
   */
  test(name, fn) {
    this.tests.push({ name, fn });
  }

  /**
   * 设置前置钩子
   * @param {Function} fn - 前置函数
   */
  beforeEach(fn) {
    this.beforeEachFn = fn;
  }

  /**
   * 设置后置钩子
   * @param {Function} fn - 后置函数
   */
  afterEach(fn) {
    this.afterEachFn = fn;
  }

  /**
   * 运行所有测试
   * @returns {Promise<Object>}
   */
  async run() {
    console.log('🧪 开始运行测试...\n');
    
    this.results = [];
    let passed = 0;
    let failed = 0;

    for (const test of this.tests) {
      try {
        // 前置
        if (this.beforeEachFn) {
          await this.beforeEachFn();
        }

        // 运行测试
        await test.fn();
        
        // 后置
        if (this.afterEachFn) {
          await this.afterEachFn();
        }

        this.results.push({ name: test.name, status: 'passed' });
        console.log(`✅ ${test.name}`);
        passed++;

      } catch (error) {
        this.results.push({ 
          name: test.name, 
          status: 'failed',
          error: error.message 
        });
        console.log(`❌ ${test.name}`);
        console.log(`   ${error.message}`);
        failed++;
      }
    }

    const summary = {
      total: this.tests.length,
      passed,
      failed,
      duration: Date.now()
    };

    this.printSummary(summary);
    return summary;
  }

  /**
   * 打印摘要
   * @param {Object} summary - 测试摘要
   */
  printSummary(summary) {
    console.log('\n' + '='.repeat(50));
    console.log('测试结果');
    console.log('='.repeat(50));
    console.log(`总计: ${summary.total}`);
    console.log(`通过: ${summary.passed} ✅`);
    console.log(`失败: ${summary.failed} ❌`);
    console.log(`成功率: ${(summary.passed / summary.total * 100).toFixed(1)}%`);
    console.log('='.repeat(50));
  }

  /**
   * 断言相等
   * @param {*} actual - 实际值
   * @param {*} expected - 期望值
   * @param {string} message - 消息
   */
  assertEqual(actual, expected, message = '') {
    if (actual !== expected) {
      throw new Error(
        message || `断言失败: 期望 ${expected}, 实际 ${actual}`
      );
    }
  }

  /**
   * 断言为真
   * @param {*} value - 值
   * @param {string} message - 消息
   */
  assertTrue(value, message = '') {
    if (!value) {
      throw new Error(message || '断言失败: 期望为真');
    }
  }

  /**
   * 断言为假
   * @param {*} value - 值
   * @param {string} message - 消息
   */
  assertFalse(value, message = '') {
    if (value) {
      throw new Error(message || '断言失败: 期望为假');
    }
  }

  /**
   * 断言抛出错误
   * @param {Function} fn - 函数
   * @param {string} message - 消息
   */
  assertThrows(fn, message = '') {
    let threw = false;
    try {
      fn();
    } catch (e) {
      threw = true;
    }
    
    if (!threw) {
      throw new Error(message || '断言失败: 期望抛出错误');
    }
  }

  /**
   * 断言包含
   * @param {*} haystack - 被搜索对象
   * @param {*} needle - 搜索对象
   * @param {string} message - 消息
   */
  assertContains(haystack, needle, message = '') {
    const contains = Array.isArray(haystack) 
      ? haystack.includes(needle)
      : haystack.indexOf(needle) !== -1;
      
    if (!contains) {
      throw new Error(message || `断言失败: 期望包含 ${needle}`);
    }
  }
}

/**
 * 模拟工具
 */
export class MockUtils {
  /**
   * 创建模拟函数
   * @returns {Function}
   */
  static fn() {
    const mockFn = (...args) => {
      mockFn.calls.push(args);
      return mockFn.returnValue;
    };
    
    mockFn.calls = [];
    mockFn.returnValue = undefined;
    
    mockFn.mockReturnValue = (value) => {
      mockFn.returnValue = value;
      return mockFn;
    };
    
    mockFn.mockImplementation = (impl) => {
      const original = mockFn;
      const newFn = (...args) => {
        newFn.calls.push(args);
        return impl(...args);
      };
      newFn.calls = [];
      return newFn;
    };
    
    return mockFn;
  }

  /**
   * 创建模拟定时器
   */
  static createMockTimers() {
    const timers = {
      timeouts: new Map(),
      intervals: new Map(),
      currentTime: 0,
      id: 0
    };

    const originalSetTimeout = window.setTimeout;
    const originalClearTimeout = window.clearTimeout;
    const originalSetInterval = window.setInterval;
    const originalClearInterval = window.clearInterval;

    window.setTimeout = (fn, delay) => {
      const id = ++timers.id;
      timers.timeouts.set(id, { fn, delay, time: timers.currentTime + delay });
      return id;
    };

    window.clearTimeout = (id) => {
      timers.timeouts.delete(id);
    };

    window.setInterval = (fn, delay) => {
      const id = ++timers.id;
      timers.intervals.set(id, { fn, delay, lastRun: timers.currentTime });
      return id;
    };

    window.clearInterval = (id) => {
      timers.intervals.delete(id);
    };

    timers.tick = (ms) => {
      timers.currentTime += ms;
      
      // 执行timeout
      timers.timeouts.forEach((timeout, id) => {
        if (timers.currentTime >= timeout.time) {
          timeout.fn();
          timers.timeouts.delete(id);
        }
      });
      
      // 执行interval
      timers.intervals.forEach((interval) => {
        while (timers.currentTime >= interval.lastRun + interval.delay) {
          interval.fn();
          interval.lastRun += interval.delay;
        }
      });
    };

    timers.restore = () => {
      window.setTimeout = originalSetTimeout;
      window.clearTimeout = originalClearTimeout;
      window.setInterval = originalSetInterval;
      window.clearInterval = originalClearInterval;
    };

    return timers;
  }

  /**
   * 创建模拟Fetch
   * @param {Object} responses - 响应配置
   */
  static createMockFetch(responses) {
    const originalFetch = window.fetch;
    
    window.fetch = async (url, options) => {
      const key = `${options?.method || 'GET'} ${url}`;
      const response = responses[key] || responses[url] || {
        status: 404,
        json: async () => ({ error: 'Not found' })
      };
      
      return {
        ok: response.status >= 200 && response.status < 300,
        status: response.status,
        json: async () => response.json,
        text: async () => response.text || JSON.stringify(response.json)
      };
    };

    return {
      restore: () => {
        window.fetch = originalFetch;
      }
    };
  }
}

/**
 * DOM测试工具
 */
export class DOMTestUtils {
  /**
   * 创建测试容器
   * @returns {HTMLElement}
   */
  static createContainer() {
    const container = document.createElement('div');
    container.id = 'test-container';
    document.body.appendChild(container);
    return container;
  }

  /**
   * 清理测试容器
   */
  static cleanup() {
    const container = document.getElementById('test-container');
    if (container) {
      container.remove();
    }
  }

  /**
   * 触发事件
   * @param {Element} element - 元素
   * @param {string} eventType - 事件类型
   * @param {Object} options - 事件选项
   */
  static triggerEvent(element, eventType, options = {}) {
    const event = new Event(eventType, {
      bubbles: true,
      cancelable: true,
      ...options
    });
    
    Object.assign(event, options);
    element.dispatchEvent(event);
  }

  /**
   * 等待元素出现
   * @param {string} selector - 选择器
   * @param {number} timeout - 超时时间
   * @returns {Promise<Element>}
   */
  static waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) {
        resolve(element);
        return;
      }

      const observer = new MutationObserver(() => {
        const element = document.querySelector(selector);
        if (element) {
          observer.disconnect();
          resolve(element);
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`等待元素 ${selector} 超时`));
      }, timeout);
    });
  }

  /**
   * 等待指定时间
   * @param {number} ms - 毫秒
   * @returns {Promise}
   */
  static sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
