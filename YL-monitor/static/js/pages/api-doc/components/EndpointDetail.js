/**
 * API端点详情组件
 * 拆分自: page-api-doc.js
 * 版本: v1.0.0
 */

export class EndpointDetail {
  constructor(page) {
    this.page = page;
    this.container = document.getElementById('api-content-mount');
  }

  /**
   * 渲染端点详情
   * @param {Object} endpoint - 端点数据
   */
  render(endpoint) {
    if (!this.container) return;

    const curlCommand = this.page.generateCurlCommand(endpoint);

    this.container.innerHTML = `
      <div class="api-endpoint-card">
        <div class="api-endpoint-header">
          <span class="http-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
          <div class="api-endpoint-title">
            <h2>${endpoint.name}</h2>
            <p class="endpoint-description">${endpoint.description}</p>
          </div>
        </div>
        
        <div class="api-endpoint-body">
          <!-- API路径 -->
          <div class="api-section">
            <h3 class="api-section-title">📍 请求地址</h3>
            <div class="api-path-full">
              <code>${endpoint.path}</code>
              <button class="copy-btn" data-action="copy-to-clipboard" data-text="${endpoint.path}" title="复制路径">
                📋
              </button>
            </div>
          </div>

          <!-- 请求参数 -->
          ${endpoint.params && endpoint.params.length > 0 ? this.renderParams(endpoint.params) : ''}

          <!-- 请求体示例 -->
          ${endpoint.body ? this.renderRequestBody(endpoint.body) : ''}

          <!-- cURL命令 -->
          <div class="api-section">
            <h3 class="api-section-title">🖥️ cURL命令</h3>
            <div class="api-code-block">
              <div class="api-code-header">
                <span>Bash</span>
                <button class="copy-btn" data-action="copy-to-clipboard" data-text="${this.escapeHtml(curlCommand)}">
                  📋 复制curl命令
                </button>
              </div>
              <pre><code class="language-bash">${curlCommand}</code></pre>
            </div>
          </div>

          <!-- 响应示例 -->
          ${endpoint.response ? this.renderResponse(endpoint.response) : ''}

          <!-- 在线测试按钮 -->
          <button class="api-test-btn" data-action="open-test-panel">
            <span>🧪</span> 在线测试API
          </button>
        </div>
      </div>
    `;

    // 重新初始化代码高亮
    this.page.initCodeHighlight();
  }

  /**
   * 渲染请求参数表格
   * @param {Array} params - 参数列表
   * @returns {string}
   */
  renderParams(params) {
    return `
      <div class="api-section">
        <h3 class="api-section-title">📋 请求参数</h3>
        <table class="api-params-table">
          <thead>
            <tr>
              <th>参数名</th>
              <th>类型</th>
              <th>必填</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            ${params.map(param => `
              <tr>
                <td><code class="param-name">${param.name}</code></td>
                <td><span class="param-type">${param.type}</span></td>
                <td>${param.required ? 
                  '<span class="param-required">必填</span>' : 
                  '<span class="param-optional">可选</span>'}</td>
                <td>${param.description || '-'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  /**
   * 渲染请求体示例
   * @param {Object} body - 请求体
   * @returns {string}
   */
  renderRequestBody(body) {
    return `
      <div class="api-section">
        <h3 class="api-section-title">📤 请求体示例</h3>
        <div class="api-code-block">
          <div class="api-code-header">
            <span>JSON</span>
            <button class="copy-btn" data-action="copy-to-clipboard" data-text="${this.escapeJson(body)}">
              📋 复制
            </button>
          </div>
          <pre><code class="language-json">${JSON.stringify(body, null, 2)}</code></pre>
        </div>
      </div>
    `;
  }

  /**
   * 渲染响应示例
   * @param {Object} response - 响应数据
   * @returns {string}
   */
  renderResponse(response) {
    return `
      <div class="api-section">
        <h3 class="api-section-title">📥 响应示例</h3>
        <div class="api-response-status">
          <span class="status-code ${response.status < 400 ? 'success' : 'error'}">
            ${response.status}
          </span>
          <span class="status-message">${response.status < 400 ? 'OK' : 'Error'}</span>
        </div>
        <div class="api-code-block">
          <div class="api-code-header">
            <span>JSON</span>
            <button class="copy-btn" data-action="copy-to-clipboard" data-text="${this.escapeJson(response.example)}">
              📋 复制
            </button>
          </div>
          <pre><code class="language-json">${JSON.stringify(response.example, null, 2)}</code></pre>
        </div>
      </div>
    `;
  }

  /**
   * 渲染空状态
   */
  renderEmpty() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="api-empty-state">
        <div class="api-empty-state-icon">📚</div>
        <div class="api-empty-state-title">选择API端点</div>
        <div class="api-empty-state-desc">从左侧导航栏选择一个API端点查看详情</div>
      </div>
    `;
  }

  /**
   * 转义HTML
   * @param {string} text - 文本
   * @returns {string}
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * 转义JSON
   * @param {Object} obj - 对象
   * @returns {string}
   */
  escapeJson(obj) {
    return this.escapeHtml(JSON.stringify(obj));
  }
}
