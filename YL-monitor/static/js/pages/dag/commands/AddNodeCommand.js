/**
 * 添加节点命令
 * 拆分自: page-dag.js
 * 版本: v1.0.0
 */

export class AddNodeCommand {
  /**
   * @param {DAGPage} page - DAG页面实例
   * @param {Object} node - 节点数据
   */
  constructor(page, node) {
    this.page = page;
    this.node = node;
    this.nodeId = node.id;
  }

  /**
   * 执行添加节点
   */
  execute() {
    this.page.nodes.push(this.node);
    this.page.renderNodes();
  }

  /**
   * 撤销添加节点
   */
  undo() {
    this.page.nodes = this.page.nodes.filter(n => n.id !== this.nodeId);
    this.page.renderNodes();
  }

  /**
   * 获取命令描述
   * @returns {string}
   */
  getDescription() {
    return `添加节点: ${this.node.name}`;
  }
}
