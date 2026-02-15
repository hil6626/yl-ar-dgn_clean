/**
 * 移动节点命令
 * 拆分自: page-dag.js
 * 版本: v1.0.0
 */

export class MoveNodeCommand {
  /**
   * @param {DAGPage} page - DAG页面实例
   * @param {string} nodeId - 节点ID
   * @param {Object} oldPos - 原位置 {x, y}
   * @param {Object} newPos - 新位置 {x, y}
   */
  constructor(page, nodeId, oldPos, newPos) {
    this.page = page;
    this.nodeId = nodeId;
    this.oldPos = { ...oldPos };
    this.newPos = { ...newPos };
  }

  /**
   * 执行移动节点
   */
  execute() {
    const node = this.page.nodes.find(n => n.id === this.nodeId);
    if (node) {
      node.x = this.newPos.x;
      node.y = this.newPos.y;
      this.page.renderNodes();
      this.page.renderEdges();
    }
  }

  /**
   * 撤销移动节点
   */
  undo() {
    const node = this.page.nodes.find(n => n.id === this.nodeId);
    if (node) {
      node.x = this.oldPos.x;
      node.y = this.oldPos.y;
      this.page.renderNodes();
      this.page.renderEdges();
    }
  }

  /**
   * 获取命令描述
   * @returns {string}
   */
  getDescription() {
    const node = this.page.nodes.find(n => n.id === this.nodeId);
    return `移动节点: ${node ? node.name : this.nodeId}`;
  }
}
