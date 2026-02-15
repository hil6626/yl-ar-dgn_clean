/**
 * API测试面板组件
 * 拆分自: page-api-doc.js
 * 版本: v1.0.0
 */

export class TestPanel {
  constructor(page) {
    this.page = page;
    this.container = document.getElementById('api-test-panel-mount');
    this.overlay = null;
    this.isOpen = false;
  }

  /**
   * 打开测试面板
   * @param {Object} endpoint - 端点数据
   */
  open(endpoint) {
    if (!this.container) return;

    // 创建遮罩层
    this.overlay = document.createElement('div');
    this.overlay.className = 'api-test-overlay';
    this.overlay.id = 'api-test-overlay';
    document.body.appendChild(this.overlay);

    this.container.innerHTML = `
      <div class="api-test-panel-header">
        <h3>🧪 测试 ${endpoint.name}</h3>
        <button class="api-test-panel-close" data-action="close-test-panel">×</button>
      </div>
      <div class="api-test-panel-body">
        <div class="api-test-form-group">
          <label>请求方法</label>
          <input type="text" value="${endpoint.method}" readonly>
        </div>
        <div class="api-test-form-group">
          <label>请求地址</label>
          <input type="text" value="${window.location.origin}${endpoint.path}" readonly>
        </div>
        ${endpoint.params?.filter(p => p.in === 'path').map(p => `
          <div class="api-test-form-group">
            <label>路径参数: ${p.name}</label>
            <input type="text" id="param-${p.name}" placeholder="${p.description || ''}">
          </div>
        `).join('') || ''}
        ${endpoint.method !== 'GET' ? `
          <div class="api-test-form-group">
            <label>请求体 (JSON)</label>
            <textarea id="test-request-body">${endpoint.body ? JSON.stringify(endpoint.body, null, 2) : '{}'}</textarea>
          </div>
        ` : ''}
        <button class="api-test-submit" data-action="send-test-request">
          发送请求
        </button>
        <div id="test-result" class="api-test-result" style="display: none;">
          <h4>响应结果</h4>
          <pre id="test-response"></pre>
        </div>
      </div>
    `;

    // 动画进入
    setTimeout(() => {
      this.container.classList.add('open');
      this.overlay.classList.add('open');
    }, 10);

    this.isOpen = true;
  }

  /**
   * 关闭测试面板
   */
  close() {
    if (this.container) this.container.classList.remove('open');
    if (this.overlay) this.overlay.classList.remove('open');
    
    setTimeout(() => {
      if (this.overlay) this.overlay.remove();
      this.overlay = null;
    }, 300);
    
    this.isOpen = false;
  }

  /**
   * 显示测试结果
   * @param {string} content - 响应内容
   * @param {boolean} isError - 是否错误
   */
  showResult(content, isError = false) {
    const resultDiv = document.getElementById('test-result');
    const responsePre = document.getElementById('test-response');
    
    if (resultDiv && responsePre) {
      resultDiv.style.display = 'block';
      responsePre.textContent = content;
      responsePre.className = isError ? 'error' : '';
    }
  }

  /**
   * 获取请求体
   * @returns {Object|null}
   */
  getRequestBody() {
    const bodyText = document.getElementById('test-request-body')?.value || '{}';
    try {
      return JSON.parse(bodyText);
    } catch (e) {
      return null;
    }
  }

  /**
   * 获取路径参数
   * @param {Array} params - 参数定义
   * @returns {Object}
   */
  getPathParams(params) {
    const values = {};
    params?.filter(p => p.in === 'path').forEach(p => {
      values[p.name] = document.getElementById(`param-${p.name}`)?.value || '';
    });
    return values;
  }
}
