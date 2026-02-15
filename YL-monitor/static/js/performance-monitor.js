/**
 * 【文件功能】
 * 前端性能监控脚本，用于监控页面加载性能、资源加载、内存使用和FPS
 * 
 * 【作者信息】
 * 作者: AI Assistant
 * 创建时间: 2026-02-08
 * 最后更新: 2026-02-08
 * 
 * 【版本历史】
 * - v1.0.0 (2026-02-08): 初始版本，实现性能监控核心功能
 * 
 * 【依赖说明】
 * - 无外部依赖，纯原生JavaScript
 * 
 * 【使用示例】
 * ```javascript
 * // 初始化性能监控
 * const monitor = new PerformanceMonitor();
 * monitor.start();
 * 
 * // 获取性能报告
 * const report = monitor.getReport();
 * console.log(`首屏加载时间: ${report.fcp}ms`);
 * ```
 */

(function() {
    'use strict';

    /**
     * 【性能监控器类】
     * 提供全面的前端性能监控功能
     */
    class PerformanceMonitor {
        /**
         * 【构造函数】创建性能监控器实例
         * @param {Object} options - 配置选项
         * @param {boolean} options.enableLogging - 是否启用日志，默认true
         * @param {number} options.reportInterval - 报告间隔（毫秒），默认5000
         * @param {Function} options.onReport - 报告回调函数
         */
        constructor(options = {}) {
            this.options = {
                enableLogging: true,
                reportInterval: 5000,
                onReport: null,
                ...options
            };

            // 【性能数据存储】
            this.metrics = {
                // 【导航计时】
                navigation: {},
                // 【资源加载】
                resources: [],
                // 【核心Web指标】
                webVitals: {},
                // 【内存使用】
                memory: [],
                // 【FPS】
                fps: [],
                // 【长任务】
                longTasks: [],
                // 【错误】
                errors: []
            };

            // 【监控状态】
            this.isMonitoring = false;
            this.reportTimer = null;
            this.fpsTimer = null;
            this.memoryTimer = null;

            // 【观察者】
            this.observers = {};

            this._log('【性能监控器】初始化完成');
        }

        /**
         * 【开始监控】启动性能监控
         */
        start() {
            if (this.isMonitoring) {
                this._log('【性能监控器】已在运行中');
                return;
            }

            this.isMonitoring = true;
            this._log('【性能监控器】开始监控');

            // 【收集导航计时】
            this._collectNavigationTiming();

            // 【监控资源加载】
            this._monitorResourceLoading();

            // 【监控核心Web指标】
            this._monitorWebVitals();

            // 【监控内存】
            this._monitorMemory();

            // 【监控FPS】
            this._monitorFPS();

            // 【监控长任务】
            this._monitorLongTasks();

            // 【监控错误】
            this._monitorErrors();

            // 【启动定期报告】
            if (this.options.reportInterval > 0) {
                this.reportTimer = setInterval(() => {
                    this._generateReport();
                }, this.options.reportInterval);
            }

            // 【页面卸载时发送最终报告】
            window.addEventListener('beforeunload', () => {
                this._sendFinalReport();
            });
        }

        /**
         * 【停止监控】停止性能监控
         */
        stop() {
            if (!this.isMonitoring) {
                return;
            }

            this.isMonitoring = false;
            this._log('【性能监控器】停止监控');

            // 【清除定时器】
            if (this.reportTimer) {
                clearInterval(this.reportTimer);
                this.reportTimer = null;
            }

            if (this.fpsTimer) {
                cancelAnimationFrame(this.fpsTimer);
                this.fpsTimer = null;
            }

            if (this.memoryTimer) {
                clearInterval(this.memoryTimer);
                this.memoryTimer = null;
            }

            // 【断开观察者】
            Object.values(this.observers).forEach(observer => {
                if (observer && observer.disconnect) {
                    observer.disconnect();
                }
            });
            this.observers = {};
        }

        /**
         * 【收集导航计时】收集页面导航性能数据
         * @private
         */
        _collectNavigationTiming() {
            // 【使用Navigation Timing API】
            if (window.performance && window.performance.timing) {
                const timing = window.performance.timing;
                
                this.metrics.navigation = {
                    // 【DNS查询时间】
                    dns: timing.domainLookupEnd - timing.domainLookupStart,
                    // 【TCP连接时间】
                    tcp: timing.connectEnd - timing.connectStart,
                    // 【请求响应时间】
                    request: timing.responseEnd - timing.requestStart,
                    // 【DOM处理时间】
                    domProcessing: timing.domComplete - timing.domLoading,
                    // 【资源加载时间】
                    resourceLoading: timing.loadEventEnd - timing.domContentLoadedEventEnd,
                    // 【总加载时间】
                    totalLoad: timing.loadEventEnd - timing.navigationStart,
                    // 【首字节时间】
                    ttfb: timing.responseStart - timing.navigationStart,
                    // 【DOM准备时间】
                    domReady: timing.domContentLoadedEventEnd - timing.navigationStart
                };

                this._log('【导航计时】收集完成', this.metrics.navigation);
            }

            // 【使用Navigation Timing API v2】
            if (window.performance && window.performance.getEntriesByType) {
                const navEntries = window.performance.getEntriesByType('navigation');
                if (navEntries.length > 0) {
                    const nav = navEntries[0];
                    this.metrics.navigation.v2 = {
                        dns: nav.domainLookupEnd - nav.domainLookupStart,
                        tcp: nav.connectEnd - nav.connectStart,
                        request: nav.responseEnd - nav.requestStart,
                        domProcessing: nav.domComplete - nav.domLoading,
                        totalLoad: nav.loadEventEnd - nav.startTime,
                        ttfb: nav.responseStart - nav.startTime
                    };
                }
            }
        }

        /**
         * 【监控资源加载】监控页面资源加载性能
         * @private
         */
        _monitorResourceLoading() {
            if (!window.performance || !window.performance.getEntriesByType) {
                return;
            }

            // 【收集已有资源】
            this._collectResourceEntries();

            // 【监控新资源】
            if (window.PerformanceObserver) {
                this.observers.resource = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this._processResourceEntry(entry);
                    }
                });
                this.observers.resource.observe({ entryTypes: ['resource'] });
            }
        }

        /**
         * 【收集资源条目】
         * @private
         */
        _collectResourceEntries() {
            const entries = window.performance.getEntriesByType('resource');
            entries.forEach(entry => this._processResourceEntry(entry));
        }

        /**
         * 【处理资源条目】
         * @private
         * @param {PerformanceEntry} entry - 性能条目
         */
        _processResourceEntry(entry) {
            const resource = {
                name: entry.name,
                type: entry.initiatorType,
                duration: entry.duration,
                size: entry.transferSize,
                startTime: entry.startTime
            };

            // 【只记录慢资源（>500ms）】
            if (entry.duration > 500) {
                this.metrics.resources.push(resource);
                this._log('【慢资源】', resource);
            }
        }

        /**
         * 【监控核心Web指标】监控LCP、FID、CLS等核心指标
         * @private
         */
        _monitorWebVitals() {
            // 【监控LCP（最大内容绘制）】
            if (window.PerformanceObserver) {
                this.observers.lcp = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    
                    this.metrics.webVitals.lcp = {
                        value: lastEntry.startTime,
                        element: lastEntry.element ? lastEntry.element.tagName : null,
                        timestamp: Date.now()
                    };

                    this._log('【LCP】', this.metrics.webVitals.lcp);
                });
                this.observers.lcp.observe({ entryTypes: ['largest-contentful-paint'] });
            }

            // 【监控FID（首次输入延迟）】
            this._monitorFID();

            // 【监控CLS（累积布局偏移）】
            this._monitorCLS();

            // 【监控FCP（首次内容绘制）】
            this._monitorFCP();
        }

        /**
         * 【监控FID】首次输入延迟
         * @private
         */
        _monitorFID() {
            const measureFID = (entry) => {
                this.metrics.webVitals.fid = {
                    value: entry.processingStart - entry.startTime,
                    timestamp: Date.now()
                };
                this._log('【FID】', this.metrics.webVitals.fid);
            };

            // 【使用Event Timing API】
            if (window.PerformanceObserver) {
                this.observers.fid = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.duration > 0) {
                            measureFID(entry);
                        }
                    }
                });
                
                try {
                    this.observers.fid.observe({ 
                        entryTypes: ['first-input', 'event'] 
                    });
                } catch (e) {
                    // 【降级方案】
                    this._log('【FID】使用降级方案');
                }
            }

            // 【备用方案：使用原生事件】
            ['click', 'keydown', 'mousedown', 'pointerdown', 'touchstart'].forEach(type => {
                document.addEventListener(type, (event) => {
                    if (!this.metrics.webVitals.fid && event.timeStamp) {
                        this.metrics.webVitals.fid = {
                            value: performance.now() - event.timeStamp,
                            timestamp: Date.now(),
                            type: type
                        };
                    }
                }, { once: true, capture: true });
            });
        }

        /**
         * 【监控CLS】累积布局偏移
         * @private
         */
        _monitorCLS() {
            let clsValue = 0;
            let clsEntries = [];

            if (window.PerformanceObserver) {
                this.observers.cls = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                            clsEntries.push({
                                value: entry.value,
                                sources: entry.sources.map(s => ({
                                    node: s.node ? s.node.tagName : null,
                                    currentRect: s.currentRect
                                }))
                            });
                        }
                    }

                    this.metrics.webVitals.cls = {
                        value: clsValue,
                        entries: clsEntries.slice(-10), // 【只保留最近10条】
                        timestamp: Date.now()
                    };
                });

                try {
                    this.observers.cls.observe({ entryTypes: ['layout-shift'] });
                } catch (e) {
                    this._log('【CLS】浏览器不支持');
                }
            }
        }

        /**
         * 【监控FCP】首次内容绘制
         * @private
         */
        _monitorFCP() {
            if (window.PerformanceObserver) {
                this.observers.fcp = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.name === 'first-contentful-paint') {
                            this.metrics.webVitals.fcp = {
                                value: entry.startTime,
                                timestamp: Date.now()
                            };
                            this._log('【FCP】', this.metrics.webVitals.fcp);
                        }
                    }
                });

                this.observers.fcp.observe({ entryTypes: ['paint'] });
            } else if (window.performance && window.performance.timing) {
                // 【降级方案】
                window.addEventListener('load', () => {
                    setTimeout(() => {
                        const timing = window.performance.timing;
                        this.metrics.webVitals.fcp = {
                            value: timing.domContentLoadedEventEnd - timing.navigationStart,
                            timestamp: Date.now(),
                            method: 'fallback'
                        };
                    }, 0);
                });
            }
        }

        /**
         * 【监控内存】监控内存使用情况
         * @private
         */
        _monitorMemory() {
            if (!window.performance || !window.performance.memory) {
                this._log('【内存监控】浏览器不支持');
                return;
            }

            // 【定期收集内存数据】
            this.memoryTimer = setInterval(() => {
                const memory = window.performance.memory;
                
                const memoryData = {
                    timestamp: Date.now(),
                    usedJSHeapSize: memory.usedJSHeapSize,
                    totalJSHeapSize: memory.totalJSHeapSize,
                    jsHeapSizeLimit: memory.jsHeapSizeLimit,
                    // 【计算使用率】
                    usageRatio: memory.usedJSHeapSize / memory.jsHeapSizeLimit
                };

                this.metrics.memory.push(memoryData);

                // 【只保留最近100条记录】
                if (this.metrics.memory.length > 100) {
                    this.metrics.memory.shift();
                }

                // 【内存告警】
                if (memoryData.usageRatio > 0.8) {
                    this._log('【内存告警】使用率超过80%', memoryData);
                }
            }, 5000); // 【每5秒收集一次】
        }

        /**
         * 【监控FPS】监控页面帧率
         * @private
         */
        _monitorFPS() {
            let lastTime = performance.now();
            let frames = 0;
            let fps = 0;

            const calculateFPS = (currentTime) => {
                frames++;
                
                if (currentTime >= lastTime + 1000) {
                    fps = Math.round((frames * 1000) / (currentTime - lastTime));
                    
                    // 【记录FPS】
                    this.metrics.fps.push({
                        timestamp: Date.now(),
                        value: fps
                    });

                    // 【只保留最近60条记录（1分钟）】
                    if (this.metrics.fps.length > 60) {
                        this.metrics.fps.shift();
                    }

                    // 【FPS告警】
                    if (fps < 30) {
                        this._log('【FPS告警】帧率低于30', { fps });
                    }

                    frames = 0;
                    lastTime = currentTime;
                }

                if (this.isMonitoring) {
                    this.fpsTimer = requestAnimationFrame(calculateFPS);
                }
            };

            this.fpsTimer = requestAnimationFrame(calculateFPS);
        }

        /**
         * 【监控长任务】监控长任务（>50ms）
         * @private
         */
        _monitorLongTasks() {
            if (!window.PerformanceObserver) {
                return;
            }

            try {
                this.observers.longTask = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        const longTask = {
                            timestamp: Date.now(),
                            duration: entry.duration,
                            startTime: entry.startTime
                        };

                        this.metrics.longTasks.push(longTask);
                        this._log('【长任务】', longTask);

                        // 【只保留最近20条】
                        if (this.metrics.longTasks.length > 20) {
                            this.metrics.longTasks.shift();
                        }
                    }
                });

                this.observers.longTask.observe({ entryTypes: ['longtask'] });
            } catch (e) {
                this._log('【长任务监控】浏览器不支持');
            }
        }

        /**
         * 【监控错误】监控JavaScript错误
         * @private
         */
        _monitorErrors() {
            // 【捕获JS错误】
            window.addEventListener('error', (event) => {
                this.metrics.errors.push({
                    timestamp: Date.now(),
                    type: 'javascript',
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno
                });
            });

            // 【捕获Promise错误】
            window.addEventListener('unhandledrejection', (event) => {
                this.metrics.errors.push({
                    timestamp: Date.now(),
                    type: 'promise',
                    message: event.reason ? event.reason.toString() : 'Unknown'
                });
            });
        }

        /**
         * 【生成报告】生成性能报告
         * @private
         */
        _generateReport() {
            const report = this.getReport();
            
            if (this.options.onReport && typeof this.options.onReport === 'function') {
                this.options.onReport(report);
            }

            // 【发送到服务器】
            this._sendToServer(report);
        }

        /**
         * 【获取报告】获取当前性能报告
         * @returns {Object} 性能报告
         */
        getReport() {
            const now = Date.now();
            
            // 【计算平均FPS】
            const avgFps = this.metrics.fps.length > 0
                ? Math.round(this.metrics.fps.reduce((a, b) => a + b.value, 0) / this.metrics.fps.length)
                : 0;

            // 【获取最新内存数据】
            const latestMemory = this.metrics.memory.length > 0
                ? this.metrics.memory[this.metrics.memory.length - 1]
                : null;

            return {
                timestamp: now,
                // 【核心Web指标】
                webVitals: {
                    fcp: this.metrics.webVitals.fcp ? Math.round(this.metrics.webVitals.fcp.value) : null,
                    lcp: this.metrics.webVitals.lcp ? Math.round(this.metrics.webVitals.lcp.value) : null,
                    fid: this.metrics.webVitals.fid ? Math.round(this.metrics.webVitals.fid.value) : null,
                    cls: this.metrics.webVitals.cls ? this.metrics.webVitals.cls.value.toFixed(4) : null
                },
                // 【导航计时】
                navigation: this.metrics.navigation,
                // 【资源统计】
                resources: {
                    slowCount: this.metrics.resources.length,
                    slowList: this.metrics.resources.slice(-5) // 【最近5个慢资源】
                },
                // 【性能指标】
                performance: {
                    avgFps: avgFps,
                    longTasksCount: this.metrics.longTasks.length,
                    errorsCount: this.metrics.errors.length
                },
                // 【内存】
                memory: latestMemory ? {
                    usedMB: Math.round(latestMemory.usedJSHeapSize / 1024 / 1024),
                    totalMB: Math.round(latestMemory.totalJSHeapSize / 1024 / 1024),
                    limitMB: Math.round(latestMemory.jsHeapSizeLimit / 1024 / 1024),
                    usagePercent: Math.round(latestMemory.usageRatio * 100)
                } : null
            };
        }

        /**
         * 【发送到服务器】发送性能数据到服务器
         * @private
         * @param {Object} report - 性能报告
         */
        _sendToServer(report) {
            // 【使用sendBeacon API】
            if (navigator.sendBeacon) {
                const data = JSON.stringify({
                    type: 'performance',
                    data: report
                });
                navigator.sendBeacon('/api/metrics/performance', new Blob([data], {
                    type: 'application/json'
                }));
            }
        }

        /**
         * 【发送最终报告】页面卸载时发送最终报告
         * @private
         */
        _sendFinalReport() {
            const report = this.getReport();
            this._sendToServer(report);
        }

        /**
         * 【日志输出】
         * @private
         * @param {...any} args - 日志参数
         */
        _log(...args) {
            if (this.options.enableLogging) {
                console.log('[PerformanceMonitor]', ...args);
            }
        }
    }

    // 【导出到全局】
    window.PerformanceMonitor = PerformanceMonitor;

    // 【自动初始化】
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.perfMonitor = new PerformanceMonitor();
            window.perfMonitor.start();
        });
    } else {
        window.perfMonitor = new PerformanceMonitor();
        window.perfMonitor.start();
    }

})();
