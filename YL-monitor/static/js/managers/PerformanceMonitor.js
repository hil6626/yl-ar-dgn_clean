/**
 * 性能监控管理器
 * 监控应用性能指标，提供优化建议
 * 版本: v1.0.0
 */

export class PerformanceMonitor {
  constructor() {
    this.metrics = {
      navigation: {},
      paint: {},
      layout: {},
      memory: {},
      resources: []
    };
    this.observers = new Map();
    this.listeners = new Set();
    this.isMonitoring = false;
    this.reportInterval = null;
  }

  /**
   * 初始化性能监控
   */
  init() {
    this.setupObservers();
    this.collectNavigationTiming();
    this.startMemoryMonitoring();
    console.log('[PerformanceMonitor] 性能监控已启动');
  }

  /**
   * 设置性能观察器
   */
  setupObservers() {
    // 性能条目观察器
    if (window.PerformanceObserver) {
      // 观察长任务
      this.observeLongTasks();
      
      // 观察布局偏移
      this.observeLayoutShifts();
      
      // 观察资源加载
      this.observeResources();
      
      // 观察绘制
      this.observePaint();
    }
  }

  /**
   * 观察长任务
   */
  observeLongTasks() {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 50) {
            this.recordMetric('longTask', {
              duration: entry.duration,
              startTime: entry.startTime
            });
            
            if (entry.duration > 100) {
              console.warn('[PerformanceMonitor] 检测到长任务:', entry.duration.toFixed(2), 'ms');
            }
          }
        }
      });
      
      observer.observe({ entryTypes: ['longtask'] });
      this.observers.set('longtask', observer);
    } catch (e) {
      console.log('[PerformanceMonitor] 长任务观察不支持');
    }
  }

  /**
   * 观察布局偏移
   */
  observeLayoutShifts() {
    try {
      const observer = new PerformanceObserver((list) => {
        let clsValue = 0;
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        }
        
        this.metrics.layout.cls = clsValue;
        
        if (clsValue > 0.1) {
          console.warn('[PerformanceMonitor] 布局偏移过高:', clsValue.toFixed(3));
        }
      });
      
      observer.observe({ entryTypes: ['layout-shift'] });
      this.observers.set('layout-shift', observer);
    } catch (e) {
      console.log('[PerformanceMonitor] 布局偏移观察不支持');
    }
  }

  /**
   * 观察资源加载
   */
  observeResources() {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.initiatorType === 'xmlhttprequest' || 
              entry.initiatorType === 'fetch') {
            this.metrics.resources.push({
              name: entry.name,
              duration: entry.duration,
              size: entry.transferSize,
              type: entry.initiatorType
            });
          }
        }
      });
      
      observer.observe({ entryTypes: ['resource'] });
      this.observers.set('resource', observer);
    } catch (e) {
      console.log('[PerformanceMonitor] 资源观察不支持');
    }
  }

  /**
   * 观察绘制
   */
  observePaint() {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.paint.fcp = entry.startTime;
            console.log('[PerformanceMonitor] FCP:', entry.startTime.toFixed(2), 'ms');
          }
          if (entry.name === 'first-paint') {
            this.metrics.paint.fp = entry.startTime;
          }
        }
      });
      
      observer.observe({ entryTypes: ['paint'] });
      this.observers.set('paint', observer);
    } catch (e) {
      console.log('[PerformanceMonitor] 绘制观察不支持');
    }
  }

  /**
   * 收集导航时间
   */
  collectNavigationTiming() {
    if (!window.performance || !window.performance.timing) return;
    
    const timing = performance.timing;
    
    // 等待页面加载完成
    window.addEventListener('load', () => {
      setTimeout(() => {
        this.metrics.navigation = {
          dns: timing.domainLookupEnd - timing.domainLookupStart,
          tcp: timing.connectEnd - timing.connectStart,
          ttfb: timing.responseStart - timing.requestStart,
          download: timing.responseEnd - timing.responseStart,
          domParse: timing.domInteractive - timing.responseEnd,
          domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
          loadComplete: timing.loadEventEnd - timing.navigationStart
        };
        
        console.log('[PerformanceMonitor] 导航时间:', this.metrics.navigation);
      }, 0);
    });
  }

  /**
   * 启动内存监控
   */
  startMemoryMonitoring() {
    if (!performance.memory) return;
    
    setInterval(() => {
      const memory = performance.memory;
      this.metrics.memory = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
        usage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit * 100).toFixed(2)
      };
      
      // 内存使用超过80%警告
      if (this.metrics.memory.usage > 80) {
        console.warn('[PerformanceMonitor] 内存使用过高:', this.metrics.memory.usage + '%');
      }
    }, 30000); // 每30秒检查一次
  }

  /**
   * 记录性能指标
   * @param {string} type - 指标类型
   * @param {Object} data - 指标数据
   */
  recordMetric(type, data) {
    if (!this.metrics[type]) {
      this.metrics[type] = [];
    }
    
    this.metrics[type].push({
      ...data,
      timestamp: Date.now()
    });
    
    // 通知监听器
    this.notifyListeners(type, data);
  }

  /**
   * 测量函数执行时间
   * @param {string} name - 测量名称
   * @param {Function} fn - 要测量的函数
   * @returns {*}
   */
  measure(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    
    const duration = end - start;
    this.recordMetric('measurements', {
      name,
      duration,
      startTime: start
    });
    
    if (duration > 16) { // 超过一帧时间
      console.warn(`[PerformanceMonitor] ${name} 执行时间过长:`, duration.toFixed(2), 'ms');
    }
    
    return result;
  }

  /**
   * 异步测量
   * @param {string} name - 测量名称
   * @param {Function} fn - 异步函数
   * @returns {Promise}
   */
  async measureAsync(name, fn) {
    const start = performance.now();
    const result = await fn();
    const end = performance.now();
    
    const duration = end - start;
    this.recordMetric('measurements', {
      name,
      duration,
      startTime: start,
      async: true
    });
    
    return result;
  }

  /**
   * 获取性能报告
   * @returns {Object}
   */
  getReport() {
    return {
      timestamp: Date.now(),
      url: window.location.href,
      metrics: this.metrics,
      summary: this.generateSummary()
    };
  }

  /**
   * 生成摘要
   * @returns {Object}
   */
  generateSummary() {
    const summary = {
      status: 'good',
      issues: []
    };
    
    // 检查FCP
    if (this.metrics.paint.fcp > 3000) {
      summary.status = 'poor';
      summary.issues.push('首次内容绘制时间过长');
    }
    
    // 检查CLS
    if (this.metrics.layout.cls > 0.1) {
      summary.status = 'poor';
      summary.issues.push('布局偏移过高');
    }
    
    // 检查内存
    if (this.metrics.memory.usage > 80) {
      summary.status = 'warning';
      summary.issues.push('内存使用过高');
    }
    
    return summary;
  }

  /**
   * 显示性能面板
   */
  showPerformancePanel() {
    const report = this.getReport();
    
    const panel = document.createElement('div');
    panel.className = 'performance-panel';
    panel.innerHTML = `
      <div class="perf-panel-overlay">
        <div class="perf-panel-content">
          <div class="perf-panel-header">
            <h3>📊 性能监控</h3>
            <button class="btn btn-ghost" data-action="close">✕</button>
          </div>
          <div class="perf-panel-body">
            <div class="perf-section">
              <h4>导航时间</h4>
              <div class="perf-metrics">
                ${this.renderMetrics(this.metrics.navigation)}
              </div>
            </div>
            <div class="perf-section">
              <h4>绘制时间</h4>
              <div class="perf-metrics">
                ${this.renderMetrics(this.metrics.paint)}
              </div>
            </div>
            <div class="perf-section">
              <h4>内存使用</h4>
              <div class="perf-metrics">
                ${this.renderMetrics(this.metrics.memory)}
              </div>
            </div>
            <div class="perf-section">
              <h4>优化建议</h4>
              <ul class="perf-suggestions">
                ${report.summary.issues.map(issue => `<li>${issue}</li>`).join('') || '<li>暂无优化建议</li>'}
              </ul>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    
    panel.querySelector('[data-action="close"]').addEventListener('click', () => {
      panel.remove();
    });
    
    requestAnimationFrame(() => {
      panel.classList.add('active');
    });
  }

  /**
   * 渲染指标
   * @param {Object} metrics - 指标对象
   * @returns {string}
   */
  renderMetrics(metrics) {
    if (!metrics || Object.keys(metrics).length === 0) {
      return '<div class="perf-metric-empty">暂无数据</div>';
    }
    
    return Object.entries(metrics).map(([key, value]) => {
      let displayValue = value;
      if (typeof value === 'number') {
        displayValue = value > 1000 
          ? (value / 1000).toFixed(2) + 's'
          : value.toFixed(2) + 'ms';
      }
      
      return `
        <div class="perf-metric">
          <span class="metric-name">${key}</span>
          <span class="metric-value">${displayValue}</span>
        </div>
      `;
    }).join('');
  }

  /**
   * 添加监听器
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消监听函数
   */
  onMetric(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * 通知监听器
   * @param {string} type - 指标类型
   * @param {Object} data - 指标数据
   */
  notifyListeners(type, data) {
    this.listeners.forEach(callback => {
      try {
        callback(type, data);
      } catch (error) {
        console.error('[PerformanceMonitor] 监听器错误:', error);
      }
    });
  }

  /**
   * 导出报告
   * @returns {string} JSON字符串
   */
  exportReport() {
    return JSON.stringify(this.getReport(), null, 2);
  }

  /**
   * 销毁
   */
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    this.listeners.clear();
  }
}
