/**
 * AR数据管理器
 * 拆分自: page-ar.js
 * 版本: v1.0.0
 */

export class ARDataManager {
  constructor(page) {
    this.page = page;
    this.apiBaseUrl = '/api/v1';
  }

  /**
   * 加载AR节点数据
   * @returns {Promise<Array>}
   */
  async loadNodes() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/ar/nodes`);
      if (!response.ok) throw new Error('获取AR节点失败');

      const data = await response.json();
      return data.nodes || [];
    } catch (error) {
      console.error('[ARDataManager] 加载AR节点失败:', error);
      this.page.ui.showToast({
        type: 'error',
        message: '加载AR节点失败'
      });
      return [];
    }
  }

  /**
   * 刷新节点
   * @param {string} nodeId - 节点ID
   * @returns {Promise<Object|null>}
   */
  async refreshNode(nodeId) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/ar/nodes/${nodeId}`);
      if (!response.ok) throw new Error('刷新节点失败');

      const data = await response.json();
      return data.node || null;
    } catch (error) {
      console.error('[ARDataManager] 刷新节点失败:', error);
      return null;
    }
  }
}
