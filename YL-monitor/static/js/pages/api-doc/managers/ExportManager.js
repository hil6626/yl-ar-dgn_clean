/**
 * API Doc导出管理器（多格式导出）
 * 版本: v1.0.0
 */

export class ExportManager {
  constructor(page) {
    this.page = page;
    this.formats = ['markdown', 'html', 'json', 'openapi'];
  }

  /**
   * 显示导出格式选择弹窗
   */
  showExportDialog() {
    const modal = document.createElement('div');
    modal.className = 'export-dialog-modal';
    modal.innerHTML = `
      <div class="export-dialog-content">
        <div class="export-dialog-header">
          <h3>📥 导出API文档</h3>
          <p>选择要导出的格式：</p>
        </div>
        <div class="export-dialog-body">
          <div class="export-options">
            <button class="export-option" data-format="markdown">
              <div class="export-icon">📝</div>
              <div class="export-info">
                <div class="export-name">Markdown</div>
                <div class="export-desc">适合GitHub、文档站点</div>
              </div>
            </button>
            <button class="export-option" data-format="html">
              <div class="export-icon">🌐</div>
              <div class="export-info">
                <div class="export-name">HTML</div>
                <div class="export-desc">完整的离线文档</div>
              </div>
            </button>
            <button class="export-option" data-format="json">
              <div class="export-icon">📋</div>
              <div class="export-info">
                <div class="export-name">JSON</div>
                <div class="export-desc">原始数据结构</div>
              </div>
            </button>
            <button class="export-option" data-format="openapi">
              <div class="export-icon">🔌</div>
              <div class="export-info">
                <div class="export-name">OpenAPI 3.0</div>
                <div class="export-desc">标准API规范格式</div>
              </div>
            </button>
          </div>
        </div>
        <div class="export-dialog-footer">
          <button class="btn btn-secondary" data-action="close-export-dialog">取消</button>
        </div>
      </div>
    `;

    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
      .export-dialog-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
      }
      .export-dialog-content {
        background: var(--bg-primary);
        border-radius: 12px;
        width: 90%;
        max-width: 500px;
        animation: slideUp 0.3s ease;
      }
      .export-dialog-header {
        padding: 24px;
        border-bottom: 1px solid var(--border);
      }
      .export-dialog-header h3 {
        margin: 0 0 8px 0;
        color: var(--text-primary);
      }
      .export-dialog-header p {
        margin: 0;
        color: var(--text-secondary);
        font-size: 14px;
      }
      .export-dialog-body {
        padding: 16px;
      }
      .export-options {
        display: grid;
        gap: 12px;
      }
      .export-option {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        border: 2px solid var(--border);
        border-radius: 8px;
        background: var(--bg-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
      }
      .export-option:hover {
        border-color: var(--primary);
        background: var(--primary-50);
      }
      .export-icon {
        font-size: 24px;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-primary);
        border-radius: 8px;
      }
      .export-name {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
      }
      .export-desc {
        font-size: 13px;
        color: var(--text-secondary);
      }
      .export-dialog-footer {
        padding: 16px 24px;
        border-top: 1px solid var(--border);
        display: flex;
        justify-content: flex-end;
      }
    `;
    document.head.appendChild(style);

    document.body.appendChild(modal);

    // 绑定格式选择事件
    modal.querySelectorAll('.export-option').forEach(btn => {
      btn.addEventListener('click', () => {
        const format = btn.dataset.format;
        this.export(format);
        modal.remove();
      });
    });

    // 绑定关闭事件
    modal.querySelector('[data-action="close-export-dialog"]').addEventListener('click', () => {
      modal.remove();
    });

    // 点击遮罩关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }

  /**
   * 执行导出
   * @param {string} format - 导出格式
   */
  export(format) {
    const apiData = this.page.apiData;
    
    switch (format) {
      case 'markdown':
        this.exportMarkdown(apiData);
        break;
      case 'html':
        this.exportHTML(apiData);
        break;
      case 'json':
        this.exportJSON(apiData);
        break;
      case 'openapi':
        this.exportOpenAPI(apiData);
        break;
    }
  }

  /**
   * 导出Markdown格式
   * @param {Array} apiData - API数据
   */
  exportMarkdown(apiData) {
    let markdown = '# API文档\n\n';
    markdown += `生成时间: ${new Date().toLocaleString('zh-CN')}\n\n`;
    markdown += '---\n\n';

    for (const module of apiData) {
      markdown += `## ${module.name}\n\n`;
      if (module.description) {
        markdown += `${module.description}\n\n`;
      }

      for (const endpoint of module.endpoints) {
        markdown += `### ${endpoint.name}\n\n`;
        markdown += `\`${endpoint.method}\` \`${endpoint.path}\`\n\n`;
        
        if (endpoint.description) {
          markdown += `${endpoint.description}\n\n`;
        }

        // 参数表格
        if (endpoint.params && endpoint.params.length > 0) {
          markdown += '**参数：**\n\n';
          markdown += '| 名称 | 类型 | 必填 | 说明 |\n';
          markdown += '|------|------|------|------|\n';
          
          for (const param of endpoint.params) {
            const required = param.required ? '是' : '否';
            markdown += `| ${param.name} | ${param.type || 'string'} | ${required} | ${param.description || '-'} |\n`;
          }
          markdown += '\n';
        }

        // 响应示例
        if (endpoint.responseExample) {
          markdown += '**响应示例：**\n\n';
          markdown += '```json\n';
          markdown += JSON.stringify(endpoint.responseExample, null, 2);
          markdown += '\n```\n\n';
        }

        markdown += '---\n\n';
      }
    }

    this.downloadFile(markdown, 'api-documentation.md', 'text/markdown');
    this.showSuccess('Markdown文档已导出');
  }

  /**
   * 导出HTML格式
   * @param {Array} apiData - API数据
   */
  exportHTML(apiData) {
    const html = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API文档</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        h1 { color: #2563eb; margin-bottom: 20px; }
        h2 { color: #1e40af; margin: 40px 0 20px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
        h3 { color: #374151; margin: 30px 0 15px; }
        .endpoint { background: #f9fafb; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .method { 
            display: inline-block; 
            padding: 4px 12px; 
            border-radius: 4px; 
            font-weight: 600; 
            font-size: 12px;
            margin-right: 10px;
        }
        .method-get { background: #dbeafe; color: #1e40af; }
        .method-post { background: #d1fae5; color: #065f46; }
        .method-put { background: #fef3c7; color: #92400e; }
        .method-delete { background: #fee2e2; color: #991b1b; }
        .path { font-family: monospace; font-size: 14px; color: #6b7280; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #f3f4f6; font-weight: 600; }
        pre {
            background: #1f2937;
            color: #e5e7eb;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }
        .timestamp { color: #9ca3af; font-size: 14px; margin-bottom: 30px; }
    </style>
</head>
<body>
    <h1>API文档</h1>
    <p class="timestamp">生成时间: ${new Date().toLocaleString('zh-CN')}</p>
    
    ${apiData.map(module => `
        <h2>${module.name}</h2>
        ${module.description ? `<p>${module.description}</p>` : ''}
        
        ${module.endpoints.map(endpoint => `
            <div class="endpoint">
                <h3>${endpoint.name}</h3>
                <p>
                    <span class="method method-${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                    <span class="path">${endpoint.path}</span>
                </p>
                ${endpoint.description ? `<p>${endpoint.description}</p>` : ''}
                
                ${endpoint.params && endpoint.params.length > 0 ? `
                    <table>
                        <thead>
                            <tr>
                                <th>参数</th>
                                <th>类型</th>
                                <th>必填</th>
                                <th>说明</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${endpoint.params.map(param => `
                                <tr>
                                    <td><code>${param.name}</code></td>
                                    <td>${param.type || 'string'}</td>
                                    <td>${param.required ? '是' : '否'}</td>
                                    <td>${param.description || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                ` : ''}
                
                ${endpoint.responseExample ? `
                    <p><strong>响应示例：</strong></p>
                    <pre>${JSON.stringify(endpoint.responseExample, null, 2)}</pre>
                ` : ''}
            </div>
        `).join('')}
    `).join('')}
</body>
</html>
    `;

    this.downloadFile(html, 'api-documentation.html', 'text/html');
    this.showSuccess('HTML文档已导出');
  }

  /**
   * 导出JSON格式
   * @param {Array} apiData - API数据
   */
  exportJSON(apiData) {
    const json = JSON.stringify(apiData, null, 2);
    this.downloadFile(json, 'api-documentation.json', 'application/json');
    this.showSuccess('JSON数据已导出');
  }

  /**
   * 导出OpenAPI 3.0格式
   * @param {Array} apiData - API数据
   */
  exportOpenAPI(apiData) {
    const openApi = {
      openapi: '3.0.0',
      info: {
        title: 'YL-Monitor API',
        version: '1.0.0',
        description: 'YL-Monitor 监控平台API文档'
      },
      servers: [
        {
          url: '/api/v1',
          description: '本地服务器'
        }
      ],
      paths: {}
    };

    // 转换端点为OpenAPI格式
    for (const module of apiData) {
      for (const endpoint of module.endpoints) {
        const pathKey = endpoint.path.replace(/{/g, '{').replace(/}/g, '}');
        
        if (!openApi.paths[pathKey]) {
          openApi.paths[pathKey] = {};
        }

        const methodKey = endpoint.method.toLowerCase();
        openApi.paths[pathKey][methodKey] = {
          summary: endpoint.name,
          description: endpoint.description,
          tags: [module.name],
          parameters: endpoint.params?.map(param => ({
            name: param.name,
            in: endpoint.path.includes(`{${param.name}}`) ? 'path' : 'query',
            required: param.required || false,
            schema: {
              type: param.type || 'string'
            },
            description: param.description
          })) || [],
          responses: {
            '200': {
              description: '成功',
              content: {
                'application/json': {
                  example: endpoint.responseExample
                }
              }
            }
          }
        };
      }
    }

    const yaml = this.convertToYaml(openApi);
    this.downloadFile(yaml, 'openapi.yaml', 'application/yaml');
    this.showSuccess('OpenAPI规范已导出');
  }

  /**
   * 转换为YAML格式
   * @param {Object} obj - 对象
   * @param {number} indent - 缩进级别
   * @returns {string}
   */
  convertToYaml(obj, indent = 0) {
    const spaces = '  '.repeat(indent);
    let yaml = '';

    for (const [key, value] of Object.entries(obj)) {
      if (value === null) {
        yaml += `${spaces}${key}: null\n`;
      } else if (typeof value === 'object' && !Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`;
        yaml += this.convertToYaml(value, indent + 1);
      } else if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`;
        for (const item of value) {
          if (typeof item === 'object') {
            yaml += `${spaces}- \n`;
            yaml += this.convertToYaml(item, indent + 1).replace(/^(\s+)/, '$1  ');
          } else {
            yaml += `${spaces}- ${item}\n`;
          }
        }
      } else {
        yaml += `${spaces}${key}: ${value}\n`;
      }
    }

    return yaml;
  }

  /**
   * 下载文件
   * @param {string} content - 文件内容
   * @param {string} filename - 文件名
   * @param {string} mimeType - MIME类型
   */
  downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * 显示成功提示
   * @param {string} message - 消息内容
   */
  showSuccess(message) {
    this.page.ui.showToast({
      type: 'success',
      message: message
    });
  }
}
