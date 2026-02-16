/**
 * AR页面入口
 * 重构自: page-ar.js (500+行 → 模块化拆分)
 * 版本: v9.0.0 (模块化版本)
 */

// 导入组件
import { Sidebar, MainContent, NodeModal } from './components/index.js';

// 导入管理器
import { ARWebSocketManager, ARDataManager } from './managers/index.js';

/**
 * AR页面主类
 */
export default class ARPage {
  /**
   * @param {Object} deps - 依赖项（可选）
   * @param {Object} deps.uiComponents - UI组件库（可选）
   */
  constructor(deps = {}) {
    this.apiBaseUrl = '/api/v1';
    this.ui = deps.uiComponents || { showToast: () => {} };
    this.arNodes = [];
    
    // 初始化管理器
    this.wsManager = new ARWebSocketManager(this);
    this.dataManager = new ARDataManager(this);
    
    // 初始化组件
    this.sidebar = new Sidebar(this);
    this.mainContent = new MainContent(this);
    this.nodeModal = new NodeModal(this);
    
    // 挂载点引用
    this.mounts = {
      sidebar: document.getElementById('sidebar-mount'),
      mainContent: document.getElementById('main-content-mount')
    };
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[ARPage] 初始化AR监控页面 v9.0.0 (模块化)...');

    // 1. 渲染侧边栏
    this.sidebar.render();
    
    // 2. 渲染主内容区
    this.mainContent.render();
    
    // 3. 加载AR节点数据
    this.arNodes = await this.dataManager.loadNodes();
    this.sidebar.renderNodes(this.arNodes);
    this.mainContent.updateStats(this.arNodes);
    
    // 4. 加载组件状态 (AR-backend 和 User GUI)
    await this.loadComponentStatus();
    
    // 5. 连接WebSocket
    this.wsManager.connect();
    
    // 6. 绑定事件
    this.bindEvents();
    
    // 7. 启动定期更新
    this.startPeriodicUpdates();

    console.log('[ARPage] AR监控页面初始化完成 ✅');
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 全局点击事件委托
    document.addEventListener('click', (e) => {
      const actionEl = e.target.closest('[data-action]');
      if (!actionEl) return;
      
      const action = actionEl.dataset.action;
      this.handleAction(action, actionEl);
    });
  }

  /**
   * 处理动作
   * @param {string} action - 动作名称
   * @param {HTMLElement} element - 触发元素
   */
  handleAction(action, element) {
    switch(action) {
      case 'refresh-ar':
        this.refreshAR();
        break;
      case 'start-ar':
        this.startARScene();
        break;
      case 'stop-ar':
        this.stopARScene();
        break;
      case 'settings-ar':
        this.openSettings();
        break;
      case 'close-modal':
        this.nodeModal.close();
        break;
      case 'refresh-node':
        const nodeId = element.dataset.nodeId;
        this.refreshNode(nodeId);
        break;
      case 'view-logs':
        const logNodeId = element.dataset.nodeId;
        this.viewNodeLogs(logNodeId);
        break;
      case 'select-node':
        const selectNodeId = element.dataset.nodeId;
        this.selectNode(selectNodeId);
        break;
    }
  }

  /**
   * 选择节点
   * @param {string} nodeId - 节点ID
   */
  selectNode(nodeId) {
    const node = this.arNodes.find(n => n.id === nodeId);
    if (!node) return;
    
    this.nodeModal.show(node);
    
    // 高亮选中的节点
    document.querySelectorAll('#ar-nodes-list .ar-node-item').forEach(item => {
      item.classList.toggle('active', item.dataset.nodeId === nodeId);
    });
  }

  /**
   * 刷新AR
   */
  async refreshAR() {
    this.arNodes = await this.dataManager.loadNodes();
    this.sidebar.renderNodes(this.arNodes);
    this.mainContent.updateStats(this.arNodes);
    
    this.ui.showToast({
      type: 'success',
      message: '已刷新AR节点状态'
    });
  }

  /**
   * 启动AR场景
   */
  startARScene() {
    this.mainContent.setSceneStatus('rendering');
    
    this.ui.showToast({
      type: 'info',
      message: '正在启动AR场景...'
    });
    
    // 模拟启动过程
    setTimeout(() => {
      this.mainContent.render3DScene(this.arNodes);
      this.mainContent.setSceneStatus('running');
      
      this.ui.showToast({
        type: 'success',
        message: 'AR场景已启动'
      });
    }, 2000);
  }

  /**
   * 停止AR场景
   */
  stopARScene() {
    this.mainContent.setSceneStatus('idle');
    
    this.ui.showToast({
      type: 'info',
      message: 'AR场景已停止'
    });
  }

  /**
   * 打开设置
   */
  openSettings() {
    this.ui.showToast({
      type: 'info',
      message: '设置功能开发中...'
    });
  }

  /**
   * 刷新节点
   * @param {string} nodeId - 节点ID
   */
  async refreshNode(nodeId) {
    this.ui.showToast({
      type: 'info',
      message: `正在刷新节点 ${nodeId}...`
    });
    
    // 重新加载所有节点
    await this.refreshAR();
  }

  /**
   * 查看节点日志
   * @param {string} nodeId - 节点ID
   */
  viewNodeLogs(nodeId) {
    this.ui.showToast({
      type: 'info',
      message: `查看节点 ${nodeId} 日志功能开发中...`
    });
  }

  /**
   * 显示节点详情弹窗
   * @param {Object} node - 节点数据
   */
  showNodeModal(node) {
    this.nodeModal.show(node);
  }

  /**
   * 获取节点状态文本
   * @param {string} status - 状态码
   * @returns {string}
   */
  getARNodeStatusText(status) {
    const statusMap = {
      'online': '在线',
      'offline': '离线',
      'busy': '繁忙',
      'error': '错误'
    };
    return statusMap[status] || status || '未知';
  }

  /**
   * 加载组件状态 (AR-backend 和 User GUI)
   */
  async loadComponentStatus() {
    try {
      // 获取AR-backend状态
      const arBackendStatus = await this.fetchComponentHealth('http://0.0.0.0:5501/health');
      
      // 获取User GUI状态
      const userGuiStatus = await this.fetchComponentHealth('http://0.0.0.0:5502/health');
      
      // 更新UI
      this.mainContent.updateComponentStatus({
        arBackend: arBackendStatus,
        userGui: userGuiStatus
      });
      
      console.log('[ARPage] 组件状态已更新:', { arBackend: arBackendStatus, userGui: userGuiStatus });
    } catch (error) {
      console.error('[ARPage] 加载组件状态失败:', error);
    }
  }

  /**
   * 获取组件健康状态
   * @param {string} url - 健康检查URL
   * @returns {string} 'online' 或 'offline'
   */
  async fetchComponentHealth(url) {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        // 5秒超时
        signal: AbortSignal.timeout(5000)
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.status === 'healthy' ? 'online' : 'offline';
      }
      return 'offline';
    } catch (error) {
      return 'offline';
    }
  }

  /**
   * 启动定期更新
   */
  startPeriodicUpdates() {
    // 每30秒更新一次组件状态
    setInterval(() => {
      this.loadComponentStatus();
    }, 30000);
    
    console.log('[ARPage] 已启动定期更新 (30秒间隔)');
  }
}
