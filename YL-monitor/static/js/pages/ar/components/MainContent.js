/**
 * AR页面主内容区组件
 * 拆分自: page-ar.js
 * 版本: v1.0.0
 */

export class MainContent {
  constructor(page) {
    this.page = page;
    this.container = document.getElementById('main-content-mount');
  }

  /**
   * 渲染主内容区
   */
  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="ar-main">
        <!-- 页面头部 -->
        <div class="ar-page-header">
          <div class="ar-title-section">
            <div class="ar-icon">🥽</div>
            <div>
              <h2 class="ar-title">AR 监控</h2>
              <p class="ar-subtitle">增强现实节点管理与可视化</p>
            </div>
          </div>
          <div class="ar-header-actions">
            <button class="btn btn-secondary" data-action="refresh-ar">
              <span>🔄</span>
              <span>刷新</span>
            </button>
            <button class="btn btn-secondary" data-action="settings-ar">
              <span>⚙️</span>
              <span>设置</span>
            </button>
          </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="ar-stats-grid">
          <div class="ar-stat-card">
            <div class="ar-stat-icon total">📊</div>
            <div class="ar-stat-info">
              <div id="total-nodes" class="ar-stat-value">0</div>
              <div class="ar-stat-label">总节点数</div>
            </div>
          </div>
          <div class="ar-stat-card">
            <div class="ar-stat-icon online">✓</div>
            <div class="ar-stat-info">
              <div id="online-nodes" class="ar-stat-value online">0</div>
              <div class="ar-stat-label">在线节点</div>
            </div>
          </div>
          <div class="ar-stat-card">
            <div class="ar-stat-icon offline">✗</div>
            <div class="ar-stat-info">
              <div id="offline-nodes" class="ar-stat-value offline">0</div>
              <div class="ar-stat-label">离线节点</div>
            </div>
          </div>
          <div class="ar-stat-card">
            <div class="ar-stat-icon backend">🖥️</div>
            <div class="ar-stat-info">
              <div id="ar-backend-status" class="ar-stat-value">未知</div>
              <div class="ar-stat-label">AR-backend</div>
            </div>
          </div>
          <div class="ar-stat-card">
            <div class="ar-stat-icon gui">🖱️</div>
            <div class="ar-stat-info">
              <div id="user-gui-status" class="ar-stat-value">未知</div>
              <div class="ar-stat-label">User GUI</div>
            </div>
          </div>
        </div>
        
        <!-- AR可视化区域 -->
        <div class="ar-visualization-section">
          <div class="ar-visualization-header">
            <div class="ar-visualization-title">
              <span>🎬</span>
              <span>AR 场景可视化</span>
            </div>
            <div class="ar-scene-status">
              <span class="status-dot" id="scene-status-dot"></span>
              <span id="scene-status" class="status-badge-ar idle">状态: 空闲</span>
            </div>
          </div>
          <div class="ar-visualization-container" id="ar-visualization">
            <div class="ar-empty-state">
              <div class="ar-empty-icon">🥽</div>
              <div class="ar-empty-title">AR 场景监控</div>
              <div class="ar-empty-description">实时显示 AR 节点状态和资源使用情况</div>
              <button class="btn btn-primary mt-4" data-action="start-ar">
                <span>▶</span>
                <span>启动场景</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 更新统计
   * @param {Array} nodes - 节点数据
   */
  updateStats(nodes) {
    const total = nodes.length;
    const online = nodes.filter(n => n.status === 'online').length;
    const offline = total - online;

    const totalEl = document.getElementById('total-nodes');
    const onlineEl = document.getElementById('online-nodes');
    const offlineEl = document.getElementById('offline-nodes');

    if (totalEl) totalEl.textContent = total;
    if (onlineEl) onlineEl.textContent = online;
    if (offlineEl) offlineEl.textContent = offline;
  }

  /**
   * 更新组件状态 (AR-backend 和 User GUI)
   * @param {Object} components - 组件状态对象 {arBackend: 'online', userGui: 'online'}
   */
  updateComponentStatus(components) {
    const arBackendEl = document.getElementById('ar-backend-status');
    const userGuiEl = document.getElementById('user-gui-status');

    if (arBackendEl && components.arBackend) {
      arBackendEl.textContent = components.arBackend === 'online' ? '在线' : '离线';
      arBackendEl.className = `ar-stat-value ${components.arBackend === 'online' ? 'online' : 'offline'}`;
    }

    if (userGuiEl && components.userGui) {
      userGuiEl.textContent = components.userGui === 'online' ? '在线' : '离线';
      userGuiEl.className = `ar-stat-value ${components.userGui === 'online' ? 'online' : 'offline'}`;
    }
  }

  /**
   * 渲染3D AR场景
   * @param {Array} nodes - 节点数据
   */
  render3DScene(nodes) {
    const vizContainer = document.getElementById('ar-visualization');
    if (!vizContainer) return;

    // 获取节点状态
    const displayNodes = nodes.length > 0 ? nodes : [
      { id: 'ar-1', name: 'AR-01', status: 'online' },
      { id: 'ar-2', name: 'AR-02', status: 'online' },
      { id: 'ar-3', name: 'AR-03', status: 'busy' },
      { id: 'ar-4', name: 'AR-04', status: 'offline' }
    ];

    vizContainer.innerHTML = `
      <div class="ar-3d-scene">
        <div class="ar-nodes-3d">
          ${displayNodes.map(node => `
            <div class="ar-node-3d ${node.status}" data-node-id="${node.id}">
              <span class="ar-node-3d-icon">🥽</span>
              <span class="ar-node-3d-label">${node.name}</span>
            </div>
          `).join('')}
        </div>
        <div class="ar-video-preview">
          <div class="ar-video-preview-header">
            <span class="status-dot online pulse"></span>
            <span>实时预览</span>
          </div>
          <div class="ar-video-preview-content">
            <span>视频流 (模拟)</span>
          </div>
        </div>
      </div>
    `;

    // 绑定节点点击事件
    vizContainer.querySelectorAll('.ar-node-3d').forEach(nodeEl => {
      nodeEl.addEventListener('click', () => {
        const nodeId = nodeEl.dataset.nodeId;
        const node = this.page.arNodes.find(n => n.id === nodeId) || 
          displayNodes.find(n => n.id === nodeId);
        if (node) {
          this.page.showNodeModal(node);
        }
      });
    });
  }

  /**
   * 设置场景状态
   * @param {string} status - 状态 (idle, rendering, running)
   */
  setSceneStatus(status) {
    const statusEl = document.getElementById('scene-status');
    const statusDot = document.getElementById('scene-status-dot');
    const vizContainer = document.getElementById('ar-visualization');

    const statusMap = {
      idle: { text: '状态: 空闲', class: 'idle', dot: 'offline' },
      rendering: { text: '状态: 渲染中', class: 'rendering', dot: 'busy' },
      running: { text: '状态: 运行中', class: 'running', dot: 'online pulse' }
    };

    const config = statusMap[status] || statusMap.idle;

    if (statusEl) {
      statusEl.textContent = config.text;
      statusEl.className = `status-badge-ar ${config.class}`;
    }

    if (statusDot) {
      statusDot.className = `status-dot ${config.dot}`;
    }

    if (status === 'rendering' && vizContainer) {
      vizContainer.innerHTML = `
        <div class="ar-rendering-state">
          <div class="ar-rendering-spinner"></div>
          <div class="ar-rendering-text">AR场景渲染中...</div>
          <div class="ar-rendering-subtext">正在连接AR节点</div>
        </div>
      `;
    } else if (status === 'idle' && vizContainer) {
      vizContainer.innerHTML = `
        <div class="ar-empty-state">
          <div class="ar-empty-icon">🥽</div>
          <div class="ar-empty-title">AR 场景监控</div>
          <div class="ar-empty-description">实时显示 AR 节点状态和资源使用情况</div>
          <button class="btn btn-primary mt-4" data-action="start-ar">
            <span>▶</span>
            <span>启动场景</span>
          </button>
        </div>
      `;
    }
  }
}
