/**
 * 虚拟滚动组件
 * 优化大数据列表渲染性能
 * 版本: v1.0.0
 */

export class VirtualScroller {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      itemHeight: 50,
      bufferSize: 5,
      overscan: 3,
      ...options
    };
    
    this.items = [];
    this.visibleItems = [];
    this.startIndex = 0;
    this.endIndex = 0;
    this.scrollTop = 0;
    this.containerHeight = 0;
    this.totalHeight = 0;
    
    this.init();
  }

  /**
   * 初始化虚拟滚动
   */
  init() {
    this.setupContainer();
    this.createScrollContainer();
    this.bindEvents();
    this.calculateDimensions();
  }

  /**
   * 设置容器
   */
  setupContainer() {
    this.container.style.overflow = 'auto';
    this.container.style.position = 'relative';
    this.containerHeight = this.container.clientHeight;
  }

  /**
   * 创建滚动容器
   */
  createScrollContainer() {
    // 内容容器（实际渲染的项）
    this.contentContainer = document.createElement('div');
    this.contentContainer.className = 'virtual-scroll-content';
    this.contentContainer.style.position = 'relative';
    
    // 占位容器（用于撑开滚动条）
    this.spacer = document.createElement('div');
    this.spacer.className = 'virtual-scroll-spacer';
    
    this.container.innerHTML = '';
    this.container.appendChild(this.spacer);
    this.container.appendChild(this.contentContainer);
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    let ticking = false;
    
    this.container.addEventListener('scroll', () => {
      this.scrollTop = this.container.scrollTop;
      
      if (!ticking) {
        requestAnimationFrame(() => {
          this.updateVisibleItems();
          ticking = false;
        });
        ticking = true;
      }
    });

    // 窗口大小变化
    window.addEventListener('resize', () => {
      this.calculateDimensions();
      this.updateVisibleItems();
    });
  }

  /**
   * 计算尺寸
   */
  calculateDimensions() {
    this.containerHeight = this.container.clientHeight;
    this.visibleCount = Math.ceil(this.containerHeight / this.options.itemHeight);
    this.totalHeight = this.items.length * this.options.itemHeight;
    
    // 更新占位高度
    this.spacer.style.height = `${this.totalHeight}px`;
  }

  /**
   * 设置数据
   * @param {Array} items - 数据项
   */
  setItems(items) {
    this.items = items;
    this.calculateDimensions();
    this.updateVisibleItems();
  }

  /**
   * 更新可见项
   */
  updateVisibleItems() {
    const { itemHeight, bufferSize, overscan } = this.options;
    
    // 计算可见范围
    const start = Math.floor(this.scrollTop / itemHeight);
    const visibleCount = Math.ceil(this.containerHeight / itemHeight);
    
    // 添加缓冲
    this.startIndex = Math.max(0, start - bufferSize);
    this.endIndex = Math.min(
      this.items.length,
      start + visibleCount + bufferSize + overscan
    );
    
    // 渲染可见项
    this.renderItems();
  }

  /**
   * 渲染项
   */
  renderItems() {
    const { itemHeight } = this.options;
    const visibleItems = this.items.slice(this.startIndex, this.endIndex);
    
    // 计算偏移
    const offsetY = this.startIndex * itemHeight;
    
    // 更新内容容器位置
    this.contentContainer.style.transform = `translateY(${offsetY}px)`;
    
    // 渲染项
    const html = visibleItems.map((item, index) => {
      const actualIndex = this.startIndex + index;
      return this.renderItem(item, actualIndex);
    }).join('');
    
    this.contentContainer.innerHTML = html;
    
    // 绑定事件
    this.bindItemEvents();
  }

  /**
   * 渲染单个项（子类可重写）
   * @param {*} item - 数据项
   * @param {number} index - 索引
   * @returns {string}
   */
  renderItem(item, index) {
    return `
      <div class="virtual-item" data-index="${index}" style="height: ${this.options.itemHeight}px">
        ${this.options.renderItem ? this.options.renderItem(item, index) : JSON.stringify(item)}
      </div>
    `;
  }

  /**
   * 绑定项事件
   */
  bindItemEvents() {
    this.contentContainer.querySelectorAll('.virtual-item').forEach(el => {
      el.addEventListener('click', (e) => {
        const index = parseInt(el.dataset.index);
        if (this.options.onItemClick) {
          this.options.onItemClick(this.items[index], index, e);
        }
      });
    });
  }

  /**
   * 滚动到指定项
   * @param {number} index - 索引
   * @param {string} behavior - 滚动行为
   */
  scrollToItem(index, behavior = 'smooth') {
    const { itemHeight } = this.options;
    const scrollTop = index * itemHeight;
    
    this.container.scrollTo({
      top: scrollTop,
      behavior
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
      top: this.totalHeight - this.containerHeight,
      behavior: 'smooth'
    });
  }

  /**
   * 添加项
   * @param {*} item - 数据项
   */
  addItem(item) {
    this.items.push(item);
    this.calculateDimensions();
    this.updateVisibleItems();
  }

  /**
   * 删除项
   * @param {number} index - 索引
   */
  removeItem(index) {
    this.items.splice(index, 1);
    this.calculateDimensions();
    this.updateVisibleItems();
  }

  /**
   * 更新项
   * @param {number} index - 索引
   * @param {*} item - 新数据
   */
  updateItem(index, item) {
    this.items[index] = item;
    if (index >= this.startIndex && index < this.endIndex) {
      this.updateVisibleItems();
    }
  }

  /**
   * 获取当前可见项
   * @returns {Array}
   */
  getVisibleItems() {
    return this.items.slice(this.startIndex, this.endIndex);
  }

  /**
   * 获取当前可见范围
   * @returns {Object}
   */
  getVisibleRange() {
    return {
      start: this.startIndex,
      end: this.endIndex,
      count: this.endIndex - this.startIndex
    };
  }

  /**
   * 销毁
   */
  destroy() {
    this.container.innerHTML = '';
    this.items = [];
    this.visibleItems = [];
  }
}
