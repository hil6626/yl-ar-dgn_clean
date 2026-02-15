/**
 * 节点面板组件
 * 拆分自: page-dag.js renderNodePanel()
 * 版本: v1.0.0
 */

export class NodePanel {
  /**
   * @param {DAGPage} page - DAG页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('dag-nodes-panel');
  }

  /**
   * 渲染节点面板
   */
  render() {
    if (!this.mount) {
      console.warn('[NodePanel] 挂载点不存在: #dag-nodes-panel');
      return;
    }
    
    this.mount.innerHTML = this.generateHTML();
    this.bindEvents();
    
    console.log('[NodePanel] 节点面板渲染完成');
  }

  /**
   * 生成HTML
   * @returns {string}
   */
  generateHTML() {
    return `
      <div class="dag-nodes-header">
        <h3>节点库</h3>
      </div>
      <div class="dag-nodes-content">
        ${this.page.nodeTemplates.map((category, catIndex) => `
          <div class="dag-node-category">
            <div class="dag-category-header ${category.expanded ? 'expanded' : ''}" data-category="${catIndex}">
              <span class="category-icon">${category.icon}</span>
              <span class="category-name">${category.category}</span>
              <span class="category-toggle">▶</span>
            </div>
            <div class="dag-category-nodes ${category.expanded ? 'expanded' : ''}" id="category-${catIndex}">
              ${category.nodes.map(node => `
                <div class="dag-node-template" 
                     draggable="true"
                     data-node-type="${node.type}"
                     data-node-shape="${node.shape}"
                     data-node-name="${node.name}"
                     data-node-icon="${node.icon}"
                     data-node-color="${node.color}">
                  <div class="node-shape ${node.shape}" style="background: ${node.color}"></div>
                  <span class="node-label">${node.name}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 分类展开/折叠
    this.mount.querySelectorAll('.dag-category-header').forEach(header => {
      header.addEventListener('click', () => this.toggleCategory(header));
    });

    // 拖拽事件
    this.mount.querySelectorAll('.dag-node-template').forEach(template => {
      template.addEventListener('dragstart', (e) => this.handleDragStart(e, template));
    });
  }

  /**
   * 切换分类展开/折叠
   * @param {HTMLElement} header - 分类头部元素
   */
  toggleCategory(header) {
    const catIndex = header.dataset.category;
    const nodesContainer = document.getElementById(`category-${catIndex}`);
    const isExpanded = header.classList.contains('expanded');
    
    header.classList.toggle('expanded', !isExpanded);
    nodesContainer.classList.toggle('expanded', !isExpanded);
  }

  /**
   * 处理拖拽开始
   * @param {DragEvent} e - 拖拽事件
   * @param {HTMLElement} template - 节点模板元素
   */
  handleDragStart(e, template) {
    e.dataTransfer.setData('nodeType', template.dataset.nodeType);
    e.dataTransfer.setData('nodeShape', template.dataset.nodeShape);
    e.dataTransfer.setData('nodeName', template.dataset.nodeName);
    e.dataTransfer.setData('nodeIcon', template.dataset.nodeIcon);
    e.dataTransfer.setData('nodeColor', template.dataset.nodeColor);
    e.dataTransfer.effectAllowed = 'copy';
    
    console.log(`[NodePanel] 开始拖拽节点: ${template.dataset.nodeName}`);
  }

  /**
   * 展开指定分类
   * @param {number} categoryIndex - 分类索引
   */
  expandCategory(categoryIndex) {
    const header = this.mount.querySelector(`[data-category="${categoryIndex}"]`);
    const nodesContainer = document.getElementById(`category-${categoryIndex}`);
    
    if (header && nodesContainer) {
      header.classList.add('expanded');
      nodesContainer.classList.add('expanded');
    }
  }

  /**
   * 折叠指定分类
   * @param {number} categoryIndex - 分类索引
   */
  collapseCategory(categoryIndex) {
    const header = this.mount.querySelector(`[data-category="${categoryIndex}"]`);
    const nodesContainer = document.getElementById(`category-${categoryIndex}`);
    
    if (header && nodesContainer) {
      header.classList.remove('expanded');
      nodesContainer.classList.remove('expanded');
    }
  }
}
