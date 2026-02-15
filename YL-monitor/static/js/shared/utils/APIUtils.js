/**
 * API工具函数库
 * 共享模块 - 所有页面可复用
 * 版本: v1.0.0
 */

/**
 * 默认请求配置
 */
const DEFAULT_CONFIG = {
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
};

/**
 * 构建完整URL
 * @param {string} endpoint - API端点
 * @returns {string}
 */
export function buildURL(endpoint) {
  const base = DEFAULT_CONFIG.baseURL;
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${base}${path}`;
}

/**
 * 发送GET请求
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @returns {Promise<any>}
 */
export async function get(endpoint, options = {}) {
  return request(endpoint, { ...options, method: 'GET' });
}

/**
 * 发送POST请求
 * @param {string} endpoint - API端点
 * @param {Object} data - 请求数据
 * @param {Object} options - 请求选项
 * @returns {Promise<any>}
 */
export async function post(endpoint, data, options = {}) {
  return request(endpoint, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data)
  });
}

/**
 * 发送PUT请求
 * @param {string} endpoint - API端点
 * @param {Object} data - 请求数据
 * @param {Object} options - 请求选项
 * @returns {Promise<any>}
 */
export async function put(endpoint, data, options = {}) {
  return request(endpoint, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

/**
 * 发送DELETE请求
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @returns {Promise<any>}
 */
export async function del(endpoint, options = {}) {
  return request(endpoint, { ...options, method: 'DELETE' });
}

/**
 * 发送通用请求
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @returns {Promise<any>}
 */
export async function request(endpoint, options = {}) {
  const url = buildURL(endpoint);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || DEFAULT_CONFIG.timeout);
  
  try {
    const response = await fetch(url, {
      ...DEFAULT_CONFIG,
      ...options,
      headers: {
        ...DEFAULT_CONFIG.headers,
        ...options.headers
      },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
      error.status = response.status;
      error.response = response;
      throw error;
    }
    
    // 检查响应内容类型
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return await response.text();
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    
    throw error;
  }
}

/**
 * 带重试的请求
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @param {number} maxRetries - 最大重试次数
 * @returns {Promise<any>}
 */
export async function requestWithRetry(endpoint, options = {}, maxRetries = 3) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await request(endpoint, options);
    } catch (error) {
      lastError = error;
      
      // 不重试客户端错误（4xx）
      if (error.status >= 400 && error.status < 500) {
        throw error;
      }
      
      // 指数退避
      const delay = Math.pow(2, i) * 1000;
      await sleep(delay);
    }
  }
  
  throw lastError;
}

/**
 * 批量请求
 * @param {Array<{endpoint: string, options: Object}>} requests - 请求数组
 * @returns {Promise<Array>}
 */
export async function batchRequest(requests) {
  return Promise.all(
    requests.map(({ endpoint, options }) => request(endpoint, options))
  );
}

/**
 * 延迟函数
 * @param {number} ms - 毫秒
 * @returns {Promise<void>}
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 构建查询字符串
 * @param {Object} params - 参数对象
 * @returns {string}
 */
export function buildQueryString(params) {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  
  const query = searchParams.toString();
  return query ? `?${query}` : '';
}

/**
 * 解析错误信息
 * @param {Error} error - 错误对象
 * @returns {string}
 */
export function parseError(error) {
  if (error.status === 404) {
    return '请求的资源不存在';
  }
  if (error.status === 401) {
    return '未授权，请重新登录';
  }
  if (error.status === 403) {
    return '没有权限执行此操作';
  }
  if (error.status >= 500) {
    return '服务器错误，请稍后重试';
  }
  if (error.message === 'Request timeout') {
    return '请求超时，请检查网络连接';
  }
  return error.message || '未知错误';
}

/**
 * API响应缓存
 */
class APICache {
  constructor() {
    this.cache = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5分钟
  }
  
  /**
   * 获取缓存数据
   * @param {string} key - 缓存键
   * @returns {any|null}
   */
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
  
  /**
   * 设置缓存数据
   * @param {string} key - 缓存键
   * @param {any} data - 数据
   * @param {number} ttl - 过期时间（毫秒）
   */
  set(key, data, ttl = this.defaultTTL) {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl
    });
  }
  
  /**
   * 清除缓存
   * @param {string} key - 缓存键（可选，不提供则清除所有）
   */
  clear(key) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
}

// 导出缓存实例
export const apiCache = new APICache();

/**
 * 带缓存的GET请求
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @param {number} ttl - 缓存时间（毫秒）
 * @returns {Promise<any>}
 */
export async function getCached(endpoint, options = {}, ttl) {
  const cacheKey = `${endpoint}:${JSON.stringify(options)}`;
  const cached = apiCache.get(cacheKey);
  
  if (cached) {
    return cached;
  }
  
  const data = await get(endpoint, options);
  apiCache.set(cacheKey, data, ttl);
  return data;
}

/**
 * 清除API缓存
 * @param {string} pattern - 匹配模式（可选）
 */
export function clearCache(pattern) {
  if (!pattern) {
    apiCache.clear();
    return;
  }
  
  // 清除匹配的缓存
  for (const key of apiCache.cache.keys()) {
    if (key.includes(pattern)) {
      apiCache.cache.delete(key);
    }
  }
}
