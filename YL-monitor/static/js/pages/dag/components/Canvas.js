/**
 * 画布组件 - 处理DAG画布渲染和交互
 * 拆分自: page-dag.js 中的画布相关方法
 * 版本: v1.0.0
 */

import { MoveNodeCommand } from '../commands/MoveNodeCommand.js';

export class Canvas {
  /**
   * @param {DAGPage} page - DAG页面实例
   */
  constructor(page) {
    this.page = page;
    this.canvasContainer = null;
    this.canvas = null;
    this.scale = 1;
    this.translateX = 0;
    this.translateY = 0;
    this.isDragging = false;
    this.isNodeDragging = false;
    this.dragNode = null;
    this.dragOffset = { x: 0, y: 0 };
    this.dragStartPos = null;
  }

  /**
   * 初始化画布
   */
  init() {
    this.canvasContainer = document.getElementById('dag-canvas-container');
    this.canvas = document.getElementById('dag-canvas');
    
    if (!this.canvas || !this.canvasContainer) {
      console.warn('[Canvas] 画布元素不存在');
      return;
    }

    this.updateTransform();
    this.bindCanvasEvents();
    this.bindZoomControls();
    
    console.log('[Canvas] 画布初始化完成');
  }

  /**
   * 渲染画布
   */
  render() {
    this.init();
    this.renderNodes();
    this.renderEdges();
  }

  /**
   * 渲染节点
   */
  renderNodes() {
    const container = document.getElementById('dag-nodes-layer');
    if (!container) return;

    container.innerHTML = this.page.nodes.map(node => `
      <div class="dag-node shape-${node.shape} status-${node.status} ${this.page.selectedNode?.id === node.id ? 'selected' : ''}"
           data-node-id="${node.id}"
           style="left: ${node.x}px; top: ${node.y}px; border-color: ${node.color}">
        <div class="node-content">
          <div class="node-icon">${node.icon}</div>
          <div class="node-name">${node.name}</div>
          <div class="node-status">
            <span class="status-dot"></span>
            <span>${this.getStatusText(node.status)}</span>
          </div>
        </div>
        <div class="connection-point top"></div>
        <div class="connection-point bottom"></div>
        <div class="connection-point left"></div>
        <div class="connection-point right"></div>
      </div>
    `).join('');

    // 绑定节点事件
    container.querySelectorAll('.dag-node').forEach(nodeEl => {
      nodeEl.addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectNode(nodeEl.dataset.nodeId);
      });

      nodeEl.addEventListener('mousedown', (e) => {
        e.stopPropagation();
        this.startNodeDrag(e, nodeEl.dataset.nodeId);
      });
    });
  }

  /**
   * 渲染边线
   */
  renderEdges() {
    const svg = document.getElementById('dag-edges-layer');
    if (!svg) return;

    // 清空现有边线
    svg.innerHTML = '';

    // 计算边线路径
    this.page.edges.forEach((edge, index) => {
      const fromNode = this.page.nodes.find(n => n.id === edge.from);
      const toNode = this.page.nodes.find(n => n.id === edge.to);
      
      if (!fromNode || !toNode) return;

      const path = this.calculateBezierPath(fromNode, toNode);
      
      const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      pathEl.setAttribute('d', path);
      
      // 检查是否选中
      const isSelected = this.page.selectedEdge && 
        this.page.selectedEdge.from === edge.from && 
        this.page.selectedEdge.to === edge.to;
      
      let className = 'dag-edge-path';
      if (edge.label) className += ' conditional';
      if (isSelected) className += ' selected';
      if (this.page.edgeEditMode) className += ' editable';
      
      pathEl.setAttribute('class', className);
      pathEl.setAttribute('data-edge-index', index);
      pathEl.setAttribute('data-edge-from', edge.from);
      pathEl.setAttribute('data-edge-to', edge.to);
      
      // 绑定点击事件
      pathEl.addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectEdge(edge);
      });
      
      // 绑定双击删除
      pathEl.addEventListener('dblclick', (e) => {
        e.stopPropagation();
        this.page.deleteEdge(edge);
      });
      
      svg.appendChild(pathEl);

      // 添加标签
      if (edge.label) {
        const midX = (fromNode.x + toNode.x) / 2 + 60;
        const midY = (fromNode.y + toNode.y) / 2 + 30;
        
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', midY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', 'var(--text-secondary)');
        text.setAttribute('font-size', '12');
        text.textContent = edge.label;
        
        svg.appendChild(text);
      }
    });
  }

  /**
   * 计算贝塞尔曲线路径
   * @param {Object} fromNode - 起始节点
   * @param {Object} toNode - 目标节点
   * @returns {string} SVG路径
   */
  calculateBezierPath(fromNode, toNode) {
    const fromX = fromNode.x + 60;
    const fromY = fromNode.y + 30;
    const toX = toNode.x + 60;
    const toY = toNode.y + 30;
    
    const controlX1 = fromX + (toX - fromX) / 2;
    const controlY1 = fromY;
    const controlX2 = fromX + (toX - fromX) / 2;
    const controlY2 = toY;
    
    return `M ${fromX} ${fromY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${toX} ${toY}`;
  }

  /**
   * 获取状态文本
   * @param {string} status - 状态码
   * @returns {string}
   */
  getStatusText(status) {
    const statusMap = {
      pending: '等待中',
      running: '运行中',
      success: '成功',
      error: '失败',
      warning: '警告'
    };
    return statusMap[status] || status;
  }

  /**
   * 选中节点
   * @param {string} nodeId - 节点ID
   */
  selectNode(nodeId) {
    this.page.selectedNode = this.page.nodes.find(n => n.id === nodeId);
    this.page.selectedEdge = null;
    this.renderNodes();
    this.renderEdges();
    this.page.propertiesPanel.renderNodeProperties();
  }

  /**
   * 选中边线
   * @param {Object} edge - 边线数据
   */
  selectEdge(edge) {
    this.page.selectedEdge = edge;
    this.page.selectedNode = null;
    this.renderEdges();
    this.renderNodes();
    this.page.propertiesPanel.renderEdgeProperties();
  }

  /**
   * 开始画布拖拽
   * @param {MouseEvent} e - 鼠标事件
   */
  startCanvasDrag(e) {
    this.isDragging = true;
    this.dragStartX = e.clientX - this.translateX;
    this.dragStartY = e.clientY - this.translateY;
    this.canvas.classList.add('dragging');
  }

  /**
   * 开始节点拖拽
   * @param {MouseEvent} e - 鼠标事件
   * @param {string} nodeId - 节点ID
   */
  startNodeDrag(e, nodeId) {
    this.isNodeDragging = true;
    this.dragNode = this.page.nodes.find(n => n.id === nodeId);
    
    if (this.dragNode) {
      const rect = this.canvas.getBoundingClientRect();
      this.dragOffset.x = (e.clientX - rect.left) / this.scale - this.dragNode.x;
      this.dragOffset.y = (e.clientY - rect.top) / this.scale - this.dragNode.y;
      this.dragStartPos = { x: this.dragNode.x, y: this.dragNode.y };
    }
  }

  /**
   * 处理鼠标移动
   * @param {MouseEvent} e - 鼠标事件
   */
  handleMouseMove(e) {
    if (this.isDragging) {
      this.translateX = e.clientX - this.dragStartX;
      this.translateY = e.clientY - this.dragStartY;
      this.updateTransform();
    }
    
    if (this.isNodeDragging && this.dragNode) {
      const rect = this.canvas.getBoundingClientRect();
      this.dragNode.x = (e.clientX - rect.left) / this.scale - this.dragOffset.x;
      this.dragNode.y = (e.clientY - rect.top) / this.scale - this.dragOffset.y;
      
      // 更新节点位置
      const nodeEl = document.querySelector(`[data-node-id="${this.dragNode.id}"]`);
      if (nodeEl) {
        nodeEl.style.left = `${this.dragNode.x}px`;
        nodeEl.style.top = `${this.dragNode.y}px`;
      }
      
      // 重新渲染边线
      this.renderEdges();
    }
  }

  /**
   * 处理鼠标释放
   */
  handleMouseUp() {
    // 如果节点被拖拽，记录移动命令
    if (this.isNodeDragging && this.dragNode && this.dragStartPos) {
      const newPos = { x: this.dragNode.x, y: this.dragNode.y };
      
      if (this.dragStartPos.x !== newPos.x || this.dragStartPos.y !== newPos.y) {
        const command = new MoveNodeCommand(this.page, this.dragNode.id, this.dragStartPos, newPos);
        this.page.commandManager.execute(command);
        this.page.autoSaveManager.markUnsaved();
      }
    }
    
    this.isDragging = false;
    this.isNodeDragging = false;
    this.dragNode = null;
    this.dragStartPos = null;
    this.canvas?.classList.remove('dragging');
  }

  /**
   * 更新画布变换
   */
  updateTransform() {
    if (this.canvas) {
      this.canvas.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
    }
  }

  /**
   * 放大
   */
  zoomIn() {
    this.scale = Math.min(this.scale * 1.2, 3);
    this.updateTransform();
    this.updateZoomDisplay();
  }

  /**
   * 缩小
   */
  zoomOut() {
    this.scale = Math.max(this.scale / 1.2, 0.3);
    this.updateTransform();
    this.updateZoomDisplay();
  }

  /**
   * 适应画布
   */
  zoomFit() {
    this.scale = 1;
    this.translateX = 0;
    this.translateY = 0;
    this.updateTransform();
    this.updateZoomDisplay();
  }

  /**
   * 更新缩放显示
   */
  updateZoomDisplay() {
    const display = document.getElementById('zoom-level');
    if (display) {
      display.textContent = `${Math.round(this.scale * 100)}%`;
    }
  }

  /**
   * 绑定画布事件
   */
  bindCanvasEvents() {
    // 画布拖拽
    this.canvas?.addEventListener('mousedown', (e) => {
      if (e.target === this.canvas || e.target.classList.contains('dag-edges-layer')) {
        this.startCanvasDrag(e);
      }
    });

    // 画布点击 - 清除选中
    this.canvas?.addEventListener('click', (e) => {
      if (e.target === this.canvas || e.target.id === 'dag-edges-layer') {
        this.page.selectedNode = null;
        this.page.selectedEdge = null;
        this.renderNodes();
        this.renderEdges();
        this.page.propertiesPanel.renderEmpty();
      }
    });

    // 画布拖放
    this.canvas?.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    });

    this.canvas?.addEventListener('drop', (e) => {
      e.preventDefault();
      this.page.handleDrop(e);
    });
  }

  /**
   * 绑定缩放控制
   */
  bindZoomControls() {
    document.getElementById('zoom-in')?.addEventListener('click', () => this.zoomIn());
    document.getElementById('zoom-out')?.addEventListener('click', () => this.zoomOut());
    document.getElementById('zoom-fit')?.addEventListener('click', () => this.zoomFit());
  }
}
