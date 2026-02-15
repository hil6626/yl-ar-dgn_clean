/**
 * AR页面侧边栏组件
 * 拆分自: page-ar.js
 * 版本: v1.0.0
 */

export class Sidebar {
  constructor(page) {
    this.page = page;
    this.container = document.getElementById('sidebar-mount');
  }

  /**
   * 渲染侧边栏
   */
  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="ar-sidebar">
        <!-- 节点列表 -->
        <div class="ar-nodes-section">
          <div class="ar-nodes-header">
            <span>🥽</span>
            <span>AR 节点</span>
          </div>
          <ul id="ar-nodes-list" class="ar-nodes-list">
            <li class="ar-node-item loading">
              <span class="loading-spinner"></span>
              <span>加载节点中...</span>
            </li>
          </ul>
        </div>
        
        <!-- 资源监控 -->
        <div class="ar-resources-section">
          <div class="ar-resources-title">
            <span>📊</span>
            <span>资源监控</span>
          </div>
          <div class="resource-monitor">
            <div class="resource-item">
              <div class="resource-header">
                <div class="resource-label">
                  <span class="resource-icon cpu">CPU</span>
                  <span>处理器</span>
                </div>
                <span id="cpu-value" class="resource-value">0%</span>
              </div>
              <div class="resource-progress-bar">
                <div id="cpu-fill" class="resource-progress-fill cpu" style="width: 0%"></div>
              </div>
            </div>
            <div class="resource-item">
              <div class="resource-header">
                <div class="resource-label">
                  <span class="resource-icon memory">MEM</span>
                  <span>内存</span>
                </div>
                <span id="memory-value" class="resource-value">0%</span>
              </div>
              <div class="resource-progress-bar">
                <div id="memory-fill" class="resource-progress-fill memory" style="width: 0%"></div>
              </div>
            </div>
            <div class="resource-item">
              <div class="resource-header">
                <div class="resource-label">
                  <span class="resource-icon gpu">GPU</span>
                  <span>显卡</span>
                </div>
                <span id="gpu-value" class="resource-value">0%</span>
              </div>
              <div class="resource-progress-bar">
                <div id="gpu-fill" class="resource-progress-fill gpu" style="width: 0%"></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 控制按钮 -->
        <div class="ar-controls-section">
          <button class="ar-control-btn start" data-action="start-ar">
            <span>▶</span>
            <span>启动场景</span>
          </button>
          <button class="ar-control-btn stop" data-action="stop-ar">
            <span>⏹</span>
            <span>停止场景</span>
          </button>
          <button class="ar-control-btn refresh" data-action="refresh-ar">
            <span>🔄</span>
            <span>刷新状态</span>
          </button>
        </div>
      </div>
    `;
  }

  /**
   * 渲染AR节点列表
   * @param {Array} nodes - 节点数据
   */
  renderNodes(nodes) {
    const list = document.getElementById('ar-nodes-list');
    if (!list) return;

    if (nodes.length === 0) {
      list.innerHTML = '<li class="ar-node-item empty"><span>暂无AR节点</span></li>';
      return;
    }

    list.innerHTML = nodes.map(node => `
      <li class="ar-node-item" data-node-id="${node.id}" data-action="select-node">
        <span class="node-status-indicator ${node.status}"></span>
        <div class="node-info">
          <div class="node-name">${node.name}</div>
          <div class="node-meta">${node.ip_address || 'N/A'}</div>
        </div>
        <span class="node-status-text ${node.status}">${this.page.getARNodeStatusText(node.status)}</span>
      </li>
    `).join('');

    // 绑定节点选择事件
    list.querySelectorAll('[data-action="select-node"]').forEach(item => {
      item.addEventListener('click', () => {
        const nodeId = item.dataset.nodeId;
        this.page.selectNode(nodeId);
      });
    });
  }

  /**
   * 更新资源条
   * @param {Object} resources - 资源数据
   */
  updateResources(resources) {
    const cpu = resources.cpu || 0;
    const memory = resources.memory || 0;
    const gpu = resources.gpu || 0;

    const cpuValue = document.getElementById('cpu-value');
    const cpuFill = document.getElementById('cpu-fill');
    const memoryValue = document.getElementById('memory-value');
    const memoryFill = document.getElementById('memory-fill');
    const gpuValue = document.getElementById('gpu-value');
    const gpuFill = document.getElementById('gpu-fill');

    if (cpuValue) cpuValue.textContent = `${cpu}%`;
    if (cpuFill) cpuFill.style.width = `${cpu}%`;

    if (memoryValue) memoryValue.textContent = `${memory}%`;
    if (memoryFill) memoryFill.style.width = `${memory}%`;

    if (gpuValue) gpuValue.textContent = `${gpu}%`;
    if (gpuFill) gpuFill.style.width = `${gpu}%`;
  }
}
