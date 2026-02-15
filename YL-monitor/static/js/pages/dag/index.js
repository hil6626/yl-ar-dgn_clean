/**
 * DAG页面入口
 * 重构自: page-dag.js (1,510行 → 模块化拆分)
 * 版本: v9.0.0 (模块化版本)
 */

// 导入命令类
import {
  CommandManager,
  AddNodeCommand,
  DeleteNodeCommand,
  MoveNodeCommand,
  UpdateNodePropertyCommand,
  AddEdgeCommand,
  DeleteEdgeCommand
} from './commands/index.js';

// 导入管理器
import { AutoSaveManager, ExecutionManager } from './managers/index.js';

// 导入组件
import { NodePanel, Canvas, PropertiesPanel, ControlBar } from './components/index.js';

/**
 * DAG页面主类
 */
export default class DAGPage {
  /**
   * @param {Object} deps - 依赖项（可选）
   * @param {Object} deps.themeManager - 主题管理器（可选）
   * @param {Object} deps.uiComponents - UI组件库（可选）
   */
  constructor(deps = {}) {
    this.themeManager = deps.themeManager || null;
    this.ui = deps.uiComponents || { showToast: () => {}, showConfirm: () => {} };
    this.apiBaseUrl = '/api/v1';
    
    // 初始化管理器
    this.commandManager = new CommandManager(this);
    this.autoSaveManager = new AutoSaveManager(this);
    this.executionManager = new ExecutionManager(this);
    
    // 初始化组件
    this.nodePanel = new NodePanel(this);
    this.canvas = new Canvas(this);
    this.propertiesPanel = new PropertiesPanel(this);
    this.controlBar = new ControlBar(this);
    
    // 数据状态
    this.nodes = [];
    this.edges = [];
    this.selectedNode = null;
    this.selectedEdge = null;
    this.edgeEditMode = false;
    
    // 节点模板配置
    this.nodeTemplates = [
      {
        category: '基础节点',
        icon: '🔧',
        expanded: true,
        nodes: [
          { type: 'start', name: '开始节点', shape: 'circle', icon: '🚀', color: '#10b981' },
          { type: 'end', name: '结束节点', shape: 'circle', icon: '🏁', color: '#ef4444' }
        ]
      },
      {
        category: '处理节点',
        icon: '⚙️',
        expanded: true,
        nodes: [
          { type: 'process', name: '处理节点', shape: 'rect', icon: '⚙️', color: '#3b82f6' },
          { type: 'condition', name: '条件判断', shape: 'diamond', icon: '❓', color: '#f59e0b' },
          { type: 'loop', name: '循环节点', shape: 'hexagon', icon: '🔄', color: '#8b5cf6' }
        ]
      },
      {
        category: '数据节点',
        icon: '📦',
        expanded: false,
        nodes: [
          { type: 'input', name: '数据输入', shape: 'rounded', icon: '📥', color: '#06b6d4' },
          { type: 'output', name: '数据输出', shape: 'rounded', icon: '📤', color: '#ec4899' },
          { type: 'transform', name: '数据转换', shape: 'rect', icon: '🔀', color: '#6366f1' }
        ]
      }
    ];
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[DAGPage] 初始化DAG页面 v9.0.0 (模块化)...');
    
    // 1. 渲染控制栏
    this.controlBar.render();
    
    // 2. 渲染节点库
    this.nodePanel.render();
    
    // 3. 渲染画布
    this.canvas.render();
    
    // 4. 渲染属性面板
    this.propertiesPanel.render();
    
    // 5. 渲染执行面板
    this.renderExecutionPanel();
    
    // 6. 加载DAG数据
    await this.loadDAGData();
    
    // 7. 初始化自动保存
    this.autoSaveManager.init();
    
    // 8. 绑定全局事件
    this.bindGlobalEvents();
    
    console.log('[DAGPage] DAG页面初始化完成 ✅');
  }

  /**
   * 渲染执行面板
   */
  renderExecutionPanel() {
    const mount = document.getElementById('dag-execution-panel');
    if (!mount) return;

    // 绑定折叠/展开
    const header = mount.querySelector('.execution-panel-header');
    if (header) {
      header.addEventListener('click', () => {
        const isCollapsed = mount.classList.contains('collapsed');
        mount.classList.toggle('collapsed', !isCollapsed);
        mount.classList.toggle('expanded', isCollapsed);
      });
    }
  }

  /**
   * 加载DAG数据
   */
  async loadDAGData() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/dag/definition`);
      if (!response.ok) throw new Error('加载DAG数据失败');
      
      const data = await response.json();
      this.nodes = data.nodes || this.getSampleNodes();
      this.edges = data.edges || this.getSampleEdges();
    } catch (error) {
      console.warn('[DAGPage] 使用示例数据:', error);
      this.nodes = this.getSampleNodes();
      this.edges = this.getSampleEdges();
    }

    this.canvas.renderNodes();
    this.canvas.renderEdges();
  }

  /**
   * 获取示例节点
   * @returns {Array}
   */
  getSampleNodes() {
    return [
      { id: 'node-1', type: 'start', name: '开始', shape: 'circle', icon: '🚀', x: 100, y: 200, status: 'success', color: '#10b981' },
      { id: 'node-2', type: 'process', name: '数据处理', shape: 'rect', icon: '⚙️', x: 300, y: 200, status: 'success', color: '#3b82f6' },
      { id: 'node-3', type: 'condition', name: '条件判断', shape: 'diamond', icon: '❓', x: 500, y: 200, status: 'running', color: '#f59e0b' },
      { id: 'node-4', type: 'process', name: '分支A', shape: 'rect', icon: '🔀', x: 700, y: 100, status: 'pending', color: '#6366f1' },
      { id: 'node-5', type: 'process', name: '分支B', shape: 'rect', icon: '🔀', x: 700, y: 300, status: 'pending', color: '#6366f1' },
      { id: 'node-6', type: 'end', name: '结束', shape: 'circle', icon: '🏁', x: 900, y: 200, status: 'pending', color: '#ef4444' }
    ];
  }

  /**
   * 获取示例边线
   * @returns {Array}
   */
  getSampleEdges() {
    return [
      { from: 'node-1', to: 'node-2' },
      { from: 'node-2', to: 'node-3' },
      { from: 'node-3', to: 'node-4', label: '是' },
      { from: 'node-3', to: 'node-5', label: '否' },
      { from: 'node-4', to: 'node-6' },
      { from: 'node-5', to: 'node-6' }
    ];
  }

  /**
   * 绑定全局事件
   */
  bindGlobalEvents() {
    // 全局鼠标事件
    document.addEventListener('mousemove', (e) => this.canvas.handleMouseMove(e));
    document.addEventListener('mouseup', () => this.canvas.handleMouseUp());
    
    // 键盘事件 - Delete键删除选中
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (this.selectedNode) {
          this.deleteNode();
        } else if (this.selectedEdge) {
          this.deleteEdge(this.selectedEdge);
        }
      }
    });
  }

  /**
   * 处理拖放
   * @param {DragEvent} e - 拖拽事件
   */
  handleDrop(e) {
    const nodeType = e.dataTransfer.getData('nodeType');
    const nodeShape = e.dataTransfer.getData('nodeShape');
    const nodeName = e.dataTransfer.getData('nodeName');
    const nodeIcon = e.dataTransfer.getData('nodeIcon');
    const nodeColor = e.dataTransfer.getData('nodeColor');
    
    if (!nodeType) return;
    
    const rect = this.canvas.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.canvas.translateX) / this.canvas.scale - 60;
    const y = (e.clientY - rect.top - this.canvas.translateY) / this.canvas.scale - 30;
    
    const newNode = {
      id: `node-${Date.now()}`,
      type: nodeType,
      name: nodeName,
      shape: nodeShape,
      icon: nodeIcon,
      color: nodeColor,
      x: Math.max(0, x),
      y: Math.max(0, y),
      status: 'pending'
    };
    
    // 使用命令模式添加节点
    const command = new AddNodeCommand(this, newNode);
    this.commandManager.execute(command);
    
    // 标记有未保存变更
    this.autoSaveManager.markUnsaved();
    
    this.ui.showToast({ type: 'success', message: `已添加节点: ${nodeName}` });
  }

  /**
   * 删除节点
   */
  deleteNode() {
    if (!this.selectedNode) return;
    
    this.ui.showConfirm({
      title: '删除节点',
      message: `确定要删除节点 "${this.selectedNode.name}" 吗？`,
      type: 'danger',
      confirmText: '删除',
      onConfirm: () => {
        // 查找相关边线
        const relatedEdges = this.edges.filter(e => 
          e.from === this.selectedNode.id || e.to === this.selectedNode.id
        );
        
        // 使用命令模式删除节点
        const command = new DeleteNodeCommand(this, this.selectedNode, relatedEdges);
        this.commandManager.execute(command);
        
        this.selectedNode = null;
        this.propertiesPanel.renderEmpty();
        
        // 标记有未保存变更
        this.autoSaveManager.markUnsaved();
        
        this.ui.showToast({ type: 'success', message: '节点已删除' });
      }
    });
  }

  /**
   * 删除边线
   * @param {Object} edge - 边线数据
   */
  deleteEdge(edge) {
    if (!edge) return;
    
    const fromNode = this.nodes.find(n => n.id === edge.from);
    const toNode = this.nodes.find(n => n.id === edge.to);
    
    this.ui.showConfirm({
      title: '删除连线',
      message: `确定要删除从 "${fromNode?.name || edge.from}" 到 "${toNode?.name || edge.to}" 的连线吗？`,
      type: 'danger',
      confirmText: '删除',
      onConfirm: () => {
        const command = new DeleteEdgeCommand(this, edge);
        this.commandManager.execute(command);
        
        this.selectedEdge = null;
        this.propertiesPanel.renderEmpty();
        
        // 标记有未保存变更
        this.autoSaveManager.markUnsaved();
        
        this.ui.showToast({ type: 'success', message: '连线已删除' });
      }
    });
  }

  /**
   * 切换连线编辑模式
   */
  toggleEdgeEditMode() {
    this.edgeEditMode = !this.edgeEditMode;
    this.controlBar.updateButtonStates();
    this.canvas.renderEdges();
    
    this.ui.showToast({ 
      type: 'info', 
      message: this.edgeEditMode ? '进入连线编辑模式，可以选中和删除连线' : '退出连线编辑模式' 
    });
  }

  /**
   * 保存DAG
   */
  async saveDAG() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/dag/definition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes: this.nodes, edges: this.edges })
      });
      
      if (!response.ok) throw new Error('保存失败');
      
      // 通知自动保存管理器已手动保存
      this.autoSaveManager.onManualSave();
      
      this.ui.showToast({ type: 'success', message: 'DAG已保存' });
    } catch (error) {
      console.error('[DAGPage] 保存失败:', error);
      this.ui.showToast({ type: 'error', message: '保存失败' });
    }
  }

  /**
   * 撤销
   */
  undo() {
    this.commandManager.undo();
    this.controlBar.updateButtonStates();
  }

  /**
   * 重做
   */
  redo() {
    this.commandManager.redo();
    this.controlBar.updateButtonStates();
  }

  /**
   * 导出DAG
   */
  exportDAG() {
    const dagData = {
      name: 'YL-Monitor DAG',
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      nodes: this.nodes,
      edges: this.edges
    };
    
    const blob = new Blob([JSON.stringify(dagData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dag-definition.json';
    a.click();
    URL.revokeObjectURL(url);
    
    this.ui.showToast({ type: 'success', message: 'DAG已导出' });
  }

  /**
   * 渲染节点（委托给Canvas组件）
   */
  renderNodes() {
    this.canvas.renderNodes();
  }

  /**
   * 渲染边线（委托给Canvas组件）
   */
  renderEdges() {
    this.canvas.renderEdges();
  }
}
