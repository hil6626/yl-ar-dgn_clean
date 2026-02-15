/**
 * 懒加载管理器
 * 优化图片和组件的懒加载
 * 版本: v1.0.0
 */

export class LazyLoadManager {
  constructor(options = {}) {
    this.options = {
      rootMargin: '50px',
      threshold: 0.1,
      placeholder: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E',
      ...options
    };
    
    this.observer = null;
    this.elements = new Map();
    this.loadedElements = new Set();
  }

  /**
   * 初始化懒加载
   */
  init() {
    this.createObserver();
    this.scanElements();
    console.log('[LazyLoadManager] 懒加载管理器已启动');
  }

  /**
   * 创建IntersectionObserver
   */
  createObserver() {
    this.observer = new IntersectionObserver(
      (entries) => this.handleIntersection(entries),
      {
        root: null,
        rootMargin: this.options.rootMargin,
        threshold: this.options.threshold
      }
    );
  }

  /**
   * 处理交叉观察
   * @param {Array} entries - 观察条目
   */
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const element = entry.target;
        this.loadElement(element);
        this.observer.unobserve(element);
      }
    });
  }

  /**
   * 扫描页面元素
   */
  scanElements() {
    // 懒加载图片
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => this.observe(img, 'image'));

    // 懒加载背景图
    const bgElements = document.querySelectorAll('[data-bg-src]');
    bgElements.forEach(el => this.observe(el, 'background'));

    // 懒加载组件
    const components = document.querySelectorAll('[data-lazy-component]');
    components.forEach(el => this.observe(el, 'component'));

    // 懒加载iframe
    const iframes = document.querySelectorAll('iframe[data-src]');
    iframes.forEach(iframe => this.observe(iframe, 'iframe'));
  }

  /**
   * 观察元素
   * @param {Element} element - DOM元素
   * @param {string} type - 元素类型
   */
  observe(element, type) {
    if (this.loadedElements.has(element)) return;
    
    this.elements.set(element, { type, loaded: false });
    this.observer.observe(element);
    
    // 设置占位符
    this.setPlaceholder(element, type);
  }

  /**
   * 设置占位符
   * @param {Element} element - DOM元素
   * @param {string} type - 元素类型
   */
  setPlaceholder(element, type) {
    if (type === 'image') {
      element.src = this.options.placeholder;
      element.classList.add('lazy-image');
    } else if (type === 'background') {
      element.classList.add('lazy-background');
    } else if (type === 'component') {
      element.classList.add('lazy-component');
    }
  }

  /**
   * 加载元素
   * @param {Element} element - DOM元素
   */
  loadElement(element) {
    const info = this.elements.get(element);
    if (!info || info.loaded) return;

    switch (info.type) {
      case 'image':
        this.loadImage(element);
        break;
      case 'background':
        this.loadBackground(element);
        break;
      case 'component':
        this.loadComponent(element);
        break;
      case 'iframe':
        this.loadIframe(element);
        break;
    }

    info.loaded = true;
    this.loadedElements.add(element);
    this.elements.set(element, info);
  }

  /**
   * 加载图片
   * @param {HTMLImageElement} img - 图片元素
   */
  loadImage(img) {
    const src = img.dataset.src;
    const srcset = img.dataset.srcset;
    
    if (!src) return;

    // 创建新图片预加载
    const preloadImg = new Image();
    
    preloadImg.onload = () => {
      img.src = src;
      if (srcset) {
        img.srcset = srcset;
      }
      img.classList.add('loaded');
      img.classList.remove('lazy-image');
      
      // 触发自定义事件
      img.dispatchEvent(new CustomEvent('lazyloaded', { 
        detail: { src, element: img } 
      }));
    };
    
    preloadImg.onerror = () => {
      img.classList.add('error');
      console.error('[LazyLoadManager] 图片加载失败:', src);
    };
    
    preloadImg.src = src;
  }

  /**
   * 加载背景图
   * @param {Element} element - DOM元素
   */
  loadBackground(element) {
    const src = element.dataset.bgSrc;
    if (!src) return;

    const img = new Image();
    
    img.onload = () => {
      element.style.backgroundImage = `url(${src})`;
      element.classList.add('loaded');
      element.classList.remove('lazy-background');
      
      element.dispatchEvent(new CustomEvent('lazyloaded', {
        detail: { src, element }
      }));
    };
    
    img.onerror = () => {
      element.classList.add('error');
    };
    
    img.src = src;
  }

  /**
   * 加载组件
   * @param {Element} element - DOM元素
   */
  loadComponent(element) {
    const componentName = element.dataset.lazyComponent;
    const componentData = element.dataset.componentData;
    
    element.classList.add('loading');
    
    // 动态导入组件
    import(`/static/js/components/${componentName}.js`)
      .then(module => {
        const ComponentClass = module.default || module[componentName];
        
        if (ComponentClass) {
          const data = componentData ? JSON.parse(componentData) : {};
          const instance = new ComponentClass(element, data);
          
          if (instance.init) {
            instance.init();
          }
          
          element.classList.add('loaded');
          element.classList.remove('lazy-component', 'loading');
          
          element.dispatchEvent(new CustomEvent('componentloaded', {
            detail: { name: componentName, instance }
          }));
        }
      })
      .catch(error => {
        console.error('[LazyLoadManager] 组件加载失败:', componentName, error);
        element.classList.add('error');
      });
  }

  /**
   * 加载iframe
   * @param {HTMLIFrameElement} iframe - iframe元素
   */
  loadIframe(iframe) {
    const src = iframe.dataset.src;
    if (!src) return;

    iframe.src = src;
    iframe.classList.add('loaded');
    iframe.classList.remove('lazy-iframe');
    
    iframe.dispatchEvent(new CustomEvent('lazyloaded', {
      detail: { src, element: iframe }
    }));
  }

  /**
   * 手动触发加载
   * @param {Element} element - DOM元素
   */
  triggerLoad(element) {
    if (this.elements.has(element)) {
      this.loadElement(element);
      this.observer.unobserve(element);
    }
  }

  /**
   * 预加载指定元素
   * @param {string} selector - CSS选择器
   */
  preload(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => this.triggerLoad(el));
  }

  /**
   * 刷新扫描
   */
  refresh() {
    this.scanElements();
  }

  /**
   * 获取加载统计
   * @returns {Object}
   */
  getStats() {
    const total = this.elements.size;
    const loaded = this.loadedElements.size;
    
    return {
      total,
      loaded,
      pending: total - loaded,
      loadedPercent: total > 0 ? (loaded / total * 100).toFixed(2) : 0
    };
  }

  /**
   * 销毁
   */
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    
    this.elements.clear();
    this.loadedElements.clear();
  }
}
