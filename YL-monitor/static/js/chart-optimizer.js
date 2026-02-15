/**
 * 图表性能优化器
 * 
 * 功能:
 * - 大数据量数据采样 (LTTB算法)
 * - Canvas渲染优化
 * - 图表懒加载
 * - 增量更新
 * - 性能监控
 * 
 * 作者: AI Assistant
 * 版本: 1.0.0
 */

/**
 * LTTB (Largest Triangle Three Buckets) 数据采样算法
 * 
 * 用于大数据量时保持图表形状的同时减少数据点
 */
class LTTBSampler {
    /**
     * 执行LTTB采样
     * 
     * @param {Array} data - 原始数据数组 [{x, y}, ...]
     * @param {number} threshold - 目标数据点数量
     * @returns {Array} 采样后的数据
     */
    static sample(data, threshold) {
        if (!data || data.length === 0) {
            return [];
        }
        
        if (data.length <= threshold) {
            return data;
        }
        
        const sampled = [];
        let sampledIndex = 0;
        
        // 始终保留第一个点
        sampled[sampledIndex++] = data[0];
        
        const bucketSize = (data.length - 2) / (threshold - 2);
        let a = 0; // 当前点索引
        
        for (let i = 0; i < threshold - 2; i++) {
            // 计算当前桶的范围
            const bucketStart = Math.floor((i + 0) * bucketSize) + 1;
            const bucketEnd = Math.floor((i + 1) * bucketSize) + 1;
            
            // 计算下一个桶的平均点
            const nextBucketStart = Math.floor((i + 1) * bucketSize) + 1;
            const nextBucketEnd = Math.floor((i + 2) * bucketSize) + 1;
            
            let avgX = 0;
            let avgY = 0;
            let avgCount = 0;
            
            for (let j = nextBucketStart; j < nextBucketEnd && j < data.length; j++) {
                avgX += data[j].x;
                avgY += data[j].y;
                avgCount++;
            }
            
            avgX /= avgCount;
            avgY /= avgCount;
            
            // 在当前桶中找到与三角形面积最大的点
            let maxArea = -1;
            let maxIdx = bucketStart;
            
            const pointA = data[a];
            
            for (let j = bucketStart; j < bucketEnd && j < data.length; j++) {
                const pointB = data[j];
                
                // 计算三角形面积
                const area = Math.abs(
                    (pointA.x - avgX) * (pointB.y - pointA.y) -
                    (pointA.x - pointB.x) * (avgY - pointA.y)
                );
                
                if (area > maxArea) {
                    maxArea = area;
                    maxIdx = j;
                }
            }
            
            sampled[sampledIndex++] = data[maxIdx];
            a = maxIdx;
        }
        
        // 始终保留最后一个点
        sampled[sampledIndex] = data[data.length - 1];
        
        return sampled;
    }
    
    /**
     * 自适应采样 - 根据数据量自动选择采样率
     * 
     * @param {Array} data - 原始数据
     * @param {Object} options - 配置
     * @returns {Object} 采样结果和数据信息
     */
    static adaptiveSample(data, options = {}) {
        const maxPoints = options.maxPoints || 1000;
        const minPoints = options.minPoints || 100;
        
        const originalLength = data.length;
        let sampledData = data;
        let samplingRatio = 1;
        
        if (originalLength > maxPoints) {
            sampledData = this.sample(data, maxPoints);
            samplingRatio = maxPoints / originalLength;
        } else if (originalLength < minPoints && options.interpolate) {
            // 数据点太少，可以插值(可选)
            sampledData = this.interpolate(data, minPoints);
            samplingRatio = minPoints / originalLength;
        }
        
        return {
            data: sampledData,
            originalLength,
            sampledLength: sampledData.length,
            samplingRatio,
            isSampled: originalLength !== sampledData.length
        };
    }
    
    /**
     * 线性插值
     * 
     * @param {Array} data - 原始数据
     * @param {number} targetCount - 目标数据点数量
     * @returns {Array} 插值后的数据
     */
    static interpolate(data, targetCount) {
        if (data.length >= targetCount) {
            return data;
        }
        
        const result = [];
        const step = (data.length - 1) / (targetCount - 1);
        
        for (let i = 0; i < targetCount; i++) {
            const idx = i * step;
            const lower = Math.floor(idx);
            const upper = Math.ceil(idx);
            const ratio = idx - lower;
            
            if (lower === upper) {
                result.push(data[lower]);
            } else {
                const point1 = data[lower];
                const point2 = data[upper];
                
                result.push({
                    x: point1.x + (point2.x - point1.x) * ratio,
                    y: point1.y + (point2.y - point1.y) * ratio,
                    interpolated: true
                });
            }
        }
        
        return result;
    }
}


/**
 * Canvas渲染优化器
 */
class CanvasOptimizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.dpr = window.devicePixelRatio || 1;
        
        this.setupHighDPI();
    }
    
    /**
     * 设置高DPI支持
     */
    setupHighDPI() {
        const rect = this.canvas.getBoundingClientRect();
        
        this.canvas.width = rect.width * this.dpr;
        this.canvas.height = rect.height * this.dpr;
        
        this.ctx.scale(this.dpr, this.dpr);
        
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;
    }
    
    /**
     * 批量绘制路径
     * 
     * @param {Array} points - 点数组
     * @param {Function} drawFn - 绘制函数
     */
    batchDraw(points, drawFn) {
        this.ctx.beginPath();
        
        for (let i = 0; i < points.length; i++) {
            drawFn(points[i], i, this.ctx);
        }
        
        this.ctx.stroke();
    }
    
    /**
     * 使用requestAnimationFrame优化绘制
     * 
     * @param {Function} drawFn - 绘制函数
     */
    optimizedDraw(drawFn) {
        requestAnimationFrame(() => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            drawFn(this.ctx);
        });
    }
    
    /**
     * 离屏渲染
     * 
     * @param {number} width - 宽度
     * @param {number} height - 高度
     * @returns {CanvasRenderingContext2D} 离屏context
     */
    createOffscreenContext(width, height) {
        const offscreen = document.createElement('canvas');
        offscreen.width = width * this.dpr;
        offscreen.height = height * this.dpr;
        
        const ctx = offscreen.getContext('2d');
        ctx.scale(this.dpr, this.dpr);
        
        return { canvas: offscreen, ctx };
    }
    
    /**
     * 双缓冲绘制
     * 
     * @param {Function} renderFn - 渲染函数
     */
    doubleBufferDraw(renderFn) {
        const rect = this.canvas.getBoundingClientRect();
        const { canvas: offscreen, ctx } = this.createOffscreenContext(
            rect.width, 
            rect.height
        );
        
        // 在离屏canvas上渲染
        renderFn(ctx);
        
        // 一次性复制到主canvas
        this.ctx.drawImage(offscreen, 0, 0);
    }
}


/**
 * 图表懒加载器
 */
class ChartLazyLoader {
    constructor(options) {
        this.charts = new Map();
        this.observer = null;
        this.options = {
            rootMargin: '50px',
            threshold: 0.1,
            ...options
        };
        
        this.init();
    }
    
    /**
     * 初始化Intersection Observer
     */
    init() {
        if (!('IntersectionObserver' in window)) {
            // 不支持则立即加载所有
            this.loadAll();
            return;
        }
        
        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            {
                rootMargin: this.options.rootMargin,
                threshold: this.options.threshold
            }
        );
    }
    
    /**
     * 注册图表
     * 
     * @param {string} id - 图表ID
     * @param {HTMLElement} element - 图表容器元素
     * @param {Function} loadFn - 加载函数
     */
    register(id, element, loadFn) {
        this.charts.set(id, {
            element,
            loadFn,
            loaded: false
        });
        
        this.observer.observe(element);
    }
    
    /**
     * 处理交叉观察事件
     * 
     * @param {Array} entries - 观察条目
     */
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = this.findChartId(entry.target);
                if (id) {
                    this.loadChart(id);
                }
            }
        });
    }
    
    /**
     * 查找图表ID
     * 
     * @param {HTMLElement} element - 元素
     * @returns {string|null} 图表ID
     */
    findChartId(element) {
        for (const [id, chart] of this.charts) {
            if (chart.element === element) {
                return id;
            }
        }
        return null;
    }
    
    /**
     * 加载图表
     * 
     * @param {string} id - 图表ID
     */
    loadChart(id) {
        const chart = this.charts.get(id);
        if (!chart || chart.loaded) {
            return;
        }
        
        chart.loaded = true;
        chart.loadFn();
        
        // 停止观察已加载的图表
        this.observer.unobserve(chart.element);
    }
    
    /**
     * 加载所有图表
     */
    loadAll() {
        for (const [id] of this.charts) {
            this.loadChart(id);
        }
    }
    
    /**
     * 销毁
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.charts.clear();
    }
}


/**
 * 图表增量更新器
 */
class ChartIncrementalUpdater {
    constructor(maxPoints = 1000) {
        this.maxPoints = maxPoints;
        this.dataBuffer = [];
    }
    
    /**
     * 添加新数据点
     * 
     * @param {Object} point - 数据点 {x, y}
     */
    addPoint(point) {
        this.dataBuffer.push(point);
        
        // 保持数据量在限制范围内
        if (this.dataBuffer.length > this.maxPoints) {
            this.dataBuffer.shift();
        }
    }
    
    /**
     * 批量添加数据点
     * 
     * @param {Array} points - 数据点数组
     */
    addPoints(points) {
        this.dataBuffer.push(...points);
        
        // 超出限制时进行采样
        if (this.dataBuffer.length > this.maxPoints) {
            this.dataBuffer = LTTBSampler.sample(
                this.dataBuffer, 
                this.maxPoints
            );
        }
    }
    
    /**
     * 获取当前数据
     * 
     * @returns {Array} 数据数组
     */
    getData() {
        return [...this.dataBuffer];
    }
    
    /**
     * 清空数据
     */
    clear() {
        this.dataBuffer = [];
    }
}


/**
 * 图表性能监控器
 */
class ChartPerformanceMonitor {
    constructor() {
        this.metrics = {
            renderTime: 0,
            dataPoints: 0,
            fps: 0,
            memoryUsage: 0
        };
        
        this.frameCount = 0;
        this.lastTime = performance.now();
    }
    
    /**
     * 开始测量
     */
    startMeasure() {
        this.measureStart = performance.now();
    }
    
    /**
     * 结束测量
     * 
     * @param {number} dataPoints - 数据点数量
     */
    endMeasure(dataPoints) {
        const endTime = performance.now();
        this.metrics.renderTime = endTime - this.measureStart;
        this.metrics.dataPoints = dataPoints;
        
        // 计算FPS
        this.frameCount++;
        const now = performance.now();
        if (now - this.lastTime >= 1000) {
            this.metrics.fps = this.frameCount;
            this.frameCount = 0;
            this.lastTime = now;
        }
        
        // 估算内存使用
        this.metrics.memoryUsage = this.estimateMemoryUsage(dataPoints);
    }
    
    /**
     * 估算内存使用
     * 
     * @param {number} dataPoints - 数据点数量
     * @returns {number} 估算的内存使用(字节)
     */
    estimateMemoryUsage(dataPoints) {
        // 假设每个数据点约占用 64 字节 (两个数字 + 对象开销)
        return dataPoints * 64;
    }
    
    /**
     * 获取性能报告
     * 
     * @returns {Object} 性能指标
     */
    getReport() {
        return {
            ...this.metrics,
            performance: this.metrics.renderTime < 16 ? 'excellent' : 
                        this.metrics.renderTime < 33 ? 'good' : 'poor'
        };
    }
}


/**
 * 综合图表优化器
 * 
 * 整合所有优化功能的统一接口
 */
class ChartOptimizer {
    constructor(options = {}) {
        this.options = {
            maxPoints: 1000,
            enableSampling: true,
            enableLazyLoad: true,
            enableIncremental: true,
            ...options
        };
        
        this.sampler = LTTBSampler;
        this.lazyLoader = this.options.enableLazyLoad ? new ChartLazyLoader() : null;
        this.updater = this.options.enableIncremental ? new ChartIncrementalUpdater(this.options.maxPoints) : null;
        this.monitor = new ChartPerformanceMonitor();
    }
    
    /**
     * 处理数据
     * 
     * @param {Array} rawData - 原始数据
     * @returns {Object} 处理后的数据和元信息
     */
    processData(rawData) {
        this.monitor.startMeasure();
        
        let processedData = rawData;
        let samplingInfo = null;
        
        // 数据采样
        if (this.options.enableSampling && rawData.length > this.options.maxPoints) {
            const result = this.sampler.adaptiveSample(rawData, {
                maxPoints: this.options.maxPoints
            });
            
            processedData = result.data;
            samplingInfo = {
                originalCount: result.originalLength,
                sampledCount: result.sampledLength,
                ratio: result.samplingRatio
            };
        }
        
        this.monitor.endMeasure(processedData.length);
        
        return {
            data: processedData,
            sampling: samplingInfo,
            performance: this.monitor.getReport()
        };
    }
    
    /**
     * 更新数据(增量)
     * 
     * @param {Array} newPoints - 新数据点
     */
    updateData(newPoints) {
        if (this.updater) {
            this.updater.addPoints(newPoints);
            return this.updater.getData();
        }
        return newPoints;
    }
    
    /**
     * 注册懒加载图表
     * 
     * @param {string} id - 图表ID
     * @param {HTMLElement} element - 容器元素
     * @param {Function} loadFn - 加载函数
     */
    registerLazyChart(id, element, loadFn) {
        if (this.lazyLoader) {
            this.lazyLoader.register(id, element, loadFn);
        } else {
            // 立即加载
            loadFn();
        }
    }
    
    /**
     * 创建优化的Canvas
     * 
     * @param {HTMLCanvasElement} canvas - Canvas元素
     * @returns {CanvasOptimizer} Canvas优化器
     */
    createOptimizedCanvas(canvas) {
        return new CanvasOptimizer(canvas);
    }
    
    /**
     * 获取性能报告
     * 
     * @returns {Object} 性能报告
     */
    getPerformanceReport() {
        return this.monitor.getReport();
    }
    
    /**
     * 销毁
     */
    destroy() {
        if (this.lazyLoader) {
            this.lazyLoader.destroy();
        }
    }
}


// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LTTBSampler,
        CanvasOptimizer,
        ChartLazyLoader,
        ChartIncrementalUpdater,
        ChartPerformanceMonitor,
        ChartOptimizer
    };
} else {
    window.LTTBSampler = LTTBSampler;
    window.CanvasOptimizer = CanvasOptimizer;
    window.ChartLazyLoader = ChartLazyLoader;
    window.ChartIncrementalUpdater = ChartIncrementalUpdater;
    window.ChartPerformanceMonitor = ChartPerformanceMonitor;
    window.ChartOptimizer = ChartOptimizer;
}
