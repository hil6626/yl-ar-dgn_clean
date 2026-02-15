/**
 * 属性面板组件
 * 拆分自: page-dag.js 中的属性相关方法
 * 版本: v1.0.0
 */

export class PropertiesPanel {
  /**
   * @param {DAGPage} page - DAG页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('properties-content');
  }

  /**
   * 渲染属性面板
   */
  render() {
    if (!this.mount) {
      console.warn('[PropertiesPanel] 挂载点不存在: #properties-content');
      return;
    }
    
    this.renderEmpty();
    console.log('[PropertiesPanel] 属性面板渲染完成');
  }

  /**
   * 渲染空状态
   */
  renderEmpty() {
    if (!this.mount) return;
    
    this.mount.innerHTML = `
      <div class="dag-properties-empty">
        <div class="empty-icon">📋</div>
        <p>选择节点或连线查看属性</p>
      </div>
    `;
  }

  /**
   * 渲染节点属性
   */
  renderNodeProperties() {
    if (!this.mount) return;

    const node = this.page.selectedNode;
    if (!node) {
      this.renderEmpty();
      return;
    }

    this.mount.innerHTML = `
      <div class="dag-property-group">
        <label class="dag-property-label">节点ID</label>
        <input type="text" class="dag-property-input" value="${node.id}" readonly>
      </div>
      
      <div class="dag-property-group">
        <label class="dag-property-label">节点名称</label>
        <input type="text" class="dag-property-input" id="prop-name" value="${node.name}">
      </div>
      
      <div class="dag-property-group">
        <label class="dag-property-label">节点类型</label>
        <select class="dag-property-select" id="prop-type">
          <option value="start" ${node.type === 'start' ? 'selected' : ''}>开始节点</option>
          <option value="process" ${node.type === 'process' ? 'selected' : ''}>处理节点</option>
          <option value="condition" ${node.type === 'condition' ? 'selected' : ''}>条件判断</option>
          <option value="end" ${node.type === 'end' ? 'selected' : ''}>结束节点</option>
        </select>
      </div>
      
      <div class="dag-property-group">
        <label class="dag-property-label">执行脚本</label>
        <input type="text" class="dag-property-input" id="prop-script" placeholder="输入脚本路径">
      </div>
      
      <div class="dag-property-group">
        <label class="dag-property-label">节点配置</label>
        <textarea class="dag-property-textarea" id="prop-config" placeholder="JSON配置..."></textarea>
      </div>
      
      <div class="dag-property-group">
        <label class="dag-property-toggle">
          <input type="checkbox" id="prop-enabled" checked>
          <span class="dag-toggle-slider"></span>
          <span>启用节点</span>
        </label>
      </div>
      
      <div class="dag-property-actions">
        <button class="dag-control-btn primary" id="btn-save-node">
          <span>💾</span> 保存
        </button>
        <button class="dag-control-btn danger" id="btn-delete-node">
          <span>🗑️</span> 删除
        </button>
      </div>
    `;

    // 绑定事件
    document.getElementById('btn-save-node')?.addEventListener('click', () => this.saveNodeProperties());
    document.getElementById('btn-delete-node')?.addEventListener('click', () => this.page.deleteNode());
  }

  /**
   * 渲染边线属性
   */
  renderEdgeProperties() {
    if (!this.mount) return;

    const edge = this.page.selectedEdge;
    if (!edge) {
      this.renderEmpty();
      return;
    }

    const fromNode = this.page.nodes.find(n => n.id === edge.from);
    const toNode = this.page.nodes.find(n => n.id === edge.to);

    this.mount.innerHTML = `
      <div class="dag-property-group">
        <label class="dag-property-label">连线信息</label>
        <div class="edge-info">
          <p>从: ${fromNode?.name || edge.from}</p>
          <p>到: ${toNode?.name || edge.to}</p>
        </div>
      </div>
      
      <div class="dag-property-group">
        <label class="dag-property-label">条件标签</label>
        <input type="text" class="dag-property-input" id="edge-label" 
               value="${edge.label || ''}" placeholder="输入条件标签">
      </div>
      
      <div class="dag-property-actions">
        <button class="dag-control-btn primary" id="btn-save-edge">
          <span>💾</span> 保存
        </button>
        <button class="dag-control-btn danger" id="btn-delete-edge">
          <span>🗑️</span> 删除连线
        </button>
      </div>
    `;

    // 绑定事件
    document.getElementById('btn-save-edge')?.addEventListener('click', () => this.saveEdgeProperties());
    document.getElementById('btn-delete-edge')?.addEventListener('click', () => this.page.deleteEdge(edge));
  }

  /**
   * 保存节点属性
   */
  saveNodeProperties() {
    const node = this.page.selectedNode;
    if (!node) return;

    const nameInput = document.getElementById('prop-name');
    const typeInput = document.getElementById('prop-type');

    if (nameInput) node.name = nameInput.value;
    if (typeInput) node.type = typeInput.value;

    this.page.renderNodes();
    this.page.autoSaveManager.markUnsaved();
    this.page.ui.showToast({ type: 'success', message: '节点属性已保存' });
  }

  /**
   * 保存边线属性
   */
  saveEdgeProperties() {
    const edge = this.page.selectedEdge;
    if (!edge) return;

    const labelInput = document.getElementById('edge-label');
    if (labelInput) {
      edge.label = labelInput.value || undefined;
    }

    this.page.renderEdges();
    this.page.autoSaveManager.markUnsaved();
    this.page.ui.showToast({ type: 'success', message: '连线属性已保存' });
  }
}
