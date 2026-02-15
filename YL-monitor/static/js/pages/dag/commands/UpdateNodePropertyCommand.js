/**
 * 更新节点属性命令
 * 拆分自: page-dag.js
 * 版本: v1.0.0
 */

export class UpdateNodePropertyCommand {
  /**
   * @param {DAGPage} page - DAG页面实例
   * @param {string} nodeId - 节点ID
   * @param {string} property - 属性名
   * @param {*} oldValue - 原值
   * @param {*} newValue - 新值
   */
  constructor(page, nodeId, property, oldValue, newValue) {
    this.page = page;
    this.nodeId = nodeId;
    this.property = property;
    this.oldValue = oldValue;
    this.newValue = newValue;
  }

  /**
   * 执行更新属性
   */
  execute() {
    const node = this.page.nodes.find(n => n.id === this.nodeId);
    if (node) {
      node[this.property] = this.newValue;
      this.page.renderNodes();
    }
  }

  /**
   * 撤销更新属性
   */
  undo() {
    const node = this.page.nodes.find(n => n.id === this.nodeId);
    if (node) {
      node[this.property] = this.oldValue;
      this.page.renderNodes();
    }
  }

  /**
   * 获取命令描述
   * @returns {string}
   */
  getDescription() {
    const node = this.page.nodes.find(n => n.id === this.nodeId);
    return `更新节点属性: ${node ? node.name : this.nodeId}.${this.property}`;
  }
}
