/**
 * cURL命令生成器
 * 拆分自: page-api-doc.js
 * 版本: v1.0.0
 */

export class CurlGenerator {
  /**
   * 生成cURL命令
   * @param {Object} endpoint - 端点数据
   * @returns {string}
   */
  generate(endpoint) {
    let curl = `curl -X ${endpoint.method} "${window.location.origin}${endpoint.path}"`;

    if (endpoint.method !== 'GET') {
      curl += ' \\\n  -H "Content-Type: application/json"';
    }

    curl += ' \\\n  -H "Authorization: Bearer YOUR_TOKEN_HERE"';

    if (endpoint.body) {
      curl += ` \\\n  -d '${JSON.stringify(endpoint.body)}'`;
    }

    return curl;
  }
}
