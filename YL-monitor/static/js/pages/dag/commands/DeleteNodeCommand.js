/**
 * 删除节点命令
 * 拆分自: page-dag.js
 * 版本: v1.0.0
 */

export class DeleteNodeCommand {
  /**
   * @param {DAGPage} page - DAG页面实例
   * @param {Object} node - 要删除的节点
   * @param {Array} relatedEdges - 相关的边线
   */
  constructor(page, node, relatedEdges) {
    this.page = page;
    this.node = node;
    this.nodeId = node.id;
    this.relatedEdges = relatedEdges || [];
  }

  /**
   * 执行删除节点
   */
  execute() {
    // 删除相关边线
    this.page.edges = this.page.edges.filter(e => 
      !this.relatedEdges.some(re => re.from === e.from && re.to === e.to)
    );
    
    // 删除节点
    this.page.nodes = this.page.nodes.filter(n => n.id !== this.nodeId);
    
    this.page.renderNodes();
    this.page.renderEdges();
  }

  /**
   * 撤销删除节点
   */
  undo() {
    // 恢复节点
    this.page.nodes.push(this.node);
    
    // 恢复边线
    this.page.edges.push(...this.relatedEdges);
    
    this.page.renderNodes();
    this.page.renderEdges();
  }

  /**
   * 获取命令描述
   * @returns {string}
   */
  getDescription() {
    return `删除节点: ${this.node.name}`;
  }
}
