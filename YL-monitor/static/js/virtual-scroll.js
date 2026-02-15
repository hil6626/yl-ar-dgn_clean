/**
 * 虚拟滚动组件
 * 
 * 功能:
 * - 大数据量列表虚拟滚动
 * - 动态高度支持
 * - 平滑滚动体验
 * - 内存优化
 * 
 * 作者: AI Assistant
 * 版本: 1.0.0
 */

class VirtualScroller {
    /**
     * 创建虚拟滚动实例
     * 
     * @param {Object} options - 配置选项
     * @param {HTMLElement} options.container - 容器元素
     * @param {number} options.itemHeight - 项目高度(固定高度时)
     * @param {number} options.bufferSize - 缓冲区大小(默认5)
     * @param {Function} options.renderItem - 渲染项目函数
     * @param {Function} options.getItemHeight - 获取项目高度函数(动态高度时)
     * @param {Function} options.onVisibleRangeChange - 可见范围变化回调
     */
    constructor(options) {
        this.container = options.container;
        this.itemHeight = options.itemHeight || 50;
        this.bufferSize = options.bufferSize || 5;
        this.renderItem = options.renderItem;
        this.getItemHeight = options.getItemHeight;
        this.onVisibleRangeChange = options.onVisibleRangeChange;
        
        this.items = [];
        this.totalHeight = 0;
        this.scrollTop = 0;
        this.containerHeight = 0;
        this.visibleStart = 0;
        this.visibleEnd = 0;
        
        this.isDynamicHeight = !!this.getItemHeight;
        this.itemHeights = []; // 动态高度缓存
        this.itemPositions = []; // 项目位置缓存
        
        this.scrollHandler = this.handleScroll.bind(this);
        this.resizeHandler = this.handleResize.bind(this);
        
        this.init();
    }
    
    /**
     * 初始化
     */
    init() {
        // 设置容器样式
        this.container.style.overflow = 'auto';
        this.container.style.position = 'relative';
        
        // 创建内容层
        this.contentLayer = document.createElement('div');
        this.contentLayer.style.position = 'relative';
        this.container.appendChild(this.contentLayer);
        
        // 创建可视层
        this.visibleLayer = document.createElement('div');
        this.visibleLayer.style.position = 'absolute';
        this.visibleLayer.style.top = '0';
        this.visibleLayer.style.left = '0';
        this.visibleLayer.style.right = '0';
        this.contentLayer.appendChild(this.visibleLayer);
        
        // 绑定事件
        this.container.addEventListener('scroll', this.scrollHandler, { passive: true });
        window.addEventListener('resize', this.resizeHandler);
        
        // 初始计算
        this.updateContainerHeight();
        this.updateVisibleRange();
    }
    
    /**
     * 设置数据
     * 
     * @param {Array} items - 数据项数组
     */
    setItems(items) {
        this.items = items || [];
        
        if (this.isDynamicHeight) {
            this.calculateDynamicHeights();
        } else {
            this.totalHeight = this.items.length * this.itemHeight;
        }
        
        this.contentLayer.style.height = `${this.totalHeight}px`;
        this.updateVisibleRange();
    }
    
    /**
     * 计算动态高度
     */
    calculateDynamicHeights() {
        this.itemHeights = [];
        this.itemPositions = [];
        this.totalHeight = 0;
        
        for (let i = 0; i < this.items.length; i++) {
            const height = this.getItemHeight(this.items[i], i);
            this.itemHeights[i] = height;
            this.itemPositions[i] = this.totalHeight;
            this.totalHeight += height;
        }
    }
    
    /**
     * 更新容器高度
     */
    updateContainerHeight() {
        this.containerHeight = this.container.clientHeight;
    }
    
    /**
     * 处理滚动事件
     */
    handleScroll() {
        this.scrollTop = this.container.scrollTop;
        this.updateVisibleRange();
    }
    
    /**
     * 处理窗口大小变化
     */
    handleResize() {
        this.updateContainerHeight();
        this.updateVisibleRange();
    }
    
    /**
     * 获取项目索引(基于滚动位置)
     * 
     * @param {number} position - 滚动位置
     * @returns {number} 项目索引
     */
    getItemIndexAtPosition(position) {
        if (!this.isDynamicHeight) {
            return Math.floor(position / this.itemHeight);
        }
        
        // 二分查找动态高度项目
        let left = 0;
        let right = this.itemPositions.length - 1;
        
        while (left <= right) {
            const mid = Math.floor((left + right) / 2);
            const midPosition = this.itemPositions[mid];
            
            if (midPosition === position) {
                return mid;
            } else if (midPosition < position) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        
        return Math.max(0, right);
    }
    
    /**
     * 更新可见范围
     */
    updateVisibleRange() {
        const start = this.getItemIndexAtPosition(this.scrollTop);
        const end = this.getItemIndexAtPosition(this.scrollTop + this.containerHeight);
        
        // 添加缓冲区
        const bufferedStart = Math.max(0, start - this.bufferSize);
        const bufferedEnd = Math.min(this.items.length - 1, end + this.bufferSize);
        
        // 检查是否有变化
        if (bufferedStart === this.visibleStart && bufferedEnd === this.visibleEnd) {
            return;
        }
        
        this.visibleStart = bufferedStart;
        this.visibleEnd = bufferedEnd;
        
        this.renderVisibleItems();
        
        // 触发回调
        if (this.onVisibleRangeChange) {
            this.onVisibleRangeChange({
                start: this.visibleStart,
                end: this.visibleEnd,
                visibleStart: start,
                visibleEnd: end
            });
        }
    }
    
    /**
     * 渲染可见项目
     */
    renderVisibleItems() {
        // 清空可视层
        this.visibleLayer.innerHTML = '';
        
        if (this.items.length === 0) {
            return;
        }
        
        // 计算偏移量
        const offsetY = this.isDynamicHeight 
            ? this.itemPositions[this.visibleStart] 
            : this.visibleStart * this.itemHeight;
        
        this.visibleLayer.style.transform = `translateY(${offsetY}px)`;
        
        // 渲染可见项目
        const fragment = document.createDocumentFragment();
        
        for (let i = this.visibleStart; i <= this.visibleEnd; i++) {
            if (i >= this.items.length) break;
            
            const item = this.items[i];
            const element = this.renderItem(item, i);
            
            if (element) {
                if (this.isDynamicHeight) {
                    element.style.height = `${this.itemHeights[i]}px`;
                } else {
                    element.style.height = `${this.itemHeight}px`;
                }
                
                fragment.appendChild(element);
            }
        }
        
        this.visibleLayer.appendChild(fragment);
    }
    
    /**
     * 滚动到指定项目
     * 
     * @param {number} index - 项目索引
     * @param {string} behavior - 滚动行为('auto' | 'smooth')
     */
    scrollToItem(index, behavior = 'auto') {
        if (index < 0 || index >= this.items.length) {
            return;
        }
        
        const position = this.isDynamicHeight 
            ? this.itemPositions[index] 
            : index * this.itemHeight;
        
        this.container.scrollTo({
            top: position,
            behavior: behavior
        });
    }
    
    /**
     * 滚动到顶部
     */
    scrollToTop() {
        this.container.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    /**
     * 滚动到底部
     */
    scrollToBottom() {
        this.container.scrollTo({ 
            top: this.totalHeight, 
            behavior: 'smooth' 
        });
    }
    
    /**
     * 获取当前可见范围
     * 
     * @returns {Object} 可见范围信息
     */
    getVisibleRange() {
        return {
            start: this.visibleStart,
            end: this.visibleEnd,
            count: this.visibleEnd - this.visibleStart + 1
        };
    }
    
    /**
     * 刷新(重新计算和渲染)
     */
    refresh() {
        if (this.isDynamicHeight) {
            this.calculateDynamicHeights();
        }
        this.updateContainerHeight();
        this.updateVisibleRange();
    }
    
    /**
     * 销毁
     */
    destroy() {
        this.container.removeEventListener('scroll', this.scrollHandler);
        window.removeEventListener('resize', this.resizeHandler);
        
        if (this.contentLayer && this.contentLayer.parentNode) {
            this.contentLayer.parentNode.removeChild(this.contentLayer);
        }
        
        this.items = [];
        this.itemHeights = [];
        this.itemPositions = [];
    }
    
    /**
     * 更新单个项目
     * 
     * @param {number} index - 项目索引
     * @param {Object} newItem - 新项目数据
     */
    updateItem(index, newItem) {
        if (index < 0 || index >= this.items.length) {
            return;
        }
        
        this.items[index] = newItem;
        
        // 如果在可见范围内，重新渲染
        if (index >= this.visibleStart && index <= this.visibleEnd) {
            this.renderVisibleItems();
        }
    }
    
    /**
     * 添加项目
     * 
     * @param {Object} item - 项目数据
     * @param {number} index - 插入位置(默认末尾)
     */
    addItem(item, index = -1) {
        if (index === -1) {
            index = this.items.length;
        }
        
        this.items.splice(index, 0, item);
        
        if (this.isDynamicHeight) {
            this.calculateDynamicHeights();
        } else {
            this.totalHeight = this.items.length * this.itemHeight;
        }
        
        this.contentLayer.style.height = `${this.totalHeight}px`;
        this.updateVisibleRange();
    }
    
    /**
     * 删除项目
     * 
     * @param {number} index - 项目索引
     */
    removeItem(index) {
        if (index < 0 || index >= this.items.length) {
            return;
        }
        
        this.items.splice(index, 1);
        
        if (this.isDynamicHeight) {
            this.calculateDynamicHeights();
        } else {
            this.totalHeight = this.items.length * this.itemHeight;
        }
        
        this.contentLayer.style.height = `${this.totalHeight}px`;
        this.updateVisibleRange();
    }
}


/**
 * 表格虚拟滚动器
 * 
 * 针对表格优化的虚拟滚动
 */
class TableVirtualScroller extends VirtualScroller {
    /**
     * 创建表格虚拟滚动实例
     * 
     * @param {Object} options - 配置选项
     * @param {HTMLElement} options.tableContainer - 表格容器
     * @param {HTMLElement} options.tbody - tbody元素
     * @param {Array} options.columns - 列定义
     */
    constructor(options) {
        super({
            container: options.tbody,
            itemHeight: options.rowHeight || 40,
            bufferSize: options.bufferSize || 5,
            renderItem: (item, index) => this.renderRow(item, index, options.columns),
            getItemHeight: options.getRowHeight
        });
        
        this.tableContainer = options.tableContainer;
        this.columns = options.columns;
        this.thead = options.thead;
        
        this.initTable();
    }
    
    /**
     * 初始化表格
     */
    initTable() {
        // 设置表格样式
        this.tableContainer.style.overflow = 'auto';
        
        // 固定表头
        if (this.thead) {
            this.thead.style.position = 'sticky';
            this.thead.style.top = '0';
            this.thead.style.zIndex = '10';
            this.thead.style.backgroundColor = '#fff';
        }
    }
    
    /**
     * 渲染行
     * 
     * @param {Object} item - 行数据
     * @param {number} index - 行索引
     * @param {Array} columns - 列定义
     * @returns {HTMLElement} tr元素
     */
    renderRow(item, index, columns) {
        const tr = document.createElement('tr');
        
        columns.forEach(column => {
            const td = document.createElement('td');
            const value = item[column.key];
            
            if (column.render) {
                td.innerHTML = column.render(value, item, index);
            } else {
                td.textContent = value !== undefined ? value : '';
            }
            
            if (column.width) {
                td.style.width = column.width;
                td.style.minWidth = column.width;
            }
            
            if (column.align) {
                td.style.textAlign = column.align;
            }
            
            tr.appendChild(td);
        });
        
        return tr;
    }
}


/**
 * 性能监控装饰器
 * 
 * 用于监控虚拟滚动性能
 */
class VirtualScrollPerformanceMonitor {
    constructor() {
        this.metrics = {
            renderCount: 0,
            totalRenderTime: 0,
            averageRenderTime: 0,
            maxRenderTime: 0,
            frameDrops: 0
        };
        
        this.targetFPS = 60;
        this.frameTime = 1000 / this.targetFPS;
    }
    
    /**
     * 记录渲染性能
     * 
     * @param {number} renderTime - 渲染时间(毫秒)
     */
    recordRender(renderTime) {
        this.metrics.renderCount++;
        this.metrics.totalRenderTime += renderTime;
        this.metrics.averageRenderTime = this.metrics.totalRenderTime / this.metrics.renderCount;
        
        if (renderTime > this.metrics.maxRenderTime) {
            this.metrics.maxRenderTime = renderTime;
        }
        
        if (renderTime > this.frameTime) {
            this.metrics.frameDrops++;
        }
    }
    
    /**
     * 获取性能报告
     * 
     * @returns {Object} 性能指标
     */
    getReport() {
        return {
            ...this.metrics,
            fps: this.metrics.averageRenderTime > 0 
                ? Math.round(1000 / this.metrics.averageRenderTime) 
                : 0,
            performance: this.metrics.averageRenderTime < this.frameTime ? 'good' : 'poor'
        };
    }
    
    /**
     * 重置
     */
    reset() {
        this.metrics = {
            renderCount: 0,
            totalRenderTime: 0,
            averageRenderTime: 0,
            maxRenderTime: 0,
            frameDrops: 0
        };
    }
}


// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VirtualScroller, TableVirtualScroller, VirtualScrollPerformanceMonitor };
} else {
    window.VirtualScroller = VirtualScroller;
    window.TableVirtualScroller = TableVirtualScroller;
    window.VirtualScrollPerformanceMonitor = VirtualScrollPerformanceMonitor;
}
