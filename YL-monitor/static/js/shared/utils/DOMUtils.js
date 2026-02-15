/**
 * DOM工具函数库
 * 共享模块 - 所有页面可复用
 * 版本: v1.0.0
 */

/**
 * 安全地获取DOM元素
 * @param {string} selector - CSS选择器
 * @param {HTMLElement} context - 上下文元素（默认为document）
 * @returns {HTMLElement|null}
 */
export function $(selector, context = document) {
  return context.querySelector(selector);
}

/**
 * 安全地获取所有匹配的DOM元素
 * @param {string} selector - CSS选择器
 * @param {HTMLElement} context - 上下文元素（默认为document）
 * @returns {NodeList}
 */
export function $$(selector, context = document) {
  return context.querySelectorAll(selector);
}

/**
 * 创建带属性的DOM元素
 * @param {string} tag - 标签名
 * @param {Object} attrs - 属性对象
 * @param {string|HTMLElement} content - 内容
 * @returns {HTMLElement}
 */
export function createElement(tag, attrs = {}, content = '') {
  const el = document.createElement(tag);
  
  Object.entries(attrs).forEach(([key, value]) => {
    if (key === 'className') {
      el.className = value;
    } else if (key === 'dataset') {
      Object.entries(value).forEach(([dataKey, dataValue]) => {
        el.dataset[dataKey] = dataValue;
      });
    } else if (key.startsWith('on') && typeof value === 'function') {
      el.addEventListener(key.slice(2).toLowerCase(), value);
    } else {
      el.setAttribute(key, value);
    }
  });
  
  if (typeof content === 'string') {
    el.innerHTML = content;
  } else if (content instanceof HTMLElement) {
    el.appendChild(content);
  }
  
  return el;
}

/**
 * 添加/移除/切换类名
 * @param {HTMLElement} el - 目标元素
 * @param {string} className - 类名
 * @param {boolean} force - 强制添加或移除
 */
export function toggleClass(el, className, force) {
  if (!el) return;
  el.classList.toggle(className, force);
}

/**
 * 添加类名
 * @param {HTMLElement} el - 目标元素
 * @param {string} className - 类名
 */
export function addClass(el, className) {
  if (!el) return;
  el.classList.add(className);
}

/**
 * 移除类名
 * @param {HTMLElement} el - 目标元素
 * @param {string} className - 类名
 */
export function removeClass(el, className) {
  if (!el) return;
  el.classList.remove(className);
}

/**
 * 检查是否包含类名
 * @param {HTMLElement} el - 目标元素
 * @param {string} className - 类名
 * @returns {boolean}
 */
export function hasClass(el, className) {
  return el?.classList.contains(className) || false;
}

/**
 * 设置元素显示/隐藏
 * @param {HTMLElement} el - 目标元素
 * @param {boolean} show - 是否显示
 */
export function setVisible(el, show) {
  if (!el) return;
  el.style.display = show ? '' : 'none';
}

/**
 * 安全地设置HTML内容
 * @param {HTMLElement} el - 目标元素
 * @param {string} html - HTML内容
 */
export function setHTML(el, html) {
  if (!el) return;
  el.innerHTML = html;
}

/**
 * 安全地设置文本内容
 * @param {HTMLElement} el - 目标元素
 * @param {string} text - 文本内容
 */
export function setText(el, text) {
  if (!el) return;
  el.textContent = text;
}

/**
 * 获取/设置data属性
 * @param {HTMLElement} el - 目标元素
 * @param {string} key - 属性名
 * @param {string} value - 属性值（可选）
 * @returns {string|undefined}
 */
export function data(el, key, value) {
  if (!el) return;
  if (value !== undefined) {
    el.dataset[key] = value;
  } else {
    return el.dataset[key];
  }
}

/**
 * 委托事件监听
 * @param {HTMLElement} container - 容器元素
 * @param {string} selector - 目标选择器
 * @param {string} event - 事件类型
 * @param {Function} handler - 处理函数
 */
export function delegate(container, selector, event, handler) {
  container.addEventListener(event, (e) => {
    const target = e.target.closest(selector);
    if (target && container.contains(target)) {
      handler.call(target, e, target);
    }
  });
}

/**
 * 等待DOM元素出现
 * @param {string} selector - CSS选择器
 * @param {number} timeout - 超时时间（毫秒）
 * @returns {Promise<HTMLElement>}
 */
export function waitForElement(selector, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const el = document.querySelector(selector);
    if (el) {
      resolve(el);
      return;
    }
    
    const observer = new MutationObserver(() => {
      const el = document.querySelector(selector);
      if (el) {
        observer.disconnect();
        resolve(el);
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    setTimeout(() => {
      observer.disconnect();
      reject(new Error(`Element ${selector} not found within ${timeout}ms`));
    }, timeout);
  });
}

/**
 * 防抖函数
 * @param {Function} fn - 目标函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function}
 */
export function debounce(fn, delay = 300) {
  let timer = null;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * 节流函数
 * @param {Function} fn - 目标函数
 * @param {number} limit - 限制时间（毫秒）
 * @returns {Function}
 */
export function throttle(fn, limit = 300) {
  let inThrottle = false;
  return function(...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * 动画帧节流
 * @param {Function} fn - 目标函数
 * @returns {Function}
 */
export function rafThrottle(fn) {
  let ticking = false;
  return function(...args) {
    if (!ticking) {
      requestAnimationFrame(() => {
        fn.apply(this, args);
        ticking = false;
      });
      ticking = true;
    }
  };
}
