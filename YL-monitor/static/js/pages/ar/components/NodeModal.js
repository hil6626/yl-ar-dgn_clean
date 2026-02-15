/**
 * AR节点详情弹窗组件
 * 拆分自: page-ar.js
 * 版本: v1.0.0
 */

export class NodeModal {
  constructor(page) {
    this.page = page;
    this.modal = null;
  }

  /**
   * 显示节点详情弹窗
   * @param {Object} node - 节点数据
   */
  show(node) {
    // 移除已存在的弹窗
    this.close();

    // 创建模态框
    this.modal = document.createElement('div');
    this.modal.className = 'ar-node-modal';
    this.modal.id = 'ar-node-modal';
    this.modal.innerHTML = `
      <div class="ar-node-modal-content">
        <div class="ar-node-modal-header">
          <div class="ar-node-modal-title">
            <span class="node-status-indicator ${node.status}"></span>
            <span>${node.name}</span>
          </div>
          <button class="btn btn-sm btn-ghost" data-action="close-modal">×</button>
        </div>
        <div class="ar-node-modal-body">
          <div class="ar-node-details-grid">
            <div class="ar-detail-item">
              <span class="ar-detail-label">节点ID</span>
              <span class="ar-detail-value">${node.id}</span>
            </div>
            <div class="ar-detail-item">
              <span class="ar-detail-label">IP地址</span>
              <span class="ar-detail-value">${node.ip_address || 'N/A'}</span>
            </div>
            <div class="ar-detail-item">
              <span class="ar-detail-label">状态</span>
              <span class="ar-detail-value status-${node.status}">${this.page.getARNodeStatusText(node.status)}</span>
            </div>
            <div class="ar-detail-item">
              <span class="ar-detail-label">最后在线</span>
              <span class="ar-detail-value">${node.last_seen || '未知'}</span>
            </div>
          </div>
          
          <div class="ar-resource-details">
            <div class="ar-resource-details-title">
              <span>📊</span>
              <span>资源使用趋势</span>
            </div>
            <div class="ar-resource-chart">
              <span>资源使用图表 (开发中)</span>
            </div>
          </div>
          
          <div class="flex gap-2 mt-4">
            <button class="btn btn-primary" data-action="refresh-node" data-node-id="${node.id}">
              🔄 刷新状态
            </button>
            <button class="btn btn-secondary" data-action="view-logs" data-node-id="${node.id}">
              📋 查看日志
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.modal);

    // 显示动画
    requestAnimationFrame(() => {
      this.modal.classList.add('active');
    });

    // 绑定关闭事件
    this.modal.querySelector('[data-action="close-modal"]').addEventListener('click', () => {
      this.close();
    });

    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.close();
      }
    });
  }

  /**
   * 关闭弹窗
   */
  close() {
    if (this.modal) {
      this.modal.classList.remove('active');
      setTimeout(() => {
        if (this.modal) {
          this.modal.remove();
          this.modal = null;
        }
      }, 300);
    }
  }
}
